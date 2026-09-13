from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.entities import Employee, LeaveBalance
from app.schemas.auth import CurrentUser

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("/me")
async def my_profile(
    user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> dict:
    employee = await db.scalar(select(Employee).where(Employee.user_id == user.id))
    if not employee:
        raise HTTPException(404, detail="Employee profile not found")
    return {
        "employee_code": employee.employee_code, "full_name": user.full_name,
        "email": user.email, "role": user.role, "job_title": employee.job_title,
        "joining_date": employee.joining_date, "location": employee.location,
        "department_id": employee.department_id,
    }


@router.get("/me/leave")
async def my_leave(
    year: int = date.today().year, user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    employee = await db.scalar(select(Employee).where(Employee.user_id == user.id))
    if not employee:
        raise HTTPException(404, detail="Employee profile not found")
    balances = (
        await db.scalars(
            select(LeaveBalance).where(LeaveBalance.employee_id == employee.id, LeaveBalance.year == year)
        )
    ).all()
    return [
        {"leave_type": item.leave_type, "allocated": item.allocated, "used": item.used,
         "pending": item.pending, "available": item.allocated - item.used - item.pending}
        for item in balances
    ]

