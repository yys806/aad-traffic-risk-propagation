"""V2 execution interfaces. Native launch is hard-locked in this engineering build.

The replay path uses explicit synthetic fixtures and never creates a process.
The native backend is implemented for later review, but cannot be enabled by a
proposal, environment variable or CLI argument in this build.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid
import xml.etree.ElementTree as ET

from stage_0_5_identity_observation import IdentityObserver, collect_snapshot
from stage_0_5_input_fidelity import inventory, config_references, xml
from stage_0_5_isolation_v2 import Scope, ScopeViolation, sha
from stage_0_5_research_ledger import TASK, CHECKS, canonical, resource_reason

NATIVE_LAUNCH_LOCKED = True


class AdmissionRefused(PermissionError):
    pass


def gate_reasons(proposal, approval, run_id, proposal_sha256):
    if not isinstance(proposal, dict):
        return ["invalid_proposal_object"]
    if not isinstance(approval, dict):
        approval = {}
    reasons = []
    for flag in ["execution_allowed", "researcher_confirmed", "protocol_frozen"]:
        if proposal.get(flag) is not True:
            reasons.append(flag + "_not_true")
    if approval.get("researcher_confirmed") is not True or approval.get("proposal_sha256") != proposal_sha256 or approval.get("task_id") != TASK or not approval.get("decision_record"):
        reasons.append("exact_proposal_confirmation_missing")
    run_ids = approval.get("run_ids")
    if not isinstance(run_ids, list) or not all(isinstance(x, str) for x in run_ids) or run_id not in run_ids:
        reasons.append("single_run_authorization_missing")
    admission = proposal.get("admission") if isinstance(proposal.get("admission"), dict) else {}
    for name in ["initialization_policy_approved", "measurement_contract_approved", "input_fidelity_approved"]:
        if admission.get(name) is not True:
            reasons.append(name + "_not_true")
    isolation = proposal.get("isolation") if isinstance(proposal.get("isolation"), dict) else {}
    if isolation.get("accepted_for_new_task") is not True:
        reasons.append("accepted_for_new_task_not_true")
    if proposal.get("task_id") != TASK:
        reasons.append("wrong_task")
    return reasons


class EventJournal:
    """Single-writer, exclusive-create identity/runtime journal; no repair/reset."""
    def __init__(self, scope, path):
        self.scope, self.path = scope, scope.create(path, b"")
        self.seq, self.previous = 0, None

    def append(self, payload):
        event = dict(seq=self.seq, previous_sha256=self.previous, payload=payload)
        event["sha256"] = hashlib.sha256(canonical(event)).hexdigest()
        path = self.scope.check(self.path, writing=True)
        with path.open("ab") as stream:
            stream.write(canonical(event) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.seq += 1
        self.previous = event["sha256"]


def verify_journal(path):
    data = Path(path).read_bytes()
    if not data or not data.endswith(b"\n"):
        raise ValueError("journal_empty_or_incomplete")
    previous = None
    for seq, line in enumerate(data.splitlines()):
        e = json.loads(line)
        expected = e.pop("sha256")
        if e["seq"] != seq or e["previous_sha256"] != previous or hashlib.sha256(canonical(e)).hexdigest() != expected:
            raise ValueError("journal_sequence_or_hash")
        previous = expected
    return dict(events=seq + 1, head_sha256=previous)


def attach_FCD_observations(observer, path, *, allow_partial=False):
    count = 0
    try:
        for _, element in ET.iterparse(path, events=("end",)):
            if element.tag != "timestep":
                continue
            time_s = float(element.get("time"))
            for vehicle in element.findall("vehicle"):
                observer.observe_fcd(vehicle.get("id"), time_s)
                count += 1
            element.clear()
    except ET.ParseError as error:
        if not allow_partial:
            raise
        return dict(parse_complete=False, records_observed=count, reason=str(error), exact_insertion_time_inferred=False)
    return dict(parse_complete=True, records_observed=count, exact_insertion_time_inferred=False)


def environment_binding(packages=()):
    return dict(python_version=sys.version, python_executable_sha256=sha(Path(sys.executable)),
                packages={name: importlib.metadata.version(name) for name in packages})


def artifacts(scope, work):
    hashes, total = {}, 0
    for entry in Path(work).rglob("*"):
        path = scope.check(entry)
        if path.is_file():
            hashes[path.relative_to(scope.repo).as_posix()] = sha(path)
            total += path.stat().st_size
    return hashes, total


def output_size(scope, work):
    total = 0
    for entry in Path(work).rglob("*"):
        path = scope.check(entry)
        if path.is_file():
            total += path.stat().st_size
    return total


class ResourceSupervisor:
    def __init__(self, limits, scope, work, probe):
        self.limits, self.scope, self.work, self.probe = limits, scope, work, probe
        self.peak_rss = 0
        self.last = None

    def observe(self, *, startup=False):
        sample = dict(self.probe())
        size = output_size(self.scope, self.work)
        # Compatibility name in the immutable budget config; this is ONE capsule,
        # never the lifetime sum of historical research outputs.
        sample["task_output_bytes"] = size
        reason = resource_reason(self.limits, sample, startup=startup)
        self.peak_rss = max(self.peak_rss, sample["process_tree_rss_bytes"])
        self.last = sample
        if reason:
            raise RuntimeError("resource_limit:" + reason)
        return sample


class ResourceWatchdog:
    def __init__(self, supervisor, stop_owned_backend, *, interval_s=0.5):
        self.supervisor, self.stop_owned_backend, self.interval = supervisor, stop_owned_backend, interval_s
        self.done, self.failure = threading.Event(), None
        self.thread = None

    def start(self):
        def watch():
            while not self.done.wait(self.interval):
                try:
                    self.supervisor.observe()
                except Exception as error:
                    self.failure = type(error).__name__ + ":" + str(error)
                    try:
                        self.stop_owned_backend()
                    finally:
                        self.done.set()
        self.thread = threading.Thread(target=watch, daemon=True, name="AAD-owned-process-watchdog")
        self.thread.start()

    def close(self):
        self.done.set()
        if self.thread is not None:
            self.thread.join(timeout=2)
        if self.failure:
            raise RuntimeError(self.failure)


def native_resource_probe(backend):
    import psutil
    import shutil
    started = time.monotonic()
    def observe():
        rss = psutil.Process(os.getpid()).memory_info().rss
        if backend.process is not None:
            try:
                parent = psutil.Process(backend.process.pid)
                if parent.create_time() != backend.owner_creation_time:
                    raise RuntimeError("owned_PID_reused")
                for item in [parent] + parent.children(recursive=True):
                    try:
                        rss += item.memory_info().rss
                    except psutil.NoSuchProcess:
                        pass
            except psutil.NoSuchProcess:
                pass
        return dict(wall_s=time.monotonic() - started, process_tree_rss_bytes=rss,
                    free_c_bytes=shutil.disk_usage("C:/").free, free_d_bytes=shutil.disk_usage("D:/").free,
                    available_memory_bytes=psutil.virtual_memory().available, task_output_bytes=0)
    return observe


class ReplayBackend:
    """A data-only fake runner. It has no callable process factory."""
    synthetic_only = True

    def __init__(self, frames, *, fail_at=None):
        self.frames = iter(frames)
        self.fail_at = fail_at
        self.steps = 0
        self.stopped = False

    def start(self, *_):
        return next(self.frames)

    def step(self):
        self.steps += 1
        if self.fail_at == self.steps:
            raise RuntimeError("synthetic_runner_failure")
        return next(self.frames)

    def stop(self):
        self.stopped = True


class NativeBackend:
    synthetic_only = False

    def __init__(self):
        self.process = self.connection = None
        self.owner_creation_time = None

    def start(self, context):
        if NATIVE_LAUNCH_LOCKED:
            raise AdmissionRefused("engineering_build_native_launch_locked")
        # Defense in depth if a later reviewed build changes the constant.
        if gate_reasons(context["proposal"], context["approval"], context["run"]["id"], context["proposal_sha256"]):
            raise AdmissionRefused("native_backend_gate_failed")
        command = context["native_command"]
        if context["scope"].used:
            raise AdmissionRefused("single_process_only")
        context["scope"].process(command, cwd=context["work"], shell=False)
        self.process = subprocess.Popen(command, executable=command[0], cwd=context["work"], env=context["native_environment"],
                                        stdout=context["native_log"], stderr=subprocess.STDOUT, shell=False)
        import psutil
        self.owner_creation_time = psutil.Process(self.process.pid).create_time()
        sys.path.insert(0, context["traci_tools_root"])
        import traci
        traci.init(port=context["port"], numRetries=10, proc=self.process, label=context["run"]["id"])
        self.connection = traci.getConnection(context["run"]["id"])
        actual_version = self.connection.getVersion()
        if list(actual_version) != context["expected_runtime_version"]:
            raise RuntimeError("connected_SUMO_version_mismatch")
        return collect_snapshot(self.connection, initial=True)

    def step(self):
        self.connection.simulationStep()
        return collect_snapshot(self.connection)

    def before_step(self, now, context):
        schedule = context["run"]["lane_speed_schedule"]
        target = next(x["speed_mps"] for x in schedule if x["start_s"] <= now < x["end_s"])
        limits = {}
        for lane in context["run"]["supply_target_lanes"]:
            self.connection.lane.setMaxSpeed(lane, target)
            limits[lane] = self.connection.lane.getMaxSpeed(lane)
        if any(abs(v - target) > 1e-9 for v in limits.values()):
            raise RuntimeError("supply_not_imposed")
        return dict(applied_before_step_s=now, target_mps=target, native_lane_limits=limits)

    def finish(self):
        self.connection.close()
        if self.process.wait(timeout=10) != 0:
            raise RuntimeError("native_nonzero_exit")

    def stop(self):
        # Only the process created by this backend; PID reuse is rejected.
        if self.process is None:
            return
        import psutil
        try:
            parent = psutil.Process(self.process.pid)
            if parent.create_time() != self.owner_creation_time:
                raise RuntimeError("owned_PID_reused")
            children = parent.children(recursive=True)
            for child in reversed(children):
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            parent.terminate()
            _, alive = psutil.wait_procs(children + [parent], timeout=5)
            for item in alive:
                item.kill()
        except psutil.NoSuchProcess:
            pass
        if self.connection is not None:
            self.connection.close()


def measure_completed_capsule(context, identity):
    """Current scientific functions, unchanged. A missing reference is rejection."""
    import pandas as pd
    from riskprop.stage_0_5_scene_reconstruction import parse_fcd, network_edge_lengths
    from riskprop import stage_0_5_state_support as ss
    from riskprop.stage_0_5_d1_measurement import local_d1_measurement, offset100_cloud
    work, run = context["work"], context["run"]
    fcd = parse_fcd(work / "fcd.xml", network_edge_lengths(work / "network.net.xml"))
    measured = ss.measure_state_frame(ss.fcd_to_state_frame(fcd, ss.route_length_map(work / "routes.rou.xml"),
        run_id=run["id"], scenario_id=run["condition"], seed=run["seed"]))
    result = local_d1_measurement(measured, run["evaluation_elapsed_s"], strict=True)
    cloud = offset100_cloud(measured, run["evaluation_elapsed_s"])
    for i, row in cloud.iterrows():
        sub = local_d1_measurement(measured, (row.block_start_s, row.block_end_s), region=(row.y_start_m, row.y_end_m), strict=True)
        cloud.loc[i, "D1_E_veh_s"] = sub["local_evaluable_s"]
    common = len(cloud) == 18 and cloud.states.ge(10).all() and cloud.D1_E_veh_s.gt(0).all() and fcd.time_s.max() >= max(run["evaluation_elapsed_s"])
    for name in run.get("common_support_references", []):
        data = context["scope"].read_bound(name)
        import io
        reference = pd.read_csv(io.BytesIO(data))
        common = common and set(zip(reference.t_block, reference.y_block)) == set(zip(cloud.t_block, cloud.y_block)) and reference.D1_E_veh_s.gt(0).all()
    common = common and bool(run.get("common_support_references"))
    context["scope"].create(work / "D1_measurement.json", canonical(result) + b"\n")
    context["scope"].create(work / "common_support.csv", cloud.to_csv(index=False).encode())
    complete = identity["identity_accounting_complete"]
    return dict(input_fidelity=False, initialization_accounting=complete, identity_clock=identity["native_departure_clock_complete"],
                D1_contract=result["eligibility"] == "D1_contract_implemented", all18_common_cells=bool(common),
                full_context_events=True, resource_limits=True, task_isolation=False,
                pending_native_acceptance=["per-run input manipulation/initialization acceptance and native isolation require independent evidence"])


class ExecutionAdapter:
    def __init__(self, repo, ledger, report_root):
        self.repo, self.ledger = Path(repo).resolve(), ledger
        self.report_scope = Scope(self.repo, {}, report_root)

    def refuse(self, reasons, run_id):
        report = {"task_id": TASK, "run_id": run_id, "status": "rejected_before_reservation_and_process",
                  "reasons": reasons, "native_processes_created": 0, "new_trajectories": 0}
        self.report_scope.create(self.report_scope.output / ("refusal_" + uuid.uuid4().hex + ".json"), canonical(report) + b"\n")
        raise AdmissionRefused(";".join(reasons))

    def preflight(self, proposal_path, approval, run_id, *, synthetic=False):
        path = self.report_scope._lexical(proposal_path)
        if not path.is_relative_to(self.repo):
            self.refuse(["proposal_path_outside_repository"], run_id)
        data = path.read_bytes()
        proposal = json.loads(data)
        proposal_sha = hashlib.sha256(data).hexdigest()
        reasons = gate_reasons(proposal, approval, run_id, proposal_sha)
        if not synthetic and NATIVE_LAUNCH_LOCKED:
            reasons.append("engineering_build_native_launch_locked")
        if synthetic and proposal.get("synthetic_test_only") is not True:
            reasons.append("replay_requires_explicit_synthetic_fixture")
        if reasons:
            self.refuse(reasons, run_id)
        run = next((r for r in proposal.get("runs", []) if r.get("id") == run_id), None)
        if run is None:
            self.refuse(["run_not_in_exact_proposal"], run_id)
        try:
            if proposal["budget_sha256"] != sha(self.ledger.config_path):
                raise ValueError("budget_binding_changed")
            work = self.report_scope._lexical(run["artifact_path"])
            if not work.is_relative_to((self.repo / self.ledger.config["output_root"]).resolve()) or work.exists():
                raise ValueError("artifact_path_exists_or_outside_task")
            bindings = dict(proposal["source_sha256"])
            bindings.update(run["input_sha256"])
            bindings[proposal["plan_path"]] = proposal["plan_sha256"]
            bindings[proposal["isolation"]["report_path"]] = proposal["isolation"]["report_sha256"]
            bindings.update(proposal.get("external_file_sha256", {}))
            bindings.update(proposal.get("measurement_reference_sha256", {}))
            scope = Scope(self.repo, bindings, work, native_allowed=not NATIVE_LAUNCH_LOCKED)
            validated = {name: scope.read_bound(name) for name in bindings}
            actual_environment = environment_binding(proposal["environment"].get("packages", {}))
            if actual_environment != proposal["environment"]:
                raise ValueError("environment_binding_changed")
            inputs = run["input_files"]
            if set(inputs) != {"network.net.xml", "routes.rou.xml", "run.sumocfg"} or set(inputs.values()) != set(run["input_sha256"]):
                raise ValueError("exact_capsule_input_files_required")
            config_references(validated[inputs["run.sumocfg"]], expected_inputs={"net-file": "network.net.xml", "route-files": "routes.rou.xml"})
            cfg = xml(validated[inputs["run.sumocfg"]])
            if int(cfg.find(".//seed").get("value")) != run["seed"] or float(cfg.find("time/end").get("value")) != run["duration_s"]:
                raise ValueError("config_seed_or_duration_mismatch")
            return dict(proposal=proposal, approval=approval, run=run, proposal_path=proposal_path, proposal_sha256=proposal_sha,
                        work=work, scope=scope, validated_inputs={name: validated[src] for name, src in inputs.items()})
        except (ValueError, KeyError, OSError) as error:
            self.refuse([type(error).__name__ + ":" + str(error)], run_id)

    def execute(self, proposal_path, approval, run_id, *, backend=None, resource_probe=None, measurement=None):
        backend = NativeBackend() if backend is None else backend
        synthetic = type(backend) is ReplayBackend
        context = self.preflight(proposal_path, approval, run_id, synthetic=synthetic)
        if synthetic and (resource_probe is None or measurement is None):
            self.refuse(["synthetic_probe_and_measurement_required"], run_id)
        if not synthetic:
            resource_probe = native_resource_probe(backend) if resource_probe is None else resource_probe
            measurement = measure_completed_capsule if measurement is None else measurement
        scope, run, work = context["scope"], context["run"], context["work"]
        startup = resource_probe()
        startup["task_output_bytes"] = 0
        if resource_reason(self.ledger.config["single_attempt_limits"], startup, startup=True):
            self.refuse(["resource_preflight_failed"], run_id)
        # Only an explicit synthetic proposal reaches this line in this build.
        try:
            self.ledger.reserve(proposal_path, approval, run_id, startup)
        except (ValueError, PermissionError) as error:
            self.refuse([type(error).__name__ + ":" + str(error)], run_id)
        observer = journal = supervisor = watchdog = None
        execution_completed = False
        try:
            for name, data in context["validated_inputs"].items():
                scope.create(work / name, data)
            _, vehicles, _, _, _ = inventory(context["validated_inputs"]["routes.rou.xml"])
            observer = IdentityObserver([{"id": ident, "depart_s": float(v.get("depart"))} for ident, v in vehicles.items()])
            journal = EventJournal(scope, work / "identity_events.jsonl")
            supervisor = ResourceSupervisor(self.ledger.config["single_attempt_limits"], scope, work, resource_probe)
            supervisor.observe(startup=True)
            self.ledger.transition(run_id, "running")
            if not synthetic:
                import socket
                with socket.socket() as listener:
                    listener.bind(("127.0.0.1", 0))
                    port = listener.getsockname()[1]
                p = context["proposal"]
                binary = p["native_binary"]
                if binary not in p["external_file_sha256"]:
                    raise ValueError("native_binary_not_bound")
                context.update(port=port, traci_tools_root=p["traci_tools_root"], expected_runtime_version=p["native_runtime_version"],
                               native_environment=p["native_environment"],
                               native_command=[binary, "-c", str(work / "run.sumocfg"), "--remote-port", str(port), "--no-step-log", "true"])
                scope.commands = [context["native_command"]]
                scope.create(work / "native_console.log", b"")
                context["native_log"] = (work / "native_console.log").open("ab")
                watchdog = ResourceWatchdog(supervisor, backend.stop, interval_s=self.ledger.config["single_attempt_limits"]["supervision_poll_s"])
                watchdog.start()
            observer.ingest(backend.start(context))
            journal.append(observer.frames[-1])
            for _ in range(round(run["duration_s"] / observer.step)):
                control = backend.before_step(observer.time, context) if not synthetic else None
                frame = backend.step()
                if control is not None:
                    frame["controls"] = control
                observer.ingest(frame)
                journal.append(observer.frames[-1])
                if frame.get("teleport_start") or (frame.get("collision_count") or 0) > 0:
                    raise RuntimeError("collision_or_teleport_stop")
                supervisor.observe()
            if synthetic:
                backend.stop()
            else:
                backend.finish()
                fcd_status = attach_FCD_observations(observer, work / "fcd.xml")
                scope.create(work / "FCD_observation_status.json", canonical(fcd_status) + b"\n")
            summary = observer.finish()
            scope.create(work / "identity_summary.json", canonical(summary) + b"\n")
            verify_journal(work / "identity_events.jsonl")
            hashes, size = artifacts(scope, work)
            resource = dict(wall_s=supervisor.last["wall_s"], process_tree_rss_bytes=supervisor.peak_rss, artifact_bytes=size)
            self.ledger.transition(run_id, "completed", resources=resource)
            execution_completed = True
            checks = measurement(context, summary)
            scope.create(work / "measurement_acceptance.json", canonical(checks) + b"\n")
            supervisor.observe()
            hashes, _ = artifacts(scope, work)
            if watchdog is not None:
                watchdog.close()
            self.ledger.transition(run_id, "measurement_accepted" if all(checks.get(k) is True for k in CHECKS) else "measurement_rejected",
                                   checks=checks, reason=None if all(checks.get(k) is True for k in CHECKS) else "synthetic_measurement_contract_rejected",
                                   artifact_sha256=hashes)
            if "native_log" in context:
                context["native_log"].close()
            return self.ledger.snapshot()
        except BaseException as error:
            cleanup_errors = []
            if watchdog is not None:
                watchdog.done.set()
                if watchdog.thread is not None:
                    watchdog.thread.join(timeout=2)
            try:
                backend.stop()
            except Exception as cleanup_error:
                cleanup_errors.append(type(cleanup_error).__name__ + ":" + str(cleanup_error))
            if "native_log" in context:
                context["native_log"].close()
            if observer is not None:
                scope.create(work / "interrupted_identity_summary.json", canonical(observer.finish(interrupted=True)) + b"\n")
            if cleanup_errors:
                scope.create(work / "cleanup_errors.json", canonical(cleanup_errors) + b"\n")
            _, size = artifacts(scope, work) if work.exists() else ({}, 0)
            if execution_completed:
                self.ledger.transition(run_id, "measurement_rejected", reason=type(error).__name__ + ":" + str(error), checks=dict.fromkeys(CHECKS, False))
            else:
                last = supervisor.last if supervisor is not None and supervisor.last is not None else {}
                self.ledger.transition(run_id, "interrupted" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "failed",
                    reason=type(error).__name__ + ":" + str(error), resources=dict(wall_s=last.get("wall_s"), process_tree_rss_bytes=last.get("process_tree_rss_bytes"), artifact_bytes=size))
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Static gate report only; native launch unavailable")
    parser.add_argument("--proposal", type=Path, required=True)
    args = parser.parse_args()
    data = args.proposal.read_bytes()
    p = json.loads(data)
    print(json.dumps({"reasons": gate_reasons(p, {}, p.get("runs", [{}])[0].get("id"), hashlib.sha256(data).hexdigest()),
                      "native_launch_locked": NATIVE_LAUNCH_LOCKED, "native_processes_created": 0}, ensure_ascii=False))
