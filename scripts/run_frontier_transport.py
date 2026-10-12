"""Frontier transport: Claude Opus 5.5 through the direct Anthropic API.

Two arms from the preregistered GLM/Muse design, run one per invocation:

- exploit: the 80-cell extension matrix (2 frames x rule x "whatever it
  takes" x schedules 13-22, rich narration, disclosed 90-day horizon), one
  realisation, observed for the first 20 days;
- discrepancy: the baseline-climate matrix (2 frames x schedules 13-22),
  one realisation, clean histories to day 45 with extra/missing branches
  revealed on day 2 and day 46, ten days each.

Preparation and checks make no inference calls. Recording, exact replay on
recovery, and stop-for-review follow run_transport_extension.py; the model
client, response validation, cost accounting and the day-20 observation
window are the only differences. A hard spending cap applies across the batch.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
import dataclasses
import json
import os
from pathlib import Path
import re
import shutil
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import calibrate_transport as audit
from scripts import frontier_anthropic as fa
from scripts import run_transport_extension as ext
from tnt_bench.harness import run as run_module
from tnt_bench.harness.conditions import Condition
from tnt_bench.harness.discrepancy import execute_discrepancy_group
from tnt_bench.harness.run import RunSpec, execute_run
from tnt_bench.themes import ThemedView

DEFAULT_ROOT = ROOT / "runs/transport_opus55_2026-09-27"
EXT_ROOT = ROOT / "runs/transport_glm_muse_2026-09-20"
REGISTRATION = "docs/osf/TRANSPORT_OPUS55_2026-09-27.md"  # cites this plan's SHA-256; not frozen inside it
SOURCE_MODEL = "meta/muse-glimmer-30b"  # template cells: identical matrix, model swapped
MODEL = fa.MODEL
ARMS = ("exploit", "discrepancy")
OBSERVE_DAYS = {"exploit": 20}
DEFAULT_CAP_USD = 750.0
PROFILE = {"model": MODEL, "effort": "low", "max_tokens": 16384, "thinking_display": "summarized",
           "sampling": "API default (Opus 5.5 rejects temperature)", "prices_per_mtok": fa.PRICES,
           "transport": "Anthropic Messages API (direct), prompt caching, thinking-binding drop_block"}
read, write, rows, append, digest = audit.read, audit.write, audit.rows, audit.append, audit.digest
Stop = audit.CalibrationStop


# ---------------------------------------------------------------- plan

def frontier_jobs():
    plan = read(EXT_ROOT / "plan.json")
    jobs = []
    for job in plan["jobs"]:
        spec = dict(job["spec"])
        if spec["model"] != SOURCE_MODEL or job["arm"] not in ARMS:
            continue
        if job["arm"] == "discrepancy" and spec["replicate"] != 1:
            continue  # A-lite: one realisation
        spec.update(model=MODEL, temperature=None)
        if job["kind"] == "full":
            run_id = ext.parse_spec(spec).run_id
            jobs.append({"arm": job["arm"], "kind": "full", "job_id": run_id, "run_id": run_id, "spec": spec,
                         "observe_days": OBSERVE_DAYS.get(job["arm"])})
        else:
            old = SOURCE_MODEL.replace("/", "_")
            new = MODEL.replace("/", "_")
            prefix = job["prefix_id"].replace(old, new)
            jobs.append({"arm": "discrepancy", "kind": "group", "job_id": prefix, "prefix_id": prefix, "spec": spec,
                         "branches": [b.replace(old, new) for b in job["branches"]]})
    counts = Counter(j["arm"] for j in jobs)
    if counts != Counter({"exploit": 80, "discrepancy": 20}):
        raise Stop(f"Unexpected frontier matrix: {dict(counts)}")
    return jobs


def smoke_jobs():
    out = []
    for name, frame, seed, exploit in [("ordinary", "neutral", 900001, None),
                                       ("exploit_fantasy", "fantasy", 12, "ambiguous_wit")]:
        spec = RunSpec(MODEL, Condition(frame, "rich" if exploit else "static"), seed, horizon=90,
                       temperature=None, exploit_condition=exploit, action_protocol="disclosed_journal_v1")
        out.append({"job_id": MODEL + "__" + name, "kind": "smoke", "arm": "smoke", "spec": dataclasses.asdict(spec)})
    return out


def source_hashes():
    files = [p for p in (ROOT / "tnt_bench").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    files += [Path(__file__), ROOT / "scripts/frontier_anthropic.py", ROOT / "scripts/run_transport_extension.py",
              ROOT / "scripts/calibrate_transport.py"]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(files)}


def runtime():
    import anthropic
    return {**audit.runtime_versions(), "anthropic_sdk": anthropic.__version__, "sdk_path": str(fa.DEPS)}


def prepare(root):
    if (root / "plan.json").exists():
        raise Stop("Already prepared; use check. Existing plans are never overwritten.")
    jobs, smoke = frontier_jobs(), smoke_jobs()
    root.mkdir(parents=True, exist_ok=True)
    for sub in ("packs", "schedules"):
        (root / sub).mkdir(exist_ok=True)
        for p in (EXT_ROOT / sub).iterdir():
            shutil.copy2(p, root / sub / p.name)
    artifacts = {p.relative_to(root).as_posix(): digest(p) for d in ("packs", "schedules")
                 for p in (root / d).iterdir() if p.is_file()}
    hashes = source_hashes()
    for name in hashes:
        target = root / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    plan = {"created_at": audit.now(), "model": MODEL, "profile": PROFILE, "jobs": jobs, "smoke_jobs": smoke,
            "arm_order": list(ARMS), "observe_days": OBSERVE_DAYS, "cap_usd": DEFAULT_CAP_USD,
            "registration": REGISTRATION,
            "template": {"batch": EXT_ROOT.relative_to(ROOT).as_posix(), "plan_sha256": digest(EXT_ROOT / "plan.json"),
                         "model": SOURCE_MODEL},
            "source_hashes": hashes, "artifact_hashes": artifacts, "runtime": runtime(),
            "max_workers": 6}
    write(root / "plan.json", plan)
    (root / "plan.sha256").write_text(digest(root / "plan.json") + "\n", encoding="ascii")
    check(root)


def check(root):
    if digest(root / "plan.json") != (root / "plan.sha256").read_text().strip():
        raise Stop("Frozen plan changed.")
    plan = read(root / "plan.json")
    if source_hashes() != plan["source_hashes"]:
        raise Stop("Frozen runtime/analysis source changed; record an amendment before continuing.")
    if runtime() != plan["runtime"]:
        raise Stop("Python environment or SDK changed since preparation.")
    for name, sha in plan["artifact_hashes"].items():
        if digest(root / name) != sha:
            raise Stop(f"Frozen artifact changed: {name}")
    return plan


# ---------------------------------------------------------------- execution

class SpendGuard:
    """Batch-wide cap: settled provider-priced cost plus open reservations."""

    def __init__(self, root, cap):
        self.cap, self.lock, self.open = cap, threading.Lock(), {}
        self.spent = sum(e.get("cost") or 0 for p in root.glob("*/*/attempt-*/api_calls.jsonl")
                         for e in rows(p) if e["kind"] == "response")

    def reserve(self, key, amount):
        with self.lock:
            if self.spent + sum(self.open.values()) + amount > self.cap:
                raise Stop(f"Spending cap ${self.cap:.2f}: ${self.spent:.2f} settled; request not sent.")
            self.open[key] = amount

    def settle(self, key, cost):
        with self.lock:
            self.open.pop(key, None)
            self.spent += cost


def valid_response(raw):
    usage = raw.get("usage") or {}
    return (str(raw.get("model", "")).startswith(MODEL) and raw.get("stop_reason") in ("end_turn", "tool_use")
            and isinstance(usage.get("output_tokens"), int))


def measured_chat(path, key, stop, guard):
    state = {}

    def before(request):
        if stop.is_set():
            raise Stop("Batch interrupted; request not sent.")
        request_id = os.urandom(8).hex()
        nbytes = len(json.dumps(request["body"], ensure_ascii=False).encode("utf-8"))
        guard.reserve(request_id, (nbytes / 3) * fa.PRICES["input"] / 1e6 + PROFILE["max_tokens"] * fa.PRICES["output"] / 1e6)
        state.update(request_id=request_id, start=time.monotonic())
        match = re.search(r"=== DAY (\d+)", request["messages"][1]["content"])
        append(path, {"kind": "request", "at": audit.now(), "request_id": request_id,
                      "day": int(match.group(1)) if match else None, "request": request})

    def after(raw):
        cost = fa.response_cost(raw)
        guard.settle(state["request_id"], cost)
        append(path, {"kind": "response", "at": audit.now(), "request_id": state["request_id"],
                      "seconds": time.monotonic() - state["start"], "cost": cost,
                      "cache": fa.cache_summary(raw), "thinking_dropped": fa.dropped_thinking(raw), "response": raw})
        if not valid_response(raw):
            raise Stop("Unexpected model, refusal or truncated output; response preserved for review.")

    client = fa.anthropic_chat_client(key, MODEL, effort=PROFILE["effort"], max_tokens=PROFILE["max_tokens"],
                                      before_request=before, on_response=after)

    def chat(messages, tools):
        for attempt in range(3):
            try:
                return client(messages, tools)
            except (Stop, fa.ReviewStop):
                raise
            except Exception as error:
                append(path, {"kind": "error", "at": audit.now(), "request_id": state.get("request_id"),
                              "error_type": type(error).__name__, "message": str(error)[:1000]})
                guard.settle(state.get("request_id"), 0.0)
                transient = type(error).__name__ in audit.TRANSIENT_ERRORS or "Overloaded" in type(error).__name__
                if transient and attempt < 2:
                    if stop.wait((5, 15)[attempt]):
                        raise Stop("Batch interrupted; retry not sent.") from error
                    continue
                raise Stop(f"{type(error).__name__}; attempt preserved. Review, then --resume.") from error
    return chat


def history(source, settings, seen=None):
    seen = set() if seen is None else seen
    source = source.resolve()
    if source in seen or read(source / "settings.json") != settings:
        raise Stop("Recovery ancestry/settings mismatch.")
    seen.add(source)
    pairs, pending = [], None
    if (source / "recovery.json").exists():
        parent = read(source / "recovery.json")
        if digest(Path(parent["source"]) / "api_calls.jsonl") != parent["api_sha256"]:
            raise Stop("Recovery source log changed.")
        pairs, pending = history(Path(parent["source"]), settings, seen)
    for event in rows(source / "api_calls.jsonl"):
        if event["kind"] == "request":
            if pending and (pending["request"]["messages"], pending["request"]["tools"]) != (
                    event["request"]["messages"], event["request"]["tools"]):
                raise Stop("Recovery found changed inputs after an unanswered request.")
            pending = event
        elif event["kind"] == "response":
            if not pending or pending["request_id"] != event["request_id"] or not valid_response(event["response"]):
                raise Stop("Cannot replay an invalid or truncated response; technical review required.")
            pairs.append((pending["request"], event["response"]))
            pending = None
        elif event["kind"] == "error" and event["error_type"] not in audit.TRANSIENT_ERRORS:
            raise Stop("Non-transient error requires review before recovery.")
    return pairs, pending["request"] if pending else None


class ReplayingChat:
    def __init__(self, pairs, pending, live):
        self.pairs, self.pending, self.live, self.index = pairs, pending, live, 0

    def __call__(self, messages, tools):
        expected = self.pairs[self.index][0] if self.index < len(self.pairs) else self.pending
        if expected is not None and (messages != expected["messages"] or tools != expected["tools"]):
            raise Stop(f"Recovery request mismatch at call {self.index + 1}; no new inference issued.")
        if self.index < len(self.pairs):
            raw = self.pairs[self.index][1]
            self.index += 1
            return fa.parse_response(raw)
        self.pending = None
        return self.live(messages, tools)


@contextmanager
def observation_window(days):
    """Stop a full run after `days` played days; the world still states 90."""
    if days is None:
        yield
        return
    class ObservedView(ThemedView):
        @property
        def done(self):
            return self.engine.done or self.engine.state.day > days
    original = run_module.ThemedView
    run_module.ThemedView = ObservedView
    try:
        yield
    finally:
        run_module.ThemedView = original


def execute_job(root, plan, job, key, stop, guard, resume=False, chat_factory=None):
    base = ext.job_directory(root, job)
    if ext.completed(root, job):
        return "already complete"
    existing = sorted(base.glob("attempt-*"), key=lambda p: int(p.name.split("-")[-1]))
    if existing and not resume:
        raise Stop(f"Interrupted attempt for {job['job_id']}; use --resume to replay saved decisions.")
    settings = json.loads(json.dumps({"job": job, "profile": plan["profile"], "plan_sha256": digest(root / "plan.json")}))
    pairs, pending = history(existing[-1], settings) if existing else ([], None)
    attempt = base / f"attempt-{len(existing) + 1}"
    attempt.mkdir(parents=True, exist_ok=False)
    write(attempt / "settings.json", settings)
    if existing:
        (existing[-1] / "api_calls.jsonl").touch(exist_ok=True)
        write(attempt / "recovery.json", {"source": str(existing[-1].resolve()),
                                          "api_sha256": digest(existing[-1] / "api_calls.jsonl"),
                                          "saved_responses": len(pairs), "at": audit.now()})
    (attempt / "api_calls.jsonl").touch(exist_ok=False)
    factory = chat_factory or (lambda path: measured_chat(path, key, stop, guard))
    chat = ReplayingChat(pairs, pending, factory(attempt / "api_calls.jsonl"))
    spec = ext.parse_spec(job["spec"], job["kind"] == "group")
    pack = ext.pack_for(root, spec)
    artifacts = attempt / "data"
    artifacts.mkdir()
    print(f"Starting {job['arm']}: {job['job_id']} (reusing {len(pairs)} saved responses)", flush=True)
    try:
        if job["kind"] == "group":
            result = execute_discrepancy_group(spec, artifacts, chat, pack)
        elif job["kind"] == "smoke":
            result = ext.smoke_run(spec, artifacts, chat, pack)
            result["cache"] = smoke_cache_gate(attempt / "api_calls.jsonl")
            if not result["cache"]["pass"]:
                raise Stop("Smoke: no cache reads within a day; caching is not engaging. Review before collection.")
        else:
            result = execute_run(spec, artifacts, chat, pack)
            observed = len(rows(artifacts / job["run_id"] / "days.jsonl"))
            result = {**result, "observe_days": job.get("observe_days"), "observed_days": observed}
        if chat.index != len(pairs) or chat.pending is not None:
            raise Stop("Recovery finished before consuming the saved trajectory; review required.")
        write(attempt / "complete.json", {"at": audit.now(), "job_id": job["job_id"], "result": result})
    except BaseException as error:
        write(attempt / "stopped.json", {"at": audit.now(), "type": type(error).__name__, "message": str(error)})
        raise
    print(f"Completed {job['job_id']}", flush=True)
    return job["job_id"]


def smoke_cache_gate(path):
    responses = [e for e in rows(path) if e["kind"] == "response"]
    reads = sum(e["cache"]["cache_read_input_tokens"] for e in responses)
    prompt = sum(sum(e["cache"][k] for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
                 for e in responses)
    return {"pass": reads > 0, "cache_read_share": reads / prompt if prompt else 0.0,
            "cost_usd": sum(e["cost"] for e in responses), "responses": len(responses),
            "thinking_dropped": sum(len(e["thinking_dropped"]) for e in responses)}


def run(root, arm, resume=False, workers=4, cap=None):
    plan = check(root)
    if not 1 <= workers <= plan["max_workers"]:
        raise Stop(f"Workers must be 1-{plan['max_workers']}.")
    jobs = plan["smoke_jobs"] if arm == "smoke" else [j for j in plan["jobs"] if j["arm"] == arm]
    if arm != "smoke" and any(not ext.completed(root, j) for j in plan["smoke_jobs"]):
        raise Stop("Run smoke first: interface and caching checks must pass before main collection.")
    todo = [j for j in jobs if not ext.completed(root, j)]
    if not todo:
        print(f"{arm}: all {len(jobs)} jobs already complete; no requests."); return
    if not resume and any(list(ext.job_directory(root, j).glob("attempt-*")) for j in todo):
        raise Stop("Interrupted attempts present. Use --resume; existing traces will be replayed, not regenerated.")
    key = os.environ.get("ANTHROPIC_API_KEY")  # None lets the SDK use an `ant auth login` profile
    guard = SpendGuard(root, cap if cap is not None else plan["cap_usd"])
    lock = root / "running.lock"
    if lock.exists():
        pid = int(lock.read_text().strip())
        if audit.process_alive(pid):
            raise Stop(f"Frontier runner already active (PID {pid}).")
        lock.unlink()
    with lock.open("x", encoding="ascii") as stream:
        stream.write(str(os.getpid()))
    stop, active, errors = threading.Event(), {}, []
    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        with observation_window(OBSERVE_DAYS.get(arm)):
            while todo or active:
                while todo and len(active) < workers and not stop.is_set():
                    job = todo.pop(0)
                    active[pool.submit(execute_job, root, plan, job, key, stop, guard, resume)] = job
                if not active:
                    break
                done, _ = wait(active, timeout=30, return_when=FIRST_COMPLETED)
                if not done:
                    print(f"{arm}: {len(active)} active; {len(todo)} queued; ${guard.spent:.2f} settled.", flush=True)
                for future in done:
                    job = active.pop(future)
                    try:
                        future.result()
                    except Exception as error:
                        errors.append(f"{job['job_id']}: {error}")
                        stop.set()
        if errors:
            raise Stop("\n".join(errors))
    except KeyboardInterrupt:
        stop.set()
        print("Stopping after in-flight requests return; artifacts and billed responses are preserved.", flush=True)
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
        lock.unlink(missing_ok=True)
    print(f"{arm} finished; ${guard.spent:.2f} settled across the batch. No next arm starts automatically.")


def summary(root):
    plan = read(root / "plan.json")
    out = []
    for arm in ("smoke",) + ARMS:
        jobs = plan["smoke_jobs"] if arm == "smoke" else [j for j in plan["jobs"] if j["arm"] == arm]
        log = [e for p in (root / arm).glob("*/attempt-*/api_calls.jsonl") for e in rows(p) if e["kind"] == "response"]
        prompt = sum(sum(e["cache"][k] for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
                     for e in log)
        out.append({"arm": arm, "planned": len(jobs), "completed": sum(ext.completed(root, j) is not None for j in jobs),
                    "responses": len(log), "cost_usd": round(sum(e["cost"] for e in log), 2),
                    "cache_read_share": round(sum(e["cache"]["cache_read_input_tokens"] for e in log) / prompt, 3) if prompt else None,
                    "thinking_dropped": sum(len(e["thinking_dropped"]) for e in log)})
    write(root / "status.json", out)
    print(json.dumps(out, indent=2))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "check", "summary", "smoke", *ARMS))
    parser.add_argument("--out", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--cap", type=float, default=None, help="batch spending cap in USD (default: frozen plan)")
    args = parser.parse_args()
    root = args.out.resolve()
    if args.command == "prepare":
        prepare(root); summary(root)
    elif args.command == "check":
        check(root); print("Frozen plan, runtime, packs and sources verified. No inference calls.")
    elif args.command == "summary":
        summary(root)
    else:
        run(root, args.command, args.resume, args.workers, args.cap)


if __name__ == "__main__":
    try:
        main()
    except (Stop, FileExistsError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
