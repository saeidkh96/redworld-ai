from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class MarketState:
    food_units: Decimal = Decimal("5000")
    demand_index: float = 1.0
    last_restock_day: int = 1
