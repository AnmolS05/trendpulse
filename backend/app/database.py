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
    # Enable WAL mode and Foreign Keys enforcement for SQLite relational consistency
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.execute(text("PRAGMA foreign_keys=ON;"))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency to yield database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_schema_migrations(engine):
    """
    Checks the schema of existing tables and alters them dynamically 
    to add any columns defined in SQLAlchemy models but missing in the database.
    """
    import logging
    from sqlalchemy import inspect
    
    logger = logging.getLogger(__name__)
    
    # Create tables if they do not exist
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    db_dialect = engine.dialect
    
    with engine.begin() as conn:
        for table_name, table in Base.metadata.tables.items():
            if engine.url.drivername.startswith("sqlite"):
                pragma_info = conn.execute(text(f"PRAGMA table_info({table_name});")).fetchall()
                db_cols = {row[1] for row in pragma_info}
            else:
                db_cols = {col["name"] for col in inspector.get_columns(table_name)}
                
            if not db_cols:
                continue
                
            for col_name, column in table.columns.items():
                if col_name not in db_cols:
                    col_type_str = str(column.type.compile(dialect=db_dialect))
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type_str};"
                    logger.info(f"Applying migration: {sql}")
                    conn.execute(text(sql))
