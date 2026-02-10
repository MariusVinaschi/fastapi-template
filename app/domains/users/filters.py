from pydantic import EmailStr

from app.domains.base.filters import BaseFilterParams
from app.domains.users.schemas import RoleEnum


class UserFilter(BaseFilterParams):
    email: EmailStr | None = None
    role: RoleEnum | None = None
    clerk_id: str | None = None
