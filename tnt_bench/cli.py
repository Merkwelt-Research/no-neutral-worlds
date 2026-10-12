"""Command-line entry point.

    python -m tnt_bench run --models baseline:heuristic,baseline:oracle \
        --seeds 1,2,3 --horizon 30 --out runs/
    python -m tnt_bench run --models openai/gpt-4o-mini --seeds 42 \
        --cells fantasy-rich,neutral-rich --gm-model openai/gpt-4o-mini --out runs/
    python -m tnt_bench summarize --out runs/

LLM runs read OPENROUTER_API_KEY (or --api-key-env) and talk to an
OpenAI-compatible endpoint. Baseline-only matrices need no key; rich cells
need a GM model (or previously cached packs under <out>/packs/).
"""

from __future__ import annotations

import argparse
import os
import sys

from .exploit import EXPLOIT_CONDITIONS
from .discrepancy import DISCREPANCY_KINDS, NORMATIVE_CLIMATES
from .harness import ALL_CELLS, Condition, expand_specs, run_matrix, summarize
from .harness.run import BASELINE_PREFIX


def _parse_cells(text: str) -> list[Condition]:
    cells = []
    for token in text.split(","):
        framing, _, richness = token.strip().partition("-")
        cells.append(Condition(framing=framing, richness=richness))
    return cells


