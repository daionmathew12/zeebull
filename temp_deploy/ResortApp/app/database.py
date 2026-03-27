from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env file from the parent directory (ResortApp/.env)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"Loaded .env from: {env_path.absolute()}")
else:
    print(f"Warning: .env file not found at {env_path.absolute()}")

# Fallback: also try loading from current directory
if not os.getenv("DATABASE_URL"):
    load_dotenv(override=True)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if SQLALCHEMY_DATABASE_URL:
    print(f"Database URL loaded: {SQLALCHEMY_DATABASE_URL[:50]}...")

# Allow overriding with local postgres superuser (useful when regular user lacks perms)
def _str_to_bool(value: str) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")

if os.getenv("USE_LOCAL_POSTGRES_USER") and _str_to_bool(os.getenv("USE_LOCAL_POSTGRES_USER")):
    pg_user = os.getenv("LOCAL_PG_USER", "postgres")
    pg_password = os.getenv("LOCAL_PG_PASSWORD", "")
    pg_host = os.getenv("LOCAL_PG_HOST", "localhost")
    pg_port = os.getenv("LOCAL_PG_PORT", "5432")
    pg_db = os.getenv("LOCAL_PG_DB", "orchid")
    auth = f"{pg_user}:{pg_password}@" if pg_password else f"{pg_user}@"
    SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{auth}{pg_host}:{pg_port}/{pg_db}"
    print(f"Overriding DATABASE_URL with local postgres superuser '{pg_user}' at {pg_host}:{pg_port}/{pg_db}")

# Provide default SQLite database if DATABASE_URL is still not set
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./orchid.db"
    print(f"Warning: DATABASE_URL not found in environment. Using default: {SQLALCHEMY_DATABASE_URL}")

# Add SSL parameters and connection pool settings to fix connection issues
# Increased pool size for production stability
# SQLite doesn't support sslmode, so we check if it's SQLite
connect_args = {}
if SQLALCHEMY_DATABASE_URL and not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "sslmode": "disable",  # Disable SSL for local connections
        "connect_timeout": 10,  # Connection timeout in seconds
        "options": "-c statement_timeout=60000"  # 60 second statement timeout (increased for large queries)
    }
else:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_size=50,  # Increased pool size to prevent exhaustion
    max_overflow=50,  # Increased overflow
    pool_pre_ping=True,  # Verify connections before use (fixes connection drops)
    pool_recycle=1800,  # Recycle connections after 30 minutes to prevent stale connections
    pool_timeout=60,  # Increased timeout for getting connection from pool
    echo=False,  # Set to True for SQL query logging
    execution_options={
        "isolation_level": "READ COMMITTED"  # Better concurrency with read committed
    } if SQLALCHEMY_DATABASE_URL and not SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
