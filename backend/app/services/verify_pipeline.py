from __future__ import annotations

import json
import base64
from typing import Any

import numpy as np
from PIL import Image

from app.core.config import settings
from app.core.container import AppContainer
from app.schemas.verify import LocalVerifyResponse, VerificationVerdict, VerifyResponse, VerifySignalSummary
from app.utils.image_io import canonicalize_image

# invisible-watermark always returns bytes even for unwatermarked images (DCT noise).
# A valid packed token is 19 bytes before Reed-Solomon expansion.
# Anything shorter is extraction noise — treat as no watermark.
_MIN_TOKEN_BYTES = 19


class VerifyPipelineService:
    """Extraction -> signature verification -> fingerprint comparison pipeline."""

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

    @staticmethod
    def _hamming_hex(hex_a: str, hex_b: str, bits: int) -> int:
        return int((int(hex_a, 16) ^ int(hex_b, 16)).bit_count()) if bits > 0 else 0

    @staticmethod
    def _classify_pdq(pdq_distance: int | None) -> str | None:
        if pdq_distance is None:
            return None
        if pdq_distance < 15:
            return "IDENTICAL"
        if pdq_distance <= 30:
            return "MODIFIED"
        return "HEAVILY_MODIFIED"

    @staticmethod
    def _clean_asset_id_hint(asset_id_hint: str | None) -> str | None:
        if not asset_id_hint:
            return None
        cleaned = asset_id_hint.strip().lower()
        return cleaned or None

    def _classify_clip(self, clip_similarity: float | None) -> str | None:
        if clip_similarity is None:
            return None
        if clip_similarity > settings.VERIFY_CLIP_SAME_THRESHOLD:
            return "SAME_OR_TRIVIAL"
        if clip_similarity >= settings.VERIFY_CLIP_DERIVATIVE_THRESHOLD:
            return "PROBABLE_DERIVATIVE"
        return "DIFFERENT_CONTENT"

    def _unknown_response(
        self,
        *,
        reason: str,
        current_pdq_hex: str,
        current_semantic_hex: str,
    ) -> VerifyResponse:
        report = {
            "verdict": VerificationVerdict.UNKNOWN_ORIGIN.value,
            "signature_valid": False,
            "watermark_detected": False,
            "pdq_distance": None,
            "clip_similarity": None,
            "reason": reason,
        }
        explanation = self._container.gemini_explainer_service.explain_verification(report)
        return VerifyResponse(
            asset_id=None,
            verdict=VerificationVerdict.UNKNOWN_ORIGIN,
            signals=VerifySignalSummary(
                signature_valid=False,
                watermark_detected=False,
                current_pdq_hash_hex=current_pdq_hex,
                current_semantic_hash_hex=current_semantic_hex,
                pdq_distance=None,
                clip_similarity=None,
            ),
            gemini_explanation=explanation,
            reasons=[reason],
        )

    def _compare_with_record_hint(
        self,
        *,
        asset_id: str,
        record: dict[str, Any],
        current_pdq_hex: str,
        current_semantic_hex: str,
        current_clip: np.ndarray,
        current_pdq_quality: int,
        watermark_detected: bool,
        reasons: list[str],
    ) -> VerifyResponse:
        signature = base64.urlsafe_b64decode(record["signature_b64"].encode("utf-8"))
        payload = record["payload"]
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        signature_valid = self._container.rsa_service.verify(payload_bytes, signature)

        pdq_distance = self._hamming_hex(record["pdq_hash_hex"], current_pdq_hex, 256)
        clip_similarity: float | None = None
        if record.get("clip_embedding"):
            baseline_clip = np.array(record["clip_embedding"], dtype=np.float32)
            clip_similarity = float(np.dot(current_clip, baseline_clip))
        elif record.get("semantic_hash_hex"):
            semantic_hd = self._hamming_hex(record["semantic_hash_hex"], current_semantic_hex, 64)
            clip_similarity = max(0.0, 1.0 - (semantic_hd / 64.0))

        pdq_result = self._classify_pdq(pdq_distance)
        clip_result = self._classify_clip(clip_similarity)
        reasons.extend(
            [
                f"Used asset ID hint={asset_id} because a trusted watermark token was unavailable",
                f"Compared to persisted record: pdq_distance={pdq_distance}, clip_similarity={clip_similarity:.4f}"
                if clip_similarity is not None
                else f"Compared to persisted record: pdq_distance={pdq_distance}, clip_similarity=unavailable",
                f"PDQ quality persisted/current=unknown/{current_pdq_quality}",
            ]
        )

        if not signature_valid:
            verdict = VerificationVerdict.TAMPERED_RECORD
            reasons.append("RSA signature validation failed for hinted record")
        elif pdq_result == "IDENTICAL" and clip_result == "SAME_OR_TRIVIAL":
            verdict = VerificationVerdict.VERIFIED_AUTHENTIC
            reasons.append("Hinted record signature is valid and fingerprints match")
        elif clip_result == "PROBABLE_DERIVATIVE" and pdq_result == "HEAVILY_MODIFIED":
            verdict = VerificationVerdict.UNVERIFIED_SUSPICIOUS_LAUNDERING
            reasons.append("Hinted record has semantic similarity but heavy pixel drift")
        else:
            verdict = VerificationVerdict.VERIFIED_MODIFIED
            reasons.append("Hinted record signature is valid but fingerprint drift indicates modification")

        report: dict[str, Any] = {
            "verdict": verdict.value,
            "signature_valid": signature_valid,
            "watermark_detected": watermark_detected,
            "db_record_found": True,
            "pdq_distance": pdq_distance,
            "clip_similarity": clip_similarity,
            "pdq_result": pdq_result,
            "clip_result": clip_result,
            "asset_id": asset_id,
        }
        explanation = self._container.gemini_explainer_service.explain_verification(report)
        return VerifyResponse(
            asset_id=asset_id,
            verdict=verdict,
            signals=VerifySignalSummary(
                signature_valid=signature_valid,
                watermark_detected=watermark_detected,
                db_record_found=True,
                current_pdq_hash_hex=current_pdq_hex,
                current_semantic_hash_hex=current_semantic_hex,
                pdq_distance=pdq_distance,
                clip_similarity=clip_similarity,
                pdq_result=pdq_result,
                clip_result=clip_result,
            ),
            gemini_explanation=explanation,
            reasons=reasons,
        )

    def run(self, *, image: Image.Image, asset_id_hint: str | None = None) -> VerifyResponse:
        normalized = canonicalize_image(image)
        current_pdq_hash, current_pdq_quality = self._container.pdq_fingerprint_service.hash_image(normalized)
        current_pdq_hex = self._pdq_hash_to_hex(current_pdq_hash)
        current_clip = self._container.clip_fingerprint_service.embedding(normalized)
        current_semantic_hex = self._semantic_hash_hex(current_clip)
        cleaned_asset_id_hint = self._clean_asset_id_hint(asset_id_hint)

        raw_extracted = self._container.watermark_service.extract(normalized)
        # Guard against DCT noise returned for unwatermarked images
        extracted = raw_extracted if (raw_extracted and len(raw_extracted) >= _MIN_TOKEN_BYTES) else None

        if not extracted:
            if cleaned_asset_id_hint:
                hinted_record = self._container.provenance_store_service.get_record(cleaned_asset_id_hint)
                if hinted_record:
                    return self._compare_with_record_hint(
                        asset_id=cleaned_asset_id_hint,
                        record=hinted_record,
                        current_pdq_hex=current_pdq_hex,
                        current_semantic_hex=current_semantic_hex,
                        current_clip=current_clip,
                        current_pdq_quality=current_pdq_quality,
                        watermark_detected=False,
                        reasons=["No watermark payload could be extracted"],
                    )
            return self._unknown_response(
                reason="No trusted system watermark token could be extracted",
                current_pdq_hex=current_pdq_hex,
                current_semantic_hex=current_semantic_hex,
            )

        try:
            token = self._container.watermark_service.unpack_token(extracted)
        except Exception:
            if cleaned_asset_id_hint:
                hinted_record = self._container.provenance_store_service.get_record(cleaned_asset_id_hint)
                if hinted_record:
                    return self._compare_with_record_hint(
                        asset_id=cleaned_asset_id_hint,
                        record=hinted_record,
                        current_pdq_hex=current_pdq_hex,
                        current_semantic_hex=current_semantic_hex,
                        current_clip=current_clip,
                        current_pdq_quality=current_pdq_quality,
                        watermark_detected=False,
                        reasons=["Watermark-like noise was detected, but no valid token could be decoded"],
                    )
            return self._unknown_response(
                reason="Watermark-like noise was detected, but no valid system token could be decoded",
                current_pdq_hex=current_pdq_hex,
                current_semantic_hex=current_semantic_hex,
            )

        asset_id = token.get("asset_id")
        issued_at = int(token.get("issued_at", 0) or 0)
        extracted_commitment = str(token.get("commitment", ""))
        extracted_mini_mac = str(token.get("mini_mac", ""))
        local_mac_valid = bool(
            asset_id
            and issued_at
            and self._container.mini_mac_service.verify(
                asset_id=str(asset_id),
                issued_at=issued_at,
                mini_mac=extracted_mini_mac,
            )
        )
        record = self._container.provenance_store_service.get_record(str(asset_id)) if asset_id else None
        if not record:
            if not local_mac_valid:
                return self._unknown_response(
                    reason="Decoded token failed local MAC validation, so it is not trusted as a system watermark",
                    current_pdq_hex=current_pdq_hex,
                    current_semantic_hex=current_semantic_hex,
                )
            verdict = VerificationVerdict.FORGED_OR_UNKNOWN
            report = {
                "verdict": verdict.value,
                "signature_valid": False,
                "watermark_detected": True,
                "local_mac_valid": local_mac_valid,
                "reason": "No database record found for token asset_id",
            }
            explanation = self._container.gemini_explainer_service.explain_verification(report)
            return VerifyResponse(
                asset_id=str(asset_id) if asset_id else None,
                verdict=verdict,
                signals=VerifySignalSummary(
                    signature_valid=False,
                    watermark_detected=True,
                    local_mac_valid=local_mac_valid,
                    db_record_found=False,
                    commitment_valid=None,
                    current_pdq_hash_hex=current_pdq_hex,
                    current_semantic_hash_hex=current_semantic_hex,
                ),
                gemini_explanation=explanation,
                reasons=["Watermark token was present, but no matching provenance record was found"],
            )

        signature = base64.urlsafe_b64decode(record["signature_b64"].encode("utf-8"))
        payload = record["payload"]
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        commitment_valid = self._container.commitment_service.verify(
            asset_id=str(asset_id),
            signature=signature,
            commitment=extracted_commitment,
        )
        signature_valid = self._container.rsa_service.verify(payload_bytes, signature)

        pdq_distance: int | None = None
        clip_similarity: float | None = None
        pdq_result: str | None = None
        clip_result: str | None = None
        reasons: list[str] = []
        reasons.append(f"Local mini-MAC valid={local_mac_valid}")
        reasons.append(f"Commitment valid={commitment_valid}")

        payload_pdq_hex = payload.get("pdq_hash_hex")
        payload_semantic_hex = payload.get("semantic_hash_hex")
        if payload_pdq_hex:
            pdq_distance = self._hamming_hex(payload_pdq_hex, current_pdq_hex, 256)
            reasons.append(f"Payload PDQ distance={pdq_distance}")
        if payload_semantic_hex:
            semantic_hd = self._hamming_hex(payload_semantic_hex, current_semantic_hex, 64)
            clip_similarity = max(0.0, 1.0 - (semantic_hd / 64.0))
            reasons.append(f"Payload semantic hash distance={semantic_hd}")

        assets = self._container.cache.get("assets", {})
        cached = assets.get(asset_id) if asset_id else None

        if cached:
            baseline_pdq_hash = np.array(cached["pdq_hash"], dtype=np.uint8)
            pdq_distance = self._container.pdq_fingerprint_service.distance(baseline_pdq_hash, current_pdq_hash)
            baseline_clip = np.array(cached["clip_embedding"], dtype=np.float32)
            clip_similarity = float(np.dot(current_clip, baseline_clip))
            reasons.append(
                f"Compared to cached baseline: pdq_distance={pdq_distance}, clip_similarity={clip_similarity:.4f}"
            )
            reasons.append(
                f"PDQ quality baseline/current={cached['pdq_quality']}/{current_pdq_quality}"
            )
        elif record and record.get("clip_embedding"):
            baseline_clip = np.array(record["clip_embedding"], dtype=np.float32)
            clip_similarity = float(np.dot(current_clip, baseline_clip))
            pdq_distance = self._hamming_hex(record["pdq_hash_hex"], current_pdq_hex, 256)
            reasons.append(
                f"Compared to persisted record: pdq_distance={pdq_distance}, clip_similarity={clip_similarity:.4f}"
            )
            reasons.append(
                f"PDQ quality persisted/current=unknown/{current_pdq_quality}"
            )
        else:
            reasons.append("No persisted baseline record available for richer similarity comparison")

        pdq_result = self._classify_pdq(pdq_distance)
        clip_result = self._classify_clip(clip_similarity)

        if not local_mac_valid or not commitment_valid:
            verdict = VerificationVerdict.FORGED_TOKEN
            reasons.append("Token failed local MAC or commitment binding")
        elif not signature_valid:
            verdict = VerificationVerdict.TAMPERED_RECORD
            reasons.append("RSA signature validation failed")
        elif pdq_distance is None or clip_similarity is None:
            verdict = VerificationVerdict.INCONCLUSIVE
            reasons.append("Signature valid but baseline comparison unavailable")
        elif pdq_result == "IDENTICAL" and clip_result == "SAME_OR_TRIVIAL":
            verdict = VerificationVerdict.VERIFIED_AUTHENTIC
            reasons.append("Signature valid and fingerprint similarity within threshold")
        elif clip_result == "PROBABLE_DERIVATIVE" and pdq_result == "HEAVILY_MODIFIED":
            verdict = VerificationVerdict.UNVERIFIED_SUSPICIOUS_LAUNDERING
            reasons.append("Semantic similarity remains high while pixel fingerprint changed heavily")
        else:
            verdict = VerificationVerdict.VERIFIED_MODIFIED
            reasons.append("Signature valid but fingerprint drift indicates modification")

        report: dict[str, Any] = {
            "verdict": verdict.value,
            "signature_valid": signature_valid,
            "watermark_detected": True,
            "local_mac_valid": local_mac_valid,
            "commitment_valid": commitment_valid,
            "pdq_distance": pdq_distance,
            "clip_similarity": clip_similarity,
            "pdq_result": pdq_result,
            "clip_result": clip_result,
            "asset_id": asset_id,
        }
        explanation = self._container.gemini_explainer_service.explain_verification(report)

        return VerifyResponse(
            asset_id=asset_id,
            verdict=verdict,
            signals=VerifySignalSummary(
                signature_valid=signature_valid,
                watermark_detected=True,
                local_mac_valid=local_mac_valid,
                db_record_found=True,
                commitment_valid=commitment_valid,
                current_pdq_hash_hex=current_pdq_hex,
                current_semantic_hash_hex=current_semantic_hex,
                pdq_distance=pdq_distance,
                clip_similarity=clip_similarity,
                pdq_result=pdq_result,
                clip_result=clip_result,
            ),
            gemini_explanation=explanation,
            reasons=reasons,
        )

    def run_local(self, *, image: Image.Image) -> LocalVerifyResponse:
        normalized = canonicalize_image(image)

        raw_extracted = self._container.watermark_service.extract(normalized)
        # Same noise guard as run() — short byte sequences are DCT noise
        extracted = raw_extracted if (raw_extracted and len(raw_extracted) >= _MIN_TOKEN_BYTES) else None

        if not extracted:
            return LocalVerifyResponse(
                local_verdict="NO_SYSTEM_TOKEN",
                watermark_detected=False,
                note="No embedded token could be extracted",
            )

        try:
            token = self._container.watermark_service.unpack_token(extracted)
        except Exception:
            return LocalVerifyResponse(
                local_verdict="NO_SYSTEM_TOKEN",
                watermark_detected=False,
                note="Watermark-like noise was found, but no valid system token could be decoded",
            )

        asset_id = str(token.get("asset_id", ""))
        issued_at = int(token.get("issued_at", 0) or 0)
        mini_mac = str(token.get("mini_mac", ""))
        mac_valid = bool(
            asset_id
            and issued_at
            and self._container.mini_mac_service.verify(
                asset_id=asset_id,
                issued_at=issued_at,
                mini_mac=mini_mac,
            )
        )
        return LocalVerifyResponse(
            local_verdict="AUTHENTIC_SYSTEM_TOKEN" if mac_valid else "NO_SYSTEM_TOKEN",
            asset_id=asset_id or None,
            watermark_detected=mac_valid,
            mini_mac_valid=mac_valid,
            version=token.get("v"),
            note="Full provenance requires online verification" if mac_valid else "Decoded token failed local MAC validation",
        )

