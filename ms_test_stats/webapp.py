from pathlib import Path
import pandas as pd
from flask import Flask, jsonify, render_template

UNMARKED_LEVEL = "unmarked"

def _order_devices(cols):
    order = ["cpu", "gpu", "npu", "unknown"]
    return sorted(list(cols), key=lambda x: order.index(x) if x in order else 999)

def _order_grades(cols):
    order = ["A", "B", "C"]
    return sorted(list(cols), key=lambda x: order.index(x) if x in order else 999)

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

        df_level = df_level[df_level["level"] != UNMARKED_LEVEL]
        df_level_device = df_level_device[df_level_device["level"] != UNMARKED_LEVEL]

        levels = df_level["level"].tolist()
        totals = df_level["total_cases"].tolist()

        pivot = (df_level_device
                 .pivot_table(index="level", columns="device", values="cases", aggfunc="sum", fill_value=0)
                 .reindex(levels, fill_value=0))

        devices = _order_devices(pivot.columns)
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

    @app.get("/api/quality")
    def api_quality():
        df_quality = pd.read_excel(excel, sheet_name="summary_quality")
        df_quality_level = pd.read_excel(excel, sheet_name="summary_quality_level")

        grades = _order_grades(df_quality["quality_grade"].tolist())
        qmap = {row["quality_grade"]: int(row["cases"]) for _, row in df_quality.iterrows()}
        overall = [qmap.get(g, 0) for g in grades]

        df_quality_level = df_quality_level[df_quality_level["level"] != UNMARKED_LEVEL]
        levels = sorted(df_quality_level["level"].unique().tolist())
        pivot = (df_quality_level
                 .pivot_table(index="level", columns="quality_grade", values="cases", aggfunc="sum", fill_value=0)
                 .reindex(levels, fill_value=0))

        grade_cols = _order_grades(pivot.columns)
        series = [{"name": g, "data": pivot[g].astype(int).tolist()} for g in grade_cols]

        return jsonify({
            "grades": grades,
            "overall": overall,
            "levels": levels,
            "series": series
        })

    return app
