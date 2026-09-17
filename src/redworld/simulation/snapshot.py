from __future__ import annotations

from collections import Counter

from redworld.simulation.world_state import WorldState


def world_summary(world: WorldState) -> dict[str, object]:
    moving = sum(1 for citizen in world.citizens.values() if citizen.is_moving)
    employed = sum(1 for citizen in world.citizens.values() if citizen.employed)
    return {
        "name": world.name,
        "version": "2.0.0",
        "tick": world.tick,
        "time": world.clock.label,
        "day": world.clock.day,
        "year": world.clock.year,
        "month": world.clock.month,
        "week": world.clock.week,
        "weekday": world.clock.weekday,
        "minute_of_day": world.clock.minute_of_day,
        "population": len(world.citizens),
        "employed": employed,
        "unemployment_rate": world.economy.unemployment_rate,
        "moving": moving,
        "businesses": len(world.businesses),
        "banks": len(world.banks),
        "ledger_entries": world.ledger.audit_entry_count(),
        "ledger_total": str(world.ledger.trial_balance_delta().amount),
        "events": len(world.events.events),
        "households": len(world.households),
        "relationships": len(world.society.relationships),
        "market_food_units": str(world.commerce.market.food_units),
        "living_civilization": {
            "development_level": round(world.civilization.development_level, 3),
            "stability": round(world.civilization.stability, 3),
            "prosperity": round(world.civilization.prosperity, 3),
            "resilience": round(world.civilization.resilience, 3),
            "price_index": round(world.civilization.economy.price_index, 3),
            "inflation_rate": round(world.civilization.economy.inflation_rate, 3),
            "governance_approval": round(world.civilization.governance.approval, 3),
            "active_crises": len(world.civilization.crises.active),
            "history_events": len(world.civilization.history.records),
            "strategy": world.civilization.intelligence.strategy,
        },
        "world_evolution": {
            "births_realized": world.evolution.births_realized,
            "deaths_realized": world.evolution.deaths_realized,
            "marriages_realized": world.evolution.marriages_realized,
            "separations_realized": world.evolution.separations_realized,
            "hires_realized": world.evolution.hires_realized,
            "layoffs_realized": world.evolution.layoffs_realized,
            "businesses_created": world.evolution.businesses_created,
            "businesses_closed": world.evolution.businesses_closed,
            "policies_applied": world.evolution.policies_applied,
            "city_projects_realized": world.evolution.city_projects_realized,
            "crises_triggered": world.evolution.crises_triggered,
            "migrations_realized": world.evolution.migrations_realized,
        },
        "self_evolving_world": {
            "citizen_minds": len(world.self_evolving.minds),
            "social_ties": len(world.self_evolving.social_ties),
            "causal_links": world.self_evolving.causal_links,
            "emergent_events": world.self_evolving.emergent_events_created,
            "adaptations": world.self_evolving.adaptations,
        },
        "autonomous_world": {
            "enabled": world.autonomous_world.enabled,
            "agents": len(world.autonomous_world.agents),
            "total_decisions": world.autonomous_world.total_decisions,
            "autonomous_actions": world.autonomous_world.autonomous_actions,
            "pending_human_reviews": len(world.autonomous_world.pending_reviews),
            "emergence_index": round(world.autonomous_world.emergence_index, 3),
            "learning_index": round(world.autonomous_world.learning_index, 3),
            "world_years_simulated": round(world.autonomous_world.world_years_simulated, 4),
        },
        "autonomous_society": {
            "public_mood": round(world.autonomous_society.public_mood, 3),
            "social_cohesion": round(world.autonomous_society.social_cohesion, 3),
            "civic_participation": round(world.autonomous_society.civic_participation, 3),
            "institutional_trust": round(world.autonomous_society.institutional_trust, 3),
            "collective_agency": round(world.autonomous_society.collective_agency, 3),
            "polarization": round(world.autonomous_society.polarization, 3),
            "institutions": len(world.autonomous_society.institutions),
            "community_groups": len(world.autonomous_society.groups),
            "collective_decisions": world.autonomous_society.decisions_made,
            "education_index": round(world.autonomous_society.education_index, 3),
            "public_health": round(world.autonomous_society.public_health, 3),
            "cultural_vitality": round(world.autonomous_society.cultural_vitality, 3),
            "social_mobility": round(world.autonomous_society.social_mobility, 3),
            "inequality_pressure": round(world.autonomous_society.inequality_pressure, 3),
            "movements": len(world.autonomous_society.movements),
        },
    }


