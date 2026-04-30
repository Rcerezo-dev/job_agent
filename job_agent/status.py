# status.py  —  run with: python job_agent/status.py
import csv
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

from config import BASE_DIR, CSV_FILE
from tracker import APPLIED_FILE, load_applied

_W = 60  # total display width

STATUS_ORDER = ["applied", "interview", "offer", "rejected"]
STATUS_ICON  = {"applied": "📨", "interview": "🗣️ ", "offer": "🎉", "rejected": "✗"}


def _load_jobs_csv():
    if not Path(CSV_FILE).exists():
        return []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _last_modified(path):
    if not Path(path).exists():
        return "—"
    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _bar(n, total, width=20):
    filled = round(n / total * width) if total else 0
    return "█" * filled + "░" * (width - filled)


def main():
    applied = load_applied()
    jobs    = _load_jobs_csv()

    print("=" * _W)
    print(" JOB AGENT — STATUS".center(_W))
    print("=" * _W)

    # ── Last scrape ───────────────────────────────────────────────
    print(f"\n  Last scrape   {_last_modified(CSV_FILE)}")
    print(f"  Jobs found    {len(jobs)}")
    print(f"  Applications  {len(applied)}")

    if not applied:
        print("\n  No applications logged yet. Run main.py and choose a job.\n")
        print("=" * _W)
        return

    # ── Pipeline breakdown ────────────────────────────────────────
    counts = Counter(row["status"] for row in applied)
    total  = len(applied)

    print(f"\n  {'PIPELINE':}")
    print(f"  {'─' * (_W - 4)}")
    for status in STATUS_ORDER:
        n    = counts.get(status, 0)
        icon = STATUS_ICON.get(status, "  ")
        bar  = _bar(n, total)
        print(f"  {icon} {status:<12} {bar}  {n}")

    # ── Application history ───────────────────────────────────────
    print(f"\n  {'HISTORY':}")
    print(f"  {'─' * (_W - 4)}")
    col = {"date": 12, "company": 22, "role": 22, "status": 10}
    header = (
        f"  {'Date':<{col['date']}}"
        f"{'Company':<{col['company']}}"
        f"{'Role':<{col['role']}}"
        f"{'Status':<{col['status']}}"
    )
    print(header)
    print(f"  {'─' * (col['date'] + col['company'] + col['role'] + col['status'])}")

    for row in sorted(applied, key=lambda r: r["date"], reverse=True):
        line = (
            f"  {row['date']:<{col['date']}}"
            f"{row['company'][:col['company']-1]:<{col['company']}}"
            f"{row['title'][:col['role']-1]:<{col['role']}}"
            f"{row['status']:<{col['status']}}"
        )
        print(line)

    print("=" * _W)


if __name__ == "__main__":
    main()
