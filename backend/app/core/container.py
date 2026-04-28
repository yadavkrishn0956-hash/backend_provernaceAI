from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from reedsolo import RSCodec
from imwatermark import WatermarkDecoder, WatermarkEncoder

from app.services.crypto_rsa import RSASignatureService
from app.services.crypto_commitment import CommitmentService
from app.services.crypto_mac import MiniMACService
from app.services.fingerprint_clip import CLIPFingerprintService
from app.services.fingerprint_pdq import PDQFingerprintService
from app.services.gemini_explainer import GeminiExplainerService
from app.services.image_generation import DeterministicImageGenerationService
from app.services.provenance_store import ProvenanceStoreService
from app.services.watermark_codec import WatermarkCodecService


@dataclass
class AppContainer:
    """In-memory singleton container initialized at startup."""

    rsa_private_key: RSAPrivateKey
    rsa_public_key: RSAPublicKey
    rs_codec: RSCodec
    watermark_encoder: WatermarkEncoder
    watermark_decoder: WatermarkDecoder
    rsa_service: RSASignatureService
    commitment_service: CommitmentService
    mini_mac_service: MiniMACService
    watermark_service: WatermarkCodecService
    clip_fingerprint_service: CLIPFingerprintService
    pdq_fingerprint_service: PDQFingerprintService
    gemini_explainer_service: GeminiExplainerService
    image_generation_service: DeterministicImageGenerationService
    provenance_store_service: ProvenanceStoreService
    gemini_client: Any
    gemini_model: str
    cache: dict[str, Any]