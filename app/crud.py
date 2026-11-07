import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import FetchRun, Listing, utcnow
from app.schemas import ListingCreate

def list_listings(
        db: Session, sector: str | None, q: str | None, limit: int, offset: int
) -> tuple[int, list[Listing]]:
    query = select(Listing)
    if sector:
        query = query.where(Listing.sector == sector)
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(Listing.title.ilike(pattern), Listing.company.ilike(pattern)))

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Listing.first_seen_at.desc(), Listing.id.desc()).limit(limit).offset(offset)).all()
    return total, list(rows)

def get_listing(db: Session, listing_id: int) -> Listing | None:
    return db.get(Listing, listing_id)

def create_listing(db: Session, body: ListingCreate) -> Listing:
    listing = Listing(
            source="manual",
            external_id=uuid.uuid4().hex,
            sector=body.sector,
            title=body.title,
            company=body.company,
            location=body.location,
            url=str(body.url),
            salary_min=body.salary_min,
            salary_max=body.salary_max,
    )
    db.add(listing)
    return listing

def delete_listing(db: Session, listing: Listing) -> None:
    db.delete(listing)

def upsert_listing(db: Session, data: dict) -> bool:
    existing = db.scalar(
        select(Listing).where(
            Listing.source == data["source"], Listing.external_id == data["external_id"]
        )
    )
    if existing is None:
        db.add(Listing(**data))
        return True
    for key, value in data.items():
        setattr(existing, key, value)
    existing.last_seen_at = utcnow()
    return False

def listing_counts(db: Session) -> dict[str, int]:
    rows = db.execute(select(Listing.sector, func.count(Listing.id)).group_by(Listing.sector))
    return {sector: count for sector, count in rows}

def last_fetch_run(db: Session) -> FetchRun | None:
    return db.scalar(select(FetchRun).order_by(FetchRun.started_at.desc()).limit(1))

def last_successful_fetch_timestamp(db: Session) -> float:
    finished = db.scalar(
        select(func.max(FetchRun.finished_at)).where(FetchRun.status == "success")
    )
    return finished.timestamp() if finished else 0.0


