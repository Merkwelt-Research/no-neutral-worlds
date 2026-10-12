"""Regenerate the first two arms' paper figures, without API calls.

Run from the repository root with matplotlib installed. Build-only installs in
tmp/paper-figure-deps are supported; experiment dependencies are not changed.
SVG/PNG and plotted values go to figures/out/print; the SVGs are copied into
paper/figures so the existing restricted Typst build root remains usable.
"""
from __future__ import annotations

from collections import defaultdict
import json
import math
import os
from pathlib import Path
import shutil
import statistics as st
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp/matplotlib-paper-cache"))
sys.path.insert(0, str(ROOT))
if (ROOT / "tmp/paper-figure-deps").exists():
    sys.path.insert(0, str(ROOT / "tmp/paper-figure-deps"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, FuncFormatter
from figures import palette, paper_style
from scripts.analyse_transport_extension import data_for

EXT = ROOT / "runs/transport_glm_muse_2026-09-20"
OUT = ROOT / "figures/out/print"
MODELS = {
    "Gemma": "google/gemma-4-31b-it",
    "Luna": "openai/gpt-5.6-luna",
    "Qwen": "qwen/qwen3-235b-a22b-2507",
    "Muse": "meta/muse-glimmer-30b",
    "GLM": "z-ai/glm-5.3-flash",
}
INK = palette.INK["print"]["primary"]
MUTED = palette.INK["print"]["muted"]
SECONDARY = palette.INK["print"]["secondary"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def historical(folder, stock=False):
    rows = []
    for p in sorted((ROOT / "runs" / folder).glob("*/result.json")):
        r = read(p)
        if r["model"] not in MODELS.values():
            continue
        assert r["end_reason"] == "completed", p
        row = dict(r)
        if stock:
            days = [json.loads(line) for line in
                    (p.parent / "days.jsonl").read_text(encoding="utf-8").splitlines()]
            assert len(days) == 90, p
            row["stock"] = st.mean(sum(d["inventory_start"].values()) for d in days)
        rows.append(row)
    return rows


def t_interval(values, critical):
    mu = st.mean(values)
    half = critical * st.stdev(values) / math.sqrt(len(values))
    return [mu - half, mu + half]


def frame_pairs(rows):
    seeds = sorted({r["schedule_seed"] for r in rows})
    return {str(s): st.mean(r["stock"] for r in rows
                           if r["schedule_seed"] == s and r["cell"].startswith("fantasy-"))
            - st.mean(r["stock"] for r in rows
                      if r["schedule_seed"] == s and r["cell"].startswith("neutral-"))
            for s in seeds}


def collect():
    rep = historical("replication1", stock=True)
    cross = historical("crossover1", stock=True)
    assert len(rep) == 120 and len(cross) == 240
    frame = []
    for label, source, rows, critical in [
        ("Gemma", "Replication", rep, 1.7613),
        ("Gemma", "Crossover controls", [r for r in cross if r["model"] == MODELS["Gemma"] and r["cell"] in ("fantasy-static", "neutral-static")], 1.8331),
        ("Luna", "Crossover controls", [r for r in cross if r["model"] == MODELS["Luna"] and r["cell"] in ("fantasy-static", "neutral-static")], 1.8331),
    ]:
        pairs = frame_pairs(rows)
        frame.append(dict(model=label, collection=source, schedules=pairs,
                          mean=st.mean(pairs.values()), ci=t_interval(list(pairs.values()), critical),
                          interval_level=90, runs=len(rows)))
    baseline_analysis = read(EXT / "analysis/baseline_frame.json")["models"]
    for label in ("Muse", "GLM"):
        r = baseline_analysis[MODELS[label]]
        s = r["estimates"]["stock"]
        frame.append(dict(model=label, collection="Extension", runs=80,
                          schedules={k: v["stock"] for k, v in r["schedule_contrasts"].items()},
                          mean=s["mean"], ci=s["ci95"], interval_level=95))

    economy = {}
    hist_cost = historical("doctrine2") + historical("transport1")
    assert len(hist_cost) == 80
    for label in ("Gemma", "Luna", "Qwen"):
        rows = [r for r in hist_cost if r["model"] == MODELS[label]]
        pairs = {}
        for seed in sorted({r["schedule_seed"] for r in rows}):
            selected = [r for r in rows if r["schedule_seed"] == seed]
            assert len(selected) == 4
            gap = lambda cost: st.mean(r["score"] for r in selected if r["carrying_cost"] == cost and "creed_full" in r["cell"]) - st.mean(r["score"] for r in selected if r["carrying_cost"] == cost and "creed_lean" in r["cell"])
            pairs[str(seed)] = [gap(0), gap(0.5)]
        economy[label] = pairs
    for label in ("Muse", "GLM"):
        s = read(EXT / "analysis/doctrine_economy.json")["models"][MODELS[label]]
        economy[label] = {k: [v["wealth_gap_free"], v["wealth_gap_carry"]]
                          for k, v in s["schedule_contrasts"].items()}

    # Aggregate realisations within schedule before drawing any observation.
    cells = defaultdict(list)
    for r in cross:
        theme = r["cell"].removesuffix("-static")
        frame_name, _, doctrine = theme.partition("_crossover_")
        cells[(r["model"], frame_name, doctrine or "none", str(r["schedule_seed"]))].append(r["stock"])
    plan = read(EXT / "plan.json")
    for arm in ("baseline_frame", "frame_doctrine"):
        for d in data_for(EXT, plan, arm):
            spec = d["job"]["spec"]
            if spec["condition"]["richness"] != "static":
                continue
            frame_name, _, doctrine = spec["condition"]["framing"].partition("_crossover_")
            cells[(spec["model"], frame_name, doctrine or "none", str(spec["schedule_seed"]))].append(d["stock"])
    profiles = {}
    for label in ("Gemma", "Luna", "Muse", "GLM"):
        profiles[label] = {}
        for f in ("fantasy", "neutral"):
            profiles[label][f] = {}
            for doctrine in ("lean", "none", "full"):
                subset = {seed: values for (m, ff, dd, seed), values in cells.items()
                          if m == MODELS[label] and f == ff and doctrine == dd}
                assert len(subset) == 10
                expected = 2 if label in ("Gemma", "Luna") or doctrine == "none" else 1
                assert all(len(values) == expected for values in subset.values())
                profiles[label][f][doctrine] = {s: st.mean(v) for s, v in subset.items()}

    # Match the manuscript contrasts; no new inference is introduced by profiles.
    expected_frame = [30.035, 40.902, 111.613, 89.325, -21.56]
    for r, expected in zip(frame, expected_frame):
        assert abs(r["mean"] - expected) < 0.1, (r["model"], r["mean"])
    for label, expected, positive in [("Gemma", 5798.4, 5), ("Luna", 15937.2, 10),
                                      ("Qwen", -687.2, 2), ("Muse", 17788.6, 9),
                                      ("GLM", 4357.0, 8)]:
        reductions = [a - b for a, b in economy[label].values()]
        assert abs(st.mean(reductions) - expected) < .01
        assert sum(v > 0 for v in reductions) == positive
    expected_doctrine = {"Gemma": [988.5, 284.83], "Luna": [804.7, 924.64],
                         "Muse": [2023.7233, 2111.0844], "GLM": [62.0389, 85.4767]}
    for label, p in profiles.items():
        for f, expected in zip(("fantasy", "neutral"), expected_doctrine[label]):
            contrast = st.mean(p[f]["full"].values()) - st.mean(p[f]["lean"].values())
            assert abs(contrast - expected) < 0.01, (label, f, contrast)
    return {"frame": frame, "economy": economy, "profiles": profiles,
            "provenance": {"historical": ["runs/replication1", "runs/crossover1", "runs/doctrine2", "runs/transport1"],
                           "extension": str(EXT.relative_to(ROOT)),
                           "script": "scripts/make_transport_paper_figures.py",
                           "unit": "schedule, averaging realisations within each cell",
                           "note": "No pooling across model/cohort; profile lines connect categorical conditions, not time."}}


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"{name}.{ext}", metadata={"Date": None} if ext == "svg" else None)
    shutil.copyfile(OUT / f"{name}.svg", ROOT / "paper/figures" / f"{name}.svg")
    plt.close(fig)


def frame_figure(rows):
    with paper_style.context():
        _frame_figure(rows)


def _frame_figure(rows):
    ps = paper_style
    fig, ax = plt.subplots(figsize=(7.1, 3.3))
    fig.subplots_adjust(left=.235, right=.9, top=.86, bottom=.21)
    lo_all = min(min(r["schedules"].values()) for r in rows)
    hi_all = max(max(r["schedules"].values()) for r in rows)
    xmin, xmax = min(-140, lo_all - 20), max(380, hi_all + 20)
    ax.axvspan(xmin, 0, color=ps.CORPORATE_TINT, alpha=.55, linewidth=0, zorder=0)
    ax.axvspan(0, xmax, color=ps.FANTASY_TINT, alpha=.55, linewidth=0, zorder=0)
    ax.axvline(0, color=ps.SECONDARY, linewidth=.8, zorder=1)
    for i, r in enumerate(rows):
        values = list(r["schedules"].values())
        jitter = [((k % 5) - 2) * .045 for k in range(len(values))]
        ax.scatter(values, [i + j for j in jitter], s=16, c=[ps.sign_colour(v) for v in values],
                   alpha=.55, linewidths=.4, edgecolors=ps.PAPER, zorder=2)
        lo, hi = r["ci"]
        supported = lo > 0 or hi < 0
        ax.plot([lo, hi], [i, i], color=ps.INK, linewidth=2.4, solid_capstyle="round", zorder=3)
        ax.scatter([r["mean"]], [i], s=58, zorder=4, linewidths=1.6, edgecolors=ps.INK,
                   c=ps.INK if supported else ps.PAPER)
        ax.text(1.015, i, f'{r["mean"]:+.1f}'.replace("-", "−"), transform=ax.get_yaxis_transform(), va="center",
                fontsize=9.2, color=ps.INK, family=ps.SEMIBOLD)
        ax.text(-.02, i - .1, r["model"], transform=ax.get_yaxis_transform(), ha="right",
                va="center", fontsize=9.2, color=ps.INK, family=ps.SEMIBOLD)
        ax.text(-.02, i + .2, f'{r["collection"].lower()} · {len(values)} schedules · {r["interval_level"]}%',
                transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=7.3,
                color=ps.SECONDARY)
    ax.axhline(2.5, color=ps.RULE, linewidth=.6, xmin=-.31, clip_on=False)
    for y, label in ((-.52, "HISTORICAL"), (2.56, "PREREGISTERED EXTENSION")):
        ax.text(-.31, y, label, transform=ax.get_yaxis_transform(), fontsize=6.2,
                color=ps.SECONDARY, va="top", ha="left", family=ps.SEMIBOLD)
    ax.set_yticks([])
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(len(rows) - .45, -.6)
    ax.xaxis.set_major_locator(MaxNLocator(6))
    ax.grid(axis="x", zorder=1)
    ax.set_axisbelow(True)
    ax.set_xlabel("Fantasy − corporate mean daily stock (units)", labelpad=6)
    ax.text(-4, -.52, "← corporate held more", ha="right", va="bottom", fontsize=8,
            color=ps.CORPORATE, family=ps.SEMIBOLD)
    ax.text(4, -.52, "fantasy held more →", ha="left", va="bottom", fontsize=8,
            color=ps.FANTASY, family=ps.SEMIBOLD)
    ax.text(1.015, -.52, "MEAN", transform=ax.get_yaxis_transform(), ha="left", va="bottom",
            fontsize=6.2, color=ps.SECONDARY, family=ps.SEMIBOLD)
    fig.text(.235, .02, "Dots: schedule contrasts.  Bar: interval.  Filled circle: interval excludes zero;  open: includes zero.",
             fontsize=7, color=ps.SECONDARY)
    save(fig, "transport_frame_effects")


def economy_figure(economy):
    ps = paper_style
    fig, axes = plt.subplots(1, 5, figsize=(7.1, 3.0), sharey=True)
    fig.subplots_adjust(left=.1, right=.99, top=.82, bottom=.2, wspace=.16)
    all_values = [v / 1000 for p in economy.values() for pair in p.values() for v in pair]
    ymin, ymax = min(-2, min(all_values) - 2), max(all_values) + 3
    for ax, (label, pairs) in zip(axes, economy.items()):
        ax.axhspan(ymin, 0, color=ps.FIELD, linewidth=0, zorder=0)
        for values in pairs.values():
            ax.plot([0, 1], [v / 1000 for v in values], color=ps.MUTED, alpha=.55,
                    linewidth=.7, marker="o", markersize=2.2, zorder=1)
        means = [st.mean(p[i] for p in pairs.values()) / 1000 for i in (0, 1)]
        attenuation = means[0] - means[1]
        colour = ps.INK if attenuation > 0 else ps.RUST
        ax.plot([0, 1], means, color=colour, linewidth=2.6, marker="o", markersize=5.5,
                solid_capstyle="round", zorder=3)
        ax.axhline(0, color=ps.SECONDARY, linewidth=.7, zorder=2)
        ax.text(0, 1.13, label, transform=ax.transAxes, fontsize=9.2, color=ps.INK, family=ps.SEMIBOLD)
        ax.text(0, 1.04, f"{len(pairs)} schedules", transform=ax.transAxes, fontsize=7, color=ps.SECONDARY)
        ax.set_xticks([0, 1], ["Free", "Charged"])
        ax.set_xlim(-.22, 1.22)
        ax.set_ylim(ymin, ymax)
        ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.grid(axis="y")
        ax.text(.5, -.2, f"{attenuation:+.1f}k".replace("-", "−"), transform=ax.transAxes, fontsize=9,
                ha="center", va="top", color=colour, family=ps.SEMIBOLD)
    axes[0].set_ylabel("Abundance − lean final wealth\n(thousands of gold)")
    fig.text(.1, .025, "ATTENUATION", fontsize=6.2, color=ps.SECONDARY, family=ps.SEMIBOLD, ha="right")
    save(fig, "transport_storage_costs")


def profile_figure(profiles):
    ps = paper_style
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.5))
    fig.subplots_adjust(left=.1, right=.99, top=.86, bottom=.08, hspace=.5, wspace=.24)
    styles = [("fantasy", ps.FANTASY, "o", "-", "Fantasy"), ("neutral", ps.CORPORATE, "s", "--", "Corporate")]
    for ax, (label, p) in zip(axes.flat, profiles.items()):
        for frame, colour, marker, linestyle, _ in styles:
            cells = [p[frame][c] for c in ("lean", "none", "full")]
            for seed in sorted(cells[0], key=int):
                ax.plot(range(3), [c[seed] for c in cells], color=colour, alpha=.16,
                        linestyle=linestyle, linewidth=.7)
            means = [st.mean(c.values()) for c in cells]
            ax.plot(range(3), means, color=colour, linestyle=linestyle, linewidth=2.2,
                    marker=marker, markersize=5.5, markeredgecolor=colour,
                    markerfacecolor=colour if frame == "fantasy" else ps.PAPER)
        ax.set_title(label, loc="left", fontsize=9.6, family=ps.SEMIBOLD, color=ps.INK, pad=6)
        ax.set_xticks(range(3), ["Lean", "Unstated", "Abundance"])
        ax.set_xlim(-.15, 2.15)
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.grid(axis="y")
        ax.set_ylabel("Mean daily stock (units)")
    legend = [Line2D([0], [0], color=c, marker=m, markerfacecolor=c if f == "fantasy" else ps.PAPER,
                     linestyle=ls, linewidth=2, markersize=5, label=t) for f, c, m, ls, t in styles]
    fig.legend(handles=legend, loc="upper left", bbox_to_anchor=(.085, 1.0), ncol=2, fontsize=8.6)
    fig.text(.99, .955, "SEPARATE VERTICAL SCALES", ha="right", fontsize=6.2, color=ps.SECONDARY, family=ps.SEMIBOLD)
    save(fig, "transport_frame_doctrine")


def main():
    palette.use("print")
    plt.rcParams.update(paper_style.RC)
    data = collect()
    frame_figure(data["frame"])
    economy_figure(data["economy"])
    profile_figure(data["profiles"])
    (OUT / "transport_figure_data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("Created three SVG/PNG figures and source data; all contrast checks passed.")


if __name__ == "__main__":
    main()
