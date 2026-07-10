"""
Shared SlowAPI limiter instance.

Kept separate from app.api.main so route modules can use @limiter.limit without
importing the application package (avoids circular imports: main → router → routes → main).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
