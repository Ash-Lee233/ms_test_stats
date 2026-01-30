"""
Author: Shawny
"""
import re
import yaml
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ms_test_stats.scanner import collect_sources
from ms_test_stats.parser import extract_testcases_from_file
from ms_test_stats.stats import build_dataframes
from ms_test_stats.excel import write_excel
from ms_test_stats.webapp import create_app
from ms_test_stats.report import write_report


def _parse_worker(args):
    """Worker function for parallel AST parsing."""
    py_path, src, level_pattern = args
    try:
        return extract_testcases_from_file(py_path, src, re.compile(level_pattern))
    except SyntaxError:
        return []


def main():
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))

    repo_root = Path(cfg["repo_root"]).resolve()
    tests_root = repo_root / cfg.get("tests_dir", "tests")
    out_excel = cfg.get("output_excel", "output/stats.xlsx")

    level_pattern = cfg.get("level_regex", r"^level\\d+$")
    level_re = re.compile(level_pattern)

    sources = collect_sources(tests_root)

    cases = []
    work_items = [(py_path, src, level_pattern) for py_path, src in sources]
    with ProcessPoolExecutor() as pool:
        for result in pool.map(_parse_worker, work_items):
            cases.extend(result)

    dfs = build_dataframes(cases, cfg["device_keywords"], str(tests_root))
    write_excel(out_excel, **dfs)

    print(f"[OK] Excel written to: {out_excel}")
    write_report(out_excel, "output/report.html")
    print("[OK] Static report written to: output/report.html")
    print("[OK] Start web on http://127.0.0.1:5000")
    app = create_app(out_excel)
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    main()
