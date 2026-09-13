from redworld.domains.time import WorldClock


def test_clock_rolls_over_day() -> None:
    clock = WorldClock(day=1, minute_of_day=23 * 60 + 45, minutes_per_tick=15)
    clock.advance()
    assert clock.day == 2
    assert clock.minute_of_day == 0
    assert clock.tick == 1
