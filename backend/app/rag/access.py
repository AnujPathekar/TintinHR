from dataclasses import dataclass
from uuid import UUID

from app.models.entities import Role, Visibility
from app.schemas.auth import CurrentUser

ROLE_VISIBILITY: dict[Role, tuple[Visibility, ...]] = {
    Role.EMPLOYEE: (Visibility.PUBLIC, Visibility.EMPLOYEE),
    Role.MANAGER: (Visibility.PUBLIC, Visibility.EMPLOYEE, Visibility.MANAGER),
    Role.HR: (Visibility.PUBLIC, Visibility.EMPLOYEE, Visibility.MANAGER, Visibility.HR),
    Role.ADMIN: tuple(Visibility),
}


@dataclass(frozen=True)
class AccessScope:
    user_id: UUID
    role: Role
    department_id: UUID | None
    authz_version: int
    visibilities: tuple[Visibility, ...]

    @property
    def cache_key(self) -> str:
        department = str(self.department_id) if self.department_id else "global"
        return f"{self.user_id}:{self.role.value}:{department}:v{self.authz_version}"


def build_access_scope(user: CurrentUser) -> AccessScope:
    role = Role(user.role)
    return AccessScope(user.id, role, user.department_id, user.authz_version, ROLE_VISIBILITY[role])

