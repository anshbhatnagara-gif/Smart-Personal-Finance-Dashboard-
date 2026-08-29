"""SQLAlchemy 2.x database engine, session management, and Base definition.
Supports TiDB Cloud (MySQL-compatible) in production with connection pooling,
SSL/TLS support, and local SQLite fallback for development and offline testing.
"""

from typing import Generator, Dict, Any

# Ensure PyMySQL acts as MySQLdb if any component attempts MySQLdb import
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception:
    pass

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings


def normalize_database_url(database_url: str) -> str:
    """Return a SQLAlchemy URL that explicitly specifies the pymysql driver for MySQL."""
    raw_url = str(database_url or "").strip()
    if raw_url.startswith("mysql://"):
        return "mysql+pymysql://" + raw_url[len("mysql://"):]
    elif raw_url.startswith("mysql+mysqlconnector://"):
        return "mysql+pymysql://" + raw_url[len("mysql+mysqlconnector://"):]
    return raw_url


db_url = normalize_database_url(settings.DATABASE_URL)


# 2. Configure dialect-specific engine arguments and connection pooling
engine_kwargs: Dict[str, Any] = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True
}
connect_args: Dict[str, Any] = {}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif db_url.startswith("mysql"):
    # TiDB Cloud / MySQL connection pool optimizations
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 300  # Recycle connections every 5 min to avoid serverless timeout drops
    connect_args["charset"] = "utf8mb4"

engine_kwargs["connect_args"] = connect_args

engine = create_engine(
    db_url,
    **engine_kwargs
)


# 3. Enforce SQLite foreign key constraints when using SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if db_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Declarative Base class for all SQLAlchemy 2.x models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency yielding a transactional database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connected() -> bool:
    """Execute a lightweight query to verify active database connectivity."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_database_dialect() -> str:
    """Return the active database dialect name ('mysql', 'sqlite', etc.)."""
    return engine.dialect.name


def init_db() -> None:
    """Initialize all database tables defined in the models package."""
    # Import all models to ensure they are registered on the Base metadata
    import app.models.user  # noqa: F401
    import app.models.transaction  # noqa: F401
    import app.models.budget  # noqa: F401
    import app.models.goal  # noqa: F401
    import app.models.smart_action  # noqa: F401
    Base.metadata.create_all(bind=engine)

