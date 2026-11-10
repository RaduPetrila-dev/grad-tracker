from app.jobs import fetch_listings
from tests.test_fetch_job import fake_client

def test_metrics_page_exposes_counters(client, make_listing):
    make_listing(sector="psychology")
    client.get("/api/listings")
    body = client.get("/metrics").text
    assert 'http_requests_total{method="GET",route="/api/listings",status="200"}' in body
    assert 'grad_tracker_listings{sector="psychology"} 1.0' in body

def test_metrics_show_last_successful_fetch(client):
    assert "grad_tracker_last_successful_fetch_timestamp_seconds 0.0" in client.get("/metrics").text
    fetch_listings.run(fake_client(), "key")
    line = next(
        row
        for row in client.get("/metrics").text.splitlines()
        if row.startswith("grad_tracker_last_successful_fetch_timestamp_seconds ")
    )
    assert float(line.split()[1]) > 1_700_000_000

