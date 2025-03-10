from app.user.schemas import UserRead


def valid_data_from_user_object(data: dict, user: UserRead):
    assert data["email"] == user.email
    assert data["first_name"] == user.first_name
    assert data["last_name"] == user.last_name
    assert data["role"] == user.role


def valid_dict_from_value(
    data: dict, email: str, first_name: str, last_name: str, role: str
):
    assert data["email"] == email
    assert data["first_name"] == first_name
    assert data["last_name"] == last_name
    assert data["role"] == role


def valid_dict_content(data: dict):
    assert "id" in data
    assert isinstance(data["id"], str)

    assert "email" in data
    assert isinstance(data["email"], str)

    assert "created_at" in data
    assert "updated_at" in data
