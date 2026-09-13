from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from redworld.domain.value_objects.money import Money


class AccountType(StrEnum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class PostingSide(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


@dataclass(frozen=True, slots=True)
class Account:
    name: str
    account_type: AccountType
    owner_id: UUID | None = None
    currency: str = "RWC"
    id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True, slots=True)
class Posting:
    account_id: UUID
    side: PostingSide
    amount: Money
    memo: str = ""

    def __post_init__(self) -> None:
        if self.amount.amount <= 0:
            raise ValueError("posting amount must be positive")


@dataclass(frozen=True, slots=True)
class JournalEntry:
    tick: int
    description: str
    postings: tuple[Posting, ...]
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if len(self.postings) < 2:
            raise ValueError("journal entry requires at least two postings")
        currencies = {posting.amount.currency for posting in self.postings}
        if len(currencies) != 1:
            raise ValueError("journal entry postings must use one currency")
        debit_total = sum(
            posting.amount.amount for posting in self.postings if posting.side is PostingSide.DEBIT
        )
        credit_total = sum(
            posting.amount.amount for posting in self.postings if posting.side is PostingSide.CREDIT
        )
        if debit_total != credit_total:
            raise ValueError("journal entry is not balanced")
