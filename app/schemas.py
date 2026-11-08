from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

Sector = Literal["pharma", "psychology"]

class ListingOut(BaseModel):
    """The shape of one listings in every API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    sector: str
    title: str
    company: str | None
    location: str | None
    url: str
    salary_min: float | None
    salary_max: float | None
    salary_type: str | None
    posted_at: datetime | None
    first_seen_at: datetime


class ListingPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ListingOut]

class ListingCreate(BaseModel):
    """The body of POST /api/listings. Pydantic rejects bad inpit with a 422 before code runs"""

    sector: Sector
    title: str = Field(min_length=3, max_length=300)
    company: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    url: HttpUrl
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)

class Stats(BaseModel):
    total: int
    by_sector: dict[str, int]
    last_fetch_status: str | None
    last_fetch_finished_at: datetime | None

