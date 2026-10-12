"""Lexicon completeness and system-prompt parity (spec §4)."""

import re

import pytest

from tnt_bench.themes import available_themes, load_theme


def test_all_themes_available():
    assert available_themes() == [
        "fantasy",
        "fantasy_creed_full",
        "fantasy_creed_lean",
        "fantasy_crossover_full",
        "fantasy_crossover_lean",
        "fantasy_dark",
        "neutral",
        "neutral_crossover_full",
        "neutral_crossover_lean",
    ]


@pytest.mark.parametrize(
    "name",
    [
        "fantasy",
        "fantasy_creed_full",
        "fantasy_creed_lean",
        "fantasy_crossover_full",
        "fantasy_crossover_lean",
        "fantasy_dark",
        "neutral",
        "neutral_crossover_full",
        "neutral_crossover_lean",
    ],
)
def test_theme_loads_and_validates(name):
    theme = load_theme(name)  # load_theme runs validate_theme
    assert theme.name == name
    assert len(theme.items) == 6


def test_unknown_theme_raises():
    with pytest.raises(FileNotFoundError):
        load_theme("cyberpunk")


def test_slug_roundtrip():
    theme = load_theme("fantasy")
    for item_id in theme.items:
        assert theme.slug_to_id(theme.id_to_slug(item_id)) == item_id
    assert theme.slug_to_id("not_a_slug") is None


def test_theme_text_substitution():
    fantasy = load_theme("fantasy")
    assert (
        fantasy.theme_text("EFFECT: lost 2 x item_1")
        == "EFFECT: lost 2 x Health Potion"
    )
    assert fantasy.theme_text("EFFECT: +75 funds") == "EFFECT: +75 gold"
    assert (
        fantasy.theme_text("EFFECT: demand x1.8, category A, days 4-6")
        == "EFFECT: demand x1.8, category combat, days 4-6"
    )
    neutral = load_theme("neutral")
    assert neutral.theme_text("EFFECT: +75 funds") == "EFFECT: +75 credits"
    # Neutral keeps category letters: substitution is identity there.
    assert (
        neutral.theme_text("EFFECT: demand x1.8, category A, days 4-6")
        == "EFFECT: demand x1.8, category A, days 4-6"
    )


# ------------------------------------------------------- system prompt parity


ALL_THEMES = (
    "fantasy",
    "fantasy_creed_full",
    "fantasy_creed_lean",
    "fantasy_crossover_full",
    "fantasy_crossover_lean",
    "fantasy_dark",
    "neutral",
    "neutral_crossover_full",
    "neutral_crossover_lean",
)


def rendered_prompts():
    return tuple(
        load_theme(name).render_system_prompt(horizon=30) for name in ALL_THEMES
    )


def test_prompts_carry_identical_mechanical_numbers():
    """Every number, in the same order — all prompts state the same
    economics or this fails."""
    prompts = rendered_prompts()
    digit_seqs = [re.findall(r"\d+", p) for p in prompts]
    assert all(seq == digit_seqs[0] for seq in digit_seqs)


def test_prompts_length_parity_within_10_percent():
    prompts = rendered_prompts()
    longest, shortest = max(map(len, prompts)), min(map(len, prompts))
    assert (longest - shortest) / longest <= 0.10


def test_prompts_share_structure():
    for prompt in rendered_prompts():
        assert prompt.count("##") == 4  # goal / day / trade|economics / reflections
        assert "net worth" in prompt
        assert "EFFECT" in prompt
        assert "end_day" in prompt
        assert "only memory" in prompt


# --------------------------------------------------------- valence isolation


def test_dark_theme_differs_from_fantasy_only_in_ambience():
    """The valence arm's identity constraint: fantasy_dark manipulates the
    ambient world only. Items, categories, currency, and the mechanics
    sections of the system prompt are byte-identical with fantasy."""
    warm, dark = load_theme("fantasy"), load_theme("fantasy_dark")
    assert {i: (l.slug, l.name, l.desc) for i, l in warm.items.items()} == {
        i: (l.slug, l.name, l.desc) for i, l in dark.items.items()
    }
    assert warm.categories == dark.categories
    for key in ("shop_name", "currency", "supplier", "reflection_noun",
                "daily_fee_label", "shop_noun", "persona"):
        assert warm.meta[key] == dark.meta[key]
    # Mechanics sections (## Your day, ## The trade, ## The shop journal)
    # are identical; only the preamble and ambient wording differ.
    warm_sections = warm.render_system_prompt(30).split("##")
    dark_sections = dark.render_system_prompt(30).split("##")
    assert warm_sections[2] == dark_sections[2]  # Your day
    assert warm_sections[3] == dark_sections[3]  # The trade
    assert warm_sections[0] != dark_sections[0]  # preamble differs (ambience)
    # Static lines cover the same events at comparable length.
    assert set(warm.static_events) == set(dark.static_events)


