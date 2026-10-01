from app.utils.text import chunks, extract_json


def test_json_extraction_and_chunking():
    assert extract_json('prefix ```json\n{"ok": true}\n``` suffix')["ok"] is True
    parts = chunks("one two three", 7)
    assert " ".join(parts) == "one two three"
    assert all(len(item) <= 7 for item in parts)

