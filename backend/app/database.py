"""Database connection and session setup."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Detect if SQLite is used to apply SQLite-specific connection arguments
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False, "timeout": 30}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

if is_sqlite:
    # Enable WAL mode for SQLite for better concurrency handling
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency to yield database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
