from __future__ import annotations

import io
import hashlib
import textwrap

from PIL import Image, ImageDraw
from google import genai
from google.genai import types

from app.core.config import settings


class DeterministicImageGenerationService:
    """Generates images from text prompts using Gemini Flash image generation."""

    def __init__(self, width: int = 768, height: int = 768):
        self._width = width
        self._height = height

    def generate(self, prompt: str) -> Image.Image:
        normalized_prompt = (prompt or "").strip() or "abstract digital art"

        if not settings.GEMINI_ENABLED or not settings.GEMINI_API_KEY:
            return self._generate_fallback(normalized_prompt)

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            response = client.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=normalized_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            # Extract the image part from the response
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                    image = image.resize((self._width, self._height), Image.LANCZOS)
                    return image

            raise RuntimeError("Gemini returned no image in response parts.")

        except Exception as e:
            return self._generate_fallback(
                f"{normalized_prompt}\n\nGemini image generation unavailable: {e}"
            )

    def _generate_fallback(self, prompt: str) -> Image.Image:
        digest = hashlib.sha256(prompt.encode("utf-8")).digest()
        colors = [
            tuple(48 + digest[i + j] % 160 for j in range(3))
            for i in range(0, 12, 3)
        ]
        image = Image.new("RGB", (self._width, self._height), colors[0])
        draw = ImageDraw.Draw(image)

        for y in range(self._height):
            ratio = y / max(1, self._height - 1)
            start = colors[int(ratio * (len(colors) - 1))]
            end = colors[min(len(colors) - 1, int(ratio * (len(colors) - 1)) + 1)]
            blended = tuple(int(start[i] * (1 - ratio) + end[i] * ratio) for i in range(3))
            draw.line([(0, y), (self._width, y)], fill=blended)

        for i in range(18):
            x0 = digest[(i * 3) % len(digest)] / 255 * self._width
            y0 = digest[(i * 3 + 1) % len(digest)] / 255 * self._height
            radius = 40 + digest[(i * 3 + 2) % len(digest)] % 130
            color = colors[i % len(colors)]
            outline = tuple(min(255, c + 70) for c in color)
            draw.ellipse(
                (x0 - radius, y0 - radius, x0 + radius, y0 + radius),
                outline=outline,
                width=3,
            )

        title = "Generated from prompt"
        wrapped = textwrap.wrap(prompt.split("\n", 1)[0], width=34)[:4]
        text = "\n".join([title, "", *wrapped])
        box_margin = 48
        draw.rounded_rectangle(
            (box_margin, self._height - 220, self._width - box_margin, self._height - 48),
            radius=24,
            fill=(255, 255, 255),
            outline=(230, 234, 242),
            width=2,
        )
        draw.text((box_margin + 28, self._height - 190), text, fill=(20, 28, 45))
        return image
