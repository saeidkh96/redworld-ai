from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ActionType(StrEnum):
    IDLE = "idle"
    SLEEP = "sleep"
    WORK = "work"
    EAT = "eat"
    SHOP = "shop"
    SOCIALIZE = "socialize"
    RELAX = "relax"
    HEALTHCARE = "healthcare"
    GO_HOME = "go_home"


@dataclass(frozen=True, slots=True)
class ActionProposal:
    action: ActionType
    target_location_id: str | None = None
    reason: str = ""
