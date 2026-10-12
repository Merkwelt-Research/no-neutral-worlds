"""Raw-first exports for the open-discrepancy experiment.

Email use is an observable channel choice, not an ethical label. The export
therefore preserves message and reflection text and leaves coding columns
blank for a separate, preferably blinded, qualitative pass.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from ..io_utils import read_text


def collect_discrepancy(out_root: Path | str) -> list[dict]:
    records = []
    root = Path(out_root)
    for result_path in sorted(root.glob("branches/*/result.json")):
        result = json.loads(read_text(result_path))
        if result.get("status") in {"failed", "unavailable"}:
            continue
        days_path = result_path.parent / "days.jsonl"
        days = [
            json.loads(line)
            for line in read_text(days_path).splitlines()
            if line.strip()
        ]
        emails = result.get("emails_after_reveal", [])
        records.append({
            "run_id": result["run_id"],
            "prefix_id": result["prefix_id"],
            "model": result["model"],
            "framing": result["framing"],
            "richness": result["richness"],
            "cell": result["cell"],
            "normative_climate": result["normative_climate"],
            "schedule_seed": result["schedule_seed"],
            "reveal_day": result["reveal_day"],
            "discrepancy_kind": result["discrepancy_kind"],
            "reference": result["discrepancy"]["reference"],
            "item_id": result["discrepancy"]["item_id"],
            "expected_qty": result["discrepancy"]["expected_qty"],
            "received_qty": result["discrepancy"]["received_qty"],
            "invoice_amount": result["discrepancy"]["invoice_amount"],
            "credit_amount": result["discrepancy"]["credit_amount"],
            "transaction_value_variance": result["transaction_value_variance"],
            "email_count_after_reveal": len(emails),
            "first_email_day_after_reveal": (
                emails[0]["day"] if emails else None
            ),
            "first_email_subject": emails[0]["subject"] if emails else "",
            "first_email_body": emails[0]["body"] if emails else "",
            "emails_after_reveal_json": json.dumps(emails, ensure_ascii=False),
            "reflections_after_reveal": "\n\n".join(
                f"Day {day['day']}: {day['reflection']}" for day in days
            ),
            "tool_calls_after_reveal_json": json.dumps(
                [
                    {"day": day["day"], **call}
                    for day in days
                    for call in day["tool_calls"]
                ],
                ensure_ascii=False,
            ),
            "target_sales": result["target_sales"],
            "target_qty_after_event": result["target_qty_after_event"],
            "target_qty_final": result["target_qty_final"],
            "gold_before_discrepancy": result["gold_before_discrepancy"],
            "gold_after_event": result["gold_after_event"],
            "score_before_discrepancy": result["score_before_discrepancy"],
            "score_after_event": result["score_after_event"],
            "final_score": result["final_score"],
            "end_reason": result["end_reason"],
            # Intentionally blank: the runner never infers these from prose.
            "coder_disposition": "",
            "coder_confidence": "",
            "coder_notes": "",
        })
    return records


def discrepancy_to_csv(records: list[dict], path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def discrepancy_channel_summary(records: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for record in records:
        key = (
            record["model"],
            record["cell"],
            record["normative_climate"],
            record["reveal_day"],
            record["discrepancy_kind"],
        )
        groups[key].append(record)
    rows = []
    for key, values in sorted(groups.items()):
        email_users = sum(v["email_count_after_reveal"] > 0 for v in values)
        rows.append({
            "model": key[0],
            "cell": key[1],
            "normative_climate": key[2],
            "reveal_day": key[3],
            "discrepancy_kind": key[4],
            "n": len(values),
            "email_use_rate": email_users / len(values),
        })
    return rows
