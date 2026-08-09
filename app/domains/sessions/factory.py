"""
Refresh session factory - For testing and seeding data.
"""

import uuid
from datetime import UTC, datetime, timedelta

import factory

from app.domains.base.factory import BaseFactory
from app.domains.sessions.models import RefreshSession
from app.domains.users.factory import UserFactory


class RefreshSessionFactory(BaseFactory):
    """Factory for creating RefreshSession instances"""

    class Meta:
        model = RefreshSession

    token_hash = factory.Faker("sha256")
    family_id = factory.LazyFunction(uuid.uuid4)
    expires_at = factory.LazyFunction(lambda: datetime.now(UTC) + timedelta(days=7))
    used_at = None
    revoked_at = None

    user = factory.SubFactory(UserFactory)
