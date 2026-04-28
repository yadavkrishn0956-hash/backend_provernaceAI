import base64
import json
from typing import Any


def encode_payload(payload: dict[str, Any]) -> str:
    """Serialize payload into URL-safe base64 string for transport/storage."""
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_payload(encoded: str) -> dict[str, Any]:
    raw = base64.urlsafe_b64decode(encoded.encode("utf-8"))
    return json.loads(raw.decode("utf-8"))
