"""
Author: Shawny
"""
from typing import Dict, Iterable, Set

def devices_from_markers(markers: Iterable[str], device_keywords: Dict[str, list[str]]) -> Set[str]:
    ms = {m.lower() for m in markers}
    out: Set[str] = set()

    for dev, keys in device_keywords.items():
        for m in ms:
            if any(k in m for k in keys):
                out.add(dev)
                break

    return out
