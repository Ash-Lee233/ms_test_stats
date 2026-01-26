import pandas as pd
from typing import Dict, List

from .device_map import devices_from_markers
from .parser import TestCaseMeta
from .path_dim import dir_group

def build_dataframes(cases: List[TestCaseMeta],
                     device_keywords: Dict[str, list[str]],
                     tests_root: str):

    rows = []
    for c in cases:
        devs = sorted(devices_from_markers(c.markers, device_keywords))
        rows.append({
            "file": c.file_path,
            "dir_group": dir_group(c.file_path, tests_root),
            "test": c.node_name,
            "level": c.level or "unmarked",
            "devices": ",".join(devs) if devs else "unknown",
            "markers": ",".join(sorted(c.markers)),
        })

    df_cases = pd.DataFrame(rows)

    df_level = (df_cases.groupby("level", as_index=False)
                .agg(total_cases=("test", "count"))
                .sort_values("level"))

    # explode device labels to allow multi-device counting
    df_exploded = df_cases.copy()
    df_exploded["device"] = df_exploded["devices"].str.split(",")
    df_exploded = df_exploded.explode("device")
    df_exploded["device"] = df_exploded["device"].fillna("unknown")

    df_level_device = (df_exploded.groupby(["level", "device"], as_index=False)
                       .agg(cases=("test", "count"))
                       .sort_values(["level", "device"]))

    df_dir_level = (df_cases.groupby(["dir_group", "level"], as_index=False)
                    .agg(total_cases=("test", "count"))
                    .sort_values(["dir_group", "level"]))

    df_dir_level_device = (df_exploded.groupby(["dir_group", "level", "device"], as_index=False)
                           .agg(cases=("test", "count"))
                           .sort_values(["dir_group", "level", "device"]))

    return df_cases, df_level, df_level_device, df_dir_level, df_dir_level_device
