"""
db.py
MySQL persistence layer for storing historical metrics and alert events.
"""

import os
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "cloud_monitoring"),
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Creates required tables if they don't already exist."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cpu_percent FLOAT,
                memory_percent FLOAT,
                disk_percent FLOAT,
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type VARCHAR(50),
                severity VARCHAR(20),
                detail TEXT,
                auto_healed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Error:
        # Allows the service to run locally/demo mode even without MySQL configured
        pass


def save_metrics(data: dict):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO metrics (cpu_percent, memory_percent, disk_percent, status) "
            "VALUES (%s, %s, %s, %s)",
            (data["cpu_percent"], data["memory_percent"], data["disk_percent"], data["status"]),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Error:
        pass


def save_alert(issue: dict):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO alerts (type, severity, detail, auto_healed) VALUES (%s, %s, %s, %s)",
            (
                issue.get("type"),
                issue.get("severity"),
                issue.get("detail", issue.get("service", "")),
                issue.get("auto_healed", False),
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Error:
        pass


def fetch_alerts(limit=20):
    """Fetches the latest alerts from MySQL."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM alerts ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )

        alerts = cursor.fetchall()

        cursor.close()
        conn.close()

        return alerts

    except Error as e:
        print("Error fetching alerts:", e)
        return []
