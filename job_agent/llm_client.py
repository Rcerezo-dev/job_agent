import ollama
import re

MODEL_NAME = "qwen2.5:14b"


def clean_text(text):
    text = text.replace('"', "")
    text = text.replace("Here is a professional CV summary:", "")
    text = text.replace("Here are the 8 relevant CV skills for this job:", "")
    text = text.replace("Here are the 8 relevant CV skills for a", "")
    text = text.replace("Here's a short natural cover letter:", "")
    text = text.replace("Here is a short natural cover letter:", "")
    text = text.replace("Here is your cover letter:", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def ask_llm(prompt):
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response["message"]["content"].strip()
    return clean_text(raw)


def score_with_llm(job, profile):
    """Return (score 0-10, short reason) for a job against a candidate profile."""
    desc = (job.get("description") or "")[:300]
    prompt = (
        "Rate this job for the candidate. "
        "Reply with ONLY: <number 0-10> | <reason max 6 words>\n\n"
        f"Candidate: {profile}\n"
        f"Job: {job['title']} at {job['company']} ({job.get('location', '')})\n"
        f"{desc}"
    )
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response["message"]["content"].strip()
    match = re.search(r'(\d+)\s*(?:/\s*10)?\s*[|·\-:,]\s*(.+)', raw)
    if match:
        score  = min(10, max(0, int(match.group(1))))
        reason = match.group(2).strip()[:60]
        return score, reason
    nums = re.findall(r'\b(\d+)\b', raw)
    if nums:
        return min(10, max(0, int(nums[0]))), raw[:60]
    return 5, raw[:60]


def extract_salary(text: str) -> str:
    """Return salary range string extracted from job description, or '' if not found."""
    sample = text[:1500]
    prompt = (
        "Extract the salary or salary range from this job description. "
        "Reply with only the salary (e.g. '35.000 – 45.000 € / year' or '$80k–$100k'). "
        "If no salary is mentioned, reply with exactly: not mentioned\n\n"
        f"{sample}"
    )
    raw = ask_llm(prompt).strip()
    if "not mentioned" in raw.lower() or len(raw) > 80:
        return ""
    return raw


def detect_language(text):
    if len(text.strip()) < 50:
        return "English"
    sample = text[:600].strip()
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{
            "role": "user",
            "content": (
                "What language is the following text written in? "
                "Reply with only the language name in English (e.g. 'English', 'Spanish', 'French', 'German'). "
                "No extra text, no punctuation.\n\n"
                f"Text:\n{sample}"
            )
        }]
    )
    raw = response["message"]["content"].strip().strip('"').strip("'")
    # Take only the first word in case the model adds explanation
    lang = raw.split()[0].capitalize() if raw else "English"
    return lang