"""Append-only engineering admission ledger. No simulator/launch API.

Unlimited cumulative attempts do not authorize a run. Each admission binds an
exact proposal and a separate human decision; failed runs remain failed. This
module deliberately does not call the historical capped supervisor.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re


TASK = "AAD-0.5-INTERACTION-RESEARCH-V2"
CHECKS = ("input_fidelity", "initialization_accounting", "identity_clock",
          "D1_contract", "all18_common_cells", "full_context_events",
          "resource_limits", "task_isolation")
TERMINAL = {"measurement_accepted", "measurement_rejected", "failed", "interrupted"}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def relative(root, name):
    require(isinstance(name, str) and bool(name) and not Path(name).is_absolute(), "relative_path_required")
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()) and path != root.resolve(), "path_escape")
    return path


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def resource_reason(limits, sample, *, startup=False):
    required = ["free_c_bytes", "free_d_bytes", "task_output_bytes", "wall_s", "process_tree_rss_bytes"]
    if startup:
        required.append("available_memory_bytes")
    require(all(number(sample.get(k)) for k in required), "resource_observation_missing")
    for field, bound, lower in [
        ("free_c_bytes", "min_free_c_bytes", True), ("free_d_bytes", "min_free_d_bytes", True),
        ("task_output_bytes", "task_output_bytes", False), ("wall_s", "per_attempt_wall_s", False),
        ("process_tree_rss_bytes", "process_tree_rss_bytes", False),
    ]:
        exceeds = sample[field] < limits[bound] if lower else sample[field] > limits[bound]
        if exceeds:
            return field
    if startup and sample["available_memory_bytes"] < limits["min_available_memory_bytes"]:
        return "available_memory_bytes"
    return None


class ResearchLedger:
    def __init__(self, repo, config_path):
        self.repo = Path(repo).resolve()
        self.config_path = relative(self.repo, config_path)
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
        require(self.config["task_id"] == TASK, "wrong_task")
        require(self.config["maximum_new_trajectory_attempts"] is None and
                self.config["cumulative_wall_s"] is None and self.config["workers"] == 1, "budget_contract")
        require(self.config["automatic_retry"] is False, "automatic_retry_forbidden")
        self.path = relative(self.repo, self.config["ledger_path"])
        for old in self.config["historical_references"]:
            require(self.path != relative(self.repo, old["path"]), "historical_ledger_immutable")

    @contextmanager
    def lock(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_suffix(self.path.suffix + ".lock")
        # Exclusive lock; stale locks require explicit recovery, never auto-delete.
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, str(os.getpid()).encode("ascii"))
            yield
        finally:
            os.close(fd)
            lock.unlink()

    def events(self):
        if not self.path.exists():
            return []
        data = self.path.read_bytes()
        require(data.endswith(b"\n"), "incomplete_journal_preserve_and_recover")
        events = []
        for line in data.splitlines():
            event = json.loads(line)
            expected = event.pop("sha256")
            require(hashlib.sha256(canonical(event)).hexdigest() == expected, "journal_digest")
            require(event["seq"] == len(events) and event["task_id"] == TASK, "journal_sequence_or_task")
            require(event["previous_sha256"] == (events[-1]["sha256"] if events else None), "journal_chain")
            event["sha256"] = expected
            events.append(event)
        require(events[0]["kind"] == "task_created" and
                events[0]["payload"]["budget_sha256"] == digest(self.config_path), "budget_binding_changed")
        return events

    def snapshot(self):
        attempts = {}
        for e in self.events():
            kind, run, payload = e["kind"], e["run_id"], e["payload"]
            if kind == "task_created":
                continue
            if kind == "reserved":
                require(run not in attempts, "duplicate_run_id")
                attempts[run] = dict(payload, status=kind, reserved_utc=e["utc"], started_utc=None,
                                     failure_reason=None, resources=None, measurement_acceptance="pending",
                                     reviewed_for_continuation=False)
            else:
                require(run in attempts, "unknown_run_id")
                a = attempts[run]
                if kind == "continuation_review":
                    require(a["status"] in TERMINAL, "review_before_terminal")
                    a["reviewed_for_continuation"] = True
                    a["continuation_review"] = payload
                else:
                    allowed = {"running": {"reserved"}, "completed": {"running"},
                               "failed": {"reserved", "running"}, "interrupted": {"reserved", "running"},
                               "measurement_accepted": {"completed"}, "measurement_rejected": {"completed"}}
                    require(kind in allowed and a["status"] in allowed[kind], "invalid_transition")
                    a.update(payload, status=kind)
                    if kind == "running":
                        a["started_utc"] = e["utc"]
                    if kind in {"completed", "failed", "interrupted"}:
                        a["run_finished_utc"] = e["utc"]
                    if kind in TERMINAL:
                        a["ended_utc"] = e["utc"]
        return {"task_id": TASK, "maximum_new_trajectory_attempts": None,
                "initialized": bool(self.events()), "attempt_count": len(attempts), "attempts": attempts,
                "historical_attempts": "separate; never imported as new attempts",
                "has_launch_API": False}

    def _append(self, kind, run, payload):
        events = self.events()
        event = dict(seq=len(events), task_id=TASK, utc=datetime.now(timezone.utc).isoformat(),
                     previous_sha256=events[-1]["sha256"] if events else None,
                     kind=kind, run_id=run, payload=payload)
        event["sha256"] = hashlib.sha256(canonical(event)).hexdigest()
        with self.path.open("ab") as stream:
            stream.write(canonical(event) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())

    def initialize(self):
        with self.lock():
            require(not self.path.exists(), "ledger_exists_no_reset")
            for old in self.config["historical_references"]:
                require(digest(relative(self.repo, old["path"])) == old["sha256"], "historical_reference_changed")
            self._append("task_created", None, {"budget_sha256": digest(self.config_path),
                        "authorization": self.config["authorization"],
                        "execution_allowed": False, "historical_references": self.config["historical_references"]})

    def reserve(self, proposal_path, approval, run_id, resource_sample):
        """Record one attempt before any future launcher. No process is started."""
        path = relative(self.repo, proposal_path)
        p = json.loads(path.read_text(encoding="utf-8"))
        require(approval.get("researcher_confirmed") is True and approval.get("task_id") == TASK and
                approval.get("proposal_sha256") == digest(path) and bool(approval.get("decision_record")),
                "exact_researcher_confirmation_required")
        require(p.get("task_id") == TASK and p.get("execution_allowed") is True and
                p.get("researcher_confirmed") is True, "proposal_not_executable")
        require(p.get("budget_sha256") == digest(self.config_path), "proposal_budget_binding")
        require(all(p.get("admission", {}).get(k) is True for k in
                    ["initialization_policy_approved", "measurement_contract_approved", "input_fidelity_approved"]),
                "scientific_admission_pending")
        require(p.get("isolation", {}).get("accepted_for_new_task") is True, "task_isolation_not_accepted")
        report = relative(self.repo, p["isolation"]["report_path"])
        require(digest(report) == p["isolation"]["report_sha256"], "isolation_report_binding")
        proof = json.loads(report.read_text(encoding="utf-8"))
        require(proof.get("task_id") == TASK and proof.get("input_and_test_resource_scope_accepted") is True,
                "isolation_evidence_incomplete")
        require(p["plan_sha256"] == digest(relative(self.repo, p["plan_path"])), "plan_binding")
        require(bool(p.get("plan_version")) and re.fullmatch(r"[0-9a-f]{40}", p.get("git_commit", "")) and
                re.fullmatch(r"[0-9a-f]{64}", p.get("worktree_sha256", "")) and bool(p.get("environment")), "provenance_missing")
        runs = p["runs"]
        require(len({r["id"] for r in runs}) == len(runs), "duplicate_proposal_run")
        run = next((r for r in runs if r["id"] == run_id), None)
        require(run is not None and re.fullmatch(r"[A-Za-z0-9_-]+", run_id), "unknown_or_invalid_run")
        require(isinstance(run.get("seed"), int) and not isinstance(run["seed"], bool), "seed_required")
        require(all(run.get(k) for k in ["question", "contrast", "condition", "factors", "initialization_policy"]), "research_purpose_missing")
        for role, bindings in [("source", p["source_sha256"]), ("input", run["input_sha256"])]:
            require(bool(bindings), "missing_file_bindings")
            for name, expected in bindings.items():
                if role == "input":
                    require(not any(marker in name.lower() for marker in ["locked_holdout", "0820_0835"]), "validation_input_forbidden")
                require(digest(relative(self.repo, name)) == expected, "file_binding_changed:" + name)
        output = relative(self.repo, run["artifact_path"])
        output_root = relative(self.repo, self.config["output_root"])
        require(output.is_relative_to(output_root) and output != output_root and not output.exists(), "artifact_path_not_new")
        require(resource_reason(self.config["single_attempt_limits"], resource_sample, startup=True) is None, "resource_preflight_failed")
        with self.lock():
            state = self.snapshot()
            require(bool(self.events()), "initialize_first")
            require(run_id not in state["attempts"], "duplicate_run_id")
            for a in state["attempts"].values():
                require(a["status"] in TERMINAL, "previous_attempt_unreviewed_or_active")
                require(a["status"] == "measurement_accepted" or a["reviewed_for_continuation"], "failure_requires_explicit_review")
            signature = hashlib.sha256(canonical({k: run[k] for k in
                ["seed", "condition", "factors", "initialization_policy", "input_sha256"]})).hexdigest()
            duplicates = [key for key, a in state["attempts"].items() if a["configuration_signature"] == signature]
            if duplicates:
                require(run.get("replicate_of") in duplicates and bool(run.get("repeat_reason")), "duplicate_configuration_requires_reason")
            self._append("reserved", run_id, dict(run, task_id=TASK, plan_version=p["plan_version"],
                        plan_sha256=p["plan_sha256"], proposal_sha256=digest(path), source_sha256=p["source_sha256"],
                        git_commit=p["git_commit"], worktree_sha256=p["worktree_sha256"], environment=p["environment"],
                        decision_record=approval["decision_record"], resource_before=resource_sample,
                        isolation=p["isolation"], configuration_signature=signature))
        return self.snapshot()

    def transition(self, run_id, kind, *, reason=None, resources=None, checks=None, artifact_sha256=None):
        require(kind in {"running", "completed", "failed", "interrupted", "measurement_accepted", "measurement_rejected"}, "unknown_transition")
        with self.lock():
            a = self.snapshot()["attempts"][run_id]
            allowed = {"running": {"reserved"}, "completed": {"running"}, "failed": {"reserved", "running"},
                       "interrupted": {"reserved", "running"}, "measurement_accepted": {"completed"}, "measurement_rejected": {"completed"}}
            require(a["status"] in allowed[kind], "invalid_transition")
            payload = {}
            if kind in {"completed", "failed", "interrupted"}:
                require(isinstance(resources, dict) and all(k in resources for k in
                        ["wall_s", "process_tree_rss_bytes", "artifact_bytes"]), "resource_record_required")
                require(all(v is None or number(v) for v in resources.values()), "invalid_resource_record")
                payload["resources"] = resources  # None means unobserved, never a fabricated zero.
            if kind in {"failed", "interrupted", "measurement_rejected"}:
                require(bool(reason), "failure_reason_required")
                payload["failure_reason"] = reason
            if kind.startswith("measurement_"):
                require(isinstance(checks, dict) and set(CHECKS).issubset(checks) and
                        all(type(checks[k]) is bool for k in CHECKS), "measurement_checks_required")
                if kind == "measurement_accepted":
                    require(all(checks[k] for k in CHECKS) and bool(artifact_sha256), "measurement_acceptance_failed")
                    limits = self.config["single_attempt_limits"]
                    actual = a["resources"]
                    require(all(number(actual.get(k)) for k in ["wall_s", "process_tree_rss_bytes", "artifact_bytes"]), "resource_observation_missing")
                    require(actual["wall_s"] <= limits["per_attempt_wall_s"] and
                            actual["process_tree_rss_bytes"] <= limits["process_tree_rss_bytes"] and
                            actual["artifact_bytes"] <= limits["task_output_bytes"], "resource_acceptance_failed")
                    for name, expected in artifact_sha256.items():
                        path = relative(self.repo, name)
                        require(path.is_relative_to(relative(self.repo, a["artifact_path"])) and digest(path) == expected, "artifact_binding_changed")
                payload.update(measurement_acceptance=kind, measurement_checks=checks, artifact_sha256=artifact_sha256 or {})
            self._append(kind, run_id, payload)
        return self.snapshot()

    def review_failure(self, run_id, decision):
        with self.lock():
            a = self.snapshot()["attempts"][run_id]
            require(a["status"] in {"failed", "interrupted", "measurement_rejected"}, "not_a_failed_attempt")
            require(decision.get("researcher_confirmed") is True and decision.get("task_id") == TASK and
                    decision.get("run_id") == run_id and bool(decision.get("decision_record")), "continuation_decision_required")
            self._append("continuation_review", run_id, decision)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Offline ledger validation/report only; never launches SUMO")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--config", default="code/configs/stage_0_5_interaction_research_v2.json")
    args = parser.parse_args()
    print(json.dumps(ResearchLedger(args.repo_root, args.config).snapshot(), ensure_ascii=False, indent=2))
