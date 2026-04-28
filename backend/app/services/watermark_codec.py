


from __future__ import annotations
 
import base64
import json
from threading import Lock
from typing import Any
 
import cv2
import numpy as np
from imwatermark import WatermarkDecoder, WatermarkEncoder
from PIL import Image
from reedsolo import RSCodec
 
 
class WatermarkCodecError(ValueError):
    pass
 
 
class WatermarkCodecService:
    """Pack/unpack + invisible watermark embed/extract helpers."""
 
    def __init__(
        self,
        rs_codec: RSCodec,
        encoder: WatermarkEncoder,
        decoder: WatermarkDecoder,
        *,
        method: str = "dwtDct",
        max_payload_bytes: int = 256,
    ):
        self._rs_codec = rs_codec
        self._encoder = encoder
        self._decoder = decoder
        self._method = method
        self._max_payload_bytes = max_payload_bytes
        self._lock = Lock()
 
    def pack(self, payload: dict[str, Any], signature: bytes) -> bytes:
        """Legacy envelope packer retained for compatibility with older records."""
        envelope = {
            "payload": payload,
            "signature_b64": base64.urlsafe_b64encode(signature).decode("utf-8"),
            "sig_alg": "RSA-PSS-SHA256",
        }
        return self.pack_json(envelope)
 
    def pack_token(self, token: dict[str, Any]) -> bytes:
        raw = b"".join(
            [
                int(token["v"]).to_bytes(1, "big"),
                int(str(token["asset_id"]), 16).to_bytes(4, "big"),
                int(str(token["commitment"]), 16).to_bytes(8, "big"),
                int(str(token["mini_mac"]), 16).to_bytes(2, "big"),
                int(token["issued_at"]).to_bytes(4, "big"),
            ]
        )
        encoded = bytes(self._rs_codec.encode(raw))
        if len(encoded) > self._max_payload_bytes:
            raise WatermarkCodecError(
                f"Packed token too large for watermark capacity: {len(encoded)} > {self._max_payload_bytes}"
            )
        return encoded
 
    def pack_json(self, envelope: dict[str, Any]) -> bytes:
        raw = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
        encoded = bytes(self._rs_codec.encode(raw))
        if len(encoded) > self._max_payload_bytes:
            raise WatermarkCodecError(
                f"Packed payload too large for watermark capacity: {len(encoded)} > {self._max_payload_bytes}"
            )
        return encoded
 
    def unpack(self, packed: bytes) -> tuple[dict[str, Any], bytes]:
        try:
            decoded = self._rs_codec.decode(packed)
            if isinstance(decoded, tuple):
                decoded_bytes = bytes(decoded[0])
            else:
                decoded_bytes = bytes(decoded)
            envelope = json.loads(decoded_bytes.decode("utf-8"))
            signature = base64.urlsafe_b64decode(envelope["signature_b64"].encode("utf-8"))
            payload = envelope["payload"]
            return payload, signature
        except Exception as exc:
            raise WatermarkCodecError("Failed to decode packed watermark payload") from exc
 
    def unpack_token(self, packed: bytes) -> dict[str, Any]:
        try:
            decoded = self._rs_codec.decode(packed)
            if isinstance(decoded, tuple):
                decoded_bytes = bytes(decoded[0])
            else:
                decoded_bytes = bytes(decoded)
            if len(decoded_bytes) >= 19:
                return {
                    "v": int.from_bytes(decoded_bytes[0:1], "big"),
                    "asset_id": decoded_bytes[1:5].hex(),
                    "commitment": decoded_bytes[5:13].hex(),
                    "mini_mac": decoded_bytes[13:15].hex(),
                    "issued_at": int.from_bytes(decoded_bytes[15:19], "big"),
                }
            envelope = json.loads(decoded_bytes.decode("utf-8"))
            token = envelope.get("token", envelope)
            if not isinstance(token, dict):
                raise TypeError("token must be an object")
            return token
        except Exception as exc:
            raise WatermarkCodecError("Failed to decode compact watermark token") from exc
 
    def embed(self, image: Image.Image, packed: bytes) -> Image.Image:
        if len(packed) > self._max_payload_bytes:
            raise WatermarkCodecError(
                f"Packed payload too large for embed: {len(packed)} > {self._max_payload_bytes}"
            )
 
        # Pad to the fixed max_payload_bytes length so the decoder always
        # extracts exactly max_payload_bytes * 8 bits — matching what was embedded.
        padded = packed.ljust(self._max_payload_bytes, b"\x00")
 
        bgr = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
 
        with self._lock:
            self._encoder.set_watermark("bytes", padded)
            embedded = self._encoder.encode(bgr, self._method)
 
        if embedded is None:
            raise WatermarkCodecError("Watermark embedding failed")
 
        rgb = cv2.cvtColor(embedded, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)
 
    def extract(self, image: Image.Image) -> bytes | None:
        bgr = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
 
        with self._lock:
            extracted = self._decoder.decode(bgr, self._method)
 
        if extracted is None:
            return None
 
        if isinstance(extracted, bytes):
            result = extracted
        elif isinstance(extracted, np.ndarray):
            result = extracted.tobytes()
        else:
            result = bytes(extracted)
 
        # Do NOT strip trailing \x00 bytes here — the RS codec needs the full
        # padded buffer (max_payload_bytes long) to decode correctly.
        # Only return None if the buffer is entirely zero (nothing was embedded).
        return result if any(result) else None