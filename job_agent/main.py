import csv
from scraper import search_jobs
from scorer import score_job, score_jobs_with_llm
from cv_writer import save_documents
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

with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["title", "company", "location", "description", "link", "score", "reason", "source"],
    )
    writer.writeheader()
    writer.writerows(jobs)

top = jobs[:15]
print(f"\nTOP OFFERS ({len(jobs)} relevant jobs found):\n")

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
    else:
        print("Number out of range.")
except ValueError:
    print("Please enter a number.")
