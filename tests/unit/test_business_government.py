from redworld.domains.businesses import business_profit
from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_genesis_world


def test_business_profit_and_business_tax_are_recorded() -> None:
    world = create_genesis_world()
    business = next(iter(world.businesses.values()))
    SimulationEngine(world).step()
    profit = business_profit(business=business, ledger=world.ledger)
    assert profit.currency == "RWC"
    assert business.tax_expense_account_id is not None
    assert world.ledger.balance(business.tax_expense_account_id).amount > 0
    assert any(event.event_type == "BusinessTaxCollected" for event in world.events.events)


def test_citizen_basic_consumption_need_is_served_by_purchase() -> None:
    world = create_genesis_world()
    SimulationEngine(world).step()
    assert all(citizen.last_consumption_tick == 1 for citizen in world.citizens.values())
