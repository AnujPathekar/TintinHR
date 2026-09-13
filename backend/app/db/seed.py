import asyncio
from datetime import date
from uuid import uuid4

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.entities import Department, Employee, Holiday, LeaveBalance, Role, User

DEMO_PASSWORD = "TintinHR@123"


async def seed() -> None:
    async with SessionLocal() as db:
        if await db.scalar(select(User.id).limit(1)):
            print("Database already contains users; seed skipped.")
            return
        engineering = Department(id=uuid4(), name="Engineering", code="ENG")
        people = Department(id=uuid4(), name="People Operations", code="HR")
        db.add_all([engineering, people])
        users = [
            User(id=uuid4(), email="employee@tintinhr.demo", full_name="Aarav Sharma", password_hash=hash_password(DEMO_PASSWORD), role=Role.EMPLOYEE),
            User(id=uuid4(), email="manager@tintinhr.demo", full_name="Meera Rao", password_hash=hash_password(DEMO_PASSWORD), role=Role.MANAGER),
            User(id=uuid4(), email="hr@tintinhr.demo", full_name="Kavya Iyer", password_hash=hash_password(DEMO_PASSWORD), role=Role.HR),
            User(id=uuid4(), email="admin@tintinhr.demo", full_name="Dev Admin", password_hash=hash_password(DEMO_PASSWORD), role=Role.ADMIN),
        ]
        db.add_all(users)
        await db.flush()
        manager = Employee(
            id=uuid4(), user_id=users[1].id, employee_code="TIN1002", department_id=engineering.id,
            joining_date=date(2022, 4, 18), job_title="Engineering Manager", location="Bengaluru",
        )
        employee = Employee(
            id=uuid4(), user_id=users[0].id, employee_code="TIN1001", department_id=engineering.id,
            manager_id=manager.id, joining_date=date(2024, 7, 15), job_title="Software Engineer", location="Bengaluru",
        )
        hr = Employee(
            id=uuid4(), user_id=users[2].id, employee_code="TIN2001", department_id=people.id,
            joining_date=date(2021, 2, 1), job_title="HR Business Partner", location="Bengaluru",
        )
        admin = Employee(
            id=uuid4(), user_id=users[3].id, employee_code="TIN9001", department_id=people.id,
            joining_date=date(2020, 1, 6), job_title="Platform Administrator", location="Bengaluru",
        )
        db.add_all([manager, employee, hr, admin])
        await db.flush()
        current_year = date.today().year
        db.add_all([
            LeaveBalance(id=uuid4(), employee_id=employee.id, leave_type="Casual Leave", year=current_year, allocated=12, used=4, pending=1),
            LeaveBalance(id=uuid4(), employee_id=employee.id, leave_type="Sick Leave", year=current_year, allocated=10, used=2, pending=0),
            LeaveBalance(id=uuid4(), employee_id=manager.id, leave_type="Casual Leave", year=current_year, allocated=12, used=3, pending=0),
            Holiday(id=uuid4(), name="Republic Day", holiday_date=date(current_year, 1, 26), location=None, is_optional=False),
            Holiday(id=uuid4(), name="Karnataka Rajyotsava", holiday_date=date(current_year, 11, 1), location="Bengaluru", is_optional=False),
        ])
        await db.commit()
        print("Seed complete.")
        print("Users: employee/manager/hr/admin @tintinhr.demo")
        print(f"Development-only password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())

