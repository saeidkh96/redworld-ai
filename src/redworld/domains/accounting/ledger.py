from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from redworld.domain.value_objects.money import Money
from redworld.domains.accounting.models import (
    Account,
    AccountType,
    JournalEntry,
    PostingSide,
)


@dataclass(slots=True)
class Ledger:
    currency: str = "RWC"
    accounts: dict[UUID, Account] = field(default_factory=dict)
    entries: list[JournalEntry] = field(default_factory=list)

    _debit_totals: dict[UUID, Decimal] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _credit_totals: dict[UUID, Decimal] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _total_debits: Decimal = field(
        default=Decimal("0"),
        init=False,
        repr=False,
    )
    _total_credits: Decimal = field(
        default=Decimal("0"),
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Build balance indexes for any entries supplied at construction time."""
        for account_id in self.accounts:
            self._debit_totals[account_id] = Decimal("0")
            self._credit_totals[account_id] = Decimal("0")

        for entry in self.entries:
            self._index_entry(entry)

    def add_account(self, account: Account) -> UUID:
        if account.id in self.accounts:
            raise ValueError(f"account already exists: {account.id}")
        if account.currency != self.currency:
            raise ValueError("account currency does not match ledger")

        self.accounts[account.id] = account
        self._debit_totals.setdefault(account.id, Decimal("0"))
        self._credit_totals.setdefault(account.id, Decimal("0"))
        return account.id

    def post(self, entry: JournalEntry) -> None:
        for posting in entry.postings:
            account = self.accounts.get(posting.account_id)
            if account is None:
                raise KeyError(f"unknown account: {posting.account_id}")
            if posting.amount.currency != account.currency:
                raise ValueError("posting currency does not match account")

        self.entries.append(entry)
        self._index_entry(entry)

    def _index_entry(self, entry: JournalEntry) -> None:
        for posting in entry.postings:
            amount = posting.amount.amount
            account_id = posting.account_id

            if posting.side is PostingSide.DEBIT:
                self._debit_totals[account_id] = (
                    self._debit_totals.get(account_id, Decimal("0")) + amount
                )
                self._total_debits += amount
            else:
                self._credit_totals[account_id] = (
                    self._credit_totals.get(account_id, Decimal("0")) + amount
                )
                self._total_credits += amount

    def balance_amount(self, account_id: UUID) -> Decimal:
        account = self.accounts[account_id]
        debit = self._debit_totals.get(account_id, Decimal("0"))
        credit = self._credit_totals.get(account_id, Decimal("0"))

        normal_debit = account.account_type in {
            AccountType.ASSET,
            AccountType.EXPENSE,
        }
        return debit - credit if normal_debit else credit - debit

    def balance(self, account_id: UUID) -> Money:
        account = self.accounts[account_id]
        return Money(self.balance_amount(account_id), account.currency)

    def trial_balance_delta(self) -> Money:
        return Money(self._total_debits - self._total_credits, self.currency)

    def total_balance(self) -> Decimal:
        """Compatibility helper for world-level balance invariants."""
        return self.trial_balance_delta().amount

    def audit_entry_count(self) -> int:
        return len(self.entries)
