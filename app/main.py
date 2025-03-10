import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin import init_admin
from app.config import settings
from app.router import api_router

log = logging.getLogger("uvicorn")


def create_application() -> FastAPI:
    """Get Fastapi application

    This is the main constructor of an application

    :return: application
    """
    app = FastAPI(
        title="FastAPI Template",
        version=settings.VERSION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
    )
    app.include_router(router=api_router, prefix=settings.API_V1_STR)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_application()
init_admin(app)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD
    )
