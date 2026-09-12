from dataclasses import dataclass, field
from uuid import UUID

from redworld.core.events import EventStore
from redworld.domain.entities import Bank, Business, Citizen, Economy, Government
from redworld.domains.accounting.ledger import Ledger
from redworld.domains.banking.service import BankingService
from redworld.domains.employment.service import EmploymentService


@dataclass(slots=True)
class WorldState:
    name: str
    tick: int = 0
    citizens: dict[str, Citizen] = field(default_factory=dict)
    businesses: dict[str, Business] = field(default_factory=dict)
    banks: dict[str, Bank] = field(default_factory=dict)
    government: Government | None = None
    economy: Economy = field(default_factory=Economy)
    ledger: Ledger = field(default_factory=Ledger)
    employment: EmploymentService = field(default_factory=EmploymentService)
    banking: BankingService = field(default_factory=BankingService)
    events: EventStore = field(default_factory=EventStore)
    system_issuance_account_id: UUID | None = None
