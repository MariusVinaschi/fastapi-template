from faker import Faker

fake = Faker()


def generate_member_data(organization_id: str, user_id: str) -> dict:
    return {
        "gender": fake.random_element(
            elements=(
                "male",
                "female",
            )
        ),
        "role": fake.random_element(
            elements=(
                "manager",
                "standard",
                "contact",
                "customer",
                "prospect",
                "supplier",
                "insurer",
            )
        ),
        "phone": "+447911123456",
        "informations": fake.text(max_nb_chars=100),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "is_borderer": fake.boolean(50),
        "language": fake.random_element(
            elements=(
                "fr",
                "en",
                "ja",
                "it",
            )
        ),
        "user_id": user_id,
        "organization_id": organization_id,
        "created_by": "test",
        "updated_by": "test",
    }


def generate_update_member_data() -> dict:
    return {
        "gender": fake.random_element(
            elements=(
                "male",
                "female",
            )
        ),
        "phone": "+447911123456",
        "informations": fake.text(max_nb_chars=100),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "is_borderer": fake.boolean(50),
        "language": fake.random_element(
            elements=(
                "fr",
                "en",
                "ja",
                "it",
            )
        ),
    }
