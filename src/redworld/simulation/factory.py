from redworld.domain.entities import Bank, Citizen, Economy, Government
from redworld.simulation.world_state import WorldState


def create_genesis_world(name: str = "Genesis") -> WorldState:
    citizen = Citizen(name="Genesis Citizen")
    bank = Bank(name="Genesis Bank")
    government = Government(name="Genesis Government")

    return WorldState(
        name=name,
        citizens={str(citizen.id): citizen},
        banks={str(bank.id): bank},
        government=government,
        economy=Economy(),
    )
