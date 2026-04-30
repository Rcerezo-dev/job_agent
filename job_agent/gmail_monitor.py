"""
Phase 9 — Gmail reply monitor.

Connects to Gmail via IMAP, scans recent emails for replies from companies
in applied.csv, classifies them (interview / rejected / offer), and updates
applied.csv status accordingly.

Requires in .env:
    GMAIL_USER=you@gmail.com
    GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx   # Gmail App Password (not your main password)

Enable IMAP: Gmail settings → See all settings → Forwarding and POP/IMAP → Enable IMAP.
Create App Password: myaccount.google.com → Security → 2-Step Verification → App passwords.
"""
import csv
import email
import imaplib
from datetime import date, timedelta

from config import DATA_DIR, GMAIL_USER, GMAIL_APP_PASSWORD
from tracker import APPLIED_FILE, load_applied

_DAYS_BACK = 14

_OFFER_WORDS     = ["offer letter", "oferta de trabajo", "job offer", "propuesta laboral", "oferta formal"]
_INTERVIEW_WORDS = ["interview", "entrevista", "prueba técnica", "technical test",
                    "technical assessment", "llamada", "videollamada", "meet", "screening"]
_REJECTION_WORDS = ["unfortunately", "lamentablemente", "not selected", "no seguirás",
                    "descartado", "rejected", "no avanzarás", "no hemos podido",
                    "we will not", "not moving forward", "other candidates"]


def _classify(subject: str, body: str) -> str:
    text = (subject + " " + body).lower()
    for kw in _OFFER_WORDS:
        if kw in text:
            return "offer"
    for kw in _INTERVIEW_WORDS:
        if kw in text:
            return "interview"
    for kw in _REJECTION_WORDS:
        if kw in text:
            return "rejected"
    return ""


def _match_company(text: str, companies: list[str]) -> str:
    text_lower = text.lower()
    for company in companies:
        if company.lower() in text_lower:
            return company
    return ""


def _body_text(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(errors="ignore")[:600]
                except Exception:
                    return ""
    try:
        return msg.get_payload(decode=True).decode(errors="ignore")[:600]
    except Exception:
        return ""


def scan_replies() -> list[dict]:
    """
    Scan Gmail inbox for replies from companies in applied.csv.
    Returns a list of dicts: {company, title, link, subject, status}.
    Returns [] if Gmail is not configured or no matches found.
    """
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("Gmail not configured — add GMAIL_USER and GMAIL_APP_PASSWORD to .env")
        return []

    apps = load_applied()
    if not apps:
        return []

    companies = [r["company"] for r in apps if r.get("company")]
    company_to_app = {r["company"]: r for r in apps}

    since = (date.today() - timedelta(days=_DAYS_BACK)).strftime("%d-%b-%Y")

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("inbox")

        _, uids = mail.search(None, f"SINCE {since}")
        events = []

        for uid in (uids[0].split() if uids[0] else []):
            _, data = mail.fetch(uid, "(RFC822)")
            if not data or not data[0]:
                continue
            msg     = email.message_from_bytes(data[0][1])
            subject = msg.get("Subject", "")
            sender  = msg.get("From", "")
            body    = _body_text(msg)

            status = _classify(subject, body)
            if not status:
                continue

            company = _match_company(subject + " " + sender + " " + body, companies)
            if not company:
                continue

            app = company_to_app[company]
            events.append({
                "company": company,
                "title":   app.get("title", ""),
                "link":    app.get("link", ""),
                "subject": subject,
                "status":  status,
            })

        mail.logout()
        return events

    except imaplib.IMAP4.error as exc:
        print(f"Gmail login failed: {exc}")
        return []
    except Exception as exc:
        print(f"Gmail scan error: {exc}")
        return []


def update_statuses(events: list[dict]) -> int:
    """
    Write detected reply statuses back to applied.csv.
    Returns the number of rows updated.
    """
    if not events or not APPLIED_FILE.exists():
        return 0

    with open(APPLIED_FILE, encoding="utf-8") as f:
        reader    = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows      = list(reader)

    updates = {e["link"]: e["status"] for e in events}
    changed = 0
    for row in rows:
        new_status = updates.get(row.get("link", ""))
        if new_status and row.get("status") != new_status:
            row["status"] = new_status
            changed += 1

    if changed:
        with open(APPLIED_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {changed} application status(es) from Gmail replies.")

    return changed
