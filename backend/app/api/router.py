from fastapi import APIRouter

from app.api.routes.assets import router as assets_router
from app.api.routes.health import router as health_router
from app.api.routes.process import router as process_router
from app.api.routes.records import router as records_router
from app.api.routes.verify import router as verify_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(assets_router, tags=["assets"])
api_router.include_router(process_router, tags=["process"])
api_router.include_router(verify_router, tags=["verify"])
api_router.include_router(records_router, tags=["records"])
