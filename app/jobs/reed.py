from datetime import datetime, timezone

import httpx

SEARCH_URL = "https://www.reed.co.uk/api/1.0/search"
JOB_URL = "https://www.reed.co.uk/api/1.0/jobs/{job_id}"



def search(client: httpx.Client, api_key: str, keywords: str, graduate: bool) -> list[dict]:
    params = {"keywords": keywords, "resultsToTake": 100}
    if graduate:
        params["graduate"] = "true"
    response = client.get(SEARCH_URL, params=params, auth=(api_key, ""), timeout=20)
    response.raise_for_status()
    return response.json().get("results", [])

def details(client: httpx.Client, api_key: str, job_id: str) -> dict:
    response = client.get(JOB_URL.format(job_id=job_id), auth=(api_key, ""), timeout=20)
    response.raise_for_status()
    return response.json()

def salary_type(record: dict) -> str | None:
    value = record.get("salaryType")
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().lower()[:20]


def parse_data(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%d/%m/%Y").replace(tzinfo=timezone.utc)

def to_listing(result: dict, sector: str) -> dict:
    return {
        "source": "reed",
        "external_id": str(result["jobId"]),
        "sector": sector,
        "title": (result.get("jobTitle") or "")[:300],
        "company": result.get("employerName"),
        "location": result.get("locationName"),
        "url": result["jobUrl"],
        "salary_min": result.get("minimumSalary"),
        "salary_max": result.get("maximumSalary"),
        "posted_at": parse_data(result.get("date")),
    }

