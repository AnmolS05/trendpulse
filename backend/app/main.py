"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import routes
from .ingestion.poller import start_poller, stop_event

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown lifespan events."""
    # Run database schema migrations
    from .database import engine, run_schema_migrations, SessionLocal
    run_schema_migrations(engine)
    
    # Run autonomous refactoring migration: Clear Watchlist, Brand and EntityRecommendation
    from .models import Watchlist, Brand, EntityRecommendation
    db = SessionLocal()
    try:
        db.query(Watchlist).delete()
        db.query(Brand).delete()
        db.query(EntityRecommendation).delete()
        db.commit()
    finally:
        db.close()
    
    # Start the background poller loop (interval of 10 minutes / 600s)
    start_poller(interval_seconds=600)
    yield
    # Signal the background poller thread to exit gracefully
    stop_event.set()

app = FastAPI(title="TrendPulse API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api")

@app.get("/health")
def health_check():
    """Simple API health check endpoint."""
    return {"status": "ok"}

