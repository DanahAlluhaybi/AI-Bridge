"""
database.py

Database connection setup: the SQLAlchemy engine, session factory, and
declarative base used by every model in models.py.

SQLite backs this app (a single file, ai_bridge.db, in the backend
directory). Swapping to a different database later only requires
changing SQLALCHEMY_DATABASE_URL and connect_args here -- nothing else
in the app talks to the database engine directly.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./ai_bridge.db"

# check_same_thread=False: SQLite normally restricts a connection to
# the thread that created it, but FastAPI can service a request on a
# different thread than the one that opened the session.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session and guarantees it
    gets closed afterward, even if the request handler raises.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
