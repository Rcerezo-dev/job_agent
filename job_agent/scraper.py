# scraper.py
import re
import html
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _strip_html(text):
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


# ── JSON APIs (reliable, no scraping needed) ─────────────────────────────────

def search_remotive():
    try:
        response = requests.get("https://remotive.com/api/remote-jobs", timeout=10)
        response.raise_for_status()
        jobs = []
        for item in response.json().get("jobs", []):
            jobs.append({
                "title": item["title"],
                "company": item["company_name"],
                "location": item.get("candidate_required_location", "Remote"),
                "description": _strip_html(item.get("description", item.get("category", ""))),
                "link": item["url"],
                "source": "Remotive",
            })
        return jobs
    except Exception as e:
        print(f"  Remotive error: {e}")
        return []


def search_arbeitnow():
    try:
        response = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=10)
        response.raise_for_status()
        jobs = []
        for item in response.json().get("data", []):
            jobs.append({
                "title": item["title"],
                "company": item["company_name"],
                "location": item.get("location", "Remote"),
                "description": _strip_html(item.get("description", "")),
                "link": item["url"],
                "source": "Arbeitnow",
            })
        return jobs
    except Exception as e:
        print(f"  Arbeitnow error: {e}")
        return []


def search_jobicy():
    try:
        response = requests.get("https://jobicy.com/api/v0/jobs?count=50", timeout=10)
        response.raise_for_status()
        jobs = []
        for item in response.json().get("jobs", []):
            jobs.append({
                "title": item["jobTitle"],
                "company": item["companyName"],
                "location": item.get("jobGeo", "Remote"),
                "description": _strip_html(
                    item.get("jobDescription", item.get("jobExcerpt", ""))
                ),
                "link": item["url"],
                "source": "Jobicy",
            })
        return jobs
    except Exception as e:
        print(f"  Jobicy error: {e}")
        return []


# ── HTML scrapers ─────────────────────────────────────────────────────────────

