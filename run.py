import re
import yaml
from pathlib import Path

from ms_test_stats.scanner import collect_sources
from ms_test_stats.parser import extract_testcases_from_file
from ms_test_stats.stats import build_dataframes
from ms_test_stats.excel import write_excel
from ms_test_stats.webapp import create_app

def main():
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))

    repo_root = Path(cfg["repo_root"]).resolve()
    tests_root = repo_root / cfg.get("tests_dir", "tests")
    out_excel = cfg.get("output_excel", "output/stats.xlsx")

    level_re = re.compile(cfg.get("level_regex", r"^level\d+$"))

    sources = collect_sources(tests_root)

    cases = []
    for py_path, src in sources:
        try:
            cases.extend(extract_testcases_from_file(py_path, src, level_re))
        except SyntaxError:
            # Rare: some files may not be parseable
            continue

    df_cases, df_level, df_level_device, df_dir_level, df_dir_level_device = build_dataframes(
        cases, cfg["device_keywords"], str(tests_root)
    )

    write_excel(out_excel,
                df_cases,
                df_level,
                df_level_device,
                df_dir_level,
                df_dir_level_device)

    print(f"[OK] Excel written to: {out_excel}")
    print("[OK] Start web on http://127.0.0.1:5000")
    app = create_app(out_excel)
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    main()
