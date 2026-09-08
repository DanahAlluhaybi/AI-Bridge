"""
database.py
------------
This file has exactly one job: set up the connection to our database and
give the rest of the app a safe way to use it.

We're using SQLite because it's a single file on disk (ai_bridge.db) --
no server to install, no account to create, no cost. That's perfect for
learning and for a free MVP. Later, if we ever move to AWS (Phase 2,
optional), this is the ONE file that would change -- the rest of the app
doesn't need to know or care what database engine is underneath.

We use SQLAlchemy as an ORM (Object-Relational Mapper). Instead of writing
raw SQL strings everywhere, we describe our data as Python classes
(see models.py) and SQLAlchemy translates that into SQL for us. This
matters for this project specifically because later phases add several
related tables (Enterprise Systems, Use Cases, Risk Assessments, Audit
Logs...) and doing that by hand in raw SQL gets error-prone fast.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# "sqlite:///./ai_bridge.db" means: use SQLite, and store the data in a
# file called ai_bridge.db in the directory the backend is run from.
SQLALCHEMY_DATABASE_URL = "sqlite:///./ai_bridge.db"

# connect_args is SQLite-specific: by default SQLite only allows the
# thread that created a connection to use it. FastAPI can handle a
# request on a different thread, so we relax that restriction here.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# A "session" is a temporary workspace for talking to the database
# (add things, query things, then commit or roll back). SessionLocal is
# a factory that hands out new sessions when we ask for one.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class every table model (in models.py) will inherit
# from. SQLAlchemy uses it to keep track of every table we define.
Base = declarative_base()


def get_db():
    """
    This is a FastAPI "dependency". Any endpoint that needs database
    access will ask for one of these, and FastAPI calls this function
    for us. The `yield` pattern guarantees the session is always closed
    afterwards, even if the request raised an error -- so we never leak
    open database connections.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
