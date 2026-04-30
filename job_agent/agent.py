"""
Agent loop — the LLM decides which tools to call and in what order.

Usage:
    from agent import run
    run("Find the best AI jobs in Madrid today and prepare documents for the top match.")

    # Skip human confirmation prompts:
    run(goal, auto=True)
"""
import json
import re
from datetime import date

import ollama

from llm_client import MODEL_NAME
from config import SKILLS, EXPERIENCE, GITHUB_PROJECTS
import tools as _tools

_REGISTRY = _tools.REGISTRY
_SCHEMAS  = _tools.SCHEMAS

_CONFIRM_TOOLS = {"generate_cv", "log_application"}

_SKILLS_STR = ", ".join(SKILLS)
_EXP_STR = "\n".join(
    f"  - {e['role']} at {e['company']} ({e['period']})" for e in EXPERIENCE
)
_PROJECTS_STR = "\n".join(
    f"  - {p['name']}: {p['description']}" for p in GITHUB_PROJECTS
)


def _build_system_prompt() -> str:
    return f"""You are a job-search agent acting on behalf of a candidate. Today is {date.today().isoformat()}.

=== CANDIDATE PROFILE ===
Skills: {_SKILLS_STR}

Experience:
{_EXP_STR}

Projects:
{_PROJECTS_STR}

=== INSTRUCTIONS ===
- Always call search_jobs first to get current listings.
- Use read_applications to avoid applying to the same job twice.
- Optionally call fetch_job_page or score_job to evaluate a promising listing more deeply.
- Call generate_cv for the best match (this requires human confirmation unless --auto).
- Call log_application after generating a CV (also requires confirmation).
- Finish with a brief plain-text summary: which job you chose and why.
- Do not invent job listings — only work with results from the tools.
"""


def _call_tool(name: str, args: dict, auto: bool) -> str:
    fn = _REGISTRY.get(name)
    if fn is None:
        return f"Error: unknown tool '{name}'"

    if name in _CONFIRM_TOOLS and not auto:
        preview = json.dumps(args, ensure_ascii=False)[:200]
        answer = input(f"\n  Agent wants to call {name}({preview})\n  Allow? [y/N]: ").strip().lower()
        if answer != "y":
            return "Tool call denied by user."

    try:
        result = fn(**args)
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as exc:
        return f"Error calling {name}: {exc}"


def _react_fallback(text: str, auto: bool) -> str | None:
    """
    Parse a ReAct-style plain-text action if the model forgot to use the tool API.
    Pattern: Action: tool_name({"key": "value"})
    Returns the observation string, or None if no pattern found.
    """
    match = re.search(
        r'Action:\s*(\w+)\s*\((\{.*?\}|\s*)\)',
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    name     = match.group(1)
    args_raw = match.group(2).strip()
    try:
        args = json.loads(args_raw) if args_raw else {}
    except json.JSONDecodeError:
        args = {}
    print(f"  [ReAct fallback] Parsed action from text: {name}")
    return _call_tool(name, args, auto)


def run(goal: str, auto: bool = False) -> None:
    messages = [
        {"role": "system",  "content": _build_system_prompt()},
        {"role": "user",    "content": goal},
    ]

    print(f"\nAgent started  •  model: {MODEL_NAME}")
    print(f"Goal: {goal}\n")

    for turn in range(20):
        response = ollama.chat(
            model=MODEL_NAME,
            messages=messages,
            tools=_SCHEMAS,
        )
        msg        = response["message"]
        content    = msg.get("content") or ""
        tool_calls = msg.get("tool_calls") or []

        # Add assistant turn to history
        messages.append({
            "role": "assistant",
            "content": content,
            **({"tool_calls": tool_calls} if tool_calls else {}),
        })

        if not tool_calls:
            # Check for ReAct-style fallback before giving up
            observation = _react_fallback(content, auto)
            if observation:
                messages.append({"role": "tool", "content": observation})
                continue
            # No tool calls — agent is done
            print("\n=== Agent report ===")
            print(content)
            return

        for tc in tool_calls:
            name = tc["function"]["name"]
            args = tc["function"]["arguments"]
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}

            print(f"  → {name}({json.dumps(args, ensure_ascii=False)[:120]})")
            result = _call_tool(name, args, auto)
            messages.append({"role": "tool", "content": result})

    print("Agent reached the turn limit without finishing.")
