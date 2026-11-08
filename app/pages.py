import math
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import crud
from app.db import get_db

PAGE_SIZE = 20
SECTORS = {"pharma": "Pharma and life sciences", "psychology": "Clinical psychology"}

def format_pay(salary_min: float | None, salary_max: float | None, salary_type: str | None) -> str:

    def money(value: float) -> str:
        return f"£{value:,.0f}" if value == int(value) else f"£{value:,.2f}"

    if salary_min and salary_max and salary_min != salary_max:
        text = f"{money(salary_min)} to {money(salary_max)}"
    elif salary_min or salary_max:
        text = money(salary_min or salary_max)
    else:
        return ""
    return f"{text} {salary_type}" if salary_type else text


templates = Jinja2Templates(directory=Path(__file__).parent /"templates")
templates.env.globals["format_pay"] = format_pay
router = APIRouter(include_in_schema=False)

@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    sector: str | None = None,
    q: str | None = None,
    page: int = 1,
    db: Session = Depends(get_db),
):
    if sector not in SECTORS:
        sector = None
    q = (q or "").strip()[:100]
    page = max(page, 1)

    total, items = crud.list_listings(db, sector, q or None, PAGE_SIZE, (page - 1) * PAGE_SIZE)
    return templates.TemplateResponse(
        request,
        "listings.html",
        {
            "items": items,
            "total": total,
            "sector": sector,
            "sectors": SECTORS,
            "q": q,
            "page": page,
            "pages": max(1, math.ceil(total / PAGE_SIZE)),
        },
    )
