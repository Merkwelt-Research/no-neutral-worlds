"""Horizon figures: when the ending becomes audible, and how conduct follows it.

Offline. Reads the historical Gemma/Qwen ablation (runs/ablation1, ongoing and
undisclosed) with its terminal-score twins (runs/main3 static, seeds 2-6), and
the Muse/GLM endpoint-by-objective factorial. Exploratory measures, not the
registered language endpoint:

- horizon reference: a journal that refers to the end of the whole run
  (patterns below), after removing the day header and excluding event
  countdowns, stock-coverage arithmetic and delivery dates;
- mean morning stock by day; stock value held at close; final net worth;
- final-week below-cost selling via the registered endgame audit.

Writes figures/out/print/horizon_{audibility,stock}.{svg,png} and
horizon_figure_data.json, and copies the SVGs to paper/figures.
"""
from __future__ import annotations

import glob
import json
import os
from pathlib import Path
import random
import re
import shutil
import statistics as st
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp/matplotlib-paper-cache"))
sys.path.insert(0, str(ROOT))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator
from figures import paper_style as ps
from tnt_bench.analysis.endgame import endgame_audit

OUT = ROOT / "figures/out/print"
EXT = ROOT / "runs/transport_glm_muse_2026-09-20/endpoint_objective"
SEED = 20260920

HEAD = re.compile(r"^\s*\**\s*day\s*\d+\s*\**\s*[:.\-—]", re.I)
EVENT = re.compile(r"surge|slump|shortage|cheap|fad|event|boom|festival|promo|spike|discount|supply|demand|sale|dip|price|cost|tier", re.I)
PATTERNS = [re.compile(p, re.I) for p in (
    r"\b(ends?|ending|last|final|close[sd]?|closing|through|until|thru|by|before)\W+(\w+\W+){0,3}day\s*90\b",
    r"\bday\s*90\W+(\w+\W+){0,3}(end|ends|close|closes|closing|final|finish|wrap)\b",
    r"\b(\d+|two|three|four|five|six|seven|eight|nine|ten|few)\s+(trading\s+|more\s+|remaining\s+|operating\s+|business\s+)?days?\s+(left|remain|remaining|to go)\b",
    r"\bend of (the )?(run|assignment|contract|simulation|game|horizon|operation|operations|period|term|engagement)\b",
    r"\b(assignment|run|contract|operations?|engagement)\s+(ends|end|closes|close|concludes|wraps)\b",
    r"\b(final|last)\s+(week|stretch|days)\b",
    r"\bend[- ]?game\b",
)]


SCORE_TALK = re.compile(r"net worth|score|final tally|final balance|final total|tally", re.I)


def horizon_ref(text: str) -> bool:
    t = HEAD.sub("", text or "")
    for pattern in PATTERNS:
        for m in pattern.finditer(t):
            before, after = t[max(0, m.start() - 30):m.start()], t[m.end():m.end() + 30]
            if re.search(r"[~=@]|\d\s*-\s*\d|/day", before + m.group(0)):
                continue  # stock-coverage arithmetic
            if EVENT.search(before[-18:] + " " + after[:22]):
                continue  # countdown of a scheduled event
            if "90" in m.group(0) and re.search(r"arriv|deliver|dawn|land", before + after, re.I):
                continue  # a delivery date
            if re.match(r"\s*('s|’s)", after):
                continue  # "last week's"
            return True
    return False


def load(folder: Path) -> dict:
    days = [json.loads(line) for line in open(folder / "days.jsonl", encoding="utf-8")]
    result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
    audit = endgame_audit(folder)
    return {
        "run_id": result["run_id"], "seed": result["schedule_seed"], "frame": result["cell"].split("-")[0],
        "score": result["score"], "days": len(days),
        "stock": [sum(d["inventory_start"].values()) for d in days],
        "close_stock_value": days[-1]["net_worth_end"] - days[-1]["gold_end"],
        "horizon": [horizon_ref(d.get("reflection", "")) and not d.get("forced") for d in days],
        "score_talk": sum(bool(SCORE_TALK.search(d.get("reflection", "") or "")) for d in days),
        "fire_sale_tax": audit.get("fire_sale_tax", 0) or 0,
    }


def collect() -> dict:
    groups = {}
    for key, pattern in (("Gemma", "google_gemma-4-31b-it"), ("Qwen", "qwen_qwen3-235b-a22b-2507")):
        for disclosed, root, suffix in ((True, "runs/main3", ""), (False, "runs/ablation1", "__undisclosed")):
            runs = []
            for cell in ("fantasy-static", "neutral-static"):
                for seed in range(2, 7):
                    runs.append(load(ROOT / root / f"{pattern}__{cell}__s{seed}__h90{suffix}"))
            groups[(key, disclosed)] = runs
    for f in glob.glob(str(EXT / "*/attempt-*/complete.json")):
        result = json.loads(Path(f).read_text(encoding="utf-8"))["result"]
        folder = Path(glob.glob(str(Path(f).parent / "data/*/days.jsonl"))[0]).parent
        model = "Muse" if "muse" in result["model"] else "GLM"
        run = load(folder)
        run["objective"] = result["score_objective"]
        groups.setdefault((model, result["disclose_horizon"]), []).append(run)
    assert all(len(v) == 10 for k, v in groups.items() if k[0] in ("Gemma", "Qwen"))
    assert all(len(v) == 40 for k, v in groups.items() if k[0] in ("Muse", "GLM"))
    return groups


