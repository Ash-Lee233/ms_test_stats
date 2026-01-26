"""
Author: Shawny
"""
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

    @app.get("/api/level_device")
    def api_level_device():
        df_level_device = pd.read_excel(excel, sheet_name="summary_level_device")
        df_level = pd.read_excel(excel, sheet_name="summary_level")

        df_level_device = df_level_device[df_level_device["level"] != UNMARKED_LEVEL]
        df_level = df_level[df_level["level"] != UNMARKED_LEVEL]

        levels = df_level["level"].tolist()
        pivot = (df_level_device
                 .pivot_table(index="level", columns="device", values="cases", aggfunc="sum", fill_value=0)
                 .reindex(levels, fill_value=0))

        devices = _order_devices(pivot.columns)
        series = [{"name": d, "data": pivot[d].astype(int).tolist()} for d in devices]

        return jsonify({"levels": levels, "devices": devices, "series": series})

    @app.get("/api/dir_top")
    def api_dir_top():
        df = pd.read_excel(excel, sheet_name="summary_dir_top").head(20)
        return jsonify({"dirs": df["dir_group"].tolist(), "totals": [int(x) for x in df["total"].tolist()]})

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

        return jsonify({"grades": grades, "overall": overall, "levels": levels, "series": series})

    @app.get("/api/quality_owner_table")
    def api_quality_owner_table():
        df = pd.read_excel(excel, sheet_name="summary_quality_owner_subdir")
        # Expect columns: owner_top, owner_subdir, quality_grade, cases (fallback supported)
        if "owner_subdir" not in df.columns and "owner" in df.columns:
            df["owner_subdir"] = df["owner"]
        if "owner_top" not in df.columns and "owner_subdir" in df.columns:
            df["owner_top"] = df["owner_subdir"].astype(str).str.split("/", n=1).str[0]
        def second_level(s: str) -> str:
            if not isinstance(s, str):
                return ""
            parts = s.split("/", 1)
            return parts[1] if len(parts) == 2 else ""

        df = df.copy()
        df["owner_second"] = df["owner_subdir"].map(second_level)
        pivot = df.pivot_table(index=["owner_top", "owner_second"], columns="quality_grade", values="cases", aggfunc="sum", fill_value=0)
        grades = _order_grades(pivot.columns)

        rows = []
        for (top, second), rowv in pivot.iterrows():
            row = {"owner_top": top, "owner_sub": second}
            total = 0
            for g in grades:
                v = int(rowv[g]) if g in pivot.columns else 0
                row[g] = v
                total += v
            row["total"] = total
            rows.append(row)

        return jsonify({"grades": grades, "rows": rows})

    @app.get("/api/pytest_decorators_table")
    def api_pytest_decorators_table():
        df = pd.read_excel(excel, sheet_name="summary_pytest_decorators")
        return jsonify({"rows": df.to_dict(orient="records")})


    @app.get("/shutdown")
    def shutdown():
        # For local automation only
        func = None
        try:
            from flask import request
            func = request.environ.get("werkzeug.server.shutdown")
        except Exception:
            func = None
        if func:
            func()
            return "shutting down"
        return "shutdown not available", 500

    return app
