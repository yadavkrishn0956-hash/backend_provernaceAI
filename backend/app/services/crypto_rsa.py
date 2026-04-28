from __future__ import annotations

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey


class RSASignatureService:
    """RSA-PSS SHA-256 signer/verifier for provenance payloads."""

    algorithm = "RSA-PSS-SHA256"

    def __init__(self, private_key: RSAPrivateKey, public_key: RSAPublicKey):
        self._private_key = private_key
        self._public_key = public_key

    @property
    def public_key(self) -> RSAPublicKey:
        return self._public_key

    def sign(self, payload: bytes) -> bytes:
        return self._private_key.sign(
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

    def verify(self, payload: bytes, signature: bytes) -> bool:
        try:
            self._public_key.verify(
                signature,
                payload,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except InvalidSignature:
            return False
