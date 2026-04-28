from __future__ import annotations

import io

import numpy as np
from google import genai
from PIL import Image


class CLIPFingerprintService:
    """
    Drop-in replacement for CLIP using Gemini embeddings.
    Interface is identical — embedding() returns np.ndarray,
    similarity() returns float. Rest of system unchanged.
    """

    EMBEDDING_DIM = 3072  # gemini-embedding-2 default output dimension  # Gemini embedding dim vs CLIP's 512

    def __init__(self, client: genai.Client | None, embed_model: str, *, enabled: bool):
        self._client = client
        self._embed_model = embed_model
        self._enabled = enabled and client is not None

    def embedding(self, image: Image.Image) -> np.ndarray:
        if not self._enabled or self._client is None:
            return self._fallback_embedding(image)

        try:
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            image_bytes = buf.getvalue()

            result = self._client.models.embed_content(
                model=self._embed_model,
                contents=[
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": image_bytes,
                                }
                            }
                        ]
                    }
                ],
            )
            vec = np.array(result.embeddings[0].values, dtype=np.float32)
            norm = float(np.linalg.norm(vec))
            if norm == 0.0:
                vec[0] = 1.0
                norm = 1.0
            return (vec / norm).astype(np.float32)

        except Exception:
            return self._fallback_embedding(image)

    def similarity(self, image_a: Image.Image, image_b: Image.Image) -> float:
        emb_a = self.embedding(image_a)
        emb_b = self.embedding(image_b)
        if emb_a.shape != emb_b.shape:
            return 0.0  # dimension mismatch — old CLIP record vs new Gemini vector
        score = float(np.dot(emb_a, emb_b))
        return max(-1.0, min(1.0, score))

    def _fallback_embedding(self, image: Image.Image) -> np.ndarray:
        """Used when Gemini is unavailable. Returns deterministic hash-based vector."""
        thumb = image.convert("L").resize((32, 16))
        vec = np.asarray(thumb, dtype=np.float32).reshape(-1)
        vec = vec - float(vec.mean())
        norm = float(np.linalg.norm(vec))
        if norm == 0.0:
            vec[0] = 1.0
            norm = 1.0
        return (vec / norm).astype(np.float32)