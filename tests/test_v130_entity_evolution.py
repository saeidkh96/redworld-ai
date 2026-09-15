from redworld.domains.civilization.models import DevelopmentRecord, PolicyRecord
from redworld.domains.evolution.service import WorldEvolutionService
from redworld.simulation.factory import create_world
from redworld.simulation.snapshot import evolution_snapshot, world_summary


def test_v130_world_reports_final_version_and_evolution_state() -> None:
    world = create_world(population=80, seed=130)
    assert world_summary(world)["version"] == "1.4.0"
    snapshot = evolution_snapshot(world)
    assert snapshot["entity_population"] == 80
    assert snapshot["businesses_created"] == 0


def test_v125_births_create_real_citizens_and_household_membership() -> None:
    world = create_world(population=100, seed=125)
    world.clock.day = 361
    before = len(world.citizens)
    WorldEvolutionService().yearly_life_events(world)
    assert len(world.citizens) > before
    assert world.evolution.births_realized > 0
    assert any(event.event_type == "CitizenBorn" for event in world.events.events)


def test_v126_confident_economy_creates_real_business() -> None:
    world = create_world(population=80, seed=126)
    world.clock.day = 391
    world.civilization.economy.confidence_index = 0.8
    before = len(world.businesses)
    WorldEvolutionService().monthly_economy(world)
    assert len(world.businesses) == before + 1
    assert world.evolution.businesses_created == 1


def test_v127_policy_changes_real_government_parameter() -> None:
    world = create_world(population=80, seed=127)
    world.clock.day = 421
    assert world.government is not None
    before = world.government.income_tax_rate
    world.civilization.governance.policies.append(
        PolicyRecord(2, 3, "Revenue Tax Reform", "tax", 0.7)
    )
    WorldEvolutionService().monthly_economy(world)
    assert world.government.income_tax_rate > before
    assert world.evolution.policies_applied == 1


def test_v128_city_development_creates_real_location() -> None:
    world = create_world(population=80, seed=128)
    world.clock.day = 451
    world.civilization.city.developments.append(
        DevelopmentRecord(2, 4, "central", "Community Center", 0.2)
    )
    before = len(world.geography.locations)
    WorldEvolutionService().monthly_economy(world)
    assert len(world.geography.locations) == before + 1
    assert world.evolution.city_projects_realized == 1


def test_v130_monthly_mutations_are_idempotent() -> None:
    world = create_world(population=80, seed=1300)
    world.clock.day = 721
    world.civilization.economy.confidence_index = 0.8
    service = WorldEvolutionService()
    service.monthly_economy(world)
    count = len(world.businesses)
    service.monthly_economy(world)
    assert len(world.businesses) == count


def test_v125_deaths_remove_real_citizens() -> None:
    world = create_world(population=100, seed=1251)
    world.clock.day = 361
    world.civilization.demography.fertility_rate = 0.0
    world.civilization.demography.mortality_rate = 0.05

    before = len(world.citizens)
    WorldEvolutionService().yearly_life_events(world)

    assert len(world.citizens) < before
    assert world.evolution.deaths_realized > 0
    assert any(event.event_type == "CitizenDied" for event in world.events.events)


def test_v125_partnerships_mutate_real_households() -> None:
    world = create_world(population=100, seed=1252)
    service = WorldEvolutionService()

    before_marriages = world.evolution.marriages_realized
    service._realize_partnerships(world, marriages=10, separations=0)

    assert world.evolution.marriages_realized > before_marriages
    assert any(event.event_type == "HouseholdPartnershipFormed" for event in world.events.events)

    before_households = len(world.households)
    service._realize_partnerships(world, marriages=0, separations=2)

    assert world.evolution.separations_realized > 0
    assert len(world.households) > before_households
    assert any(event.event_type == "HouseholdSeparated" for event in world.events.events)


def test_v126_economy_hires_and_lays_off_real_citizens() -> None:
    world = create_world(population=500, seed=1261)
    service = WorldEvolutionService()

    world.clock.day = 391
    world.civilization.economy.confidence_index = 0.9
    service.monthly_economy(world)

    assert world.evolution.hires_realized > 0
    assert any(citizen.employed for citizen in world.citizens.values())

    world.clock.day += 31
    world.civilization.economy.confidence_index = 0.1
    service.monthly_economy(world)

    assert world.evolution.layoffs_realized > 0
    assert any(event.event_type == "CitizenLaidOff" for event in world.events.events)


def test_v129_crisis_mutates_real_world_entities() -> None:
    from redworld.domains.civilization.models import CrisisKind, CrisisRecord

    world = create_world(population=100, seed=129)
    world.clock.day = 481

    business = next(iter(world.businesses.values()))
    before = business.productivity_per_employee

    world.civilization.crises.active.append(
        CrisisRecord(
            CrisisKind.RECESSION,
            world.clock.year,
            world.clock.month,
            0.8,
            0.8,
        )
    )

    WorldEvolutionService().monthly_economy(world)

    assert business.productivity_per_employee < before
    assert world.evolution.crises_triggered == 1
    assert any(event.event_type == "WorldCrisisTriggered" for event in world.events.events)


def test_v129_positive_migration_creates_real_residents() -> None:
    world = create_world(population=100, seed=1291)
    world.clock.day = 511
    world.civilization.city.migration_balance = 3

    before = len(world.citizens)
    WorldEvolutionService().monthly_economy(world)

    assert len(world.citizens) == before + 3
    assert world.evolution.migrations_realized == 3
    event_types = [event.event_type for event in world.events.events]
    assert event_types.count("CitizenMigratedIn") == 3
    assert "CitizenBorn" not in event_types


def test_v129_negative_migration_removes_real_residents() -> None:
    world = create_world(population=100, seed=1292)
    world.clock.day = 541
    world.civilization.city.migration_balance = -2

    before = len(world.citizens)
    WorldEvolutionService().monthly_economy(world)

    assert len(world.citizens) == before - 2
    assert world.evolution.migrations_realized == -2
    event_types = [event.event_type for event in world.events.events]
    assert event_types.count("CitizenMigratedOut") == 2
    assert "CitizenDied" not in event_types
