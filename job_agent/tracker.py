# tracker.py
import csv
from datetime import date
from pathlib import Path

from config import BASE_DIR

APPLIED_FILE = BASE_DIR / "applied.csv"

_FIELDS = ["date", "title", "company", "location", "source", "score", "reason", "status", "link"]


def log_application(job):
    """Append one row to applied.csv when a CV is generated."""
    first_write = not APPLIED_FILE.exists()
    with open(APPLIED_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS, extrasaction="ignore")
        if first_write:
            writer.writeheader()
        writer.writerow({
            "date":     date.today().isoformat(),
            "title":    job.get("title", ""),
            "company":  job.get("company", ""),
            "location": job.get("location", ""),
            "source":   job.get("source", ""),
            "score":    job.get("score", ""),
            "reason":   job.get("reason", ""),
            "status":   "applied",
            "link":     job.get("link", ""),
        })
    print(f"Logged to applied.csv  →  {job.get('company')} / {job.get('title')}")


def load_applied():
    """Return all rows from applied.csv as a list of dicts."""
    if not APPLIED_FILE.exists():
        return []
    with open(APPLIED_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_applied_links():
    """Return the set of job links already in applied.csv."""
    return {row["link"] for row in load_applied()}
