from pydantic import BaseModel, EmailStr, Field
from decimal import Decimal
from datetime import datetime, time


class BusinessRegistration(BaseModel):
    business_name: str = Field(min_length=2, max_length=150)
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ServiceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    duration_minutes: int = Field(gt=0)


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )
    duration_minutes: int | None = Field(default=None, gt=0)


class ServiceResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: Decimal
    duration_minutes: int
    is_active: bool

    model_config = {"from_attributes": True}


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    job_title: str | None = Field(default=None, max_length=100)


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    job_title: str | None = Field(default=None, max_length=100)


class EmployeeResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr | None
    phone: str | None
    job_title: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class AppointmentCreate(BaseModel):
    service_id: int = Field(gt=0)
    employee_id: int = Field(gt=0)
    customer_name: str = Field(min_length=2, max_length=150)
    customer_email: EmailStr | None = None
    customer_phone: str | None = Field(default=None, max_length=20)
    start_time: datetime


class AppointmentResponse(BaseModel):
    id: int
    business_id: int
    service_id: int
    employee_id: int
    customer_name: str
    customer_email: EmailStr | None
    customer_phone: str | None
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BusinessHoursCreate(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    open_time: time | None = None
    close_time: time | None = None
    is_closed: bool = False


class BusinessHoursResponse(BaseModel):
    id: int
    business_id: int
    day_of_week: int
    open_time: time | None
    close_time: time | None
    is_closed: bool

    model_config = {"from_attributes": True}
