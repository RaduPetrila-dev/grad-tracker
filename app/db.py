from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# One engine per process. pool_pre_ping replaces dead connections after a database restart.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    """Parent Class for every table model"""

def get_db():
    """FastAPI dependency: opens one database session per request and always closes the session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

