from app.image.base import GeneratedImage
from app.image.overlay import add_text_overlay


def test_overlay_and_text_free_preservation(png_bytes):
    image = GeneratedImage(png_bytes)
    unchanged = add_text_overlay(image, [])
    changed = add_text_overlay(image, ["EXACT OFFER"])
    assert unchanged.data == png_bytes
    assert changed.data != png_bytes and changed.metadata["overlay_lines"] == ["EXACT OFFER"]

