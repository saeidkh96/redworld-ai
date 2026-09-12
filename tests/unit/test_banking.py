from decimal import Decimal

from redworld.domain.value_objects.money import Money
from redworld.simulation.factory import create_genesis_world


def test_genesis_registers_bank_deposit_accounts() -> None:
    world = create_genesis_world()
    assert len(world.banking.deposit_accounts) == 5
    bank = next(iter(world.banks.values()))
    sheet = world.banking.balance_sheet(bank=bank, ledger=world.ledger)
    assert sheet.registered_deposits == Money.of(460)
    assert sheet.cash_reserves == Money.of(500)


def test_bank_can_issue_accrue_and_repay_reserve_backed_loan() -> None:
    world = create_genesis_world()
    bank = next(iter(world.banks.values()))
    citizen = next(iter(world.citizens.values()))
    assert citizen.cash_account_id is not None
    loan = world.banking.issue_loan(
        tick=0,
        bank=bank,
        borrower_id=citizen.id,
        borrower_cash_account_id=citizen.cash_account_id,
        amount=Money.of(50),
        ledger=world.ledger,
        events=world.events,
        annual_interest_rate=Decimal("0.12"),
        term_ticks=10,
    )
    interest = world.banking.accrue_interest(tick=1, loan=loan, events=world.events)
    assert interest == Money.of("0.50")
    assert loan.remaining_principal == Money.of("50.50")
    assert loan.scheduled_principal_payment().amount > 0
    paid = world.banking.repay(
        tick=1,
        loan=loan,
        borrower_cash_account_id=citizen.cash_account_id,
        bank=bank,
        amount=Money.of(20),
        ledger=world.ledger,
        events=world.events,
    )
    assert paid == Money.of(20)
    assert loan.remaining_principal == Money.of("30.50")
    sheet = world.banking.balance_sheet(bank=bank, ledger=world.ledger)
    assert sheet.loans_outstanding == Money.of("30.50")
