"""
Author: Shawny
"""
from pathlib import Path
import pandas as pd
import json

UNMARKED_LEVEL = "unmarked"

def _order_devices(cols):
    order = ["cpu", "gpu", "npu", "unknown"]
    return sorted(list(cols), key=lambda x: order.index(x) if x in order else 999)

def _order_grades(cols):
    order = ["A", "B", "C"]
    return sorted(list(cols), key=lambda x: order.index(x) if x in order else 999)

def write_report(excel_path: str, html_path: str) -> None:
    """Generate a static HTML report from Excel data."""
    excel = Path(excel_path)
    out_html = Path(html_path)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    
    # Read data from Excel (same logic as webapp API endpoints)
    df_level_device = pd.read_excel(excel, sheet_name="summary_level_device")
    df_level = pd.read_excel(excel, sheet_name="summary_level")
    
    df_level_device = df_level_device[df_level_device["level"] != UNMARKED_LEVEL]
    df_level = df_level[df_level["level"] != UNMARKED_LEVEL]
    
    levels = df_level["level"].tolist()
    pivot = (df_level_device
             .pivot_table(index="level", columns="device", values="cases", aggfunc="sum", fill_value=0)
             .reindex(levels, fill_value=0))
    
    devices = _order_devices(pivot.columns)
    series_ld = [{"name": d, "data": pivot[d].astype(int).tolist()} for d in devices]
    data_level_device = {"levels": levels, "devices": devices, "series": series_ld}
    
    # Top directories
    df_dir_top = pd.read_excel(excel, sheet_name="summary_dir_top").head(20)
    data_dir_top = {"dirs": df_dir_top["dir_group"].tolist(), "totals": [int(x) for x in df_dir_top["total"].tolist()]}
    
    # Quality data
    df_quality = pd.read_excel(excel, sheet_name="summary_quality")
    df_quality_level = pd.read_excel(excel, sheet_name="summary_quality_level")
    
    grades = _order_grades(df_quality["quality_grade"].tolist())
    qmap = {row["quality_grade"]: int(row["cases"]) for _, row in df_quality.iterrows()}
    overall = [qmap.get(g, 0) for g in grades]
    
    df_quality_level = df_quality_level[df_quality_level["level"] != UNMARKED_LEVEL]
    levels_q = sorted(df_quality_level["level"].unique().tolist())
    pivot_q = (df_quality_level
               .pivot_table(index="level", columns="quality_grade", values="cases", aggfunc="sum", fill_value=0)
               .reindex(levels_q, fill_value=0))
    
    grade_cols = _order_grades(pivot_q.columns)
    series_q = [{"name": g, "data": pivot_q[g].astype(int).tolist()} for g in grade_cols]
    data_quality = {"grades": grades, "overall": overall, "levels": levels_q, "series": series_q}
    
    # Quality owner table
    df_quality_owner = pd.read_excel(excel, sheet_name="summary_quality_owner_subdir")
    if "owner_subdir" not in df_quality_owner.columns and "owner" in df_quality_owner.columns:
        df_quality_owner["owner_subdir"] = df_quality_owner["owner"]
    if "owner_top" not in df_quality_owner.columns and "owner_subdir" in df_quality_owner.columns:
        df_quality_owner["owner_top"] = df_quality_owner["owner_subdir"].astype(str).str.split("/", n=1).str[0]
    
    def second_level(s: str) -> str:
        if not isinstance(s, str):
            return ""
        parts = s.split("/", 1)
        return parts[1] if len(parts) == 2 else ""
    
    df_quality_owner = df_quality_owner.copy()
    df_quality_owner["owner_second"] = df_quality_owner["owner_subdir"].map(second_level)
    pivot_owner = df_quality_owner.pivot_table(index=["owner_top", "owner_second"], columns="quality_grade", values="cases", aggfunc="sum", fill_value=0)
    grades_owner = _order_grades(pivot_owner.columns)
    
    rows_owner = []
    for (top, second), rowv in pivot_owner.iterrows():
        row = {"owner_top": top, "owner_sub": second}
        total = 0
        for g in grades_owner:
            v = int(rowv[g]) if g in pivot_owner.columns else 0
            row[g] = v
            total += v
        row["total"] = total
        rows_owner.append(row)
    
    data_quality_owner = {"grades": grades_owner, "rows": rows_owner}
    
    # Pytest decorators table
    df_pytest = pd.read_excel(excel, sheet_name="summary_pytest_decorators")
    data_pytest = {"rows": df_pytest.to_dict(orient="records")}
    
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
