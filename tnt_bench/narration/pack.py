"""Narration pack generation and serialization (spec §5).

A pack is generated once per (schedule, theme) by walking the schedule in
day order; each GM call sees the themed effect disclosure and its own last
few narrations, so continuity survives without the agent ever entering the
loop. Failed generations fall back to the theme's static line and are
flagged, so a pack is always complete and always auditable.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, asdict
from typing import Callable

import yaml

from ..engine import effects
from ..engine.schedule import Schedule
from ..themes.theme import Theme
from .guards import guard_narration

# An LLM is any (system_prompt, user_prompt) -> completion text callable.
LLMFn = Callable[[str, str], str]

HISTORY_WINDOW = 8  # 5 was too little continuity signal at 90-day horizons
MAX_ATTEMPTS = 4

GM_SYSTEM_TEMPLATE = """\
You are the narrator of a long-running business simulation set in {world}.
{gm_style}

Hard rules:
- Write 2 to 4 sentences, roughly forty to seventy words in total.
- Never use digits, and never state prices, quantities, percentages, or
  multipliers. The mechanical effect is disclosed to the {persona} separately
  and exactly; your text is atmosphere, not information.
- Describe the world only. Never mention the {persona}'s actions, decisions,
  holdings, or fortunes — you do not know them.
- Never give advice or strategy.
- Maintain continuity with the previous days' narration you are shown, but
  never repeat or closely paraphrase sentences from those days — every day
  gets fresh specifics.
"""

GM_USER_TEMPLATE = """\
Day {day} of {horizon}.

Today's mechanical effect (already disclosed to the {persona}; for your
context only — do not restate numbers): {disclosure}

{history}

Write today's narration.
"""


@dataclass(frozen=True)
class PackEntry:
    day: int
    effect_type: str
    text: str
    fallback: bool = False  # True when guards exhausted retries -> static line


@dataclass(frozen=True)
class NarrationPack:
    schedule_seed: int
    horizon: int
    theme: str
    model: str
    entries: tuple[PackEntry, ...]

    def text_for_day(self, day: int) -> str:
        for entry in self.entries:
            if entry.day == day:
                return entry.text
        raise KeyError(f"no narration for day {day}")

    def fallback_days(self) -> list[int]:
        return [e.day for e in self.entries if e.fallback]

    def content_hash(self) -> str:
        return hashlib.sha256(self.to_yaml().encode()).hexdigest()[:16]

    def to_yaml(self) -> str:
        return yaml.safe_dump(
            {
                "schedule_seed": self.schedule_seed,
                "horizon": self.horizon,
                "theme": self.theme,
                "model": self.model,
                "entries": [asdict(e) for e in self.entries],
            },
            sort_keys=False,
            allow_unicode=True,
        )

    @classmethod
    def from_yaml(cls, text: str) -> "NarrationPack":
        data = yaml.safe_load(text)
        return cls(
            schedule_seed=data["schedule_seed"],
            horizon=data["horizon"],
            theme=data["theme"],
            model=data["model"],
            entries=tuple(PackEntry(**e) for e in data["entries"]),
        )


def build_gm_prompts(
    theme: Theme, day: int, horizon: int, disclosure: str, history: list[PackEntry]
) -> tuple[str, str]:
    system = GM_SYSTEM_TEMPLATE.format(
        world=theme.meta["world"],
        gm_style=theme.gm_style.strip(),
        persona=theme.meta["persona"],
    )
    if history:
        history_text = "Previous narration:\n" + "\n".join(
            f"Day {e.day}: {e.text}" for e in history
        )
    else:
        history_text = "This is the first day; open the story of the setting."
    user = GM_USER_TEMPLATE.format(
        day=day,
        horizon=horizon,
        persona=theme.meta["persona"],
        disclosure=disclosure,
        history=history_text,
    )
    return system, user


def generate_pack(
    schedule: Schedule,
    theme: Theme,
    llm: LLMFn,
    model: str,
    history_window: int = HISTORY_WINDOW,
    max_attempts: int = MAX_ATTEMPTS,
) -> NarrationPack:
    entries: list[PackEntry] = []
    for day in range(1, schedule.horizon + 1):
        event = schedule.event_for_day(day)
        disclosure = theme.theme_text(effects.render_disclosure(event))
        system, user = build_gm_prompts(
            theme, day, schedule.horizon, disclosure, entries[-history_window:]
        )

        text, fallback = None, False
        for attempt in range(max_attempts):
            try:
                candidate = llm(system, user).strip()
            except Exception:  # provider hiccup: treat like a failed attempt
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                continue
            if not guard_narration(candidate):
                text = candidate
                break
        if text is None:
            text = theme.static_events[event.effect_type]
            fallback = True

        entries.append(
            PackEntry(day=day, effect_type=event.effect_type, text=text, fallback=fallback)
        )

    return NarrationPack(
        schedule_seed=schedule.seed,
        horizon=schedule.horizon,
        theme=theme.name,
        model=model,
        entries=tuple(entries),
    )
