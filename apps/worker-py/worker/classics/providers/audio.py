from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class AudioRenderRequest:
    text: str
    voice_profile: str
    output_path: Path
    trace_path: Path


@dataclass(frozen=True)
class AudioRenderResult:
    provider: str
    model: str
    audio_path: Path
    trace_path: Path
    sample_rate: int


class AudioProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    def render(self, request: AudioRenderRequest) -> AudioRenderResult: ...