# from __future__ import annotations

# import json
# import base64
# from typing import Any

# import numpy as np
# from PIL import Image

# from app.core.config import settings
# from app.core.container import AppContainer
# from app.schemas.verify import LocalVerifyResponse, VerificationVerdict, VerifyResponse, VerifySignalSummary
# from app.utils.image_io import canonicalize_image


# class VerifyPipelineService:
#     """Extraction -> signature verification -> fingerprint comparison pipeline."""

#     def __init__(self, container: AppContainer):
#         self._container = container

#     @staticmethod
#     def _pdq_hash_to_hex(pdq_hash: np.ndarray) -> str:
#         bits = "".join(str(int(v)) for v in np.asarray(pdq_hash).astype(np.uint8).tolist())
#         return format(int(bits, 2), "064x")

#     @staticmethod
#     def _semantic_hash_hex(embedding: np.ndarray, nbits: int = 64) -> str:
#         vec = np.asarray(embedding, dtype=np.float32)[:nbits]
#         bits = "".join("1" if float(v) >= 0.0 else "0" for v in vec)
#         return format(int(bits, 2), "016x")

#     @staticmethod
#     def _hamming_hex(hex_a: str, hex_b: str, bits: int) -> int:
#         return int((int(hex_a, 16) ^ int(hex_b, 16)).bit_count()) if bits > 0 else 0

