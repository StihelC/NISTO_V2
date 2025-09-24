"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import api, models
from .db import Base, engine


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="NISTO API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def notion_embed_headers(request, call_next):  # type: ignore[override]
        response = await call_next(request)
        response.headers[
            "Content-Security-Policy"
        ] = "frame-ancestors 'self' https://www.notion.so https://notion.so;"
        return response

    @app.get("/healthz")
    async def healthcheck():
        return {"status": "ok"}

    app.include_router(api.router)

    return app


app = create_app()

