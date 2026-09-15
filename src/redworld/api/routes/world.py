from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from redworld.api.dependencies import get_engine
from redworld.api.schemas import SimulationStepResponse
from redworld.domains.agents import ApprovalStatus, AutonomousAgentService
from redworld.simulation.engine import SimulationEngine
from redworld.simulation.snapshot import (
    agent_snapshot,
    autonomous_world_snapshot,
    civilization_snapshot,
    evolution_snapshot,
    live_snapshot,
    map_snapshot,
    world_summary,
)

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
    limit: int = Query(50, ge=1, le=5000),
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
        "autonomous_agent": agent_snapshot(engine.world, str(citizen.id)),
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
            "life_stage": profile.life_stage.value,
            "learning_progress": round(profile.learning_progress, 3),
            "career_progress": round(profile.career_progress, 3),
            "burnout_risk": round(profile.burnout_risk, 3),
            "civic_engagement": round(profile.civic_engagement, 3),
            "cultural_identity": round(profile.cultural_identity, 3),
            "community_influence": round(profile.community_influence, 3),
            "experience_days": profile.experience_days,
            "history": [
                {"year": e.year, "kind": e.kind, "summary": e.summary} for e in profile.events[-10:]
            ],
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
        "education_index": round(state.education_index, 3),
        "public_health": round(state.public_health, 3),
        "cultural_vitality": round(state.cultural_vitality, 3),
        "social_mobility": round(state.social_mobility, 3),
        "inequality_pressure": round(state.inequality_pressure, 3),
        "institutions": [
            {
                "id": key,
                "name": i.name,
                "kind": i.kind.value,
                "trust": round(i.trust, 3),
                "legitimacy": round(i.legitimacy, 3),
                "participation": round(i.participation, 3),
                "capacity": round(i.capacity, 3),
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
                "cultural_identity": round(g.cultural_identity, 3),
            }
            for key, g in state.groups.items()
        ],
        "movements": [
            {
                "name": m.name,
                "cause": m.cause,
                "support": round(m.support, 3),
                "intensity": round(m.intensity, 3),
            }
            for m in state.movements.values()
        ],
        "decision_history": [
            {
                "tick": d.tick,
                "title": d.title,
                "support": round(d.support, 3),
                "enacted": d.enacted,
            }
            for d in state.decision_history[-20:]
        ],
        "norms": [
            {"name": n.name, "strength": round(n.strength, 3), "compliance": round(n.compliance, 3)}
            for n in state.norms.values()
        ],
    }


@router.get("/autonomy")
def get_autonomous_world(engine: EngineDependency) -> dict[str, object]:
    return autonomous_world_snapshot(engine.world)


@router.get("/autonomy/agents")
def list_autonomous_agents(
    engine: EngineDependency,
    kind: str | None = Query(None),
    limit: int = Query(100, ge=1, le=2000),
    offset: int = Query(0, ge=0),
) -> dict[str, object]:
    agents = list(engine.world.autonomous_world.agents.values())
    if kind is not None:
        agents = [agent for agent in agents if agent.kind.value == kind]
    selected = agents[offset : offset + limit]
    return {
        "total": len(agents),
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "agent_id": agent.agent_id,
                "kind": agent.kind.value,
                "name": agent.name,
                "autonomy": round(agent.autonomy, 3),
                "decisions": agent.decisions,
                "last_decision_tick": agent.last_decision_tick,
                "goals": [goal.key for goal in agent.goals],
                "plan_goal": agent.plan.goal_key if agent.plan else None,
            }
            for agent in selected
        ],
    }


@router.get("/autonomy/agents/{agent_id}")
def get_autonomous_agent(agent_id: str, engine: EngineDependency) -> dict[str, object]:
    payload = agent_snapshot(engine.world, agent_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="autonomous agent not found")
    return payload


@router.get("/autonomy/reviews")
def get_human_review_queue(engine: EngineDependency) -> dict[str, object]:
    payload = autonomous_world_snapshot(engine.world)
    return {
        "pending": payload["pending_human_reviews"],
        "items": payload["pending_reviews"],
    }


@router.post("/autonomy/reviews/{review_id}")
def resolve_human_review(
    review_id: str,
    engine: EngineDependency,
    decision: ApprovalStatus = Query(...),  # noqa: B008
    note: str = Query(""),  # noqa: B008
) -> dict[str, object]:
    if review_id not in engine.world.autonomous_world.pending_reviews:
        raise HTTPException(status_code=404, detail="review not found")
    try:
        review = AutonomousAgentService().resolve_review(
            state=engine.world.autonomous_world,
            review_id=review_id,
            decision=decision,
            note=note,
            society=engine.world.autonomous_society,
            civilization=engine.world.civilization,
            tick=engine.world.tick,
            events=engine.world.events,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": review.id,
        "status": review.status.value,
        "agent_id": review.agent_id,
        "intent": review.intent.value,
        "resolved_tick": review.resolved_tick,
    }


@router.get("/civilization")
def get_living_civilization(engine: EngineDependency) -> dict[str, object]:
    return civilization_snapshot(engine.world)


@router.get("/history")
def get_world_history(
    engine: EngineDependency,
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, object]:
    records = engine.world.civilization.history.records[-limit:]
    return {
        "total": len(engine.world.civilization.history.records),
        "items": [
            {
                "sequence": record.sequence,
                "tick": record.tick,
                "year": record.year,
                "month": record.month,
                "category": record.category,
                "title": record.title,
                "summary": record.summary,
                "causes": record.causes,
                "effects": record.effects,
                "significance": round(record.significance, 3),
            }
            for record in records
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


@router.get("/evolution")
def get_evolution(engine: EngineDependency) -> dict[str, object]:
    return evolution_snapshot(engine.world)


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
