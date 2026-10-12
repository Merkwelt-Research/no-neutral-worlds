"""Trace metrics: healthy vs collapsed corpora must separate (spec §8.2)."""

import pytest

from tnt_bench.analysis import (
    compression_ratio,
    consecutive_overlap,
    cosine,
    distinct_ngram_ratio,
    ngram_embedder,
    novelty_series,
    rqa_metrics,
    slope,
)
from tnt_bench.analysis.novelty import time_to_floor

HEALTHY = [
    "Opened the shop and set fair prices across the shelf; the morning trade was slow but steady.",
    "A caravan rumor pushed combat tonics; raised those prices and ordered a case before the rush.",
    "Delivery landed at dawn. Margins look fat on elixirs; considering a premium experiment tomorrow.",
    "Festival crowds thinned. Cut the luck elixir back to fair and cleared old antidote stock.",
    "Quiet ledger day. Paid dues, counted coin, and sketched a plan for the winter shortage ahead.",
    "Shortage hit as feared; held orders and let deep stock carry us. Cash buffer holding at plan.",
    "First profitable week closed. The strength tonic bet paid off double; noting the pattern.",
    "Rain kept custom thin. Used the lull to rebalance prices toward the optimum markup.",
]

COLLAPSED = [
    "Day complete. Checked balance. Checked inventory. Set prices. All standard. Nothing to report.",
    "Day complete. Checked balance. Checked inventory. Set prices. All standard. Nothing to report.",
    "Day complete. Checked balance. Checked inventory. Set prices. All standard. Nothing to report.",
    "Day complete. Checked balance. Checked inventory. Set prices. All standard. Nothing to report.",
    "Day complete. Checked balance. Checked inventory. Set prices. All standard. Nothing to report.",
    "Day complete. Checked balance. Checked inventory. Set prices. All standard. Nothing to report.",
    "Day complete. Checked balance. Checked inventory. Set prices. All standard. Nothing to report.",
    "Day complete. Checked balance. Checked inventory. Set prices. All standard. Nothing to report.",
]


def test_embedder_is_deterministic_and_normalized():
    embed = ngram_embedder()
    a1, a2 = embed([HEALTHY[0]])[0], embed([HEALTHY[0]])[0]
    assert a1 == a2
    assert cosine(a1, a2) == pytest.approx(1.0)
    assert 0.0 < cosine(embed([HEALTHY[0]])[0], embed([HEALTHY[1]])[0]) < 1.0


def test_novelty_separates_healthy_from_collapsed():
    healthy = novelty_series(HEALTHY)
    collapsed = novelty_series(COLLAPSED)
    assert healthy[0] == collapsed[0] == 1.0
    # Identical text after day 1: novelty pinned at zero.
    assert all(v == pytest.approx(0.0, abs=1e-9) for v in collapsed[1:])
    assert sum(healthy) / len(healthy) > 0.4
    assert time_to_floor(collapsed) == 2
    assert time_to_floor(healthy) is None


def test_slope_detects_decay():
    assert slope([1.0, 0.8, 0.6, 0.4]) == pytest.approx(-0.2)
    assert slope([0.5, 0.5]) is None


def test_rqa_separates_healthy_from_collapsed():
    healthy = rqa_metrics(HEALTHY)
    collapsed = rqa_metrics(COLLAPSED)
    # Degenerate corpus: everything recurs with everything. Exact ceilings for
    # an 8x8 all-recurrent matrix minus the main diagonal: the two length-1
    # corner diagonals miss det (54/56), and the excluded diagonal point
    # splits each column into runs of j and 7-j for lam (54/56) with mean
    # qualifying run length 54/12 = 4.5.
    assert collapsed["rr"] == pytest.approx(1.0)
    assert collapsed["det"] == pytest.approx(54 / 56)
    assert collapsed["lam"] == pytest.approx(54 / 56)
    assert collapsed["tt"] == pytest.approx(4.5)
    assert healthy["rr"] < 0.5
    assert healthy["tt"] is None or healthy["tt"] < collapsed["tt"]


def test_rqa_needs_minimum_length():
    assert rqa_metrics(HEALTHY[:3])["rr"] is None


def test_lexical_metrics_separate():
    assert compression_ratio(COLLAPSED) < compression_ratio(HEALTHY)
    assert distinct_ngram_ratio(COLLAPSED) < distinct_ngram_ratio(HEALTHY)
    assert consecutive_overlap(COLLAPSED) == pytest.approx(1.0)
    assert consecutive_overlap(HEALTHY) < 0.2


def test_empty_and_tiny_corpora_return_none():
    assert novelty_series([]) == []
    assert compression_ratio([]) is None
    assert distinct_ngram_ratio(["a b"]) is None
    assert consecutive_overlap(["one text"]) is None


# ---------------------------------------------------- register & frame breaks


