from __future__ import annotations

from collections import Counter

from redworld.simulation.world_state import WorldState


def world_summary(world: WorldState) -> dict[str, object]:
    moving = sum(1 for citizen in world.citizens.values() if citizen.is_moving)
    employed = sum(1 for citizen in world.citizens.values() if citizen.employed)
    return {
        "name": world.name,
        "version": "1.2.0",
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
