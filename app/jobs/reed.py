from datetime import datetime, timezone

import httpx

SEARCH_URL = "https://www.reed.co.uk/api/1.0/search"

def search(client: httpx.Client, api_key: str, keywords: str, graduate: bool) -> list[dict]:
    params = {"keywords": keywords, "resultsToTake": 100}
    if graduate:
        params["graduate"] = "true"
    response = client.get(SEARCH_URL, params=params, auth=(api_key, ""), timeout=20)
    response.raise_for_status()
    return response.json().get("results", [])


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
        "company": result.get("employmerName"),
        "location": result.get("locationName"),
        "url": result["jobUrl"],
        "salary_min": result.get("minimumSalary"),
        "salary_max": result.get("maximumSalary"),
        "posted_at": parse_data(result.get("date")),
    }

