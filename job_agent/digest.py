"""
Daily job digest — run standalone to get a markdown summary of today's top 5 new jobs.
Uses only keyword scoring (fast, no LLM) so it's cheap to schedule.

    python -m job_agent.digest
    python -m job_agent.digest --silent   # no auto-open, returns job list
"""
import os
import platform
import subprocess
from datetime import date

from scraper import search_jobs
from scorer import score_job
from tracker import load_applied_links
from config import PROJECT_ROOT

DIGEST_FILE = PROJECT_ROOT / "digest.md"


def run(silent: bool = False) -> list[dict]:
    """
    Scrape, keyword-score, and write digest.md.
    Returns the full list of new scored jobs (not just top 5) so callers
    can filter by score threshold for escalation.
    silent=True skips auto-opening the file.
    """
    jobs = search_jobs()

    for job in jobs:
        job["score"] = score_job(job)

    jobs = [
        j for j in jobs
        if j["score"] > 0
        and (
            "madrid" in j["location"].lower()
            or "spain" in j["location"].lower()
        )
    ]

    applied = load_applied_links()
    jobs = [j for j in jobs if j["link"] not in applied]
    jobs.sort(key=lambda x: x["score"], reverse=True)
    top5 = jobs[:5]

    today = date.today().isoformat()
    lines = [f"# Daily Digest — {today}", "", f"{len(jobs)} new relevant jobs found.", ""]

    for i, j in enumerate(top5, 1):
        lines += [
            f"## {i}. {j['title']} — {j['company']}",
            f"**Score:** {j['score']}/10",
            f"**Location:** {j['location']}  ·  **Source:** {j.get('source', '')}",
            f"**Link:** {j['link']}",
            "",
        ]

    DIGEST_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Digest written → digest.md  ({len(top5)} jobs shown, {len(jobs)} total new)")

    if not silent:
        try:
            if platform.system() == "Windows":
                os.startfile(str(DIGEST_FILE))
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(DIGEST_FILE)], check=False)
            else:
                subprocess.run(["xdg-open", str(DIGEST_FILE)], check=False)
        except Exception:
            pass

    return jobs


if __name__ == "__main__":
    import sys
    run(silent="--silent" in sys.argv)
