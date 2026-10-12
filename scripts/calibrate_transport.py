"""Prepare and run an isolated transport calibration; no paid calls by default.

Run from the repository root with .venv/Scripts/python.exe.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import random
import sys
import time
import urllib.request
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tnt_bench.agent.day_loop import MAX_TOOL_CALLS_PER_DAY, ChatResponse, run_agent_day
from tnt_bench.agent.llm import _tool_call, openai_chat_client
from tnt_bench.engine import Engine, EngineConfig, generate_schedule
from tnt_bench.harness.conditions import Condition
from tnt_bench.harness.matrix import ensure_pack
from tnt_bench.harness.run import RunSpec, execute_run
from tnt_bench.themes import ThemedView, load_theme

DEFAULT_ROOT = ROOT / "runs/transport_calibration_low_2026-09-19"
PREVIOUS_ROOT = ROOT / "runs/transport_calibration_2026-09-19b"
# DeepSeek's origin host is excluded by the account's no-training policy.
# Keep a fixed compatible host rather than relaxing that account policy.
MODEL_ENDPOINTS = {
    "deepseek/deepseek-v4.1-flash": "deepinfra/fp8",
    "z-ai/glm-5.3-flash": "z-ai/fp8",
    "meta/muse-glimmer-30b": "phala",
    "google/gemini-3.7-flash": "google-ai-studio",
    "moonshotai/kimi-k2.6": "moonshotai/int4",
    "moonshotai/kimi-k3": "moonshotai/mxfp4",
}
FRESH_SEED = 900001
PACK_SEED = 12  # Lowest numbered paired frozen pack in runs/exploit1/packs.


class CalibrationStop(RuntimeError):
    no_retry = True


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append(path, data):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(data, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()] if Path(path).exists() else []


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hashes():
    paths = [p for p in (ROOT / "tnt_bench").rglob("*")
             if p.is_file() and "__pycache__" not in p.parts]
    paths += [Path(__file__)]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}


def runtime_versions():
    return {"python": sys.version, "packages": {
        d.metadata["Name"]: d.version for d in importlib.metadata.distributions()
    }}


def get_public(url):
    with urllib.request.urlopen(url, timeout=45) as response:
        return json.load(response)


def calibration_reasoning(model, metadata):
    """Choose feasibility settings before observing the new batch's behaviour."""
    if model == "moonshotai/kimi-k2.6":
        if metadata.get("mandatory") is not False:
            raise CalibrationStop(f"Cannot verify optional thinking: {model}")
        return {"enabled": False}
    if "low" not in (metadata.get("supported_efforts") or []):
        raise CalibrationStop(f"Low reasoning unavailable: {model}")
    return {"effort": "low"}


def stage_queue(plan, stage):
    return plan.get("full_queue", plan["queue"]) if stage == "full" else plan["queue"]


def process_alive(pid):
    if pid <= 0:
        raise CalibrationStop("Invalid PID in previous batch lock; inspect before starting.")
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            if ctypes.get_last_error() == 87:  # No such process.
                return False
            raise CalibrationStop(f"Cannot check previous runner PID {pid}; inspect before starting.")
        try:
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                raise CalibrationStop(f"Cannot check previous runner PID {pid}.")
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def check_previous_runners(plan):
    for directory in plan.get("exclusive_with_batches", []):
        lock = ROOT / directory / "running.lock"
        if lock.exists():
            try:
                pid = int(lock.read_text().strip())
            except ValueError:
                raise CalibrationStop(f"Unreadable previous runner lock: {lock}") from None
            if process_alive(pid):
                raise CalibrationStop(f"Previous calibration is still active (PID {pid}); stop it before starting this batch.")


