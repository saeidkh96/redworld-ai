from decimal import Decimal

from redworld.simulation import SimulationEngine
from redworld.simulation.factory import create_world


def test_ledger_stays_globally_balanced() -> None:
    world = create_world(population=120)
    assert world.ledger.total_balance() == Decimal("0.00")
    SimulationEngine(world).run(20)
    assert world.ledger.total_balance() == Decimal("0.00")
    assert world.ledger.audit_entry_count() > 0
