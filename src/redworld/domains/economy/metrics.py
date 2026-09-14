from decimal import Decimal

from redworld.domain.entities.economy import Economy
from redworld.domain.value_objects.money import Money
from redworld.simulation.world_state import WorldState


def refresh_economy_metrics(world: WorldState) -> Economy:
    currency = world.ledger.currency
    citizen_cash = Decimal("0")
    business_cash = Decimal("0")
    bank_cash = Decimal("0")

    for citizen in world.citizens.values():
        if citizen.cash_account_id is not None:
            citizen_cash += world.ledger.balance_amount(citizen.cash_account_id)

    for business in world.businesses.values():
        if business.cash_account_id is not None:
            business_cash += world.ledger.balance_amount(business.cash_account_id)

    for bank in world.banks.values():
        if bank.cash_account_id is not None:
            bank_cash += world.ledger.balance_amount(bank.cash_account_id)

    government_cash = Decimal("0")
    if world.government is not None and world.government.treasury_account_id is not None:
        government_cash = world.ledger.balance_amount(world.government.treasury_account_id)

    employed = sum(1 for citizen in world.citizens.values() if citizen.employed)
    population = len(world.citizens)

    world.economy.total_household_cash = Money(citizen_cash, currency)
    world.economy.total_business_cash = Money(business_cash, currency)
    world.economy.total_bank_cash = Money(bank_cash, currency)
    world.economy.government_cash = Money(government_cash, currency)
    world.economy.unemployment_rate = (
        0.0 if population == 0 else (population - employed) / population
    )
    return world.economy
