from redworld.domain.value_objects.money import Money
from redworld.simulation.factory import create_genesis_world


def test_genesis_world_has_employment_and_business_accounts() -> None:
    world = create_genesis_world()
    assert len(world.employment.active_contracts()) == 3
    business = next(iter(world.businesses.values()))
    assert len(business.employee_ids) == 3
    assert business.cash_account_id is not None
    assert world.ledger.balance(business.cash_account_id) == Money.of(300)
