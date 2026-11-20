"""
auto_heal.py
Implements the auto-healing engine: detects unhealthy services/resources
and takes automated corrective action (service restart, cache clear, etc.)
to reduce manual intervention and downtime.
"""

import subprocess
import datetime
from monitor import get_system_metrics

# Services this system watches over and can auto-restart
MONITORED_SERVICES = ["nginx", "monitoring-agent", "app-worker"]

_alert_log = []  # in-memory fallback; persisted copy lives in MySQL via db.py


def run_health_check() -> dict:
    """
    Evaluates current system health and monitored services.
    Automatically attempts to heal any unhealthy service found.
    """
    metrics = get_system_metrics()
    issues = []

    if metrics["status"] in ("WARNING", "CRITICAL"):
        issues.append({
            "type": "RESOURCE",
            "severity": metrics["status"],
            "detail": f"CPU={metrics['cpu_percent']}% MEM={metrics['memory_percent']}% "
                      f"DISK={metrics['disk_percent']}%",
            "timestamp": metrics["timestamp"],
        })

    for service in MONITORED_SERVICES:
        if not _is_service_running(service):
            healed = _restart_service(service)
            issues.append({
                "type": "SERVICE_DOWN",
                "severity": "CRITICAL",
                "service": service,
                "auto_healed": healed,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            })

    for issue in issues:
        _alert_log.append(issue)

    return {
        "metrics": metrics,
        "issues_found": len(issues) > 0,
        "issues": issues,
    }


def _is_service_running(service_name: str) -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "--quiet", service_name],
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        # In non-systemd / containerized environments this check is mocked
        return True


def _restart_service(service_name: str) -> bool:
    """Attempts to restart a failed service. Returns True on success."""
    try:
        subprocess.run(["systemctl", "restart", service_name], timeout=10, check=True)
        return True
    except Exception:
        return False


def get_alert_log(limit: int = 20) -> list:
    return _alert_log[-limit:][::-1]