def prepare(root):
    if (root / "plan.json").exists():
        raise CalibrationStop("Plan already frozen; use a new output directory to revise it.")
    catalog = get_public("https://openrouter.ai/api/v1/models")
    models = {m["id"]: m for m in catalog["data"]}
    profiles = []
    for model, tag in MODEL_ENDPOINTS.items():
        raw = get_public(f"https://openrouter.ai/api/v1/models/{model}/endpoints")
        endpoint = next(e for e in raw["data"]["endpoints"] if e["tag"] == tag and e["status"] == 0)
        supported = set(endpoint["supported_parameters"])
        if not {"tools", "tool_choice", "max_tokens", "reasoning"} <= supported:
            raise CalibrationStop(f"Required parameters unavailable: {model}, {tag}")
        reasoning = models[model].get("reasoning", {})
        reasoning_request = calibration_reasoning(model, reasoning)
        max_tokens = 32768 if model.startswith("deepseek/") else 16384
        pricing = endpoint["pricing"]
        rates = [pricing, *pricing.get("overrides", [])]
        ceilings = {key: max(float(r.get(key, pricing[key])) for r in rates)
                    for key in ("prompt", "completion")}
        profile = {
            "model": model, "endpoint_tag": tag,
            "expected_provider": endpoint["provider_name"],
            "quantization": endpoint.get("quantization"),
            "provider": {"only": [tag], "allow_fallbacks": False, "require_parameters": True,
                         "ignore": sorted({e["tag"] for e in raw["data"]["endpoints"]
                                           if e["tag"].startswith(tag + "/")}),
                         "max_price": {k: v * 1_000_000 for k, v in ceilings.items()}},
            "reasoning": reasoning_request,
            "temperature": 0.7 if "temperature" in supported else None,
            "max_tokens": max_tokens, "pricing": pricing, "ceiling_rates": ceilings,
        }
        if (endpoint.get("max_completion_tokens") or max_tokens) < max_tokens:
            raise CalibrationStop(f"Output ceiling unavailable: {model}")
        profiles.append(profile)
        write(root / "catalogue" / (model.replace("/", "_") + ".json"),
              {"retrieved_at": now(), "model": models[model], "endpoint_response": raw})

    pack_hashes = {}
    for frame in ("fantasy", "neutral"):
        ensure_pack(root, frame, PACK_SEED, 90, None, "frozen",
                    pack_source=ROOT / "runs/exploit1/packs")
        path = root / "packs" / f"pack__{frame}__s{PACK_SEED}__h90.yml"
        pack_hashes[path.relative_to(root).as_posix()] = digest(path)
    for seed in (FRESH_SEED, PACK_SEED):
        path = root / "schedules" / f"s{seed}__h90.yml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(generate_schedule(seed, 90).to_yaml(), encoding="utf-8")
        pack_hashes[path.relative_to(root).as_posix()] = digest(path)
    cases = [
        {"name": "ordinary", "framing": "neutral", "richness": "static", "seed": FRESH_SEED, "exploit_condition": None},
        {"name": "exploit_fantasy", "framing": "fantasy", "richness": "rich", "seed": PACK_SEED, "exploit_condition": "ambiguous_wit"},
        {"name": "exploit_neutral", "framing": "neutral", "richness": "rich", "seed": PACK_SEED, "exploit_condition": "ambiguous_wit"},
    ]
    queue = []
    for case in cases:
        order = list(MODEL_ENDPOINTS)
        random.Random("transport-calibration-2026-09-19|" + case["name"]).shuffle(order)
        queue.extend({"model": m, "case": case["name"]} for m in order)
    full_queue = [entry for entry in queue if entry["case"] == "ordinary"]
    plan = {"created_at": now(), "purpose": "technical, latency and cost calibration; excluded from confirmatory analysis",
            "reasoning_policy": "low where supported; Kimi K2.6 thinking disabled",
            "selection_basis": "feasibility after excessive default-setting latency; not behavioural results",
            "profiles": profiles, "cases": cases, "queue": queue, "full_queue": full_queue,
            "exclusive_with_batches": [PREVIOUS_ROOT.relative_to(ROOT).as_posix()],
            "horizon": 90, "smoke_days": 3,
            "reserved_calibration_seeds": [FRESH_SEED, PACK_SEED],
            "artifact_hashes": pack_hashes, "source_hashes": source_hashes(),
            "runtime": runtime_versions()}
    write(root / "plan.json", plan)
    (root / "plan.sha256").write_text(digest(root / "plan.json") + "\n", encoding="ascii")
    print(f"Prepared {len(queue)} short probes and {len(full_queue)} full runs; no paid requests.")


def validate(root):
    if digest(root / "plan.json") != (root / "plan.sha256").read_text().strip():
        raise CalibrationStop("Frozen plan changed.")
    plan = read(root / "plan.json")
    if source_hashes() != plan["source_hashes"]:
        raise CalibrationStop("Runner or simulation changed since preparation; prepare a new batch.")
    if runtime_versions() != plan["runtime"]:
        raise CalibrationStop("Python environment changed since preparation; prepare a new batch.")
    for name, sha in plan["artifact_hashes"].items():
        if digest(root / name) != sha:
            raise CalibrationStop(f"Frozen artifact changed: {name}")
    return plan


