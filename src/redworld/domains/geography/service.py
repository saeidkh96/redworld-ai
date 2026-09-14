from __future__ import annotations

from dataclasses import dataclass, field
from heapq import heappop, heappush
from math import hypot

from .models import City, District, Location, Region, TravelEdge


@dataclass(slots=True)
class GeographyService:
    regions: dict[str, Region] = field(default_factory=dict)
    cities: dict[str, City] = field(default_factory=dict)
    districts: dict[str, District] = field(default_factory=dict)
    locations: dict[str, Location] = field(default_factory=dict)
    adjacency: dict[str, list[TravelEdge]] = field(default_factory=dict)

    _path_cache: dict[tuple[str, str], tuple[str, ...]] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def add_region(self, region: Region) -> None:
        self.regions[region.id] = region

    def add_city(self, city: City) -> None:
        if city.region_id not in self.regions:
            raise ValueError("city region does not exist")
        self.cities[city.id] = city

    def add_district(self, district: District) -> None:
        if district.city_id not in self.cities:
            raise ValueError("district city does not exist")
        self.districts[district.id] = district

    def add_location(self, location: Location) -> None:
        if location.district_id not in self.districts:
            raise ValueError("location district does not exist")

        self.locations[location.id] = location
        self.adjacency.setdefault(location.id, [])
        self._path_cache.clear()

    def connect(
        self,
        source: str,
        target: str,
        minutes: int | None = None,
        *,
        bidirectional: bool = True,
    ) -> None:
        if source not in self.locations or target not in self.locations:
            raise ValueError("both locations must exist")

        if minutes is None:
            a = self.locations[source].coordinate
            b = self.locations[target].coordinate
            minutes = max(1, round(hypot(a.x - b.x, a.y - b.y) * 1.2))

        self.adjacency[source].append(TravelEdge(source, target, minutes))

        if bidirectional:
            self.adjacency[target].append(TravelEdge(target, source, minutes))

        self._path_cache.clear()

    def shortest_path(self, source: str, target: str) -> list[str]:
        if source == target:
            return [source]

        cache_key = (source, target)
        cached = self._path_cache.get(cache_key)

        if cached is not None:
            return list(cached)

        queue: list[tuple[int, str, list[str]]] = [(0, source, [source])]
        best: dict[str, int] = {source: 0}

        while queue:
            cost, node, path = heappop(queue)

            if node == target:
                cached_path = tuple(path)
                self._path_cache[cache_key] = cached_path
                return list(cached_path)

            if cost != best.get(node):
                continue

            for edge in self.adjacency.get(node, []):
                new_cost = cost + edge.minutes

                if new_cost < best.get(edge.target, 10**12):
                    best[edge.target] = new_cost
                    heappush(
                        queue,
                        (
                            new_cost,
                            edge.target,
                            [*path, edge.target],
                        ),
                    )

        raise ValueError(f"no route between {source} and {target}")

    def district_locations(self, district_id: str) -> list[Location]:
        return [x for x in self.locations.values() if x.district_id == district_id]
