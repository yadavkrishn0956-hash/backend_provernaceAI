from __future__ import annotations

import hashlib


class CommitmentService:
    """Builds the 64-bit hash commitment that binds token to DB signature."""

    def build(self, *, asset_id: str, signature: bytes) -> str:
        commitment_input = f"{asset_id}{signature.hex()}".encode("utf-8")
        return hashlib.sha256(commitment_input).hexdigest()[:16]

    def verify(self, *, asset_id: str, signature: bytes, commitment: str) -> bool:
        return self.build(asset_id=asset_id, signature=signature) == commitment
