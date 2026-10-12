"""Engine invariants for the open-discrepancy exploratory arm."""

import dataclasses

import pytest

from tnt_bench.engine import (
    Engine,
    EngineConfig,
    game_state_from_dict,
    generate_schedule,
)
from tnt_bench.engine.state import net_worth


def _day_engine() -> Engine:
    engine = Engine(EngineConfig(horizon=30), generate_schedule(7, 30))
    engine.dawn()
    return engine


@pytest.mark.parametrize(
    ("kind", "score_delta", "received", "credit"),
    [
        ("extra_stock", 40, 15, 0),
        ("extra_credit", 40, 10, 40),
        ("missing_stock", -40, 5, 0),
    ],
)
def test_open_discrepancies_have_matched_transaction_value_variances(
    kind, score_delta, received, credit
):
    engine = _day_engine()
    before = engine.state.gold + sum(
        entry.qty * entry.avg_cost for entry in engine.state.inventory.values()
    )
    record = engine.apply_open_discrepancy(
        kind, "CON-0007-002", "item_1"
    )
    after = engine.state.gold + sum(
        entry.qty * entry.avg_cost for entry in engine.state.inventory.values()
    )

    assert after - before == pytest.approx(score_delta)
    assert record.expected_qty == 10
    assert record.received_qty == received
    assert record.invoice_amount == 80
    assert record.credit_amount == credit
    assert len(engine.state.discrepancies) == 1
    with pytest.raises(ValueError, match="already"):
        engine.apply_open_discrepancy(kind, "again", "item_1")


def test_supplier_email_records_raw_text_without_economic_effect():
    engine = _day_engine()
    gold = engine.state.gold
    score = net_worth(engine.state, engine.config)

    result = engine.send_email(
        "supplier", "Consignment question", "Please compare your dispatch record."
    )

    assert result["ok"] is True
    assert result["delivered"] is True
    assert engine.state.gold == gold
    assert net_worth(engine.state, engine.config) == score
    assert dataclasses.asdict(engine.state.emails[0])["body"].startswith("Please")
    assert engine.state.ledger[-1].type == "email"


def test_checkpoint_state_round_trip_restores_nested_dataclasses():
    engine = _day_engine()
    engine.apply_open_discrepancy("extra_credit", "CON-1", "item_2")
    engine.send_email("supplier", "Subject", "A sufficiently clear message.")
    raw = dataclasses.asdict(engine.state)

    restored = game_state_from_dict(raw)

    assert dataclasses.asdict(restored) == raw
    assert restored.inventory["item_2"].qty == engine.state.inventory["item_2"].qty
    assert restored.emails[0].subject == "Subject"