#     def run(self, *, image: Image.Image) -> VerifyResponse:
#         normalized = canonicalize_image(image)
#         current_pdq_hash, current_pdq_quality = self._container.pdq_fingerprint_service.hash_image(normalized)
#         current_pdq_hex = self._pdq_hash_to_hex(current_pdq_hash)
#         current_clip = self._container.clip_fingerprint_service.embedding(normalized)
#         current_semantic_hex = self._semantic_hash_hex(current_clip)
#         extracted = self._container.watermark_service.extract(normalized)

#         if not extracted:
#             report = {
#                 "verdict": VerificationVerdict.UNKNOWN_ORIGIN.value,
#                 "signature_valid": False,
#                 "watermark_detected": False,
#                 "pdq_distance": None,
#                 "clip_similarity": None,
#                 "reason": "No embedded payload detected",
#             }
#             explanation = self._container.gemini_explainer_service.explain_verification(report)
#             return VerifyResponse(
#                 asset_id=None,
#                 verdict=VerificationVerdict.UNKNOWN_ORIGIN,
#                 signals=VerifySignalSummary(
#                     signature_valid=False,
#                     watermark_detected=False,
#                     pdq_distance=None,
#                     clip_similarity=None,
#                 ),
#                 gemini_explanation=explanation,
#                 reasons=["No watermark payload could be extracted"],
#             )

