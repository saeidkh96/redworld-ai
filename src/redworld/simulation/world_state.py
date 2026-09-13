from dataclasses import dataclass, field
from uuid import UUID

from redworld.core.events import EventStore
from redworld.domain.entities import Bank, Business, Citizen, Economy, Government
from redworld.domains.accounting.ledger import Ledger
from redworld.domains.autonomy import SocietyState
from redworld.domains.banking.service import BankingService
from redworld.domains.civilization import CivilizationState
from redworld.domains.commerce import CommerceService
from redworld.domains.employment.service import EmploymentService
from redworld.domains.geography import GeographyService
from redworld.domains.households import Household
from redworld.domains.life.progression import CitizenLifeProfile
from redworld.domains.memory import MemoryService
from redworld.domains.planning import PlanningService
from redworld.domains.society import SocialGraph
from redworld.domains.time import WorldClock


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
    seed: int = 20260912
    geography: GeographyService = field(default_factory=GeographyService)
    clock: WorldClock = field(default_factory=WorldClock)
    households: dict[str, Household] = field(default_factory=dict)
    society: SocialGraph = field(default_factory=SocialGraph)
    commerce: CommerceService = field(default_factory=CommerceService)
    memories: MemoryService = field(default_factory=MemoryService)
    planning: PlanningService = field(default_factory=PlanningService)
    life_profiles: dict[str, CitizenLifeProfile] = field(default_factory=dict)
    autonomous_society: SocietyState = field(default_factory=SocietyState)
    civilization: CivilizationState = field(default_factory=CivilizationState)
