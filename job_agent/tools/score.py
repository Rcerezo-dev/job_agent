from scorer import score_job as _keyword_score
from llm_client import score_with_llm
from config import SKILLS, EXPERIENCE

_PROFILE = (
    "AI engineer (career transitioner from teaching). "
    f"Skills: {', '.join(SKILLS[:10])}. "
    f"Experience: {'; '.join(e['role'] + ' at ' + e['company'] for e in EXPERIENCE[:2])}."
)

SCHEMA = {
    "type": "function",
    "function": {
        "name": "score_job",
        "description": (
            "Score a single job against the candidate profile. "
            "Returns a keyword score (fast heuristic) and an LLM score (0–10) with a reason."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title":       {"type": "string", "description": "Job title"},
                "company":     {"type": "string", "description": "Company name"},
                "location":    {"type": "string"},
                "description": {"type": "string", "description": "Job description text"},
                "link":        {"type": "string"},
            },
            "required": ["title", "company", "description"],
        },
    },
}


def run(title: str, company: str, description: str,
        location: str = "", link: str = "") -> dict:
    job = {
        "title": title, "company": company,
        "location": location, "description": description, "link": link,
    }
    keyword_score = _keyword_score(job)
    llm_score, reason = score_with_llm(job, _PROFILE)
    return {
        "keyword_score": keyword_score,
        "llm_score": llm_score,
        "reason": reason,
    }