#         try:
#             token = self._container.watermark_service.unpack_token(extracted)
#         except Exception:
#             report = {
#                 "verdict": VerificationVerdict.FORGED_TOKEN.value,
#                 "signature_valid": False,
#                 "watermark_detected": True,
#                 "pdq_distance": None,
#                 "clip_similarity": None,
#                 "reason": "Payload could not be decoded",
#             }
#             explanation = self._container.gemini_explainer_service.explain_verification(report)
#             return VerifyResponse(
#                 asset_id=None,
#                 verdict=VerificationVerdict.FORGED_TOKEN,
#                 signals=VerifySignalSummary(
#                     signature_valid=False,
#                     watermark_detected=True,
#                     pdq_distance=None,
#                     clip_similarity=None,
#                 ),
#                 gemini_explanation=explanation,
#                 reasons=["Watermark payload was detected but unpacking failed"],
#             )

#         asset_id = token.get("asset_id")
#         issued_at = int(token.get("issued_at", 0) or 0)
#         extracted_commitment = str(token.get("commitment", ""))
#         extracted_mini_mac = str(token.get("mini_mac", ""))
#         local_mac_valid = bool(
#             asset_id
#             and issued_at
#             and self._container.mini_mac_service.verify(
#                 asset_id=str(asset_id),
#                 issued_at=issued_at,
#                 mini_mac=extracted_mini_mac,
#             )
#         )
#         record = self._container.provenance_store_service.get_record(str(asset_id)) if asset_id else None
#         if not record:
#             verdict = VerificationVerdict.FORGED_OR_UNKNOWN if local_mac_valid else VerificationVerdict.FORGED_TOKEN
#             report = {
#                 "verdict": verdict.value,
#                 "signature_valid": False,
#                 "watermark_detected": True,
#                 "local_mac_valid": local_mac_valid,
#                 "reason": "No database record found for token asset_id",
#             }
#             explanation = self._container.gemini_explainer_service.explain_verification(report)
#             return VerifyResponse(
#                 asset_id=str(asset_id) if asset_id else None,
#                 verdict=verdict,
#                 signals=VerifySignalSummary(
#                     signature_valid=False,
#                     watermark_detected=True,
#                     local_mac_valid=local_mac_valid,
#                     db_record_found=False,
#                     commitment_valid=None,
#                 ),
#                 gemini_explanation=explanation,
#                 reasons=["Watermark token was present, but no matching provenance record was found"],
#             )

