from datetime import datetime

from pydantic import BaseModel


class RecordResponse(BaseModel):
    asset_id: str
    payload: dict
    signature_b64: str
    pdq_hash_hex: str
    semantic_hash_hex: str
    commitment: str | None = None
    mini_mac: str | None = None
    clip_embedding: list[float] | None = None
    created_at: datetime
    updated_at: datetime
