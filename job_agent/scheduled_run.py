"""
Phase 9 — Autonomous scheduled run.

Runs the daily digest (keyword-only, no LLM) + Gmail reply scan silently.
Escalates to notifications.md only when:
  - A job scores >= 8 (high-score alert)
  - A reply from a company is detected (interview / offer / rejected)

Schedule with Windows Task Scheduler:
    Action: python C:\\...\\job_agent\\scheduled_run.py
    Trigger: Daily at preferred time

Or run manually:
    python -m job_agent.scheduled_run
"""
from datetime import date

from config import NOTIFICATIONS_FILE
from digest import run as run_digest
from gmail_monitor import scan_replies, update_statuses

_MIN_SCORE = 8


def _notify(title: str, body: str) -> None:
    existing = ""
    if NOTIFICATIONS_FILE.exists():
        existing = NOTIFICATIONS_FILE.read_text(encoding="utf-8")

    entry = f"## {date.today().isoformat()} — {title}\n\n{body}\n\n---\n\n"
    NOTIFICATIONS_FILE.write_text(entry + existing, encoding="utf-8")

    try:
        from plyer import notification
        notification.notify(title=f"Job Agent: {title}", message=body[:200], timeout=10)
    except Exception:
        pass


def run() -> None:
    escalated = False

    # --- Daily digest (silent, no auto-open) ---
    jobs = run_digest(silent=True)

    high_score = [j for j in jobs if j.get("score", 0) >= _MIN_SCORE]
    if high_score:
        lines = [
            f"- **{j['title']}** at {j['company']} — {j['score']}/10  \n  {j['link']}"
            for j in high_score
        ]
        _notify(
            f"{len(high_score)} high-score job(s) found",
            "\n".join(lines),
        )
        escalated = True

    # --- Gmail reply scan ---
    replies = scan_replies()
    update_statuses(replies)

    for reply in replies:
        status_label = {"interview": "Interview invitation", "offer": "Job offer", "rejected": "Rejection"}.get(
            reply["status"], reply["status"].title()
        )
        _notify(
            f"{status_label} — {reply['company']}",
            f"**{reply['title']}**\nSubject: {reply['subject']}\nStatus updated to: **{reply['status']}**",
        )
        escalated = True

    if not escalated:
        print(f"[{date.today().isoformat()}] Scheduled run complete — nothing to escalate.")
    else:
        print(f"[{date.today().isoformat()}] Notifications written → notifications.md")


if __name__ == "__main__":
    run()
