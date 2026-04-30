"""
Phase 8 — Agent memory.

Reads applied.csv to track outcomes across runs, generates a rolling
agent_memory.md summary, and provides a context snippet for the system prompt.
"""
import csv
from datetime import date
from pathlib import Path

import ollama

from config import DATA_DIR
from llm_client import MODEL_NAME

MEMORY_FILE = DATA_DIR / "agent_memory.md"
_MAX_CHARS = 2000  # ~500 tokens


def load_memory() -> str:
    """Return memory text for injection into the system prompt (capped at ~500 tokens)."""
    if not MEMORY_FILE.exists():
        return ""
    text = MEMORY_FILE.read_text(encoding="utf-8").strip()
    if len(text) > _MAX_CHARS:
        text = text[:_MAX_CHARS] + "\n...(truncated)"
    return text


def _read_applied() -> list[dict]:
    applied_file = DATA_DIR / "applied.csv"
    if not applied_file.exists():
        return []
    with open(applied_file, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def update_memory(agent_summary: str = "") -> None:
    """
    Re-read applied.csv outcomes, then ask the LLM to write a fresh
    agent_memory.md: what worked, what to avoid, keyword suggestions.
    Called automatically at the end of each agent run.
    """
    rows = _read_applied()
    if not rows:
        print("No application history yet — skipping memory update.")
        return

    lines = ["date,title,company,score,status"]
    for r in rows[-30:]:  # last 30 applications
        lines.append(
            f"{r.get('date','')},{r.get('title','')},{r.get('company','')}"
            f",{r.get('score','')},{r.get('status','applied')}"
        )
    applications_text = "\n".join(lines)

    summary_section = f"\nLast session summary: {agent_summary}\n" if agent_summary else ""

    prompt = f"""You are reviewing a job application history for a junior AI/ML engineer candidate based in Madrid.

Application history (CSV, most recent 30):
{applications_text}
{summary_section}
Write a concise memory note (max 350 words) for the agent to use on the next run.
Use this exact structure:

## What worked
- Job titles and companies that progressed (interview / offer status)
- Skills or keywords that seemed to resonate

## What to avoid
- Titles or companies marked as rejected
- Patterns that seem to be a poor fit

## Keyword suggestions
- 2–3 concrete search keyword adjustments based on the outcome data

## Recent activity
- Brief factual summary of the last 3–5 applications

Keep it factual and grounded in the data. Today is {date.today().isoformat()}.
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    memory_text = response["message"]["content"].strip()

    header = f"# Agent Memory\n\n_Last updated: {date.today().isoformat()}_\n\n"
    MEMORY_FILE.write_text(header + memory_text, encoding="utf-8")
    print(f"Memory updated → data/agent_memory.md")
