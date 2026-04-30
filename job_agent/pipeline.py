"""Manual interactive pipeline — the original scripted workflow."""
import csv

from scraper import search_jobs
from scorer import score_job, score_jobs_with_llm
from cv_writer import save_documents, generate_company_research, generate_interview_prep
from tracker import load_applied_links, log_application, create_app_folder
from llm_client import extract_salary
from config import CSV_FILE


def run_pipeline():
    jobs = search_jobs()

    for job in jobs:
        job["score"] = score_job(job)

    jobs = [
        job for job in jobs
        if job["score"] > 0
        and (
            "madrid" in job["location"].lower()
            or "spain" in job["location"].lower()
        )
    ]

    jobs = score_jobs_with_llm(jobs)
    jobs.sort(key=lambda x: x["score"], reverse=True)

    applied_links = load_applied_links()
    already_applied = [j for j in jobs if j["link"] in applied_links]
    jobs = [j for j in jobs if j["link"] not in applied_links]

    if already_applied:
        print(f"({len(already_applied)} previously applied job(s) hidden — run status.py to review)\n")

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["title", "company", "location", "description", "link", "score", "reason", "source"],
        )
        writer.writeheader()
        writer.writerows(jobs)

    top = jobs[:15]
    print(f"TOP OFFERS ({len(jobs)} new relevant jobs):\n")

    for i, job in enumerate(top, start=1):
        print("-" * 40)
        print(f'{i}. {job["title"]} | {job["company"]}  [{job.get("source", "")}]')
        print(f'Score: {job["score"]}/10  —  {job.get("reason", "")}')
        print(f'{job["location"]}')
        print(job["link"])

    print("-" * 40)

    try:
        choice = int(input("\nChoose a job (number): "))
        if 1 <= choice <= len(top):
            selected_job = top[choice - 1]
            folder = create_app_folder(selected_job)
            save_documents(selected_job, folder)
            salary = extract_salary(selected_job.get("real_description", selected_job["description"]))
            if salary:
                print(f"Salary: {salary}")
            selected_job["salary"] = salary
            print("Generating company research...")
            generate_company_research(selected_job, folder)
            print("Generating interview prep...")
            generate_interview_prep(selected_job, folder)
            log_application(selected_job, folder)
        else:
            print("Number out of range.")
    except ValueError:
        print("Please enter a number.")
