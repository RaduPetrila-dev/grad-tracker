from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import api, pages
from app.db import get_db
from app.metrics import MetricsMiddleware, metrics_response

app = FastAPI(title="UK Grad Tracker", version="1.0.0")
app.add_middleware(MetricsMiddleware)
app.include_router(api.router)
app.include_router(pages.router)



@app.get("/health", tags=["ops"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok"}

@app.get("/metrics", include_in_schema=False)
def metrics(db: Session = Depends(get_db)):
    return metrics_response(db)

