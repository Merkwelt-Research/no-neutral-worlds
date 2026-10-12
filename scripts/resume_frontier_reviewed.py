"""Frontier transport with the classifier-censoring amendment (27 Sep 2026).

Applies runs/transport_opus55_2026-09-27/reviews/classifier_censoring_amendment_2026-09-27.json
without changing the frozen runner or adapter (their hashes stay valid):

- a response with stop_reason "refusal" ends that trajectory at that day;
  it is not retried, not sent to another model, and not coded as behaviour;
- the job is closed with complete.json {"censored": true, ...}; completed
  days and the tool results logged before the block remain observed data;
- the batch continues with the remaining jobs.

Everything else (recording, exact replay, spending cap, stop-for-review on
truncation or unexpected model) is the frozen runner's.

    python scripts/resume_frontier_reviewed.py exploit --resume
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_frontier_transport as fr

AMENDMENT = "reviews/classifier_censoring_amendment_2026-09-27.json"
# The frozen functions, captured before main() swaps the module attributes.
FROZEN_MEASURED_CHAT = fr.measured_chat
FROZEN_EXECUTE_JOB = fr.execute_job
read, write, rows, append = fr.read, fr.write, fr.rows, fr.append


class Censored(RuntimeError):
    """Classifier or model refusal: close the trajectory, keep going."""
    no_retry = True

    def __init__(self, info):
        super().__init__(f"censored by refusal on day {info.get('day')} ({info.get('category')})")
        self.info = info


def refusal_info(raw, day):
    details = raw.get("stop_details") or {}
    usage = raw.get("usage") or {}
    return {"day": day, "category": details.get("category"), "explanation": details.get("explanation"),
            "output_tokens": usage.get("output_tokens"), "pre_output": not raw.get("content")}


def measured_chat(path, key, stop, guard):
    """The frozen measured chat, except that a refusal censors the trajectory."""
    inner = FROZEN_MEASURED_CHAT(path, key, stop, guard)

    def chat(messages, tools):
        try:
            return inner(messages, tools)
        except fr.Stop as error:
            log = rows(path)
            last = next((e for e in reversed(log) if e["kind"] == "response"), None)
            if last is None or last["response"].get("stop_reason") != "refusal":
                raise
            request = next(e for e in reversed(log) if e["kind"] == "request" and e["request_id"] == last["request_id"])
            raise Censored(refusal_info(last["response"], request["day"])) from error
    return chat


def observed_days(attempt):
    found = list((attempt / "data").rglob("days.jsonl"))
    return sum(len(rows(p)) for p in found)


def close_censored(attempt, job, info):
    write(attempt / "complete.json", {"at": fr.audit.now(), "job_id": job["job_id"],
                                      "result": {"censored": True, **info, "observed_days": observed_days(attempt),
                                                 "amendment": AMENDMENT}})


def execute_job(root, plan, job, key, stop, guard, resume=False, chat_factory=None):
    try:
        return FROZEN_EXECUTE_JOB(root, plan, job, key, stop, guard, resume, chat_factory)
    except Censored as error:
        attempt = sorted(fr.ext.job_directory(root, job).glob("attempt-*"), key=lambda p: int(p.name.split("-")[-1]))[-1]
        close_censored(attempt, job, error.info)
        print(f"Censored {job['job_id']}: {error}", flush=True)
        return job["job_id"]


def close_prior_refusals(root, plan):
    """Close attempts that stopped on a refusal before this amendment existed."""
    closed = []
    for job in plan["jobs"]:
        base = fr.ext.job_directory(root, job)
        attempts = sorted(base.glob("attempt-*"), key=lambda p: int(p.name.split("-")[-1]))
        if not attempts or fr.ext.completed(root, job):
            continue
        last_attempt = attempts[-1]
        log = rows(last_attempt / "api_calls.jsonl") if (last_attempt / "api_calls.jsonl").exists() else []
        last = next((e for e in reversed(log) if e["kind"] == "response"), None)
        if last is not None and last["response"].get("stop_reason") == "refusal":
            request = next(e for e in reversed(log) if e["kind"] == "request" and e["request_id"] == last["request_id"])
            close_censored(last_attempt, job, refusal_info(last["response"], request["day"]))
            closed.append(job["job_id"])
    return closed




def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm", choices=fr.ARMS)
    parser.add_argument("--out", type=Path, default=fr.DEFAULT_ROOT)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--cap", type=float, default=None)
    args = parser.parse_args()
    root = args.out.resolve()
    plan = fr.check(root)
    if not (root / AMENDMENT).exists():
        raise fr.Stop(f"Amendment record missing: {AMENDMENT}")
    wrapper_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    append(root / "reviews/reviewed_invocations.jsonl", {"at": fr.audit.now(), "arm": args.arm,
                                                          "wrapper_sha256": wrapper_sha,
                                                          "amendment_sha256": fr.digest(root / AMENDMENT),
                                                          "plan_sha256": fr.digest(root / "plan.json")})
    for job_id in close_prior_refusals(root, plan):
        print(f"Closed earlier refusal as censored: {job_id}", flush=True)
    fr.measured_chat, fr.execute_job = measured_chat, execute_job
    fr.run(root, args.arm, args.resume, args.workers, args.cap)


if __name__ == "__main__":
    try:
        main()
    except (fr.Stop, FileExistsError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
