from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Any

from redworld.core.events import DomainEvent
from redworld.domain.value_objects.money import Money
from redworld.domains.geography import Coordinate, Location, LocationType
from redworld.domains.society import Relationship, RelationshipType

from .models import (
    CausalRecord,
    CitizenMind,
    EmergentEvent,
    MarketSignal,
    SelfEvolvingState,
    SocialTie,
)


def stable(*x: object) -> int:
    return int(hashlib.sha256("|".join(map(str, x)).encode()).hexdigest()[:16], 16)


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


class SelfEvolvingCivilizationService:
    """Deterministic bounded civilization feedback coupled to the real world state."""

    def bootstrap(self, w: Any) -> None:
        s: SelfEvolvingState = w.self_evolving
        active = set(w.citizens)
        traits = ("adaptive", "social", "cautious", "ambitious", "creative")
        goals = ("stability", "prosperity", "community", "learning", "mobility")
        for cid, citizen in w.citizens.items():
            if cid not in s.minds:
                n = stable(cid, "mind")
                generation = max(0, int(getattr(citizen, "age", 0)) // 25)
                # New children inherit their household's youngest existing generation.
                household = w.households.get(str(getattr(citizen, "household_id", "")))
                if household:
                    relatives = [s.minds.get(str(mid)) for mid in household.member_ids]
                    known = [m.generation for m in relatives if m is not None]
                    if known and citizen.age < 18:
                        generation = max(0, min(known) - 1)
                s.minds[cid] = CitizenMind(
                    cid,
                    generation,
                    traits[n % len(traits)],
                    goals[(n // 7) % len(goals)],
                )
        for cid in list(s.minds):
            if cid not in active:
                del s.minds[cid]
        counts: dict[int, int] = {}
        for mind in s.minds.values():
            counts[mind.generation] = counts.get(mind.generation, 0) + 1
        s.generations = counts
        if not s.markets:
            for sector in ("essentials", "housing", "services", "industry"):
                s.markets[sector] = MarketSignal(sector)

    def update(self, w: Any) -> None:
        self.bootstrap(w)
        s = w.self_evolving
        clock = w.clock
        if s.last_day != clock.day:
            self.daily(w)
            s.last_day = clock.day
        month_key = f"{clock.year}:{clock.month}"
        if clock.day_of_month == 1 and s.last_month != month_key:
            self.monthly(w)
            s.last_month = month_key
        if clock.day_of_month == 1 and clock.month == 1 and s.last_year != clock.year:
            self.yearly(w)
            s.last_year = clock.year

    def daily(self, w: Any) -> None:
        self.bootstrap(w)
        s = w.self_evolving
        ids = sorted(s.minds)
        goals = ("stability", "prosperity", "community", "learning", "mobility")
        for cid in ids[:: max(1, len(ids) // 64)]:
            mind = s.minds[cid]
            q = (stable(cid, w.clock.day) % 1000) / 1000
            mind.knowledge = clamp(mind.knowledge + 0.0005 + q * 0.0005)
            profile = w.life_profiles.get(cid)
            if profile is not None:
                mind.reputation = clamp(0.75 * mind.reputation + 0.25 * profile.reputation)
                profile.education = clamp(profile.education + mind.knowledge * 0.0001)
            if q > 0.92:
                mind.goal = goals[stable(cid, w.clock.day, "goal") % len(goals)]

        sample = ids[:: max(1, len(ids) // 24)]
        for left_id, right_id in zip(sample, sample[1:], strict=False):
            key = ":".join(sorted((left_id, right_id)))
            tie = s.social_ties.setdefault(key, SocialTie(left_id, right_id))
            delta = ((stable(key, w.clock.day) % 201) - 100) / 10000
            tie.affinity = clamp(tie.affinity + delta)
            tie.trust = clamp(tie.trust + delta * 0.5)
            tie.conflict = clamp(tie.conflict - delta * 0.25)
            self._sync_social_graph(w, tie)
            s.relationship_updates += 1

        for event in s.emergent_events:
            if not event.resolved and w.tick - event.tick > 240:
                event.resolved = True

    def _sync_social_graph(self, w: Any, tie: SocialTie) -> None:
        left = w.citizens.get(tie.left_id)
        right = w.citizens.get(tie.right_id)
        if left is None or right is None:
            return
        existing = [
            rel
            for rel in w.society.for_citizen(left.id)
            if {rel.source_id, rel.target_id} == {left.id, right.id}
        ]
        strength = clamp((tie.affinity + tie.trust + (1.0 - tie.conflict)) / 3)
        if existing:
            existing[0].strength = strength
        elif strength >= 0.48:
            w.society.add(Relationship(left.id, right.id, RelationshipType.FRIEND, strength))

    def monthly(self, w: Any) -> None:
        s = w.self_evolving
        population = max(1, len(w.citizens))
        employed = sum(1 for citizen in w.citizens.values() if citizen.employed)
        density = max(1, len(w.businesses)) / max(1.0, population / 40)
        for sector, market in s.markets.items():
            noise = ((stable(sector, w.clock.year, w.clock.month) % 101) - 50) / 5000
            market.demand = max(0.5, min(1.8, 0.8 + employed / population * 0.4 + noise))
            market.supply = max(0.5, min(1.8, 0.8 + density * 0.2 - noise))
            market.price = max(
                0.6, min(1.8, market.price + (market.demand - market.supply) * 0.025)
            )
            s.market_updates += 1
        self._apply_market_to_businesses(w)

        unemployment = 1 - employed / population
        s.public_sentiment = clamp(s.public_sentiment + (0.18 - unemployment) * 0.02)
        self._apply_institutional_feedback(w)

        occupancy = len(w.citizens) / max(1, len(w.households))
        s.housing_pressure = clamp((occupancy - 2.2) / 2.8)
        if s.housing_pressure > 0.35:
            growth = min(0.02, s.housing_pressure * 0.015)
            s.city_capacity += growth
            s.infrastructure += growth * 0.5
            if self._expand_real_city(w):
                s.city_expansions += 1
            self.record(w, "housing_pressure", "city_expansion", growth)

        average_price = sum(m.price for m in s.markets.values()) / len(s.markets)
        if average_price > 1.08:
            self.record(w, "market_pressure", "household_pressure", average_price - 1)
        if s.housing_pressure > 0.35:
            self.record(w, "population_density", "urban_expansion", s.housing_pressure)

        candidates: list[tuple[str, str, float]] = []
        if average_price > 1.12:
            candidates.append(
                (
                    "cost_pressure",
                    "Rising prices are reshaping household choices.",
                    average_price - 1,
                )
            )
        if s.housing_pressure > 0.45:
            candidates.append(
                (
                    "housing_wave",
                    "Housing pressure is accelerating urban development.",
                    s.housing_pressure,
                )
            )
        if s.public_sentiment < 0.38:
            candidates.append(
                ("civic_pressure", "Public sentiment is increasing institutional pressure.", 0.5)
            )
        for kind, summary, severity in candidates:
            event_id = f"{w.clock.year}:{w.clock.month}:{kind}"
            if not any(event.event_id == event_id for event in s.emergent_events):
                event = EmergentEvent(event_id, kind, summary, clamp(severity), w.tick)
                s.emergent_events.append(event)
                s.emergent_events_created += 1
                self._apply_emergent_event(w, event)
                self.record(w, kind, "emergent_event", severity)

        pressure = (s.housing_pressure + 1 - s.public_sentiment) / 2
        if pressure > 0.32:
            s.infrastructure += min(0.01, pressure * 0.01)
            self._adapt_world(w, pressure)
            s.adaptations += 1
            self.record(w, "combined_pressure", "civilization_adaptation", pressure)
        s.history = s.history[-512:]
        s.emergent_events = s.emergent_events[-128:]

    def _apply_market_to_businesses(self, w: Any) -> None:
        if not w.businesses:
            return
        sectors = tuple(sorted(w.self_evolving.markets))
        for business in w.businesses.values():
            sector = sectors[stable(business.id, "sector") % len(sectors)]
            signal = w.self_evolving.markets[sector]
            price_factor = Decimal(str(max(0.97, min(1.03, 1 + (signal.price - 1) * 0.08))))
            wage_factor = Decimal(
                str(max(0.985, min(1.02, 1 + (signal.demand - signal.supply) * 0.02)))
            )
            business.unit_price = Money(
                business.unit_price.amount * price_factor, business.unit_price.currency
            )
            business.wage_offer = Money(
                business.wage_offer.amount * wage_factor, business.wage_offer.currency
            )
            business.productivity_per_employee = max(
                Decimal("0.5"),
                business.productivity_per_employee
                * Decimal(str(max(0.99, min(1.01, signal.supply)))),
            )

    def _apply_institutional_feedback(self, w: Any) -> None:
        society = w.autonomous_society
        society.public_mood = clamp(
            0.8 * society.public_mood + 0.2 * w.self_evolving.public_sentiment
        )
        society.institutional_trust = clamp(
            society.institutional_trust + (w.self_evolving.public_sentiment - 0.5) * 0.02
        )
        for institution in society.institutions.values():
            institution.trust = clamp(0.85 * institution.trust + 0.15 * society.institutional_trust)
            institution.capacity = clamp(institution.capacity + (society.public_mood - 0.5) * 0.01)
            w.self_evolving.institutional_updates += 1

    def _expand_real_city(self, w: Any) -> bool:
        if not w.geography.districts:
            return False
        index = w.self_evolving.city_expansions + 1
        district = sorted(w.geography.districts.values(), key=lambda d: d.id)[
            index % len(w.geography.districts)
        ]
        location_id = f"adaptive-{district.id}-{w.clock.year:02d}-{w.clock.month:02d}"
        if location_id in w.geography.locations:
            return False
        dx = ((index % 5) - 2) * 0.8
        dy = (((index // 5) % 5) - 2) * 0.8
        x = max(0.0, min(100.0, district.center.x + dx))
        y = max(0.0, min(100.0, district.center.y + dy))
        w.geography.add_location(
            Location(
                location_id,
                district.id,
                f"Adaptive Infrastructure {index}",
                LocationType.PUBLIC,
                Coordinate(x, y),
                180,
            )
        )
        district_locations = w.geography.district_locations(district.id)
        neighbor = next((loc for loc in district_locations if loc.id != location_id), None)
        if neighbor is not None:
            w.geography.connect(location_id, neighbor.id, 3)
        w.events.append(
            DomainEvent(
                "AdaptiveCityLocationCreated",
                w.tick,
                {"location_id": location_id, "district_id": district.id},
            )
        )
        return True

    def _apply_emergent_event(self, w: Any, event: EmergentEvent) -> None:
        if event.kind == "cost_pressure":
            for citizen in list(w.citizens.values())[:64]:
                citizen.consumption_budget = Money(
                    citizen.consumption_budget.amount * Decimal("0.99"),
                    citizen.consumption_budget.currency,
                )
        elif event.kind == "housing_wave":
            self._expand_real_city(w)
        elif event.kind == "civic_pressure":
            w.autonomous_society.civic_participation = clamp(
                w.autonomous_society.civic_participation + 0.02
            )
        w.events.append(
            DomainEvent(
                "EmergentWorldEvent", w.tick, {"kind": event.kind, "severity": event.severity}
            )
        )

    def _adapt_world(self, w: Any, pressure: float) -> None:
        # Adaptation feeds back into institutions and citizens rather than remaining a counter.
        w.autonomous_society.collective_agency = clamp(
            w.autonomous_society.collective_agency + pressure * 0.005
        )
        for profile in list(w.life_profiles.values())[:64]:
            profile.civic_trust = clamp(
                profile.civic_trust + (w.self_evolving.public_sentiment - 0.5) * 0.002
            )

    def yearly(self, w: Any) -> None:
        self.bootstrap(w)
        s = w.self_evolving
        deaths = max(0, int(getattr(w.evolution, "deaths_realized", 0)))
        survivors = sorted(s.minds.values(), key=lambda m: (m.generation, m.citizen_id))
        for mind in survivors[: min(deaths, len(survivors), 12)]:
            mind.knowledge = clamp(mind.knowledge + 0.03)
            mind.reputation = clamp(mind.reputation + 0.01)
            s.inheritances += 1
        for younger, older in zip(survivors[:24], reversed(survivors[-24:]), strict=False):
            if younger.citizen_id != older.citizen_id:
                younger.knowledge = clamp(younger.knowledge + min(0.02, older.knowledge * 0.02))
                younger.reputation = clamp(younger.reputation + older.reputation * 0.005)
                profile = w.life_profiles.get(younger.citizen_id)
                if profile is not None:
                    profile.education = clamp(profile.education + older.knowledge * 0.002)
                s.knowledge_transfers += 1
        self.bootstrap(w)

    def record(self, w: Any, cause: str, effect: str, magnitude: float) -> None:
        w.self_evolving.history.append(
            CausalRecord(w.tick, w.clock.year, cause, effect, round(float(magnitude), 6))
        )
        w.self_evolving.causal_links += 1

    def snapshot(self, w: Any) -> dict[str, object]:
        s = w.self_evolving
        return {
            "version": "1.4.0",
            "milestone": "Self-Evolving Civilization",
            "citizen_minds": len(s.minds),
            "social_ties": len(s.social_ties),
            "generations": dict(sorted(s.generations.items())),
            "markets": {
                k: {
                    "price": round(v.price, 4),
                    "demand": round(v.demand, 4),
                    "supply": round(v.supply, 4),
                }
                for k, v in s.markets.items()
            },
            "public_sentiment": round(s.public_sentiment, 4),
            "housing_pressure": round(s.housing_pressure, 4),
            "city_capacity": round(s.city_capacity, 4),
            "infrastructure": round(s.infrastructure, 4),
            "causal_links": s.causal_links,
            "active_emergent_events": [
                {
                    "id": e.event_id,
                    "kind": e.kind,
                    "summary": e.summary,
                    "severity": round(e.severity, 4),
                }
                for e in s.emergent_events
                if not e.resolved
            ][-16:],
            "adaptations": s.adaptations,
            "human_review_authority_preserved": True,
        }
