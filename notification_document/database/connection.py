
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings


if not settings.DATABASE_URL:
    raise ValueError(
        "NOTIFICATION_DATABASE_URL is not configured"
    )


database_url = settings.DATABASE_URL.replace(
    "postgresql://",
    "postgresql+psycopg2://",
    1
)

engine = create_engine(
    database_url,
    pool_pre_ping=True
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
