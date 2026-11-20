"""
monitor.py
Collects real-time CPU, memory, and disk metrics from the host system.
"""

import psutil
import datetime

# Thresholds that define "unhealthy" -- tune per deployment
CPU_THRESHOLD = 85.0     # percent
MEMORY_THRESHOLD = 90.0  # percent
DISK_THRESHOLD = 90.0    # percent


def get_system_metrics() -> dict:
    """Collects a single point-in-time snapshot of system resource usage."""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "cpu_percent": cpu,
        "memory_percent": memory.percent,
        "memory_used_gb": round(memory.used / (1024 ** 3), 2),
        "memory_total_gb": round(memory.total / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / (1024 ** 3), 2),
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "status": _evaluate_status(cpu, memory.percent, disk.percent),
    }


def _evaluate_status(cpu: float, mem: float, disk: float) -> str:
    if cpu > CPU_THRESHOLD or mem > MEMORY_THRESHOLD or disk > DISK_THRESHOLD:
        return "CRITICAL"
    if cpu > CPU_THRESHOLD * 0.75 or mem > MEMORY_THRESHOLD * 0.75:
        return "WARNING"
    return "HEALTHY"

if __name__ == "__main__":
    print("Test 1:", _evaluate_status(40, 40, 40))
    print("Test 2:", _evaluate_status(70, 50, 40))
    print("Test 3:", _evaluate_status(90, 50, 40))