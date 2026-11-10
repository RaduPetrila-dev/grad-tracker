# UK Grad Tracker

![CI](https://github.com/RaduPetrila-dev/grad-tracker/actions/workflows/ci.yml/badge.svg)

A web app listing graduate roles in UK pharma, life sciences and clinical psychology. A daily job pulls new roles from the Reed.co.uk jobs API into PostgreSQL, a FastAPI service serves them as a web page and a REST API, and Prometheus watches the whole system.

> **Status:** in active development. Phases 1 to 10 of 11 are complete. Continuous deployment comes next.

## Features

- Listings page with a sector filter, title and company search, and pages of 20
- REST API with interactive docs at `/docs`
- Daily fetch at 06:15 UTC: five Reed searches, a title filter to drop off-topic and senior roles, and an upsert keyed on the Reed job id, so reruns never create duplicates
- Pay shown with its period, such as "£93 to £120 per day", read from Reed's details endpoint
- Prometheus metrics at `/metrics` and three alert rules, each covered by unit tests

## Architecture

```
Reed API ──► fetch job (cron, 06:15 UTC) ──► PostgreSQL (RDS)
                                                  │
browser / curl ──► FastAPI app (Docker, EC2) ◄────┘
                         │
                   /metrics ──► Prometheus ──► alert rules
```

## Tech stack

| Area | Tools |
|---|---|
| Language | Python 3.13 |
| Web | FastAPI, Uvicorn, Jinja2, Pico CSS |
| Data | PostgreSQL 17, SQLAlchemy 2, Alembic |
| Testing | pytest, httpx MockTransport, promtool |
| Infrastructure | Docker, Docker Compose, AWS EC2, Amazon RDS |
| CI | GitHub Actions |
| Monitoring | Prometheus |

## API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/listings?sector=&q=&limit=&offset=` | none | One page of listings plus the total |
| GET | `/api/listings/{id}` | none | One listing |
| POST | `/api/listings` | `X-API-Key` | Add a listing by hand |
| DELETE | `/api/listings/{id}` | `X-API-Key` | Remove a listing |
| GET | `/api/stats` | none | Counts by sector and the last fetch run |
| GET | `/health` | none | 200 when the app and database both answer, 503 otherwise |
| GET | `/metrics` | none | Prometheus metrics |

## Run locally

You need Docker and a free Reed API key from [reed.co.uk/developers](https://www.reed.co.uk/developers/jobseeker).

```bash
git clone https://github.com/RaduPetrila-dev/grad-tracker.git
cd grad-tracker
cp .env.example .env          # add REED_API_KEY and a new ADMIN_API_KEY
docker compose up -d --build  # Postgres, the app and Prometheus
docker compose run --rm app python -m app.jobs.fetch_listings
```

Then open:

- http://localhost:8000 for the listings page
- http://localhost:8000/docs for the API docs
- http://localhost:9090 for Prometheus

## Tests

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
docker compose up -d db
pytest -v
```

32 tests cover the API, the fetch job (with Reed mocked by `httpx.MockTransport`), the page and the metrics. The alert rules have their own tests:

```bash
docker run --rm -v "$PWD/monitoring:/etc/prometheus" --entrypoint promtool \
  prom/prometheus:v3.16.0 test rules /etc/prometheus/alerts_test.yml
```

GitHub Actions runs both on every pull request. `main` accepts changes only through a pull request with green checks.

## Monitoring

| Alert | Fires when |
|---|---|
| AppDown | Prometheus fails every scrape for 2 minutes |
| FetchJobStale | No successful fetch job in 26 hours |
| HighErrorRate | More than 5% of requests return a 5xx error for 10 minutes |

Metrics: `http_requests_total`, `http_request_duration_seconds`, `grad_tracker_listings` and `grad_tracker_last_successful_fetch_timestamp_seconds`.

## Deployment

The app runs in Docker on an AWS EC2 t3.micro, with the database on Amazon RDS. RDS has no public access: only the server reaches port 5432. Prometheus listens on localhost only and opens through an SSH tunnel. Database migrations run on every container start.

Deploys are manual for now. On the server:

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Continuous deployment is the next phase.

## Roadmap

- [x] FastAPI app, PostgreSQL models and Alembic migrations
- [x] REST API with API-key auth on writes
- [x] Daily Reed fetch job with a relevance filter and salary periods
- [x] Listings page
- [x] Test suite (32 tests)
- [x] Docker and Docker Compose
- [x] GitHub Actions CI, pull requests and branch protection
- [x] Deployment on AWS EC2 and RDS
- [x] Prometheus metrics and tested alert rules
- [ ] Continuous deployment: prebuilt images on GitHub Container Registry, pulled by the server
- [ ] HTTPS with a custom domain

## Data source

Job listings come from the [Reed.co.uk Jobseeker API](https://www.reed.co.uk/developers/jobseeker).
