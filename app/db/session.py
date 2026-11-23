from collections.abc import Iterator

from sqlalchemy import create_engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

database_url = make_url(settings.database_url.get_secret_value())
if database_url.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}:
    raise ValueError("DATABASE_URL must be a PostgreSQL URL.")

engine = create_engine(database_url.set(drivername="postgresql+psycopg"), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
