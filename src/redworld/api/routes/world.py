from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from redworld.api.dependencies import get_engine
from redworld.api.schemas import SimulationStepResponse
from redworld.simulation.engine import SimulationEngine
from redworld.simulation.snapshot import live_snapshot, map_snapshot, world_summary

router = APIRouter(prefix="/world", tags=["world"])
EngineDependency = Annotated[SimulationEngine, Depends(get_engine)]


@router.get("")
def get_world(engine: EngineDependency) -> dict[str, object]:
    return world_summary(engine.world)


@router.post("/step", response_model=SimulationStepResponse)
def step_world(
    engine: EngineDependency,
    steps: int = Query(1, ge=1, le=500),
) -> SimulationStepResponse:
    engine.run(steps)
    return SimulationStepResponse(
        stepped=steps,
        world=world_summary(engine.world),
    )


@router.get("/map")
def get_map(
    engine: EngineDependency,
    render_sample: int = Query(100, ge=0, le=500),
) -> dict[str, object]:
    return map_snapshot(engine.world, render_sample=render_sample)


@router.get("/citizens")
def list_citizens(
    engine: EngineDependency,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, object]:
    citizens = list(engine.world.citizens.values())
    selected = citizens[offset : offset + limit]
    return {
        "total": len(citizens),
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "id": str(citizen.id),
                "name": citizen.name,
                "age": citizen.age,
                "occupation": citizen.occupation,
                "employed": citizen.employed,
                "home_location_id": citizen.home_location_id,
                "work_location_id": citizen.work_location_id,
                "current_location_id": citizen.current_location_id,
                "moving": citizen.is_moving,
                "action": citizen.current_action,
                "household_id": str(citizen.household_id) if citizen.household_id else None,
            }
            for citizen in selected
        ],
    }


@router.get("/citizens/{citizen_id}")
def get_citizen(citizen_id: str, engine: EngineDependency) -> dict[str, object]:
    citizen = engine.world.citizens.get(citizen_id)
    if citizen is None:
        raise HTTPException(status_code=404, detail="citizen not found")

    location = engine.world.geography.locations.get(citizen.current_location_id or "")
    cash = (
        None
        if citizen.cash_account_id is None
        else str(engine.world.ledger.balance(citizen.cash_account_id))
    )
    profile = engine.world.life_profiles.get(str(citizen.id))
    return {
        "id": str(citizen.id),
        "name": citizen.name,
        "age": citizen.age,
        "occupation": citizen.occupation,
        "employed": citizen.employed,
        "home_location_id": citizen.home_location_id,
        "work_location_id": citizen.work_location_id,
        "current_location_id": citizen.current_location_id,
        "current_location": location.name if location else None,
        "destination_location_id": citizen.destination_location_id,
        "moving": citizen.is_moving,
        "cash": cash,
        "action": citizen.current_action,
        "household_id": str(citizen.household_id) if citizen.household_id else None,
        "needs": {
            "hunger": round(citizen.needs.hunger, 3),
            "energy": round(citizen.needs.energy, 3),
            "social": round(citizen.needs.social, 3),
            "health": round(citizen.needs.health, 3),
            "safety": round(citizen.needs.safety, 3),
        },
        "goals": [
            {"type": goal.goal_type.value, "progress": round(goal.progress, 3)}
            for goal in engine.world.planning.for_citizen(citizen.id)
        ],
        "memories": [
            {"tick": memory.tick, "kind": memory.kind, "summary": memory.summary}
            for memory in engine.world.memories.recent(citizen.id)
        ],
        "relationships": len(engine.world.society.for_citizen(citizen.id)),
        "life": None
        if profile is None
        else {
            "education": round(profile.education, 3),
            "skill": round(profile.skill, 3),
            "happiness": round(profile.happiness, 3),
            "stress": round(profile.stress, 3),
            "physical_health": round(profile.physical_health, 3),
            "mental_health": round(profile.mental_health, 3),
            "belonging": round(profile.belonging, 3),
            "civic_trust": round(profile.civic_trust, 3),
            "culture": round(profile.culture, 3),
            "environmental_awareness": round(profile.environmental_awareness, 3),
            "reputation": round(profile.reputation, 3),
            "autonomy": round(profile.autonomy, 3),
            "life_satisfaction": round(profile.life_satisfaction, 3),
        },
    }


@router.get("/society")
def get_autonomous_society(engine: EngineDependency) -> dict[str, object]:
    state = engine.world.autonomous_society
    return {
        "public_mood": round(state.public_mood, 3),
        "social_cohesion": round(state.social_cohesion, 3),
        "civic_participation": round(state.civic_participation, 3),
        "institutional_trust": round(state.institutional_trust, 3),
        "collective_agency": round(state.collective_agency, 3),
        "polarization": round(state.polarization, 3),
        "decisions_made": state.decisions_made,
        "institutions": [
            {
                "id": key,
                "name": i.name,
                "kind": i.kind.value,
                "trust": round(i.trust, 3),
                "legitimacy": round(i.legitimacy, 3),
                "participation": round(i.participation, 3),
            }
            for key, i in state.institutions.items()
        ],
        "groups": [
            {
                "id": key,
                "name": g.name,
                "members": len(g.member_ids),
                "cohesion": round(g.cohesion, 3),
                "influence": round(g.influence, 3),
            }
            for key, g in state.groups.items()
        ],
        "norms": [
            {"name": n.name, "strength": round(n.strength, 3), "compliance": round(n.compliance, 3)}
            for n in state.norms.values()
        ],
    }


@router.get("/events")
def get_events(
    engine: EngineDependency,
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, object]:
    events = engine.world.events.events[-limit:]
    return {
        "items": [
            {"name": event.event_type, "tick": event.tick, "payload": event.payload}
            for event in events
        ]
    }


@router.websocket("/live")
async def live_world(websocket: WebSocket) -> None:
    await websocket.accept()
    engine = get_engine()
    try:
        while True:
            engine.step()
            await websocket.send_json(
                live_snapshot(
                    engine.world,
                    render_sample=120,
                    event_limit=12,
                )
            )
            await asyncio.sleep(1.25)
    except WebSocketDisconnect:
        return
