"""
Author: Shawny
"""
import pandas as pd
from typing import Dict, List

from .device_map import devices_from_markers
from .parser import TestCaseMeta
from .path_dim import dir_group, owner_top, owner_subdir
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
        markers_csv = ",".join(sorted(c.markers))
        pytest_decs_csv = ",".join([d for d in c.pytest_decorators if d])
        is_skip = ("skip" in {m.lower() for m in c.markers})
        rows.append({
            "file": c.file_path,
            "dir_group": dir_group(c.file_path, tests_root),
            "owner_top": owner_top(c.file_path, tests_root),
            "owner_subdir": owner_subdir(c.file_path, tests_root),
            "test": c.node_name,
            "level": c.level or "unmarked",
            "devices": ",".join(devs) if devs else "unknown",
            "markers": markers_csv,
            "pytest_decorators": pytest_decs_csv,
            "is_skip": bool(is_skip),
            "assert_count": int(c.assert_count),
            "has_docstring": bool(c.has_docstring),
            "has_parametrize": bool(c.has_parametrize),
            "quality_score": int(q.score),
            "quality_grade": q.grade,
        })

    df_cases_all = pd.DataFrame(rows)

    # Main statistics exclude ONLY @pytest.mark.skip
    df_cases_main = df_cases_all[~df_cases_all["is_skip"]].copy()

    # ---- MAIN summaries (skip removed) ----
    df_level = (df_cases_main.groupby("level", as_index=False)
                .agg(total_cases=("test", "count"))
                .sort_values("level"))

    df_exploded = df_cases_main.copy()
    df_exploded["device"] = df_exploded["devices"].str.split(",")
    df_exploded = df_exploded.explode("device")
    df_exploded["device"] = df_exploded["device"].fillna("unknown")

    df_level_device = (df_exploded.groupby(["level", "device"], as_index=False)
                       .agg(cases=("test", "count"))
                       .sort_values(["level", "device"]))

    df_dir_top = (df_cases_main.groupby("dir_group", as_index=False)
                  .agg(total=("test", "count"))
                  .sort_values("total", ascending=False))

    # ---- QUALITY summaries (NO skipping) ----
    df_quality = (df_cases_all.groupby("quality_grade", as_index=False)
                  .agg(cases=("test", "count"))
                  .sort_values("quality_grade"))

    df_quality_level = (df_cases_all.groupby(["level", "quality_grade"], as_index=False)
                        .agg(cases=("test", "count"))
                        .sort_values(["level", "quality_grade"]))

    # More fine-grained owner for table: owner_subdir
    df_quality_owner = (df_cases_all.groupby(["owner_top", "owner_subdir", "quality_grade"], as_index=False)
                        .agg(cases=("test", "count"))
                        .sort_values(["owner_top", "owner_subdir", "quality_grade"]))

    # ---- pytest decorator stats (count test cases per decorator) ----
    df_dec = df_cases_all[["test", "pytest_decorators"]].copy()
    df_dec["pytest_decorator"] = df_dec["pytest_decorators"].str.split(",")
    df_dec = df_dec.explode("pytest_decorator")
    df_dec["pytest_decorator"] = df_dec["pytest_decorator"].fillna("").str.strip()
    df_dec = df_dec[df_dec["pytest_decorator"] != ""]

    df_pytest_decorators = (df_dec.groupby("pytest_decorator", as_index=False)
                            .agg(
                                occurrences=("pytest_decorator", "count"),
                                unique_test_cases=("test", "nunique"),
                            )
                            .sort_values(["occurrences", "unique_test_cases"], ascending=False))

    return {
        "df_cases_all": df_cases_all,
        "df_level": df_level,
        "df_level_device": df_level_device,
        "df_dir_top": df_dir_top,
        "df_quality": df_quality,
        "df_quality_level": df_quality_level,
        "df_quality_owner": df_quality_owner,
        "df_pytest_decorators": df_pytest_decorators,
    }