def map_snapshot(world: WorldState, render_sample: int = 100) -> dict[str, object]:
    geography = world.geography
    districts = [
        {
            "id": district.id,
            "name": district.name,
            "kind": district.kind,
            "x": district.center.x,
            "y": district.center.y,
            "width": district.width,
            "height": district.height,
        }
        for district in geography.districts.values()
    ]
    locations = [
        {
            "id": location.id,
            "name": location.name,
            "district_id": location.district_id,
            "type": location.location_type.value,
            "x": location.coordinate.x,
            "y": location.coordinate.y,
            "capacity": location.capacity,
        }
        for location in geography.locations.values()
    ]

    seen: set[tuple[str, str]] = set()
    roads: list[dict[str, object]] = []
    for source, edges in geography.adjacency.items():
        for edge in edges:
            key = tuple(sorted((source, edge.target)))
            typed_key: tuple[str, str] = (key[0], key[1])
            if typed_key in seen:
                continue
            seen.add(typed_key)
            start = geography.locations[source].coordinate
            end = geography.locations[edge.target].coordinate
            source_id = str(source)
            target_id = str(edge.target)
            source_hub = source_id.startswith("hub-")
            target_hub = target_id.startswith("hub-")
            source_street = source_id.startswith("street-")
            target_street = target_id.startswith("street-")
            if source_hub and target_hub:
                road_kind = "arterial"
            elif (source_hub or source_street) and (target_hub or target_street):
                road_kind = "street"
            else:
                road_kind = "access"
            roads.append(
                {
                    "source": source,
                    "target": edge.target,
                    "x1": start.x,
                    "y1": start.y,
                    "x2": end.x,
                    "y2": end.y,
                    "minutes": edge.minutes,
                    "kind": road_kind,
                }
            )

    citizens = list(world.citizens.values())
    stride = max(1, len(citizens) // max(1, render_sample))
    agents: list[dict[str, object]] = []
    for citizen in citizens[::stride][:render_sample]:
        if citizen.current_location_id is None:
            continue
        location = geography.locations[citizen.current_location_id]
        agents.append(
            {
                "id": str(citizen.id),
                "name": citizen.name,
                "x": location.coordinate.x,
                "y": location.coordinate.y,
                "moving": citizen.is_moving,
                "location_id": location.id,
                "destination_location_id": citizen.destination_location_id,
                "action": citizen.current_action,
            }
        )

    counts = Counter(
        citizen.current_location_id
        for citizen in citizens
        if citizen.current_location_id is not None
    )
    density = [
        {"location_id": location_id, "count": count} for location_id, count in counts.items()
    ]
    return {
        "summary": world_summary(world),
        "districts": districts,
        "locations": locations,
        "roads": roads,
        "agents": agents,
        "density": density,
    }


def live_snapshot(
    world: WorldState,
    render_sample: int = 120,
    event_limit: int = 12,
) -> dict[str, object]:
    """Return only dynamic world data for low-overhead live updates."""
    geography = world.geography
    citizens = list(world.citizens.values())
    stride = max(1, len(citizens) // max(1, render_sample))
    agents: list[dict[str, object]] = []
    for citizen in citizens[::stride][:render_sample]:
        if citizen.current_location_id is None:
            continue
        location = geography.locations[citizen.current_location_id]
        agents.append(
            {
                "id": str(citizen.id),
                "name": citizen.name,
                "x": location.coordinate.x,
                "y": location.coordinate.y,
                "moving": citizen.is_moving,
                "location_id": location.id,
                "destination_location_id": citizen.destination_location_id,
                "action": citizen.current_action,
            }
        )

    counts = Counter(
        citizen.current_location_id
        for citizen in citizens
        if citizen.current_location_id is not None
    )
    density = [
        {"location_id": location_id, "count": count} for location_id, count in counts.items()
    ]
    recent_events = world.events.events[-event_limit:]
    return {
        "summary": world_summary(world),
        "agents": agents,
        "density": density,
        "events": [
            {"name": event.event_type, "tick": event.tick, "payload": event.payload}
            for event in recent_events
        ],
    }


def civilization_snapshot(world: WorldState) -> dict[str, object]:
    state = world.civilization
    return {
        "development_level": round(state.development_level, 3),
        "stability": round(state.stability, 3),
        "prosperity": round(state.prosperity, 3),
        "resilience": round(state.resilience, 3),
        "demography": {
            "resident_population": state.demography.resident_population,
            "births": state.demography.births,
            "deaths": state.demography.deaths,
            "marriages": state.demography.marriages,
            "separations": state.demography.separations,
            "households_formed": state.demography.households_formed,
            "generation": state.demography.generation,
            "fertility_rate": round(state.demography.fertility_rate, 4),
            "mortality_rate": round(state.demography.mortality_rate, 4),
            "median_age": round(state.demography.median_age, 2),
            "dependency_ratio": round(state.demography.dependency_ratio, 3),
        },
        "careers": {
            "promotions": state.careers.promotions,
            "job_changes": state.careers.job_changes,
            "layoffs": state.careers.layoffs,
            "hires": state.careers.hires,
            "mobility_index": round(state.careers.mobility_index, 3),
            "average_skill": round(state.careers.average_skill, 3),
            "wage_index": round(state.careers.wage_index, 3),
            "career_ladder": {
                key: round(value, 3) for key, value in state.careers.career_ladder.items()
            },
            "class_distribution": {
                key.value: round(value, 3)
                for key, value in state.careers.class_distribution.items()
            },
        },
        "economy": {
            "price_index": round(state.economy.price_index, 4),
            "inflation_rate": round(state.economy.inflation_rate, 4),
            "demand_index": round(state.economy.demand_index, 3),
            "supply_index": round(state.economy.supply_index, 3),
            "poverty_rate": round(state.economy.poverty_rate, 3),
            "wealth_concentration": round(state.economy.wealth_concentration, 3),
            "business_births": state.economy.business_births,
            "business_failures": state.economy.business_failures,
            "productivity_index": round(state.economy.productivity_index, 3),
            "confidence_index": round(state.economy.confidence_index, 3),
        },
        "governance": {
            "approval": round(state.governance.approval, 3),
            "months_to_election": state.governance.months_to_election,
            "elections_held": state.governance.elections_held,
            "governing_bloc": state.governance.governing_bloc,
            "opposition_bloc": state.governance.opposition_bloc,
            "seats": dict(state.governance.seats),
            "public_budget_index": round(state.governance.public_budget_index, 3),
            "policy_effectiveness": round(state.governance.policy_effectiveness, 3),
            "policies": [
                {
                    "year": policy.year,
                    "month": policy.month,
                    "name": policy.name,
                    "area": policy.area,
                    "support": round(policy.support, 3),
                    "active": policy.active,
                }
                for policy in state.governance.policies[-20:]
            ],
        },
        "social_dynamics": {
            "cooperation": round(state.social.cooperation, 3),
            "conflict": round(state.social.conflict, 3),
            "protest_pressure": round(state.social.protest_pressure, 3),
            "opinion_diversity": round(state.social.opinion_diversity, 3),
            "norm_adaptation": round(state.social.norm_adaptation, 3),
            "protests": state.social.protests,
            "civic_campaigns": state.social.civic_campaigns,
        },
        "city_evolution": {
            "infrastructure_index": round(state.city.infrastructure_index, 3),
            "housing_capacity_index": round(state.city.housing_capacity_index, 3),
            "public_space_index": round(state.city.public_space_index, 3),
            "migration_balance": state.city.migration_balance,
            "construction_projects": state.city.construction_projects,
            "land_use_changes": state.city.land_use_changes,
            "developments": [
                {
                    "year": development.year,
                    "month": development.month,
                    "district_id": development.district_id,
                    "project": development.project,
                    "impact": round(development.impact, 3),
                }
                for development in state.city.developments[-20:]
            ],
        },
        "crises": {
            "resilience": round(state.crises.resilience, 3),
            "resolved": state.crises.resolved,
            "active": [
                {
                    "kind": crisis.kind.value,
                    "started_year": crisis.started_year,
                    "started_month": crisis.started_month,
                    "severity": round(crisis.severity, 3),
                    "pressure": round(crisis.pressure, 3),
                    "duration_months": crisis.duration_months,
                }
                for crisis in state.crises.active
            ],
        },
        "world_intelligence": {
            "citizen_adaptation": round(state.intelligence.citizen_adaptation, 3),
            "institution_adaptation": round(state.intelligence.institution_adaptation, 3),
            "economic_adaptation": round(state.intelligence.economic_adaptation, 3),
            "foresight": round(state.intelligence.foresight, 3),
            "strategy": state.intelligence.strategy,
            "decisions": state.intelligence.decisions,
        },
        "history_count": len(state.history.records),
    }


def autonomous_world_snapshot(world: WorldState) -> dict[str, object]:
    state = world.autonomous_world
    kinds = Counter(agent.kind.value for agent in state.agents.values())
    pending = list(state.pending_reviews.values())
    return {
        "enabled": state.enabled,
        "initialized": state.initialized,
        "agents": len(state.agents),
        "agent_kinds": dict(kinds),
        "total_decisions": state.total_decisions,
        "autonomous_actions": state.autonomous_actions,
        "blocked_actions": state.blocked_actions,
        "pending_human_reviews": len(pending),
        "approved_actions": state.approved_actions,
        "rejected_actions": state.rejected_actions,
        "replans": state.replans,
        "interactions": len(state.interactions),
        "collective_signal": round(state.collective_signal, 3),
        "emergence_index": round(state.emergence_index, 3),
        "learning_index": round(state.learning_index, 3),
        "world_years_simulated": round(state.world_years_simulated, 4),
        "pending_reviews": [
            {
                "id": review.id,
                "agent_id": review.agent_id,
                "agent_name": review.agent_name,
                "agent_kind": review.agent_kind.value,
                "intent": review.intent.value,
                "reason": review.reason,
                "risk_level": review.risk_level.value,
                "risk_score": round(review.risk_score, 3),
                "expected_impact": review.expected_impact,
                "created_tick": review.created_tick,
                "status": review.status.value,
            }
            for review in pending[-50:]
        ],
        "recent_interactions": [
            {
                "tick": interaction.tick,
                "source_agent_id": interaction.source_agent_id,
                "target_agent_id": interaction.target_agent_id,
                "kind": interaction.kind,
                "outcome": round(interaction.outcome, 3),
                "summary": interaction.summary,
            }
            for interaction in state.interactions[-30:]
        ],
    }


def agent_snapshot(world: WorldState, agent_id: str) -> dict[str, object] | None:
    agent = world.autonomous_world.agents.get(agent_id)
    if agent is None:
        return None
    return {
        "agent_id": agent.agent_id,
        "kind": agent.kind.value,
        "name": agent.name,
        "autonomy": round(agent.autonomy, 3),
        "risk_tolerance": round(agent.risk_tolerance, 3),
        "learning_rate": round(agent.learning_rate, 3),
        "last_observed_tick": agent.last_observed_tick,
        "last_decision_tick": agent.last_decision_tick,
        "decisions": agent.decisions,
        "successful_actions": agent.successful_actions,
        "failed_actions": agent.failed_actions,
        "beliefs": {
            key: {
                "value": round(belief.value, 3),
                "confidence": round(belief.confidence, 3),
                "learned_tick": belief.learned_tick,
                "source": belief.source,
            }
            for key, belief in agent.beliefs.items()
        },
        "goals": [
            {
                "key": goal.key,
                "priority": round(goal.priority, 3),
                "target": round(goal.target, 3),
                "progress": round(goal.progress, 3),
                "active": goal.active,
            }
            for goal in agent.goals
        ],
        "plan": None
        if agent.plan is None
        else {
            "goal_key": agent.plan.goal_key,
            "current_step": agent.plan.current_step,
            "revisions": agent.plan.revisions,
            "complete": agent.plan.complete,
            "steps": [
                {
                    "intent": step.intent.value,
                    "reason": step.reason,
                    "completed": step.completed,
                }
                for step in agent.plan.steps
            ],
        },
        "memories": [
            {
                "tick": memory.tick,
                "kind": memory.kind,
                "summary": memory.summary,
                "outcome": round(memory.outcome, 3),
                "importance": round(memory.importance, 3),
            }
            for memory in agent.memories[-16:]
        ],
    }


def evolution_snapshot(world: WorldState) -> dict[str, object]:
    state = world.evolution
    return {
        "version": "1.4.0",
        "entity_population": len(world.citizens),
        "entity_businesses": len(world.businesses),
        "entity_households": len(world.households),
        "births_realized": state.births_realized,
        "deaths_realized": state.deaths_realized,
        "marriages_realized": state.marriages_realized,
        "separations_realized": state.separations_realized,
        "hires_realized": state.hires_realized,
        "layoffs_realized": state.layoffs_realized,
        "businesses_created": state.businesses_created,
        "businesses_closed": state.businesses_closed,
        "policies_applied": state.policies_applied,
        "city_projects_realized": state.city_projects_realized,
        "crises_triggered": state.crises_triggered,
        "migrations_realized": state.migrations_realized,
        "active_world_shocks": dict(state.active_shocks),
    }


def self_evolving_snapshot(world: WorldState) -> dict[str, object]:
    from redworld.domains.self_evolving import SelfEvolvingCivilizationService

    service = SelfEvolvingCivilizationService()
    service.bootstrap(world)
    return service.snapshot(world)


def living_digital_world_snapshot(world: WorldState) -> dict[str, object]:
    from redworld.domains.living_world_v2 import LivingDigitalWorldService

    service = LivingDigitalWorldService()
    service.bootstrap(world)
    world.living_world_v2.world_inspections += 1
    return service.snapshot(world)


def world_timeline_snapshot(world: WorldState, limit: int = 100) -> dict[str, object]:
    records = world.living_world_v2.timeline[-limit:]
    return {
        "total": len(world.living_world_v2.timeline),
        "items": [
            {
                "sequence": r.sequence,
                "tick": r.tick,
                "year": r.year,
                "month": r.month,
                "category": r.category,
                "title": r.title,
                "cause": r.cause,
                "effect": r.effect,
                "significance": round(r.significance, 3),
            }
            for r in records
        ],
    }
