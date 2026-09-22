"""Fixture: a service reaching into a foreign repository. Must be rejected."""

from repoleak.domains.users.repository import UserRepository

used = UserRepository
