from redworld.domain.entities.economy import Economy
from redworld.domain.value_objects.money import Money
from redworld.simulation.world_state import WorldState


def refresh_economy_metrics(world: WorldState) -> Economy:
    currency = world.ledger.currency
    citizen_cash = Money.zero(currency)
    business_cash = Money.zero(currency)
    bank_cash = Money.zero(currency)

    for citizen in world.citizens.values():
        if citizen.cash_account_id is not None:
            citizen_cash = citizen_cash + world.ledger.balance(citizen.cash_account_id)
    for business in world.businesses.values():
        if business.cash_account_id is not None:
            business_cash = business_cash + world.ledger.balance(business.cash_account_id)
    for bank in world.banks.values():
        if bank.cash_account_id is not None:
            bank_cash = bank_cash + world.ledger.balance(bank.cash_account_id)

    government_cash = Money.zero(currency)
    if world.government is not None and world.government.treasury_account_id is not None:
        government_cash = world.ledger.balance(world.government.treasury_account_id)

    employed = sum(1 for citizen in world.citizens.values() if citizen.employed)
    population = len(world.citizens)
    world.economy.total_household_cash = citizen_cash
    world.economy.total_business_cash = business_cash
    world.economy.total_bank_cash = bank_cash
    world.economy.government_cash = government_cash
    world.economy.unemployment_rate = (
        0.0 if population == 0 else (population - employed) / population
    )
    return world.economy
