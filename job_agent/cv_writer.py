import os
import platform
import subprocess
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from job_reader import get_job_text
from llm_client import ask_llm, detect_language
from config import (
    EDUCATION, EXPERIENCE, GITHUB_PROJECTS, GITHUB_URL, LANGUAGES,
    LINKEDIN, OUTPUTS_DIR, SKILLS, TONE, USER_CITY, USER_EMAIL, USER_NAME, USER_PHONE,
)

# ── Palette ───────────────────────────────────────────────────────────────────

_NAVY  = colors.HexColor("#1C2E4A")
_BLUE  = colors.HexColor("#2563EB")
_GRAY  = colors.HexColor("#6B7280")
_BODY  = colors.HexColor("#374151")
_CHIP  = colors.HexColor("#EFF6FF")
_RULE  = colors.HexColor("#CBD5E1")

# ── Paragraph styles ──────────────────────────────────────────────────────────

_name = ParagraphStyle(
    "Name", fontName="Helvetica-Bold", fontSize=20,
    textColor=_NAVY, spaceAfter=3,
)
_contact = ParagraphStyle(
    "Contact", fontName="Helvetica", fontSize=8.5,
    textColor=_GRAY, spaceAfter=0,
)
_section = ParagraphStyle(
    "Section", fontName="Helvetica-Bold", fontSize=10,
    textColor=_BLUE, spaceBefore=14, spaceAfter=5,
)
_body = ParagraphStyle(
    "Body", fontName="Helvetica", fontSize=10,
    textColor=_BODY, leading=15, spaceAfter=4,
)
_bold_body = ParagraphStyle(
    "BoldBody", fontName="Helvetica-Bold", fontSize=10,
    textColor=_NAVY, spaceAfter=4,
)
_chip_text = ParagraphStyle(
    "Chip", fontName="Helvetica", fontSize=9,
    textColor=_NAVY, alignment=TA_CENTER,
)
_entry_role = ParagraphStyle(
    "EntryRole", fontName="Helvetica-Bold", fontSize=10,
    textColor=_NAVY, spaceAfter=1,
)
_entry_company = ParagraphStyle(
    "EntryCompany", fontName="Helvetica-Oblique", fontSize=9.5,
    textColor=_GRAY, spaceAfter=4,
)
_entry_period = ParagraphStyle(
    "EntryPeriod", fontName="Helvetica", fontSize=9.5,
    textColor=_GRAY, alignment=TA_LEFT,
)
_bullet = ParagraphStyle(
    "Bullet", fontName="Helvetica", fontSize=9.5,
    textColor=_BODY, leading=14, leftIndent=10, spaceAfter=2,
)
_tech_tags = ParagraphStyle(
    "TechTags", fontName="Helvetica-Oblique", fontSize=8.5,
    textColor=_BLUE, spaceAfter=4,
)
_lang_level = ParagraphStyle(
    "LangLevel", fontName="Helvetica", fontSize=9.5,
    textColor=_GRAY,
)
_contact_right = ParagraphStyle(
    "ContactRight", fontName="Helvetica", fontSize=8.5,
    textColor=_GRAY, alignment=TA_RIGHT, leading=13,
)
_letter_body = ParagraphStyle(
    "LetterBody", fontName="Helvetica", fontSize=10,
    textColor=_BODY, leading=16, spaceAfter=10,
)
_signature = ParagraphStyle(
    "Sig", fontName="Helvetica-Bold", fontSize=10,
    textColor=_NAVY, spaceBefore=20,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _rule():
    return HRFlowable(width="100%", thickness=0.5, color=_RULE,
                      spaceBefore=4, spaceAfter=8)

PAGE_W = A4[0] - 40 * mm   # usable width with 20 mm margins each side

def _skills_table(skills_str):
    items = [s.strip() for s in skills_str.replace("\n", ",").split(",") if s.strip()]
    cols = 3
    while len(items) % cols:
        items.append("")
    rows = [
        [Paragraph(items[i + c], _chip_text) for c in range(cols)]
        for i in range(0, len(items), cols)
    ]
    col_w = PAGE_W / cols
    tbl = Table(rows, colWidths=[col_w] * cols)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _CHIP),
        ("GRID",          (0, 0), (-1, -1), 1.5, colors.white),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    return tbl

def _open_file(path):
    try:
        if platform.system() == "Windows":
            os.startfile(str(path))
        elif platform.system() == "Darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception:
        pass


def _doc(path):
    return SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )

def _contact_line(*parts):
    filled = [p for p in parts if p and "tuemail" not in p and "tuperfil" not in p
              and "tuusuario" not in p and "Tunombre" not in p and "XXX" not in p]
    return "   ·   ".join(filled)

