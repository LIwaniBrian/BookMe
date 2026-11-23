from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from app.database import get_db
from app.dependencies import get_current_owner
from app.models import (
    Appointment,
    BusinessHours,
    Employee,
    Service,
)
BUSINESS_TIMEZONE = ZoneInfo("Africa/Johannesburg")
router = APIRouter(
    prefix="/availability",
    tags=["Availability"],
)


@router.get("/")
def check_availability(
    service_id: int,
    employee_id: int,
    start_time: datetime,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_owner),
):
    if start_time.tzinfo is None or start_time.utcoffset() is None:
        raise HTTPException(
            status_code=422,
            detail="Appointment time must include a timezone.",
        )

    # Convert to South African business time.
    start_time = (
        start_time
        .astimezone(BUSINESS_TIMEZONE)
        .replace(tzinfo=None)
    )

    if start_time <= datetime.now(BUSINESS_TIMEZONE).replace(tzinfo=None):
        return {
            "available": False,
            "reason": "Appointments cannot be booked in the past",
        }

    service = (
        db.query(Service)
        .filter(
            Service.id == service_id,
            Service.business_id == current_user.business_id,
            Service.is_active == True,
        )
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == employee_id,
            Employee.business_id == current_user.business_id,
            Employee.is_active == True,
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    end_time = start_time + timedelta(
        minutes=service.duration_minutes
    )

    weekday = start_time.weekday()

    business_hours = (
        db.query(BusinessHours)
        .filter(
            BusinessHours.business_id == current_user.business_id,
            BusinessHours.day_of_week == weekday,
        )
        .first()
    )

    if not business_hours or business_hours.is_closed:
        return {
            "available": False,
            "reason": "Business is closed on this day",
        }

    if (
        start_time.time() < business_hours.open_time
        or end_time.time() > business_hours.close_time
    ):
        return {
            "available": False,
            "reason": "Appointment falls outside business hours",
        }

    existing_appointment = (
        db.query(Appointment)
        .filter(
            Appointment.business_id == current_user.business_id,
            Appointment.employee_id == employee_id,
            Appointment.status != "cancelled",
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        )
        .first()
    )

    if existing_appointment:
        return {
            "available": False,
            "reason": "Employee already has an appointment at this time",
        }

    return {
        "available": True,
        "start_time": start_time,
        "end_time": end_time,
    }
