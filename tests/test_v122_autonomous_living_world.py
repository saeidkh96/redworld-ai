from fastapi.testclient import TestClient

from redworld.api.dependencies import get_engine
from redworld.api.main import app
from redworld.domains.agents import (
    ActionReview,
    AgentIntent,
    AgentKind,
    ApprovalStatus,
    AutonomousAgentService,
    RiskLevel,
)
from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_world


def test_autonomous_world_bootstraps_all_actor_types_at_tick_zero() -> None:
    engine = SimulationEngine(create_world())
    state = engine.world.autonomous_world
    assert state.initialized is True
    assert len(state.agents) == 1544
    kinds = {agent.kind for agent in state.agents.values()}
    assert kinds == {AgentKind.CITIZEN, AgentKind.BUSINESS, AgentKind.INSTITUTION}
    assert engine.world.tick == 0


def test_citizens_observe_plan_act_and_learn_without_commands() -> None:
    engine = SimulationEngine(create_world())
    engine.run(16)
    citizens = [
        agent
        for agent in engine.world.autonomous_world.agents.values()
        if agent.kind == AgentKind.CITIZEN and agent.decisions > 0
    ]
    assert citizens
    assert any(agent.beliefs for agent in citizens)
    assert any(agent.goals for agent in citizens)
    assert any(agent.plan is not None for agent in citizens)
    assert any(agent.memories for agent in citizens)
    assert engine.world.autonomous_world.autonomous_actions > 0


def test_businesses_institutions_and_interactions_evolve_autonomously() -> None:
    engine = SimulationEngine(create_world())
    engine.run(32)
    state = engine.world.autonomous_world
    business_decisions = [
        agent.decisions for agent in state.agents.values() if agent.kind == AgentKind.BUSINESS
    ]
    institution_decisions = [
        agent.decisions for agent in state.agents.values() if agent.kind == AgentKind.INSTITUTION
    ]
    assert min(business_decisions) >= 2
    assert min(institution_decisions) >= 1
    assert state.interactions
    assert state.emergence_index > 0.0
    assert state.learning_index > 0.0


def test_high_impact_intent_requires_human_review() -> None:
    engine = SimulationEngine(create_world())
    level, score, impact = AutonomousAgentService().assess_risk(
        AgentIntent.HIGH_IMPACT_DISRUPTION,
        engine.world.civilization,
        engine.world.autonomous_society,
    )
    assert level == RiskLevel.HIGH
    assert score >= 0.8
    assert "public safety" in impact


def test_human_can_approve_reject_or_modify_queued_action() -> None:
    engine = SimulationEngine(create_world())
    state = engine.world.autonomous_world
    citizen_agent = next(
        agent for agent in state.agents.values() if agent.kind == AgentKind.CITIZEN
    )
    review = ActionReview(
        id="review-test",
        agent_id=citizen_agent.agent_id,
        agent_name=citizen_agent.name,
        agent_kind=citizen_agent.kind,
        intent=AgentIntent.HIGH_IMPACT_DISRUPTION,
        reason="test review",
        risk_level=RiskLevel.HIGH,
        risk_score=0.91,
        expected_impact="bounded simulation impact",
        created_tick=engine.world.tick,
    )
    state.pending_reviews[review.id] = review
    resolved = AutonomousAgentService().resolve_review(
        state=state,
        review_id=review.id,
        decision=ApprovalStatus.MODIFIED,
        note="allow bounded version only",
        society=engine.world.autonomous_society,
        civilization=engine.world.civilization,
        tick=engine.world.tick,
        events=engine.world.events,
    )
    assert resolved.status == ApprovalStatus.MODIFIED
    assert "review-test" not in state.pending_reviews
    assert state.approved_actions == 1


def test_autonomy_api_exposes_agents_and_human_review_queue() -> None:
    get_engine.cache_clear()
    client = TestClient(app)
    summary = client.get("/api/v1/world").json()
    assert summary["version"] == "2.0.0"
    assert summary["autonomous_world"]["agents"] == 1544

    autonomy = client.get("/api/v1/world/autonomy")
    assert autonomy.status_code == 200
    assert autonomy.json()["initialized"] is True

    agents = client.get("/api/v1/world/autonomy/agents?kind=citizen&limit=5")
    assert agents.status_code == 200
    payload = agents.json()
    assert payload["total"] == 1500
    assert len(payload["items"]) == 5

    agent_id = payload["items"][0]["agent_id"]
    detail = client.get(f"/api/v1/world/autonomy/agents/{agent_id}")
    assert detail.status_code == 200
    assert detail.json()["kind"] == "citizen"

    reviews = client.get("/api/v1/world/autonomy/reviews")
    assert reviews.status_code == 200
    assert "items" in reviews.json()
