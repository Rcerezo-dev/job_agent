# tracker.py
import csv
import re
from datetime import date
from pathlib import Path

from config import DATA_DIR, APPLICATIONS_DIR

APPLIED_FILE = DATA_DIR / "applied.csv"

_FIELDS = ["date", "title", "company", "location", "source", "score", "reason", "salary", "status", "link", "folder_path"]


def _slug(text, max_len=40):
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text.strip())
    return text[:max_len].rstrip("-")


def create_app_folder(job):
    """Create applications/YYYY-MM-DD_Company_Role/ and write job_offer.md + notes.md."""
    today   = date.today().isoformat()
    company = _slug(job.get("company", "Unknown"))
    role    = _slug(job.get("title",   "Role"))
    folder  = APPLICATIONS_DIR / f"{today}_{company}_{role}"
    folder.mkdir(parents=True, exist_ok=True)

    job_offer_md = f"""# {job.get("title", "")} — {job.get("company", "")}

**Source:** {job.get("source", "")}
**Location:** {job.get("location", "")}
**Score:** {job.get("score", "")}/10
**Reason:** {job.get("reason", "")}
**Link:** {job.get("link", "")}

---

## Job Description

{job.get("real_description", job.get("description", ""))}
"""
    (folder / "job_offer.md").write_text(job_offer_md, encoding="utf-8")
    (folder / "notes.md").write_text("# Notes\n\n## Interview notes\n\n\n## Follow-up\n\n", encoding="utf-8")

    print(f"Application folder: applications/{folder.name}/")
    return folder


def log_application(job, folder_path=""):
    """Append one row to applied.csv when a CV is generated."""
    first_write = not APPLIED_FILE.exists()
    with open(APPLIED_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS, extrasaction="ignore")
        if first_write:
            writer.writeheader()
        writer.writerow({
            "date":        date.today().isoformat(),
            "title":       job.get("title", ""),
            "company":     job.get("company", ""),
            "location":    job.get("location", ""),
            "source":      job.get("source", ""),
            "score":       job.get("score", ""),
            "reason":      job.get("reason", ""),
            "status":      "applied",
            "link":        job.get("link", ""),
            "folder_path": str(folder_path),
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
