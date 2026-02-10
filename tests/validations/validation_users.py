from app.domains.users.schemas import UserRead


def valid_data_from_user_object(data: dict, user: UserRead):
    assert data["email"] == user.email
    assert data["role"] == user.role


def valid_dict_from_value(data: dict, email: str, role: str):
    assert data["email"] == email
    assert data["role"] == role


def valid_dict_content(data: dict):
    assert "id" in data
    assert isinstance(data["id"], str)

    assert "email" in data
    assert isinstance(data["email"], str)

    assert "created_at" in data
    assert "updated_at" in data
