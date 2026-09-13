from uuid import uuid4

from app.rag.access import build_access_scope
from app.schemas.auth import CurrentUser


def user(role: str) -> CurrentUser:
    return CurrentUser(
        id=uuid4(), email=f"{role}@example.com", full_name="Test User",
        role=role, department_id=uuid4(), authz_version=1,
    )


def test_employee_cannot_retrieve_restricted_visibility() -> None:
    scope = build_access_scope(user("employee"))
    assert {item.value for item in scope.visibilities} == {"public", "employee"}
    assert "hr" not in {item.value for item in scope.visibilities}


def test_admin_has_every_visibility() -> None:
    scope = build_access_scope(user("admin"))
    assert {item.value for item in scope.visibilities} == {"public", "employee", "manager", "hr", "admin"}