#         signature = base64.urlsafe_b64decode(record["signature_b64"].encode("utf-8"))
#         payload = record["payload"]
#         payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
#         commitment_valid = self._container.commitment_service.verify(
#             asset_id=str(asset_id),
#             signature=signature,
#             commitment=extracted_commitment,
#         )
#         signature_valid = self._container.rsa_service.verify(payload_bytes, signature)

#         pdq_distance: int | None = None
#         clip_similarity: float | None = None
#         pdq_result: str | None = None
#         clip_result: str | None = None
#         reasons: list[str] = []
#         reasons.append(f"Local mini-MAC valid={local_mac_valid}")
#         reasons.append(f"Commitment valid={commitment_valid}")

#         payload_pdq_hex = payload.get("pdq_hash_hex")
#         payload_semantic_hex = payload.get("semantic_hash_hex")
#         if payload_pdq_hex:
#             pdq_distance = self._hamming_hex(payload_pdq_hex, current_pdq_hex, 256)
#             reasons.append(f"Payload PDQ distance={pdq_distance}")
#         if payload_semantic_hex:
#             semantic_hd = self._hamming_hex(payload_semantic_hex, current_semantic_hex, 64)
#             clip_similarity = max(0.0, 1.0 - (semantic_hd / 64.0))
#             reasons.append(f"Payload semantic hash distance={semantic_hd}")

