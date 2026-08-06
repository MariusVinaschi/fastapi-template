"""
User factories - For testing and seeding data.
These use factory_boy for generating test data.
"""

import factory
from faker import Faker

from app.domains.base.factory import BaseFactory
from app.domains.users.models import APIKey, User
from app.domains.users.password import hash_password

fake = Faker()

# Known plaintext + its hash, computed once so factory-built users share a cheap
# (single argon2 call) yet real hash that login tests can authenticate against.
DEFAULT_TEST_PASSWORD = "password123"
_DEFAULT_PASSWORD_HASH = hash_password(DEFAULT_TEST_PASSWORD)


class UserFactory(BaseFactory):
    """Factory for creating User instances"""

    class Meta:
        model = User

    email = factory.Faker("email")
    role = factory.LazyFunction(lambda: fake.random_element(elements=("admin", "standard")))
    password_hash = _DEFAULT_PASSWORD_HASH

    created_by = factory.Faker("email")
    updated_by = factory.Faker("email")


class APIKeyFactory(BaseFactory):
    """Factory for creating APIKey instances"""

    class Meta:
        model = APIKey

    key_hash = factory.Faker("sha256")
    user = factory.SubFactory(UserFactory)
