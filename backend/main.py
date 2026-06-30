from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown logic."""
    run_etl()
    yield


app = FastAPI(title="Vambe Dashboard", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Mount static files (React build) — populated after frontend build
app.mount("/", StaticFiles(directory="backend/static", html=True), name="static")