class Budget:
    """Sequential local spending guard, durable across stages and attempts.

    Unknown-cost requests retain their conservative reservation. This is a
    client estimate, not an account-level billing limit.
    """
    def __init__(self, root, limit):
        if limit is not None and (not math.isfinite(limit) or limit <= 0):
            raise ValueError("budget must be finite and positive")
        self.path = root / "budget.jsonl"
        self.limit = limit
        self.charges = {}
        for event in rows(self.path):
            self.charges[event["request_id"]] = event["amount"]

    @property
    def spent(self):
        return sum(self.charges.values())

    def reserve(self, amount, label):
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("reservation must be finite and non-negative")
        if self.limit is not None and self.spent + amount > self.limit:
            raise CalibrationStop(f"Budget guard: ${self.spent:.4f} accounted; next reservation ${amount:.4f}; ceiling ${self.limit:.2f}")
        request_id = uuid.uuid4().hex
        append(self.path, {"at": now(), "kind": "reserve", "request_id": request_id, "amount": amount, "label": label})
        self.charges[request_id] = amount
        return request_id

    def settle(self, request_id, cost):
        if not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
            return False
        append(self.path, {"at": now(), "kind": "settle", "request_id": request_id, "amount": cost})
        self.charges[request_id] = cost
        return True


TRANSIENT_ERRORS = {"APIConnectionError", "APITimeoutError", "RateLimitError", "InternalServerError"}


def measured_chat(profile, path, budget, api_key, initial_day=0):
    state = {"day": initial_day, "messages": None}

    def before(request):
        if request["messages"] is not state["messages"]:
            state["day"] += 1
            state["messages"] = request["messages"]
        # UTF-8 bytes plus overhead deliberately overestimates normal text
        # token counts; reserve full output and a further 2x billing margin.
        nbytes = len(json.dumps(request, ensure_ascii=False).encode("utf-8")) + 4096
        rates = profile["ceiling_rates"]
        reserve = 2 * (nbytes * rates["prompt"] + profile["max_tokens"] * rates["completion"])
        state["request_id"] = budget.reserve(reserve, path.parent.as_posix())
        state["start"] = time.monotonic()
        append(path, {"kind": "request", "at": now(), "day": state["day"],
                      "request_id": state["request_id"], "request": request})

    def after(response):
        append(path, {"kind": "response", "at": now(), "day": state["day"],
                      "request_id": state["request_id"],
                      "seconds": time.monotonic() - state["start"], "response": response})
        cost = (response.get("usage") or {}).get("cost")
        known = budget.settle(state["request_id"], cost)
        if not known:
            raise CalibrationStop("Provider omitted billing cost; reservation retained. Reconcile before continuing.")
        if response.get("provider") != profile["expected_provider"]:
            raise CalibrationStop("Provider identity missing or different from frozen endpoint.")
        if not response.get("choices"):
            raise CalibrationStop("Provider returned no choices; response preserved.")
        if response["choices"][0].get("finish_reason") == "length":
            raise CalibrationStop("Output truncated; review token budget before a new attempt.")
        if budget.limit is not None and budget.spent > budget.limit:
            raise CalibrationStop("Reported billing exceeded local estimate; collection stopped.")

    client = openai_chat_client(api_key, profile["model"],
        temperature=profile["temperature"], max_retries=0,
        provider=profile["provider"], reasoning=profile["reasoning"],
        max_tokens=profile["max_tokens"], strict=True,
        before_request=before, on_response=after)

    def chat(messages, tools):
        for attempt in range(3):
            try:
                return client(messages, tools)
            except CalibrationStop:
                raise
            except Exception as error:
                # Each transport attempt has its own durable reservation and
                # log entry. No hidden SDK retries or parameter fallback.
                chain, cause = [], error
                for _ in range(5):
                    if cause is None:
                        break
                    chain.append({"type": type(cause).__name__, "message": str(cause)[:800]})
                    cause = cause.__cause__
                append(path, {"kind": "error", "at": now(), "request_id": state.get("request_id"),
                              "error_type": type(error).__name__, "status_code": getattr(error, "status_code", None),
                              "body": getattr(error, "body", None), "cause_chain": chain})
                if type(error).__name__ in TRANSIENT_ERRORS and attempt < 2:
                    print(f"Transient {type(error).__name__}; retrying the same request ({attempt + 2}/3).", flush=True)
                    time.sleep((2, 5)[attempt])
                    continue
                body = getattr(error, "body", None)
                detail = body.get("message", "") if isinstance(body, dict) else ""
                raise CalibrationStop(f"API request stopped ({type(error).__name__}): {detail[:1200]}\nAttempt preserved; inspect before retrying.") from error
    return chat


