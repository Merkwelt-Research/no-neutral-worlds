"""Checkpoint/branch integration tests with a deterministic chat stub."""

import json

from tnt_bench.agent.day_loop import ChatResponse, ChatToolCall
from tnt_bench.analysis import (
    collect_discrepancy,
    discrepancy_channel_summary,
    discrepancy_to_csv,
)
from tnt_bench.harness import (
    Condition,
    DiscrepancyGroupSpec,
    execute_discrepancy_group,
)


def _end_day_chat(messages, tools):
    reflection = (
        "The day is complete. I checked the available record and will carry "
        "the current stock, balance, and relevant observations into tomorrow. "
    )
    return ChatResponse(
        tool_calls=[
            ChatToolCall(
                id="end",
                name="end_day",
                arguments={"reflection": reflection},
            )
        ]
    )


def test_shared_prefix_forks_short_counterfactual_branches(tmp_path):
    spec = DiscrepancyGroupSpec(
        model="test/model",
        condition=Condition("fantasy", "static"),
        schedule_seed=7,
        normative_climate="baseline",
        horizon=30,
        reveal_days=(2, 4),
        discrepancy_kinds=("extra_stock", "missing_stock"),
        observation_days=2,
    )

    results = execute_discrepancy_group(
        spec, tmp_path, chat=_end_day_chat
    )

    assert len(results) == 4
    assert all(result["observation_days_completed"] == 2 for result in results)
    assert all(result["email_count_after_reveal"] == 0 for result in results)
    assert {
        (result["discrepancy_kind"], result["transaction_value_variance"])
        for result in results
    } == {("extra_stock", 40), ("missing_stock", -40)}
    by_day = {}
    for result in results:
        by_day.setdefault(result["reveal_day"], set()).add(
            result["checkpoint_hash"]
        )
        branch_dir = tmp_path / "branches" / result["run_id"]
        assert len((branch_dir / "days.jsonl").read_text().splitlines()) == 2
        assert (branch_dir / "start_checkpoint.json").exists()
    assert all(len(hashes) == 1 for hashes in by_day.values())
    assert len({r["discrepancy"]["item_id"] for r in results}) == 1
    prefix_dir = tmp_path / "prefixes" / spec.prefix_id
    assert len((prefix_dir / "days.jsonl").read_text().splitlines()) == 3

    records = collect_discrepancy(tmp_path)
    assert len(records) == 4
    assert len(discrepancy_channel_summary(records)) == 4
    csv_path = tmp_path / "coding.csv"
    discrepancy_to_csv(records, csv_path)
    header = csv_path.read_text(encoding="utf-8-sig").splitlines()[0]
    assert "coder_disposition" in header
    assert "emails_after_reveal_json" in header

    # Completed branches are resumable and never call the model again.
    def fail_chat(*_args):
        raise AssertionError("completed group should have been loaded")

    resumed = execute_discrepancy_group(spec, tmp_path, chat=fail_chat)
    assert {r["run_id"] for r in resumed} == {r["run_id"] for r in results}


def test_branch_manifests_name_shared_history_dependence(tmp_path):
    spec = DiscrepancyGroupSpec(
        model="test/model",
        condition=Condition("neutral", "static"),
        schedule_seed=8,
        normative_climate="audit",
        horizon=30,
        reveal_days=(2,),
        discrepancy_kinds=("extra_credit",),
        observation_days=2,
    )
    [result] = execute_discrepancy_group(spec, tmp_path, chat=_end_day_chat)
    manifest = json.loads(
        (
            tmp_path / "branches" / result["run_id"] / "manifest.json"
        ).read_text()
    )
    assert manifest["prefix_id"] == result["prefix_id"]
    assert manifest["checkpoint_hash"] == result["checkpoint_hash"]
    assert manifest["administrative_censoring"] is True
