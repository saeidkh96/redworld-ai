from redworld.core.events import DomainEvent, EventStore
from redworld.domain.entities import Bank, Business, Citizen, Economy, Government
from redworld.domain.value_objects.money import Money
from redworld.domains.accounting import (
    Account,
    AccountType,
    JournalEntry,
    Ledger,
    Posting,
    PostingSide,
)
from redworld.domains.economy import refresh_economy_metrics
from redworld.domains.employment import EmploymentService
from redworld.simulation.world_state import WorldState


def _add_actor_accounts(world: WorldState) -> None:
    for citizen in world.citizens.values():
        citizen.cash_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: cash", AccountType.ASSET, citizen.id)
        )
        citizen.income_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: income", AccountType.REVENUE, citizen.id)
        )
        citizen.consumption_expense_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: consumption", AccountType.EXPENSE, citizen.id)
        )
        citizen.tax_expense_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: tax", AccountType.EXPENSE, citizen.id)
        )

    for business in world.businesses.values():
        business.cash_account_id = world.ledger.add_account(
            Account(f"{business.name}: cash", AccountType.ASSET, business.id)
        )
        business.revenue_account_id = world.ledger.add_account(
            Account(f"{business.name}: revenue", AccountType.REVENUE, business.id)
        )
        business.wage_expense_account_id = world.ledger.add_account(
            Account(f"{business.name}: wages", AccountType.EXPENSE, business.id)
        )
        business.tax_expense_account_id = world.ledger.add_account(
            Account(f"{business.name}: tax", AccountType.EXPENSE, business.id)
        )

    for bank in world.banks.values():
        bank.cash_account_id = world.ledger.add_account(
            Account(f"{bank.name}: reserves", AccountType.ASSET, bank.id)
        )
        bank.interest_revenue_account_id = world.ledger.add_account(
            Account(f"{bank.name}: interest revenue", AccountType.REVENUE, bank.id)
        )

    if world.government is not None:
        gov = world.government
        gov.treasury_account_id = world.ledger.add_account(
            Account(f"{gov.name}: treasury", AccountType.ASSET, gov.id)
        )
        gov.tax_revenue_account_id = world.ledger.add_account(
            Account(f"{gov.name}: tax revenue", AccountType.REVENUE, gov.id)
        )
        gov.spending_expense_account_id = world.ledger.add_account(
            Account(f"{gov.name}: public spending", AccountType.EXPENSE, gov.id)
        )


def _seed_money(world: WorldState) -> None:
    issuance = world.ledger.add_account(Account("World issuance", AccountType.EQUITY))
    world.system_issuance_account_id = issuance
    postings: list[Posting] = []
    allocations: list[tuple[object, Money]] = []
    for citizen in world.citizens.values():
        allocations.append((citizen.cash_account_id, Money.of("40.00")))
    for business in world.businesses.values():
        allocations.append((business.cash_account_id, Money.of("300.00")))
    for bank in world.banks.values():
        allocations.append((bank.cash_account_id, Money.of("500.00")))
    if world.government is not None:
        allocations.append((world.government.treasury_account_id, Money.of("200.00")))

    total = Money.zero()
    for account_id, amount in allocations:
        from uuid import UUID

        if not isinstance(account_id, UUID):
            raise ValueError("seed account was not initialized")
        postings.append(Posting(account_id, PostingSide.DEBIT, amount))
        total = total + amount
    postings.append(Posting(issuance, PostingSide.CREDIT, total))
    world.ledger.post(JournalEntry(0, "Genesis monetary allocation", tuple(postings)))


def create_genesis_world(name: str = "Genesis") -> WorldState:
    citizens = [Citizen(name=f"Citizen {index}") for index in range(1, 5)]
    bank = Bank(name="Genesis Bank")
    government = Government(name="Genesis Government")
    business = Business(name="Genesis Foods", owner_id=citizens[0].id)

    world = WorldState(
        name=name,
        citizens={str(citizen.id): citizen for citizen in citizens},
        businesses={str(business.id): business},
        banks={str(bank.id): bank},
        government=government,
        economy=Economy(),
        ledger=Ledger(),
        employment=EmploymentService(),
        events=EventStore(),
    )
    _add_actor_accounts(world)
    _seed_money(world)

    for citizen in citizens:
        if citizen.cash_account_id is None:
            raise ValueError("citizen cash account missing")
        world.banking.register_deposit_account(
            bank=bank,
            owner_id=citizen.id,
            ledger_account_id=citizen.cash_account_id,
        )
    if business.cash_account_id is None:
        raise ValueError("business cash account missing")
    world.banking.register_deposit_account(
        bank=bank,
        owner_id=business.id,
        ledger_account_id=business.cash_account_id,
    )

    for citizen in citizens[:3]:
        world.employment.hire(
            tick=0,
            citizen=citizen,
            business=business,
            wage=business.wage_offer,
            events=world.events,
        )
    return world


