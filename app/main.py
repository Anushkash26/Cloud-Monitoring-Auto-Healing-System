"""
Cloud Monitoring & Auto-Healing System
----------------------------------------
REST API entry point. Exposes endpoints to fetch live system metrics,
trigger health checks, and view/manage active alerts.

Author: Atharva Shevate
"""
from flask import Flask, jsonify, request, render_template
from monitor import get_system_metrics
from auto_heal import run_health_check
from db import init_db, save_metrics, save_alert, fetch_alerts

app = Flask(__name__)
init_db()


@app.route("/")
def dashboard():
    return render_template("index.html")

@app.route("/api/health", methods=["GET"])
def health():
    """Simple liveness probe for the monitoring service itself."""
    return jsonify({"status": "ok", "service": "cloud-monitoring-autohealing"}), 200


@app.route("/api/metrics", methods=["GET"])
def metrics():
    """
    Returns current CPU, memory, and disk utilization.
    Also persists the snapshot to MySQL for historical trend analysis.
    """
    data = get_system_metrics()
    save_metrics(data)
    return jsonify(data), 200


@app.route("/api/check", methods=["POST"])
def check():
    """
    Runs a full health check against configured services/thresholds.
    If a service is found unhealthy, auto-healing (restart) is triggered
    and an alert is logged and persisted.
    """
    result = run_health_check()
    if result["issues_found"]:
        for issue in result["issues"]:
            save_alert(issue)
    return jsonify(result), 200


@app.route("/api/alerts", methods=["GET"])
def alerts():
    limit = request.args.get("limit", 20, type=int)
    return jsonify(fetch_alerts(limit))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
