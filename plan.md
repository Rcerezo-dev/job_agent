# Job Agent — Roadmap

---

## ✅ Done

- Multi-source scraper: Remotive, Arbeitnow, Jobicy, LinkedIn, InfoJobs, Tecnoempleo, Domestika, landing.jobs
- Keyword-based job scorer with Madrid/Spain/Europe location boost
- Language detection via Ollama — CV and cover letter written in the job's language
- AI-generated professional summary, skill selection, and cover letter (Ollama, llama3.1:8b)
- Skills grounded in real config.py list — model cannot invent skills
- PDF output with proper formatting: header, sections, dividers, skills chip grid
- Professional Experience section in PDF (KeepCoding projects + teaching roles)
- Education section in PDF
- Personal data in config.py (name, email, city, skills, experience, education)

---

## Phase 1 — CV completeness  *(next)*

### Your items
- [x] **Languages section** — add `LANGUAGES` list to `config.py` (e.g. `[{"language": "Spanish", "level": "Native"}, {"language": "English", "level": "C1"}]`) and render it in the PDF between Education and Skills
- [x] **GitHub project filtering** — store your GitHub projects in `config.py` with title + description, then ask the LLM to pick the 2–3 most relevant ones for each job offer and inject them into the CV as a "Selected Projects" section

### My additions
- [x] **Smarter scorer** — replace the keyword list in `scorer.py` with an LLM call: give it the job description + your profile and get a 0–10 relevance score with a one-line reason. Much more accurate than word matching
- [x] **Auto-open PDF** — after generating the documents, call `os.startfile()` (Windows) to open the CV automatically so you don't have to navigate to the folder every time

---

## Phase 2 — Application tracking  *(1–2 weeks)*

- [x] **Applied jobs log** — when you choose a job and generate the CV, write a row to an `applied.csv` with date, company, role, link, and status (`applied / interview / rejected / offer`). Prevents applying twice and builds a history
- [x] **Status CLI** — a small `status.py` script that prints a table of your pipeline: how many jobs scraped, how many CVs generated, interview rate, etc.
- [x] **Deduplication across runs** — compare new scraped jobs against `applied.csv` and `jobs.csv` so already-seen listings don't reappear at the top

---

## Phase 3 — Full automation  *(2–4 weeks)*

- [ ] **Email sending** — after generating documents, compose a draft in Gmail (via SMTP or the Gmail MCP already available in this session) with the CV and cover letter attached, addressed to the company's contact if found in the job posting
- [ ] **Daily job alerts** — schedule the scraper to run every morning, score the new jobs, and send you a summary email with the top 5
- [ ] **Company research** — when you select a job, run a second LLM call that searches for context about the company (size, product, culture) and appends a "Why this company" paragraph to the cover letter

---

## Phase 4 — Quality & polish  *(ongoing)*

- [ ] **Scraper robustness** — add retry logic with exponential backoff for HTML scrapers; rotate User-Agent; cache results for 6 hours to avoid hammering sites on repeated runs
- [ ] **Salary extraction** — scan the job description with the LLM and extract salary range if mentioned; show it next to each listing in the terminal and save it in the CSV
- [ ] **Cover letter tone variants** — add a `TONE` setting in `config.py` (`"formal"` / `"direct"` / `"startup"`) that gets injected into the cover letter prompt
- [ ] **Multiple output formats** — alongside PDF, write a plain `.txt` version for job portals that don't accept PDFs (InfoJobs, LinkedIn Easy Apply)
- [ ] **Interview prep** — a fourth document generated per application: 5 likely interview questions for the role + bullet-point answers based on your experience

---

## Architecture at a glance

```
config.py          ← all personal data, skills, experience, education, projects
scraper.py         ← 8 sources → unified job list
scorer.py          ← relevance score per job
main.py            ← orchestrator: scrape → score → rank → pick → generate
llm_client.py      ← Ollama wrapper (ask_llm, detect_language)
job_reader.py      ← fetches full job description from URL
cv_writer.py       ← PDF generation (cv + cover letter)
outputs/           ← cv_custom.pdf, cover_letter.pdf
jobs.csv           ← full scored job list from last run
applied.csv        ← (Phase 2) your application history
```
