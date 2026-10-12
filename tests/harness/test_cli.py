"""CLI smoke tests (baseline-only, no network)."""

from tnt_bench.cli import _parse_cells, main
from tnt_bench.harness import Condition


def test_parse_cells():
    assert _parse_cells("fantasy-rich, neutral-static") == [
        Condition("fantasy", "rich"),
        Condition("neutral", "static"),
    ]


def test_cli_baseline_run_and_summarize(tmp_path, capsys):
    out = str(tmp_path / "runs")
    code = main([
        "run",
        "--models", "baseline:heuristic,baseline:random",
        "--seeds", "42",
        "--cells", "fantasy-static,neutral-static",
        "--out", out,
    ])
    assert code == 0
    assert "4 runs" in capsys.readouterr().out

    code = main(["summarize", "--out", out])
    assert code == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 4
    assert "score=" in lines[0]


def test_cli_expands_exploit_factorial_as_one_randomized_queue(tmp_path, capsys):
    out = tmp_path / "exploit"
    code = main([
        "run",
        "--models", "baseline:heuristic",
        "--seeds", "42",
        "--cells", "fantasy-static,neutral-static",
        "--exploit-factorial",
        "--block-randomize", "tnt-exploit-test",
        "--out", str(out),
    ])
    assert code == 0
    assert "8 runs" in capsys.readouterr().out

    csv_path = tmp_path / "exploit.csv"
    code = main([
        "analyze-exploit", "--out", str(out), "--csv", str(csv_path),
    ])
    assert code == 0
    output = capsys.readouterr().out
    assert "wrote 8 rows" in output
    assert output.count("neither=100%") == 8
    assert csv_path.exists()


def test_cli_requires_api_key_for_llm_models(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    code = main([
        "run", "--models", "some/model", "--seeds", "1",
        "--cells", "fantasy-static", "--out", str(tmp_path),
    ])
    assert code == 2
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err


def test_cli_open_discrepancy_protocol_dry_run_needs_no_api_key(
    tmp_path, capsys, monkeypatch
):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    code = main([
        "run-discrepancy",
        "--models", "google/gemma-4-31b-it",
        "--seeds", "12,13,14,15,16",
        "--out", str(tmp_path / "discrepancy1"),
        "--dry-run",
    ])
    assert code == 0
    output = capsys.readouterr().out
    assert "30 shared clean prefixes + 180 short branches" in output
    assert "3150" in output
