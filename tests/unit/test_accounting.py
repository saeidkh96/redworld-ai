import pytest

from redworld.domain.value_objects.money import Money
from redworld.domains.accounting import (
    Account,
    AccountType,
    JournalEntry,
    Ledger,
    Posting,
    PostingSide,
)


def test_unbalanced_journal_entry_is_rejected() -> None:
    ledger = Ledger()
    cash = ledger.add_account(Account("cash", AccountType.ASSET))
    equity = ledger.add_account(Account("equity", AccountType.EQUITY))
    with pytest.raises(ValueError, match="not balanced"):
        JournalEntry(
            0,
            "bad",
            (
                Posting(cash, PostingSide.DEBIT, Money.of(10)),
                Posting(equity, PostingSide.CREDIT, Money.of(9)),
            ),
        )


def test_ledger_tracks_balances_and_trial_balance() -> None:
    ledger = Ledger()
    cash = ledger.add_account(Account("cash", AccountType.ASSET))
    equity = ledger.add_account(Account("equity", AccountType.EQUITY))
    ledger.post(
        JournalEntry(
            0,
            "seed",
            (
                Posting(cash, PostingSide.DEBIT, Money.of(100)),
                Posting(equity, PostingSide.CREDIT, Money.of(100)),
            ),
        )
    )
    assert ledger.balance(cash) == Money.of(100)
    assert ledger.balance(equity) == Money.of(100)
    assert ledger.trial_balance_delta() == Money.zero()
