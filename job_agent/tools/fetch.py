from job_reader import get_job_text

SCHEMA = {
    "type": "function",
    "function": {
        "name": "fetch_job_page",
        "description": "Fetch the full job description text from a job posting URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of the job posting",
                },
            },
            "required": ["url"],
        },
    },
}


def run(url: str) -> str:
    text = get_job_text(url)
    return text if text else "Could not fetch job description."
