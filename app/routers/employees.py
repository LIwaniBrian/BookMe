from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_owner
from app.models import Employee, User
from app.schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse


router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    data: EmployeeCreate,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    employee = Employee(
        business_id=current_user.business_id,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        job_title=data.job_title,
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)

    return employee


@router.get(
    "/",
    response_model=list[EmployeeResponse],
)
def list_employees(
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    employees = db.query(Employee).filter(
        Employee.business_id == current_user.business_id
    ).all()

    return employees


@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.business_id == current_user.business_id,
    ).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)

    return employee


@router.delete("/{employee_id}")
def deactivate_employee(
    employee_id: int,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.business_id == current_user.business_id,
    ).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    employee.is_active = False

    db.commit()

    return {
        "message": "Employee deactivated successfully",
    }
