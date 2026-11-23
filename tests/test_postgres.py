
from tests.date_helpers import get_future_monday
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier
from zoneinfo import ZoneInfo

import pytest
from dotenv import dotenv_values
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.models
from app.database import Base
from app.models import Business, Service, Employee, BusinessHours
from app.schemas import AppointmentCreate
from app.routers.appointments import create_appointment


@pytest.fixture
def postgres_setup():
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

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        connection.execute(text("""
            TRUNCATE TABLE
                appointments,
                business_hours,
                employees,
                services,
                users,
                businesses
            RESTART IDENTITY CASCADE
        """))

    db = TestingSessionLocal()

    try:
        business = Business(name="Concurrency Test Business")
        db.add(business)
        db.flush()

        service = Service(
            business_id=business.id,
            name="Haircut",
            price=150.00,
            duration_minutes=45,
            is_active=True,
        )

        employee = Employee(
            business_id=business.id,
            full_name="Test Employee",
            is_active=True,
        )

        hours = BusinessHours(
            business_id=business.id,
            day_of_week=0,
            open_time=datetime.strptime("09:00", "%H:%M").time(),
            close_time=datetime.strptime("17:00", "%H:%M").time(),
            is_closed=False,
        )

        db.add_all([service, employee, hours])
        db.commit()

        yield {
            "engine": engine,
            "session_factory": TestingSessionLocal,
            "business_id": business.id,
            "service_id": service.id,
            "employee_id": employee.id,
        }

    finally:
        db.close()

        with engine.begin() as connection:
            connection.execute(text(
                "DROP TRIGGER IF EXISTS bookme_test_delay ON appointments"
            ))
            connection.execute(text(
                "DROP FUNCTION IF EXISTS bookme_test_delay_function()"
            ))

            connection.execute(text("""
                TRUNCATE TABLE
                    appointments,
                    business_hours,
                    employees,
                    services,
                    users,
                    businesses
                RESTART IDENTITY CASCADE
            """))

        engine.dispose()


def test_postgres_connection(postgres_setup):
    with postgres_setup["engine"].connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar()

    assert result == 1


def test_concurrent_bookings_cannot_double_book(postgres_setup):
    engine = postgres_setup["engine"]
    SessionLocal = postgres_setup["session_factory"]

    business_id = postgres_setup["business_id"]
    service_id = postgres_setup["service_id"]
    employee_id = postgres_setup["employee_id"]

    # Add a temporary delay to make the competing requests overlap.
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE OR REPLACE FUNCTION bookme_test_delay_function()
            RETURNS TRIGGER AS $$
            BEGIN
                PERFORM pg_sleep(2);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))

        connection.execute(text("""
            CREATE TRIGGER bookme_test_delay
            BEFORE INSERT ON appointments
            FOR EACH ROW
            EXECUTE FUNCTION bookme_test_delay_function();
        """))

    barrier = Barrier(2)

    def attempt_booking(customer_name):
        db = SessionLocal()

        try:
            barrier.wait(timeout=10)

            booking = AppointmentCreate(
                service_id=service_id,
                employee_id=employee_id,
                customer_name=customer_name,
                start_time=get_future_monday(),
            )

            appointment = create_appointment(
                appointment_data=booking,
                db=db,
                current_user=type(
                    "TestUser",
                    (),
                    {"business_id": business_id},
                )(),
            )

            return ("created", appointment.id)

        except HTTPException as exc:
            db.rollback()
            return ("rejected", exc.status_code)

        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(attempt_booking, "Customer One")
        second = executor.submit(attempt_booking, "Customer Two")

        results = [first.result(timeout=20), second.result(timeout=20)]

    assert sum(result[0] == "created" for result in results) == 1
    assert sum(result == ("rejected", 409) for result in results) == 1

    verification_session = SessionLocal()

    try:
        from app.models import Appointment

        appointments = (
            verification_session.query(Appointment)
            .filter(
                Appointment.business_id == business_id,
                Appointment.employee_id == employee_id,
            )
            .all()
        )

        assert len(appointments) == 1

    finally:
        verification_session.close()
