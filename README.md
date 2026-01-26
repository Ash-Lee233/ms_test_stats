# MindSpore Tests Stats (Git Clone Version) + Simple Quality Scoring

This project scans a **locally cloned** MindSpore repository and analyzes the `tests/` directory to produce:

- Total test cases per `level` (`level0`, `level1`, ...)
- Per-level device breakdown: **CPU / GPU / NPU (Ascend)** + `unknown`
- Grouping by directory dimension (e.g., `ut/python`, `st`)
- Excel reports (multiple sheets)
- Web-based charts (Flask + ECharts)

## Added: Simple Test Quality Scoring (A/B/C)

Each test case is assigned a **quality score** and **grade** based on simple static heuristics:

- +2 if it has at least 1 `assert` statement
- +1 extra if it has 3+ `assert` statements
- +1 if it uses `@pytest.mark.parametrize`
- +1 if it has a docstring
- -1 if it is marked with `skip` / `skipif` / `xfail`

Grade mapping:
- **A**: score >= 4
- **B**: score in [2, 3]
- **C**: score <= 1

Tune weights/rules in `ms_test_stats/quality.py`.

## Chart behavior

- `unmarked` level is **kept in Excel** but **excluded from level-based charts**.
- **All charts display value labels** on bars.

---

## Quickstart

1) Clone MindSpore
```bash
git clone https://gitee.com/mindspore/mindspore.git
```

2) Configure `config.yaml` (set `repo_root`)

3) Install
```bash
pip install -r requirements.txt
```

4) Run
```bash
python run.py
```

Open:
- Web: http://127.0.0.1:5000
- Excel: output/stats.xlsx