def search_linkedin():
    """
    Uses LinkedIn's public guest-jobs endpoint (no login needed).
    May return empty results if LinkedIn rate-limits the IP.
    """
    queries = ["junior AI madrid", "data analyst junior madrid", "python junior madrid"]
    jobs = []
    seen = set()

    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    for query in queries:
        try:
            resp = requests.get(
                base_url,
                params={"keywords": query, "location": "Madrid, Spain", "start": 0, "count": 25},
                headers=HEADERS,
                timeout=12,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.find_all("div", class_="base-card"):
                title_el  = card.find(class_="base-search-card__title")
                company_el = card.find(class_="base-search-card__subtitle")
                loc_el    = card.find(class_="job-search-card__location")
                link_el   = card.find("a", class_="base-card__full-link") or card.find("a", href=True)

                if not title_el:
                    continue
                link = (link_el.get("href", "").split("?")[0]) if link_el else ""
                if not link or link in seen:
                    continue
                seen.add(link)

                jobs.append({
                    "title": title_el.text.strip(),
                    "company": company_el.text.strip() if company_el else "Unknown",
                    "location": loc_el.text.strip() if loc_el else "Madrid",
                    "description": "",
                    "link": link,
                    "source": "LinkedIn",
                })
            time.sleep(1.5)
        except Exception as e:
            print(f"  LinkedIn error: {e}")
            break

    return jobs


def search_infojobs():
    """
    Scrapes InfoJobs search results for Madrid.
    May be blocked by Cloudflare on some requests.
    """
    try:
        resp = requests.get(
            "https://www.infojobs.net/jobsearch/search-results/list.xhtml",
            params={"keyword": "junior python ai datos", "province": "madrid"},
            headers=HEADERS,
            timeout=12,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []

        for item in soup.find_all("li", class_=lambda c: c and "offer-item" in c):
            title_el   = item.find("a", class_=lambda c: c and ("js-o-link" in c or "o-link" in c))
            company_el = item.find(class_=lambda c: c and "company" in str(c).lower())
            loc_el     = item.find(class_=lambda c: c and "location" in str(c).lower())

            if not title_el:
                continue
            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = "https://www.infojobs.net" + link

            jobs.append({
                "title": title_el.text.strip(),
                "company": company_el.text.strip() if company_el else "Unknown",
                "location": loc_el.text.strip() if loc_el else "Madrid",
                "description": "",
                "link": link,
                "source": "InfoJobs",
            })
        return jobs
    except Exception as e:
        print(f"  InfoJobs error: {e}")
        return []


def search_tecnoempleo():
    """Scrapes Tecnoempleo — Spanish tech jobs board, Madrid filter."""
    queries = ["python junior", "datos junior", "AI junior"]
    jobs = []
    seen = set()

    for kw in queries:
        try:
            resp = requests.get(
                "https://www.tecnoempleo.com/busqueda-empleo.php",
                params={"te": kw, "pr": "madrid"},
                headers=HEADERS,
                timeout=12,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.find_all("div", class_=lambda c: c and "col-10" in c):
                title_el = card.find("a", href=lambda h: h and "/oferta-trabajo/" in h)
                if not title_el:
                    continue
                link = "https://www.tecnoempleo.com" + title_el["href"]
                if link in seen:
                    continue
                seen.add(link)

                company_el = card.find("a", href=lambda h: h and "/empresa/" in h)
                loc_el     = card.find("p", class_=lambda c: c and "text-gray" in c)

                jobs.append({
                    "title": title_el.text.strip(),
                    "company": company_el.text.strip() if company_el else "Unknown",
                    "location": loc_el.text.strip() if loc_el else "Madrid",
                    "description": "",
                    "link": link,
                    "source": "Tecnoempleo",
                })
            time.sleep(0.8)
        except Exception as e:
            print(f"  Tecnoempleo error: {e}")
            break

    return jobs


def search_domestika():
    """Scrapes Domestika's jobs section (design/creative/tech roles)."""
    try:
        resp = requests.get(
            "https://www.domestika.org/es/jobs",
            headers=HEADERS,
            timeout=12,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []

        for card in soup.find_all("article"):
            title_el   = card.find("h2") or card.find("h3")
            link_el    = card.find("a", href=True)
            company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
            loc_el     = card.find(class_=lambda c: c and "location" in str(c).lower())

            if not title_el or not link_el:
                continue
            link = link_el["href"]
            if not link.startswith("http"):
                link = "https://www.domestika.org" + link

            jobs.append({
                "title": title_el.text.strip(),
                "company": company_el.text.strip() if company_el else "Domestika",
                "location": loc_el.text.strip() if loc_el else "Spain",
                "description": "",
                "link": link,
                "source": "Domestika",
            })
        return jobs
    except Exception as e:
        print(f"  Domestika error: {e}")
        return []


def search_startups_madrid():
    """
    Scrapes landing.jobs filtered to Madrid — focused on startups and tech companies.
    landing.jobs is an EU startup job board with good Madrid coverage.
    """
    try:
        resp = requests.get(
            "https://landing.jobs/jobs",
            params={"search": "junior", "location_name": "Madrid", "page": 1},
            headers=HEADERS,
            timeout=12,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []

        for card in soup.find_all("article"):
            title_el   = card.find("h2") or card.find("h3")
            link_el    = card.find("a", href=True)
            company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
            loc_el     = card.find(class_=lambda c: c and "location" in str(c).lower())

            if not title_el or not link_el:
                continue
            link = link_el["href"]
            if not link.startswith("http"):
                link = "https://landing.jobs" + link

            jobs.append({
                "title": title_el.text.strip(),
                "company": company_el.text.strip() if company_el else "Unknown",
                "location": loc_el.text.strip() if loc_el else "Madrid",
                "description": "",
                "link": link,
                "source": "Startups Madrid",
            })
        return jobs
    except Exception as e:
        print(f"  Startups Madrid error: {e}")
        return []


# ── Aggregator ────────────────────────────────────────────────────────────────

def search_jobs():
    all_jobs = []

    sources = [
        ("Remotive",        search_remotive),
        ("Arbeitnow",       search_arbeitnow),
        ("Jobicy",          search_jobicy),
        ("LinkedIn",        search_linkedin),
        ("InfoJobs",        search_infojobs),
        ("Tecnoempleo",     search_tecnoempleo),
        ("Domestika",       search_domestika),
        ("Startups Madrid", search_startups_madrid),
    ]

    for name, fn in sources:
        print(f"Fetching from {name}...", end=" ", flush=True)
        jobs = fn()
        print(f"{len(jobs)} jobs")
        all_jobs.extend(jobs)

    seen = set()
    unique = []
    for job in all_jobs:
        if job["link"] not in seen:
            seen.add(job["link"])
            unique.append(job)

    print(f"\nTotal: {len(unique)} unique jobs fetched\n")
    return unique
