from __future__ import annotations

import json
import re
from typing import Any


def chunks(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    result: list[str] = []
    remaining = text
    while remaining:
        cut = min(limit, len(remaining))
        if cut < len(remaining):
            newline = remaining.rfind("\n", 0, cut)
            space = remaining.rfind(" ", 0, cut)
            boundary = max(newline, space)
            if boundary > 0:
                cut = boundary
        result.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    return result


def extract_json(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I | re.S)
    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("no JSON object found")


def clean_wrapper(value: str) -> str:
    value = value.strip()
    wrappers = [("`", "`"), ('"', '"'), ("'", "'"), ("<", ">")]
    changed = True
    while changed and len(value) >= 2:
        changed = False
        for left, right in wrappers:
            if value.startswith(left) and value.endswith(right):
                value = value[1:-1].strip()
                changed = True
    return value