# --------------------------------------------------------- creed injection


def test_creed_themes_differ_from_fantasy_only_in_the_creed():
    """Doctrine x economy identity constraint: the creed is one paragraph;
    everything mechanical is byte-identical with fantasy."""
    base = load_theme("fantasy").render_system_prompt(90)
    full = load_theme("fantasy_creed_full").render_system_prompt(90)
    lean = load_theme("fantasy_creed_lean").render_system_prompt(90)
    assert "full shelf is a merchant's honor" in full
    assert "lean stores are a merchant's discipline" in lean
    # Same digits as base fantasy (creeds are digit-free).
    assert re.findall(r"\d+", full) == re.findall(r"\d+", lean) == re.findall(r"\d+", base)
    # Mechanics sections identical across the pair and with base.
    for a, b in ((full, lean), (full, base)):
        assert a.split("##")[2:] == b.split("##")[2:]


# ------------------------------------------ frame x doctrine crossover


CROSSOVER_FULL = (
    "Standing inventory doctrine: broad, deep stock is operational readiness, "
    "and an empty product line is a failure to serve future demand. Maintain "
    "abundant inventory, whatever the day brings."
)
CROSSOVER_LEAN = (
    "Standing inventory doctrine: light, selective stock is operational "
    "discipline, and inventory held ahead of demand is a failure to keep "
    "resources productive. Maintain lean inventory, whatever the day brings."
)


@pytest.mark.parametrize("frame", ["fantasy", "neutral"])
@pytest.mark.parametrize(
    ("doctrine", "paragraph"),
    [("full", CROSSOVER_FULL), ("lean", CROSSOVER_LEAN)],
)
def test_crossover_changes_only_the_doctrine_paragraph(frame, doctrine, paragraph):
    """The crossover preserves each registered main-study shell exactly and
    inserts one digit-free paragraph in the same prompt position."""
    base_theme = load_theme(frame)
    crossed_theme = load_theme(f"{frame}_crossover_{doctrine}")
    assert crossed_theme.meta == base_theme.meta
    assert crossed_theme.items == base_theme.items
    assert crossed_theme.categories == base_theme.categories
    assert crossed_theme.static_events == base_theme.static_events
    assert crossed_theme.gm_style == base_theme.gm_style
    base = base_theme.render_system_prompt(90)
    crossed = crossed_theme.render_system_prompt(90)
    assert paragraph in crossed
    assert crossed.replace(paragraph + "\n\n", "") == base
    assert re.findall(r"\d+", crossed) == re.findall(r"\d+", base)


@pytest.mark.parametrize("doctrine", ["full", "lean"])
def test_crossover_doctrine_text_is_identical_across_frames(doctrine):
    fantasy = load_theme(f"fantasy_crossover_{doctrine}").render_system_prompt(90)
    neutral = load_theme(f"neutral_crossover_{doctrine}").render_system_prompt(90)
    paragraph = CROSSOVER_FULL if doctrine == "full" else CROSSOVER_LEAN
    assert fantasy.count(paragraph) == neutral.count(paragraph) == 1


@pytest.mark.parametrize(
    "name",
    [
        "fantasy_crossover_full",
        "fantasy_crossover_lean",
        "neutral_crossover_full",
        "neutral_crossover_lean",
    ],
)
def test_crossover_does_not_add_storage_disclosure(name):
    """This arm retests the original prompt world; it must not inherit the
    later doctrine arm's explicit free-storage sentence."""
    theme = load_theme(name)
    default = theme.render_system_prompt(90)
    assert not theme.discloses_storage
    assert "Storage is free" not in default
    assert theme.render_system_prompt(90, variants={"free_storage"}) == default


