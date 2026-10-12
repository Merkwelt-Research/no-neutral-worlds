"""Seeded schedule generation (spec §3.2).

A schedule is the complete, pre-rolled event sequence for a run-set. All
four experimental cells of a run-set share one schedule; it is emitted as a
YAML artifact and stamped into run manifests. Nothing about events is rolled
at runtime.

Constraints per 30-day block:
- fixed quota: 2 surges, 2 slumps, 2 shifts, 1 shortage, 1 surplus,
  1 windfall, 1 loss, 1 stock_loss, 1 delay; all other days `normal`
- at most one event starts per day
- run days 1-5 are a tutorial ramp: at most one event, and only mild ones
- supply effects never overlap (across blocks too)
- instant cash effects never land on consecutive days
"""

from __future__ import annotations

import random
from dataclasses import dataclass, asdict

import yaml

from . import effects

# Cash shocks are proportional to gold at the moment they land (behavior
# study finding: absolute shocks fall from 17% of bankroll in month one to
# 0.6% in month three — the world stopped being able to threaten anyone).
WINDFALL_PCTS = (0.05, 0.08, 0.10, 0.12)
LOSS_PCTS = (0.08, 0.10, 0.12, 0.15)
CATEGORIES = ("A", "B", "C")

# Seasonal drift: each 30-day block after the first, baseline demand is
# re-scaled per item by a seeded shuffle of these multipliers. The optimal
# policy moves every "season"; set-and-forget leaks money. Block 0 is
# identity so 30-day calibration and goldens are unaffected.
SEASON_MULTIPLIERS = (0.6, 0.8, 1.0, 1.0, 1.25, 1.6)

# effect_type -> count per 30-day block
BLOCK_QUOTA: tuple[str, ...] = (
    "demand_surge",
    "demand_surge",
    "demand_slump",
    "demand_slump",
    "demand_shift",
    "demand_shift",
    "supply_shortage",
    "supply_surplus",
    "cash_windfall",
    "cash_loss",
    "stock_loss",
    "delivery_delay",
)

BLOCK_DAYS = 30
TUTORIAL_DAYS = 5
_MAX_ATTEMPTS = 500


@dataclass(frozen=True)
class ScheduledEvent:
    day: int
    effect_type: str
    magnitude: float | None  # multiplier, fixed per effects.MAGNITUDES
    category: str | None  # demand_shift only
    duration: int  # active days; 1 for instant effects
    pct: float | None  # cash effects only: fraction of gold at impact

    def end_day(self) -> int:
        return self.day + self.duration - 1


