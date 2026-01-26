import pandas as pd
from typing import Dict, List

from .device_map import devices_from_markers
from .parser import TestCaseMeta
from .path_dim import dir_group
from .quality import score_test_case

def build_dataframes(cases: List[TestCaseMeta],
                     device_keywords: Dict[str, list[str]],
                     tests_root: str):
    rows = []
    for c in cases:
        devs = sorted(devices_from_markers(c.markers, device_keywords))
        q = score_test_case(
            assert_count=c.assert_count,
            has_parametrize=c.has_parametrize,
            has_docstring=c.has_docstring,
            markers=c.markers,
        )
        rows.append({
            "file": c.file_path,
            "dir_group": dir_group(c.file_path, tests_root),
            "test": c.node_name,
            "level": c.level or "unmarked",
            "devices": ",".join(devs) if devs else "unknown",
            "markers": ",".join(sorted(c.markers)),
            "assert_count": int(c.assert_count),
            "has_docstring": bool(c.has_docstring),
            "has_parametrize": bool(c.has_parametrize),
            "quality_score": int(q.score),
            "quality_grade": q.grade,
        })

    df_cases = pd.DataFrame(rows)

    df_level = (df_cases.groupby("level", as_index=False)
                .agg(total_cases=("test", "count"))
                .sort_values("level"))

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

    df_quality = (df_cases.groupby("quality_grade", as_index=False)
                  .agg(cases=("test", "count"))
                  .sort_values("quality_grade"))

    df_quality_level = (df_cases.groupby(["level", "quality_grade"], as_index=False)
                        .agg(cases=("test", "count"))
                        .sort_values(["level", "quality_grade"]))

    df_quality_dir = (df_cases.groupby(["dir_group", "quality_grade"], as_index=False)
                      .agg(cases=("test", "count"))
                      .sort_values(["dir_group", "quality_grade"]))

    return {
        "df_cases": df_cases,
        "df_level": df_level,
        "df_level_device": df_level_device,
        "df_dir_level": df_dir_level,
        "df_dir_level_device": df_dir_level_device,
        "df_quality": df_quality,
        "df_quality_level": df_quality_level,
        "df_quality_dir": df_quality_dir,
    }
