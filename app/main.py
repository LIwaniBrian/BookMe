
from fastapi import FastAPI

from app.config import settings


app = FastAPI(
    title=settings.app_name,
    description="A multi-tenant booking and appointment management API for small businesses in South Africa.",
    version="1.0.0",
    debug=settings.debug,
)


@app.get("/")
def root():
    return {
        "message": "Welcome to BookMe API",
        "status": "running",
    }
