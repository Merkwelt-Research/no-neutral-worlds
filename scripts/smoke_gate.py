"""Mechanical, outcome-blind smoke-test gate (docs/osf/REPLICATION.md).

Reads ONLY operational fields from a smoke run-set and prints per-model
gate verdicts. It never opens the "score" side of result.json — the file's
existence is checked for completion, its contents are not read — so the
gate cannot leak outcomes into adapter decisions.

    python scripts/smoke_gate.py runs/replication_smoke

Frozen thresholds (per model, pooled over its smoke runs):
  1. completion: every run has result.json
  2. forced-day rate <= 10%
  3. invalid-argument tool results < 10% of tool calls
  4. total nudges <= 1 per agent-day on average
Exit code 0 iff every model passes all four.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

FORCED_RATE_MAX = 0.10
INVALID_CALL_RATE_MAX = 0.10
NUDGES_PER_DAY_MAX = 1.0


def main(root: str) -> int:
    stats: dict[str, dict] = defaultdict(
        lambda: {"runs": 0, "complete": 0, "days": 0, "forced": 0,
                 "nudges": 0, "tool_calls": 0, "invalid_calls": 0,
                 "temperature": set()}
    )
    run_dirs = [d for d in sorted(Path(root).iterdir())
                if d.is_dir() and (d / "manifest.json").exists()]
    if not run_dirs:
        print(f"no runs under {root}")
        return 1

    for run_dir in run_dirs:
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        s = stats[manifest["model"]]
        s["runs"] += 1
        s["complete"] += int((run_dir / "result.json").exists())
        s["temperature"].add(manifest.get("temperature"))
        days_path = run_dir / "days.jsonl"
        if not days_path.exists():
            continue
        for line in days_path.read_text(encoding="utf-8").splitlines():
            day = json.loads(line)
            s["days"] += 1
            s["forced"] += int(day["forced"])
            s["nudges"] += day["nudges"]
            for call in day["tool_calls"]:
                s["tool_calls"] += 1
                error = call["result"].get("error", "")
                s["invalid_calls"] += int(
                    not call["result"].get("ok")
                    and str(error).startswith("invalid tool arguments")
                )

    all_pass = True
    for model, s in sorted(stats.items()):
        forced_rate = s["forced"] / s["days"] if s["days"] else 1.0
        invalid_rate = s["invalid_calls"] / s["tool_calls"] if s["tool_calls"] else 0.0
        nudges_per_day = s["nudges"] / s["days"] if s["days"] else 0.0
        checks = [
            ("completion", s["complete"] == s["runs"],
             f"{s['complete']}/{s['runs']} runs complete"),
            ("forced-day rate", forced_rate <= FORCED_RATE_MAX,
             f"{s['forced']}/{s['days']} = {forced_rate:.0%} (max {FORCED_RATE_MAX:.0%})"),
            ("tool-call validity", invalid_rate < INVALID_CALL_RATE_MAX,
             f"{s['invalid_calls']}/{s['tool_calls']} invalid = {invalid_rate:.1%} "
             f"(max <{INVALID_CALL_RATE_MAX:.0%})"),
            ("nudge burden", nudges_per_day <= NUDGES_PER_DAY_MAX,
             f"{s['nudges']} nudges / {s['days']} days = {nudges_per_day:.2f}/day "
             f"(max {NUDGES_PER_DAY_MAX:.1f})"),
        ]
        model_pass = all(ok for _, ok, _ in checks)
        all_pass &= model_pass
        print(f"\n{model}  ->  {'PASS' if model_pass else 'FAIL'}")
        for name, ok, detail in checks:
            print(f"  [{'ok' if ok else 'FAIL'}] {name:<20} {detail}")
        temps = sorted(str(t) for t in s["temperature"])
        print(f"  [--] temperature requested: {', '.join(temps)} (recorded, not gated)")

    print(f"\ngate: {'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "runs/replication_smoke"))
