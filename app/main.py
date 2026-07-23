from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.opportunities import (
    router as opportunities_router,
)
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description=(
        "Track, filter, score, and save Web3 grants, "
        "bounties, hackathons, and developer opportunities."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    opportunities_router,
    prefix=settings.api_v1_prefix,
)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "documentation": "/docs",
    }