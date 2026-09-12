
from redworld.core.events import DomainEvent, EventStore
from redworld.domain.entities.citizen import Citizen
from redworld.domain.entities.government import Government
from redworld.domain.value_objects.money import Money
from redworld.domains.accounting.ledger import Ledger
from redworld.domains.accounting.models import JournalEntry, Posting, PostingSide


class GovernmentService:
    def collect_income_tax(
        self,
        *,
        tick: int,
        citizen: Citizen,
        government: Government,
        taxable_income: Money,
        ledger: Ledger,
        events: EventStore,
    ) -> Money:
        if citizen.cash_account_id is None or citizen.tax_expense_account_id is None:
            raise ValueError("citizen accounts are not initialized")
        if government.treasury_account_id is None or government.tax_revenue_account_id is None:
            raise ValueError("government accounts are not initialized")
        raw = Money(taxable_income.amount * government.income_tax_rate, ledger.currency)
        available = ledger.balance(citizen.cash_account_id)
        tax = raw.min(available)
        if tax.amount <= 0:
            return Money.zero(ledger.currency)
        ledger.post(JournalEntry(
            tick=tick,
            description=f"Income tax: {citizen.name}",
            postings=(
                Posting(government.treasury_account_id, PostingSide.DEBIT, tax),
                Posting(government.tax_revenue_account_id, PostingSide.CREDIT, tax),
                Posting(citizen.tax_expense_account_id, PostingSide.DEBIT, tax),
                Posting(citizen.cash_account_id, PostingSide.CREDIT, tax),
            ),
        ))
        events.append(
            DomainEvent(
                "TaxCollected",
                tick,
                {"citizen_id": str(citizen.id), "amount": str(tax.amount)},
            )
        )
        return tax


    def collect_business_tax(
        self,
        *,
        tick: int,
        business: object,
        government: Government,
        taxable_revenue: Money,
        ledger: Ledger,
        events: EventStore,
    ) -> Money:
        from redworld.domain.entities.business import Business

        if not isinstance(business, Business):
            raise TypeError("invalid business")
        if business.cash_account_id is None or business.tax_expense_account_id is None:
            raise ValueError("business accounts are not initialized")
        if government.treasury_account_id is None or government.tax_revenue_account_id is None:
            raise ValueError("government accounts are not initialized")
        raw = Money(taxable_revenue.amount * government.business_tax_rate, ledger.currency)
        available = ledger.balance(business.cash_account_id)
        tax = raw.min(available)
        if tax.amount <= 0:
            return Money.zero(ledger.currency)
        ledger.post(
            JournalEntry(
                tick=tick,
                description=f"Business tax: {business.name}",
                postings=(
                    Posting(government.treasury_account_id, PostingSide.DEBIT, tax),
                    Posting(government.tax_revenue_account_id, PostingSide.CREDIT, tax),
                    Posting(business.tax_expense_account_id, PostingSide.DEBIT, tax),
                    Posting(business.cash_account_id, PostingSide.CREDIT, tax),
                ),
            )
        )
        events.append(
            DomainEvent(
                "BusinessTaxCollected",
                tick,
                {"business_id": str(business.id), "amount": str(tax.amount)},
            )
        )
        return tax

    def welfare(
        self,
        *,
        tick: int,
        citizen: Citizen,
        government: Government,
        ledger: Ledger,
        events: EventStore,
    ) -> Money:
        if citizen.employed:
            return Money.zero(ledger.currency)
        if citizen.cash_account_id is None or citizen.income_account_id is None:
            raise ValueError("citizen accounts are not initialized")
        if government.treasury_account_id is None or government.spending_expense_account_id is None:
            raise ValueError("government accounts are not initialized")
        available = ledger.balance(government.treasury_account_id)
        payment = government.welfare_payment.min(available)
        if payment.amount <= 0:
            return Money.zero(ledger.currency)
        ledger.post(JournalEntry(
            tick=tick,
            description=f"Welfare: {citizen.name}",
            postings=(
                Posting(government.spending_expense_account_id, PostingSide.DEBIT, payment),
                Posting(government.treasury_account_id, PostingSide.CREDIT, payment),
                Posting(citizen.cash_account_id, PostingSide.DEBIT, payment),
                Posting(citizen.income_account_id, PostingSide.CREDIT, payment),
            ),
        ))
        events.append(
            DomainEvent(
                "WelfarePaid",
                tick,
                {"citizen_id": str(citizen.id), "amount": str(payment.amount)},
            )
        )
        return payment
