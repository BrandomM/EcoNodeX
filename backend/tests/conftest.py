"""Pytest fixtures for EcoNodeX tests.

Uses an in-memory SQLite database. The FastAPI lifespan (init_db + seed)
still runs against the real DB path at startup — but that's harmless since all
test CRUD operations go through the dependency-injected test session.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event as sqla_event
from sqlalchemy.orm import sessionmaker

TEST_DB_URL = "sqlite:///:memory:"

_test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})


@sqla_event.listens_for(_test_engine, "connect")
def _set_pragmas(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables on the test engine (once per session)."""
    from backend.app.database import Base
    from backend.app import models  # noqa: registers all ORM models
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def db():
    """Each test gets a fresh transaction that is rolled back on teardown."""
    conn = _test_engine.connect()
    trans = conn.begin()
    session = _TestingSession(bind=conn)
    yield session
    session.close()
    trans.rollback()
    conn.close()


@pytest.fixture()
def client(db):
    """FastAPI TestClient with the test DB session injected."""
    from backend.app.database import get_db
    from backend.app.main import app

    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
