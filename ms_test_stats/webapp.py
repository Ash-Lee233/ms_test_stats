from pathlib import Path
import pandas as pd
from flask import Flask, jsonify, render_template

UNMARKED_LEVEL = "unmarked"

def create_app(excel_path: str) -> Flask:
    app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent.parent / "templates"))
    excel = Path(excel_path)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/summary")
    def api_summary():
        df_level = pd.read_excel(excel, sheet_name="summary_level")
        df_level_device = pd.read_excel(excel, sheet_name="summary_level_device")

        # Exclude 'unmarked' from charts only
        df_level = df_level[df_level["level"] != UNMARKED_LEVEL]
        df_level_device = df_level_device[df_level_device["level"] != UNMARKED_LEVEL]

        levels = df_level["level"].tolist()
        totals = df_level["total_cases"].tolist()

        pivot = (df_level_device
                 .pivot_table(index="level", columns="device", values="cases", aggfunc="sum", fill_value=0)
                 .reindex(levels, fill_value=0))

        devices = sorted(list(pivot.columns),
                         key=lambda x: ["cpu", "gpu", "npu", "unknown"].index(x)
                         if x in ["cpu","gpu","npu","unknown"] else 999)

        series = [{"name": d, "data": pivot[d].astype(int).tolist()} for d in devices]

        return jsonify({
            "levels": levels,
            "totals": [int(x) for x in totals],
            "devices": devices,
            "series": series
        })

    @app.get("/api/dir_top")
    def api_dir_top():
        df_cases = pd.read_excel(excel, sheet_name="cases")
        top = (df_cases.groupby("dir_group", as_index=False)
                      .agg(total=("test", "count"))
                      .sort_values("total", ascending=False)
                      .head(20))
        return jsonify({
            "dirs": top["dir_group"].tolist(),
            "totals": [int(x) for x in top["total"].tolist()]
        })

    return app
