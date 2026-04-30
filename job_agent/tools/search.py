from scraper import search_jobs as _scrape
from scorer import score_job as _keyword_score
from tracker import load_applied_links

SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_jobs",
        "description": (
            "Scrape all job boards, score listings by keywords, deduplicate against "
            "already-applied jobs, and return the top new listings sorted by score."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location filter, e.g. 'Madrid' or 'Spain'",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Maximum number of jobs to return (default 15)",
                },
            },
            "required": ["location"],
        },
    },
}


def run(location: str = "Madrid", top_n: int = 15) -> list[dict]:
    jobs = _scrape()
    for job in jobs:
        job["score"] = _keyword_score(job)

    jobs = [
        j for j in jobs
        if j["score"] > 0 and location.lower() in j["location"].lower()
    ]

    applied = load_applied_links()
    jobs = [j for j in jobs if j["link"] not in applied]
    jobs.sort(key=lambda x: x["score"], reverse=True)

    return [
        {
            "title": j["title"],
            "company": j["company"],
            "location": j["location"],
            "score": j["score"],
            "source": j.get("source", ""),
            "link": j["link"],
            "description": j.get("description", "")[:300],
        }
        for j in jobs[:top_n]
    ]
