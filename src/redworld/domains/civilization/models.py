from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class SocialClass(StrEnum):
    LOW_INCOME = "low_income"
    WORKING = "working"
    MIDDLE = "middle"
    UPPER = "upper"


class CrisisKind(StrEnum):
    RECESSION = "recession"
    SHORTAGE = "shortage"
    EPIDEMIC = "epidemic"
    DISASTER = "disaster"
    BOOM = "boom"
    POLICY_SHOCK = "policy_shock"


@dataclass(slots=True)
class DemographyState:
    resident_population: int = 0
    births: int = 0
    deaths: int = 0
    marriages: int = 0
    separations: int = 0
    households_formed: int = 0
    generation: int = 1
    fertility_rate: float = 0.018
    mortality_rate: float = 0.008
    median_age: float = 35.0
    dependency_ratio: float = 0.35


@dataclass(slots=True)
class CareerState:
    promotions: int = 0
    job_changes: int = 0
    layoffs: int = 0
    hires: int = 0
    mobility_index: float = 0.45
    average_skill: float = 0.45
    wage_index: float = 1.0
    career_ladder: dict[str, float] = field(
        default_factory=lambda: {"entry": 0.32, "mid": 0.43, "senior": 0.20, "lead": 0.05}
    )
    class_distribution: dict[SocialClass, float] = field(
        default_factory=lambda: {
            SocialClass.LOW_INCOME: 0.20,
            SocialClass.WORKING: 0.40,
            SocialClass.MIDDLE: 0.32,
            SocialClass.UPPER: 0.08,
        }
    )


@dataclass(slots=True)
class DynamicEconomyState:
    price_index: float = 1.0
    inflation_rate: float = 0.02
    demand_index: float = 0.55
    supply_index: float = 0.55
    poverty_rate: float = 0.18
    wealth_concentration: float = 0.42
    business_births: int = 0
    business_failures: int = 0
    productivity_index: float = 0.50
    confidence_index: float = 0.55


@dataclass(slots=True)
class PolicyRecord:
    year: int
    month: int
    name: str
    area: str
    support: float
    active: bool = True


@dataclass(slots=True)
class GovernanceState:
    approval: float = 0.55
    election_cycle_months: int = 24
    months_to_election: int = 24
    elections_held: int = 0
    governing_bloc: str = "Civic Coalition"
    opposition_bloc: str = "Community Reform Bloc"
    seats: dict[str, int] = field(
        default_factory=lambda: {"Civic Coalition": 7, "Community Reform Bloc": 5}
    )
    public_budget_index: float = 0.50
    policy_effectiveness: float = 0.50
    policies: list[PolicyRecord] = field(default_factory=list)


@dataclass(slots=True)
class SocialDynamicsState:
    cooperation: float = 0.60
    conflict: float = 0.18
    protest_pressure: float = 0.12
    opinion_diversity: float = 0.45
    norm_adaptation: float = 0.50
    protests: int = 0
    civic_campaigns: int = 0


@dataclass(slots=True)
class DevelopmentRecord:
    year: int
    month: int
    district_id: str
    project: str
    impact: float


@dataclass(slots=True)
class CityEvolutionState:
    infrastructure_index: float = 0.55
    housing_capacity_index: float = 0.55
    public_space_index: float = 0.50
    migration_balance: int = 0
    construction_projects: int = 0
    land_use_changes: int = 0
    developments: list[DevelopmentRecord] = field(default_factory=list)


@dataclass(slots=True)
class CrisisRecord:
    kind: CrisisKind
    started_year: int
    started_month: int
    severity: float
    pressure: float
    active: bool = True
    duration_months: int = 0


@dataclass(slots=True)
class CrisisState:
    active: list[CrisisRecord] = field(default_factory=list)
    resolved: int = 0
    resilience: float = 0.55


@dataclass(slots=True)
class HistoricalRecord:
    sequence: int
    tick: int
    year: int
    month: int
    category: str
    title: str
    summary: str
    causes: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    significance: float = 0.5


@dataclass(slots=True)
class HistoryState:
    sequence: int = 0
    records: list[HistoricalRecord] = field(default_factory=list)


@dataclass(slots=True)
class IntelligenceState:
    citizen_adaptation: float = 0.50
    institution_adaptation: float = 0.50
    economic_adaptation: float = 0.50
    foresight: float = 0.45
    strategy: str = "balanced_development"
    decisions: int = 0


@dataclass(slots=True)
class CivilizationState:
    initialized: bool = False
    development_level: float = 0.50
    stability: float = 0.55
    prosperity: float = 0.50
    resilience: float = 0.55
    demography: DemographyState = field(default_factory=DemographyState)
    careers: CareerState = field(default_factory=CareerState)
    economy: DynamicEconomyState = field(default_factory=DynamicEconomyState)
    governance: GovernanceState = field(default_factory=GovernanceState)
    social: SocialDynamicsState = field(default_factory=SocialDynamicsState)
    city: CityEvolutionState = field(default_factory=CityEvolutionState)
    crises: CrisisState = field(default_factory=CrisisState)
    history: HistoryState = field(default_factory=HistoryState)
    intelligence: IntelligenceState = field(default_factory=IntelligenceState)
