from __future__ import annotations

from typing import Any


class GeminiExplainerService:
    """Generates human-readable verification explanations with Gemini when available."""

    def __init__(self, client: Any, model: str, *, enabled: bool):
        self._client = client
        self._model = model
        self._enabled = enabled and client is not None

    def explain_verification(self, report: dict[str, Any]) -> str:
        fallback = self._fallback_explanation(report)
        if not self._enabled:
            return fallback

        prompt = (
            "You are a forensic verification assistant. "
            "Explain the result in 2-4 concise sentences for a product UI. "
            "Do not speculate beyond provided signals.\n\n"
            f"Verification report:\n{report}"
        )

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
            text = getattr(response, "text", None)
            if text and text.strip():
                return text.strip()
            return fallback
        except Exception:
            return fallback

    @staticmethod
    def _fallback_explanation(report: dict[str, Any]) -> str:
        verdict = report.get("verdict", "unverifiable")
        signature_valid = report.get("signature_valid", False)
        watermark_detected = report.get("watermark_detected", False)
        pdq_distance = report.get("pdq_distance")
        clip_similarity = report.get("clip_similarity")

        return (
            "Gemini explanation unavailable; using local summary. "
            f"Verdict={verdict}, signature_valid={signature_valid}, "
            f"watermark_detected={watermark_detected}, pdq_distance={pdq_distance}, "
            f"clip_similarity={clip_similarity}."
        )
