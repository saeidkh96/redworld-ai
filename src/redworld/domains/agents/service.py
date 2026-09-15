from __future__ import annotations

from hashlib import sha256

from redworld.core.events import DomainEvent, EventStore
from redworld.domain.entities import Business, Citizen
from redworld.domains.autonomy import SocietyState
from redworld.domains.civilization import CivilizationState
from redworld.domains.life.progression import CitizenLifeProfile
from redworld.domains.self_evolving.models import CitizenMind

from .models import (
    ActionReview,
    AgentGoal,
    AgentIntent,
    AgentInteraction,
    AgentKind,
    AgentMemory,
    AgentPlan,
    AgentState,
    ApprovalStatus,
    AutonomousWorldState,
    Belief,
    PlanStep,
    RiskLevel,
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _noise(key: str, tick: int, span: float = 0.08) -> float:
    digest = sha256(f"{key}:{tick}".encode()).digest()
    unit = int.from_bytes(digest[:4], "big") / 0xFFFFFFFF
    return (unit - 0.5) * 2.0 * span


class AutonomousAgentService:
    """Deterministic autonomous-agent layer with bounded knowledge and human review."""

    def bootstrap(
        self,
        *,
        state: AutonomousWorldState,
        citizens: list[Citizen],
        businesses: list[Business],
        society: SocietyState,
        tick: int,
        events: EventStore,
        minds: dict[str, CitizenMind] | None = None,
    ) -> None:
        if state.initialized:
            self._sync_new_agents(state, citizens, businesses, society)
            return

        self._sync_new_agents(state, citizens, businesses, society)
        state.initialized = True
        events.append(
            DomainEvent(
                "AutonomousWorldInitialized",
                tick,
                {
                    "agents": len(state.agents),
                    "citizens": len(citizens),
                    "businesses": len(businesses),
                    "institutions": len(society.institutions),
                },
            )
        )

    def _sync_new_agents(
        self,
        state: AutonomousWorldState,
        citizens: list[Citizen],
        businesses: list[Business],
        society: SocietyState,
    ) -> None:
        for citizen in citizens:
            key = str(citizen.id)
            if key not in state.agents:
                state.agents[key] = AgentState(
                    agent_id=key,
                    kind=AgentKind.CITIZEN,
                    name=citizen.name,
                    autonomy=0.58 + (citizen.id.int % 29) / 100.0,
                    risk_tolerance=0.12 + (citizen.id.int % 23) / 100.0,
                    learning_rate=0.08 + (citizen.id.int % 11) / 100.0,
                )
        for business in businesses:
            key = str(business.id)
            if key not in state.agents:
                state.agents[key] = AgentState(
                    agent_id=key,
                    kind=AgentKind.BUSINESS,
                    name=business.name,
                    autonomy=0.72,
                    risk_tolerance=0.34,
                    learning_rate=0.10,
                )
        for institution in society.institutions.values():
            key = str(institution.id)
            if key not in state.agents:
                state.agents[key] = AgentState(
                    agent_id=key,
                    kind=AgentKind.INSTITUTION,
                    name=institution.name,
                    autonomy=0.68,
                    risk_tolerance=0.18,
                    learning_rate=0.09,
                )

    def update(
        self,
        *,
        state: AutonomousWorldState,
        citizens: dict[str, Citizen],
        businesses: dict[str, Business],
        profiles: dict[str, CitizenLifeProfile],
        society: SocietyState,
        civilization: CivilizationState,
        tick: int,
        events: EventStore,
        minds: dict[str, CitizenMind] | None = None,
    ) -> None:
        if not state.enabled:
            return

        citizen_list = list(citizens.values())
        business_list = list(businesses.values())
        self.bootstrap(
            state=state,
            citizens=citizen_list,
            businesses=business_list,
            society=society,
            tick=tick,
            events=events,
        )

        # Citizens reason on a staggered cadence so large populations remain inexpensive.
        for citizen in citizen_list:
            if (citizen.id.int + tick) % 8 != 0:
                continue
            agent = state.agents[str(citizen.id)]
            profile = profiles.get(str(citizen.id))
            self._observe_citizen(agent, citizen, profile, society, civilization, tick)
            self._refresh_citizen_goals(
                agent, citizen, profile, tick, None if minds is None else minds.get(str(citizen.id))
            )
            self._ensure_plan(agent, tick, state)
            self._advance_plan(
                state=state,
                agent=agent,
                citizen=citizen,
                profile=profile,
                society=society,
                civilization=civilization,
                tick=tick,
                events=events,
            )

        # Organizations operate at a slower cadence and react to the same world from their own view.
        if tick % 16 == 0:
            for business in business_list:
                self._update_business_agent(
                    state=state,
                    agent=state.agents[str(business.id)],
                    business=business,
                    civilization=civilization,
                    tick=tick,
                    events=events,
                )

        if tick % 32 == 0:
            for institution in society.institutions.values():
                self._update_institution_agent(
                    state=state,
                    agent=state.agents[str(institution.id)],
                    society=society,
                    civilization=civilization,
                    tick=tick,
                    events=events,
                )

        self._agent_interactions(state, tick, events)
        self._update_world_metrics(state, society, civilization, tick)

    def _observe_citizen(
        self,
        agent: AgentState,
        citizen: Citizen,
        profile: CitizenLifeProfile | None,
        society: SocietyState,
        civilization: CivilizationState,
        tick: int,
    ) -> None:
        profile_stress = profile.stress if profile else 0.35
        observations = {
            "personal_health": 1.0 - citizen.needs.health,
            "personal_hunger": citizen.needs.hunger,
            "personal_social_need": citizen.needs.social,
            "job_security": 0.78 if citizen.employed else 0.18,
            "economic_pressure": _clamp(
                civilization.economy.poverty_rate
                + abs(civilization.economy.inflation_rate) * 1.7
                + (0.2 if not citizen.employed else 0.0)
            ),
            "public_mood": society.public_mood,
            "institutional_trust": society.institutional_trust,
            "protest_pressure": civilization.social.protest_pressure,
            "personal_stress": profile_stress,
        }
        for topic, truth in observations.items():
            perceived = _clamp(truth + _noise(f"{agent.agent_id}:{topic}", tick))
            agent.beliefs[topic] = Belief(
                topic=topic,
                value=perceived,
                confidence=0.62 + min(0.30, agent.autonomy * 0.25),
                learned_tick=tick,
            )
        agent.last_observed_tick = tick

    def _refresh_citizen_goals(
        self,
        agent: AgentState,
        citizen: Citizen,
        profile: CitizenLifeProfile | None,
        tick: int,
        mind: CitizenMind | None = None,
    ) -> None:
        stress = profile.stress if profile else 0.35
        candidates = [
            AgentGoal("health", 0.35 + citizen.needs.health * 0.65, 0.85, created_tick=tick),
            AgentGoal(
                "financial_security",
                0.48 + (0.35 if not citizen.employed else 0.0),
                0.80,
                created_tick=tick,
            ),
            AgentGoal("belonging", 0.30 + citizen.needs.social * 0.55, 0.75, created_tick=tick),
            AgentGoal("growth", 0.32 + stress * 0.15, 0.72, created_tick=tick),
        ]
        if profile is not None and profile.skill < 0.60:
            candidates[-1].priority += 0.20
        if mind is not None:
            preferred = {
                "stability": "financial_security",
                "prosperity": "financial_security",
                "community": "belonging",
                "learning": "growth",
                "mobility": "growth",
            }.get(mind.goal)
            for candidate in candidates:
                if candidate.key == preferred:
                    candidate.priority += 0.18 + mind.knowledge * 0.04
        candidates.sort(key=lambda goal: goal.priority, reverse=True)
        agent.goals = candidates[:3]

    def _ensure_plan(self, agent: AgentState, tick: int, state: AutonomousWorldState) -> None:
        if not agent.goals:
            return
        top = agent.goals[0]
        if agent.plan is not None and not agent.plan.complete and agent.plan.goal_key == top.key:
            return
        if agent.plan is not None:
            state.replans += 1
        agent.plan = self._make_plan(top.key, tick)

    def _make_plan(self, goal_key: str, tick: int) -> AgentPlan:
        plans: dict[str, list[PlanStep]] = {
            "health": [
                PlanStep(AgentIntent.SEEK_HEALTHCARE, "protect health"),
                PlanStep(AgentIntent.REST, "recover after care"),
            ],
            "financial_security": [
                PlanStep(AgentIntent.EARN_INCOME, "improve financial security"),
                PlanStep(AgentIntent.SAVE, "build a buffer"),
            ],
            "belonging": [
                PlanStep(AgentIntent.SOCIALIZE, "strengthen relationships"),
                PlanStep(AgentIntent.COLLABORATE, "take part in community life"),
            ],
            "growth": [
                PlanStep(AgentIntent.LEARN, "improve skills"),
                PlanStep(AgentIntent.CHANGE_JOB, "seek a better opportunity"),
            ],
        }
        return AgentPlan(goal_key=goal_key, steps=plans.get(goal_key, []), created_tick=tick)

    def _advance_plan(
        self,
        *,
        state: AutonomousWorldState,
        agent: AgentState,
        citizen: Citizen,
        profile: CitizenLifeProfile | None,
        society: SocietyState,
        civilization: CivilizationState,
        tick: int,
        events: EventStore,
    ) -> None:
        plan = agent.plan
        if plan is None or plan.complete:
            return
        step = plan.steps[plan.current_step]
        intent = step.intent

        # High social pressure may cause a small subset to independently consider protest.
        pressure = agent.beliefs.get("protest_pressure")
        trust = agent.beliefs.get("institutional_trust")
        if pressure and trust and pressure.value > 0.62 and trust.value < 0.38:
            if (citizen.id.int + tick) % 97 == 0:
                intent = AgentIntent.PEACEFUL_PROTEST
            if pressure.value > 0.86 and agent.risk_tolerance > 0.28:
                if (citizen.id.int + tick) % 389 == 0:
                    intent = AgentIntent.HIGH_IMPACT_DISRUPTION

        risk_level, risk_score, impact = self.assess_risk(intent, civilization, society)
        state.total_decisions += 1
        agent.decisions += 1
        agent.last_decision_tick = tick
        if risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            self._queue_review(
                state=state,
                agent=agent,
                intent=intent,
                reason=step.reason,
                risk_level=risk_level,
                risk_score=risk_score,
                expected_impact=impact,
                tick=tick,
                events=events,
            )
            agent.failed_actions += 1
            return

        outcome = self._execute_citizen_intent(
            intent=intent,
            citizen=citizen,
            profile=profile,
            society=society,
            civilization=civilization,
        )
        step.completed = True
        plan.current_step += 1
        agent.successful_actions += 1
        state.autonomous_actions += 1
        self._learn(agent, intent, outcome, tick)
        events.append(
            DomainEvent(
                "AutonomousAgentActed",
                tick,
                {
                    "agent_id": agent.agent_id,
                    "agent_kind": agent.kind.value,
                    "intent": intent.value,
                    "outcome": round(outcome, 3),
                },
            )
        )

    def assess_risk(
        self,
        intent: AgentIntent,
        civilization: CivilizationState,
        society: SocietyState,
    ) -> tuple[RiskLevel, float, str]:
        if intent == AgentIntent.HIGH_IMPACT_DISRUPTION:
            score = _clamp(0.82 + civilization.social.conflict * 0.15)
            return RiskLevel.HIGH, score, "could disrupt shared city systems or public safety"
        if intent == AgentIntent.PEACEFUL_PROTEST:
            score = _clamp(0.32 + society.polarization * 0.20)
            return RiskLevel.MEDIUM, score, "may increase short-term civic pressure"
        if intent == AgentIntent.ADJUST_PRICES:
            score = _clamp(0.18 + abs(civilization.economy.inflation_rate))
            return RiskLevel.LOW, score, "localized economic effect"
        return RiskLevel.LOW, 0.08, "limited reversible effect"

    def _queue_review(
        self,
        *,
        state: AutonomousWorldState,
        agent: AgentState,
        intent: AgentIntent,
        reason: str,
        risk_level: RiskLevel,
        risk_score: float,
        expected_impact: str,
        tick: int,
        events: EventStore,
    ) -> None:
        # Avoid flooding the queue with duplicate unresolved proposals from one agent.
        if any(review.agent_id == agent.agent_id for review in state.pending_reviews.values()):
            return
        review_id = f"review-{tick}-{agent.agent_id[:8]}"
        review = ActionReview(
            id=review_id,
            agent_id=agent.agent_id,
            agent_name=agent.name,
            agent_kind=agent.kind,
            intent=intent,
            reason=reason,
            risk_level=risk_level,
            risk_score=risk_score,
            expected_impact=expected_impact,
            created_tick=tick,
        )
        state.pending_reviews[review_id] = review
        state.blocked_actions += 1
        events.append(
            DomainEvent(
                "HumanApprovalRequired",
                tick,
                {
                    "review_id": review_id,
                    "agent_id": agent.agent_id,
                    "intent": intent.value,
                    "risk": risk_level.value,
                },
            )
        )

    def resolve_review(
        self,
        *,
        state: AutonomousWorldState,
        review_id: str,
        decision: ApprovalStatus,
        note: str,
        society: SocietyState,
        civilization: CivilizationState,
        tick: int,
        events: EventStore,
    ) -> ActionReview:
        if decision not in {
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.MODIFIED,
        }:
            raise ValueError("review decision must be approved, rejected or modified")
        review = state.pending_reviews.pop(review_id)
        review.status = decision
        review.reviewer_note = note
        review.resolved_tick = tick
        if decision == ApprovalStatus.REJECTED:
            state.rejected_actions += 1
        else:
            state.approved_actions += 1
            # Human approval allows only bounded, abstract simulation effects.
            if review.intent == AgentIntent.HIGH_IMPACT_DISRUPTION:
                magnitude = 0.015 if decision == ApprovalStatus.MODIFIED else 0.03
                society.public_mood = _clamp(society.public_mood - magnitude)
                civilization.stability = _clamp(civilization.stability - magnitude)
                civilization.social.conflict = _clamp(civilization.social.conflict + magnitude)
        state.resolved_reviews.append(review)
        if len(state.resolved_reviews) > 200:
            del state.resolved_reviews[:-200]
        events.append(
            DomainEvent(
                "HumanReviewResolved",
                tick,
                {
                    "review_id": review.id,
                    "decision": decision.value,
                    "agent_id": review.agent_id,
                },
            )
        )
        return review

    def _execute_citizen_intent(
        self,
        *,
        intent: AgentIntent,
        citizen: Citizen,
        profile: CitizenLifeProfile | None,
        society: SocietyState,
        civilization: CivilizationState,
    ) -> float:
        outcome = 0.55
        if profile is None:
            return outcome
        if intent == AgentIntent.LEARN:
            profile.learning_progress = _clamp(profile.learning_progress + 0.012)
            profile.skill = _clamp(profile.skill + 0.004)
            outcome = 0.70
        elif intent == AgentIntent.SOCIALIZE:
            profile.belonging = _clamp(profile.belonging + 0.012)
            society.social_cohesion = _clamp(society.social_cohesion + 0.0002)
            outcome = 0.66
        elif intent == AgentIntent.SEEK_HEALTHCARE:
            profile.physical_health = _clamp(profile.physical_health + 0.008)
            profile.mental_health = _clamp(profile.mental_health + 0.005)
            outcome = 0.72
        elif intent == AgentIntent.REST:
            profile.stress = _clamp(profile.stress - 0.010)
            outcome = 0.64
        elif intent == AgentIntent.EARN_INCOME:
            outcome = 0.72 if citizen.employed else 0.34
        elif intent == AgentIntent.SAVE:
            outcome = 0.62 if citizen.employed else 0.28
        elif intent == AgentIntent.CHANGE_JOB:
            profile.career_progress = _clamp(profile.career_progress + 0.006)
            outcome = 0.52 + civilization.careers.mobility_index * 0.25
        elif intent == AgentIntent.COLLABORATE:
            profile.civic_engagement = _clamp(profile.civic_engagement + 0.008)
            society.civic_participation = _clamp(society.civic_participation + 0.0002)
            outcome = 0.65
        elif intent == AgentIntent.PEACEFUL_PROTEST:
            civilization.social.protests += 1
            civilization.social.protest_pressure = _clamp(
                civilization.social.protest_pressure - 0.003
            )
            society.collective_agency = _clamp(society.collective_agency + 0.001)
            outcome = 0.48
        return _clamp(outcome)

    def _learn(self, agent: AgentState, intent: AgentIntent, outcome: float, tick: int) -> None:
        agent.memories.append(
            AgentMemory(
                tick=tick,
                kind="action_outcome",
                summary=f"{intent.value} produced outcome {outcome:.2f}",
                outcome=outcome,
                importance=0.45 + abs(outcome - 0.5),
            )
        )
        if len(agent.memories) > 32:
            del agent.memories[:-32]
        if agent.goals:
            agent.goals[0].progress = _clamp(
                agent.goals[0].progress + outcome * agent.learning_rate * 0.20
            )

    def _update_business_agent(
        self,
        *,
        state: AutonomousWorldState,
        agent: AgentState,
        business: Business,
        civilization: CivilizationState,
        tick: int,
        events: EventStore,
    ) -> None:
        low_inventory = float(business.inventory_units) < max(
            10.0, len(business.employee_ids) * 2.0
        )
        weak_confidence = civilization.economy.confidence_index < 0.42
        if weak_confidence:
            intent = AgentIntent.STABILIZE_BUSINESS
        elif low_inventory:
            intent = AgentIntent.EXPAND_BUSINESS
        else:
            intent = AgentIntent.ADJUST_PRICES
        agent.decisions += 1
        agent.last_decision_tick = tick
        state.total_decisions += 1
        state.autonomous_actions += 1
        outcome = 0.56 + civilization.economy.confidence_index * 0.20
        self._learn(agent, intent, _clamp(outcome), tick)
        events.append(
            DomainEvent(
                "OrganizationAgentActed",
                tick,
                {"agent_id": agent.agent_id, "kind": "business", "intent": intent.value},
            )
        )

    def _update_institution_agent(
        self,
        *,
        state: AutonomousWorldState,
        agent: AgentState,
        society: SocietyState,
        civilization: CivilizationState,
        tick: int,
        events: EventStore,
    ) -> None:
        if civilization.social.protest_pressure > 0.48:
            intent = AgentIntent.COMMUNITY_CAMPAIGN
            civilization.social.civic_campaigns += 1
            society.civic_participation = _clamp(society.civic_participation + 0.001)
        else:
            intent = AgentIntent.ADVOCATE_POLICY
        agent.decisions += 1
        agent.last_decision_tick = tick
        state.total_decisions += 1
        state.autonomous_actions += 1
        self._learn(agent, intent, 0.63, tick)
        events.append(
            DomainEvent(
                "OrganizationAgentActed",
                tick,
                {"agent_id": agent.agent_id, "kind": "institution", "intent": intent.value},
            )
        )

    def _agent_interactions(
        self, state: AutonomousWorldState, tick: int, events: EventStore
    ) -> None:
        if tick % 24 != 0:
            return
        active = [agent for agent in state.agents.values() if agent.last_decision_tick > 0]
        if len(active) < 2:
            return
        interaction_count = min(12, len(active) // 2)
        for index in range(interaction_count):
            source = active[(index * 7 + tick) % len(active)]
            target = active[(index * 13 + tick + 1) % len(active)]
            if source.agent_id == target.agent_id:
                continue
            outcome = _clamp(0.52 + _noise(source.agent_id + target.agent_id, tick, 0.18))
            interaction = AgentInteraction(
                tick=tick,
                source_agent_id=source.agent_id,
                target_agent_id=target.agent_id,
                kind="information_exchange",
                outcome=outcome,
                summary=f"{source.name} exchanged local information with {target.name}",
            )
            state.interactions.append(interaction)
            if len(state.interactions) > 300:
                del state.interactions[:-300]
            events.append(
                DomainEvent(
                    "AgentInteraction",
                    tick,
                    {
                        "source": source.agent_id,
                        "target": target.agent_id,
                        "outcome": round(outcome, 3),
                    },
                )
            )

    def _update_world_metrics(
        self,
        state: AutonomousWorldState,
        society: SocietyState,
        civilization: CivilizationState,
        tick: int,
    ) -> None:
        agents = list(state.agents.values())
        if not agents:
            return
        learned = sum(1 for agent in agents if agent.memories)
        planned = sum(1 for agent in agents if agent.plan is not None)
        interaction_factor = min(1.0, len(state.interactions) / max(1.0, len(agents) * 0.10))
        state.learning_index = _clamp(learned / len(agents))
        state.collective_signal = _clamp(
            0.45 * society.collective_agency
            + 0.30 * society.civic_participation
            + 0.25 * interaction_factor
        )
        state.emergence_index = _clamp(
            0.30 * (planned / len(agents))
            + 0.25 * state.learning_index
            + 0.25 * state.collective_signal
            + 0.20 * civilization.intelligence.citizen_adaptation
        )
        civilization.intelligence.citizen_adaptation = _clamp(
            0.70 * civilization.intelligence.citizen_adaptation
            + 0.30 * (0.55 * state.learning_index + 0.45 * state.emergence_index)
        )
        organization_agents = [agent for agent in agents if agent.kind != AgentKind.CITIZEN]
        if organization_agents:
            organization_learning = sum(1 for agent in organization_agents if agent.memories) / len(
                organization_agents
            )
            civilization.intelligence.institution_adaptation = _clamp(
                0.75 * civilization.intelligence.institution_adaptation
                + 0.25 * organization_learning
            )
        state.world_years_simulated = tick / (96.0 * 365.0)
