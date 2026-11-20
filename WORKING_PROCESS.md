# Working Process — How This Project Works

This document walks through exactly how the Cloud Monitoring & Auto-Healing System operates, end to end, from the moment it starts up to the moment it heals a failing service.

---

## 1. Startup

1. `docker-compose up --build` builds the Flask app image and pulls the official MySQL image.
2. The `app` container starts, calls `init_db()` from `db.py`, which connects to MySQL and creates the `metrics` and `alerts` tables if they don't already exist.
3. Gunicorn binds the Flask app to port `5000` and the API is ready to receive requests.

---

## 2. Collecting Metrics

- `monitor.py` uses the `psutil` library to read live system stats directly from the OS:
  - CPU utilization (`psutil.cpu_percent`)
  - Memory usage (`psutil.virtual_memory`)
  - Disk usage (`psutil.disk_usage`)
- Each reading is compared against configurable thresholds (`CPU_THRESHOLD`, `MEMORY_THRESHOLD`, `DISK_THRESHOLD`) to classify the system as `HEALTHY`, `WARNING`, or `CRITICAL`.
- Every call to `GET /api/metrics` returns a fresh snapshot **and** writes it to the `metrics` table in MySQL, so history builds up automatically over time.

---

## 3. Health Checks

- `POST /api/check` runs `run_health_check()` in `auto_heal.py`.
- This does two things in one pass:
  1. **Resource check** — re-evaluates CPU/memory/disk against thresholds.
  2. **Service check** — loops through `MONITORED_SERVICES` (e.g. `nginx`, `monitoring-agent`, `app-worker`) and checks whether each is currently running via `systemctl is-active`.

---

## 4. Auto-Healing Decision

For every issue found:

- If it's a **resource issue** (e.g. CPU is critical), it's logged as an alert — resource issues are informational since there's no single "restart" action for high CPU.
- If it's a **service down** issue, the system automatically calls `systemctl restart <service>` to attempt recovery, and records whether the restart succeeded (`auto_healed: true/false`).

This is the core value of the project: **the system doesn't wait for a human to notice and manually restart something — it reacts immediately.**

---

## 5. Alerting & History

- Every issue (resource or service) is appended to the in-memory alert log and persisted to the `alerts` table in MySQL.
- `GET /api/alerts?limit=20` returns the most recent alerts, newest first — useful for a dashboard, a Slack bot, or a nightly report.

---

## 6. Data Flow Summary

```
psutil (OS) 
   → monitor.py (collect + classify) 
   → main.py (REST API layer) 
   → auto_heal.py (evaluate + auto-restart) 
   → db.py (persist metrics + alerts to MySQL)
   → client / dashboard (reads via REST API)
```

---

## 7. Deployment Flow

```
Local code 
   → Docker image (Dockerfile) 
   → docker-compose (app + MySQL together) 
   → AWS EC2 instance (docker-compose up -d)
   → Publicly reachable REST API
```

---

## 8. Extending the Project

Some natural next steps if you want to build on this:

- Swap the in-memory alert log for a real-time feed (e.g. WebSocket) so a dashboard updates live.
- Add a scheduler (cron or `APScheduler`) to call `/api/check` automatically every N seconds instead of relying on manual/external triggers.
- Add notification hooks (Slack/Email) inside `auto_heal.py` right after an issue is detected.
- Replace the hardcoded `MONITORED_SERVICES` list with a config file or database table so services can be added without code changes.
