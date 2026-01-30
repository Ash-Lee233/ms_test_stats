"""
Author: Shawny
"""
from concurrent.futures import ThreadPoolExecutor
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

def _read_one(path: Path) -> tuple[str, str]:
    return (str(path), read_text(path))

def collect_sources(tests_root: Path) -> List[tuple[str, str]]:
    files = list(iter_py_files(tests_root))
    items: List[tuple[str, str]] = []
    with ThreadPoolExecutor() as pool:
        for result in tqdm(pool.map(_read_one, files), total=len(files), desc=f"Scanning {tests_root}"):
            items.append(result)
    return items
