from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CitizenArc:
    citizen_id: str
    family_role: str = "member"
    education_stage: str = "general"
    career_level: str = "entry"
    personality_depth: float = 0.5
    memory_depth: float = 0.0
    legacy_knowledge: float = 0.0
    life_transitions: int = 0
    initialized: bool = False


@dataclass(slots=True)
class OrganizationProfile:
    organization_id: str
    kind: str
    members: int = 0
    influence: float = 0.5
    resilience: float = 0.5
    collective_action: float = 0.0
    action_active: bool = False
    last_action_month: str = ""


@dataclass(slots=True)
class UrbanDistrictState:
    district_id: str
    housing_demand: float = 0.0
    land_use_pressure: float = 0.0
    infrastructure_load: float = 0.0
    expansions: int = 0
    last_expansion_tick: int = -1


@dataclass(slots=True)
class TimelineRecord:
    sequence: int
    tick: int
    year: int
    month: int
    category: str
    title: str
    cause: str
    effect: str
    significance: float


@dataclass(slots=True)
class LivingDigitalWorldState:
    last_day: object = -1
    last_month: str = ""
    last_year: int = -1
    citizen_arcs: dict[str, CitizenArc] = field(default_factory=dict)
    organizations: dict[str, OrganizationProfile] = field(default_factory=dict)
    urban_districts: dict[str, UrbanDistrictState] = field(default_factory=dict)
    timeline: list[TimelineRecord] = field(default_factory=list)
    family_transitions: int = 0
    education_transitions: int = 0
    career_transitions: int = 0
    collective_actions: int = 0
    visible_city_expansions: int = 0
    causal_chains: int = 0
    emergent_crises: int = 0
    long_run_cycles: int = 0
    world_inspections: int = 0
