from fastapi import APIRouter

from app.api.v1.endpoints import (
    events,
    evidence,
    health,
    investigations,
    metrics,
    releases,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(releases.router)
api_router.include_router(events.router)
api_router.include_router(metrics.router)
api_router.include_router(evidence.router)
api_router.include_router(investigations.router)