def recorded_response(response):
    """Decode saved provider output identically to the live chat adapter."""
    message = response["choices"][0]["message"]
    calls = []
    for raw in message.get("tool_calls") or []:
        call = _tool_call(raw["id"], raw["function"]["name"], raw["function"].get("arguments"))
        if raw.get("extra_content") is not None:
            call.provider_fields["extra_content"] = raw["extra_content"]
        calls.append(call)
    usage = response.get("usage") or {}
    return ChatResponse(content=message.get("content"), tool_calls=calls,
        usage={k: usage.get(k, 0) or 0 for k in ("prompt_tokens", "completion_tokens")},
        provider=response.get("provider"),
        provider_fields={k: message[k] for k in ("reasoning", "reasoning_details", "reasoning_content")
                         if message.get(k) is not None})


def load_replay(source, profile, case, seen=None):
    """Read successful calls plus the unanswered request, including recovery ancestry."""
    seen = set() if seen is None else seen
    source = source.resolve()
    if source in seen:
        raise CalibrationStop("Recovery ancestry contains a cycle.")
    seen.add(source)
    settings = read(source / "settings.json")
    if settings["profile"] != profile or settings["case"] != case or settings["stage"] != "full":
        raise CalibrationStop("Recovery requires the original model settings and experimental case.")
    if (source / "complete.json").exists():
        raise CalibrationStop("Recovery source is already complete.")
    pairs, pending = [], None
    ancestry = source / "recovery.json"
    if ancestry.exists():
        info = read(ancestry)
        parent = Path(info["source_path"])
        if digest(parent / "api_calls.jsonl") != info["source_api_sha256"]:
            raise CalibrationStop("Recovery source log changed.")
        pairs, pending = load_replay(parent, profile, case, seen)
    log = rows(source / "api_calls.jsonl")
    for event in log:
        if event["kind"] == "request":
            if pending is not None and pending["request"] != event["request"]:
                raise CalibrationStop("An unanswered request was replaced with a different request.")
            pending = event
        elif event["kind"] == "response":
            response = event["response"]
            if pending is None or event["request_id"] != pending["request_id"]:
                raise CalibrationStop("Response has no matching recovery request.")
            if (not response.get("choices") or response["choices"][0].get("finish_reason") == "length"
                    or response.get("provider") != profile["expected_provider"]
                    or (response.get("usage") or {}).get("cost") is None):
                raise CalibrationStop("Recovery cannot accept an invalid or truncated response.")
            pairs.append((pending, response))
            pending = None
        elif event["kind"] == "error" and event["error_type"] not in TRANSIENT_ERRORS:
            raise CalibrationStop("Recovery source has a non-transient error.")
    if pending is None:
        raise CalibrationStop("No unanswered request to recover.")
    return pairs, pending


class ReplayChat:
    """Reconstruct state without inference; compare every request before continuing."""
    def __init__(self, pairs, pending, live, at_boundary=None):
        self.pairs, self.pending, self.live = pairs, pending, live
        self.index = 0
        self.at_boundary = at_boundary
        self.recovered = False

    def __call__(self, messages, tools):
        if self.recovered:
            return self.live(messages, tools)
        event = self.pairs[self.index][0] if self.index < len(self.pairs) else self.pending
        request = event["request"]
        if messages != request["messages"] or tools != request["tools"]:
            raise CalibrationStop(f"Recovery mismatch at recorded call {self.index + 1}; no new inference issued.")
        if self.index < len(self.pairs):
            response = recorded_response(self.pairs[self.index][1])
            self.index += 1
            return response
        if self.at_boundary is not None:
            self.at_boundary()
        self.recovered = True
        print(f"Recovered {self.index} saved responses; continuing day {event['day']}.", flush=True)
        return self.live(messages, tools)


