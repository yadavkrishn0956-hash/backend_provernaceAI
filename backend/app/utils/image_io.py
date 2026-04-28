from __future__ import annotations

from io import BytesIO

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError


class ImageDecodeError(ValueError):
    pass


async def read_upload_image(
    upload: UploadFile,
    *,
    max_bytes: int = 10 * 1024 * 1024,
) -> Image.Image:
    data = await upload.read()
    await upload.seek(0)

    if not data:
        raise ImageDecodeError("Uploaded image is empty")
    if len(data) > max_bytes:
        raise ImageDecodeError(f"Uploaded image exceeds {max_bytes} bytes limit")

    try:
        image = Image.open(BytesIO(data))
        image.load()
    except UnidentifiedImageError as exc:
        raise ImageDecodeError("Unsupported or corrupted image file") from exc

    return image.convert("RGB")


def canonicalize_image(image: Image.Image, *, max_side: int = 1024) -> Image.Image:
    width, height = image.size

    # Upscale if too small for watermarking (imwatermark requires 256x256 minimum)
    if width < 256 or height < 256:
        scale = 256 / min(width, height)
        width = max(256, int(width * scale))
        height = max(256, int(height * scale))
        image = image.resize((width, height), Image.Resampling.LANCZOS)

    # Downscale if too large
    longest = max(width, height)
    if longest > max_side:
        scale = max_side / float(longest)
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    return image

def image_to_png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
