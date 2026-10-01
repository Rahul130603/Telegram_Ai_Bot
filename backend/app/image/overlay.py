from __future__ import annotations

import io
import textwrap

from PIL import Image, ImageDraw, ImageFont

from .base import GeneratedImage


def add_text_overlay(image: GeneratedImage, lines: list[str], *, enabled: bool = True, position: str = "auto", max_lines: int = 4, font_path: str = "") -> GeneratedImage:
    if not enabled or not lines:
        return image
    with Image.open(io.BytesIO(image.data)).convert("RGBA") as canvas:
        width, height = canvas.size
        font_size = max(20, min(width, height) // 14)
        try:
            font = ImageFont.truetype(font_path or "DejaVuSans-Bold.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        wrapped: list[str] = []
        for line in lines:
            wrapped.extend(textwrap.wrap(str(line), width=max(10, width // max(font_size // 2, 1))))
        wrapped = wrapped[:max_lines]
        draw = ImageDraw.Draw(canvas)
        spacing = max(6, font_size // 5)
        boxes = [draw.textbbox((0, 0), line, font=font, stroke_width=1) for line in wrapped]
        block_height = sum(box[3] - box[1] for box in boxes) + spacing * max(0, len(boxes) - 1)
        y = 32 if position == "top" else (height - block_height) // 2 if position == "center" else height - block_height - 40
        padding = 24
        draw.rounded_rectangle((20, y - padding, width - 20, y + block_height + padding), radius=18, fill=(0, 0, 0, 155))
        for line, box in zip(wrapped, boxes, strict=True):
            line_width = box[2] - box[0]
            draw.text(((width - line_width) / 2, y), line, font=font, fill="white", stroke_width=2, stroke_fill="black")
            y += box[3] - box[1] + spacing
        output = io.BytesIO()
        canvas.convert("RGB").save(output, "JPEG", quality=94)
    return GeneratedImage(output.getvalue(), metadata={**image.metadata, "overlay": True, "overlay_lines": lines[:max_lines], "rendered_lines": wrapped})

