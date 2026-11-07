import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.db import get_db
from app.schemas import ListingCreate, ListingOut, ListingPage, Sector, Stats

router = APIRouter(prefix="/api", tags=["listings"])

def required_admin(x_api_key: str = Header(default="")) -> None:
    if not secrets.compare_digest(x_api_key, settings.admin_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@router.get("/listings", response_model=ListingPage)
def read_listings(
    sector: Sector | None = None,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total, items = crud.list_listings(db, sector, q, limit, offset)
    return ListingPage(total=total, limit=limit, offset=offset, items=items)

@router.get("/listing/{listing_id}", response_model=ListingOut)
def read_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = crud.get_listing(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")


@router.post(
    "/listings",
    response_model=ListingOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(required_admin)],
)
def add_listing(body: ListingCreate, db: Session = Depends(get_db)):
    listing = crud.create_listing(db, body)
    db.commit()
    return listing

@router.delete(
    "/listings/{listing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(required_admin)],
)
def remove_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = crud.get_listing(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    crud.delete_listing(db, listing)
    db.commit()

@router.get("/stats", response_model=Stats)
def read_stats(db: Session = Depends(get_db)):
    counts = crud.listing_counts(db)
    last_run = crud.last_fetch_run(db)
    return Stats(
        total=sum(counts.values()),
        by_sector=counts,
        last_fetch_status=last_run.status if last_run else None,
        last_fetch_finished_at=last_run.finished_at if last_run else None,
    )

