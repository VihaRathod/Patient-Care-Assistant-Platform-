
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.connection import engine
from database.base import Base

# Import models so SQLAlchemy registers their tables
from models.notification import Notification
from routers.documents import router as documents_router
from routers.notifications import router as notifications_router

from scheduler.scheduler import (
    start_scheduler,
    stop_scheduler
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Initial development setup.
    # We will move to Alembic migrations later.
    Base.metadata.create_all(bind=engine)

    start_scheduler()

    yield

    stop_scheduler()


app = FastAPI(
    title="Notification & Document Service",
    description="Handles appointment reminders, emails and documents",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(notifications_router)
app.include_router(documents_router)


@app.get("/")
def root():

    return {
        "message": "Notification & Document Service is running"
    }
