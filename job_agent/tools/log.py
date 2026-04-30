from tracker import log_application

SCHEMA = {
    "type": "function",
    "function": {
        "name": "log_application",
        "description": "Log a job application to applied.csv with status 'applied'.",
        "parameters": {
            "type": "object",
            "properties": {
                "title":       {"type": "string"},
                "company":     {"type": "string"},
                "link":        {"type": "string"},
                "location":    {"type": "string"},
                "source":      {"type": "string"},
                "score":       {"type": "number"},
                "reason":      {"type": "string"},
                "salary":      {"type": "string"},
                "folder_path": {"type": "string"},
            },
            "required": ["title", "company", "link"],
        },
    },
}


def run(title: str, company: str, link: str, location: str = "",
        source: str = "", score: float = 0, reason: str = "",
        salary: str = "", folder_path: str = "") -> dict:
    job = {
        "title": title, "company": company, "location": location,
        "source": source, "score": score, "reason": reason,
        "salary": salary, "link": link,
    }
    log_application(job, folder_path)
    return {"status": "logged", "company": company, "title": title}
