import factory
from faker import Faker

from app.core.factory import BaseFactory
from app.user.models import User

fake = Faker()


class UserFactory(BaseFactory):
    class Meta:
        model = User

    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = factory.LazyFunction(
        lambda: fake.random_element(elements=("manager", "standard"))
    )

    created_by = factory.Faker("email")
    updated_by = factory.Faker("email")
