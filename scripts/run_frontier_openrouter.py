"""Frontier transport: GPT-6 Sol through OpenRouter, pinned to OpenAI.

The same two arms and cells as the Opus 5.5 frontier transport
(run_frontier_transport.py), with the model changed:

- exploit: the 80-cell extension matrix (2 frames x rule x "whatever it
  takes" x schedules 13-22, rich narration, disclosed 90-day horizon), one
  realisation, observed for the first 20 days;
- discrepancy: the baseline-climate matrix (2 frames x schedules 13-22),
  one realisation, clean histories to day 45 with extra/missing branches
  revealed on day 2 and day 46, ten days each.

The model client, recording, exact replay and job layout are the GLM/Muse
extension's (run_transport_extension.py). Differences: provider pinned to
OpenAI's standard endpoint, reasoning effort low, no temperature (the model
takes none), a batch-wide spending cap, a smoke gate on automatic prompt
caching, and the Opus amendment's censoring rule registered in advance: a
model refusal, provider content filter or OpenRouter moderation block ends
that trajectory at that day, with no retry and no other model, and its
unreached outcomes are missing. Preparation and checks make no inference calls.
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
from scripts import run_transport_extension as ext
from tnt_bench.agent.llm import openai_chat_client
from tnt_bench.harness import run as run_module
from tnt_bench.harness.conditions import Condition
from tnt_bench.harness.discrepancy import execute_discrepancy_group
from tnt_bench.harness.run import RunSpec, execute_run
from tnt_bench.themes import ThemedView

DEFAULT_ROOT = ROOT / "runs/transport_gpt6sol_2026-09-27"
EXT_ROOT = ROOT / "runs/transport_glm_muse_2026-09-20"
REGISTRATION = "docs/osf/TRANSPORT_GPT6SOL_2026-09-27.md"  # cites this plan's SHA-256; not frozen inside it
SOURCE_MODEL = "meta/muse-glimmer-30b"  # template cells: identical matrix, model swapped
MODEL = "openai/gpt-6-sol"
ENDPOINT_TAG = "openai"
EXPECTED_PROVIDER = "OpenAI"
ARMS = ("exploit", "discrepancy")
OBSERVE_DAYS = {"exploit": 20}
DEFAULT_CAP_USD = 250.0
AMENDMENT_RULE = ("Registered in advance from the Opus 5.5 amendment: a model refusal, provider content filter or "
                  "OpenRouter moderation block ends the trajectory at that day; no retry, no other model; "
                  "unreached outcomes are missing.")
read, write, rows, append, digest = audit.read, audit.write, audit.rows, audit.append, audit.digest
Stop = audit.CalibrationStop


class Censored(RuntimeError):
    """Refusal or moderation: close the trajectory, keep the batch going."""
    no_retry = True  # the day loop must not retry a censored request

    def __init__(self, info):
        super().__init__(f"censored on day {info.get('day')} ({info.get('category')})")
        self.info = info


# ---------------------------------------------------------------- plan

def frontier_jobs():
    plan = read(EXT_ROOT / "plan.json")
    old, new = SOURCE_MODEL.replace("/", "_"), MODEL.replace("/", "_")
    jobs = []
    for job in plan["jobs"]:
        spec = dict(job["spec"])
        if spec["model"] != SOURCE_MODEL or job["arm"] not in ARMS:
            continue
        if job["arm"] == "discrepancy" and spec["replicate"] != 1:
            continue  # one realisation, as for Opus 5.5
        spec.update(model=MODEL, temperature=None)
        if job["kind"] == "full":
            run_id = ext.parse_spec(spec).run_id
            jobs.append({"arm": job["arm"], "kind": "full", "job_id": run_id, "run_id": run_id, "spec": spec,
                         "observe_days": OBSERVE_DAYS.get(job["arm"])})
        else:
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


def endpoint_profile(root):
    """Pin the calibrated endpoint from the public catalogue (no key, no inference)."""
    catalog = {m["id"]: m for m in audit.get_public("https://openrouter.ai/api/v1/models")["data"]}
    raw = audit.get_public(f"https://openrouter.ai/api/v1/models/{MODEL}/endpoints")
    endpoint = next((e for e in raw["data"]["endpoints"] if e["tag"] == ENDPOINT_TAG and e["status"] == 0), None)
    if endpoint is None or endpoint["provider_name"] != EXPECTED_PROVIDER:
        raise Stop(f"Pinned endpoint unavailable: {MODEL} / {ENDPOINT_TAG}")
    if not {"tools", "tool_choice", "reasoning", "max_tokens"} <= set(endpoint["supported_parameters"]):
        raise Stop("Required parameters unsupported on the pinned endpoint.")
    if "low" not in catalog[MODEL]["reasoning"].get("supported_efforts", []):
        raise Stop("Low reasoning effort unavailable.")
    if (endpoint.get("max_completion_tokens") or 16384) < 16384:
        raise Stop("Output allowance below 16,384 tokens.")
    rates = [endpoint["pricing"], *endpoint["pricing"].get("overrides", [])]
    ceiling = {k: max(float(r.get(k, endpoint["pricing"][k])) for r in rates) for k in ("prompt", "completion")}
    write(root / "catalogue" / (MODEL.replace("/", "_") + ".json"),
          {"at": audit.now(), "model": catalog[MODEL], "endpoints": raw})
    return {"model": MODEL, "endpoint_tag": ENDPOINT_TAG, "expected_provider": EXPECTED_PROVIDER,
            "provider": {"only": [ENDPOINT_TAG], "allow_fallbacks": False, "require_parameters": True,
                         "ignore": sorted({e["tag"] for e in raw["data"]["endpoints"]
                                           if e["tag"].startswith(ENDPOINT_TAG + "/")}),
                         "max_price": {k: v * 1_000_000 for k, v in ceiling.items()}},
            "reasoning": {"effort": "low"}, "temperature": None, "max_tokens": 16384,
            "pricing": endpoint["pricing"], "ceiling_rates": ceiling,
            "transport": "OpenRouter chat completions, OpenAI standard endpoint only, automatic prompt caching",
            "censoring": AMENDMENT_RULE}


def source_hashes():
    files = [p for p in (ROOT / "tnt_bench").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    files += [Path(__file__), ROOT / "scripts/run_transport_extension.py", ROOT / "scripts/calibrate_transport.py",
              ROOT / "scripts/plan_transport_extension.py"]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(files)}


def prepare(root):
    if (root / "plan.json").exists():
        raise Stop("Already prepared; use check. Existing plans are never overwritten.")
    jobs, smoke = frontier_jobs(), smoke_jobs()
    root.mkdir(parents=True, exist_ok=True)
    profile = endpoint_profile(root)
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
    plan = {"created_at": audit.now(), "model": MODEL, "profile": profile, "jobs": jobs, "smoke_jobs": smoke,
            "arm_order": list(ARMS), "observe_days": OBSERVE_DAYS, "cap_usd": DEFAULT_CAP_USD,
            "registration": REGISTRATION,
            "template": {"batch": EXT_ROOT.relative_to(ROOT).as_posix(), "plan_sha256": digest(EXT_ROOT / "plan.json"),
                         "model": SOURCE_MODEL},
            "source_hashes": hashes, "artifact_hashes": artifacts, "runtime": audit.runtime_versions(),
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
    if audit.runtime_versions() != plan["runtime"]:
        raise Stop("Python environment changed since preparation.")
    for name, sha in plan["artifact_hashes"].items():
        if digest(root / name) != sha:
            raise Stop(f"Frozen artifact changed: {name}")
    return plan


# ---------------------------------------------------------------- execution

class SpendGuard:
    """Batch-wide cap: settled provider-billed cost plus open reservations."""

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


def cache_summary(raw):
    usage = raw.get("usage") or {}
    prompt = usage.get("prompt_tokens_details") or {}
    completion = usage.get("completion_tokens_details") or {}
    return {"prompt_tokens": usage.get("prompt_tokens") or 0, "cached_tokens": prompt.get("cached_tokens") or 0,
            "cache_write_tokens": prompt.get("cache_write_tokens") or 0,
            "completion_tokens": usage.get("completion_tokens") or 0,
            "reasoning_tokens": completion.get("reasoning_tokens") or 0}


def refusal(raw):
    choice = (raw.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    if choice.get("finish_reason") == "content_filter":
        return "content_filter"
    if message.get("refusal"):
        return "model_refusal"
    return None


def valid_response(raw, profile):
    return ext.valid_response(raw, profile) and str(raw.get("model", "")).startswith(MODEL)


def moderation_block(error):
    text = str(error).lower()
    return type(error).__name__ == "PermissionDeniedError" and ("moderat" in text or "flag" in text)


def measured_chat(profile, path, key, stop, guard):
    state = {}

    def before(request):
        if stop.is_set():
            raise Stop("Batch interrupted; request not sent.")
        request_id = os.urandom(8).hex()
        nbytes = len(json.dumps(request, ensure_ascii=False).encode("utf-8"))
        rates = profile["ceiling_rates"]
        guard.reserve(request_id, (nbytes / 3) * rates["prompt"] + profile["max_tokens"] * rates["completion"])
        match = re.search(r"=== DAY (\d+)", request["messages"][1]["content"])
        state.update(request_id=request_id, start=time.monotonic(), day=int(match.group(1)) if match else None)
        append(path, {"kind": "request", "at": audit.now(), "request_id": request_id, "day": state["day"],
                      "request": request})

    def after(raw):
        cost = (raw.get("usage") or {}).get("cost")
        guard.settle(state["request_id"], cost if isinstance(cost, (int, float)) else 0.0)
        append(path, {"kind": "response", "at": audit.now(), "request_id": state["request_id"],
                      "seconds": time.monotonic() - state["start"], "cost": cost, "cache": cache_summary(raw),
                      "response": raw})
        category = refusal(raw)
        if category:
            message = ((raw.get("choices") or [{}])[0].get("message") or {})
            raise Censored({"day": state["day"], "category": category, "pre_output": not message.get("content"),
                            "refusal": message.get("refusal")})
        if not valid_response(raw, profile):
            raise Stop("Unexpected model or provider, missing billing, or truncated output; response preserved for review.")

    client = openai_chat_client(key, MODEL, temperature=None, max_retries=0, provider=profile["provider"],
                                reasoning=profile["reasoning"], max_tokens=profile["max_tokens"], strict=True,
                                before_request=before, on_response=after)

    def chat(messages, tools):
        for attempt in range(3):
            try:
                return client(messages, tools)
            except (Stop, Censored):
                raise
            except Exception as error:
                append(path, {"kind": "error", "at": audit.now(), "request_id": state.get("request_id"),
                              "error_type": type(error).__name__, "message": str(error)[:1000]})
                guard.settle(state.get("request_id"), 0.0)
                if moderation_block(error):
                    raise Censored({"day": state.get("day"), "category": "moderation", "pre_output": True,
                                    "message": str(error)[:500]}) from error
                if type(error).__name__ in audit.TRANSIENT_ERRORS and attempt < 2:
                    if stop.wait((5, 15)[attempt]):
                        raise Stop("Batch interrupted; retry not sent.") from error
                    continue
                raise Stop(f"{type(error).__name__}; attempt preserved. Review, then --resume.") from error
    return chat


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


def observed_days(attempt):
    return sum(len(rows(p)) for p in (attempt / "data").rglob("days.jsonl"))


def smoke_cache_gate(path):
    responses = [e for e in rows(path) if e["kind"] == "response"]
    by_day = Counter(e["request_id"] for e in responses)
    prompt = sum(e["cache"]["prompt_tokens"] for e in responses)
    cached = sum(e["cache"]["cached_tokens"] for e in responses)
    return {"pass": cached > 0, "cache_read_share": cached / prompt if prompt else 0.0,
            "cache_write_tokens": sum(e["cache"]["cache_write_tokens"] for e in responses),
            "reasoning_tokens": sum(e["cache"]["reasoning_tokens"] for e in responses),
            "cost_usd": sum(e["cost"] or 0 for e in responses), "responses": len(by_day)}


def execute_job(root, plan, job, key, stop, guard, resume=False, chat_factory=None):
    base = ext.job_directory(root, job)
    if ext.completed(root, job):
        return "already complete"
    existing = sorted(base.glob("attempt-*"), key=lambda p: int(p.name.split("-")[-1]))
    if existing and not resume:
        raise Stop(f"Interrupted attempt for {job['job_id']}; use --resume to replay saved decisions.")
    settings = json.loads(json.dumps({"job": job, "profile": plan["profile"], "plan_sha256": digest(root / "plan.json")}))
    pairs, pending = ext.history(existing[-1], settings) if existing else ([], None)
    attempt = base / f"attempt-{len(existing) + 1}"
    attempt.mkdir(parents=True, exist_ok=False)
    write(attempt / "settings.json", settings)
    if existing:
        (existing[-1] / "api_calls.jsonl").touch(exist_ok=True)
        write(attempt / "recovery.json", {"source": str(existing[-1].resolve()),
                                          "api_sha256": digest(existing[-1] / "api_calls.jsonl"),
                                          "saved_responses": len(pairs), "at": audit.now()})
    (attempt / "api_calls.jsonl").touch(exist_ok=False)
    factory = chat_factory or (lambda path: measured_chat(plan["profile"], path, key, stop, guard))
    chat = ext.ReplayingChat(pairs, pending, factory(attempt / "api_calls.jsonl"))
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
                raise Stop("Smoke: no cached prompt tokens within a day; caching is not engaging. Review before collection.")
        else:
            result = execute_run(spec, artifacts, chat, pack)
            observed = len(rows(artifacts / job["run_id"] / "days.jsonl"))
            result = {**result, "observe_days": job.get("observe_days"), "observed_days": observed}
        if chat.index != len(pairs) or chat.pending is not None:
            raise Stop("Recovery finished before consuming the saved trajectory; review required.")
        write(attempt / "complete.json", {"at": audit.now(), "job_id": job["job_id"], "result": result})
    except Censored as error:
        if job["kind"] == "smoke":
            write(attempt / "stopped.json", {"at": audit.now(), "type": "Censored", "message": str(error)})
            raise Stop(f"Smoke censored ({error}); review before collection.") from error
        write(attempt / "complete.json", {"at": audit.now(), "job_id": job["job_id"],
                                          "result": {"censored": True, **error.info,
                                                     "observed_days": observed_days(attempt),
                                                     "rule": AMENDMENT_RULE}})
        print(f"Censored {job['job_id']}: {error}", flush=True)
        return job["job_id"]
    except BaseException as error:
        write(attempt / "stopped.json", {"at": audit.now(), "type": type(error).__name__, "message": str(error)})
        raise
    print(f"Completed {job['job_id']}", flush=True)
    return job["job_id"]


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
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise Stop("OPENROUTER_API_KEY is not set in this process.")
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
        prompt = sum(e["cache"]["prompt_tokens"] for e in log)
        done = [ext.completed(root, j) for j in jobs]
        censored = sum(bool(d and read(d / "complete.json")["result"].get("censored")) for d in done)
        out.append({"arm": arm, "planned": len(jobs), "completed": sum(d is not None for d in done),
                    "censored": censored, "responses": len(log), "cost_usd": round(sum(e["cost"] or 0 for e in log), 2),
                    "cache_read_share": round(sum(e["cache"]["cached_tokens"] for e in log) / prompt, 3) if prompt else None,
                    "reasoning_tokens": sum(e["cache"]["reasoning_tokens"] for e in log)})
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