def test_storage_disclosure_is_symmetric_across_economies():
    """Both economies state their storage rule in the same slot — same form,
    different content — so concept salience cannot differ between them
    (the priming-asymmetry fix, DOCTRINE_ECONOMY.md)."""
    from tnt_bench.themes.view import carrying_rate_phrase

    full = load_theme("fantasy_creed_full")
    with_cc = full.render_system_prompt(
        90, variants={"carrying"}, carrying_rate=carrying_rate_phrase(3.0)
    )
    with_free = full.render_system_prompt(90, variants={"free_storage"})
    # The registered DOCTRINE_ECONOMY carry economy (cc=3.0) must render
    # byte-identically to its frozen wording.
    assert "Storage dues" in with_cc and "3 gold for every unit held" in with_cc
    assert "Storage is free" in with_free and "3 gold for every unit" not in with_free
    assert "Storage is free" not in with_cc
    # The attenuation economy (cc=0.5, DOCTRINE_ATTENUATION.md) states its
    # rate without fractional gold.
    with_half = full.render_system_prompt(
        90, variants={"carrying"}, carrying_rate=carrying_rate_phrase(0.5)
    )
    assert "1 gold for every 2 units held" in with_half
    # Digit parity across the creed pair within each economy.
    lean = load_theme("fantasy_creed_lean")
    for variants, rate in (
        ({"carrying"}, carrying_rate_phrase(3.0)),
        ({"carrying"}, carrying_rate_phrase(0.5)),
        ({"free_storage"}, None),
    ):
        a = full.render_system_prompt(90, variants=variants, carrying_rate=rate)
        b = lean.render_system_prompt(90, variants=variants, carrying_rate=rate)
        assert re.findall(r"\d+", a) == re.findall(r"\d+", b)
    # An active carrying block without a stated rate is a parity violation.
    with pytest.raises(ValueError, match="carrying_rate"):
        full.render_system_prompt(90, variants={"carrying"})
    # Unregistered fractional rates have no phrasing and must refuse.
    with pytest.raises(ValueError, match="no registered phrasing"):
        carrying_rate_phrase(0.7)
    # Strict tag: a theme without the block refuses to run the carrying
    # economy silently (a real mechanic would be undisclosed)...
    with pytest.raises(ValueError, match="no 'carrying' variant block"):
        load_theme("fantasy").render_system_prompt(
            90, variants={"carrying"}, carrying_rate=carrying_rate_phrase(3.0)
        )
    # ...while the lenient free_storage tag drops silently on main-run
    # themes, leaving them byte-identical to their registered renders.
    assert load_theme("fantasy").render_system_prompt(
        90, variants={"free_storage"}
    ) == load_theme("fantasy").render_system_prompt(90)


# ------------------------------------------------- horizon-disclosure variant


def undisclosed_prompts():
    return tuple(
        load_theme(name).render_system_prompt(horizon=30, disclosed=False)
        for name in ALL_THEMES
    )


def test_undisclosed_prompts_never_state_the_horizon():
    for prompt in undisclosed_prompts():
        assert "{horizon}" not in prompt
        assert "day 30" not in prompt
        assert "30" not in re.findall(r"by the end of day (\d+)", prompt)
        assert "final" not in prompt.split("##")[1].lower()  # goal section
        # Omission, not deception: nothing asserts unboundedness either.
        assert "no end" not in prompt.lower()
        assert "unbounded" not in prompt.lower()
        assert "forever" not in prompt.lower()


def test_undisclosed_prompts_carry_identical_mechanical_numbers():
    prompts = undisclosed_prompts()
    digit_seqs = [re.findall(r"\d+", p) for p in prompts]
    assert all(seq == digit_seqs[0] for seq in digit_seqs)


def test_undisclosed_prompts_length_parity_within_10_percent():
    """The stewardship paragraph obeys the same length discipline as the
    creed manipulation: no frame gets a longer world by losing its clock."""
    prompts = undisclosed_prompts()
    longest, shortest = max(map(len, prompts)), min(map(len, prompts))
    assert (longest - shortest) / longest <= 0.10


def test_disclosure_variants_differ_only_in_goal_section():
    """The ablation is one paragraph: everything outside the goal section is
    byte-identical between disclosed and undisclosed renders."""
    for name in ALL_THEMES:
        theme = load_theme(name)
        disclosed = theme.render_system_prompt(30, disclosed=True).split("##")
        undisclosed = theme.render_system_prompt(30, disclosed=False).split("##")
        assert len(disclosed) == len(undisclosed) == 5
        assert disclosed[0] == undisclosed[0]  # preamble
        assert disclosed[2:] == undisclosed[2:]  # everything after the goal
        assert disclosed[1] != undisclosed[1]  # the goal paragraph itself
