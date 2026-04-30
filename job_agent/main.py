import csv
from scraper import search_jobs
from scorer import score_job, score_jobs_with_llm
from cv_writer import save_documents
from tracker import load_applied_links, log_application
from config import CSV_FILE

jobs = search_jobs()

# Phase 1 — fast keyword pre-filter
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

# Phase 2 — LLM re-scoring of surviving jobs
jobs = score_jobs_with_llm(jobs)
jobs.sort(key=lambda x: x["score"], reverse=True)

# Deduplication — hide jobs already applied to
applied_links = load_applied_links()
already_applied = [j for j in jobs if j["link"] in applied_links]
jobs = [j for j in jobs if j["link"] not in applied_links]

if already_applied:
    print(f"({len(already_applied)} previously applied job(s) hidden — run status.py to review)\n")

# Save full scored list to CSV
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
        save_documents(selected_job)
        log_application(selected_job)
    else:
        print("Number out of range.")
except ValueError:
    print("Please enter a number.")