def paired(groups, model, metric):
    """Disclosed minus withheld, averaged within schedule (and frame/objective)."""
    dis, hid = groups[(model, True)], groups[(model, False)]
    seeds = sorted({r["seed"] for r in dis})
    values = [st.mean(metric(r) for r in dis if r["seed"] == s) - st.mean(metric(r) for r in hid if r["seed"] == s)
              for s in seeds]
    rng = random.Random(SEED)
    boot = sorted(st.mean(rng.choice(values) for _ in values) for _ in range(10000))
    return {"mean": st.mean(values), "ci95": [boot[249], boot[9749]], "negative": sum(v < 0 for v in values),
            "n": len(values)}


def summarise(groups):
    out = {}
    for model in ("Gemma", "Qwen", "Muse", "GLM"):
        dis, hid = groups[(model, True)], groups[(model, False)]
        onset = [next((i + 1 for i, h in enumerate(r["horizon"]) if h), None) for r in dis]
        out[model] = {
            "historical_bundle": model in ("Gemma", "Qwen"),
            "runs_per_condition": len(dis),
            "horizon_days_per_run": {"disclosed": st.mean(sum(r["horizon"]) for r in dis),
                                     "withheld": st.mean(sum(r["horizon"]) for r in hid)},
            "disclosed_onset_median": st.median(o if o else 91 for o in onset),
            "withheld_runs_any_reference": sum(any(r["horizon"]) for r in hid),
            "final_score_mean": {"disclosed": st.mean(r["score"] for r in dis), "withheld": st.mean(r["score"] for r in hid)},
            "close_stock_value_mean": {"disclosed": st.mean(r["close_stock_value"] for r in dis),
                                       "withheld": st.mean(r["close_stock_value"] for r in hid)},
            "fire_sale_runs_over_10": {"disclosed": sum(r["fire_sale_tax"] > 10 for r in dis),
                                       "withheld": sum(r["fire_sale_tax"] > 10 for r in hid)},
            "paired": {
                "close_stock_value": paired(groups, model, lambda r: r["close_stock_value"]),
                "final_score": paired(groups, model, lambda r: r["score"]),
                "stock_days_1_30": paired(groups, model, lambda r: st.mean(r["stock"][:30])),
                "stock_days_61_80": paired(groups, model, lambda r: st.mean(r["stock"][60:80])),
                "stock_days_81_90": paired(groups, model, lambda r: st.mean(r["stock"][80:90])),
            },
        }
    for model in ("Muse", "GLM"):
        runs = groups[(model, True)] + groups[(model, False)]
        def by_objective(metric):
            seeds = sorted({r["seed"] for r in runs})
            values = [st.mean(metric(r) for r in runs if r["seed"] == s and r["objective"])
                      - st.mean(metric(r) for r in runs if r["seed"] == s and not r["objective"]) for s in seeds]
            rng = random.Random(SEED)
            boot = sorted(st.mean(rng.choice(values) for _ in values) for _ in range(10000))
            return {"mean": st.mean(values), "ci95": [boot[249], boot[9749]], "positive": sum(v > 0 for v in values)}
        out[model]["score_objective"] = {
            "score_talk_days_per_run": {"present": st.mean(r["score_talk"] for r in runs if r["objective"]),
                                        "absent": st.mean(r["score_talk"] for r in runs if not r["objective"])},
            "paired_present_minus_absent": {
                "final_score": by_objective(lambda r: r["score"]),
                "mean_stock": by_objective(lambda r: st.mean(r["stock"])),
                "close_stock_value": by_objective(lambda r: r["close_stock_value"]),
            },
        }
    return out


MODELS = ("Gemma", "Qwen", "Muse", "GLM")
SUB = {"Gemma": "historical · terminal score vs ongoing", "Qwen": "historical · terminal score vs ongoing",
       "Muse": "extension · endpoint shown vs withheld", "GLM": "extension · endpoint shown vs withheld"}


