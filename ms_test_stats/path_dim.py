"""
Author: Shawny
"""
from pathlib import Path

def dir_group(file_path: str, tests_root: str) -> str:
    p = Path(file_path).resolve()
    tr = Path(tests_root).resolve()
    try:
        rel = p.relative_to(tr)
        parts = rel.parts
        if len(parts) >= 3:
            return f"{parts[0]}/{parts[1]}"
        if len(parts) >= 2:
            return parts[0]
        return "unknown"
    except Exception:
        return "unknown"

def owner_top(file_path: str, tests_root: str) -> str:
    "Top-level directory under tests/ (e.g. ut, st, perf_test)."
    p = Path(file_path).resolve()
    tr = Path(tests_root).resolve()
    try:
        rel = p.relative_to(tr)
        return rel.parts[0] if rel.parts else "unknown"
    except Exception:
        return "unknown"

def owner_subdir(file_path: str, tests_root: str) -> str:
    "Second-level owner group under tests/ (e.g. ut/python, st/networks)."
    p = Path(file_path).resolve()
    tr = Path(tests_root).resolve()
    try:
        rel = p.relative_to(tr)
        parts = rel.parts
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
        if len(parts) == 1:
            return parts[0]
        return "unknown"
    except Exception:
        return "unknown"
