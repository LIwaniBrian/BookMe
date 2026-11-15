
from fastapi import FastAPI, Depends

from app.config import settings
from app.routers.auth import router as auth_router
from app.dependencies import get_current_user
from app.models import User


app = FastAPI(
    title=settings.app_name,
    description="A multi-tenant booking and appointment management API for small businesses in South Africa.",
    version="1.0.0",
    debug=settings.debug,
)

app.include_router(auth_router)


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
