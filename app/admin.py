from fastapi import FastAPI
from sqladmin import Admin

from app.database import async_engine

from app.user.admin import UserAdmin


def init_admin(app: FastAPI) -> Admin:
    admin = Admin(app, engine=async_engine)
    admin.add_view(UserAdmin)
