from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import UUID

from redworld.core.events import DomainEvent, EventStore
from redworld.domain.entities.bank import Bank
from redworld.domain.value_objects.money import Money
from redworld.domains.accounting.ledger import Ledger
from redworld.domains.accounting.models import JournalEntry, Posting, PostingSide
from redworld.domains.banking.models import DepositAccount, Loan


@dataclass(frozen=True, slots=True)
class BankBalanceSheet:
    cash_reserves: Money
    loans_outstanding: Money
    registered_deposits: Money


@dataclass(slots=True)
class BankingService:
    loans: dict[UUID, Loan] = field(default_factory=dict)
    deposit_accounts: dict[UUID, DepositAccount] = field(default_factory=dict)

    def register_deposit_account(
        self, *, bank: Bank, owner_id: UUID, ledger_account_id: UUID
    ) -> DepositAccount:
        account = DepositAccount(bank.id, owner_id, ledger_account_id)
        self.deposit_accounts[account.id] = account
        return account

    def issue_loan(
        self,
        *,
        tick: int,
        bank: Bank,
        borrower_id: UUID,
        borrower_cash_account_id: UUID,
        amount: Money,
        ledger: Ledger,
        events: EventStore,
        annual_interest_rate: Decimal = Decimal("0.05"),
        term_ticks: int = 12,
    ) -> Loan:
        if bank.cash_account_id is None:
            raise ValueError("bank cash account is not initialized")
        available = ledger.balance(bank.cash_account_id)
        if amount.amount <= 0:
            raise ValueError("loan amount must be positive")
        if term_ticks <= 0:
            raise ValueError("loan term must be positive")
        if amount.amount > available.amount * bank.max_loan_to_reserves_ratio:
            raise ValueError("loan exceeds bank credit constraint")
        ledger.post(
            JournalEntry(
                tick=tick,
                description="Loan disbursement",
                postings=(
                    Posting(borrower_cash_account_id, PostingSide.DEBIT, amount),
                    Posting(bank.cash_account_id, PostingSide.CREDIT, amount),
                ),
            )
        )
        loan = Loan(
            bank.id,
            borrower_id,
            amount,
            annual_interest_rate,
            amount,
            term_ticks=term_ticks,
        )
        self.loans[loan.id] = loan
        events.append(
            DomainEvent(
                "LoanIssued",
                tick,
                {
                    "loan_id": str(loan.id),
                    "borrower_id": str(borrower_id),
                    "amount": str(amount.amount),
                },
            )
        )
        return loan

    def accrue_interest(self, *, tick: int, loan: Loan, events: EventStore) -> Money:
        if not loan.active:
            return Money.zero(loan.remaining_principal.currency)
        # One simulation tick is treated as one month in the v0.1 reference economy.
        monthly_rate = loan.annual_interest_rate / Decimal("12")
        interest_amount = (loan.remaining_principal.amount * monthly_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
        interest = Money(interest_amount, loan.remaining_principal.currency)
        loan.remaining_principal = loan.remaining_principal + interest
        loan.ticks_elapsed += 1
        events.append(
            DomainEvent(
                "LoanInterestAccrued",
                tick,
                {"loan_id": str(loan.id), "amount": str(interest.amount)},
            )
        )
        return interest

    def repay(
        self,
        *,
        tick: int,
        loan: Loan,
        borrower_cash_account_id: UUID,
        bank: Bank,
        amount: Money,
        ledger: Ledger,
        events: EventStore,
    ) -> Money:
        if bank.cash_account_id is None:
            raise ValueError("bank cash account is not initialized")
        if not loan.active:
            return Money.zero(ledger.currency)
        payment = amount.min(loan.remaining_principal)
        if ledger.balance(borrower_cash_account_id).amount < payment.amount:
            raise ValueError("insufficient funds for loan repayment")
        ledger.post(
            JournalEntry(
                tick=tick,
                description="Loan repayment",
                postings=(
                    Posting(bank.cash_account_id, PostingSide.DEBIT, payment),
                    Posting(borrower_cash_account_id, PostingSide.CREDIT, payment),
                ),
            )
        )
        loan.remaining_principal = loan.remaining_principal - payment
        if loan.remaining_principal.is_zero():
            loan.active = False
        events.append(
            DomainEvent(
                "LoanRepaid",
                tick,
                {"loan_id": str(loan.id), "amount": str(payment.amount)},
            )
        )
        return payment

    def balance_sheet(self, *, bank: Bank, ledger: Ledger) -> BankBalanceSheet:
        if bank.cash_account_id is None:
            raise ValueError("bank cash account is not initialized")
        loans = Money.zero(ledger.currency)
        for loan in self.loans.values():
            if loan.bank_id == bank.id and loan.active:
                loans = loans + loan.remaining_principal
        deposits = Money.zero(ledger.currency)
        for deposit in self.deposit_accounts.values():
            if deposit.bank_id == bank.id:
                deposits = deposits + ledger.balance(deposit.ledger_account_id)
        return BankBalanceSheet(
            cash_reserves=ledger.balance(bank.cash_account_id),
            loans_outstanding=loans,
            registered_deposits=deposits,
        )
