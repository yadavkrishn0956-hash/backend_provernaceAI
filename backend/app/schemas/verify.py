from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class VerificationVerdict(str, Enum):
    VERIFIED_AUTHENTIC = "VERIFIED_AUTHENTIC"
    VERIFIED_MODIFIED = "VERIFIED_MODIFIED"
    FORGED_TOKEN = "FORGED_TOKEN"
    TAMPERED_RECORD = "TAMPERED_RECORD"
    FORGED_OR_UNKNOWN = "FORGED_OR_UNKNOWN"
    UNVERIFIED_SUSPICIOUS_LAUNDERING = "UNVERIFIED_SUSPICIOUS_LAUNDERING"
    UNKNOWN_ORIGIN = "UNKNOWN_ORIGIN"
    INCONCLUSIVE = "INCONCLUSIVE"


class VerifySignalSummary(BaseModel):
    signature_valid: bool
    watermark_detected: bool
    local_mac_valid: bool | None = None
    db_record_found: bool | None = None
    commitment_valid: bool | None = None
    current_pdq_hash_hex: str | None = None
    current_semantic_hash_hex: str | None = None
    pdq_distance: int | None = None
    clip_similarity: float | None = None
    pdq_result: str | None = None
    clip_result: str | None = None


class VerifyRequest(BaseModel):
    asset_id_hint: str | None = None
    issuer_id_hint: str | None = None


class VerifyResponse(BaseModel):
    asset_id: str | None = None
    verdict: VerificationVerdict
    signals: VerifySignalSummary
    gemini_explanation: str | None = None
    reasons: list[str] = Field(default_factory=list)
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LocalVerifyResponse(BaseModel):
    local_verdict: str
    asset_id: str | None = None
    watermark_detected: bool
    mini_mac_valid: bool | None = None
    version: int | None = None
    note: str
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
