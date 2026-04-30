# scorer.py
from llm_client import score_with_llm
from config import LOCATION, SKILLS

_PROFILE = f"AI engineer, {LOCATION}. " + ", ".join(SKILLS[:8]) + "."

GOOD_WORDS = {
    "junior": 5,
    "entry": 5,
    "associate": 4,
    "ai": 5,
    "data": 4,
    "python": 4,
    "llm": 5,
    "machine learning": 5,
    "nlp": 4,
    "mlops": 5,
    "rag": 5,
    "operations": 3,
    "automation": 3,
}

BAD_WORDS = {
    "senior": -8,
    "staff": -8,
    "lead": -7,
    "manager": -6,
    "director": -10,
    "php": -2,
    "ios": -2,
    "android": -2,
    "c++": -3,
}


def score_job(job):
    """Fast keyword pre-filter. Returns a rough integer score."""
    text = (
        job["title"] + " " +
        job["description"] + " " +
        job["location"]
    ).lower()

    score = sum(v for k, v in GOOD_WORDS.items() if k in text)
    score += sum(v for k, v in BAD_WORDS.items() if k in text)

    if "spain" in text or "madrid" in text:
        score += 5
    if "europe" in text or "worldwide" in text or "anywhere" in text:
        score += 3
    if "usa only" in text or "us only" in text:
        score -= 4

    return score


def score_jobs_with_llm(jobs, max_jobs=25):
    """
    Re-score the top keyword-filtered jobs with the LLM.
    Replaces job["score"] with a 0-10 value and adds job["reason"].
    Jobs beyond max_jobs keep their keyword score and get an empty reason.
    """
    to_score = jobs[:max_jobs]
    print(f"\nLLM scoring {len(to_score)} jobs...")

    for i, job in enumerate(to_score, 1):
        score, reason = score_with_llm(job, _PROFILE)
        job["score"]  = score
        job["reason"] = reason
        print(f"  {i}/{len(to_score)}  {job['title'][:40]:40}  {score}/10  {reason}")

    for job in jobs[max_jobs:]:
        job.setdefault("reason", "")

    return jobs
