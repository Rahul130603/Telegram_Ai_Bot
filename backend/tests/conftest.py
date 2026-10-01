from __future__ import annotations

import io

import pytest
from PIL import Image


@pytest.fixture
def png_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (64, 64), "blue").save(output, "PNG")
    return output.getvalue()


@pytest.fixture
def jpeg_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (64, 64), "red").save(output, "JPEG")
    return output.getvalue()

