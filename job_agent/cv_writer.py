import os
import platform
import subprocess
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
    LINKEDIN, SKILLS, USER_CITY, USER_EMAIL, USER_NAME, USER_PHONE,
)

BASE_DIR  = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "outputs"

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
    story.append(Paragraph(USER_NAME, _name))
    contact = _contact_line(USER_CITY, USER_PHONE, USER_EMAIL, LINKEDIN, GITHUB_URL)
    if contact:
        story.append(Paragraph(contact, _contact))
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


def create_cover_letter_pdf(path, job, letter_text):
    story = []

    # Sender header
    story.append(Paragraph(USER_NAME, _name))
    contact = _contact_line(USER_CITY, USER_PHONE, USER_EMAIL, LINKEDIN)
    if contact:
        story.append(Paragraph(contact, _contact))
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


def generate_cover_letter(job, language="English"):
    prompt = f"""
Write ONLY a short natural cover letter in {language}.

Rules:
- No intro text
- Max 170 words
- Calm professional tone
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


# ── Main ──────────────────────────────────────────────────────────────────────

def save_documents(job):
    OUTPUTS_DIR.mkdir(exist_ok=True)

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

    cv_path     = OUTPUTS_DIR / "cv_custom.pdf"
    letter_path = OUTPUTS_DIR / "cover_letter.pdf"

    create_cv_pdf(cv_path, job, summary, skills, projects)
    create_cover_letter_pdf(letter_path, job, cover_letter)

    print("Documents saved to outputs/")
    _open_file(cv_path)
    _open_file(letter_path)
