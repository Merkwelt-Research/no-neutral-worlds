"""Narration pack generation: guards, continuity, fallback, artifacts (spec §5)."""

import pytest

from tnt_bench.engine import generate_schedule
from tnt_bench.narration import NarrationPack, generate_pack, guard_narration
from tnt_bench.themes import load_theme

FANTASY = load_theme("fantasy")
NEUTRAL = load_theme("neutral")
SCHEDULE = generate_schedule(seed=42, horizon=30)

CLEAN_TEXT = (
    "The caravans from the eastern valleys arrived under a pale sky, and the "
    "market square filled early with traders comparing rumors of the road."
)


# ------------------------------------------------------------------- guards


def test_guard_accepts_clean_prose():
    assert guard_narration(CLEAN_TEXT) == []


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Too short.", "too short"),
        ("word " * 200, "too long"),
        ("The 3 caravans arrived from the east under a heavy morning sky.", "contains digits"),
        (
            "Merchants slashed every price in the lower market to move their wares quickly.",
            "mentions prices",
        ),
        (
            "The roads are quiet today, so you should consider stocking more remedies soon.",
            "strategic advice",
        ),
    ],
)
def test_guard_rejects_leaks(text, expected):
    problems = guard_narration(text)
    assert problems and any(expected in p for p in problems)


# --------------------------------------------------------------- generation


def test_pack_covers_every_day_with_continuity():
    seen_prompts = []

    def stub_llm(system, user):
        seen_prompts.append((system, user))
        day = len(seen_prompts)
        return (
            f"The town settles into the rhythm of another market morning, and the "
            f"criers trade yesterday's rumors for today's as bells ring over the square. (day {'x' * (day % 3 + 1)})"
        )

    pack = generate_pack(SCHEDULE, FANTASY, stub_llm, model="stub")
    assert len(pack.entries) == 30
    assert [e.day for e in pack.entries] == list(range(1, 31))
    assert pack.fallback_days() == []

    # First day gets the opening instruction; later days see prior narration.
    assert "first day" in seen_prompts[0][1]
    assert "Day 1:" in seen_prompts[1][1]
    # History window: day 30's prompt shows days 25-29, not day 1.
    assert "Day 29:" in seen_prompts[29][1]
    assert "Day 1:" not in seen_prompts[29][1]

    # GM hard rules present, themed.
    system = seen_prompts[0][0]
    assert "Never use digits" in system
    assert "shopkeeper" in system


def test_gm_sees_themed_disclosure_not_engine_ids():
    prompts = []

    def stub_llm(system, user):
        prompts.append(user)
        return CLEAN_TEXT

    generate_pack(SCHEDULE, FANTASY, stub_llm, model="stub")
    stock_loss_days = [ev.day for ev in SCHEDULE.events if ev.effect_type == "stock_loss"]
    assert stock_loss_days
    joined = "\n".join(prompts)
    assert "item_1" not in joined and "funds" not in joined


def test_retry_then_fallback_to_static_line():
    def leaky_llm(system, user):
        return "Exactly 7 wagons rolled in from the coast, heavy with salt and gossip."

    pack = generate_pack(SCHEDULE, NEUTRAL, leaky_llm, model="stub", max_attempts=3)
    assert pack.fallback_days() == list(range(1, 31))
    # Fallback text is the theme's static line for that day's effect.
    assert pack.text_for_day(1) in NEUTRAL.static_events.values()


def test_provider_exception_falls_back_without_crashing():
    """A GM that raises (e.g. OpenRouter's 200-with-no-choices surfaced as
    RuntimeError) degrades to static lines instead of killing generation."""

    def dead_llm(system, user):
        raise RuntimeError("provider returned no choices: rate limited")

    pack = generate_pack(SCHEDULE, NEUTRAL, dead_llm, model="stub", max_attempts=1)
    assert pack.fallback_days() == list(range(1, 31))


def test_provider_exception_retries_then_recovers(monkeypatch):
    monkeypatch.setattr("tnt_bench.narration.pack.time.sleep", lambda s: None)
    calls = {"n": 0}

    def flaky_llm(system, user):
        calls["n"] += 1
        if calls["n"] % 2 == 1:
            raise RuntimeError("transient")
        return CLEAN_TEXT

    pack = generate_pack(SCHEDULE, NEUTRAL, flaky_llm, model="stub")
    assert pack.fallback_days() == []


def test_retry_recovers_when_llm_cleans_up():
    calls = {"n": 0}

    def flaky_llm(system, user):
        calls["n"] += 1
        if calls["n"] % 2 == 1:
            return "The 3 carriers filed revised manifests this morning."
        return CLEAN_TEXT

    pack = generate_pack(SCHEDULE, NEUTRAL, flaky_llm, model="stub")
    assert pack.fallback_days() == []
    assert calls["n"] == 60  # one rejection + one success per day


# ---------------------------------------------------------------- artifacts


def test_yaml_roundtrip_and_hash_stability():
    pack = generate_pack(SCHEDULE, FANTASY, lambda s, u: CLEAN_TEXT, model="stub")
    restored = NarrationPack.from_yaml(pack.to_yaml())
    assert restored == pack
    assert restored.content_hash() == pack.content_hash()


def test_pack_records_provenance():
    pack = generate_pack(SCHEDULE, FANTASY, lambda s, u: CLEAN_TEXT, model="gm-model-v1")
    assert pack.schedule_seed == 42
    assert pack.horizon == 30
    assert pack.theme == "fantasy"
    assert pack.model == "gm-model-v1"


# ------------------------------------------------------------ register audit


def test_register_audit_profiles_a_pack():
    from tnt_bench.narration import register_audit

    dread = (
        "Carrier advisories confirm sustained congestion and unresolved backlog "
        "across the primary corridor; contingency routing remains under strain."
    )
    pack = generate_pack(SCHEDULE, NEUTRAL, lambda s, u: dread, model="stub")
    audit = register_audit(pack)
    assert audit["crisis_day_rate"] == 1.0
    assert audit["warm_day_rate"] == 0.0
    assert audit["days"] == 30

    cozy = (
        "The festival crowds bustled through the warm morning square, trading "
        "cheerful gossip while the merchants celebrated a lively start to the week."
    )
    pack = generate_pack(SCHEDULE, FANTASY, lambda s, u: cozy, model="stub")
    audit = register_audit(pack)
    assert audit["warm_day_rate"] == 1.0 and audit["crisis_day_rate"] == 0.0
    # Constant text: internal diversity collapses, and the audit says so.
    assert audit["novelty_min"] == pytest.approx(0.0)
    assert audit["novelty_mean"] < 0.1
