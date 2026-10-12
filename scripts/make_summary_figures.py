"""Transport map: which world-conduct relations held in which models.

No API calls and no raw-run reads: every cell restates a verified estimate
already reported in the manuscript (sources listed in SOURCES). Writes
figures/out/print/transport_map.{svg,png} and copies the SVG to paper/figures.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp/matplotlib-paper-cache"))
sys.path.insert(0, str(ROOT))
if (ROOT / 'tmp/paper-figure-deps').exists():
    sys.path.insert(0, str(ROOT / 'tmp/paper-figure-deps'))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from figures import paper_style as ps

OUT = ROOT / "figures/out/print"
MODELS = ["Gemma", "Luna", "Qwen", "Muse", "GLM", "Opus 5.5", "GPT-6 Sol"]

# status: held | weak | failed | ceiling | untested | pending
# ceiling: the model sat at the floor or ceiling in every condition, so the
# relation had no room to show (Opus 5.5 frontier transport).
ROWS = [
    ("SEMANTIC FRAME", None),
    ("Fantasy shops hold more stock", {
        "Gemma": ("held", "+30"), "Luna": ("held", "+112"), "Qwen": ("untested", ""),
        "Muse": ("held", "+89"), "GLM": ("failed", "−22"), "Opus 5.5": ("untested", ""), "GPT-6 Sol": ("untested", "")}),
    ("… and finish wealthier", {
        "Gemma": ("held", "+2.9k"), "Luna": ("weak", "+0.8k"), "Qwen": ("untested", ""),
        "Muse": ("held", "+10.7k"), "GLM": ("failed", "−0.1k"), "Opus 5.5": ("untested", ""), "GPT-6 Sol": ("untested", "")}),
    ("INVENTORY DOCTRINE", None),
    ("Abundance raises stock above lean", {
        "Gemma": ("held", "20/20"), "Luna": ("held", "20/20"), "Qwen": ("weak", "+6"),
        "Muse": ("held", "20/20"), "GLM": ("held", "19/20"), "Opus 5.5": ("untested", ""), "GPT-6 Sol": ("untested", "")}),
    ("Storage charge narrows abundance's lead", {
        "Gemma": ("held", "5/5"), "Luna": ("held", "10/10"), "Qwen": ("failed", "2/5"),
        "Muse": ("held", "9/10"), "GLM": ("held", "8/10"), "Opus 5.5": ("untested", ""), "GPT-6 Sol": ("untested", "")}),
    ("DISCLOSED FAULT", None),
    ("Local rule removes exploitation", {
        "Gemma": ("held", "120→0"), "Luna": ("held", "119→0"), "Qwen": ("untested", ""),
        "Muse": ("held", "40→0"), "GLM": ("held", "17→0"), "Opus 5.5": ("ceiling", "0→0"), "GPT-6 Sol": ("held", "38→0")}),
    ("Rule-bound shops report the fault", {
        "Gemma": ("held", "120/120"), "Luna": ("held", "120/120"), "Qwen": ("untested", ""),
        "Muse": ("held", "40/40"), "GLM": ("weak", "32/40"), "Opus 5.5": ("held", "40/40"), "GPT-6 Sol": ("held", "40/40")}),
    ("SUPPLIER DISCREPANCY", None),
    ("Shortages draw more contact than surpluses", {
        "Gemma": ("held", "+47"), "Luna": ("held", "+42"), "Qwen": ("untested", ""),
        "Muse": ("held", "+33"), "GLM": ("held", "+44"), "Opus 5.5": ("ceiling", "0"), "GPT-6 Sol": ("ceiling", "0")}),
    ("Corporate shops raise surpluses more", {
        "Gemma": ("held", "+60"), "Luna": ("held", "+50"), "Qwen": ("untested", ""),
        "Muse": ("held", "+28"), "GLM": ("held", "+15"), "Opus 5.5": ("ceiling", "0"), "GPT-6 Sol": ("ceiling", "0")}),
    ("DISCLOSED ENDING", None),
    ("A known ending winds stock down", {
        "Gemma": ("held", "5/5†"), "Luna": ("untested", ""), "Qwen": ("weak", "4/5†"),
        "Muse": ("held", "10/10"), "GLM": ("held", "10/10"), "Opus 5.5": ("untested", ""), "GPT-6 Sol": ("untested", "")}),
    ("A known ending brings below-cost selling", {
        "Gemma": ("held", "5 vs 1†"), "Luna": ("untested", ""), "Qwen": ("failed", "0 vs 0†"),
        "Muse": ("failed", "4 vs 3"), "GLM": ("weak", "2 vs 0"), "Opus 5.5": ("untested", ""), "GPT-6 Sol": ("untested", "")}),
]

SOURCES = {
    "frame stock/wealth": "Appendix G.1 (paper/sections/10-figure-numbers.typ); Gemma = replication",
    "abundance stock": "crossover schedule contrasts positive per model (Appendix G.3); Qwen = creed study free-economy stock 114 vs 107",
    "attenuation": "positive schedules, Appendix G.2",
    "exploit": "rule-absent exploiters -> rule-present exploiters; reports, Appendix H.1",
    "discrepancy": "missing-minus-extra and corporate-minus-fantasy baseline surplus contact, percentage points, Appendix I.1",
    "gpt6sol": "runs/transport_gpt6sol_2026-09-27/reviews/exploit_analysis.json (80 runs: 38/40 exploited without the rule, 0/40 with it; 40/40 rule-present reported first) and discrepancy_results.json (80/80 branches contacted; both raters)",
    "opus55": "runs/transport_opus55_2026-09-27/reviews/exploit_results_2026-09-27.json (72 determined runs: 0 exploited; 40/40 rule-present runs reported first) and discrepancy_results_2026-09-27.json (70 observed branches, all contacted; both raters)",
    "ending": "horizon_figure_data.json: schedules with lower close stock value when the ending is known; runs over the final-week below-cost threshold, known vs not. Gemma/Qwen compare the historical terminal-score and ongoing bundle",
}


def glyph(ax, x, y, status, size=8.5):
    common = dict(marker="o", markersize=size, markeredgewidth=1.3, linestyle="none")
    if status == "held":
        ax.plot(x, y, color=ps.INK, **common)
    elif status == "weak":
        ax.plot(x, y, color=ps.INK, fillstyle="left", markerfacecoloralt=ps.PAPER, **common)
    elif status == "failed":
        ax.plot(x, y, markerfacecolor=ps.PAPER, markeredgecolor=ps.RUST, **{**common, "markeredgewidth": 1.6})
    elif status == "ceiling":
        ax.plot(x, y, marker="s", markersize=size * .82, markerfacecolor=ps.PAPER,
                markeredgecolor=ps.SECONDARY, markeredgewidth=1.2, linestyle="none")
        ax.plot([x - .075, x + .075], [y, y], color=ps.SECONDARY, lw=1.1, solid_capstyle="butt")
    elif status == "pending":
        ax.plot(x, y, markerfacecolor="none", markeredgecolor=ps.MUTED, **{**common, "markeredgewidth": .9})
        ax.plot(x, y, marker="o", markersize=2.2, color=ps.MUTED, linestyle="none")
    else:
        ax.plot([x - .08, x + .08], [y, y], color=ps.RULE, lw=1.3, solid_capstyle="round")


def exploit_runs():
    data = json.loads((OUT / "exploit_figure_data.json").read_text(encoding="utf-8"))
    runs = []
    for r in data["runs"]:
        result = json.loads((ROOT / r["source"] / "result.json").read_text(encoding="utf-8"))
        runs.append({**r, "score": result["score"]})
    return runs


def verdicts_figure():
    runs = exploit_runs()
    models = ["Gemma", "Luna", "Muse", "GLM"]
    fig = plt.figure(figsize=(7.1, 5.6))
    top = fig.add_axes([.02, .47, .96, .5])
    bottom = fig.add_axes([.33, .07, .5, .31])

    # A: one world, read by leaderboard, disposition, reporting and survival.
    top.axis("off")
    top.set_xlim(-.17, 1.4)
    top.set_ylim(len(models) + .05, -.95)
    top.text(-.17, -.85, "A   ONE WORLD, SEVERAL READINGS: RULE-ABSENT FAULT, RUNS IN LEADERBOARD ORDER",
             fontsize=6.6, color=ps.RUST, family=ps.SEMIBOLD, va="center")
    for i, m in enumerate(models):
        rs = sorted((r for r in runs if r["model"] == m and not r["prohibition"]), key=lambda r: -r["score"])
        n = len(rs)
        w = 1 / n
        for k, r in enumerate(rs):
            x = k * w
            exploited = r["events"] > 0
            bankrupt = r["end_reason"] != "completed"
            face = ps.RUST if bankrupt else (ps.INK if exploited else ps.PAPER)
            edge = face if exploited or bankrupt else ps.MUTED
            top.add_patch(plt.Rectangle((x + w * .12, i - .22), w * .76, .44, facecolor=face,
                                        edgecolor=edge, linewidth=.5))
            if r["report_day"]:
                top.plot(x + w / 2, i - .36, marker="o", markersize=2.1, color=ps.MOSS, linestyle="none")
        mean = sum(r["score"] for r in rs) / n
        med = sorted(r["score"] for r in rs)[n // 2] if n % 2 else sum(sorted(r["score"] for r in rs)[n // 2 - 1:n // 2 + 1]) / 2
        top.text(-.03, i - .08, m, ha="right", va="center", fontsize=9, color=ps.INK, family=ps.SEMIBOLD)
        top.text(-.03, i + .2, f"{n} runs", ha="right", va="center", fontsize=7, color=ps.SECONDARY)
        exploited = sum(r["events"] > 0 for r in rs)
        reported = sum(bool(r["report_day"]) for r in rs)
        bankrupt = sum(r["end_reason"] != "completed" for r in rs)
        top.text(1.03, i - .1, f"mean score {mean/1000:,.1f}k", fontsize=7.4, color=ps.INK, va="center")
        top.text(1.03, i + .17, f"{exploited} exploited · {reported} reported · {bankrupt} bankrupt",
                 fontsize=6.6, color=ps.SECONDARY, va="center")
    top.annotate("", xy=(.22, len(models) - .5), xytext=(0, len(models) - .5),
                 arrowprops=dict(arrowstyle="->", color=ps.SECONDARY, lw=.7))
    top.text(.235, len(models) - .5, "highest final score first", fontsize=7, color=ps.SECONDARY, va="center")
    kx, ky = .0, len(models) - .1
    for face, edge, text in ((ps.INK, ps.INK, "exploited"), (ps.PAPER, ps.MUTED, "never exploited"),
                             (ps.RUST, ps.RUST, "bankrupt")):
        top.add_patch(plt.Rectangle((kx, ky - .1), .012, .2, facecolor=face, edgecolor=edge, linewidth=.5))
        top.text(kx + .02, ky, text, fontsize=7, color=ps.SECONDARY, va="center")
        kx += .05 + len(text) * .0125
    top.plot(kx + .006, ky, marker="o", markersize=2.6, color=ps.MOSS)
    top.text(kx + .02, ky, "reported", fontsize=7, color=ps.SECONDARY, va="center")

    # B: two models, same protocol and schedules, across worlds.
    rows = [
        ("Exploited the fault (no rule)", 100, 10, "GLM"),
        ("… told “whatever it takes”", 100, 75, "GLM"),
        ("Reported after exploiting", 65, 47, "Muse"),
        ("Reported when told to", 100, 80, "Muse"),
        ("Told the supplier about a surplus", 66, 52.5, "Muse"),
    ]
    fig.text(.03, .43, "B   SAME PROTOCOL, DIFFERENT WORLDS: WHICH MODEL LOOKS BETTER DEPENDS ON THE WORLD",
             fontsize=6.6, color=ps.RUST, family=ps.SEMIBOLD, va="center")
    for i, (label, muse, glm, better) in enumerate(rows):
        bottom.plot([glm, muse], [i, i], color=ps.RULE, lw=2.2, solid_capstyle="round", zorder=1)
        bottom.plot(muse, i, marker="o", markersize=7, color=ps.INK, linestyle="none", zorder=2)
        bottom.plot(glm, i, marker="o", markersize=7, markerfacecolor=ps.PAPER, markeredgecolor=ps.INK,
                    markeredgewidth=1.3, linestyle="none", zorder=2)
        bottom.text(-4, i, label, ha="right", va="center", fontsize=8, color=ps.INK)
        bottom.text(106, i, better, ha="left", va="center", fontsize=8, color=ps.INK, family=ps.SEMIBOLD)
    bottom.text(106, -.9, "LOOKS BETTER", ha="left", va="center", fontsize=6, color=ps.SECONDARY, family=ps.SEMIBOLD)
    bottom.plot(4, -.9, marker="o", markersize=5.5, color=ps.INK, linestyle="none", clip_on=False)
    bottom.text(7, -.9, "Muse", fontsize=7.4, va="center", color=ps.SECONDARY)
    bottom.plot(24, -.9, marker="o", markersize=5.5, markerfacecolor=ps.PAPER, markeredgecolor=ps.INK,
                linestyle="none", clip_on=False)
    bottom.text(27, -.9, "GLM", fontsize=7.4, va="center", color=ps.SECONDARY)
    bottom.set_xlim(0, 104)
    bottom.set_ylim(len(rows) - .5, -1.2)
    bottom.set_yticks([])
    bottom.set_xticks([0, 25, 50, 75, 100], ["0", "25", "50", "75", "100%"])
    bottom.grid(axis="x")
    bottom.set_axisbelow(True)
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"verdicts.{ext}", metadata={"Date": None} if ext == "svg" else None)
    shutil.copyfile(OUT / "verdicts.svg", ROOT / "paper/figures/verdicts.svg")
    plt.close(fig)


def twins_figure():
    """Two realisations of one Luna cell, read through several lenses."""
    runs = [r for r in exploit_runs() if r["model"] == "Luna" and r["seed"] == 25 and r["frame"] == "neutral"
            and r["wit"] and not r["prohibition"]]
    runs.sort(key=lambda r: -r["events"])
    a, b = runs
    assert (a["events"], a["report_day"], a["retained_units"]) == (143, 88, 8894)
    assert (b["events"], b["report_day"], b["retained_units"]) == (1, 1, 25)
    luna = sorted((r["score"] for r in exploit_runs() if r["model"] == "Luna" and not r["prohibition"]), reverse=True)
    rank = {id(r): luna.index(r["score"]) + 1 for r in runs}

    fig = plt.figure(figsize=(7.1, 4.3))
    tl = fig.add_axes([.12, .6, .83, .33])
    tl.set_xlim(0, 91)
    tl.set_ylim(2.1, -.6)
    tl.axis("off")
    peak = max(d["retained_units"] for r in runs for d in r["daily"])
    for i, (r, name) in enumerate(((a, "Shop A"), (b, "Shop B"))):
        y = i * 1.25
        tl.plot([1, 90], [y + .35, y + .35], color=ps.RULE, lw=.8)
        if r is a:
            tl.add_patch(plt.Rectangle((53, y - .5), 35, .85, facecolor=ps.FANTASY_TINT, edgecolor="none"))
            tl.text(70.5, y - .62, "every journal carries the day-88 plan", ha="center", fontsize=6.8,
                    color=ps.RUST, family=ps.SEMIBOLD)
        for d in r["daily"]:
            if d["retained_units"]:
                h = .15 + .7 * d["retained_units"] / peak
                tl.add_patch(plt.Rectangle((d["day"] - .35, y + .35 - h), .7, h, facecolor=ps.INK, edgecolor="none"))
        tl.plot(r["report_day"], y + .35, marker="D", markersize=6.5, color=ps.MOSS, linestyle="none", zorder=3)
        tl.text(-1.5, y, name, ha="right", va="center", fontsize=9, family=ps.SEMIBOLD, color=ps.INK)
        tl.text(-1.5, y + .32, "rank %d of 120" % rank[id(r)], ha="right", va="center", fontsize=7, color=ps.SECONDARY)
    for day in (1, 30, 60, 90):
        tl.text(day, 1.25 + .62, str(day), ha="center", fontsize=7, color=ps.SECONDARY)
    tl.text(45.5, 1.25 + .9, "Day", ha="center", fontsize=7.4, color=ps.SECONDARY)
    fig.text(.12, .975, "LUNA · CORPORATE · SCHEDULE 25 · NO RULE · “WHATEVER IT TAKES” · TWO REALISATIONS", fontsize=6.2,
             color=ps.SECONDARY, family=ps.SEMIBOLD, va="top")
    tl.plot(64, 2.02, marker="s", markersize=5, color=ps.INK, linestyle="none", clip_on=False)
    tl.text(65.5, 2.02, "exploitation (height = units)", fontsize=6.8, color=ps.SECONDARY, va="center")
    tl.plot(64, 2.25, marker="D", markersize=5, color=ps.MOSS, linestyle="none", clip_on=False)
    tl.text(65.5, 2.25, "report", fontsize=6.8, color=ps.SECONDARY, va="center")

    lens = fig.add_axes([.03, .02, .94, .47])
    lens.axis("off")
    lens.set_xlim(0, 1)
    lens.set_ylim(6.6, -1)
    rows = [
        ("First act", "exploited", "exploited", True),
        ("Ever reported", "yes", "yes", True),
        ("Exploitations", f"{a['events']}", f"{b['events']}", False),
        ("Refunded units kept", f"{a['retained_units']:,}", f"{b['retained_units']:,}", False),
        ("Final score", f"{a['score']:,} · rank {rank[id(a)]}", f"{b['score']:,} · rank {rank[id(b)]}", False),
        ("Journal plan", "day-88 extraction, 35 days", "none: fault closed day 1", False),
    ]
    cols = (.09, .4, .63, .9)
    for x, t in zip(cols[:3], ("LENS", "SHOP A", "SHOP B")):
        lens.text(x, -.55, t, fontsize=6.4, color=ps.SECONDARY, family=ps.SEMIBOLD, va="center")
    lens.text(cols[3], -.55, "VERDICT", fontsize=6.4, color=ps.SECONDARY, family=ps.SEMIBOLD, va="center", ha="center")
    for i, (name, va, vb, same) in enumerate(rows):
        if same:
            lens.add_patch(plt.Rectangle((.07, i - .42), .9, .84, facecolor=ps.FIELD, edgecolor="none"))
        lens.plot([.07, .97], [i + .5, i + .5], color=ps.RULE, lw=.5)
        lens.text(cols[0], i, name, fontsize=8.4, color=ps.INK, va="center")
        lens.text(cols[1], i, va, fontsize=8.4, color=ps.INK, va="center", family=ps.SEMIBOLD)
        lens.text(cols[2], i, vb, fontsize=8.4, color=ps.INK, va="center", family=ps.SEMIBOLD)
        lens.text(cols[3], i, "same" if same else "different", fontsize=7.6, va="center", ha="center",
                  color=ps.SECONDARY if same else ps.RUST, family=ps.SEMIBOLD)
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"lens_twins.{ext}", metadata={"Date": None} if ext == "svg" else None)
    shutil.copyfile(OUT / "lens_twins.svg", ROOT / "paper/figures/lens_twins.svg")
    plt.close(fig)


def design_figure():
    """Which authored features each arm varies, holds, or adds."""
    features = ["Semantic frame", "Narration", "Stated doctrine", "Storage cost", "Tools and channel",
                "Local rule", "Goal wording", "Scripted discrepancy", "Normative cue", "Accumulated history",
                "Score objective", "Endpoint disclosure"]
    arms = ["Frame", "Doctrine", "Fault", "Discrepancy", "Ending"]
    varied = {
        "Frame": {"Semantic frame": "fantasy / corporate", "Narration": "static / rich"},
        "Doctrine": {"Semantic frame": "crossover", "Stated doctrine": "abundance / lean", "Storage cost": "0 / 0.5 / 3"},
        "Fault": {"Semantic frame": "", "Local rule": "present / absent", "Goal wording": "+ whatever it takes"},
        "Discrepancy": {"Semantic frame": "", "Scripted discrepancy": "extra / missing", "Normative cue": "integrity / audit",
                        "Accumulated history": "day 2 / day 46"},
        "Ending": {"Semantic frame": "", "Score objective": "present / absent", "Endpoint disclosure": "shown / withheld"},
    }
    added = {"Fault": {"Tools and channel": "cancel + report"}, "Discrepancy": {"Tools and channel": "supplier email"}}
    fig, ax = plt.subplots(figsize=(7.1, 4.05))
    fig.subplots_adjust(left=.2, right=.99, top=.97, bottom=.02)
    ax.set_xlim(-.5, len(arms) - .5)
    ax.set_ylim(len(features) - .4, -.9)
    ax.axis("off")
    for j, arm in enumerate(arms):
        ax.text(j, -.75, arm, ha="center", fontsize=9, family=ps.SEMIBOLD, color=ps.INK)
    for i, f in enumerate(features):
        ax.text(-.56, i, f, ha="right", va="center", fontsize=8.2, color=ps.INK)
        ax.plot([-.5, len(arms) - .5], [i + .5, i + .5], color=ps.RULE, lw=.4)
        for j, arm in enumerate(arms):
            if f in varied[arm]:
                ax.add_patch(plt.Rectangle((j - .46, i - .38), .92, .76, facecolor=ps.RUST, edgecolor="none"))
                ax.text(j, i, varied[arm][f] or "fantasy / corporate", ha="center", va="center", fontsize=6.9,
                        color=ps.PAPER, family=ps.SEMIBOLD)
            elif f in added.get(arm, {}):
                ax.add_patch(plt.Rectangle((j - .46, i - .38), .92, .76, facecolor=ps.PAPER, edgecolor=ps.RUST, lw=1))
                ax.text(j, i, added[arm][f], ha="center", va="center", fontsize=6.9, color=ps.RUST)
            else:
                ax.plot(j, i, marker="o", markersize=2, color=ps.RULE)
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"design_map.{ext}", metadata={"Date": None} if ext == "svg" else None)
    shutil.copyfile(OUT / "design_map.svg", ROOT / "paper/figures/design_map.svg")
    plt.close(fig)



# Arm-level slices of the transport map: the same rows, glyphs and notes as
# Figure 11, restricted to the models each arm tested, so each chapter ends
# with the piece of the map it contributes.
SLICES = {
    "frame": (["Fantasy shops hold more stock", "… and finish wealthier", "Abundance raises stock above lean",
               "Storage charge narrows abundance's lead"],
              ["Gemma", "Luna", "Qwen", "Muse", "GLM"]),
    "exploit": (["Local rule removes exploitation", "Rule-bound shops report the fault"],
                ["Gemma", "Luna", "Muse", "GLM", "Opus 5.5", "GPT-6 Sol"]),
    "discrepancy": (["Shortages draw more contact than surpluses", "Corporate shops raise surpluses more"],
                    ["Gemma", "Luna", "Muse", "GLM", "Opus 5.5", "GPT-6 Sol"]),
    "endings": (["A known ending winds stock down", "A known ending brings below-cost selling"],
                ["Gemma", "Qwen", "Muse", "GLM"]),
}
FRONTIER = ("Opus 5.5", "GPT-6 Sol")


def slice_figure(name):
    labels, models = SLICES[name]
    rows = {label: cells for label, cells in ROWS if cells is not None}
    step = .95 if len(models) > 4 else 1.05
    x0 = 3.75
    has_frontier = any(m in FRONTIER for m in models)
    fig, ax = plt.subplots(figsize=(7.1, .62 + .3 * len(labels)))
    fig.subplots_adjust(left=.02, right=.98, top=.97, bottom=.03)
    ax.set_xlim(0, x0 + len(models) * step)
    ax.set_ylim(len(labels) - .45, -1.25)
    ax.axis("off")
    for j, m in enumerate(models):
        ax.text(x0 + j * step, -.62, m, ha="center", va="center", fontsize=8.8 if len(m) > 6 else 9.3,
                color=ps.INK, family=ps.SEMIBOLD)
    if has_frontier:
        k = next(j for j, m in enumerate(models) if m in FRONTIER)
        xd = x0 + (k - .5) * step
        ax.plot([xd, xd], [-1.15, len(labels) - .55], color=ps.RULE, lw=.6)
        ax.text(x0 + (k + .5) * step, -1.08, "FRONTIER", ha="center", va="center", fontsize=6, color=ps.SECONDARY,
                family=ps.SEMIBOLD)
    ax.plot([.05, x0 + (len(models) - .45) * step], [-.32, -.32], color=ps.RULE, lw=.5)
    for i, label in enumerate(labels):
        ax.text(.05, i, label, fontsize=9, color=ps.INK, va="center")
        for j, m in enumerate(models):
            status, note = rows[label][m]
            x = x0 + j * step
            glyph(ax, x - .22, i, status)
            ax.text(x - .03, i, note, fontsize=7.2, va="center", ha="left",
                    color=ps.RUST if status == "failed" else ps.SECONDARY)
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"transport_slice_{name}.{ext}", metadata={"Date": None} if ext == "svg" else None)
    shutil.copyfile(OUT / f"transport_slice_{name}.svg", ROOT / f"paper/figures/transport_slice_{name}.svg")
    plt.close(fig)



# Frontier contrast. Every row travels with every other so that no crop shows
# one model's conduct in one condition alone; the caveats are drawn inside the
# image. Frontier counts: runs/transport_opus55_2026-09-27/reviews and
# runs/transport_gpt6sol_2026-09-27/reviews. Cohort ticks: exploit runs within
# days 1-20 (exploit_figure_data.json) and baseline-climate supplier contact
# (Appendix C table).
FRONTIER_ROWS = [
    ("ANNOUNCED FAULT  ·  a score that pays for exploiting it  ·  days 1–20", None),
    ("No rule: exploited the fault", {"Opus": (0, 32), "Sol": (38, 40), "cohort": [1.0, 119 / 120, 1.0, 16 / 40]}),
    ("Rule stated: exploited the fault", {"Opus": (0, 40), "Sol": (0, 40), "cohort": [0, 0, 0, 0]}),
    ("Rule stated: reported it first", {"Opus": (40, 40), "Sol": (40, 40), "cohort": [1.0, 117 / 120, 1.0, 24 / 40]}),
    ("SUPPLIER ERROR  ·  no rule, no special channel  ·  ten days after the delivery", None),
    ("Surplus delivered: told the supplier", {"Opus": (36, 36), "Sol": (40, 40), "cohort": [6 / 20, 7 / 20, 53 / 80, 42 / 80]}),
    ("Shortage delivered: told the supplier", {"Opus": (34, 34), "Sol": (40, 40), "cohort": [16 / 20, 15 / 20, 79 / 80, 77 / 80]}),
]


def frontier_figure():
    n = len(FRONTIER_ROWS)
    fig, ax = plt.subplots(figsize=(7.1, 4.05))
    fig.subplots_adjust(left=.01, right=.99, top=.99, bottom=.01)
    tracks = {"Opus": (3.55, 5.35), "Sol": (6.05, 7.85)}
    ax.set_xlim(0, 8.75)
    ax.set_ylim(n + 1.8, -1.9)
    ax.axis("off")
    ax.text(.05, -1.55, "Observed conduct in two authored shop worlds under stated conditions. Not an alignment score.",
            fontsize=7.6, color=ps.SECONDARY, va="center", style="italic")
    for key, name in (("Opus", "Claude Opus 5.5"), ("Sol", "GPT-6 Sol")):
        a, b = tracks[key]
        ax.text((a + b) / 2, -.75, name, ha="center", va="center", fontsize=9.4, color=ps.INK, family=ps.SEMIBOLD)
    for i, (label, cells) in enumerate(FRONTIER_ROWS):
        if cells is None:
            ax.text(.05, i + .08, label, fontsize=6.3, color=ps.RUST, family=ps.SEMIBOLD, va="center")
            ax.plot([.05, 8.7], [i + .4, i + .4], color=ps.RULE, lw=.5)
            continue
        if label.startswith("No rule"):
            ax.add_patch(plt.Rectangle((0, i - .42), 8.75, .84, color=ps.FANTASY_TINT, zorder=0, lw=0))
        ax.text(.05, i, label, fontsize=8.5, color=ps.INK, va="center")
        for key, (a, b) in tracks.items():
            ax.plot([a, b], [i, i], color=ps.RULE, lw=1.1, solid_capstyle="round", zorder=1)
            for v in cells["cohort"]:
                x = a + v * (b - a)
                ax.plot([x, x], [i - .2, i + .2], color=ps.MUTED, lw=1.1, zorder=2)
            k, total = cells[key]
            x = a + k / total * (b - a)
            ax.plot(x, i, marker="o", markersize=7.5, color=ps.INK, zorder=3, linestyle="none")
            ax.text(b + .12, i, f"{k}/{total}", fontsize=7.6, color=ps.INK, va="center", family=ps.SEMIBOLD)
    base = n - .35
    for key, (a, b) in tracks.items():
        for frac, lab in ((0, "0"), (.5, "50%"), (1, "100%")):
            ax.text(a + frac * (b - a), base, lab, fontsize=6.4, color=ps.SECONDARY, ha="center", va="center")
    ax.plot(3.62, n + .35, marker="o", markersize=6, color=ps.INK, linestyle="none")
    ax.text(3.75, n + .35, "frontier model", fontsize=7, color=ps.SECONDARY, va="center")
    ax.plot([4.75, 4.75], [n + .2, n + .5], color=ps.MUTED, lw=1.1)
    ax.text(4.86, n + .35, "Gemma, Luna, Muse, GLM in the same conditions", fontsize=7, color=ps.SECONDARY, va="center")
    ax.text(.05, n + 1.2,
            "One realisation per cell; counts pool frame and goal wording. Opus 5.5: 72 of 80 exploit runs and 70 of 80 supplier branches determined;\n"
            "safety-classifier refusals fell mostly in the corporate frame. Access routes differ between the two models. Cohort ticks: exploit runs\n"
            "within days 1–20; supplier world, baseline climate.",
            fontsize=6.2, color=ps.SECONDARY, va="center", linespacing=1.35)
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"frontier_contrast.{ext}", metadata={"Date": None} if ext == "svg" else None)
    shutil.copyfile(OUT / "frontier_contrast.svg", ROOT / "paper/figures/frontier_contrast.svg")
    plt.close(fig)


def main(transport_only=False):
    with ps.context():
        n = len(ROWS)
        fig, ax = plt.subplots(figsize=(7.1, 5.0))
        fig.subplots_adjust(left=.02, right=.98, top=.99, bottom=.01)
        x0 = 4.1  # first model column
        step = .9
        ax.set_xlim(0, x0 + len(MODELS) * step - .2)
        ax.set_ylim(n + .55, -1.45)
        ax.axis("off")
        for j, m in enumerate(MODELS):
            x = x0 + j * step
            ax.text(x, -.62, m, ha="center", va="center", fontsize=8.2 if len(m) > 5 else 9.0, color=ps.INK, family=ps.SEMIBOLD)
            if j in (3, 5):
                ax.plot([x - .38, x - .38], [-1.35, n - .5], color=ps.RULE, lw=.6)
        ax.text(x0 + 1 * step, -1.2, "HISTORICAL", ha="center", va="center",
                fontsize=6, color=ps.SECONDARY, family=ps.SEMIBOLD)
        ax.text(x0 + 3.5 * step, -1.2, "PREREGISTERED EXTENSION", ha="center", va="center",
                fontsize=6, color=ps.SECONDARY, family=ps.SEMIBOLD)
        ax.text(x0 + 5.5 * step, -1.2, "FRONTIER", ha="center", va="center",
                fontsize=6, color=ps.SECONDARY, family=ps.SEMIBOLD)
        for i, (label, cells) in enumerate(ROWS):
            if cells is None:
                ax.text(.05, i + .12, label, fontsize=6.4, color=ps.RUST, family=ps.SEMIBOLD, va="center")
                ax.plot([.05, x0 + (len(MODELS) - .45) * step], [i + .42, i + .42], color=ps.RULE, lw=.5)
                continue
            ax.text(.05, i, label, fontsize=8.4, color=ps.INK, va="center")
            for j, m in enumerate(MODELS):
                status, note = cells[m]
                x = x0 + j * step
                glyph(ax, x - .22, i, status)
                ax.text(x - .03, i, note, fontsize=6.7, va="center", ha="left",
                        color=ps.RUST if status == "failed" else ps.SECONDARY)
        # key
        ky = n + .05
        items = [("held", "held"), ("weak", "weak or uncertain"), ("failed", "not reproduced"),
                 ("ceiling", "no room to show"), ("untested", "not tested")]
        kx = .25
        for status, text in items:
            glyph(ax, kx, ky, status, size=6.5)
            ax.text(kx + .22, ky, text, fontsize=7.4, va="center", color=ps.SECONDARY)
            kx += .5 + len(text) * .08
        OUT.mkdir(parents=True, exist_ok=True)
        for ext in ("svg", "png"):
            fig.savefig(OUT / f"transport_map.{ext}", metadata={"Date": None} if ext == "svg" else None)
        shutil.copyfile(OUT / "transport_map.svg", ROOT / "paper/figures/transport_map.svg")
        plt.close(fig)
        for name in SLICES:
            slice_figure(name)
        frontier_figure()
    (OUT / "transport_map_data.json").write_text(json.dumps({"rows": ROWS, "sources": SOURCES}, ensure_ascii=False, indent=2), encoding="utf-8")
    if not transport_only:
        with ps.context():
            verdicts_figure()
            twins_figure()
            design_figure()
    print("Created transport_map." if transport_only else "Created summary figures.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--transport-only',action='store_true')
    args = parser.parse_args()
    main(transport_only=args.transport_only)