def create_world(*, population: int = 1500, seed: int = 20260912) -> WorldState:
    """Create the spatial Genesis City while preserving the v0.1.0 genesis factory."""
    from random import Random

    from redworld.domains.geography import (
        City,
        Coordinate,
        District,
        Location,
        LocationType,
        Region,
    )

    if population < 1:
        raise ValueError("population must be positive")

    rng = Random(seed)
    citizens = [Citizen(name=f"Citizen {index:04d}") for index in range(1, population + 1)]
    owner = citizens[0]
    bank = Bank(name="Genesis Bank", location_id="central-bank")
    government = Government(name="Genesis Government", location_id="city-hall")

    businesses = [
        Business(name=f"Genesis Business {index:02d}", owner_id=owner.id) for index in range(1, 41)
    ]
    world = WorldState(
        name="RedWorld — Genesis City",
        citizens={str(c.id): c for c in citizens},
        businesses={str(b.id): b for b in businesses},
        banks={str(bank.id): bank},
        government=government,
        seed=seed,
    )

    geo = world.geography
    geo.add_region(Region("genesis-region", "Genesis Region"))
    geo.add_city(City("genesis-city", "genesis-region", "Genesis City"))
    specs = [
        ("res-north", "North Residential", 18.0, 22.0, "residential"),
        ("university", "University Quarter", 49.0, 17.0, "education"),
        ("riverside", "Riverside", 79.0, 22.0, "mixed"),
        ("central", "Central District", 48.0, 46.0, "central"),
        ("commercial", "Commercial District", 78.0, 48.0, "commercial"),
        ("res-south", "South Residential", 18.0, 72.0, "residential"),
        ("industrial", "Industrial District", 50.0, 75.0, "industrial"),
        ("civic", "Civic District", 79.0, 75.0, "civic"),
    ]
    hubs: dict[str, str] = {}
    street_nodes: dict[str, list[str]] = {}
    for district_id, name, x, y, kind in specs:
        geo.add_district(
            District(
                district_id,
                "genesis-city",
                name,
                Coordinate(x, y),
                24,
                24,
                kind,
            )
        )
        hub_id = f"hub-{district_id}"
        hubs[district_id] = hub_id
        geo.add_location(
            Location(
                hub_id,
                district_id,
                f"{name} Hub",
                LocationType.STATION,
                Coordinate(x, y),
                2000,
            )
        )
        # A small street grid gives every district real traversable streets.
        # Buildings attach to these nodes instead of connecting straight to the hub.
        street_specs = [
            ("north", x, y - 7.0),
            ("east", x + 7.0, y),
            ("south", x, y + 7.0),
            ("west", x - 7.0, y),
        ]
        street_nodes[district_id] = []
        for street_name, street_x, street_y in street_specs:
            street_id = f"street-{district_id}-{street_name}"
            street_nodes[district_id].append(street_id)
            geo.add_location(
                Location(
                    street_id,
                    district_id,
                    f"{name} {street_name.title()} Street",
                    LocationType.STATION,
                    Coordinate(street_x, street_y),
                    2000,
                )
            )
            geo.connect(hub_id, street_id, 2)
        ring = street_nodes[district_id]
        for source, target in zip(ring, ring[1:] + ring[:1], strict=True):
            geo.connect(source, target, 2)

    links = [
        ("res-north", "central"),
        ("university", "central"),
        ("riverside", "commercial"),
        ("central", "commercial"),
        ("central", "res-south"),
        ("central", "industrial"),
        ("commercial", "civic"),
        ("industrial", "civic"),
        ("res-south", "industrial"),
        ("university", "riverside"),
    ]
    for source, target in links:
        geo.connect(hubs[source], hubs[target])

    def nearest_street(district_id: str, x: float, y: float) -> str:
        return min(
            street_nodes[district_id],
            key=lambda node_id: (
                (geo.locations[node_id].coordinate.x - x) ** 2
                + (geo.locations[node_id].coordinate.y - y) ** 2
            ),
        )

    homes: list[Location] = []
    residential_centers = [
        ("res-north", 18.0, 22.0),
        ("res-south", 18.0, 72.0),
        ("riverside", 79.0, 22.0),
    ]
    for district_id, center_x, center_y in residential_centers:
        for index in range(18):
            home_index = len(homes) + 1
            x = center_x + ((index % 6) - 2.5) * 2.6
            y = center_y + ((index // 6) - 1) * 3.2
            location = Location(
                f"home-{home_index:03d}",
                district_id,
                f"Residence {home_index:03d}",
                LocationType.HOME,
                Coordinate(x, y),
                40,
            )
            geo.add_location(location)
            geo.connect(
                location.id,
                nearest_street(district_id, x, y),
                2 + index % 3,
            )
            homes.append(location)

    workplaces: list[Location] = []
    workplace_groups = [
        ("central", 48.0, 46.0, 14),
        ("commercial", 78.0, 48.0, 12),
        ("industrial", 50.0, 75.0, 10),
        ("university", 49.0, 17.0, 4),
    ]
    for district_id, center_x, center_y, count in workplace_groups:
        for index in range(count):
            work_index = len(workplaces) + 1
            x = center_x + ((index % 5) - 2) * 2.8
            y = center_y + ((index // 5) - 1) * 3.2
            location = Location(
                f"work-{work_index:03d}",
                district_id,
                f"Enterprise {work_index:02d}",
                LocationType.WORKPLACE,
                Coordinate(x, y),
                80,
            )
            geo.add_location(location)
            geo.connect(
                location.id,
                nearest_street(district_id, x, y),
                2 + index % 3,
            )
            workplaces.append(location)
            businesses[work_index - 1].location_id = location.id

    extras = [
        Location(
            "city-hall",
            "civic",
            "Genesis City Hall",
            LocationType.GOVERNMENT,
            Coordinate(78, 73),
            600,
        ),
        Location(
            "central-bank",
            "central",
            "Genesis Bank",
            LocationType.BANK,
            Coordinate(45, 44),
            400,
        ),
        Location(
            "university-main",
            "university",
            "Genesis University",
            LocationType.UNIVERSITY,
            Coordinate(49, 14),
            1500,
        ),
        Location(
            "central-park",
            "central",
            "Central Park",
            LocationType.PARK,
            Coordinate(54, 52),
            1200,
        ),
        Location(
            "city-hospital",
            "civic",
            "Genesis Hospital",
            LocationType.HOSPITAL,
            Coordinate(82, 76),
            700,
        ),
        Location(
            "market-square",
            "commercial",
            "Market Square",
            LocationType.SHOP,
            Coordinate(75, 46),
            800,
        ),
    ]
    for location in extras:
        geo.add_location(location)
        geo.connect(
            location.id,
            nearest_street(
                location.district_id,
                location.coordinate.x,
                location.coordinate.y,
            ),
            3,
        )

    _add_actor_accounts(world)
    _seed_money(world)

    from redworld.domains.households import HouseholdService
    from redworld.domains.life.models import CitizenNeeds, CitizenTraits, DailySchedule
    from redworld.domains.society import SocietyService

    occupations = [
        "Engineer",
        "Teacher",
        "Nurse",
        "Retail Worker",
        "Technician",
        "Analyst",
        "Designer",
        "Operator",
    ]
    for index, citizen in enumerate(citizens):
        citizen.age = rng.randint(18, 75)
        citizen.occupation = rng.choice(occupations)
        citizen.home_location_id = homes[index % len(homes)].id
        citizen.current_location_id = citizen.home_location_id
        citizen.needs = CitizenNeeds(
            hunger=rng.uniform(0.10, 0.45),
            energy=rng.uniform(0.08, 0.35),
            social=rng.uniform(0.10, 0.55),
            health=rng.uniform(0.01, 0.18),
            safety=rng.uniform(0.01, 0.12),
        )
        citizen.traits = CitizenTraits(
            sociability=rng.random(),
            discipline=rng.random(),
            frugality=rng.random(),
            resilience=0.35 + rng.random() * 0.65,
        )
        stagger = int(citizen.id.int % 45)
        citizen.schedule = DailySchedule(
            wake_minute=6 * 60 + stagger // 3,
            work_start_minute=8 * 60 + stagger,
            work_end_minute=16 * 60 + stagger // 3,
            sleep_minute=22 * 60 + 15 + stagger // 2,
        )
        should_employ = rng.random() < 0.82
        if should_employ:
            workplace = workplaces[index % len(workplaces)]
            citizen.work_location_id = workplace.id
            business = businesses[index % len(businesses)]
            business.wage_offer = Money.of("4.00")
            world.employment.hire(
                tick=0,
                citizen=citizen,
                business=business,
                wage=business.wage_offer,
                events=world.events,
            )
        world.planning.seed_for(citizen)

    from redworld.domains.society import Relationship, RelationshipType

    world.households = HouseholdService().create_households(citizens)
    SocietyService().seed(citizens, world.society)
    for household in world.households.values():
        members = household.member_ids
        for source_id, target_id in zip(members, members[1:], strict=False):
            world.society.add(Relationship(source_id, target_id, RelationshipType.HOUSEHOLD, 0.85))
    refresh_economy_metrics(world)
    world.events.append(
        DomainEvent(
            "WorldCreated",
            0,
            {"population": population, "seed": seed, "city": "Genesis City"},
        )
    )
    return world
