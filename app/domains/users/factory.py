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
    configuration = factory.LazyFunction(
        lambda: {
            "widgets": [
                {
                    "id": fake.random_int(min=1, max=100),
                    "x": fake.random_int(min=0, max=100),
                    "y": fake.random_int(min=0, max=100),
                }
                for _ in range(fake.random_int(min=1, max=5))
            ]
        }
    )

    created_by = factory.Faker("email")
    updated_by = factory.Faker("email")


class APIKeyFactory(BaseFactory):
    """Factory for creating APIKey instances"""

    class Meta:
        model = APIKey

    key_hash = factory.Faker("sha256")
    user = factory.SubFactory(UserFactory)

