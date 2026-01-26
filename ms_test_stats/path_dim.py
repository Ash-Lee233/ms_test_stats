from pathlib import Path

def dir_group(file_path: str, tests_root: str) -> str:
    """
    Group by directory dimension:
      tests/ut/python/... -> ut/python
      tests/st/...        -> st
    Rule: relative to tests_root, take first 2 path parts (if available).
    """
    p = Path(file_path).resolve()
    tr = Path(tests_root).resolve()

    try:
        rel = p.relative_to(tr)
    except Exception:
        parts = p.parts[-3:-1]
        return "/".join(parts) if parts else "unknown"

    parts = rel.parts
    if len(parts) >= 3:
        return f"{parts[0]}/{parts[1]}"
    if len(parts) >= 2:
        return parts[0]
    return "unknown"
