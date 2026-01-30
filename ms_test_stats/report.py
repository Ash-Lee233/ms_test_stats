"""
Author: Shawny
"""
from pathlib import Path
import json

from ms_test_stats.data_service import (
    fetch_level_device,
    fetch_dir_top,
    fetch_quality,
    fetch_quality_owner_table,
    fetch_pytest_decorators,
)


def write_report(excel_path: str, html_path: str) -> None:
    """Generate a static HTML report from Excel data."""
    out_html = Path(html_path)
    out_html.parent.mkdir(parents=True, exist_ok=True)

    data_level_device = fetch_level_device(excel_path)
    data_dir_top = fetch_dir_top(excel_path)
    data_quality = fetch_quality(excel_path)
    data_quality_owner = fetch_quality_owner_table(excel_path)
    data_pytest = fetch_pytest_decorators(excel_path)

    # Generate HTML with inline data
    html_template = Path(__file__).resolve().parent.parent / "templates" / "index.html"
    html_content = html_template.read_text(encoding="utf-8")

    # Replace API calls with inline data
    html_content = html_content.replace(
        'const ld = await (await fetch("/api/level_device")).json();',
        f'const ld = {json.dumps(data_level_device)};'
    )
    html_content = html_content.replace(
        'const d2 = await (await fetch("/api/dir_top")).json();',
        f'const d2 = {json.dumps(data_dir_top)};'
    )
    html_content = html_content.replace(
        'const q = await (await fetch("/api/quality")).json();',
        f'const q = {json.dumps(data_quality)};'
    )
    html_content = html_content.replace(
        'const qt = await (await fetch("/api/quality_owner_table")).json();',
        f'const qt = {json.dumps(data_quality_owner)};'
    )
    html_content = html_content.replace(
        'const pt = await (await fetch("/api/pytest_decorators_table")).json();',
        f'const pt = {json.dumps(data_pytest)};'
    )

    # Remove async/await since we're using inline data
    html_content = html_content.replace('async function main() {', 'function main() {')

    out_html.write_text(html_content, encoding="utf-8")
