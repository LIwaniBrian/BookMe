
from fastapi import FastAPI, Depends

from app.config import settings
from app.routers.auth import router as auth_router
from app.dependencies import get_current_user, get_current_business, get_current_owner
from app.models import User, Business
from app.routers.services import router as services_router
from app.routers.employees import router as employees_router
from app.routers.business_hours import router as business_hours_router
from app.routers.availability import router as availability_router
from app.routers.appointments import router as appointments_router

app = FastAPI(
    title=settings.app_name,
    description="A multi-tenant booking and appointment management API for small businesses in South Africa.",
    version="1.0.0",
    debug=settings.debug,
)

app.include_router(auth_router)
app.include_router(services_router)
app.include_router(employees_router)
app.include_router(business_hours_router)
app.include_router(availability_router)
app.include_router(appointments_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to BookMe API",
        "status": "running",
    }


@app.get("/auth/me")
def get_my_account(
    current_user: User = Depends(get_current_user),
):
    return {
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "business_id": current_user.business_id,
        "role": current_user.role,
    }


@app.get("/business/me")
def get_my_business(
    current_business: Business = Depends(get_current_business),
):
    return {
        "business_id": current_business.id,
        "business_name": current_business.name,
        "email": current_business.email,
        "phone": current_business.phone,
        "address": current_business.address,
    }


@app.get("/owner/dashboard")
def owner_dashboard(
    current_user: User = Depends(get_current_owner),
):
    return {
        "message": "Welcome to the owner dashboard",
        "user_id": current_user.id,
        "business_id": current_user.business_id,
        "role": current_user.role,
    }
