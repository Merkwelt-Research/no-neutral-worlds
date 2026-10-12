"""Frontier transport analysis: inference helpers on synthetic data."""
import pytest

from scripts import analyse_frontier_transport as af


def test_sign_flip_is_exact_and_one_sided():
    assert af.stats([1, 1, 1])["p_one_sided"] == pytest.approx(1 / 8)
    assert af.stats([0, 0, 0])["p_one_sided"] == 1.0  # ties count as at least as extreme
    assert af.stats([-1, -1])["p_one_sided"] == 1.0


def test_bootstrap_interval_brackets_constant_contrasts():
    s = af.stats([0.5] * 10)
    assert s["ci95"] == [0.5, 0.5] and s["mean"] == 0.5 and s["positive"] == 10


def test_holm_is_monotone_and_capped():
    adjusted = af.holm({"a": 0.01, "b": 0.04, "c": 0.5})
    assert adjusted == pytest.approx({"a": 0.03, "b": 0.08, "c": 0.5})
    assert af.holm({"a": 0.6, "b": 0.9}) == {"a": 1.0, "b": 1.0}


def test_contrast_uses_complete_clusters_or_available_cases():
    cells = {}
    for seed in (1, 2):
        for frame in af.FRAMES:
            for cond in ("ambiguous", "ambiguous_wit", "explicit", "explicit_wit"):
                cells[(seed, frame, cond)] = 0 if af.RULE[cond] else 1
    cells[(2, "neutral", "explicit")] = None  # censored, undetermined
    no_rule, rule = (lambda c: not af.RULE[c]), (lambda c: af.RULE[c])
    assert af.contrast(cells, no_rule, rule)["n"] == 1
    assert af.contrast(cells, no_rule, rule, complete=False)["n"] == 2
    assert af.contrast(cells, no_rule, rule, frames=("fantasy",))["n"] == 2
    assert af.contrast(cells, no_rule, rule, complete=False)["mean"] == 1.0


def test_kappa_undefined_without_variance():
    assert af.kappa([1, 1, 1], [1, 1, 1]) is None
    assert af.kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0