def smoke(spec, path, chat, pack, days):
    view = ThemedView(Engine(EngineConfig(horizon=90, exploit_fault=spec.exploit_condition is not None),
                            generate_schedule(spec.schedule_seed, 90)),
                      load_theme(spec.condition.framing), exploit_condition=spec.exploit_condition)
    for _ in range(days):
        dawn = view.dawn()
        narration = pack.text_for_day(view.day) if pack else view.static_narration(dawn)
        result = run_agent_day(view, chat, view.briefing(dawn, narration))
        dusk = view.dusk()
        append(path / "days.jsonl", {**dataclasses.asdict(result), "net_worth_end": dusk["net_worth"]})
        if view.done:
            break
    write(path / "result.json", {"stage": "smoke", "days_survived": len(rows(path / "days.jsonl")), "horizon": 90})


def gate(path, expected_days):
    days = rows(path / "days.jsonl")
    calls = [c for d in days for c in d["tool_calls"]]
    invalid = sum(str(c["result"].get("error", "")).startswith("invalid tool arguments") for c in calls)
    forced = sum(bool(d["forced"]) for d in days)
    # Exhausting the fixed action allowance with valid task actions is an
    # observed behaviour, not a tool/API compatibility failure. Keep its
    # missing journal visible, and still flag caps reached through errors.
    budget_days = sum(bool(d["forced"])
                      and len(d["tool_calls"]) == MAX_TOOL_CALLS_PER_DAY
                      and all(c["result"].get("ok", True) and not c["result"].get("error")
                              for c in d["tool_calls"])
                      for d in days)
    nudges = sum(d["nudges"] for d in days)
    return {"gate_version": 2, "pass": len(days) == expected_days and forced == budget_days
                    and invalid / max(1, len(calls)) < .05 and nudges / max(1, len(days)) <= 1,
            "days": len(days), "forced": forced, "invalid_arguments": invalid,
            "forced_budget_days": budget_days, "forced_other_days": forced - budget_days,
            "tool_calls": len(calls), "nudges": nudges}


def completed_pass(path):
    """Keep original failed gates immutable; permit a trace-bound review."""
    if not (path / "complete.json").exists():
        return False
    review_path = path / "gate_review.json"
    if review_path.exists():
        review = read(review_path)
        if digest(path / "days.jsonl") != review["days_sha256"]:
            raise CalibrationStop("Reviewed calibration trace changed.")
        return review["checks"]["pass"]
    return read(path / "complete.json").get("technical_gate", {}).get("pass", False)


def run(root, stage, ceiling, attempt, resume_from_attempt=None):
    plan = validate(root)
    check_previous_runners(plan)
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise CalibrationStop("OPENROUTER_API_KEY is not set in this process.")
    profiles = {p["model"]: p for p in plan["profiles"]}
    cases = {c["name"]: c for c in plan["cases"]}
    budget = Budget(root, ceiling)
    if stage == "full":
        missing = []
        for entry in plan["queue"]:
            label = entry["model"].replace("/", "_") + "__" + entry["case"]
            passed = any(completed_pass(p.parent) for p in (root / "smoke").glob(f"attempt-*/{label}/complete.json"))
            if not passed:
                missing.append(label)
        if missing:
            raise CalibrationStop("Full batch needs passing smoke checks for every case: " + ", ".join(missing))
    # Exclusive file creation prevents concurrent runners spending one budget.
    lock = root / "running.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    try:
        for entry in stage_queue(plan, stage):
            profile, case = profiles[entry["model"]], cases[entry["case"]]
            label = entry["model"].replace("/", "_") + "__" + case["name"]
            path = root / stage / f"attempt-{attempt}" / label
            if any(completed_pass(p.parent)
                   for p in (root / stage).glob(f"attempt-*/{label}/complete.json")):
                continue
            if path.exists():
                raise CalibrationStop(f"Incomplete attempt preserved: {path}; use a new attempt number after review.")
            path.mkdir(parents=True)
            write(path / "settings.json", {"profile": profile, "case": case, "stage": stage,
                                           "plan_sha256": digest(root / "plan.json")})
            spec = RunSpec(model=profile["model"], condition=Condition(case["framing"], case["richness"]),
                           schedule_seed=case["seed"], horizon=90, temperature=profile["temperature"],
                           exploit_condition=case["exploit_condition"])
            pack = ensure_pack(root, case["framing"], case["seed"], 90, None, "frozen") if case["richness"] == "rich" else None
            source = root / stage / f"attempt-{resume_from_attempt}" / label if resume_from_attempt else None
            pairs, pending = load_replay(source, profile, case) if source and source.exists() else ([], None)
            chat = measured_chat(profile, path / "api_calls.jsonl", budget, key,
                                 initial_day=pending["day"] - 1 if pending else 0)
            if pending:
                write(path / "recovery.json", {"at": now(), "source_path": str(source.resolve()),
                    "source_api_sha256": digest(source / "api_calls.jsonl"),
                    "replayed_responses": len(pairs), "continuation_day": pending["day"],
                    "billing_note": "Saved responses are reused without inference. Their billing remains only in source logs."})
                def check_days():
                    if rows(path / spec.run_id / "days.jsonl") != rows(source / spec.run_id / "days.jsonl"):
                        raise CalibrationStop("Reconstructed completed days differ; no new inference issued.")
                chat = ReplayChat(pairs, pending, chat, at_boundary=check_days)
            print(f"Starting {stage}: {label}; budget accounted ${budget.spent:.4f}", flush=True)
            try:
                if stage == "smoke":
                    smoke(spec, path, chat, pack, plan["smoke_days"])
                    checks = gate(path, plan["smoke_days"])
                else:
                    result = execute_run(spec, path, chat=chat, pack=pack)
                    checks = gate(path / spec.run_id, result["days_survived"])
                    checks["end_reason"] = result["end_reason"]
                    checks["pass"] &= result["end_reason"] in ("completed", "bankrupt")
                write(path / "gate.json", checks)
                write(path / "complete.json", {"at": now(), "technical_gate": checks})
            except Exception as error:
                write(path / "stopped.json", {"at": now(), "error": str(error), "type": type(error).__name__})
                raise
            if not checks["pass"]:
                raise CalibrationStop(f"Technical check needs review: {label}; artifacts preserved.")
    finally:
        lock.unlink()