def audibility_figure(groups, summary):
    fig, axes = plt.subplots(1, 4, figsize=(7.1, 2.75), sharey=True)
    fig.subplots_adjust(left=.08, right=.99, top=.72, bottom=.2, wspace=.12)
    bins = list(range(1, 91, 5))
    for ax, model in zip(axes, MODELS):
        for disclosed, colour, ls in ((True, ps.INK, "-"), (False, ps.MUTED, "--")):
            runs = groups[(model, disclosed)]
            ys = [100 * st.mean(st.mean(r["horizon"][b - 1:b + 4]) for r in runs) for b in bins]
            ax.plot([b + 2 for b in bins], ys, color=colour, ls=ls, lw=2 if disclosed else 1.4)
        onset = summary[model]["disclosed_onset_median"]
        ax.axvline(onset, color=ps.RUST, lw=.9, ls=(0, (2, 2)))
        ax.text(onset - 1.5, 96, f"median onset\nday {onset:g}", ha="right", va="top", fontsize=6.6, color=ps.RUST)
        ax.text(0, 1.2, model, transform=ax.transAxes, fontsize=9.2, family=ps.SEMIBOLD, color=ps.INK)
        ax.text(0, 1.08, SUB[model], transform=ax.transAxes, fontsize=6.4, color=ps.SECONDARY)
        ax.set_xlim(1, 90); ax.set_ylim(0, 100)
        ax.set_xticks([1, 30, 60, 90]); ax.set_yticks([0, 25, 50, 75, 100])
        ax.grid(axis="y")
    axes[0].set_ylabel("Journals referring to\nthe run's end (%)")
    fig.text(.53, .03, "Day (five-day windows)", ha="center", fontsize=8, color=ps.SECONDARY)
    fig.legend(handles=[Line2D([0], [0], color=ps.INK, lw=2, label="Ending known"),
                        Line2D([0], [0], color=ps.MUTED, lw=1.4, ls="--", label="Ending not given")],
               loc="upper right", bbox_to_anchor=(.99, 1.0), ncol=2, fontsize=8)
    save(fig, "horizon_audibility")


def stock_figure(groups, summary):
    fig, axes = plt.subplots(1, 4, figsize=(7.1, 2.9))
    fig.subplots_adjust(left=.08, right=.99, top=.72, bottom=.27, wspace=.3)
    for ax, model in zip(axes, MODELS):
        for disclosed, colour, ls in ((True, ps.INK, "-"), (False, ps.MUTED, "--")):
            runs = groups[(model, disclosed)]
            ys = [st.mean(r["stock"][d] for r in runs if len(r["stock"]) > d) for d in range(90)]
            ax.plot(range(1, 91), ys, color=colour, ls=ls, lw=1.9 if disclosed else 1.4)
        onset = summary[model]["disclosed_onset_median"]
        ax.axvspan(onset, 90, color=ps.FANTASY_TINT, alpha=.6, lw=0, zorder=0)
        s = summary[model]
        ax.text(0, 1.2, model, transform=ax.transAxes, fontsize=9.2, family=ps.SEMIBOLD, color=ps.INK)
        ax.text(0, 1.08, SUB[model].split(" · ")[0], transform=ax.transAxes, fontsize=6.4, color=ps.SECONDARY)
        cv, sc = s["close_stock_value_mean"], s["final_score_mean"]
        ax.text(0, -.3, f"stock value at close  {cv['disclosed']:,.0f} vs {cv['withheld']:,.0f}", transform=ax.transAxes,
                fontsize=6.7, color=ps.INK)
        ax.text(0, -.42, f"final wealth  {sc['disclosed']/1000:,.1f}k vs {sc['withheld']/1000:,.1f}k",
                transform=ax.transAxes, fontsize=6.7, color=ps.SECONDARY)
        ax.set_xlim(1, 90); ax.set_ylim(bottom=0)
        ax.set_xticks([1, 30, 60, 90])
        ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.grid(axis="y")
    axes[0].set_ylabel("Mean morning stock (units)")
    fig.legend(handles=[Line2D([0], [0], color=ps.INK, lw=1.9, label="Ending known"),
                        Line2D([0], [0], color=ps.MUTED, lw=1.4, ls="--", label="Ending not given"),
                        plt.Rectangle((0, 0), 1, 1, color=ps.FANTASY_TINT, label="after median onset")],
               loc="upper right", bbox_to_anchor=(.99, 1.0), ncol=3, fontsize=7.8)
    save(fig, "horizon_stock")


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"{name}.{ext}", metadata={"Date": None} if ext == "svg" else None)
    shutil.copyfile(OUT / f"{name}.svg", ROOT / "paper/figures" / f"{name}.svg")
    plt.close(fig)


def main():
    groups = collect()
    summary = summarise(groups)
    with ps.context():
        audibility_figure(groups, summary)
        stock_figure(groups, summary)
    (OUT / "horizon_figure_data.json").write_text(json.dumps({
        "summary": summary,
        "note": "Exploratory. Historical Gemma/Qwen compare terminal-score runs (endpoint and score objective "
                "disclosed together, collected earlier) with ongoing runs; Muse/GLM compare endpoint shown vs "
                "withheld, pooling the score-objective factor. Paired contrasts average within schedule; "
                "95% percentile schedule bootstrap, 10,000 resamples, seed 20260920.",
        "measure": [p.pattern for p in PATTERNS],
    }, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
