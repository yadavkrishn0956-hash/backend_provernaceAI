from __future__ import annotations

import numpy as np
import pdqhash
from PIL import Image


class PDQFingerprintService:
    """Geometric/perceptual fingerprinting using PDQ hash."""

    def hash_image(self, image: Image.Image) -> tuple[np.ndarray, int]:
        rgb = np.array(image.convert("RGB"), dtype=np.uint8)
        hash_vector, quality = pdqhash.compute(rgb)
        return np.asarray(hash_vector), int(quality)

    def distance(self, hash_a: np.ndarray, hash_b: np.ndarray) -> int:
        a = np.asarray(hash_a)
        b = np.asarray(hash_b)
        if a.shape != b.shape:
            raise ValueError("PDQ hashes must have the same shape")
        return int(np.count_nonzero(a != b))

    def distance_between_images(self, image_a: Image.Image, image_b: Image.Image) -> tuple[int, int, int]:
        hash_a, quality_a = self.hash_image(image_a)
        hash_b, quality_b = self.hash_image(image_b)
        return self.distance(hash_a, hash_b), quality_a, quality_b
