from pathlib import Path
import pandas as pd

def write_excel(path: str,
                df_cases: pd.DataFrame,
                df_level: pd.DataFrame,
                df_level_device: pd.DataFrame,
                df_dir_level: pd.DataFrame,
                df_dir_level_device: pd.DataFrame):

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df_cases.to_excel(w, sheet_name="cases", index=False)
        df_level.to_excel(w, sheet_name="summary_level", index=False)
        df_level_device.to_excel(w, sheet_name="summary_level_device", index=False)
        df_dir_level.to_excel(w, sheet_name="summary_dir_level", index=False)
        df_dir_level_device.to_excel(w, sheet_name="summary_dir_level_device", index=False)
