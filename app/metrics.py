import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app import crud

REQUESTS = Counter(
    "http_requests_total", "HTTP requests handled", ["method", "route", "status"]
)
LATENCY = Histogram(
    "http_request_duration_seconds", "Time spent handling a request", ["method", "route"]
)
LAST_FETCH = Gauge(
    "grad_tracker_last_successful_fetch_timestamp_seconds", "Unix time of the last succesful fetch job, 0 if none",
)
LISTINGS = Gauge(
    "grad_tracker_listings", "Listings storedy, by sector", ["sector"]
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        route_label = route.path if route else "unmatched"
        LATENCY.labels(request.method, route_label).observe(time.perf_counter() - start)
        REQUESTS.labels(request.method, route_label, str(response.status_code)).inc()
        return response

def metrics_response(db: Session) -> Response:
    LAST_FETCH.set(crud.last_successful_fetch_timestamp(db))
    LISTINGS.clear()
    for sector, count in crud.listing_counts(db).items():
        LISTINGS.labels(sector).set(count)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

