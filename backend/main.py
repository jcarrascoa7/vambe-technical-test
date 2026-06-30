import asyncio
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func

from backend.api.routes.clients import router as clients_router
from backend.api.routes.metrics import router as metrics_router
from backend.categorizer.processor import run_categorization
from backend.database import Base, SessionLocal, engine
from backend.etl.cleaner import clean, read_csv
from backend.etl.loader import load
from backend.models import Client  # noqa: F401

Base.metadata.create_all(engine)


def run_etl() -> None:
    """Run ETL pipeline if clients table is empty (idempotent)."""
    db = SessionLocal()
    try:
        count = db.query(func.count(Client.id)).scalar()
        if count > 0:
            return

        df = read_csv("data/vambe_clients_10k.csv")
        df = clean(df)
        inserted = load(df, db)
        print(f"ETL complete: {inserted} records loaded")
    finally:
        db.close()


def _has_uncategorized_records() -> bool:
    """Check if there are uncategorized records."""
    db = SessionLocal()
    try:
        count = (
            db.query(func.count(Client.id))
            .filter(Client.categorized == False)  # noqa: E712
            .scalar()
        )
        return count > 0
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown logic."""
    run_etl()

    task = None
    if _has_uncategorized_records():
        task = asyncio.create_task(run_categorization())

    yield

    if task and not task.done():
        task.cancel()


app = FastAPI(title="Vambe Dashboard", version="0.1.0", lifespan=lifespan)

app.include_router(clients_router)
app.include_router(metrics_router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Mount static files (React build) — populated after frontend build
app.mount("/", StaticFiles(directory="frontend_dist", html=True), name="static")
