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

    def add_account(self, account: Account) -> UUID:
        if account.id in self.accounts:
            raise ValueError(f"account already exists: {account.id}")
        if account.currency != self.currency:
            raise ValueError("account currency does not match ledger")
        self.accounts[account.id] = account
        return account.id

    def post(self, entry: JournalEntry) -> None:
        for posting in entry.postings:
            account = self.accounts.get(posting.account_id)
            if account is None:
                raise KeyError(f"unknown account: {posting.account_id}")
            if posting.amount.currency != account.currency:
                raise ValueError("posting currency does not match account")
        self.entries.append(entry)

    def balance(self, account_id: UUID) -> Money:
        account = self.accounts[account_id]
        debit = Decimal("0")
        credit = Decimal("0")
        for entry in self.entries:
            for posting in entry.postings:
                if posting.account_id != account_id:
                    continue
                if posting.side is PostingSide.DEBIT:
                    debit += posting.amount.amount
                else:
                    credit += posting.amount.amount
        normal_debit = account.account_type in {AccountType.ASSET, AccountType.EXPENSE}
        amount = debit - credit if normal_debit else credit - debit
        return Money(amount, account.currency)

    def trial_balance_delta(self) -> Money:
        debit = Decimal("0")
        credit = Decimal("0")
        for entry in self.entries:
            for posting in entry.postings:
                if posting.side is PostingSide.DEBIT:
                    debit += posting.amount.amount
                else:
                    credit += posting.amount.amount
        return Money(debit - credit, self.currency)

    def audit_entry_count(self) -> int:
        return len(self.entries)
