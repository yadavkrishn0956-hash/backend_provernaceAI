from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.core.config import settings
from app.schemas.common import ErrorResponse
from app.schemas.verify import LocalVerifyResponse, VerifyResponse
from app.services.verify_pipeline import VerifyPipelineService
from app.services.watermark_codec import WatermarkCodecError
from app.utils.image_io import ImageDecodeError, canonicalize_image, read_upload_image

router = APIRouter()


@router.post(
    "/verify",
    response_model=VerifyResponse,
    responses={400: {"model": ErrorResponse}},
)
async def verify_image(
    request: Request,
    image_file: UploadFile = File(...),
    asset_id_hint: str | None = Form(default=None),
) -> VerifyResponse:
    try:
        uploaded = await read_upload_image(
            image_file,
            max_bytes=settings.MAX_UPLOAD_MB * 1024 * 1024,
        )
        normalized = canonicalize_image(uploaded)
    except ImageDecodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    pipeline = VerifyPipelineService(request.app.state.container)
    try:
        return pipeline.run(image=normalized, asset_id_hint=asset_id_hint)
    except (ValueError, WatermarkCodecError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/verify/local",
    response_model=LocalVerifyResponse,
    responses={400: {"model": ErrorResponse}},
)
async def verify_image_locally(
    request: Request,
    image_file: UploadFile = File(...),
) -> LocalVerifyResponse:
    try:
        uploaded = await read_upload_image(
            image_file,
            max_bytes=settings.MAX_UPLOAD_MB * 1024 * 1024,
        )
        normalized = canonicalize_image(uploaded)
    except ImageDecodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    pipeline = VerifyPipelineService(request.app.state.container)
    try:
        return pipeline.run_local(image=normalized)
    except (ValueError, WatermarkCodecError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
