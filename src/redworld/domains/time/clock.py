from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WorldClock:
    tick: int = 0
    day: int = 1
    minute_of_day: int = 6 * 60
    minutes_per_tick: int = 15

    def advance(self, ticks: int = 1) -> None:
        if ticks < 0:
            raise ValueError("ticks must be non-negative")
        for _ in range(ticks):
            self.tick += 1
            self.minute_of_day += self.minutes_per_tick
            if self.minute_of_day >= 24 * 60:
                self.minute_of_day -= 24 * 60
                self.day += 1

    @property
    def hour(self) -> int:
        return self.minute_of_day // 60

    @property
    def minute(self) -> int:
        return self.minute_of_day % 60

    @property
    def year(self) -> int:
        return ((self.day - 1) // 360) + 1

    @property
    def month(self) -> int:
        return (((self.day - 1) % 360) // 30) + 1

    @property
    def day_of_month(self) -> int:
        return ((self.day - 1) % 30) + 1

    @property
    def week(self) -> int:
        return ((self.day - 1) // 7) + 1

    @property
    def weekday(self) -> int:
        return ((self.day - 1) % 7) + 1

    @property
    def is_weekend(self) -> bool:
        return self.weekday in {6, 7}

    @property
    def label(self) -> str:
        return (
            f"Y{self.year:02d} M{self.month:02d} "
            f"D{self.day_of_month:02d} · "
            f"{self.hour:02d}:{self.minute:02d}"
        )
