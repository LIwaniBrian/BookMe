from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_owner
from app.models import Service, User
from app.schemas import ServiceCreate, ServiceUpdate, ServiceResponse


router = APIRouter(
    prefix="/services",
    tags=["Services"],
)


@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service(
    data: ServiceCreate,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    service = Service(
        business_id=current_user.business_id,
        name=data.name,
        description=data.description,
        price=data.price,
        duration_minutes=data.duration_minutes,
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return service


@router.get(
    "/",
    response_model=list[ServiceResponse],
)
def list_services(
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    services = db.query(Service).filter(
        Service.business_id == current_user.business_id
    ).all()

    return services


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
)
def update_service(
    service_id: int,
    data: ServiceUpdate,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.business_id == current_user.business_id,
    ).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)

    return service


@router.delete("/{service_id}")
def deactivate_service(
    service_id: int,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.business_id == current_user.business_id,
    ).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    service.is_active = False

    db.commit()

    return {
        "message": "Service deactivated successfully",
    }
