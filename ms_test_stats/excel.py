from pathlib import Path
import pandas as pd

def write_excel(path: str, **dfs) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(out, engine="openpyxl") as w:
        dfs["df_cases"].to_excel(w, sheet_name="cases", index=False)
        dfs["df_level"].to_excel(w, sheet_name="summary_level", index=False)
        dfs["df_level_device"].to_excel(w, sheet_name="summary_level_device", index=False)
        dfs["df_dir_level"].to_excel(w, sheet_name="summary_dir_level", index=False)
        dfs["df_dir_level_device"].to_excel(w, sheet_name="summary_dir_level_device", index=False)
        dfs["df_quality"].to_excel(w, sheet_name="summary_quality", index=False)
        dfs["df_quality_level"].to_excel(w, sheet_name="summary_quality_level", index=False)
        dfs["df_quality_dir"].to_excel(w, sheet_name="summary_quality_dir", index=False)
