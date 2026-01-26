"""
Author: Shawny
"""
import re
import yaml
from pathlib import Path
import threading
import time

from ms_test_stats.scanner import collect_sources
from ms_test_stats.parser import extract_testcases_from_file
from ms_test_stats.stats import build_dataframes
from ms_test_stats.excel import write_excel
from ms_test_stats.webapp import create_app

def export_pdf(url: str, out_pdf: str) -> None:
    # Use Playwright to print the dashboard to PDF
    from playwright.sync_api import sync_playwright

    out = Path(out_pdf)
    out.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(url, wait_until="networkidle")
        # A little extra time for echarts rendering
        page.wait_for_timeout(1500)
        page.pdf(path=str(out), format="A4", print_background=True)
        browser.close()

def main():
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))

    repo_root = Path(cfg["repo_root"]).resolve()
    tests_root = repo_root / cfg.get("tests_dir", "tests")
    out_excel = cfg.get("output_excel", "output/stats.xlsx")
    out_pdf = cfg.get("output_pdf", "output/dashboard.pdf")

    level_re = re.compile(cfg.get("level_regex", r"^level\\d+$"))

    sources = collect_sources(tests_root)

    cases = []
    for py_path, src in sources:
        try:
            cases.extend(extract_testcases_from_file(py_path, src, level_re))
        except SyntaxError:
            continue

    dfs = build_dataframes(cases, cfg["device_keywords"], str(tests_root))
    write_excel(out_excel, **dfs)
    print(f"[OK] Excel written to: {out_excel}")

    app = create_app(out_excel)

    def run_server():
        # single-threaded server is enough for local PDF export
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    # wait for server ready
    time.sleep(1.0)

    export_pdf("http://127.0.0.1:5000/", out_pdf)
    print(f"[OK] PDF written to: {out_pdf}")

    # try to shut down
    try:
        import requests
        requests.get("http://127.0.0.1:5000/shutdown", timeout=2)
    except Exception:
        pass

if __name__ == "__main__":
    main()
