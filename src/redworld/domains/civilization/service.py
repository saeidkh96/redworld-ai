from __future__ import annotations

from statistics import mean
from typing import Protocol

from redworld.core.events import DomainEvent
from redworld.domain.entities.citizen import Citizen
from redworld.domains.autonomy import SocietyState
from redworld.domains.civilization.models import (
    CivilizationState,
    CrisisKind,
    CrisisRecord,
    DevelopmentRecord,
    HistoricalRecord,
    PolicyRecord,
    SocialClass,
)
from redworld.domains.life.progression import CitizenLifeProfile


class EventSink(Protocol):
    def append(self, event: DomainEvent) -> None: ...


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class LivingCivilizationService:
    """Deterministic long-horizon civilization evolution for RedWorld AI."""

    def bootstrap(
        self,
        *,
        state: CivilizationState,
        citizens: list[Citizen],
        profiles: dict[str, CitizenLifeProfile],
        society: SocietyState,
        tick: int,
        year: int,
        month: int,
        events: EventSink,
    ) -> None:
        if state.initialized:
            return
        state.initialized = True
        state.demography.resident_population = len(citizens)
        if citizens:
            ages = sorted(c.age for c in citizens)
            state.demography.median_age = float(ages[len(ages) // 2])
        values = [profiles[str(c.id)] for c in citizens if str(c.id) in profiles]
        if values:
            state.careers.average_skill = mean(p.skill for p in values)
            state.careers.mobility_index = society.social_mobility
        self._record_history(
            state=state,
            tick=tick,
            year=year,
            month=month,
            category="foundation",
            title="Living Civilization foundation established",
            summary=(
                "Genesis City connected demography, careers, economy, governance, "
                "society, city evolution, crises, history and adaptive intelligence."
            ),
            causes=["autonomous_society"],
            effects=["integrated_civilization_model"],
            significance=0.9,
        )
        events.append(DomainEvent("CivilizationInitialized", tick, {"year": year, "month": month}))

    def daily_update(
        self,
        *,
        state: CivilizationState,
        citizens: list[Citizen],
        profiles: dict[str, CitizenLifeProfile],
        society: SocietyState,
        unemployment_rate: float,
        tick: int,
        year: int,
        month: int,
        events: EventSink,
    ) -> None:
        if not citizens:
            return
        values = [profiles[str(c.id)] for c in citizens if str(c.id) in profiles]
        avg_happiness = mean(p.happiness for p in values) if values else 0.5
        avg_skill = mean(p.skill for p in values) if values else 0.5
        avg_health = (
            mean((p.physical_health + p.mental_health) / 2 for p in values) if values else 0.5
        )
        avg_burnout = mean(p.burnout_risk for p in values) if values else 0.1

        state.careers.average_skill = clamp(0.92 * state.careers.average_skill + 0.08 * avg_skill)
        state.careers.mobility_index = clamp(
            0.85 * state.careers.mobility_index
            + 0.15 * ((society.social_mobility + avg_skill + society.education_index) / 3)
        )

        demand_target = clamp(0.55 * avg_happiness + 0.45 * (1.0 - unemployment_rate))
        supply_target = clamp(0.55 * state.economy.productivity_index + 0.45 * avg_skill)
        state.economy.demand_index = clamp(0.92 * state.economy.demand_index + 0.08 * demand_target)
        state.economy.supply_index = clamp(0.92 * state.economy.supply_index + 0.08 * supply_target)
        state.economy.productivity_index = clamp(
            0.94 * state.economy.productivity_index + 0.06 * ((avg_skill + avg_health) / 2)
        )
        state.economy.confidence_index = clamp(
            0.85 * state.economy.confidence_index
            + 0.15 * ((society.public_mood + state.governance.approval) / 2)
        )
        state.economy.poverty_rate = clamp(
            0.94 * state.economy.poverty_rate
            + 0.06 * (0.55 * unemployment_rate + 0.45 * society.inequality_pressure)
        )
        state.economy.wealth_concentration = clamp(
            0.96 * state.economy.wealth_concentration
            + 0.04 * (0.35 + 0.65 * society.inequality_pressure)
        )

        state.social.cooperation = clamp(
            0.9 * state.social.cooperation + 0.1 * society.social_cohesion
        )
        state.social.conflict = clamp(
            0.85 * state.social.conflict
            + 0.15 * ((society.polarization + society.inequality_pressure + avg_burnout) / 3)
        )
        state.social.protest_pressure = clamp(
            0.82 * state.social.protest_pressure
            + 0.18 * ((state.social.conflict + society.inequality_pressure) / 2)
        )
        state.social.opinion_diversity = clamp(
            0.95 * state.social.opinion_diversity + 0.05 * (0.35 + society.polarization)
        )
        state.social.norm_adaptation = clamp(
            0.9 * state.social.norm_adaptation + 0.1 * society.cultural_vitality
        )

        state.governance.approval = clamp(
            0.92 * state.governance.approval
            + 0.08
            * (
                0.35 * society.public_mood
                + 0.25 * society.institutional_trust
                + 0.20 * (1.0 - unemployment_rate)
                + 0.20 * (1.0 - state.social.conflict)
            )
        )
        state.governance.policy_effectiveness = clamp(
            0.90 * state.governance.policy_effectiveness
            + 0.10 * ((state.governance.approval + society.collective_agency) / 2)
        )

        self._adapt_intelligence(state, society, unemployment_rate)
        self._progress_crises(state, avg_health)
        self._update_aggregate_indices(state, society)

        if state.social.protest_pressure >= 0.60 and tick % 24 == 0:
            state.social.protests += 1
            events.append(
                DomainEvent(
                    "CivicProtestEmerging",
                    tick,
                    {"pressure": round(state.social.protest_pressure, 3)},
                )
            )

    def monthly_update(
        self,
        *,
        state: CivilizationState,
        citizens: list[Citizen],
        society: SocietyState,
        unemployment_rate: float,
        district_ids: list[str],
        tick: int,
        year: int,
        month: int,
        events: EventSink,
    ) -> None:
        state.governance.months_to_election -= 1
        if state.governance.months_to_election <= 0:
            self._hold_election(state, society, tick, year, month, events)

        imbalance = state.economy.demand_index - state.economy.supply_index
        target_inflation = max(-0.03, min(0.18, 0.02 + imbalance * 0.12))
        state.economy.inflation_rate = 0.65 * state.economy.inflation_rate + 0.35 * target_inflation
        state.economy.price_index = max(
            0.5, state.economy.price_index * (1.0 + state.economy.inflation_rate / 12)
        )
        state.careers.wage_index = max(
            0.5,
            state.careers.wage_index * (1.0 + max(-0.01, state.economy.inflation_rate * 0.45) / 12),
        )

        employed = sum(1 for citizen in citizens if citizen.employed)
        expected_hires = int(max(0.0, (1.0 - unemployment_rate) * len(citizens) * 0.002))
        expected_layoffs = int(max(0.0, unemployment_rate * len(citizens) * 0.0015))
        state.careers.hires += expected_hires
        state.careers.layoffs += expected_layoffs
        promotions = int(employed * state.careers.average_skill * 0.0008)
        state.careers.promotions += promotions
        state.careers.job_changes += int(employed * state.careers.mobility_index * 0.0005)
        lead = clamp(0.03 + 0.10 * state.careers.average_skill)
        senior = clamp(0.14 + 0.20 * state.careers.average_skill)
        entry = clamp(0.38 - 0.20 * state.careers.mobility_index)
        mid = max(0.0, 1.0 - lead - senior - entry)
        ladder_total = entry + mid + senior + lead
        state.careers.career_ladder = {
            "entry": entry / ladder_total,
            "mid": mid / ladder_total,
            "senior": senior / ladder_total,
            "lead": lead / ladder_total,
        }

        state.economy.business_births += int(state.economy.confidence_index >= 0.60)
        state.economy.business_failures += int(
            state.economy.confidence_index <= 0.35 or state.social.conflict >= 0.65
        )

        self._evolve_social_classes(state, unemployment_rate)
        if state.social.cooperation >= 0.68:
            state.social.civic_campaigns += 1
        for crisis in state.crises.active:
            crisis.duration_months += 1
        state.city.migration_balance += int(
            round((state.prosperity + state.stability - 1.0) * len(citizens) * 0.002)
        )
        state.demography.resident_population = max(
            1,
            len(citizens)
            + state.city.migration_balance
            + state.demography.births
            - state.demography.deaths,
        )
        self._evolve_city(state, district_ids, tick, year, month, events)
        self._consider_crisis(state, society, unemployment_rate, tick, year, month, events)
        self._consider_policy(state, society, tick, year, month, events)

    def yearly_update(
        self,
        *,
        state: CivilizationState,
        citizens: list[Citizen],
        society: SocietyState,
        tick: int,
        year: int,
        month: int,
        events: EventSink,
    ) -> None:
        population = len(citizens)
        births = int(population * state.demography.fertility_rate)
        senior_share = sum(1 for c in citizens if c.age >= 65) / max(1, population)
        deaths = int(population * (state.demography.mortality_rate + senior_share * 0.008))
        marriages = int(population * clamp(society.social_cohesion) * 0.006)
        separations = int(population * clamp(society.polarization) * 0.002)
        state.demography.births += births
        state.demography.deaths += deaths
        state.demography.resident_population = max(
            1, state.demography.resident_population + births - deaths
        )
        state.demography.marriages += marriages
        state.demography.separations += separations
        state.demography.households_formed += max(0, marriages - separations)
        ages = sorted(c.age for c in citizens)
        if ages:
            state.demography.median_age = float(ages[len(ages) // 2])
        young = sum(1 for c in citizens if c.age < 18)
        old = sum(1 for c in citizens if c.age >= 65)
        state.demography.dependency_ratio = (young + old) / max(1, population - young - old)
        if year > 1 and year % 25 == 0:
            state.demography.generation += 1

        self._record_history(
            state=state,
            tick=tick,
            year=year,
            month=month,
            category="demography",
            title=f"Year {year} demographic transition",
            summary=(
                f"Civilization recorded {births} births, {deaths} deaths, "
                f"{marriages} marriages and {separations} separations."
            ),
            causes=["aging", "social_cohesion", "health_conditions"],
            effects=["generation_change", "household_change"],
            significance=0.65,
        )
        events.append(
            DomainEvent(
                "CivilizationYearCompleted",
                tick,
                {"year": year, "births": births, "deaths": deaths},
            )
        )

    def _adapt_intelligence(
        self, state: CivilizationState, society: SocietyState, unemployment_rate: float
    ) -> None:
        intelligence = state.intelligence
        intelligence.citizen_adaptation = clamp(
            0.9 * intelligence.citizen_adaptation
            + 0.1 * ((state.careers.mobility_index + society.education_index) / 2)
        )
        intelligence.institution_adaptation = clamp(
            0.9 * intelligence.institution_adaptation
            + 0.1 * ((society.collective_agency + state.governance.policy_effectiveness) / 2)
        )
        intelligence.economic_adaptation = clamp(
            0.9 * intelligence.economic_adaptation
            + 0.1 * ((state.economy.confidence_index + state.economy.productivity_index) / 2)
        )
        intelligence.foresight = clamp(
            0.92 * intelligence.foresight
            + 0.08 * ((intelligence.institution_adaptation + intelligence.economic_adaptation) / 2)
        )
        if state.economy.poverty_rate > 0.30 or unemployment_rate > 0.25:
            strategy = "inclusive_growth"
        elif state.social.conflict > 0.45:
            strategy = "social_stability"
        elif state.crises.active:
            strategy = "crisis_resilience"
        elif society.education_index < 0.55:
            strategy = "human_capital"
        else:
            strategy = "balanced_development"
        if strategy != intelligence.strategy:
            intelligence.strategy = strategy
            intelligence.decisions += 1

    def _evolve_social_classes(self, state: CivilizationState, unemployment_rate: float) -> None:
        dist = state.careers.class_distribution
        pressure = clamp((unemployment_rate + state.economy.poverty_rate) / 2)
        mobility = state.careers.mobility_index
        low = clamp(0.12 + 0.42 * pressure)
        upper = clamp(0.05 + 0.12 * state.economy.wealth_concentration)
        middle = clamp(0.22 + 0.32 * mobility - 0.12 * pressure)
        working = max(0.0, 1.0 - low - middle - upper)
        total = low + middle + upper + working
        dist[SocialClass.LOW_INCOME] = low / total
        dist[SocialClass.WORKING] = working / total
        dist[SocialClass.MIDDLE] = middle / total
        dist[SocialClass.UPPER] = upper / total

    def _evolve_city(
        self,
        state: CivilizationState,
        district_ids: list[str],
        tick: int,
        year: int,
        month: int,
        events: EventSink,
    ) -> None:
        need = max(state.economy.demand_index, state.economy.poverty_rate)
        if district_ids and need >= 0.55:
            district_id = district_ids[
                (year * 12 + month + state.city.construction_projects) % len(district_ids)
            ]
            if state.economy.poverty_rate >= 0.25:
                project = "Affordable housing expansion"
            elif state.economy.productivity_index >= 0.60:
                project = "Economic infrastructure upgrade"
            else:
                project = "Public space and mobility upgrade"
            impact = clamp(0.35 + 0.45 * state.governance.policy_effectiveness)
            state.city.developments.append(
                DevelopmentRecord(year, month, district_id, project, impact)
            )
            del state.city.developments[:-60]
            state.city.construction_projects += 1
            state.city.infrastructure_index = clamp(state.city.infrastructure_index + 0.01 * impact)
            state.city.housing_capacity_index = clamp(
                state.city.housing_capacity_index + 0.008 * impact
            )
            state.city.public_space_index = clamp(state.city.public_space_index + 0.006 * impact)
            state.city.land_use_changes += 1
            events.append(
                DomainEvent(
                    "CityDevelopmentStarted",
                    tick,
                    {"district_id": district_id, "project": project, "impact": round(impact, 3)},
                )
            )

    def _consider_policy(
        self,
        state: CivilizationState,
        society: SocietyState,
        tick: int,
        year: int,
        month: int,
        events: EventSink,
    ) -> None:
        if state.economy.poverty_rate >= 0.25:
            name, area = "Income Security Act", "welfare"
        elif state.economy.inflation_rate >= 0.08:
            name, area = "Price Stability Program", "economy"
        elif society.public_health <= 0.60:
            name, area = "Public Health Capacity Act", "health"
        elif society.education_index <= 0.55:
            name, area = "Learning Mobility Program", "education"
        else:
            return
        if any(policy.name == name and policy.active for policy in state.governance.policies):
            return
        support = clamp(
            (state.governance.approval + society.civic_participation + society.collective_agency)
            / 3
        )
        if support < 0.42:
            return
        state.governance.policies.append(PolicyRecord(year, month, name, area, support))
        del state.governance.policies[:-40]
        state.governance.public_budget_index = clamp(state.governance.public_budget_index + 0.02)
        self._record_history(
            state=state,
            tick=tick,
            year=year,
            month=month,
            category="governance",
            title=name,
            summary=f"Genesis governance enacted {name} with {support:.0%} modeled support.",
            causes=[area, "public_pressure"],
            effects=["policy_response", "budget_reallocation"],
            significance=0.7,
        )
        events.append(
            DomainEvent("PolicyEnacted", tick, {"name": name, "support": round(support, 3)})
        )

    def _hold_election(
        self,
        state: CivilizationState,
        society: SocietyState,
        tick: int,
        year: int,
        month: int,
        events: EventSink,
    ) -> None:
        state.governance.elections_held += 1
        reform_support = clamp((1.0 - state.governance.approval + society.polarization) / 2)
        if reform_support > 0.52:
            state.governance.governing_bloc, state.governance.opposition_bloc = (
                state.governance.opposition_bloc,
                state.governance.governing_bloc,
            )
        winner = state.governance.governing_bloc
        loser = state.governance.opposition_bloc
        state.governance.seats = {winner: 7, loser: 5}
        state.governance.months_to_election = state.governance.election_cycle_months
        self._record_history(
            state=state,
            tick=tick,
            year=year,
            month=month,
            category="politics",
            title=f"Civil election {state.governance.elections_held}",
            summary=f"{state.governance.governing_bloc} formed the governing majority.",
            causes=["public_approval", "polarization", "civic_participation"],
            effects=["government_mandate"],
            significance=0.85,
        )
        events.append(
            DomainEvent(
                "ElectionCompleted",
                tick,
                {
                    "winner": state.governance.governing_bloc,
                    "election": state.governance.elections_held,
                },
            )
        )

    def _consider_crisis(
        self,
        state: CivilizationState,
        society: SocietyState,
        unemployment_rate: float,
        tick: int,
        year: int,
        month: int,
        events: EventSink,
    ) -> None:
        active_kinds = {crisis.kind for crisis in state.crises.active if crisis.active}
        candidate: tuple[CrisisKind, float] | None = None
        if unemployment_rate >= 0.32 and CrisisKind.RECESSION not in active_kinds:
            candidate = (CrisisKind.RECESSION, unemployment_rate)
        elif state.economy.supply_index < 0.35 and CrisisKind.SHORTAGE not in active_kinds:
            candidate = (CrisisKind.SHORTAGE, 1.0 - state.economy.supply_index)
        elif society.public_health < 0.50 and CrisisKind.EPIDEMIC not in active_kinds:
            candidate = (CrisisKind.EPIDEMIC, 1.0 - society.public_health)
        elif state.economy.confidence_index > 0.78 and CrisisKind.BOOM not in active_kinds:
            candidate = (CrisisKind.BOOM, state.economy.confidence_index)
        elif state.social.conflict > 0.72 and CrisisKind.POLICY_SHOCK not in active_kinds:
            candidate = (CrisisKind.POLICY_SHOCK, state.social.conflict)
        if candidate is None:
            return
        kind, severity = candidate
        state.crises.active.append(
            CrisisRecord(kind, year, month, clamp(severity), clamp(severity))
        )
        self._record_history(
            state=state,
            tick=tick,
            year=year,
            month=month,
            category="crisis",
            title=f"{kind.value.replace('_', ' ').title()} begins",
            summary=f"A {kind.value} event emerged with modeled severity {severity:.2f}.",
            causes=["system_pressure"],
            effects=["adaptive_response", "economic_and_social_change"],
            significance=0.9,
        )
        events.append(
            DomainEvent(
                "CivilizationCrisisStarted",
                tick,
                {"kind": kind.value, "severity": round(severity, 3)},
            )
        )

    def _progress_crises(self, state: CivilizationState, avg_health: float) -> None:
        survivors: list[CrisisRecord] = []
        for crisis in state.crises.active:
            if not crisis.active:
                continue
            crisis.pressure = clamp(
                crisis.pressure * (0.985 - 0.008 * state.crises.resilience - 0.004 * avg_health)
            )
            if crisis.pressure < 0.18:
                crisis.active = False
                state.crises.resolved += 1
            else:
                survivors.append(crisis)
        state.crises.active = survivors
        state.crises.resilience = clamp(
            0.9 * state.crises.resilience
            + 0.1 * ((state.city.infrastructure_index + state.governance.policy_effectiveness) / 2)
        )

    def _update_aggregate_indices(self, state: CivilizationState, society: SocietyState) -> None:
        state.prosperity = clamp(
            (
                state.economy.productivity_index
                + state.economy.confidence_index
                + state.careers.mobility_index
                + (1.0 - state.economy.poverty_rate)
            )
            / 4
        )
        state.stability = clamp(
            (
                society.social_cohesion
                + state.governance.approval
                + (1.0 - state.social.conflict)
                + (1.0 - society.polarization)
            )
            / 4
        )
        state.resilience = clamp(
            (state.crises.resilience + state.city.infrastructure_index + society.collective_agency)
            / 3
        )
        state.development_level = clamp(
            (
                state.prosperity
                + state.stability
                + state.resilience
                + society.education_index
                + society.public_health
            )
            / 5
        )

    def _record_history(
        self,
        *,
        state: CivilizationState,
        tick: int,
        year: int,
        month: int,
        category: str,
        title: str,
        summary: str,
        causes: list[str],
        effects: list[str],
        significance: float,
    ) -> None:
        state.history.sequence += 1
        state.history.records.append(
            HistoricalRecord(
                sequence=state.history.sequence,
                tick=tick,
                year=year,
                month=month,
                category=category,
                title=title,
                summary=summary,
                causes=causes,
                effects=effects,
                significance=clamp(significance),
            )
        )
        del state.history.records[:-500]
