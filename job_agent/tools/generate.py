from cv_writer import save_documents, generate_company_research, generate_interview_prep
from tracker import create_app_folder
from llm_client import extract_salary

SCHEMA = {
    "type": "function",
    "function": {
        "name": "generate_cv",
        "description": (
            "Generate a tailored CV (PDF + TXT), cover letter, company research, and "
            "interview prep for a job. Creates a per-application folder and returns its path."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title":       {"type": "string", "description": "Job title"},
                "company":     {"type": "string", "description": "Company name"},
                "link":        {"type": "string", "description": "Job posting URL"},
                "description": {"type": "string", "description": "Job description text"},
                "location":    {"type": "string"},
                "source":      {"type": "string"},
                "score":       {"type": "number"},
                "reason":      {"type": "string"},
            },
            "required": ["title", "company", "link"],
        },
    },
}


def run(title: str, company: str, link: str, description: str = "",
        location: str = "", source: str = "", score: float = 0,
        reason: str = "") -> dict:
    job = {
        "title": title, "company": company, "location": location,
        "description": description, "link": link,
        "source": source, "score": score, "reason": reason,
    }
    folder = create_app_folder(job)
    save_documents(job, folder)
    salary = extract_salary(job.get("real_description", description))
    if salary:
        print(f"Salary: {salary}")
    job["salary"] = salary
    generate_company_research(job, folder)
    generate_interview_prep(job, folder)
    return {"folder": str(folder), "salary": salary}
