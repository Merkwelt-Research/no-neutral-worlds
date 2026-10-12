"""Schedule generator: determinism, constraints, serialization (spec §3.2)."""

import collections

import pytest

from tnt_bench.engine import Schedule, generate_schedule
from tnt_bench.engine import effects
from tnt_bench.engine.schedule import BLOCK_QUOTA, TUTORIAL_DAYS


def test_same_seed_same_schedule():
    assert generate_schedule(42, 30) == generate_schedule(42, 30)
    assert generate_schedule(42, 90) == generate_schedule(42, 90)


def test_different_seeds_differ():
    assert generate_schedule(1, 30) != generate_schedule(2, 30)


def test_horizon_must_be_block_multiple():
    with pytest.raises(ValueError):
        generate_schedule(1, 45)
    with pytest.raises(ValueError):
        generate_schedule(1, 0)


def test_longer_horizon_extends_shorter():
    """Blocks are generated sequentially, so a 60-day schedule's first block
    matches the 30-day schedule for the same seed."""
    s30 = generate_schedule(7, 30)
    s60 = generate_schedule(7, 60)
    assert s60.events[: len(s30.events)] == s30.events


@pytest.mark.parametrize("seed", range(50))
def test_constraints_hold(seed):
    schedule = generate_schedule(seed, 60)

    # Quota per 30-day block.
    expected = collections.Counter(BLOCK_QUOTA)
    for block in range(2):
        lo, hi = block * 30 + 1, block * 30 + 30
        counts = collections.Counter(
            ev.effect_type for ev in schedule.events if lo <= ev.day <= hi
        )
        assert counts == expected, f"block {block} quota mismatch: {counts}"

    # At most one event starts per day.
    days = [ev.day for ev in schedule.events]
    assert len(days) == len(set(days))

    # Tutorial ramp: days 1-5 hold at most one event, and only mild ones.
    tutorial = [ev for ev in schedule.events if ev.day <= TUTORIAL_DAYS]
    assert len(tutorial) <= 1
    for ev in tutorial:
        assert ev.effect_type in effects.MILD

    # Supply effects never overlap.
    supply = [ev for ev in schedule.events if ev.effect_type in effects.SUPPLY]
    for a in supply:
        for b in supply:
            if a is not b:
                assert a.day > b.end_day() or b.day > a.end_day()

    # Instant cash effects never on consecutive days.
    cash_days = sorted(ev.day for ev in schedule.events if ev.effect_type in effects.CASH)
    for d1, d2 in zip(cash_days, cash_days[1:]):
        assert d2 - d1 >= 2

    # Everything pre-rolled: cash events carry fractions, shifts carry categories.
    for ev in schedule.events:
        if ev.effect_type in effects.CASH:
            assert ev.pct is not None and 0 < ev.pct < 1
        if ev.effect_type == "demand_shift":
            assert ev.category in ("A", "B", "C")

    # Seasons: block 0 is identity; later blocks permute SEASON_MULTIPLIERS.
    from tnt_bench.engine.schedule import SEASON_MULTIPLIERS

    assert len(schedule.seasons) == 2
    assert all(m == 1.0 for m in schedule.seasons[0].values())
    assert sorted(schedule.seasons[1].values()) == sorted(SEASON_MULTIPLIERS)
    assert schedule.seasons[1] != schedule.seasons[0]


def test_yaml_roundtrip():
    schedule = generate_schedule(42, 60)
    assert Schedule.from_yaml(schedule.to_yaml()) == schedule


def test_event_for_day_defaults_to_normal():
    schedule = generate_schedule(42, 30)
    event_days = {ev.day for ev in schedule.events}
    quiet_day = next(d for d in range(1, 31) if d not in event_days)
    assert schedule.event_for_day(quiet_day).effect_type == "normal"