#         assets = self._container.cache.get("assets", {})
#         cached = assets.get(asset_id) if asset_id else None

#         if cached:
#             baseline_pdq_hash = np.array(cached["pdq_hash"], dtype=np.uint8)
#             pdq_distance = self._container.pdq_fingerprint_service.distance(baseline_pdq_hash, current_pdq_hash)
#             baseline_clip = np.array(cached["clip_embedding"], dtype=np.float32)
#             clip_similarity = float(np.dot(current_clip, baseline_clip))
#             reasons.append(
#                 f"Compared to cached baseline: pdq_distance={pdq_distance}, clip_similarity={clip_similarity:.4f}"
#             )
#             reasons.append(
#                 f"PDQ quality baseline/current={cached['pdq_quality']}/{current_pdq_quality}"
#             )
#         elif record and record.get("clip_embedding"):
#             baseline_clip = np.array(record["clip_embedding"], dtype=np.float32)
#             clip_similarity = float(np.dot(current_clip, baseline_clip))
#             pdq_distance = self._hamming_hex(record["pdq_hash_hex"], current_pdq_hex, 256)
#             reasons.append(
#                 f"Compared to persisted record: pdq_distance={pdq_distance}, clip_similarity={clip_similarity:.4f}"
#             )
#             reasons.append(
#                 f"PDQ quality persisted/current=unknown/{current_pdq_quality}"
#             )
#         else:
#             reasons.append("No persisted baseline record available for richer similarity comparison")

