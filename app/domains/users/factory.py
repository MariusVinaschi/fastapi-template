"""
User factories - For testing and seeding data.
These use factory_boy for generating test data.
"""

import factory
from faker import Faker

from app.domains.base.factory import BaseFactory
from app.domains.users.models import User, APIKey

fake = Faker()


class UserFactory(BaseFactory):
    """Factory for creating User instances"""

    class Meta:
        model = User

    email = factory.Faker("email")
    role = factory.LazyFunction(lambda: fake.random_element(elements=("admin", "standard")))

    created_by = factory.Faker("email")
    updated_by = factory.Faker("email")


class APIKeyFactory(BaseFactory):
    """Factory for creating APIKey instances"""

    class Meta:
        model = APIKey

    key_hash = factory.Faker("sha256")
    user = factory.SubFactory(UserFactory)
