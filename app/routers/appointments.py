from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_owner
from app.models import (
    Appointment,
    BusinessHours,
    Employee,
    Service,
)
from app.schemas import AppointmentCreate, AppointmentResponse

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
)


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=201,
)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_owner),
):
    service = (
        db.query(Service)
        .filter(
            Service.id == appointment_data.service_id,
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
            Employee.id == appointment_data.employee_id,
            Employee.business_id == current_user.business_id,
            Employee.is_active == True,
        )
        .with_for_update()
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    start_time = appointment_data.start_time
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
        raise HTTPException(
            status_code=400,
            detail="Business is closed on this day",
        )

    if (
        start_time.time() < business_hours.open_time
        or end_time.time() > business_hours.close_time
    ):
        raise HTTPException(
            status_code=400,
            detail="Appointment falls outside business hours",
        )

    existing_appointment = (
        db.query(Appointment)
        .filter(
            Appointment.business_id == current_user.business_id,
            Appointment.employee_id == employee.id,
            Appointment.status != "cancelled",
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        )
        .first()
    )

    if existing_appointment:
        raise HTTPException(
            status_code=409,
            detail="Employee already has an appointment at this time",
        )

    new_appointment = Appointment(
        business_id=current_user.business_id,
        service_id=service.id,
        employee_id=employee.id,
        customer_name=appointment_data.customer_name,
        customer_email=appointment_data.customer_email,
        customer_phone=appointment_data.customer_phone,
        start_time=start_time,
        end_time=end_time,
        status="pending",
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    return new_appointment


@router.get(
    "/",
    response_model=list[AppointmentResponse],
)
def get_appointments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_owner),
):
    return (
        db.query(Appointment)
        .filter(
            Appointment.business_id == current_user.business_id
        )
        .order_by(Appointment.start_time)
        .all()
    )


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_owner),
):
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.business_id == current_user.business_id,
        )
        .first()
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    return appointment


@router.patch(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_owner),
):
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.business_id == current_user.business_id,
        )
        .first()
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    if appointment.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Appointment is already cancelled",
        )

    appointment.status = "cancelled"

    db.commit()
    db.refresh(appointment)

    return appointment