#         if pdq_distance is not None:
#             if pdq_distance < 15:
#                 pdq_result = "IDENTICAL"
#             elif pdq_distance <= 30:
#                 pdq_result = "MODIFIED"
#             else:
#                 pdq_result = "HEAVILY_MODIFIED"
#         if clip_similarity is not None:
#             if clip_similarity > settings.VERIFY_CLIP_SAME_THRESHOLD:
#                 clip_result = "SAME_OR_TRIVIAL"
#             elif clip_similarity >= settings.VERIFY_CLIP_DERIVATIVE_THRESHOLD:
#                 clip_result = "PROBABLE_DERIVATIVE"
#             else:
#                 clip_result = "DIFFERENT_CONTENT"

#         if not local_mac_valid or not commitment_valid:
#             verdict = VerificationVerdict.FORGED_TOKEN
#             reasons.append("Token failed local MAC or commitment binding")
#         elif not signature_valid:
#             verdict = VerificationVerdict.TAMPERED_RECORD
#             reasons.append("RSA signature validation failed")
#         elif pdq_distance is None or clip_similarity is None:
#             verdict = VerificationVerdict.INCONCLUSIVE
#             reasons.append("Signature valid but baseline comparison unavailable")
#         elif pdq_result == "IDENTICAL" and clip_result == "SAME_OR_TRIVIAL":
#             verdict = VerificationVerdict.VERIFIED_AUTHENTIC
#             reasons.append("Signature valid and fingerprint similarity within threshold")
#         elif clip_result == "PROBABLE_DERIVATIVE" and pdq_result == "HEAVILY_MODIFIED":
#             verdict = VerificationVerdict.UNVERIFIED_SUSPICIOUS_LAUNDERING
#             reasons.append("Semantic similarity remains high while pixel fingerprint changed heavily")
#         else:
#             verdict = VerificationVerdict.VERIFIED_MODIFIED
#             reasons.append("Signature valid but fingerprint drift indicates modification")

#         report: dict[str, Any] = {
#             "verdict": verdict.value,
#             "signature_valid": signature_valid,
#             "watermark_detected": True,
#             "local_mac_valid": local_mac_valid,
#             "commitment_valid": commitment_valid,
#             "pdq_distance": pdq_distance,
#             "clip_similarity": clip_similarity,
#             "pdq_result": pdq_result,
#             "clip_result": clip_result,
#             "asset_id": asset_id,
#         }
#         explanation = self._container.gemini_explainer_service.explain_verification(report)

#         return VerifyResponse(
#             asset_id=asset_id,
#             verdict=verdict,
#             signals=VerifySignalSummary(
#                 signature_valid=signature_valid,
#                 watermark_detected=True,
#                 local_mac_valid=local_mac_valid,
#                 db_record_found=True,
#                 commitment_valid=commitment_valid,
#                 pdq_distance=pdq_distance,
#                 clip_similarity=clip_similarity,
#                 pdq_result=pdq_result,
#                 clip_result=clip_result,
#             ),
#             gemini_explanation=explanation,
#             reasons=reasons,
#         )

#     def run_local(self, *, image: Image.Image) -> LocalVerifyResponse:
#         normalized = canonicalize_image(image)
#         extracted = self._container.watermark_service.extract(normalized)
#         if not extracted:
#             return LocalVerifyResponse(
#                 local_verdict="NO_SYSTEM_TOKEN",
#                 watermark_detected=False,
#                 note="No embedded token could be extracted",
#             )

#         try:
#             token = self._container.watermark_service.unpack_token(extracted)
#         except Exception:
#             return LocalVerifyResponse(
#                 local_verdict="INVALID_TOKEN",
#                 watermark_detected=True,
#                 note="A watermark-like payload was found, but it could not be decoded",
#             )

#         asset_id = str(token.get("asset_id", ""))
#         issued_at = int(token.get("issued_at", 0) or 0)
#         mini_mac = str(token.get("mini_mac", ""))
#         mac_valid = bool(
#             asset_id
#             and issued_at
#             and self._container.mini_mac_service.verify(
#                 asset_id=asset_id,
#                 issued_at=issued_at,
#                 mini_mac=mini_mac,
#             )
#         )
#         return LocalVerifyResponse(
#             local_verdict="AUTHENTIC_SYSTEM_TOKEN" if mac_valid else "INVALID_TOKEN",
#             asset_id=asset_id or None,
#             watermark_detected=True,
#             mini_mac_valid=mac_valid,
#             version=token.get("v"),
#             note="Full provenance requires online verification" if mac_valid else "Mini-MAC check failed",
#         )