def _header_table(include_github=True):
    """Name on the left, contact details stacked on the right."""
    parts = [USER_CITY, USER_PHONE, USER_EMAIL, LINKEDIN]
    if include_github:
        parts.append(GITHUB_URL)
    lines = [p for p in parts if p and "tuemail" not in p and "tuperfil" not in p
             and "tuusuario" not in p and "Tunombre" not in p and "XXX" not in p]

    right_w = PAGE_W * 0.45
    # One paragraph per item so ReportLab never splits a URL at a slash
    contact_rows = [[Paragraph(line, _contact_right)] for line in lines]
    contact_tbl = Table(contact_rows, colWidths=[right_w])
    contact_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    tbl = Table(
        [[Paragraph(USER_NAME, _name), contact_tbl]],
        colWidths=[PAGE_W * 0.55, right_w],
    )
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return tbl

def _experience_block(entry):
    """Returns a list of flowables for one experience entry."""
    items = []
    # Role on the left, period on the right
    row = Table(
        [[Paragraph(entry["role"], _entry_role),
          Paragraph(entry["period"], _entry_period)]],
        colWidths=[PAGE_W * 0.72, PAGE_W * 0.28],
    )
    row.setStyle(TableStyle([
        ("VALIGN",         (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN",          (1, 0), (1, 0),   "RIGHT"),
        ("TOPPADDING",     (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 0),
    ]))
    items.append(row)
    items.append(Paragraph(entry["company"], _entry_company))
    for bullet in entry.get("bullets", []):
        items.append(Paragraph(f"• {bullet}", _bullet))
    items.append(Spacer(1, 4*mm))
    return items

def _education_block(entry):
    """Returns a list of flowables for one education entry."""
    items = []
    row = Table(
        [[Paragraph(entry["degree"], _entry_role),
          Paragraph(entry["period"], _entry_period)]],
        colWidths=[PAGE_W * 0.72, PAGE_W * 0.28],
    )
    row.setStyle(TableStyle([
        ("VALIGN",         (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN",          (1, 0), (1, 0),   "RIGHT"),
        ("TOPPADDING",     (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 0),
    ]))
    items.append(row)
    items.append(Paragraph(entry["institution"], _entry_company))
    for bullet in entry.get("bullets", []):
        items.append(Paragraph(f"• {bullet}", _bullet))
    items.append(Spacer(1, 3*mm))
    return items

def _projects_block(projects):
    """Returns a list of flowables for the selected GitHub projects."""
    items = []
    for proj in projects:
        url = proj.get("url", "")
        right_cell = Paragraph(url, _entry_period) if url else Paragraph("", _entry_period)
        row = Table(
            [[Paragraph(proj["name"], _entry_role), right_cell]],
            colWidths=[PAGE_W * 0.6, PAGE_W * 0.4],
        )
        row.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
            ("ALIGN",         (1, 0), (1, 0),   "RIGHT"),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        items.append(row)
        items.append(Paragraph(proj["description"], _bullet))
        tech_str = " · ".join(proj.get("tech", []))
        if tech_str:
            items.append(Paragraph(tech_str, _tech_tags))
        items.append(Spacer(1, 3 * mm))
    return items


def _languages_block(languages):
    """Returns a compact table of language / level pairs."""
    rows = [
        [Paragraph(lang["language"], _entry_role),
         Paragraph(lang["level"], _lang_level)]
        for lang in languages
    ]
    tbl = Table(rows, colWidths=[PAGE_W * 0.35, PAGE_W * 0.65])
    tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl


# ── PDF builders ──────────────────────────────────────────────────────────────

def create_cv_pdf(path, job, summary, skills, projects):
    story = []

    # Header
    story.append(_header_table(include_github=True))
    story.append(Spacer(1, 4*mm))
    story.append(_rule())

    # Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", _section))
    story.append(Paragraph(summary, _body))
    story.append(_rule())

    # Target Position
    story.append(Paragraph("TARGET POSITION", _section))
    story.append(Paragraph(job["title"], _bold_body))
    story.append(Paragraph(job["company"], _body))
    story.append(_rule())

    # Professional Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", _section))
    for entry in EXPERIENCE:
        for item in _experience_block(entry):
            story.append(item)
    story.append(_rule())

    # Selected Projects
    if projects:
        story.append(Paragraph("SELECTED PROJECTS", _section))
        for item in _projects_block(projects):
            story.append(item)
        story.append(_rule())

    # Education
    story.append(Paragraph("EDUCATION", _section))
    for entry in EDUCATION:
        for item in _education_block(entry):
            story.append(item)
    story.append(_rule())

    # Languages
    story.append(Paragraph("LANGUAGES", _section))
    story.append(_languages_block(LANGUAGES))
    story.append(_rule())

    # Key Skills
    story.append(Paragraph("KEY SKILLS", _section))
    story.append(_skills_table(skills))

    _doc(path).build(story)


def create_cv_txt(path, job, summary, skills, projects):
    """Plain-text CV for portals that don't accept file uploads."""
    contact = "  ·  ".join(p for p in [USER_CITY, USER_PHONE, USER_EMAIL, LINKEDIN, GITHUB_URL] if p)
    sep = "-" * 50
    lines = [
        USER_NAME, contact, "",
        "PROFESSIONAL SUMMARY", sep, summary, "",
        "TARGET POSITION", sep,
        f"{job['title']} at {job['company']}", "",
        "PROFESSIONAL EXPERIENCE", sep,
    ]
    for e in EXPERIENCE:
        lines.append(f"{e['role']}  |  {e['company']}  |  {e['period']}")
        for b in e.get("bullets", []):
            lines.append(f"  • {b}")
        lines.append("")
    if projects:
        lines += ["SELECTED PROJECTS", sep]
        for p in projects:
            lines.append(p["name"])
            lines.append(f"  {p['description']}")
            if p.get("tech"):
                lines.append(f"  Tech: {', '.join(p['tech'])}")
            lines.append("")
    lines += ["EDUCATION", sep]
    for e in EDUCATION:
        lines.append(f"{e['degree']}  |  {e['institution']}  |  {e['period']}")
        for b in e.get("bullets", []):
            lines.append(f"  • {b}")
        lines.append("")
    lines += ["LANGUAGES", sep]
    for lang in LANGUAGES:
        lines.append(f"{lang['language']}: {lang['level']}")
    lines += ["", "KEY SKILLS", sep, skills]
    path.write_text("\n".join(lines), encoding="utf-8")


def create_cover_letter_pdf(path, job, letter_text):
    story = []

    # Sender header
    story.append(_header_table(include_github=False))
    story.append(Spacer(1, 6*mm))

    # Date and recipient
    today = date.today().strftime("%B %d, %Y")
    story.append(Paragraph(today, _body))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(job["company"], _bold_body))
    story.append(_rule())

    # Letter body — split on blank lines to preserve paragraphs
    for para in letter_text.strip().split("\n\n"):
        para = para.strip()
        if not para:
            continue
        # Separate signature from body if still in the text
        if para.lower().startswith("best regards") or para.lower().startswith("atentamente"):
            story.append(Spacer(1, 6*mm))
            story.append(Paragraph(para, _signature))
        else:
            story.append(Paragraph(para, _letter_body))

    _doc(path).build(story)


# ── AI prompts ────────────────────────────────────────────────────────────────

_SKILLS_STR = ", ".join(SKILLS)

_CANDIDATE = (
    "AI engineer with 6+ years teaching experience and intensive AI engineering training (KeepCoding). "
    "Builds real systems: LLM agents (LangGraph, LangChain), RAG pipelines (ChromaDB, Amazon Bedrock), "
    "deep learning models (TensorFlow, PyTorch), and MLOps deployments (Docker, Terraform, MLflow, FastAPI). "
    "Education background provides strong communication, problem structuring and training skills."
)


def generate_summary(job, language="English"):
    prompt = f"""
Write ONLY a concise professional CV summary in {language}.

Rules:
- No intro text
- No quotation marks
- Max 4 lines
- Professional tone
- Only mention skills from the candidate's real skill list below

Candidate:
{_CANDIDATE}
Real skills: {_SKILLS_STR}

Target role:
{job["title"]} at {job["company"]}
"""
    return ask_llm(prompt)


def generate_skills(job, language="English"):
    prompt = f"""
From the candidate's skill list below, select the most relevant ones for this job.
Return them comma-separated in {language}.

Rules:
- Use ONLY skills from the list — do not add, invent or rename any
- No intro text
- No numbering

Candidate skills:
{_SKILLS_STR}

Job title:
{job["title"]}

Job description:
{job.get("real_description", job["description"])[:1000]}
"""
    return ask_llm(prompt)


def _match_projects(names_text):
    """Match LLM-returned project names against GITHUB_PROJECTS."""
    lines = [l.strip().lstrip("-•*0123456789. ") for l in names_text.strip().split("\n") if l.strip()]
    selected = []
    for line in lines:
        for proj in GITHUB_PROJECTS:
            if (proj["name"].lower() in line.lower() or line.lower() in proj["name"].lower()):
                if proj not in selected:
                    selected.append(proj)
                break
    return selected[:3]


def generate_projects(job):
    projects_list = "\n".join(
        f'- {p["name"]}: {p["description"]}'
        for p in GITHUB_PROJECTS
    )
    prompt = f"""
From the candidate's project list below, select the 2 or 3 most relevant for this job.
Reply with ONLY the project names, one per line. No other text, no numbering.

Job title:
{job["title"]}

Job description:
{job.get("real_description", job["description"])[:800]}

Projects:
{projects_list}
"""
    raw = ask_llm(prompt)
    return _match_projects(raw)


_TONE_MAP = {
    "formal":  "formal and professional",
    "direct":  "direct and confident — no filler phrases or empty pleasantries",
    "startup": "energetic and startup-friendly, slightly informal but still professional",
}


def generate_cover_letter(job, language="English"):
    tone_desc = _TONE_MAP.get(TONE, _TONE_MAP["formal"])
    prompt = f"""
Write ONLY a short natural cover letter in {language}.

Rules:
- No intro text
- Max 170 words
- Tone: {tone_desc}
- Use paragraphs separated by a blank line
- No placeholders
- Only reference skills from the candidate's real skill list below
- End with: Best regards, followed by a blank line, then {USER_NAME}

Candidate:
{_CANDIDATE}
Real skills: {_SKILLS_STR}

Job:
{job["title"]}

Company:
{job["company"]}
"""
    return ask_llm(prompt)


# ── Research & prep prompts ───────────────────────────────────────────────────

_EXPERIENCE_TEXT = "\n".join(
    f"- {e['role']} at {e['company']}: {'; '.join(e.get('bullets', [])[:3])}"
    for e in EXPERIENCE
)
_PROJECTS_TEXT = "\n".join(
    f"- {p['name']}: {p['description']}"
    for p in GITHUB_PROJECTS
)


def generate_company_research(job, output_dir):
    description = job.get("real_description", job.get("description", ""))[:2000]
    prompt = f"""You are a job candidate researching a company before an interview.

Based on the job description below, write a 1-page research summary with these sections:
1. **Product / Service** — what the company builds or sells
2. **Tech stack signals** — technologies, tools or methodologies mentioned
3. **Culture signals** — team size, work style, values mentioned
4. **Why this company** — a short paragraph you could use to personalise a cover letter or prepare for the interview

Rules:
- Be specific — use details from the job description
- If something is not mentioned, say "not mentioned in the job description"
- Use markdown headers

Company: {job.get("company", "")}
Role: {job.get("title", "")}

Job description:
{description}
"""
    content = ask_llm(prompt)
    md = f"# Company Research: {job.get('company', '')}\n\n{content}\n"
    (output_dir / "company_research.md").write_text(md, encoding="utf-8")
    print("Company research saved.")


def generate_interview_prep(job, output_dir):
    description = job.get("real_description", job.get("description", ""))[:2000]
    prompt = f"""You are preparing a job candidate for a technical interview.

Generate exactly 5 likely interview questions for this role and provide concise bullet-point answers grounded in the candidate's real experience and projects.

Format each question exactly like this:
## Q1: [question text]
- bullet answer point 1
- bullet answer point 2

Rules:
- Questions must be realistic for the role and seniority level
- Answers must reference the candidate's actual projects and experience listed below — no generic answers
- Be specific and concrete

Candidate experience:
{_EXPERIENCE_TEXT}

Candidate projects:
{_PROJECTS_TEXT}

Role: {job.get("title", "")}
Company: {job.get("company", "")}

Job description:
{description}
"""
    content = ask_llm(prompt)
    md = f"# Interview Prep: {job.get('title', '')} at {job.get('company', '')}\n\n{content}\n"
    (output_dir / "interview_prep.md").write_text(md, encoding="utf-8")
    print("Interview prep saved.")


# ── Main ──────────────────────────────────────────────────────────────────────

def save_documents(job, output_dir=None):
    if output_dir is None:
        output_dir = OUTPUTS_DIR
        output_dir.mkdir(exist_ok=True)

    real_text = get_job_text(job["link"])
    job["real_description"] = real_text if real_text else job["description"]

    language = detect_language(job["real_description"])
    print(f"Detected language: {language}")

    print("Generating summary...")
    summary      = generate_summary(job, language)
    print("Selecting skills...")
    skills       = generate_skills(job, language)
    print("Selecting projects...")
    projects     = generate_projects(job)
    print("Writing cover letter...")
    cover_letter = generate_cover_letter(job, language)

    cv_path     = output_dir / "cv_custom.pdf"
    cv_txt_path = output_dir / "cv_custom.txt"
    letter_path = output_dir / "cover_letter.pdf"

    create_cv_pdf(cv_path, job, summary, skills, projects)
    create_cv_txt(cv_txt_path, job, summary, skills, projects)
    create_cover_letter_pdf(letter_path, job, cover_letter)

    print(f"Documents saved to {output_dir.name}/")
    _open_file(cv_path)
    _open_file(letter_path)
