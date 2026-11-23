import pytest
import app.models

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.main import app
from app.database import Base, get_db


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def get_future_monday():
    timezone = ZoneInfo("Africa/Johannesburg")
    now = datetime.now(timezone)

    days_until_monday = (7 - now.weekday()) % 7

    # Always choose a Monday in the future.
    if days_until_monday == 0:
        days_until_monday = 7

    future_monday = now.date() + timedelta(days=days_until_monday)

    return datetime.combine(
        future_monday,
        time(10, 0),
        tzinfo=timezone,
    )
