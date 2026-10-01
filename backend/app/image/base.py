from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.utils.imaging import validate_image


@dataclass
class GeneratedImage:
    data: bytes
    mime_type: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        detected, dimensions = validate_image(self.data)
        if self.mime_type and self.mime_type != detected:
            raise ValueError("declared image MIME does not match bytes")
        self.mime_type = detected
        self.metadata.setdefault("dimensions", dimensions)


class ImageProvider(ABC):
    @property
    @abstractmethod
    def configured(self) -> bool: ...

    @abstractmethod
    async def generate(self, prompt: str, size: str = "1024x1024") -> GeneratedImage: ...

    async def close(self) -> None:
        return None

