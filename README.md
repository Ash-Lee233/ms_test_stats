# MindSpore Tests Stats

Scan a locally cloned MindSpore repository's `tests/` directory, extract pytest test case metadata via AST parsing,
generate Excel reports and serve an interactive web dashboard.

## Features

### Test Case Discovery & Parsing
- Extracts top-level `def test_*` functions and `class ...: def test_*` methods (including async)
- Supports marker inheritance:
  - Module-level `pytestmark = pytest.mark.xxx` (list/tuple)
  - Class-level decorators
  - Simple alias expansion, e.g. `level0 = pytest.mark.level0` then `@level0`
- Parallel scanning (ThreadPool for I/O) and parallel AST parsing (ProcessPool for CPU)

### Statistics & Visualizations

#### Main statistics (skip removed)
Exclude test cases marked with `@pytest.mark.skip`:
- **Level x Device** stacked bar chart (CPU/GPU/NPU/unknown), with drill-down click to view matching test cases
- **Top 20 Directories** horizontal bar chart (directory group = `tests/<top>/<second>/`)

#### Quality statistics (no skipping)
Include **all** tests (even `@pytest.mark.skip`) with static A/B/C grading:
- **Quality Grade Distribution** bar chart (overall A/B/C counts)
- **Level x Quality Grade** stacked bar chart
- **Owner x Quality Grade** table (owner refined to two directory levels, e.g. `ut/python`, `st/networks`)

See [QUALITY_SCORING.md](ms_test_stats/QUALITY_SCORING.md) for full scoring methodology.

#### Pytest decorator table
Counts how many times each `@pytest...` decorator appears on test functions/methods, with both
`occurrences` and `unique_test_cases` columns.

### Output Formats
- **Excel** (`output/stats.xlsx`) — 8 sheets: cases, summary_level, summary_level_device, summary_dir_top, summary_quality, summary_quality_level, summary_quality_owner_subdir, summary_pytest_decorators
- **Web Dashboard** — Flask server with ECharts interactive charts
- **PDF** — Playwright-based headless browser screenshot of the dashboard

## Project Structure

```
ms_test_stats/
├── run.py                  # Main entry point: scan → parse → stats → Excel → web server
├── export_pdf.py           # Export dashboard to PDF via Playwright
├── config.yaml             # Configuration (repo_root, device keywords, etc.)
├── requirements.txt        # Python dependencies
├── ms_test_stats/          # Core package
│   ├── scanner.py          # Threaded file discovery and reading
│   ├── parser.py           # AST-based test case extraction
│   ├── device_map.py       # Map pytest markers to device types
│   ├── path_dim.py         # Directory grouping utilities
│   ├── quality.py          # Static quality scoring (A/B/C)
│   ├── stats.py            # DataFrame aggregation
│   ├── excel.py            # Multi-sheet Excel writer
│   ├── data_service.py     # Caching data layer with mtime invalidation
│   ├── webapp.py           # Flask REST API (7 endpoints)
│   ├── report.py           # Static HTML report generator
│   └── QUALITY_SCORING.md  # Quality grading documentation
├── templates/
│   └── index.html          # ECharts dashboard (6 visualizations)
└── output/                 # Generated outputs
    ├── stats.xlsx
    ├── report.html
    └── dashboard.pdf
```

## Quickstart

1. Clone MindSpore & this project:
```bash
git clone https://gitee.com/mindspore/mindspore.git
git clone https://github.com/Ash-Lee233/ms_test_stats.git
```

2. Edit `config.yaml` — set `repo_root` to your MindSpore clone path.

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run:
```bash
python run.py
```

Outputs:
- Excel: `output/stats.xlsx`
- Web UI: http://127.0.0.1:5000

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard page |
| `GET /api/level_device` | Level x Device matrix (unmarked excluded, skip removed) |
| `GET /api/dir_top` | Top 20 directories by test count |
| `GET /api/quality` | Overall + per-level A/B/C distribution |
| `GET /api/quality_owner_table` | Owner x Quality grade table |
| `GET /api/pytest_decorators_table` | Pytest decorator usage stats |
| `GET /api/cases?level=X&device=Y` | Drill-down: test cases matching filter |
| `GET /shutdown` | Gracefully stop the server |

## Export to PDF

```bash
python export_pdf.py
```

This will generate `output/stats.xlsx`, start the dashboard, render it with Playwright, and save `output/dashboard.pdf`.

On first use you may need to install the browser runtime:
```bash
python -m playwright install chromium
```

## Skip Policy

| Context | `@pytest.mark.skip` handling |
|---------|------------------------------|
| Main charts (Level x Device, Top Dirs) | **Excluded** |
| Quality analysis (A/B/C) | **Included** |
| Excel `cases` sheet | **Included** (all tests listed) |

## License

MIT
