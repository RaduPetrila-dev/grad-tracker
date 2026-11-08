import logging
import sys

import httpx

from app import crud
from app.config import settings
from app.db import SessionLocal
from app.jobs import reed
from app.models import FetchRun, utcnow

SEARCHES = [
    ("pharma", "pharmaceutical", True),
    ("pharma", "life sciences", True),
    ("pharma", "biotech", True),
    ("psychology", "assistant psychologist", False),
    ("psychology", "psychology", True),
]

log = logging.getLogger('fetch_listings')

def run(client: httpx.Client, api_key: str) -> FetchRun:
    db = SessionLocal()
    fetch_run = FetchRun()
    db.add(fetch_run)
    db.commit() # record the start, so a crash still leaves a trace

    seen = new = 0
    try:
        for sector, keywords, graduate in SEARCHES:
            results = reed.search(client, api_key, keywords, graduate)
            log.info("%s: %d results for %r", sector, len(results), keywords)
            for result in results:
                seen += 1
                if crud.upsert_listing(db, reed.to_listing(result, sector)):
                    new += 1
        fetch_run.status = "sucess"
    except Exception as exc:
        db.rollback()
        log.exception("fetch failed")
        fetch_run.status = "failed"
        fetch_run.error = repr(exc)[:2000]
        seen = new = 0

    fetch_run.listings_seen = seen
    fetch_run.listing_new = new
    fetch_run.finished_at = utcnow()
    db.commit()
    db.close()
    return fetch_run

def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not settings.reed_api_key:
        log.error('Set REED_API_KEY in .env firs')
        return 1
    with httpx.Client() as client:
        result = run(client, settings.reed_api_key)
    log.info("status=%s seen=%d new=%d", result.status, result.listings_seen, result.listing_new)
    return 0 if result.status == "success" else 1

if __name__ == "__main__":
    sys.exit(main())


