from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Vambe Dashboard", version="0.1.0")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Mount static files (React build) — populated after frontend build
app.mount("/", StaticFiles(directory="backend/static", html=True), name="static")
