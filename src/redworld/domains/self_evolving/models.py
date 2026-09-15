from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CitizenMind:
    citizen_id: str
    generation: int = 0
    personality: str = "adaptive"
    goal: str = "stability"
    knowledge: float = 0.25
    reputation: float = 0.5


@dataclass
class SocialTie:
    left_id: str
    right_id: str
    affinity: float = 0.5
    trust: float = 0.5
    conflict: float = 0.0


@dataclass
class MarketSignal:
    sector: str
    price: float = 1.0
    demand: float = 1.0
    supply: float = 1.0


@dataclass
class CausalRecord:
    tick: int
    year: int
    cause: str
    effect: str
    magnitude: float


@dataclass
class EmergentEvent:
    event_id: str
    kind: str
    summary: str
    severity: float
    tick: int
    resolved: bool = False


@dataclass
class SelfEvolvingState:
    last_day: int = -1
    last_month: str = ""
    last_year: int = -1
    minds: dict[str, CitizenMind] = field(default_factory=dict)
    social_ties: dict[str, SocialTie] = field(default_factory=dict)
    markets: dict[str, MarketSignal] = field(default_factory=dict)
    history: list[CausalRecord] = field(default_factory=list)
    emergent_events: list[EmergentEvent] = field(default_factory=list)
    generations: dict[int, int] = field(default_factory=dict)
    inheritances: int = 0
    relationship_updates: int = 0
    market_updates: int = 0
    institutional_updates: int = 0
    city_expansions: int = 0
    knowledge_transfers: int = 0
    causal_links: int = 0
    emergent_events_created: int = 0
    adaptations: int = 0
    housing_pressure: float = 0.0
    city_capacity: float = 1.0
    infrastructure: float = 1.0
    public_sentiment: float = 0.5
