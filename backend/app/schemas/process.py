from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class InputMode(str, Enum):
    PROMPT = "prompt"
    UPLOAD = "upload"


class SignatureAlgorithm(str, Enum):
    RSA_PSS_SHA256 = "RSA-PSS-SHA256"


class ProcessRequest(BaseModel):
    prompt: str | None = None
    issuer_id: str = Field(default="prototype-issuer")
    user_note: str | None = None

    @model_validator(mode="after")
    def validate_prompt_if_present(self) -> "ProcessRequest":
        if self.prompt is not None and not self.prompt.strip():
            raise ValueError("prompt cannot be empty when provided")
        return self


class ProcessResponse(BaseModel):
    asset_id: str
    input_mode: InputMode
    signature_alg: SignatureAlgorithm = SignatureAlgorithm.RSA_PSS_SHA256
    watermark_version: str = "invisible-watermark-v1"
    protected_image_ref: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str = "Protected image generated successfully"
