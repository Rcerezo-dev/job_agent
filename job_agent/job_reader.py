import requests
from bs4 import BeautifulSoup


def get_job_text(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers, timeout=10)

        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text(separator=" ", strip=True)

        return text[:8000]

    except Exception as e:
        return ""