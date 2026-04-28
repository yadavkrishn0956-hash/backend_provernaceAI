from fastapi import APIRouter, Request

from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    container = request.app.state.container
    checks = {
        "rsa_service": bool(container.rsa_service),
        "watermark_service": bool(container.watermark_service),
        "clip_fingerprint_service": bool(container.clip_fingerprint_service),
        "pdq_fingerprint_service": bool(container.pdq_fingerprint_service),
        "gemini_explainer_service": bool(container.gemini_explainer_service),
        "provenance_store": container.provenance_store_service.ping(),
    }
    status = "ok" if all(checks.values()) else "degraded"
    return HealthResponse(status=status, version=settings.APP_VERSION, checks=checks)
