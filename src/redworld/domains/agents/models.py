from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class AgentKind(StrEnum):
    CITIZEN = "citizen"
    BUSINESS = "business"
    INSTITUTION = "institution"


class AgentIntent(StrEnum):
    REST = "rest"
    WORK = "work"
    EARN_INCOME = "earn_income"
    LEARN = "learn"
    SEEK_HEALTHCARE = "seek_healthcare"
    SOCIALIZE = "socialize"
    SAVE = "save"
    CHANGE_JOB = "change_job"
    COLLABORATE = "collaborate"
    EXPAND_BUSINESS = "expand_business"
    STABILIZE_BUSINESS = "stabilize_business"
    ADJUST_PRICES = "adjust_prices"
    ADVOCATE_POLICY = "advocate_policy"
    COMMUNITY_CAMPAIGN = "community_campaign"
    PEACEFUL_PROTEST = "peaceful_protest"
    HIGH_IMPACT_DISRUPTION = "high_impact_disruption"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


@dataclass(slots=True)
class Belief:
    topic: str
    value: float
    confidence: float
    learned_tick: int
    source: str = "observation"


@dataclass(slots=True)
class AgentGoal:
    key: str
    priority: float
    target: float
    progress: float = 0.0
    created_tick: int = 0
    active: bool = True


@dataclass(slots=True)
class PlanStep:
    intent: AgentIntent
    reason: str
    completed: bool = False


@dataclass(slots=True)
class AgentPlan:
    goal_key: str
    steps: list[PlanStep] = field(default_factory=list)
    current_step: int = 0
    created_tick: int = 0
    revisions: int = 0

    @property
    def complete(self) -> bool:
        return self.current_step >= len(self.steps)


@dataclass(slots=True)
class AgentMemory:
    tick: int
    kind: str
    summary: str
    outcome: float
    importance: float = 0.5


@dataclass(slots=True)
class AgentState:
    agent_id: str
    kind: AgentKind
    name: str
    autonomy: float = 0.65
    risk_tolerance: float = 0.25
    learning_rate: float = 0.12
    beliefs: dict[str, Belief] = field(default_factory=dict)
    goals: list[AgentGoal] = field(default_factory=list)
    plan: AgentPlan | None = None
    memories: list[AgentMemory] = field(default_factory=list)
    last_observed_tick: int = 0
    last_decision_tick: int = 0
    decisions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0


@dataclass(slots=True)
class ActionReview:
    id: str
    agent_id: str
    agent_name: str
    agent_kind: AgentKind
    intent: AgentIntent
    reason: str
    risk_level: RiskLevel
    risk_score: float
    expected_impact: str
    created_tick: int
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer_note: str = ""
    resolved_tick: int | None = None


@dataclass(slots=True)
class AgentInteraction:
    tick: int
    source_agent_id: str
    target_agent_id: str
    kind: str
    outcome: float
    summary: str


@dataclass(slots=True)
class AutonomousWorldState:
    initialized: bool = False
    enabled: bool = True
    agents: dict[str, AgentState] = field(default_factory=dict)
    pending_reviews: dict[str, ActionReview] = field(default_factory=dict)
    resolved_reviews: list[ActionReview] = field(default_factory=list)
    interactions: list[AgentInteraction] = field(default_factory=list)
    total_decisions: int = 0
    autonomous_actions: int = 0
    blocked_actions: int = 0
    approved_actions: int = 0
    rejected_actions: int = 0
    replans: int = 0
    collective_signal: float = 0.0
    emergence_index: float = 0.0
    learning_index: float = 0.0
    world_years_simulated: float = 0.0
