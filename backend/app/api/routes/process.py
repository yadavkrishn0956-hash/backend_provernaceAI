from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.core.config import settings
from app.schemas.common import ErrorResponse
from app.schemas.process import ProcessResponse
from app.services.process_pipeline import ProcessPipelineService
from app.services.watermark_codec import WatermarkCodecError
from app.utils.image_io import ImageDecodeError, canonicalize_image, read_upload_image

router = APIRouter()


@router.post(
    "/process",
    response_model=ProcessResponse,
    responses={400: {"model": ErrorResponse}},
)
async def process_image(
    request: Request,
    prompt: str | None = Form(default=None),
    issuer_id: str = Form(default="prototype-issuer"),
    user_note: str | None = Form(default=None),
    image_file: UploadFile | None = File(default=None),
) -> ProcessResponse:
    has_prompt = bool(prompt and prompt.strip())
    has_image = image_file is not None

    if has_prompt == has_image:
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one input: prompt or image_file",
        )

    uploaded = None
    if has_image and image_file is not None:
        try:
            uploaded = await read_upload_image(
                image_file,
                max_bytes=settings.MAX_UPLOAD_MB * 1024 * 1024,
            )
            uploaded = canonicalize_image(uploaded)
        except ImageDecodeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    pipeline = ProcessPipelineService(request.app.state.container)
    try:
        return pipeline.run(
            prompt=prompt,
            uploaded_image=uploaded,
            issuer_id=issuer_id,
            user_note=user_note,
        )
    except (ValueError, WatermarkCodecError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
