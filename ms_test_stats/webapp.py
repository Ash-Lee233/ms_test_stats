"""
Author: Shawny
"""
from pathlib import Path
from flask import Flask, jsonify, render_template, request

from ms_test_stats.data_service import (
    fetch_level_device,
    fetch_dir_top,
    fetch_quality,
    fetch_quality_owner_table,
    fetch_pytest_decorators,
    fetch_cases_by_level_device,
    fetch_cases_by_level_grade,
)


def create_app(excel_path: str) -> Flask:
    app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent.parent / "templates"))
    excel = str(Path(excel_path))

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/level_device")
    def api_level_device():
        return jsonify(fetch_level_device(excel))

    @app.get("/api/dir_top")
    def api_dir_top():
        return jsonify(fetch_dir_top(excel))

    @app.get("/api/quality")
    def api_quality():
        return jsonify(fetch_quality(excel))

    @app.get("/api/quality_owner_table")
    def api_quality_owner_table():
        return jsonify(fetch_quality_owner_table(excel))

    @app.get("/api/pytest_decorators_table")
    def api_pytest_decorators_table():
        return jsonify(fetch_pytest_decorators(excel))

    @app.get("/api/cases")
    def api_cases():
        level = request.args.get("level", "")
        device = request.args.get("device", "")
        return jsonify(fetch_cases_by_level_device(excel, level, device))

    @app.get("/api/cases_quality")
    def api_cases_quality():
        level = request.args.get("level", "")
        grade = request.args.get("grade", "")
        return jsonify(fetch_cases_by_level_grade(excel, level, grade))

    @app.get("/shutdown")
    def shutdown():
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
