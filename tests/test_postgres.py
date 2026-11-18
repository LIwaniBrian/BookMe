import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import dotenv_values


@pytest.fixture
def postgres_session():
    database_url = (
        os.getenv("BOOKME_TEST_DATABASE_URL")
        or dotenv_values(".env").get("BOOKME_TEST_DATABASE_URL")
    )
    if not database_url:
        pytest.skip("BOOKME_TEST_DATABASE_URL is not configured")

    engine = create_engine(database_url, pool_pre_ping=True)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def test_postgres_connection(postgres_session):
    result = postgres_session.execute(text("SELECT 1")).scalar()
    assert result == 1
