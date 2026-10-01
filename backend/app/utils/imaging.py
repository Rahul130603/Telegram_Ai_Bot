from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

from .errors import GenerationError


def validate_image(data: bytes) -> tuple[str, tuple[int, int]]:
    if not data:
        raise GenerationError("empty image")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            fmt = (image.format or "").upper()
            size = image.size
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise GenerationError("provider returned invalid image bytes") from exc
    mime = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}.get(fmt)
    if not mime:
        raise GenerationError(f"unsupported image format: {fmt}")
    return mime, size


def to_jpeg(data: bytes) -> bytes:
    mime, _ = validate_image(data)
    if mime == "image/jpeg":
        return data
    with Image.open(io.BytesIO(data)) as image:
        converted = image.convert("RGB")
        output = io.BytesIO()
        converted.save(output, "JPEG", quality=92, optimize=True)
        return output.getvalue()

