from __future__ import annotations

from redworld.core.events import DomainEvent
from redworld.domain.entities import Citizen
from redworld.domains.actions.models import ActionProposal, ActionType
from redworld.domains.life.service import LifeService
from redworld.domains.memory import MemoryRecord
from redworld.domains.mobility import MobilityService
from redworld.domains.society import SocietyService
from redworld.simulation.world_state import WorldState


class ActionService:
    """Validates and executes citizen actions through world-owned services."""

    def start(self, *, world: WorldState, citizen: Citizen, proposal: ActionProposal) -> None:
        target = proposal.target_location_id
        if target is not None and target not in world.geography.locations:
            return
        citizen.current_action = proposal.action.value
        citizen.action_target_location_id = target
        citizen.last_action_tick = world.tick
        world.events.append(
            DomainEvent(
                "CitizenActionStarted",
                world.tick,
                {
                    "citizen_id": str(citizen.id),
                    "action": proposal.action.value,
                    "target_location_id": target,
                    "reason": proposal.reason,
                },
            )
        )
        if (
            target is not None
            and citizen.current_location_id is not None
            and citizen.current_location_id != target
        ):
            MobilityService().request_move(
                tick=world.tick,
                citizen=citizen,
                destination_id=target,
                geography=world.geography,
                events=world.events,
            )
            return
        self.complete_if_ready(world=world, citizen=citizen)

    def complete_if_ready(self, *, world: WorldState, citizen: Citizen) -> None:
        target = citizen.action_target_location_id
        if citizen.is_moving:
            return
        if target is not None and citizen.current_location_id != target:
            return
        try:
            action = ActionType(citizen.current_action)
        except ValueError:
            action = ActionType.IDLE
        life = LifeService()
        completed = False
        if action == ActionType.EAT:
            amount = world.commerce.purchase_food(
                tick=world.tick,
                citizen=citizen,
                businesses=list(world.businesses.values()),
                ledger=world.ledger,
                events=world.events,
            )
            if amount.amount > 0:
                life.satisfy_food(citizen)
                world.economy.total_consumption = world.economy.total_consumption + amount
                world.economy.gross_output = world.economy.gross_output + amount
                world.memories.remember(
                    citizen.id,
                    MemoryRecord(world.tick, "purchase", "Bought food in Genesis City", 0.45),
                )
            completed = True
        elif action == ActionType.SHOP:
            amount = world.commerce.purchase_food(
                tick=world.tick,
                citizen=citizen,
                businesses=list(world.businesses.values()),
                ledger=world.ledger,
                events=world.events,
            )
            if amount.amount > 0:
                life.satisfy_food(citizen)
                world.economy.total_consumption = world.economy.total_consumption + amount
                world.economy.gross_output = world.economy.gross_output + amount
            completed = True
        elif action == ActionType.SLEEP:
            life.satisfy_sleep(citizen)
            completed = True
        elif action == ActionType.RELAX:
            citizen.needs.energy = max(0.0, citizen.needs.energy - 0.08)
            completed = True
        elif action == ActionType.SOCIALIZE:
            life.satisfy_social(citizen)
            SocietyService().reinforce_interaction(citizen=citizen, graph=world.society)
            world.memories.remember(
                citizen.id,
                MemoryRecord(world.tick, "social", "Spent time with people in the city", 0.40),
            )
            completed = True
        elif action == ActionType.HEALTHCARE:
            life.receive_healthcare(citizen)
            world.memories.remember(
                citizen.id, MemoryRecord(world.tick, "health", "Visited Genesis Hospital", 0.70)
            )
            completed = True
        elif action in {ActionType.WORK, ActionType.GO_HOME, ActionType.IDLE}:
            completed = True
        if completed:
            world.events.append(
                DomainEvent(
                    "CitizenActionCompleted",
                    world.tick,
                    {"citizen_id": str(citizen.id), "action": action.value},
                )
            )
            citizen.current_action = "idle"
            citizen.action_target_location_id = None
