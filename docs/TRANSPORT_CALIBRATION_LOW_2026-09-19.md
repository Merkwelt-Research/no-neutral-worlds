# Transport calibration: lower reasoning, 19 September 2026

## Amendment: DeepSeek shelved after short checks

At the author's request, DeepSeek was removed from the remaining smoke and full
queues for excessive latency, including an approximately eight-minute request
at low reasoning. Its existing artifacts and failed fantasy gate remain intact.
The gate failure involved an unaffordable order on an action-exhausted day;
it has not been reclassified as a pass. Behavioural endpoints were not the
exclusion criterion.

The original plan and checksum are archived under
`amendments/01-shelve-deepseek/` within the batch, alongside a record linking the
old and amended plan hashes. Model profiles, simulation, prompts, seeds, packs,
gates and source hashes are unchanged. Earlier settings records retain their
original plan hash. The specifications below describe the original six-model
plan; the active queues now contain 15 short checks and five full runs.

Ten short checks for the five retained models have already passed. Running the
same `smoke` command skips those and runs only the five unstarted neutral exploit
checks. It also skips DeepSeek's failed case. No new attempt number is needed.

## Purpose and scope

The default-setting calibration made one DeepSeek ordinary trajectory take about
four hours of request time. This separate feasibility batch selects lower
reasoning settings before observing its outcomes. It measures technical
reliability, cost and elapsed request time. Neither batch contributes to the
confirmatory sample; model inclusion and settings should not depend on whether
the behavioural contrasts are favourable.

The previous batch remains in `runs/transport_calibration_2026-09-19b`, including
its frozen plan, logs, interrupted attempts and an archived copy of the runner
(`runner-before-low-calibration.py`). The new batch is
`runs/transport_calibration_low_2026-09-19`. Its costs are accounted separately.
The current runner's source validation intentionally prevents continuing an old
plan after the runner changes; the old artifacts remain available for review.

## Frozen settings

| Model | Requested reasoning |
|---|---|
| DeepSeek V4.1 Flash | low |
| GLM 5.3 Flash | low |
| Muse Glimmer 30B | low |
| Gemini 3.7 Flash | low |
| Kimi K2.6 | disabled (`enabled: false`) |
| Kimi K3 | low |

K2.6 exposes optional thinking without a named low effort setting. Thinking off
is a distinct configuration, not a claim of equal compute across models. Live
catalogue snapshots verify the available settings at preparation. Providers
remain fixed and parameter/provider fallbacks remain disabled. Returned reasoning
is recorded when present; it is exploratory material, not a faithfulness measure.
See [OpenRouter's reasoning documentation](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).

DeepSeek retains its 32,768 output ceiling following the earlier truncation;
other models retain 16,384. Lowering reasoning, rather than clipping outputs,
is the intended latency intervention. All treatment comparisons within a model
in the future main collection must use the same preselected configuration.

## Fixed run counts

- Short stage: three days in ordinary, exploit fantasy and exploit neutral for
  each of six models: 18 probes, 54 simulated days.
- Full stage: one ordinary 90-day trajectory per model: six trajectories,
  at most 540 simulated days. Bankruptcy remains an allowed natural termination.
- The full stage requires all 18 short checks to pass. It starts only on a
  separate command, allowing a latency/cost review first.

The ordinary case is selected in advance, provides comparison with the existing
default-setting trajectory, and tests long-history costs. Full-length exploit
costs remain uncertain; the short exploit probes do not establish an upper bound.
Execution remains sequential. There is no mandatory spending ceiling; the optional
`--budget-usd` guard and durable accounting remain available.

Prompts, mechanics, 90-day disclosed objective, seeds (900001 and 12), frozen
narration packs and technical gates retain the previous calibration specification.
The agreed future action-budget disclosure and post-exhaustion journal change
remain separate work for the main protocol. Both seeds remain calibration-only.

## Running

Preparation and validation make no inference requests:

```powershell
.\.venv\Scripts\python.exe scripts\calibrate_transport.py prepare
.\.venv\Scripts\python.exe scripts\calibrate_transport.py check
```

After stopping the previous batch, run the short checks:

```powershell
.\.venv\Scripts\python.exe scripts\calibrate_transport.py smoke
```

The runner refuses to start if the previous batch's recorded process is still
active. It preserves old lock files and artifacts. Once the short checks are
reviewed, the full stage and summary commands are:

```powershell
.\.venv\Scripts\python.exe scripts\calibrate_transport.py full
.\.venv\Scripts\python.exe scripts\calibrate_transport.py summary
```

All these commands now default to the new lower-reasoning directory. Use an
explicit `--out` to inspect a different batch. An interrupted attempt is preserved;
review it before selecting a new attempt number or replay recovery.
