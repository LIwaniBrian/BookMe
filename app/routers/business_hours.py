from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_owner
from app.models import BusinessHours
from app.schemas import BusinessHoursCreate, BusinessHoursResponse

router = APIRouter(
    prefix="/business-hours",
    tags=["Business Hours"],
)


@router.get(
    "/",
    response_model=list[BusinessHoursResponse],
)
def get_business_hours(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_owner),
):
    return (
        db.query(BusinessHours)
        .filter(
            BusinessHours.business_id == current_user.business_id
        )
        .order_by(BusinessHours.day_of_week)
        .all()
    )


@router.post(
    "/",
    response_model=BusinessHoursResponse,
    status_code=201,
)
def create_business_hours(
    hours_data: BusinessHoursCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_owner),
):
    existing_hours = (
        db.query(BusinessHours)
        .filter(
            BusinessHours.business_id == current_user.business_id,
            BusinessHours.day_of_week == hours_data.day_of_week,
        )
        .first()
    )

    if existing_hours:
        raise HTTPException(
            status_code=400,
            detail="Business hours already exist for this day",
        )

    new_hours = BusinessHours(
        business_id=current_user.business_id,
        day_of_week=hours_data.day_of_week,
        open_time=hours_data.open_time,
        close_time=hours_data.close_time,
        is_closed=hours_data.is_closed,
    )

    db.add(new_hours)
    db.commit()
    db.refresh(new_hours)

    return new_hours


@router.put(
    "/{day_of_week}",
    response_model=BusinessHoursResponse,
)
def update_business_hours(
    day_of_week: int,
    hours_data: BusinessHoursCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_owner),
):
    if day_of_week < 0 or day_of_week > 6:
        raise HTTPException(
            status_code=400,
            detail="Day of week must be between 0 and 6",
        )

    if hours_data.day_of_week != day_of_week:
        raise HTTPException(
            status_code=400,
            detail="Day in URL must match day in request body",
        )

    hours = (
        db.query(BusinessHours)
        .filter(
            BusinessHours.business_id == current_user.business_id,
            BusinessHours.day_of_week == day_of_week,
        )
        .first()
    )

    if not hours:
        raise HTTPException(
            status_code=404,
            detail="Business hours not found for this day",
        )

    hours.open_time = hours_data.open_time
    hours.close_time = hours_data.close_time
    hours.is_closed = hours_data.is_closed

    db.commit()
    db.refresh(hours)

    return hours
