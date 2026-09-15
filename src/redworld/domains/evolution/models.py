from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class EvolutionState:
    births_realized: int = 0
    deaths_realized: int = 0
    marriages_realized: int = 0
    separations_realized: int = 0
    hires_realized: int = 0
    layoffs_realized: int = 0
    businesses_created: int = 0
    businesses_closed: int = 0
    policies_applied: int = 0
    city_projects_realized: int = 0
    crises_triggered: int = 0
    migrations_realized: int = 0
    last_year_processed: int = 0
    last_month_processed: tuple[int, int] | None = None
    applied_policy_keys: set[str] = field(default_factory=set)
    realized_developments: set[str] = field(default_factory=set)
    active_shocks: dict[str, float] = field(default_factory=dict)
