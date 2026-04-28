import os
from pathlib import Path

from pydantic import BaseModel, Field
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> None:
        return None

load_dotenv()


def _runtime_path(*parts: str) -> str:
    if os.getenv("VERCEL"):
        return str(Path("/tmp", *parts))
    return str(Path(".", *parts))


class Settings(BaseModel):
    APP_NAME: str = Field(default_factory=lambda: os.getenv("APP_NAME", "Cryptographically Bound Semantic Watermark API"))
    APP_VERSION: str = Field(default_factory=lambda: os.getenv("APP_VERSION", "0.1.0"))
    API_PREFIX: str = Field(default_factory=lambda: os.getenv("API_PREFIX", "/api/v1"))
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "dev"))

    # Runtime limits tuned for prototype safety and Cloud Run defaults.
    MAX_UPLOAD_MB: int = Field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_MB", "10")))
    REQUEST_TIMEOUT_SECONDS: int = Field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60")))

    # RSA key configuration.
    RSA_PRIVATE_KEY_B64: str | None = Field(default_factory=lambda: os.getenv("RSA_PRIVATE_KEY_B64"))
    RSA_PUBLIC_KEY_B64: str | None = Field(default_factory=lambda: os.getenv("RSA_PUBLIC_KEY_B64"))
    RSA_PRIVATE_KEY_PATH: str = Field(
        default_factory=lambda: os.getenv("RSA_PRIVATE_KEY_PATH")
        or os.getenv("PRIVATE_KEY_PATH", _runtime_path("backend", "keys", "private_key.pem"))
    )
    RSA_PUBLIC_KEY_PATH: str = Field(
        default_factory=lambda: os.getenv("RSA_PUBLIC_KEY_PATH")
        or os.getenv("PUBLIC_KEY_PATH", _runtime_path("backend", "keys", "public_key.pem"))
    )
    RSA_PRIVATE_KEY_PASSPHRASE: str | None = Field(default_factory=lambda: os.getenv("RSA_PRIVATE_KEY_PASSPHRASE"))
    HMAC_SECRET_B64: str | None = Field(default_factory=lambda: os.getenv("HMAC_SECRET_B64"))
    HMAC_SECRET_PATH: str = Field(
        default_factory=lambda: os.getenv("HMAC_SECRET_PATH", _runtime_path("backend", "keys", "hmac_secret.key"))
    )

    # CLIP / transformer runtime configuration.
    # CLIP_ENABLED: bool = Field(default_factory=lambda: os.getenv("CLIP_ENABLED", "false").lower() == "true")
    # CLIP_MODEL_NAME: str = Field(default_factory=lambda: os.getenv("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32"))
    # CLIP_LOCAL_FILES_ONLY: bool = Field(
    #     default_factory=lambda: os.getenv("CLIP_LOCAL_FILES_ONLY", "true").lower() == "true"
    # )
    # MODEL_DEVICE: str = Field(default_factory=lambda: os.getenv("MODEL_DEVICE", "auto"))

    CLIP_ENABLED: bool = Field(default_factory=lambda: False)  # deprecated, kept for compat
    GEMINI_EMBED_MODEL: str = Field(
     default_factory=lambda: os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-exp-03-07")
    )
    # Gemini runtime configuration.
    GEMINI_ENABLED: bool = Field(default_factory=lambda: os.getenv("GEMINI_ENABLED", "false").lower() == "true")
    GEMINI_API_KEY: str | None = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

    # Watermark + ECC configuration.
    RS_NSYM: int = Field(default_factory=lambda: int(os.getenv("RS_NSYM", "8")))
    WATERMARK_METHOD: str = Field(default_factory=lambda: os.getenv("WATERMARK_METHOD", "dwtDct"))
    WATERMARK_MAX_PAYLOAD_BYTES: int = Field(
        default_factory=lambda: int(os.getenv("WATERMARK_MAX_PAYLOAD_BYTES", "32"))
    )
    WATERMARK_TOKEN_VERSION: int = Field(default_factory=lambda: int(os.getenv("WATERMARK_TOKEN_VERSION", "1")))

    # Local deterministic generation stub settings.
    GENERATION_WIDTH: int = Field(default_factory=lambda: int(os.getenv("GENERATION_WIDTH", "768")))
    GENERATION_HEIGHT: int = Field(default_factory=lambda: int(os.getenv("GENERATION_HEIGHT", "768")))

    # Lightweight persistence adapter configuration.
    PROVENANCE_DB_PATH: str = Field(default_factory=lambda: os.getenv("PROVENANCE_DB_PATH", _runtime_path("data", "provenance.db")))

    # Verification thresholds for authenticity decisions.
    VERIFY_PDQ_MAX_DISTANCE: int = Field(default_factory=lambda: int(os.getenv("VERIFY_PDQ_MAX_DISTANCE", "12")))
    VERIFY_CLIP_SAME_THRESHOLD: float = Field(default_factory=lambda: float(os.getenv("VERIFY_CLIP_SAME_THRESHOLD", "0.90")))
    VERIFY_CLIP_DERIVATIVE_THRESHOLD: float = Field(
        default_factory=lambda: float(os.getenv("VERIFY_CLIP_DERIVATIVE_THRESHOLD", "0.75"))
    )


settings = Settings()
