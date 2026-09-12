from redworld.core.events import EventStore
from redworld.domain.entities import Bank, Business, Citizen, Economy, Government
from redworld.domain.value_objects.money import Money
from redworld.domains.accounting import (
    Account,
    AccountType,
    JournalEntry,
    Ledger,
    Posting,
    PostingSide,
)
from redworld.domains.employment import EmploymentService
from redworld.simulation.world_state import WorldState


def _add_actor_accounts(world: WorldState) -> None:
    for citizen in world.citizens.values():
        citizen.cash_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: cash", AccountType.ASSET, citizen.id)
        )
        citizen.income_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: income", AccountType.REVENUE, citizen.id)
        )
        citizen.consumption_expense_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: consumption", AccountType.EXPENSE, citizen.id)
        )
        citizen.tax_expense_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: tax", AccountType.EXPENSE, citizen.id)
        )

    for business in world.businesses.values():
        business.cash_account_id = world.ledger.add_account(
            Account(f"{business.name}: cash", AccountType.ASSET, business.id)
        )
        business.revenue_account_id = world.ledger.add_account(
            Account(f"{business.name}: revenue", AccountType.REVENUE, business.id)
        )
        business.wage_expense_account_id = world.ledger.add_account(
            Account(f"{business.name}: wages", AccountType.EXPENSE, business.id)
        )
        business.tax_expense_account_id = world.ledger.add_account(
            Account(f"{business.name}: tax", AccountType.EXPENSE, business.id)
        )

    for bank in world.banks.values():
        bank.cash_account_id = world.ledger.add_account(
            Account(f"{bank.name}: reserves", AccountType.ASSET, bank.id)
        )
        bank.interest_revenue_account_id = world.ledger.add_account(
            Account(f"{bank.name}: interest revenue", AccountType.REVENUE, bank.id)
        )

    if world.government is not None:
        gov = world.government
        gov.treasury_account_id = world.ledger.add_account(
            Account(f"{gov.name}: treasury", AccountType.ASSET, gov.id)
        )
        gov.tax_revenue_account_id = world.ledger.add_account(
            Account(f"{gov.name}: tax revenue", AccountType.REVENUE, gov.id)
        )
        gov.spending_expense_account_id = world.ledger.add_account(
            Account(f"{gov.name}: public spending", AccountType.EXPENSE, gov.id)
        )


def _seed_money(world: WorldState) -> None:
    issuance = world.ledger.add_account(Account("World issuance", AccountType.EQUITY))
    world.system_issuance_account_id = issuance
    postings: list[Posting] = []
    allocations: list[tuple[object, Money]] = []
    for citizen in world.citizens.values():
        allocations.append((citizen.cash_account_id, Money.of("40.00")))
    for business in world.businesses.values():
        allocations.append((business.cash_account_id, Money.of("300.00")))
    for bank in world.banks.values():
        allocations.append((bank.cash_account_id, Money.of("500.00")))
    if world.government is not None:
        allocations.append((world.government.treasury_account_id, Money.of("200.00")))

    total = Money.zero()
    for account_id, amount in allocations:
        from uuid import UUID

        if not isinstance(account_id, UUID):
            raise ValueError("seed account was not initialized")
        postings.append(Posting(account_id, PostingSide.DEBIT, amount))
        total = total + amount
    postings.append(Posting(issuance, PostingSide.CREDIT, total))
    world.ledger.post(JournalEntry(0, "Genesis monetary allocation", tuple(postings)))


def create_genesis_world(name: str = "Genesis") -> WorldState:
    citizens = [Citizen(name=f"Citizen {index}") for index in range(1, 5)]
    bank = Bank(name="Genesis Bank")
    government = Government(name="Genesis Government")
    business = Business(name="Genesis Foods", owner_id=citizens[0].id)

    world = WorldState(
        name=name,
        citizens={str(citizen.id): citizen for citizen in citizens},
        businesses={str(business.id): business},
        banks={str(bank.id): bank},
        government=government,
        economy=Economy(),
        ledger=Ledger(),
        employment=EmploymentService(),
        events=EventStore(),
    )
    _add_actor_accounts(world)
    _seed_money(world)

    for citizen in citizens:
        if citizen.cash_account_id is None:
            raise ValueError("citizen cash account missing")
        world.banking.register_deposit_account(
            bank=bank,
            owner_id=citizen.id,
            ledger_account_id=citizen.cash_account_id,
        )
    if business.cash_account_id is None:
        raise ValueError("business cash account missing")
    world.banking.register_deposit_account(
        bank=bank,
        owner_id=business.id,
        ledger_account_id=business.cash_account_id,
    )

    for citizen in citizens[:3]:
        world.employment.hire(
            tick=0,
            citizen=citizen,
            business=business,
            wage=business.wage_offer,
            events=world.events,
        )
    return world
