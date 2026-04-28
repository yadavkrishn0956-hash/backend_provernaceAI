from io import BytesIO

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get("/assets/{asset_id}/image")
async def get_asset_image(asset_id: str, request: Request) -> StreamingResponse:
    image_bytes = request.app.state.container.provenance_store_service.get_protected_image(asset_id)
    if not image_bytes:
        raise HTTPException(status_code=404, detail="Protected image not found")
    return StreamingResponse(BytesIO(image_bytes), media_type="image/png")
