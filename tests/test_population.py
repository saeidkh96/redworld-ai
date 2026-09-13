from redworld.simulation.factory import create_world


def test_default_population_is_1500() -> None:
    world = create_world()
    assert len(world.citizens) == 1500


def test_population_generation_is_deterministic() -> None:
    first = create_world(population=20, seed=123)
    second = create_world(population=20, seed=123)
    profiles_first = [
        (
            citizen.name,
            citizen.age,
            citizen.occupation,
            citizen.employed,
            citizen.home_location_id,
        )
        for citizen in first.citizens.values()
    ]
    profiles_second = [
        (
            citizen.name,
            citizen.age,
            citizen.occupation,
            citizen.employed,
            citizen.home_location_id,
        )
        for citizen in second.citizens.values()
    ]
    assert profiles_first == profiles_second
