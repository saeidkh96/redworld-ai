from uuid import UUID

from redworld.domain.value_objects.money import Money
from redworld.domains.accounting.ledger import Ledger
from redworld.domains.accounting.models import JournalEntry, Posting, PostingSide


class AccountingService:
    def __init__(self, ledger: Ledger) -> None:
        self.ledger = ledger

    def transfer(
        self,
        *,
        tick: int,
        source_account_id: UUID,
        destination_account_id: UUID,
        amount: Money,
        description: str,
    ) -> JournalEntry:
        if amount.amount <= 0:
            raise ValueError("transfer amount must be positive")
        if self.ledger.balance(source_account_id).amount < amount.amount:
            raise ValueError("insufficient funds")
        entry = JournalEntry(
            tick=tick,
            description=description,
            postings=(
                Posting(destination_account_id, PostingSide.DEBIT, amount),
                Posting(source_account_id, PostingSide.CREDIT, amount),
            ),
        )
        self.ledger.post(entry)
        return entry
