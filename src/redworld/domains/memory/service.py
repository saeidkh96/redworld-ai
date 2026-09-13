from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from redworld.domains.memory.models import MemoryRecord


@dataclass(slots=True)
class MemoryService:
    max_records_per_citizen: int = 24
    records: dict[UUID, list[MemoryRecord]] = field(default_factory=dict)

    def remember(self, citizen_id: UUID, record: MemoryRecord) -> None:
        bucket = self.records.setdefault(citizen_id, [])
        bucket.append(record)
        if len(bucket) > self.max_records_per_citizen:
            del bucket[: len(bucket) - self.max_records_per_citizen]

    def recent(self, citizen_id: UUID, limit: int = 8) -> list[MemoryRecord]:
        return self.records.get(citizen_id, [])[-limit:]
