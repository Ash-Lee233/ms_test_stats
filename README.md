# MindSpore Tests Stats (Git Clone Version)

This project scans a **locally cloned** MindSpore repository and analyzes the `tests/` directory to produce:

- Total test cases per `level` (`level0`, `level1`, ...)
- Per-level device breakdown: **CPU / GPU / NPU (Ascend)** + `unknown`
- Extra grouping by directory dimension (e.g., `ut/python`, `st`)
- Excel reports (multiple sheets)
- Web-based charts (Flask + ECharts)

## Chart behavior

- `unmarked` level is **kept in Excel** but **excluded from charts** (otherwise it can dominate the plots).
- **All charts display value labels** on bars.

---

## Prerequisites

- Python 3.9+
- Git installed

---

## Step 1: Clone MindSpore

```bash
git clone https://gitee.com/mindspore/mindspore.git
```

or GitHub mirror:

```bash
git clone https://github.com/mindspore-ai/mindspore.git
```

---

## Step 2: Configure

Edit `config.yaml`:

```yaml
repo_root: "/absolute/path/to/mindspore"
tests_dir: "tests"
output_excel: "output/stats.xlsx"
```

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 4: Run

```bash
python run.py
```

Then open:

- Web UI: http://127.0.0.1:5000
- Excel output: output/stats.xlsx

---

## Excel Sheets

| Sheet | Description |
|------|-----------|
| cases | Per-test details (file, dir_group, level, devices, markers) |
| summary_level | Total cases per level |
| summary_level_device | Level × device |
| summary_dir_level | Directory × level |
| summary_dir_level_device | Directory × level × device |

---

## Notes

- A test case can belong to multiple devices (CPU + GPU). It will be counted in each bucket.
- Ascend is mapped to `npu` by default (configurable via `device_keywords`).
- If no device marker is found, the case is counted as `unknown`.
