"""
Author: Shawny
"""
from pathlib import Path
from typing import Optional, Tuple


def _rel_parts(file_path: str, tests_root: str) -> Optional[Tuple[str, ...]]:
    """Return relative path parts from tests_root, or None on failure."""
    try:
        rel = Path(file_path).resolve().relative_to(Path(tests_root).resolve())
        return rel.parts if rel.parts else None
    except Exception:
        return None


def dir_group(file_path: str, tests_root: str) -> str:
    parts = _rel_parts(file_path, tests_root)
    if parts is None:
        return "unknown"
    if len(parts) >= 3:
        return f"{parts[0]}/{parts[1]}"
    if len(parts) >= 2:
        return parts[0]
    return "unknown"


def owner_top(file_path: str, tests_root: str) -> str:
    "Top-level directory under tests/ (e.g. ut, st, perf_test)."
    parts = _rel_parts(file_path, tests_root)
    return parts[0] if parts else "unknown"


def owner_subdir(file_path: str, tests_root: str) -> str:
    "Second-level owner group under tests/ (e.g. ut/python, st/networks)."
    parts = _rel_parts(file_path, tests_root)
    if parts is None:
        return "unknown"
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]
