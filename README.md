# MindSpore Tests Stats (Git Clone Version)

This project scans a locally cloned MindSpore repository and analyzes the `tests/` directory to generate an
Excel report and a lightweight web dashboard.

## What you get

### Main statistics (skip removed)
Main statistics **exclude** test cases marked with `@pytest.mark.skip`:
- **Level × Device** breakdown (CPU/GPU/NPU/unknown)
- **Top Directories** (Top 20) by test count (directory group = `tests/<top>/<second>/` when available)

> Note: the previous *Owner × Device* chart was removed to reduce redundancy.

### Quality statistics (no skipping)
Quality analysis **includes all tests** (no skipping), including those marked with `skip`:
- Overall A/B/C distribution
- Level × A/B/C distribution
- **Owner (subdir) × A/B/C** shown as a **table** only, where owner is refined to **one more directory level**:
  - `tests/ut/python/...` → `ut/python`
  - `tests/st/networks/...` → `st/networks`
  - If only one segment exists, it falls back to the top-level folder name.

### Pytest decorator table (occurrence count, no inference)
A table that counts how many times each `@pytest...` decorator appears on test functions/methods (e.g. `pytest.mark.parametrize`),
without any “purpose inference” column.

## How it works

### Test case extraction
The parser counts:
- Top-level `def test_*`
- `class ...: def test_*` methods

Marker inheritance supported:
- Module-level `pytestmark = pytest.mark.xxx` (also list/tuple)
- Class-level decorators
- Simple module-scope alias, e.g. `level0 = pytest.mark.level0` then `@level0`

### Skip policy
- Main charts/tables: **exclude** `@pytest.mark.skip`
- Quality (A/B/C): **include all**, even if `skip` is present

## Quickstart

1) Clone MindSpore
```bash
git clone https://gitee.com/mindspore/mindspore.git
```

2) Edit `config.yaml` and set `repo_root`

3) Install
```bash
pip install -r requirements.txt
```

4) Run
```bash
python run.py
```

Outputs:
- Excel: `output/stats.xlsx`
- Web UI: http://127.0.0.1:5000
## Export the dashboard to PDF

This project does **not** generate a static HTML report anymore. If you want a PDF snapshot of the web dashboard, run:

```bash
python export_pdf.py
```

It will:
1) generate `output/stats.xlsx`
2) start the local dashboard server
3) print the dashboard page to `output/dashboard.pdf`

### Playwright note
On first use, you may need to install the browser runtime:

```bash
python -m playwright install chromium
```
