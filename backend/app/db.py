import os
import urllib.parse
from contextlib import contextmanager
from typing import Iterator

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


conn_str = os.getenv("FABRIC_SQL_CONNECTION_STRING")
if not conn_str:
    print("⚠️  FABRIC_SQL_CONNECTION_STRING not set. Running in demo mode (no DB).")
    conn_str = None
    engine = None
else:
    # Add connection timeout for Fabric SQL
    # For ActiveDirectoryInteractive, allow 120s for user to complete browser login
    if "Connection Timeout=" not in conn_str:
        conn_str += ";Connection Timeout=120"

    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}",
        pool_pre_ping=True,          # Test connections before use
        pool_recycle=3600,           # Recycle connections after 1 hour
        pool_size=5,                 # Allow 5 concurrent connections
        max_overflow=10,             # Queue up to 10 additional connections
        pool_timeout=120,            # Wait up to 120s for a connection (ActiveDirectoryInteractive needs time for user login)
        connect_args={"timeout": 120},  # ODBC connection timeout (allow time for browser-based auth)
        echo_pool=False,             # Set to True for debugging connection pool issues
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()


@contextmanager
def get_session() -> Iterator[Session]:
    """Get a SQLAlchemy session with automatic commit/rollback."""
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Set FABRIC_SQL_CONNECTION_STRING to enable."
        )
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