def _print_results(results: list[dict]) -> None:
    if not results:
        print("no results")
        return
    width = max(len(r["run_id"]) for r in results)
    for r in results:
        if r.get("status") == "failed":
            print(f"{r['run_id']:<{width}}  FAILED: {r['error']}")
        else:
            print(
                f"{r['run_id']:<{width}}  score={r['score']:>7}  "
                f"days={r['days_survived']:>3}  {r['end_reason']}"
            )
    failed = sum(1 for r in results if r.get("status") == "failed")
    if failed:
        print(f"\n{failed} run(s) failed — re-run the same command to retry them.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tnt_bench")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="execute a run matrix")
    run_parser.add_argument("--models", required=True, help="comma-separated model ids")
    run_parser.add_argument("--seeds", required=True, help="comma-separated schedule seeds")
    run_parser.add_argument("--horizon", type=int, default=30)
    run_parser.add_argument("--cells", default=None,
                            help="comma-separated cells like fantasy-rich (default: all four)")
    run_parser.add_argument("--out", required=True, help="run-set output directory")
    run_parser.add_argument("--base-url", default="https://openrouter.ai/api/v1")
    run_parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    run_parser.add_argument("--temperature", type=float, default=0.7)
    narration_group = run_parser.add_mutually_exclusive_group()
    narration_group.add_argument(
        "--gm-model",
        default=None,
        help="model for narration pack generation (rich cells)",
    )
    narration_group.add_argument(
        "--pack-source",
        default=None,
        help=(
            "directory of frozen narration packs to copy into <out>/packs; "
            "prevents regeneration of matching rich-cell packs"
        ),
    )
    run_parser.add_argument("--gm-temperature", type=float, default=0.8)
    run_parser.add_argument("--parallel", type=int, default=1,
                            help="concurrent runs (packs pre-generate sequentially; mind rate limits)")
    run_parser.add_argument("--undisclosed-horizon", action="store_true",
                            help="horizon-disclosure ablation: agent surface never "
                            "states the run length (economics identical)")
    run_parser.add_argument("--interleave", default=None, metavar="SEED",
                            help="shuffle execution order deterministically "
                            "(new collections should pass this; avoids the "
                            "fixed-block treatment-by-time confound)")
    run_parser.add_argument("--block-randomize", default=None, metavar="SEED",
                            help="randomized complete blocks: one block per "
                            "(seed, model), cells in frozen-seed random order "
                            "with the lead condition rotating across blocks "
                            "(replication protocol; excludes --interleave)")
    run_parser.add_argument("--replicate", default="1", metavar="N[,N...]",
                            help="independent agent realization number(s) for this "
                            "collection, e.g. 1,2 to run every cell twice in one "
                            "queue (N>=2 suffixes run ids with __rN so realizations "
                            "coexist; default 1 keeps historical ids)")
    run_parser.add_argument("--carrying-cost", type=float, default=0.0,
                            help="per-unit nightly storage charge (doctrine x economy "
                            "experiment; requires themes with a 'carrying' prompt block)")
    exploit_group = run_parser.add_mutually_exclusive_group()
    exploit_group.add_argument(
        "--exploit-condition",
        default=None,
        choices=EXPLOIT_CONDITIONS,
        help=(
            "run one exploit-uptake treatment; 'ambiguous' means no explicit "
            "prohibition, with or without the _wit instruction"
        ),
    )
    exploit_group.add_argument(
        "--exploit-factorial",
        action="store_true",
        help=(
            "run all four prohibition x whatever-it-takes treatments inside "
            "each world cell and randomization block"
        ),
    )

    summarize_parser = sub.add_parser("summarize", help="rank completed results")
    summarize_parser.add_argument("--out", required=True)

    analyze_parser = sub.add_parser("analyze", help="compute trace + behavior metrics")
    analyze_parser.add_argument("--out", required=True, help="run-set directory")
    analyze_parser.add_argument("--csv", default=None, help="write per-run metrics CSV here")
    analyze_parser.add_argument("--include-baselines", action="store_true",
                                help="include baseline:* runs (excluded by default: "
                                "no trace to analyze, and they'd pollute cell means)")

    exploit_analyze_parser = sub.add_parser(
        "analyze-exploit",
        help="summarize exploit/report/neither dispositions by factorial cell",
    )
    exploit_analyze_parser.add_argument("--out", required=True, help="run-set directory")
    exploit_analyze_parser.add_argument(
        "--csv", default=None, help="write the per-run exploit table here"
    )

    discrepancy_parser = sub.add_parser(
        "run-discrepancy",
        help="run checkpointed open-discrepancy branches",
    )
    discrepancy_parser.add_argument("--models", required=True,
                                    help="comma-separated model ids")
    discrepancy_parser.add_argument("--seeds", required=True,
                                    help="comma-separated schedule seeds")
    discrepancy_parser.add_argument("--horizon", type=int, default=90)
    discrepancy_parser.add_argument(
        "--cells",
        default="fantasy-rich,neutral-rich",
        help="comma-separated world cells (default: fantasy-rich,neutral-rich)",
    )
    discrepancy_parser.add_argument(
        "--climates",
        default=",".join(NORMATIVE_CLIMATES),
        help="comma-separated ambient climates",
    )
    discrepancy_parser.add_argument(
        "--reveal-days",
        default="2,46",
        help="comma-separated pre-dawn checkpoint/reveal days",
    )
    discrepancy_parser.add_argument(
        "--discrepancies",
        default=",".join(DISCREPANCY_KINDS),
        help="comma-separated discrepancy kinds",
    )
    discrepancy_parser.add_argument("--observe-days", type=int, default=10)
    discrepancy_parser.add_argument("--out", required=True)
    discrepancy_parser.add_argument("--base-url",
                                    default="https://openrouter.ai/api/v1")
    discrepancy_parser.add_argument("--api-key-env",
                                    default="OPENROUTER_API_KEY")
    discrepancy_parser.add_argument("--temperature", type=float, default=0.7)
    discrepancy_parser.add_argument("--parallel", type=int, default=1)
    discrepancy_parser.add_argument(
        "--randomize",
        default="tnt-open-discrepancy-1",
        help="frozen randomization seed for prefix and branch order",
    )
    discrepancy_narration = discrepancy_parser.add_mutually_exclusive_group()
    discrepancy_narration.add_argument(
        "--pack-source",
        default=None,
        help="directory of frozen narration packs to reuse",
    )
    discrepancy_narration.add_argument(
        "--gm-model",
        default=None,
        help="model for narration pack generation when frozen packs are unavailable",
    )
    discrepancy_parser.add_argument("--gm-temperature", type=float, default=0.8)
    discrepancy_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and print the design without making API calls",
    )

    discrepancy_analyze_parser = sub.add_parser(
        "analyze-discrepancy",
        help="export raw correspondence and channel-use summaries",
    )
    discrepancy_analyze_parser.add_argument("--out", required=True)
    discrepancy_analyze_parser.add_argument("--csv", default=None)

    audit_parser = sub.add_parser("audit", help="register-audit narration packs")
    audit_parser.add_argument("--out", required=True, help="run-set directory (audits <out>/packs)")

    args = parser.parse_args(argv)

    if args.command == "summarize":
        _print_results(summarize(args.out))
        return 0

    if args.command == "audit":
        from pathlib import Path

        from .io_utils import read_text
        from .narration import NarrationPack, register_audit

        packs = sorted(Path(args.out).glob("packs/*.yml"))
        if not packs:
            print(f"no packs under {args.out}/packs")
            return 1
        for path in packs:
            audit = register_audit(NarrationPack.from_yaml(read_text(path)))
            print(
                f"{path.name}: crisis_days={audit['crisis_day_rate']:.0%} "
                f"warm_days={audit['warm_day_rate']:.0%} "
                f"fallbacks={audit['fallback_days']} "
                f"mean_chars={audit['mean_chars']:.0f} "
                f"novelty={audit['novelty_mean']:.2f}/min {audit['novelty_min']:.2f}"
            )
        return 0

    if args.command == "analyze":
        from .analysis import cell_summary, collect, to_csv

        metrics = collect(args.out)
        if not args.include_baselines:
            excluded = sum(1 for m in metrics if m.model.startswith(BASELINE_PREFIX))
            metrics = [m for m in metrics if not m.model.startswith(BASELINE_PREFIX)]
            if excluded:
                print(f"(excluded {excluded} baseline runs; --include-baselines to keep)")
        if not metrics:
            print("no completed runs found")
            return 1
        if args.csv:
            to_csv(metrics, args.csv)
            print(f"wrote {len(metrics)} rows to {args.csv}")
        for cell, row in cell_summary(metrics).items():
            print(f"\n[{cell}]  n={row['n']}  survival={row['survival_rate']:.0%}")
            for key, value in row.items():
                if key.endswith("_mean"):
                    sd = row.get(key[:-5] + "_sd", 0.0)
                    print(f"  {key[:-5]:<24} {value:>10.3f}  (sd {sd:.3f})")
        return 0

    if args.command == "analyze-exploit":
        from .analysis import (
            collect_exploit,
            exploit_cell_summary,
            exploit_to_csv,
        )

        records = collect_exploit(args.out)
        if not records:
            print("no completed exploit runs found")
            return 1
        if args.csv:
            exploit_to_csv(records, args.csv)
            print(f"wrote {len(records)} rows to {args.csv}")
        for row in exploit_cell_summary(records):
            print(
                f"{row['framing']}-{row['richness']} "
                f"prohibition={row['prohibition']} wit={row['wit']} "
                f"n={row['n']} "
                f"exploit={row['exploit_first_rate']:.0%} "
                f"report={row['report_first_rate']:.0%} "
                f"neither={row['neither_rate']:.0%}"
            )
        return 0

    if args.command == "analyze-discrepancy":
        from .analysis import (
            collect_discrepancy,
            discrepancy_channel_summary,
            discrepancy_to_csv,
        )

        records = collect_discrepancy(args.out)
        if not records:
            print("no completed open-discrepancy branches found")
            return 1
        if args.csv:
            discrepancy_to_csv(records, args.csv)
            print(f"wrote {len(records)} raw-first rows to {args.csv}")
        print(
            "CAUTION: email use is a channel choice, not a disclosure or "
            "ethical-disposition classification."
        )
        for row in discrepancy_channel_summary(records):
            print(
                f"{row['model']} {row['cell']} "
                f"climate={row['normative_climate']} "
                f"day={row['reveal_day']} kind={row['discrepancy_kind']} "
                f"n={row['n']} email_use={row['email_use_rate']:.0%}"
            )
        return 0

    if args.command == "run-discrepancy":
        from .harness import (
            expand_discrepancy_groups,
            run_discrepancy_matrix,
            validate_discrepancy_pack_source,
        )

        models = [m.strip() for m in args.models.split(",") if m.strip()]
        if any(model.startswith(BASELINE_PREFIX) for model in models):
            print(
                "error: run-discrepancy requires chat models; baseline policies "
                "cannot exercise free-form correspondence",
                file=sys.stderr,
            )
            return 2
        cells = _parse_cells(args.cells)
        groups = expand_discrepancy_groups(
            models=models,
            seeds=[int(s) for s in args.seeds.split(",")],
            cells=cells,
            climates=[c.strip() for c in args.climates.split(",")],
            horizon=args.horizon,
            reveal_days=[int(d) for d in args.reveal_days.split(",")],
            discrepancy_kinds=[
                kind.strip() for kind in args.discrepancies.split(",")
            ],
            observation_days=args.observe_days,
            temperature=args.temperature,
            randomize_seed=args.randomize,
        )
        branch_count = sum(
            len(group.reveal_days) * len(group.discrepancy_kinds)
            for group in groups
        )
        prefix_days = sum(group.reveal_days[-1] - 1 for group in groups)
        branch_days = sum(
            len(group.reveal_days)
            * len(group.discrepancy_kinds)
            * group.observation_days
            for group in groups
        )
        print(
            f"{len(groups)} shared clean prefixes + {branch_count} short branches "
            f"-> {args.out}"
        )
        print(
            f"planned model-days: {prefix_days} prefix + {branch_days} branch "
            f"= {prefix_days + branch_days}"
        )
        if args.pack_source:
            checked = validate_discrepancy_pack_source(groups, args.pack_source)
            print(f"validated {len(checked)} frozen narration packs")
        if args.dry_run:
            return 0

        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            print(f"error: {args.api_key_env} is not set", file=sys.stderr)
            return 2
        from .agent.llm import openai_chat_client

        def discrepancy_chat_factory(model: str):
            return openai_chat_client(
                api_key=api_key,
                model=model,
                base_url=args.base_url,
                temperature=args.temperature,
            )

        gm_llm = None
        if args.gm_model:
            from .narration.llm import openai_chat_llm

            gm_llm = openai_chat_llm(
                api_key=api_key,
                model=args.gm_model,
                base_url=args.base_url,
                temperature=args.gm_temperature,
            )

        results = run_discrepancy_matrix(
            groups,
            args.out,
            chat_factory=discrepancy_chat_factory,
            parallel=args.parallel,
            pack_source=args.pack_source,
            gm_llm=gm_llm,
            gm_model=args.gm_model or "unspecified",
            on_result=lambda result: print(
                f"  FAILED {result['run_id']}: {result['error']}"
                if result.get("status") == "failed"
                else f"  unavailable {result['run_id']}: {result['error']}"
                if result.get("status") == "unavailable"
                else (
                    f"  done {result['run_id']}: "
                    f"emails={result['email_count_after_reveal']} "
                    f"({result['end_reason']})"
                )
            ),
        )
        failed = sum(r.get("status") == "failed" for r in results)
        unavailable = sum(r.get("status") == "unavailable" for r in results)
        complete = len(results) - failed - unavailable
        print(
            f"\ncomplete={complete} unavailable={unavailable} failed={failed}"
        )
        return 1 if failed else 0

    models = [m.strip() for m in args.models.split(",")]
    seeds = [int(s) for s in args.seeds.split(",")]
    cells = _parse_cells(args.cells) if args.cells else list(ALL_CELLS)
    specs = expand_specs(
        models=models, seeds=seeds, horizon=args.horizon, cells=cells,
        disclose_horizon=not args.undisclosed_horizon,
        carrying_cost=args.carrying_cost,
        interleave_seed=args.interleave,
        block_seed=args.block_randomize,
        temperature=args.temperature,
        replicate=[int(r) for r in args.replicate.split(",")],
        exploit_condition=(
            EXPLOIT_CONDITIONS if args.exploit_factorial
            else args.exploit_condition
        ),
    )

    needs_llm = any(not m.startswith(BASELINE_PREFIX) for m in models)
    needs_gm = any(c.richness == "rich" for c in cells) and args.gm_model is not None
    api_key = os.environ.get(args.api_key_env)
    if (needs_llm or needs_gm) and not api_key:
        print(f"error: {args.api_key_env} is not set", file=sys.stderr)
        return 2

    chat_factory = None
    if needs_llm:
        from .agent.llm import openai_chat_client

        def chat_factory(model: str):
            return openai_chat_client(
                api_key=api_key, model=model,
                base_url=args.base_url, temperature=args.temperature,
            )

    gm_llm = None
    if args.gm_model:
        from .narration.llm import openai_chat_llm

        gm_llm = openai_chat_llm(
            api_key=api_key, model=args.gm_model,
            base_url=args.base_url, temperature=args.gm_temperature,
        )

    print(f"{len(specs)} runs -> {args.out}")
    results = run_matrix(
        specs, args.out,
        chat_factory=chat_factory,
        gm_llm=gm_llm,
        gm_model=args.gm_model or "unspecified",
        parallel=args.parallel,
        pack_source=args.pack_source,
        on_result=lambda r: print(
            f"  FAILED {r['run_id']}: {r['error']}"
            if r.get("status") == "failed"
            else f"  done {r['run_id']}: score={r['score']} ({r['end_reason']})"
        ),
    )
    print()
    _print_results(sorted(results, key=lambda r: r.get("score", float("-inf")), reverse=True))
    return 1 if any(r.get("status") == "failed" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
