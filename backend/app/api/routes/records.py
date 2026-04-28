from fastapi import APIRouter, HTTPException, Request

from app.schemas.records import RecordResponse

router = APIRouter()


@router.get("/records/{asset_id}", response_model=RecordResponse)
async def get_record(asset_id: str, request: Request) -> RecordResponse:
    record = request.app.state.container.provenance_store_service.get_record(asset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return RecordResponse(**record)