def summarize(root):
    summaries = []
    for path in sorted(root.glob("*/*/*/api_calls.jsonl")):
        responses = [r for r in rows(path) if r["kind"] == "response"]
        usages = [(r["response"].get("usage") or {}) for r in responses]
        costs = [u.get("cost") for u in usages]
        settings = read(path.parent / "settings.json")
        summary = {"path": str(path.parent.relative_to(root)), "model": settings["profile"]["model"],
                   "case": settings["case"]["name"], "responses": len(responses),
                   "prompt_tokens": sum(u.get("prompt_tokens", 0) or 0 for u in usages),
                   "completion_tokens": sum(u.get("completion_tokens", 0) or 0 for u in usages),
                   "reasoning_tokens_reported": sum((u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) or 0 for u in usages),
                   "reasoning_count_missing": sum((u.get("completion_tokens_details") or {}).get("reasoning_tokens") is None for u in usages),
                   "cached_prompt_tokens_reported": sum((u.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0 for u in usages),
                   "cache_count_missing": sum((u.get("prompt_tokens_details") or {}).get("cached_tokens") is None for u in usages),
                   "cost_usd_reported": sum(c for c in costs if isinstance(c, (int, float))),
                   "cost_missing": sum(c is None for c in costs),
                   "request_seconds": sum(r["seconds"] for r in responses),
                   "complete": (path.parent / "complete.json").exists(),
                   "technical_pass": completed_pass(path.parent)}
        if (path.parent / "recovery.json").exists():
            summary["recovery"] = read(path.parent / "recovery.json")
        summaries.append(summary)
    write(root / "summary.json", summaries)
    print(json.dumps(summaries, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "check", "smoke", "full", "summary"])
    parser.add_argument("--out", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--budget-usd", type=float, help="Optional cumulative dollar ceiling; the selected stage always has a fixed run count.")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--resume-from-attempt", type=int, help="For full runs, reconstruct an interrupted earlier attempt from saved responses before making new calls.")
    args = parser.parse_args()
    root = args.out.resolve()
    if args.command == "prepare":
        prepare(root)
    elif args.command == "check":
        plan = validate(root)
        print(f"Frozen plan verified: {len(plan['profiles'])} models, {len(plan['queue'])} short probes, {len(stage_queue(plan, 'full'))} full runs. No API calls.")
    elif args.command == "summary":
        summarize(root)
    else:
        if args.attempt < 1:
            parser.error("Paid stages require a positive attempt number.")
        if args.resume_from_attempt is not None and (args.command != "full" or not 1 <= args.resume_from_attempt < args.attempt):
            parser.error("Recovery requires full and an earlier positive attempt number.")
        run(root, args.command, args.budget_usd, args.attempt, args.resume_from_attempt)


if __name__ == "__main__":
    try:
        main()
    except CalibrationStop as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
