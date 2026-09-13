from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    tick: int
    kind: str
    summary: str
    importance: float = 0.50
