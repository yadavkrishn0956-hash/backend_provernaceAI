from __future__ import annotations

import logging
import os
import secrets
import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from google import genai
from imwatermark import WatermarkDecoder, WatermarkEncoder
from reedsolo import RSCodec

from app.core.config import settings
from app.core.container import AppContainer
from app.services.crypto_commitment import CommitmentService
from app.services.crypto_mac import MiniMACService
from app.services.crypto_rsa import RSASignatureService
from app.services.fingerprint_clip import CLIPFingerprintService
from app.services.fingerprint_pdq import PDQFingerprintService
from app.services.gemini_explainer import GeminiExplainerService
from app.services.image_generation import DeterministicImageGenerationService
from app.services.provenance_store import ProvenanceStoreService
from app.services.watermark_codec import WatermarkCodecService

logger = logging.getLogger(__name__)


def _load_rsa_keys() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    passphrase = (
        settings.RSA_PRIVATE_KEY_PASSPHRASE.encode("utf-8")
        if settings.RSA_PRIVATE_KEY_PASSPHRASE
        else None
    )

    if settings.RSA_PRIVATE_KEY_B64 and settings.RSA_PUBLIC_KEY_B64:
        private_key = serialization.load_pem_private_key(
            base64.b64decode(settings.RSA_PRIVATE_KEY_B64),
            password=passphrase,
        )
        public_key = serialization.load_pem_public_key(base64.b64decode(settings.RSA_PUBLIC_KEY_B64))
        if not isinstance(private_key, rsa.RSAPrivateKey):
            raise RuntimeError("Configured private key is not an RSA key")
        if not isinstance(public_key, rsa.RSAPublicKey):
            raise RuntimeError("Configured public key is not an RSA key")
        return private_key, public_key

    private_key_path = Path(settings.RSA_PRIVATE_KEY_PATH)
    public_key_path = Path(settings.RSA_PUBLIC_KEY_PATH)

    if not private_key_path.exists():
        private_key_path.parent.mkdir(parents=True, exist_ok=True)
        generated_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_key_path.write_bytes(
            generated_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        public_key_path.parent.mkdir(parents=True, exist_ok=True)
        public_key_path.write_bytes(
            generated_private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    if not public_key_path.exists():
        raise RuntimeError(f"RSA public key file not found: {public_key_path}")

    private_key = serialization.load_pem_private_key(
        private_key_path.read_bytes(),
        password=passphrase,
    )
    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())

    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise RuntimeError("Configured private key is not an RSA key")
    if not isinstance(public_key, rsa.RSAPublicKey):
        raise RuntimeError("Configured public key is not an RSA key")

    return private_key, public_key


def _load_hmac_secret() -> bytes:
    if settings.HMAC_SECRET_B64:
        secret = base64.b64decode(settings.HMAC_SECRET_B64)
        if len(secret) < 32:
            raise RuntimeError("HMAC_SECRET_B64 must decode to at least 32 bytes")
        return secret

    secret_path = Path(settings.HMAC_SECRET_PATH)
    if not secret_path.exists():
        secret_path.parent.mkdir(parents=True, exist_ok=True)
        secret_path.write_bytes(secrets.token_bytes(32))
    secret = secret_path.read_bytes()
    if len(secret) < 32:
        raise RuntimeError(f"HMAC secret must be at least 32 bytes: {secret_path}")
    return secret


def _init_gemini_client() -> genai.Client | None:
    if not settings.GEMINI_ENABLED:
        logger.warning("GEMINI_ENABLED is false — CLIPFingerprintService will use fallback hash embeddings")
        return None
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_ENABLED is true but GEMINI_API_KEY is missing")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _init_clip_fingerprint_service(gemini_client: genai.Client | None) -> CLIPFingerprintService:
    return CLIPFingerprintService(
        client=gemini_client,
        embed_model=settings.GEMINI_EMBED_MODEL,
        enabled=settings.GEMINI_ENABLED,
    )


def _init_watermark_stack() -> tuple[RSCodec, WatermarkEncoder, WatermarkDecoder]:
    rs_codec = RSCodec(settings.RS_NSYM)
    watermark_encoder = WatermarkEncoder()
    watermark_decoder = WatermarkDecoder("bytes", settings.WATERMARK_MAX_PAYLOAD_BYTES * 8)
    return rs_codec, watermark_encoder, watermark_decoder

def initialize_container() -> AppContainer:
    rsa_private_key, rsa_public_key = _load_rsa_keys()
    hmac_secret = _load_hmac_secret()
    gemini_client = _init_gemini_client()
    rs_codec, watermark_encoder, watermark_decoder = _init_watermark_stack()

    rsa_service = RSASignatureService(rsa_private_key, rsa_public_key)
    commitment_service = CommitmentService()
    mini_mac_service = MiniMACService(hmac_secret)
    watermark_service = WatermarkCodecService(
        rs_codec,
        watermark_encoder,
        watermark_decoder,
        method=settings.WATERMARK_METHOD,
        max_payload_bytes=settings.WATERMARK_MAX_PAYLOAD_BYTES,
    )
    clip_fingerprint_service = _init_clip_fingerprint_service(gemini_client)
    pdq_fingerprint_service = PDQFingerprintService()
    gemini_explainer_service = GeminiExplainerService(
        gemini_client,
        settings.GEMINI_MODEL,
        enabled=settings.GEMINI_ENABLED,
    )
    image_generation_service = DeterministicImageGenerationService(
        width=settings.GENERATION_WIDTH,
        height=settings.GENERATION_HEIGHT,
    )
    provenance_store_service = ProvenanceStoreService(settings.PROVENANCE_DB_PATH)

    return AppContainer(
        rsa_private_key=rsa_private_key,
        rsa_public_key=rsa_public_key,
        rs_codec=rs_codec,
        watermark_encoder=watermark_encoder,
        watermark_decoder=watermark_decoder,
        rsa_service=rsa_service,
        commitment_service=commitment_service,
        mini_mac_service=mini_mac_service,
        watermark_service=watermark_service,
        clip_fingerprint_service=clip_fingerprint_service,
        pdq_fingerprint_service=pdq_fingerprint_service,
        gemini_explainer_service=gemini_explainer_service,
        image_generation_service=image_generation_service,
        provenance_store_service=provenance_store_service,
        gemini_client=gemini_client,
        gemini_model=settings.GEMINI_MODEL,
        cache={},
    )
