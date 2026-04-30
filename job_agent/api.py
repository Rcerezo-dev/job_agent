import asyncio
import csv
import io
import json
import queue as _queue
import sys
import threading
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
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


# ── Phase 10 endpoints ─────────────────────────────────────────────────────────

@app.post("/run")
def run_search():
    """Scrape all sources, keyword-score, LLM re-score top 25, return jobs ≥ 8."""
    from scraper import search_jobs as _scrape
    from scorer import score_job as _keyword_score, score_jobs_with_llm
    from tracker import load_applied_links

    jobs = _scrape()
    for j in jobs:
        j["score"] = _keyword_score(j)

    applied = load_applied_links()
    jobs = [
        j for j in jobs
        if j["score"] > 0
        and j["link"] not in applied
        and ("madrid" in (j.get("location") or "").lower()
             or "spain" in (j.get("location") or "").lower())
    ]
    jobs.sort(key=lambda x: x["score"], reverse=True)

    jobs = score_jobs_with_llm(jobs, max_jobs=25)

    high = [j for j in jobs if j.get("score", 0) >= 8]
    high.sort(key=lambda x: x.get("score", 0), reverse=True)
    return {"jobs": high, "total_scraped": len(jobs)}


class GenerateBody(BaseModel):
    title: str
    company: str
    link: str
    description: str = ""
    location: str = ""
    source: str = ""
    score: float = 0
    reason: str = ""


@app.post("/generate", status_code=201)
def generate_docs(body: GenerateBody):
    """Generate CV + cover letter + research + interview prep for a job."""
    from tools.generate import run as _gen
    from tools.log import run as _log

    result = _gen(**body.model_dump())
    _log(
        title=body.title, company=body.company, link=body.link,
        location=body.location, source=body.source, score=body.score,
        reason=body.reason, folder_path=result.get("folder", ""),
    )
    return result


class ReplyBody(BaseModel):
    text: str


@app.post("/applications/{app_id}/reply")
def handle_reply(app_id: int, body: ReplyBody):
    """Classify an HR reply with the LLM and update the application status."""
    from llm_client import ask_llm

    prompt = (
        "Classify this HR email reply with exactly one word: "
        "'interview', 'offer', or 'rejected'.\n\n"
        f"Reply text:\n{body.text[:800]}"
    )
    word = ask_llm(prompt).strip().lower().split()[0] if body.text.strip() else "rejected"
    status = word if word in ("interview", "offer", "rejected") else "rejected"

    rows = _read_rows()
    if app_id < 0 or app_id >= len(rows):
        raise HTTPException(404, "Application not found")
    rows[app_id]["status"] = status
    _write_rows(rows)
    return {"id": app_id, "status": status}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatBody(BaseModel):
    app_id: int
    message: str
    history: List[ChatMessage] = []


@app.post("/chat")
def chat(body: ChatBody):
    """Mock interview chatbot grounded in the application's interview_prep.md."""
    import ollama
    from llm_client import MODEL_NAME

    rows = _read_rows()
    if body.app_id < 0 or body.app_id >= len(rows):
        raise HTTPException(404, "Application not found")

    row = rows[body.app_id]
    context = ""
    folder = row.get("folder_path", "")
    if folder:
        prep = Path(folder) / "interview_prep.md"
        if prep.exists():
            context = prep.read_text(encoding="utf-8")[:2000]

    system = (
        f"You are a mock interviewer for a junior AI engineer candidate.\n"
        f"Role: {row.get('title')} at {row.get('company')}\n"
        + (f"\nInterview prep notes:\n{context}\n" if context else "")
        + "\nAsk realistic questions and give brief, constructive feedback. "
        "Keep every response under 80 words."
    )

    messages = [{"role": "system", "content": system}]
    for m in body.history[-8:]:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": body.message})

    resp = ollama.chat(model=MODEL_NAME, messages=messages)
    return {"reply": resp["message"]["content"].strip()}


# ── Real agent streaming ───────────────────────────────────────────────────────

_DEFAULT_AGENT_GOAL = (
    "Find the best AI/ML engineering jobs in Madrid today and prepare "
    "application documents for the top match."
)


class AgentGoal(BaseModel):
    goal: str = _DEFAULT_AGENT_GOAL


class _QueueWriter(io.TextIOBase):
    """Captures print() calls from the agent thread and forwards them to a queue."""
    def __init__(self, q: _queue.Queue):
        self._q = q

    def write(self, s: str) -> int:
        if s:
            self._q.put(s)
        return len(s)

    def flush(self):
        pass


@app.post("/run/agent")
async def run_agent_stream(body: AgentGoal = None):
    """
    Run the real agent loop (agent.py) with auto=True and stream every print()
    line to the client as server-sent events.
    """
    goal = body.goal if body else _DEFAULT_AGENT_GOAL
    q: _queue.Queue = _queue.Queue()

    def _run():
        old_stdout = sys.stdout
        sys.stdout = _QueueWriter(q)
        try:
            from agent import run as _agent_run
            _agent_run(goal, auto=True)
        except Exception as exc:
            q.put(f"\n[Error] {exc}\n")
        finally:
            sys.stdout = old_stdout
            q.put(None)  # sentinel — agent is done

    threading.Thread(target=_run, daemon=True).start()

    async def generate():
        yield "data: \n\n"  # keep-alive first frame
        while True:
            try:
                line = q.get_nowait()
            except _queue.Empty:
                await asyncio.sleep(0.05)
                continue
            if line is None:
                yield "data: [DONE]\n\n"
                break
            yield f"data: {json.dumps(line)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
