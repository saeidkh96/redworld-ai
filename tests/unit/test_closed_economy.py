from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_genesis_world


def test_closed_economy_tick_moves_money_and_stays_balanced() -> None:
    world = create_genesis_world()
    engine = SimulationEngine(world)
    before_entries = world.ledger.audit_entry_count()
    engine.step()
    assert world.tick == 1
    assert world.ledger.audit_entry_count() > before_entries
    assert world.ledger.trial_balance_delta().is_zero()
    assert world.economy.total_wages.amount > 0
    assert world.economy.total_consumption.amount > 0
    assert world.economy.total_taxes.amount > 0
    assert world.economy.unemployment_rate == 0.25


def test_closed_economy_can_run_many_ticks() -> None:
    world = create_genesis_world()
    SimulationEngine(world).run(5)
    assert world.tick == 5
    assert world.ledger.trial_balance_delta().is_zero()
    assert len(world.events.events) > 5