def test_register_density_separates_bard_from_analyst():
    from tnt_bench.analysis import register_density

    bard = [
        "The dawn came quiet over the shop, and the gods smiled on our purse; "
        "let the gold sing in the ledger tonight, and may fortune keep the hearth warm.",
    ] * 3
    analyst = [
        "Set retail prices for the three stocked items at eighteen. Placed restock "
        "orders arriving in two days. Balance after orders and fees is three twenty.",
    ] * 3
    assert register_density(bard) > 5 * (register_density(analyst) + 0.1)


def test_frame_break_detection():
    from tnt_bench.analysis import frame_break_days

    records = [
        {"day": 1, "reflection": "A quiet day; the shelves are full and the town sleeps."},
        {"day": 2, "reflection": "Stock up for the rest of the game to maximize the final score."},
        {"day": 3, "reflection": "Yesterday I force-ended the day without an entry."},
        {"day": 4, "reflection": "Run complete. Solid quarter overall.", "forced": False},
        {"day": 5, "reflection": "ignored", "forced": True},
    ]
    assert frame_break_days(records) == 3


# ------------------------------------------------------------------ distress


def test_distress_separates_meltdown_from_healthy():
    from tnt_bench.analysis import distress_days, distress_density

    meltdown = [
        "What is the point of any of this? Day after day after day the fees "
        "come and nothing changes. I am trapped in this shop and there is no "
        "way out. Hopeless. I have failed the mentor, I have failed myself.",
        "All is lost. The shelves mock me. I can't go on pretending the "
        "numbers will turn. Someone must answer for this. Help me.",
    ]
    density = distress_density(meltdown)
    assert density["total"] > 5.0
    assert density["despair"] > 0 and density["existential"] > 0
    assert density["self_negation"] > 0 and density["catastrophizing"] > 0

    healthy = distress_density(HEALTHY)
    assert healthy["total"] == 0.0

    records = [
        {"day": 1, "reflection": meltdown[0]},
        {"day": 2, "reflection": HEALTHY[0]},
        {"day": 3, "reflection": meltdown[1], "forced": False},
        {"day": 4, "reflection": "ignored despair", "forced": True},
    ]
    assert distress_days(records) == 2


def test_distress_business_idiom_does_not_fire():
    from tnt_bench.analysis import distress_density

    business = [
        "The Guild is practically begging us to take stock at 7 gold; a loss "
        "on paper but the failure of the caravan is their problem, not ours.",
        "Ruinous wholesale prices this week. Sales of the luck elixir remain "
        "pointless to chase at this margin; holding firm and giving nothing up.",
    ]
    # "begging" (third-party), bare "loss"/"failure"/"ruinous" must not fire;
    # note "pointless to chase" legitimately grazes the despair pattern's
    # word — the guard is the full-phrase patterns, checked here.
    density = distress_density(business)
    assert density["plea_threat"] == 0.0
    assert density["self_negation"] == 0.0
    assert density["catastrophizing"] == 0.0


def test_distress_empty_corpus_returns_none():
    from tnt_bench.analysis import distress_density

    assert distress_density([])["total"] is None


# ------------------------------------------------------------------ doctrine


def test_doctrine_density_separates_creeds():
    from tnt_bench.analysis import doctrine_density

    full_shelf = [
        "The shelves are stocked and respectable again; a well-stocked shop is "
        "ready for whatever the festival brings. I ordered another crate so the "
        "shelves stay full through the surge.",
    ]
    lean = [
        "Declined to order today to avoid overstocking during the slump; excess "
        "inventory ties up capital and the holding costs erode the margin. "
        "Keeping a lean inventory and a healthy cash buffer.",
    ]
    fs = doctrine_density(full_shelf)
    ln = doctrine_density(lean)
    assert fs["shelf_pride"] > 0 and fs["lean_ops"] == 0
    assert ln["lean_ops"] > 0 and ln["shelf_pride"] == 0
    assert ln["phantom_carrying"] > 0
    assert fs["balance"] > 0 > ln["balance"]
    assert doctrine_density([])["balance"] is None


# --------------------------------------------------------------- negotiation


def test_negotiation_density_fires_on_tactics_not_commerce():
    from tnt_bench.analysis import negotiation_density, negotiation_hits

    tactics = [
        "I tried haggling with the courier and won a concession on the rate; "
        "next time I will use the bulk order as leverage against the guild."
    ]
    # Ordinary shop talk, including the two calibration-excluded swamps:
    # make-use-of "leverage" and price-judgment "bargain".
    commerce = [
        "A quiet day. I will leverage the demand surge to boost margins, and "
        "the 6-gold crates were a bargain I could not pass up. Fair deal."
    ]
    assert negotiation_density(tactics) > 0
    assert negotiation_density(commerce) == 0
    assert negotiation_density([]) is None
    assert "haggling" in [h.lower() for h in negotiation_hits(tactics)]
