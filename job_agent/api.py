import csv
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent))

from tracker import APPLIED_FILE, _FIELDS, create_app_folder, log_application

app = FastAPI(title="Job Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_VALID_STATUSES = {"applied", "interview", "offer", "rejected"}


def _read_rows() -> list[dict]:
    if not APPLIED_FILE.exists():
        return []
    with open(APPLIED_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_rows(rows: list[dict]) -> None:
    with open(APPLIED_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/applications")
def get_applications():
    rows = _read_rows()
    return [{"id": i, **row} for i, row in enumerate(rows)]


class StatusUpdate(BaseModel):
    status: str


@app.patch("/applications/{app_id}/status")
def update_status(app_id: int, body: StatusUpdate):
    if body.status not in _VALID_STATUSES:
        raise HTTPException(400, f"status must be one of {sorted(_VALID_STATUSES)}")
    rows = _read_rows()
    if app_id < 0 or app_id >= len(rows):
        raise HTTPException(404, "Application not found")
    rows[app_id]["status"] = body.status
    _write_rows(rows)
    return {"id": app_id, **rows[app_id]}


class NewApplication(BaseModel):
    title: str
    company: str
    location: str = ""
    source: str = "manual"
    score: str = ""
    reason: str = ""
    link: str = ""


@app.post("/applications", status_code=201)
def add_application(body: NewApplication):
    job = body.model_dump()
    folder = create_app_folder(job)
    log_application(job, folder)
    rows = _read_rows()
    app_id = len(rows) - 1
    return {"id": app_id, **rows[app_id]}


@app.get("/stats")
def get_stats():
    rows = _read_rows()
    counts = {s: 0 for s in _VALID_STATUSES}
    for row in rows:
        status = row.get("status", "applied")
        if status in counts:
            counts[status] += 1
    total = len(rows)
    return {
        "total": total,
        "counts": counts,
        "interview_rate_pct": round(counts["interview"] / total * 100, 1) if total else 0,
        "offer_rate_pct": round(counts["offer"] / total * 100, 1) if total else 0,
    }