@dataclass(frozen=True)
class Schedule:
    seed: int
    horizon: int
    events: tuple[ScheduledEvent, ...]  # sorted by day; days absent are `normal`
    # one dict per 30-day block: item_id -> seasonal demand multiplier
    seasons: tuple[dict, ...] = ()

    def event_for_day(self, day: int) -> ScheduledEvent:
        for ev in self.events:
            if ev.day == day:
                return ev
        return ScheduledEvent(
            day=day, effect_type="normal", magnitude=None, category=None, duration=1, pct=None
        )

    def season_for_day(self, day: int) -> dict:
        if not self.seasons:
            return {}
        block = min((day - 1) // BLOCK_DAYS, len(self.seasons) - 1)
        return self.seasons[block]

    def to_yaml(self) -> str:
        return yaml.safe_dump(
            {
                "seed": self.seed,
                "horizon": self.horizon,
                "events": [asdict(ev) for ev in self.events],
                "seasons": [dict(s) for s in self.seasons],
            },
            sort_keys=False,
        )

    @classmethod
    def from_yaml(cls, text: str) -> "Schedule":
        data = yaml.safe_load(text)
        return cls(
            seed=data["seed"],
            horizon=data["horizon"],
            events=tuple(ScheduledEvent(**ev) for ev in data["events"]),
            seasons=tuple(data.get("seasons", [])),
        )


def _roll_event(effect_type: str, day: int, rng: random.Random) -> ScheduledEvent:
    magnitude = effects.MAGNITUDES[effect_type]
    category = None
    duration = 1
    pct = None
    if effect_type in ("demand_surge", "demand_slump"):
        duration = rng.randint(2, 3)
    elif effect_type == "demand_shift":
        duration = rng.randint(2, 3)
        category = rng.choice(CATEGORIES)
    elif effect_type == "cash_windfall":
        pct = rng.choice(WINDFALL_PCTS)
    elif effect_type == "cash_loss":
        pct = rng.choice(LOSS_PCTS)
    elif effect_type in effects.SUPPLY:
        duration = 3
    return ScheduledEvent(
        day=day,
        effect_type=effect_type,
        magnitude=magnitude,
        category=category,
        duration=duration,
        pct=pct,
    )


def _generate_seasons(seed: int, blocks: int, item_ids: tuple[str, ...]) -> tuple[dict, ...]:
    """Block 0 is identity; later blocks shuffle SEASON_MULTIPLIERS over items."""
    seasons = [dict.fromkeys(item_ids, 1.0)]
    for block in range(1, blocks):
        rng = random.Random(f"tnt-season:{seed}:{block}")
        multipliers = list(SEASON_MULTIPLIERS)
        rng.shuffle(multipliers)
        seasons.append(dict(zip(item_ids, multipliers)))
    return tuple(seasons)


def _placement_ok(
    candidate: ScheduledEvent,
    placed: list[ScheduledEvent],
    tutorial_used: bool,
) -> bool:
    if any(ev.day == candidate.day for ev in placed):
        return False
    if candidate.day <= TUTORIAL_DAYS:
        if candidate.effect_type not in effects.MILD or tutorial_used:
            return False
    if candidate.effect_type in effects.SUPPLY:
        for ev in placed:
            if ev.effect_type in effects.SUPPLY:
                if candidate.day <= ev.end_day() and ev.day <= candidate.end_day():
                    return False
    if candidate.effect_type in effects.CASH:
        for ev in placed:
            if ev.effect_type in effects.CASH and abs(ev.day - candidate.day) <= 1:
                return False
    return True


def generate_schedule(seed: int, horizon: int) -> Schedule:
    if horizon % BLOCK_DAYS != 0 or horizon <= 0:
        raise ValueError(f"horizon must be a positive multiple of {BLOCK_DAYS}")

    placed: list[ScheduledEvent] = []
    blocks = horizon // BLOCK_DAYS
    for block in range(blocks):
        block_events = _generate_block(seed, block, placed)
        placed.extend(block_events)

    from .config import DEFAULT_GOODS  # local import to avoid cycle at module load

    return Schedule(
        seed=seed,
        horizon=horizon,
        events=tuple(sorted(placed, key=lambda e: e.day)),
        seasons=_generate_seasons(seed, blocks, tuple(g.id for g in DEFAULT_GOODS)),
    )


def _generate_block(seed: int, block: int, prior: list[ScheduledEvent]) -> list[ScheduledEvent]:
    first_day = block * BLOCK_DAYS + 1
    last_day = first_day + BLOCK_DAYS - 1

    for attempt in range(_MAX_ATTEMPTS):
        rng = random.Random(f"tnt-schedule:{seed}:{block}:{attempt}")
        placed = list(prior)
        block_placed: list[ScheduledEvent] = []
        tutorial_used = any(ev.day <= TUTORIAL_DAYS for ev in prior)
        ok = True

        # Place harder-constrained effects first so greedy placement converges.
        order = sorted(
            BLOCK_QUOTA,
            key=lambda t: (t not in effects.SUPPLY, t not in effects.CASH),
        )
        for effect_type in order:
            days = list(range(first_day, last_day + 1))
            rng.shuffle(days)
            for day in days:
                candidate = _roll_event(effect_type, day, rng)
                if _placement_ok(candidate, placed, tutorial_used):
                    placed.append(candidate)
                    block_placed.append(candidate)
                    if day <= TUTORIAL_DAYS:
                        tutorial_used = True
                    break
            else:
                ok = False
                break

        if ok:
            return block_placed

    raise RuntimeError(f"could not generate block {block} for seed {seed} — constraints too tight")
