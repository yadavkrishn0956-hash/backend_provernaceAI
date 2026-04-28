from __future__ import annotations

import hmac
from hashlib import sha256


class MiniMACService:
    """16-bit HMAC token proof for offline/local verification."""

    def __init__(self, secret: bytes):
        if len(secret) < 32:
            raise ValueError("HMAC secret must be at least 32 bytes")
        self._secret = secret

    def build(self, *, asset_id: str, issued_at: int) -> str:
        mac_input = f"{asset_id}{issued_at}".encode("utf-8")
        return hmac.new(self._secret, mac_input, sha256).hexdigest()[:4]

    def verify(self, *, asset_id: str, issued_at: int, mini_mac: str) -> bool:
        expected = self.build(asset_id=asset_id, issued_at=issued_at)
        return hmac.compare_digest(expected, mini_mac)
