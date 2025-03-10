from sqladmin import ModelView

from app.user.models import User


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.email,
    ]

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    column_searchable_list = [User.id, User.email]

    page_size = 50
    page_size_options = [25, 50, 100, 200]
