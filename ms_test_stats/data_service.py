"""
Author: Shawny
Shared data layer for webapp and report — reads Excel once and caches.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

UNMARKED_LEVEL = "unmarked"

# ---------------------------------------------------------------------------
# Module-level cache: keyed by (excel_path, mtime)
# ---------------------------------------------------------------------------
_cache: Dict[str, Tuple[float, Dict[str, pd.DataFrame]]] = {}


def _load_sheets(excel_path: str) -> Dict[str, pd.DataFrame]:
    """Return all relevant sheets, using a cache invalidated by file mtime."""
    mtime = os.path.getmtime(excel_path)
    cached = _cache.get(excel_path)
    if cached is not None and cached[0] == mtime:
        return cached[1]

    sheets = {
        name: pd.read_excel(excel_path, sheet_name=name)
        for name in [
            "cases",
            "summary_level_device",
            "summary_level",
            "summary_dir_top",
            "summary_quality",
            "summary_quality_level",
            "summary_quality_owner_subdir",
            "summary_pytest_decorators",
        ]
    }
    _cache[excel_path] = (mtime, sheets)
    return sheets


# ---------------------------------------------------------------------------
# Ordering helpers
# ---------------------------------------------------------------------------

def _order_devices(cols):
    order = ["cpu", "gpu", "npu", "unknown"]
    return sorted(list(cols), key=lambda x: order.index(x) if x in order else 999)


def _order_grades(cols):
    order = ["A", "B", "C"]
    return sorted(list(cols), key=lambda x: order.index(x) if x in order else 999)


# ---------------------------------------------------------------------------
# Data-fetching functions (each returns a plain dict)
# ---------------------------------------------------------------------------

def fetch_level_device(excel_path: str) -> Dict[str, Any]:
    sheets = _load_sheets(excel_path)
    df_level_device = sheets["summary_level_device"]
    df_level = sheets["summary_level"]

    df_level_device = df_level_device[df_level_device["level"] != UNMARKED_LEVEL]
    df_level = df_level[df_level["level"] != UNMARKED_LEVEL]

    levels = df_level["level"].tolist()
    pivot = (
        df_level_device
        .pivot_table(index="level", columns="device", values="cases", aggfunc="sum", fill_value=0)
        .reindex(levels, fill_value=0)
    )

    devices = _order_devices(pivot.columns)
    series = [{"name": d, "data": pivot[d].astype(int).tolist()} for d in devices]

    return {"levels": levels, "devices": devices, "series": series}


def fetch_dir_top(excel_path: str) -> Dict[str, Any]:
    sheets = _load_sheets(excel_path)
    df = sheets["summary_dir_top"].head(20)
    return {
        "dirs": df["dir_group"].tolist(),
        "totals": [int(x) for x in df["total"].tolist()],
    }


def fetch_quality(excel_path: str) -> Dict[str, Any]:
    sheets = _load_sheets(excel_path)
    df_quality = sheets["summary_quality"]
    df_quality_level = sheets["summary_quality_level"]

    grades = _order_grades(df_quality["quality_grade"].tolist())
    qmap = df_quality.set_index("quality_grade")["cases"].astype(int).to_dict()
    overall = [qmap.get(g, 0) for g in grades]

    df_quality_level = df_quality_level[df_quality_level["level"] != UNMARKED_LEVEL]
    levels = sorted(df_quality_level["level"].unique().tolist())
    pivot = (
        df_quality_level
        .pivot_table(index="level", columns="quality_grade", values="cases", aggfunc="sum", fill_value=0)
        .reindex(levels, fill_value=0)
    )

    grade_cols = _order_grades(pivot.columns)
    series = [{"name": g, "data": pivot[g].astype(int).tolist()} for g in grade_cols]

    return {"grades": grades, "overall": overall, "levels": levels, "series": series}


def fetch_quality_owner_table(excel_path: str) -> Dict[str, Any]:
    sheets = _load_sheets(excel_path)
    df = sheets["summary_quality_owner_subdir"].copy()

    if "owner_subdir" not in df.columns and "owner" in df.columns:
        df["owner_subdir"] = df["owner"]
    if "owner_top" not in df.columns and "owner_subdir" in df.columns:
        df["owner_top"] = df["owner_subdir"].astype(str).str.split("/", n=1).str[0]

    def second_level(s: str) -> str:
        if not isinstance(s, str):
            return ""
        parts = s.split("/", 1)
        return parts[1] if len(parts) == 2 else ""

    df["owner_second"] = df["owner_subdir"].map(second_level)
    pivot = df.pivot_table(
        index=["owner_top", "owner_second"],
        columns="quality_grade",
        values="cases",
        aggfunc="sum",
        fill_value=0,
    )
    grades = _order_grades(pivot.columns)

    rows = []
    for (top, second), rowv in pivot.iterrows():
        row = {"owner_top": top, "owner_sub": second}
        total = 0
        for g in grades:
            v = int(rowv[g]) if g in pivot.columns else 0
            row[g] = v
            total += v
        row["total"] = total
        rows.append(row)

    return {"grades": grades, "rows": rows}


def fetch_pytest_decorators(excel_path: str) -> Dict[str, Any]:
    sheets = _load_sheets(excel_path)
    df = sheets["summary_pytest_decorators"]
    return {"rows": df.to_dict(orient="records")}


def fetch_cases_by_level_device(excel_path: str, level: str, device: str) -> Dict[str, Any]:
    """Return test cases matching a specific level and device (skip excluded)."""
    sheets = _load_sheets(excel_path)
    df = sheets["cases"]
    # Exclude skipped tests (same filter as the Level×Device chart)
    df = df[~df["is_skip"]]
    # Filter by level
    df = df[df["level"] == level]
    # Filter by device — the devices column is comma-separated
    df = df[df["devices"].str.contains(device, na=False)]

    rows = df[["dir_group", "test", "level", "devices"]].to_dict(orient="records")
    return {"level": level, "device": device, "total": len(rows), "rows": rows}


def fetch_cases_by_level_grade(excel_path: str, level: str, grade: str) -> Dict[str, Any]:
    """Return test cases matching a specific level and quality grade (no skip filter)."""
    sheets = _load_sheets(excel_path)
    df = sheets["cases"]
    df = df[df["level"] == level]
    df = df[df["quality_grade"] == grade]

    rows = df[["dir_group", "test", "level", "quality_grade", "quality_score"]].to_dict(orient="records")
    return {"level": level, "grade": grade, "total": len(rows), "rows": rows}
