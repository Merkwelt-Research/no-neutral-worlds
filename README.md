# No Neutral Worlds

Code, registrations and analysis records for **No Neutral Worlds: How evaluation worlds write the behaviour they score** (Stephen Jeffery, Merkwelt Research, 2026).

LLM agents ran a small shop for ninety simulated days in a deterministic economy. Each experiment held the economy fixed and changed one feature of the world the agent was given: its frame, a stated doctrine, a local rule, the wording of the goal, a discrepancy it might report, or how the run would end. The paper reports which relations between world and conduct transported across five principal models and two frontier models. The corpus comprises 167,356 agent shop-days, plus 5,982 frontier shop-days reported separately.

- **Paper:** [`paper/no-neutral-worlds.pdf`](paper/no-neutral-worlds.pdf)
- **Supplement:** [`paper/no-neutral-worlds-supplement.pdf`](paper/no-neutral-worlds-supplement.pdf)
- **Run records:** Zenodo, [doi:10.5281/zenodo.23325311](https://doi.org/10.5281/zenodo.23325311) (see [Data](#data))
- **Registrations:** [`docs/osf/`](docs/osf), mirrored on OSF at [osf.io/2amzd](https://osf.io/2amzd/)

## Versions

The paper is versioned. Each release of this repository is tagged (`v1.0`, `v1.1`, …), and the PDFs in `paper/` are the ones belonging to that tag. Code and run records do not change between paper versions unless the release notes say so.

## Layout

```
tnt_bench/        simulation engine, theme and narration layers, agent harness, analysis
scripts/          run, scoring, analysis and figure scripts for every arm
tests/            engine, harness, analysis and frontier-runner tests
figures/          plotting style and the verified source data behind each paper figure
docs/osf/         preregistrations and dated amendments
docs/             per-arm results ledgers, specimen catalogues and field notes
docs/reviews/     semantic coding records (raters, adjudication, crosswalks)
paper/            the paper and supplement as PDFs
runs/             empty; extract the Zenodo archive here
```

The package is still called `tnt_bench`, its working name. The name is kept because the frozen run plans record SHA-256 hashes of every source file; renaming the package would break those checks.

## Setup

Python 3.12 was used throughout (3.10 or later should work).

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt          # Windows: .venv\Scripts\pip
.venv/bin/pip install -r requirements-figures.txt  # matplotlib, for figures
.venv/bin/python -m pytest
```

`requirements.txt` pins the versions recorded in the frozen run plans. The Opus 5.5 transport additionally used `anthropic==1.8.0`, in `requirements-frontier.txt`.

Figures use Segoe UI where installed and fall back to DejaVu Sans, so regenerated figures can differ in typeface from the published ones.

## Data

The run records are archived on Zenodo ([doi:10.5281/zenodo.23325311](https://doi.org/10.5281/zenodo.23325311)) as one `.tar.xz` per collection, with a `SHA256SUMS` manifest. Extract each archive into `runs/`, so that, for example, `runs/exploit1/` and `runs/transport_gpt6sol_2026-09-27/` exist. Each collection holds its frozen plan or manifest, schedules, narration packs, per-day agent transcripts and journals, raw API logs, and, for later collections, a `source/` snapshot of the code that ran it.

| Collection | Folders |
|---|---|
| Framing discovery and pilot | `main3` (120 agent and 20 baseline paths), `main`, `main2`, `smoke` |
| Gemma framing replication | `replication1` |
| Explicit creed and economy | `doctrine1`, `doctrine2`, `transport1` |
| Frame-by-doctrine crossover | `crossover1` |
| Disclosed cancellation fault | `exploit1`, `exploit_luna1`; excluded pilots `exploit_pilot*` |
| Open discrepancy | `discrepancy1`, `discrepancy_luna1` |
| Terminal-objective ablation | `ablation1` |
| Preregistered Muse/GLM extension | `transport_glm_muse_2026-09-20`; calibration `transport_calibration_*`, `transport_extension_*`, `transport_smoke` |
| Frontier transports | `transport_opus55_2026-09-27`, `transport_gpt6sol_2026-09-27` |
| Exploratory Opus 4.7/4.8 survey | `opus1` |

The paper's corpus accounting (Supplement S1.1 and S1.5) gives the shop-days each collection contributes. Pilot, calibration and smoke folders are included because the paper discloses them; they are not part of the confirmatory totals.

Raw API logs keep the provider's response objects, including OpenAI's encrypted reasoning items, which cannot be decrypted. Reasoning summaries are kept where the provider returned them. Some recovery records contain local file paths from the collection machine.

## Reproducing the results

Scripts are run from the repository root. None of the scoring, analysis or figure scripts makes API calls.

| Arm | Scoring and analysis |
|---|---|
| Frame | `score_predictions.py` (discovery), `score_replication.py`, `score_crossover.py` |
| Doctrine and economy | `score_doctrine.py`, `score_attenuation.py`, `score_transport.py`, `score_crossover.py` |
| Cancellation fault | `python -m tnt_bench analyze-exploit`, `make_exploit_paper_figures.py` |
| Open discrepancy | `python -m tnt_bench analyze-discrepancy`, `make_discrepancy_paper_figures.py` |
| Horizon and ending | `score_ablation.py`, `make_horizon_figures.py`, `endpoint_objective_analysis.py` |
| Muse/GLM extension | `analyse_transport_extension.py`, `endpoint_objective_analysis.py` |
| Frontier transports | `analyse_frontier_transport.py {exploit,results}` |
| Summary figures | `make_transport_paper_figures.py`, `make_summary_figures.py` |
| Opus 4.7/4.8 survey | `score_opus.py` |

The registrations in `docs/osf/` give each arm's frozen analysis plan. Several cite [`docs/PUBLICATION_POLICY.md`](docs/PUBLICATION_POLICY.md), adopted in July 2026, which governed how results were presented (paired contrasts, no leaderboards) and proposed tiered access to run records; its release tier has since been superseded by the full public archive. `figures/out/print/*.json` holds the verified source data for each paper figure, so most figures can be redrawn without the run archive. Figure scripts write to `figures/out/print/` and copy SVGs to `paper/figures/`.

The frozen runners can check that the code matches the plan a collection ran under, for example:

```bash
python scripts/run_frontier_openrouter.py check --out runs/transport_gpt6sol_2026-09-27
```

## Re-running collections

The runners make paid API calls through OpenRouter (`OPENROUTER_API_KEY`) or, for Opus 5.5, the Anthropic API (`ANTHROPIC_API_KEY`). The `prepare` and `check` commands are unpaid. Model identifiers, providers and serving conditions in the frozen plans reflect what was available in July to September 2026, and some will no longer be served.

## Licences

- Code (`tnt_bench/`, `scripts/`, `tests/`, `figures/*.py`): MIT, see [`LICENSE`](LICENSE).
- Paper, supplement, documentation, registrations, coding records, figure data and the archived run records: CC BY 4.0, see [`LICENSE-DATA`](LICENSE-DATA).

Agent transcripts contain text generated by third-party models. Their use may also be subject to the providers' terms.

## Citation

See [`CITATION.cff`](CITATION.cff).
