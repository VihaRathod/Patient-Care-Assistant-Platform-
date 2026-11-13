
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured in .env")


# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# Create database session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


# Dependency to provide database sessions
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
