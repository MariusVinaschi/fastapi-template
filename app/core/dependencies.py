from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.database import get_session

CurrentSession = Annotated[async_sessionmaker, Depends(get_session)]
