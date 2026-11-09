import copy

import httpx
import pytest

from app.jobs import fetch_listings

FAKE_RESULTS = {
    "results": [
        {
            "jobId": 4001,
            "employerName": "GSK",
            "jobTitle": "Graduate Pharmaceutical Scientist",
            "locationName": "Stevenage",
            "minimumSalary": 30000.0,
            "maximumSalary": 32000.0,
            "date": "01/11/2026",
            "jobUrl": "https://www.reed.co.uk/jobs/graduate-pharmaceutical-scientist/4001",
        },
        {
            "jobId": 4002,
            "employerName": "NHS Trust",
            "jobTitle": "Assistant Psychologist",
            "locationName": "Manchester",
            "minimumSalary": None,
            "maximumSalary": None,
            "date": "02/11/2026",
            "jobUrl": "https://www.reed.co.uk/jobs/assistant-psychologist/4002",
        },
    ],
    "totalResults": 2,
}

DETAILS = {4001: {"jobId": 4001, "salaryType": "Per Annum"}}

def fake_client(status_code=200, payload=FAKE_RESULTS, details=DETAILS, details_status=200, calls=None):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "www.reed.co.uk"
        assert request.headers["authorization"].startswith("Basic")
        if request.url.path.startswith("/api/1.0/jobs/"):
            job_id = int(request.url.path.rsplit("/", 1)[1])
            if calls is not None:
                calls.append(job_id)
            return httpx.Response(details_status, json=details.get(job_id, {}))
        return httpx.Response(status_code, json=payload)
    return httpx.Client(transport=httpx.MockTransport(handler))

def test_first_run_stores_new_listings(client):
    run = fetch_listings.run(fake_client(), "key")
    assert run.status == "success"
    assert run.listing_new == 2
    assert run.listings_seen == 10

    items = client.get("/api/listings").json()["items"]
    assert {item["title"] for item in items} == {
        "Graduate Pharmaceutical Scientist",
        "Assistant Psychologist",
    }

def test_second_run_adds_nothing_new(client):
    fetch_listings.run(fake_client(), "key")
    calls = []
    second = fetch_listings.run(fake_client(calls=calls), "key")
    assert second.listing_new == 0
    assert client.get("/api/listings").json()["total"] == 2
    assert calls == []

def test_first_run_stores_salary_period(client):
    calls = []
    fetch_listings.run(fake_client(calls=calls), "key", pause = 0)
    assert calls == [4001]
    periods = {item["title"]: item["salary_type"] for item in client.get("/api/listings").json()["items"]}
    assert periods == {"Graduate Pharmaceutical Scientist": "per annum", "Assistant Psychologist": None}

def test_details_failure_keeps_the_run(client):
    run = fetch_listings.run(fake_client(details_status=500), "key", pause=0)
    assert run.status == "success"
    assert run.listing_new == 2
    items = client.get("/api/listings", params={"sector": "pharma"}).json()["items"]
    assert items[0]["salary_type"] is None

def test_pay_change_looks_up_period_again(client):
    fetch_listings.run(fake_client(), "key", pause=0)
    changed = copy.deepcopy(FAKE_RESULTS)
    changed["results"][0]["minimumSalary"] = 150.0
    changed["results"][0]["maximumSalary"] = 180.0
    day_rate = {4001: {"jobId": 4001, "salaryType": "per day"}}
    fetch_listings.run(fake_client(payload=changed, details=day_rate), "key", pause=0)
    items = client.get("/api/listings", params={"sector": "pharma"}).json()["items"]
    assert items[0]["salary_type"] == "per day"

def test_api_error_marks_run_failed(client):
    run = fetch_listings.run(fake_client(status_code=401), "bad-key")
    assert run.status == "failed"
    assert "401" in run.error
    assert client.get("/api/stats").json()["last_fetch_status"] == "failed"

@pytest.mark.parametrize(
    ("title", "sector", "expected"),
    [
        ("Graduate Analytical Chemist", "pharma", True),
        ("2027 Pfizer Grange Castle Graduate Programme", "pharma", True),
        ("Junior Software Developer", "pharma", False),
        ("Assistant Psychologist", "psychology", True),
        ("Careers Coach", "psychology", False),
        ("Consultant Psychologist", "psychology", False),
    ],
)
def test_is_relevant(title, sector, expected):
    assert fetch_listings.is_relevant(title, sector) is expected
