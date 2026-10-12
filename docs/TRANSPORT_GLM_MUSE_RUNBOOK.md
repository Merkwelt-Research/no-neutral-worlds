# GLM and Muse: running one arm at a time

The selected collection uses existing seeds 13–22 and their existing narration
packs. Kimi K3 is held back. Baseline framing and discrepancy have two independent
agent realizations per cell; supporting arms have one. This is **ten schedule
clusters per model**. The two models are analysed separately.

The full allocation is 640 90-day trajectories plus 80 shared discrepancy
prefixes and 320 ten-day branches. Ordinary-rate projection: approximately
**USD 199**, with illustrative 2×/3× scenarios of **USD 398/597**. These are not
upper bounds; revised-interface probes, retries and audits are additional.
No narration generation is needed. Four workers run by default, at most two per
model. Lower concurrency with `--workers 2` or `--workers 1` if needed.

## First: revised-interface checks

The new protocol discloses the 20-action allowance and permits a separate journal
after exhaustion. Six short probes check it before main collection:

```powershell
.\.venv\Scripts\python.exe scripts\run_transport_extension.py smoke
```

They use reserved calibration seeds, not the main-study schedules. No command
automatically proceeds to another arm.

## Main arms

Run each command separately when ready. The first is:

```powershell
.\.venv\Scripts\python.exe scripts\run_transport_extension.py baseline_frame
```

Then, one at a time:

```powershell
.\.venv\Scripts\python.exe scripts\run_transport_extension.py discrepancy
.\.venv\Scripts\python.exe scripts\run_transport_extension.py frame_doctrine
.\.venv\Scripts\python.exe scripts\run_transport_extension.py doctrine_economy
.\.venv\Scripts\python.exe scripts\run_transport_extension.py exploit
.\.venv\Scripts\python.exe scripts\run_transport_extension.py endpoint_objective
```

Do not paste all five as a batch if you want pauses between arms. Each invocation
uses only the named arm. Frame/doctrine requires the completed baseline controls.
All arm allocations and endpoints are fixed before the first run; reading early
results does not change later designs without a recorded amendment.

## Analyse one while the next runs

For example, after baseline framing completes, start discrepancy in one terminal.
In another terminal, export the baseline's mechanical paired contrasts:

```powershell
.\.venv\Scripts\python.exe scripts\analyse_transport_extension.py baseline_frame
```

Substitute any other arm name after that arm completes. Discrepancy and endpoint
analysis export raw evidence and blank coding fields under `coding/`, preserving
existing filled decisions on subsequent calls. Mechanical supporting analyses
write paired contrasts under `analysis/`. Primary family-wise classification
waits for all baseline and discrepancy coding, then uses `primary` as the
analysis command. Semantic reliability and sensitivity reviews remain required.

Progress and actual billed costs, without waiting for an arm to finish:

```powershell
.\.venv\Scripts\python.exe scripts\run_transport_extension.py summary
```

## If interrupted

### Current command: reviewed recovery with Muse provider fallback

From 23 September 2026, use the reviewed wrapper for the remaining arms:

```powershell
.\.venv\Scripts\python.exe scripts\resume_transport_reviewed.py frame_doctrine --workers 4
```

It resumes automatically; do not add `--resume`. Substitute the next arm name
when ready. To validate recovery without inference, add `--check`.

Muse tries DeepInfra (`deepinfra/bf16`), Phala, Fireworks, then Together, all
serving the same model with the requested parameters required. The price cap
is $0.35 input / $1.50 output per million tokens. GLM remains on Z.AI. The wrapper
retries transient failures after 15, 30, 60, 60 and 60 seconds before stopping;
non-transient, billing and truncation failures still stop for review.

Existing responses are replayed without resampling, even when an unfinished
trajectory moves between providers. Effective routing is saved in each new
attempt's settings; actual provider identities remain in response and day logs.
The dated amendment is
`runs/transport_glm_muse_2026-09-20/reviews/provider_routing_amendment_2026-09-23.json`.
The original frozen plan and runtime sources remain unchanged. No additional
controls or automatic restarts are introduced. Earlier commands below describe
the original fixed-provider runner; use the reviewed wrapper for fallback.

Completed jobs are automatically skipped. For an interrupted arm, append
`--resume`, for example:

```powershell
.\.venv\Scripts\python.exe scripts\run_transport_extension.py baseline_frame --resume
```

Saved responses reconstruct the same decisions without paid resampling. An API
rejection, unexpected provider, truncation or missing billing still needs review.
The runner preserves all attempts and prevents a second arm runner from starting
against this batch. Ctrl+C stops new requests and waits for in-flight requests
to return so their responses and charges can be saved.

## Files and frozen specification

Batch: `runs/transport_glm_muse_2026-09-20/`.
Specification: `docs/osf/TRANSPORT_GLM_MUSE_2026-09-20.md`, copied into the batch.
The local freeze is not an assertion that an OSF submission has occurred.
The former four-model/fresh-pack designs remain as superseded drafts.

The setup command `prepare` fetches public metadata, copies existing packs and
freezes the plan without inference. Once prepared, use `check` to verify it;
do not prepare again into the same directory. Paper edits do not affect the
runner, but frozen runtime or analysis changes require an explicit amendment.
