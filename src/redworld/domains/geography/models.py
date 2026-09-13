from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class Coordinate:
    x: float
    y: float

    def __post_init__(self) -> None:
        if not (0 <= self.x <= 100 and 0 <= self.y <= 100):
            raise ValueError("coordinates must be in the normalized 0..100 world plane")


class LocationType(StrEnum):
    HOME = "home"
    WORKPLACE = "workplace"
    SHOP = "shop"
    BANK = "bank"
    GOVERNMENT = "government"
    UNIVERSITY = "university"
    PARK = "park"
    STATION = "station"
    HOSPITAL = "hospital"
    PUBLIC = "public"


@dataclass(slots=True)
class Region:
    id: str
    name: str


@dataclass(slots=True)
class City:
    id: str
    region_id: str
    name: str


@dataclass(slots=True)
class District:
    id: str
    city_id: str
    name: str
    center: Coordinate
    width: float
    height: float
    kind: str


@dataclass(slots=True)
class Location:
    id: str
    district_id: str
    name: str
    location_type: LocationType
    coordinate: Coordinate
    capacity: int = 100
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TravelEdge:
    source: str
    target: str
    minutes: int
