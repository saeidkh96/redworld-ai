from dataclasses import dataclass, field
from uuid import UUID

from redworld.core.events import DomainEvent, EventStore
from redworld.domain.entities.business import Business
from redworld.domain.entities.citizen import Citizen
from redworld.domain.value_objects.money import Money
from redworld.domains.accounting.models import JournalEntry, Posting, PostingSide
from redworld.domains.employment.models import EmploymentContract


@dataclass(slots=True)
class EmploymentService:
    contracts: dict[UUID, EmploymentContract] = field(default_factory=dict)

    def hire(
        self,
        *,
        tick: int,
        citizen: Citizen,
        business: Business,
        wage: Money,
        events: EventStore,
    ) -> EmploymentContract:
        if citizen.employed:
            raise ValueError("citizen is already employed")
        contract = EmploymentContract(citizen.id, business.id, wage)
        self.contracts[contract.id] = contract
        citizen.employed = True
        citizen.employer_id = business.id
        citizen.wage_per_tick = wage
        if citizen.id not in business.employee_ids:
            business.employee_ids.append(citizen.id)
        events.append(
            DomainEvent(
                "CitizenHired",
                tick,
                {"citizen_id": str(citizen.id), "business_id": str(business.id)},
            )
        )
        return contract

    def active_contracts(self) -> list[EmploymentContract]:
        return [contract for contract in self.contracts.values() if contract.active]

    def payroll_entry(
        self,
        *,
        tick: int,
        contract: EmploymentContract,
        citizen: Citizen,
        business: Business,
    ) -> JournalEntry:
        if citizen.cash_account_id is None:
            raise ValueError("citizen cash account is not initialized")
        if citizen.income_account_id is None:
            raise ValueError("citizen income account is not initialized")
        if business.cash_account_id is None:
            raise ValueError("business cash account is not initialized")
        if business.wage_expense_account_id is None:
            raise ValueError("business wage expense account is not initialized")
        amount = contract.wage_per_tick
        return JournalEntry(
            tick=tick,
            description=f"Payroll: {business.name} -> {citizen.name}",
            postings=(
                Posting(business.wage_expense_account_id, PostingSide.DEBIT, amount),
                Posting(business.cash_account_id, PostingSide.CREDIT, amount),
                Posting(citizen.cash_account_id, PostingSide.DEBIT, amount),
                Posting(citizen.income_account_id, PostingSide.CREDIT, amount),
            ),
        )
