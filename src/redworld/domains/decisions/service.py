from __future__ import annotations

from redworld.domain.entities.citizen import Citizen
from redworld.domains.actions.models import ActionProposal, ActionType


class DecisionService:
    """Deterministic utility-style policy for thousands of citizens."""

    def choose(
        self,
        *,
        citizen: Citizen,
        minute_of_day: int,
        market_location_id: str | None,
        park_location_id: str | None,
        hospital_location_id: str | None,
        preferred_intent: str | None = None,
    ) -> ActionProposal:
        needs = citizen.needs
        schedule = citizen.schedule

        if needs.health >= 0.72 and hospital_location_id is not None:
            return ActionProposal(ActionType.HEALTHCARE, hospital_location_id, "health")
        if minute_of_day >= schedule.sleep_minute or minute_of_day < schedule.wake_minute:
            return ActionProposal(ActionType.SLEEP, citizen.home_location_id, "night")
        if minute_of_day >= schedule.work_end_minute and citizen.home_location_id is not None:
            if citizen.current_location_id != citizen.home_location_id:
                return ActionProposal(ActionType.GO_HOME, citizen.home_location_id, "day complete")
            if needs.hunger >= 0.72:
                return ActionProposal(ActionType.EAT, citizen.home_location_id, "dinner at home")
            return ActionProposal(ActionType.IDLE, citizen.home_location_id, "home evening")
        if needs.hunger >= 0.72 and market_location_id is not None:
            return ActionProposal(ActionType.EAT, market_location_id, "hunger")
        if preferred_intent == "seek_healthcare" and hospital_location_id is not None:
            return ActionProposal(
                ActionType.HEALTHCARE, hospital_location_id, "autonomous plan: healthcare"
            )
        if preferred_intent in {"socialize", "collaborate", "peaceful_protest"}:
            if park_location_id is not None:
                return ActionProposal(
                    ActionType.SOCIALIZE,
                    park_location_id,
                    "autonomous plan: social connection",
                )
        if preferred_intent == "rest" and citizen.home_location_id is not None:
            return ActionProposal(
                ActionType.RELAX,
                citizen.home_location_id,
                "autonomous plan: rest",
            )
        if preferred_intent in {"earn_income", "change_job"}:
            if citizen.employed and citizen.work_location_id is not None:
                return ActionProposal(
                    ActionType.WORK, citizen.work_location_id, "autonomous plan: career"
                )
        if (
            citizen.employed
            and citizen.work_location_id is not None
            and schedule.is_work_time(minute_of_day)
        ):
            return ActionProposal(ActionType.WORK, citizen.work_location_id, "schedule")
        if needs.social >= 0.72 and park_location_id is not None:
            return ActionProposal(ActionType.SOCIALIZE, park_location_id, "social")
        if needs.energy >= 0.78 and citizen.home_location_id is not None:
            return ActionProposal(ActionType.RELAX, citizen.home_location_id, "fatigue")
        return ActionProposal(ActionType.IDLE, citizen.current_location_id, "no urgent need")
