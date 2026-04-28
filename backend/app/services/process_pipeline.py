from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

import numpy as np
from PIL import Image

from app.core.config import settings
from app.core.container import AppContainer
from app.schemas.process import InputMode, ProcessResponse
from app.utils.clocks import utc_now
from app.utils.ids import generate_asset_id
from app.utils.image_io import canonicalize_image, image_to_png_bytes


class ProcessPipelineService:
    """Converged prompt/upload processing -> sign -> pack -> embed pipeline."""

    def __init__(self, container: AppContainer):
        self._container = container

    @staticmethod
    def _pdq_hash_to_hex(pdq_hash: np.ndarray) -> str:
        bits = "".join(str(int(v)) for v in np.asarray(pdq_hash).astype(np.uint8).tolist())
        return format(int(bits, 2), "064x")

    @staticmethod
    def _semantic_hash_hex(embedding: np.ndarray, nbits: int = 64) -> str:
        vec = np.asarray(embedding, dtype=np.float32)[:nbits]
        bits = "".join("1" if float(v) >= 0.0 else "0" for v in vec)
        return format(int(bits, 2), "016x")

    def run(
        self,
        *,
        prompt: str | None,
        uploaded_image: Image.Image | None,
        issuer_id: str,
        user_note: str | None,
    ) -> ProcessResponse:
        has_prompt = bool(prompt and prompt.strip())
        mode = InputMode.PROMPT if has_prompt else InputMode.UPLOAD

        if mode is InputMode.PROMPT:
            source_image = self._container.image_generation_service.generate(prompt or "")
        else:
            if uploaded_image is None:
                raise ValueError("uploaded_image is required for upload mode")
            source_image = uploaded_image

        canonical = canonicalize_image(source_image)
        original_png = image_to_png_bytes(canonical)
        asset_id = generate_asset_id()
        created_at = utc_now()
        issued_at = int(created_at.timestamp())

        pdq_hash, pdq_quality = self._container.pdq_fingerprint_service.hash_image(canonical)
        clip_embedding = self._container.clip_fingerprint_service.embedding(canonical)
        pdq_hash_hex = self._pdq_hash_to_hex(pdq_hash)
        semantic_hash_hex = self._semantic_hash_hex(clip_embedding)

        payload: dict[str, Any] = {
            "asset_id": asset_id,
            "issuer_id": issuer_id,
            "input_mode": mode.value,
            "created_at": created_at.isoformat(),
            "timestamp": issued_at,
            "prompt_sha256": hashlib.sha256((prompt or "").strip().encode("utf-8")).hexdigest() if has_prompt else None,
            "user_note": user_note,
            "watermark_version": f"compact-token-v{settings.WATERMARK_TOKEN_VERSION}",
            "sig_alg": self._container.rsa_service.algorithm,
            "image_hash": hashlib.sha256(original_png).hexdigest(),
            "pdq_hash_hex": pdq_hash_hex,
            "semantic_hash_hex": semantic_hash_hex,
        }

        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        signature = self._container.rsa_service.sign(payload_bytes)
        commitment = self._container.commitment_service.build(asset_id=asset_id, signature=signature)
        mini_mac = self._container.mini_mac_service.build(asset_id=asset_id, issued_at=issued_at)
        token = {
            "v": settings.WATERMARK_TOKEN_VERSION,
            "asset_id": asset_id,
            "commitment": commitment,
            "mini_mac": mini_mac,
            "issued_at": issued_at,
        }
        packed = self._container.watermark_service.pack_token(token)
        protected_image = self._container.watermark_service.embed(canonical, packed)

        protected_png = image_to_png_bytes(protected_image)
        protected_ref = f"{settings.API_PREFIX}/assets/{asset_id}/image"

        assets = self._container.cache.setdefault("assets", {})
        assets[asset_id] = {
            "payload": payload,
            "pdq_hash": pdq_hash.astype(np.uint8).tolist(),
            "pdq_quality": int(pdq_quality),
            "clip_embedding": clip_embedding.astype(np.float32).tolist(),
            "protected_image_png": protected_png,
            "token": token,
            "signature_b64": base64.urlsafe_b64encode(signature).decode("utf-8"),
        }

        self._container.provenance_store_service.upsert_record(
            asset_id=asset_id,
            payload=payload,
            signature_b64=base64.urlsafe_b64encode(signature).decode("utf-8"),
            pdq_hash_hex=pdq_hash_hex,
            semantic_hash_hex=semantic_hash_hex,
            commitment=commitment,
            mini_mac=mini_mac,
            clip_embedding=clip_embedding.astype(np.float32).tolist(),
            protected_image_png=protected_png,
        )

        return ProcessResponse(
            asset_id=asset_id,
            input_mode=mode,
            protected_image_ref=protected_ref,
            created_at=created_at,
            message="Image processed and protected successfully",
        )
