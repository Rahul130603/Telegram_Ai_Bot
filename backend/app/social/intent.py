from __future__ import annotations

import re

PLATFORMS = {"instagram", "facebook", "linkedin", "x"}


def detect_platform(text: str) -> str | None:
    lowered = text.lower()
    aliases = {"insta": "instagram", "fb": "facebook", "twitter": "x"}
    for platform in PLATFORMS:
        if re.search(rf"\b{platform}\b", lowered):
            return platform
    for alias, platform in aliases.items():
        if re.search(rf"\b{alias}\b", lowered):
            return platform
    return None

