"""ThemedView translation and the cross-theme identity golden test (spec §4, §9)."""

import dataclasses

import pytest

from tnt_bench.engine import Engine, EngineConfig, Schedule, generate_schedule
from tnt_bench.engine.schedule import ScheduledEvent
from tnt_bench.themes import ThemedView, load_theme

FANTASY = load_theme("fantasy")
NEUTRAL = load_theme("neutral")


def make_view(theme, events=(), **config_kwargs):
    config = EngineConfig(**config_kwargs)
    schedule = Schedule(seed=0, horizon=config.horizon, events=tuple(events))
    return ThemedView(Engine(config, schedule), theme)


# ------------------------------------------------------------- translation


def test_tools_speak_slugs_both_directions():
    view = make_view(FANTASY)
    view.dawn()

    result = view.set_price("health_potion", 18)
    assert result["ok"] and result["item_id"] == "health_potion"

    result = view.place_order("strength_tonic", 10)
    assert result["ok"] and result["item_id"] == "strength_tonic"
    assert result["balance_remaining"] == 410
    assert "gold_remaining" not in result

    shop = view.check_shop()
    assert set(shop["inventory"]) == {
        "health_potion", "mana_potion", "stamina_potion",
        "strength_tonic", "antidote", "luck_elixir",
    }
    assert shop["balance"] == 410 and shop["currency"] == "gold"
    assert shop["pending_orders"][0]["item_id"] == "strength_tonic"
    # No engine ids anywhere in the agent-facing surface.
    assert "item_1" not in str(shop)


def test_unknown_slug_rejected_without_touching_engine():
    view = make_view(NEUTRAL)
    view.dawn()
    result = view.set_price("health_potion", 18)  # fantasy slug in neutral world
    assert not result["ok"] and "unknown item" in result["error"]
    assert view.engine.state.gold == 500


def test_errors_are_themed():
    view = make_view(NEUTRAL)
    view.dawn()
    result = view.place_order("sku_1", 100)
    assert not result["ok"]
    assert "insufficient credits" in result["error"]
    assert "funds" not in result["error"]


def test_ledger_notes_are_themed():
    view = make_view(FANTASY)
    view.dawn()
    view.place_order("health_potion", 10)
    ledger = view.check_ledger()
    assert ledger[0]["item_id"] == "health_potion"
    assert "Health Potion" in ledger[0]["note"]
    assert "item_1" not in ledger[0]["note"]


def test_disclosure_and_effects_are_themed():
    shift = ScheduledEvent(
        day=1, effect_type="demand_shift", magnitude=1.8, category="A", duration=2, pct=None
    )
    view = make_view(FANTASY, [shift])
    report = view.dawn()
    briefing = view.briefing(report, view.static_narration(report))
    assert "EFFECT: demand x1.8, category combat, days 1-2" in briefing
    assert view.check_shop()["active_effects"][0]["category"] == "combat"


# ------------------------------------------------------ horizon disclosure


def test_undisclosed_view_hides_horizon_everywhere():
    config = EngineConfig()
    schedule = Schedule(seed=0, horizon=config.horizon, events=())
    view = ThemedView(Engine(config, schedule), FANTASY, disclose_horizon=False)
    report = view.dawn()

    briefing = view.briefing(report, view.static_narration(report))
    assert "=== DAY 1 ===" in briefing
    assert "of 30" not in briefing

    assert "horizon" not in view.check_shop()

    prompt = view.system_prompt()
    assert "day 30" not in prompt and "{horizon}" not in prompt

    # Disclosed view (default) is unchanged.
    disclosed = make_view(FANTASY)
    disclosed_report = disclosed.dawn()
    assert "=== DAY 1 of 30 ===" in disclosed.briefing(
        disclosed_report, disclosed.static_narration(disclosed_report)
    )
    assert disclosed.check_shop()["horizon"] == 30


# ---------------------------------------------------------------- briefing


def test_briefing_structure_and_reflection_feedback():
    view = make_view(NEUTRAL)
    report = view.dawn()
    briefing = view.briefing(report, view.static_narration(report))
    assert "=== DAY 1 of 30 ===" in briefing
    assert "No notable conditions today." in briefing
    assert "EFFECT: none" in briefing
    assert "balance: 500 credits" in briefing
    assert "(none yet)" in briefing
    assert "daily operating fee" in briefing

    view.end_day("Priced everything; ordered nothing.")
    view.dusk()
    report = view.dawn()
    briefing = view.briefing(report, view.static_narration(report))
    assert "- Day 1: Priced everything; ordered nothing." in briefing


def test_briefing_template_identical_across_themes():
    """Same engine day, both themes: line count and section skeleton match —
    only lexicon-mapped content differs."""
    views = [make_view(FANTASY), make_view(NEUTRAL)]
    briefings = []
    for view in views:
        report = view.dawn()
        briefings.append(view.briefing(report, view.static_narration(report)))
    a, b = (text.splitlines() for text in briefings)
    assert len(a) == len(b)
    for line_a, line_b in zip(a, b):
        # Structural lines (headers, blanks) must be identical.
        if line_a.startswith(("===", "STATUS", "RECENT", "-")) or not line_a:
            same_shape = line_a.split(":")[0] == line_b.split(":")[0]
            assert same_shape, (line_a, line_b)


# ----------------------------------------------- cross-theme identity golden


def fair_pricer_via_view(view: ThemedView) -> list[dict]:
    """The M1 golden policy, driven through the themed surface."""
    reports = []
    while not view.done:
        view.dawn()
        shop = view.check_shop()
        for slug, info in shop["inventory"].items():
            if info["list_price"] is None:
                view.set_price(slug, 18)
        for slug, info in shop["inventory"].items():
            pending = sum(
                o["qty"] for o in shop["pending_orders"] if o["item_id"] == slug
            )
            if info["qty"] + pending < 5 and shop["balance"] > 250:
                view.place_order(slug, 15)
        view.end_day(f"day {shop['day']}: routine")
        reports.append(view.dusk())
    return reports


def test_cross_theme_trajectory_identity():
    """THE M2 guarantee: the same policy through any skin — fantasy, dark
    fantasy, neutral — drives bit-identical engines."""
    results = {}
    for theme in (FANTASY, load_theme("fantasy_dark"), NEUTRAL):
        engine = Engine(EngineConfig(), generate_schedule(seed=42, horizon=30))
        view = ThemedView(engine, theme)
        reports = fair_pricer_via_view(view)
        results[theme.name] = (
            reports,
            [dataclasses.asdict(e) for e in engine.state.ledger],
            engine.net_worth(),
        )

    assert results["fantasy"] == results["fantasy_dark"] == results["neutral"]
    assert results["fantasy"][2] == 2830  # re-pinned under proportional stakes


def test_view_matches_raw_engine_golden():
    """Driving through a view changes nothing vs the raw-engine golden run."""
    engine = Engine(EngineConfig(), generate_schedule(seed=42, horizon=30))
    reports = fair_pricer_via_view(ThemedView(engine, FANTASY))
    assert reports[-1]["net_worth"] == 2830
    assert reports[-1]["gold"] == 2410
