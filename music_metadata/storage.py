from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path


def reserve_daily_analysis(limit: int, path: str = "data/usage.db") -> tuple[bool, int]:
    """Atomically reserve one analysis from the app-wide daily allowance."""
    database = Path(path)
    database.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    with sqlite3.connect(database, timeout=10) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS daily_usage (usage_date TEXT PRIMARY KEY, analysis_count INTEGER NOT NULL)"
        )
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT analysis_count FROM daily_usage WHERE usage_date = ?", (today,)
        ).fetchone()
        current = int(row[0]) if row else 0
        if current >= limit:
            connection.rollback()
            return False, current
        updated = current + 1
        connection.execute(
            "INSERT INTO daily_usage(usage_date, analysis_count) VALUES (?, ?) "
            "ON CONFLICT(usage_date) DO UPDATE SET analysis_count = excluded.analysis_count",
            (today, updated),
        )
        connection.commit()
        return True, updated
