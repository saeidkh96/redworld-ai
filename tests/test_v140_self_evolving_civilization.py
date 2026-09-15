from decimal import Decimal

from redworld.domains.agents import AutonomousAgentService
from redworld.domains.life.progression import CitizenLifeProfile
from redworld.domains.self_evolving import SelfEvolvingCivilizationService
from redworld.simulation.factory import create_world


def setup_world():
    world = create_world(population=120, seed=1400)
    service = SelfEvolvingCivilizationService()
    service.bootstrap(world)
    return service, world


def test_v131_life_continuity_tracks_every_citizen_and_generations():
    service, world = setup_world()
    assert len(world.self_evolving.minds) == len(world.citizens)
    assert sum(world.self_evolving.generations.values()) == len(world.citizens)
    service.yearly(world)
    assert world.self_evolving.knowledge_transfers > 0


def test_v132_mind_changes_autonomous_goal_priority():
    _, world = setup_world()
    citizen = next(iter(world.citizens.values()))
    mind = world.self_evolving.minds[str(citizen.id)]
    mind.goal = "community"
    agent_service = AutonomousAgentService()
    agent_service.bootstrap(
        state=world.autonomous_world,
        citizens=list(world.citizens.values()),
        businesses=list(world.businesses.values()),
        society=world.autonomous_society,
        tick=world.tick,
        events=world.events,
    )
    agent = world.autonomous_world.agents[str(citizen.id)]
    agent_service._refresh_citizen_goals(
        agent, citizen, world.life_profiles.get(str(citizen.id)), 1, mind
    )
    belonging = next(goal for goal in agent.goals if goal.key == "belonging")
    assert belonging.priority >= 0.48


def test_v133_social_dynamics_mutate_real_social_graph():
    service, world = setup_world()
    before = len(world.society.relationships)
    service.daily(world)
    assert world.self_evolving.social_ties
    assert len(world.society.relationships) >= before
    assert any(rel.kind.value == "friend" for rel in world.society.relationships.values())


def test_v134_market_signals_change_real_business_prices():
    service, world = setup_world()
    before = {key: business.unit_price.amount for key, business in world.businesses.items()}
    world.self_evolving.markets["essentials"].price = 1.3
    world.self_evolving.markets["housing"].price = 1.3
    world.self_evolving.markets["services"].price = 1.3
    world.self_evolving.markets["industry"].price = 1.3
    service._apply_market_to_businesses(world)
    assert any(
        business.unit_price.amount != before[key] for key, business in world.businesses.items()
    )


def test_v135_institutional_feedback_changes_real_society():
    service, world = setup_world()
    world.self_evolving.public_sentiment = 0.2
    before = world.autonomous_society.institutional_trust
    service._apply_institutional_feedback(world)
    assert world.autonomous_society.institutional_trust != before
    assert world.self_evolving.institutional_updates == len(world.autonomous_society.institutions)


def test_v136_city_expansion_creates_real_geography_location():
    service, world = setup_world()
    before = len(world.geography.locations)
    assert service._expand_real_city(world) is True
    assert len(world.geography.locations) == before + 1
    assert any(
        location.id.startswith("adaptive-") for location in world.geography.locations.values()
    )


def test_v137_generational_transfer_reaches_life_profile():
    service, world = setup_world()
    citizen_id = sorted(world.self_evolving.minds)[0]
    world.life_profiles[citizen_id] = CitizenLifeProfile()
    profile = world.life_profiles[citizen_id]
    before = profile.education
    service.yearly(world)
    assert world.self_evolving.knowledge_transfers > 0
    assert profile.education >= before


def test_v138_causal_history_records_real_chain():
    service, world = setup_world()
    service.record(world, "density", "expansion", 0.8)
    record = world.self_evolving.history[-1]
    assert record.cause == "density"
    assert record.effect == "expansion"
    assert world.self_evolving.causal_links == 1


def test_v139_emergent_event_mutates_world_and_is_idempotent():
    service, world = setup_world()
    for market in world.self_evolving.markets.values():
        market.price = 1.3
    before = next(iter(world.citizens.values())).consumption_budget.amount
    event_count = len(world.self_evolving.emergent_events)
    service.monthly(world)
    assert len(world.self_evolving.emergent_events) > event_count
    assert next(iter(world.citizens.values())).consumption_budget.amount <= before
    first_count = len(world.self_evolving.emergent_events)
    service.monthly(world)
    assert len(world.self_evolving.emergent_events) == first_count


def test_v140_feedback_mutates_real_world_and_preserves_review_authority():
    service, world = setup_world()
    world.self_evolving.housing_pressure = 0.9
    before = world.autonomous_society.collective_agency
    service._adapt_world(world, 0.7)
    snapshot = service.snapshot(world)
    assert world.autonomous_society.collective_agency > before
    assert snapshot["version"] == "1.4.0"
    assert snapshot["human_review_authority_preserved"] is True
    assert all(b.unit_price.amount > Decimal("0") for b in world.businesses.values())
