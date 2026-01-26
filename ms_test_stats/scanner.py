"""
Author: Shawny
"""
from pathlib import Path
from typing import Iterable, List
from tqdm import tqdm

def iter_py_files(tests_root: Path) -> Iterable[Path]:
    for p in tests_root.rglob("*.py"):
        if p.name.startswith("."):
            continue
        yield p

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")

def collect_sources(tests_root: Path) -> List[tuple[str, str]]:
    items: List[tuple[str, str]] = []
    files = list(iter_py_files(tests_root))
    for f in tqdm(files, desc=f"Scanning {tests_root}"):
        items.append((str(f), read_text(f)))
    return items
