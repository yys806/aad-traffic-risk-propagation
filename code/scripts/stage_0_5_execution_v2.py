"""V2 execution interfaces. Native launch is hard-locked in this engineering build.

The replay path uses explicit synthetic fixtures and never creates a process.
The native backend is implemented for later review, but cannot be enabled by a
proposal, environment variable or CLI argument in this build.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import importlib
import platform
import json
import math
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


def gate_reasons(proposal, approval, run_id, proposal_sha256, *, task_id=TASK):
    if not isinstance(proposal, dict):
        return ["invalid_proposal_object"]
    if not isinstance(approval, dict):
        approval = {}
    reasons = []
    for flag in ["execution_allowed", "researcher_confirmed", "protocol_frozen"]:
        if proposal.get(flag) is not True:
            reasons.append(flag + "_not_true")
    if approval.get("researcher_confirmed") is not True or approval.get("proposal_sha256") != proposal_sha256 or approval.get("task_id") != task_id or not approval.get("decision_record"):
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
    if proposal.get("task_id") != task_id:
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


def attach_FCD_observations(observer, path, *, allow_partial=False, heartbeat=None):
    # A full FCD can take seconds to replay. Keep the production resource
    # observer active in this phase, just as in the native stepping loop.
    last_heartbeat = time.monotonic()
    if heartbeat is not None:
        heartbeat()
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
            if heartbeat is not None and time.monotonic() - last_heartbeat >= .05:
                heartbeat()
                last_heartbeat = time.monotonic()
    except ET.ParseError as error:
        if not allow_partial:
            raise
        return dict(parse_complete=False, records_observed=count, reason=str(error), exact_insertion_time_inferred=False)
    if heartbeat is not None:
        heartbeat()
    return dict(parse_complete=True, records_observed=count, exact_insertion_time_inferred=False)


def environment_binding(packages=()):
    versions = {}
    modules = {}
    for name in packages:
        module = importlib.import_module(name)
        versions[name] = importlib.metadata.version(name) or getattr(module, "__version__", None)
        if not versions[name]:
            raise ValueError("package_version_unavailable:" + name)
        modules[name] = dict(path=module.__file__, sha256=sha(Path(module.__file__)))
    return dict(python_version=sys.version, python_executable_sha256=sha(Path(sys.executable)),
                packages=versions, module_entries=modules, platform=platform.platform(), python_executable=sys.executable)


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
        self.samples = []
        self._sampling_lock = threading.RLock()

    def observe(self, *, startup=False):
        # Stepping/postprocessing and the watchdog can observe concurrently.
        # Serialize complete probes so sample clocks and append order agree.
        with self._sampling_lock:
            return self._observe(startup=startup)

    def _observe(self, *, startup=False):
        sample = dict(self.probe())
        size = output_size(self.scope, self.work)
        # Compatibility name in the immutable budget config; this is ONE capsule,
        # never the lifetime sum of historical research outputs.
        sample["task_output_bytes"] = size
        reason = resource_reason(self.limits, sample, startup=startup)
        self.peak_rss = max(self.peak_rss, sample["process_tree_rss_bytes"])
        self.last = sample
        self.samples.append(dict(sample))
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
        with backend._identity_lock:
            process, birth = backend.process, backend.owner_creation_time
        if process is not None:
            try:
                parent = psutil.Process(process.pid)
                if parent.create_time() != birth:
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

    def __init__(self, frames, *, fail_at=None, outputs=None, runtime_evidence=None):
        self.frames = iter(frames)
        self.fail_at = fail_at
        self.steps = 0
        self.stopped = False
        self.outputs = outputs or {}
        self.runtime_evidence = runtime_evidence or {}
        self.exit_code = None

    def start(self, context):
        self.context = context
        return next(self.frames)

    def step(self):
        self.steps += 1
        if self.fail_at == self.steps:
            raise RuntimeError("synthetic_runner_failure")
        return next(self.frames)

    def stop(self):
        self.stopped = True

    def finish(self):
        for name, data in self.outputs.items():
            self.context["scope"].create(self.context["work"] / name, data)
        self.exit_code = 0
        self.stop()


class NativeBackend:
    synthetic_only = False

    def __init__(self):
        self.process = self.connection = None
        self.owner_creation_time = None
        self._identity_lock = threading.RLock()

    def start(self, context):
        capsule_context=context.get("native_capsule_context")
        if not isinstance(capsule_context,dict):
            raise AdmissionRefused("engineering_build_native_launch_locked")
        # The legacy bare-host lock remains True. Native execution is admitted
        # only by the exact capsule context plus live kernel checks, never a flag.
        from stage_0_5_native_capsule_v4 import verify_live_context
        verify_live_context(capsule_context)
        command = context["native_command"]
        if context["scope"].used:
            raise AdmissionRefused("single_process_only")
        context["scope"].process(command, cwd=context["work"], shell=False)
        import psutil
        with self._identity_lock:
            self.process = subprocess.Popen(command, executable=command[0], cwd=context["work"], env=context["native_environment"],
                                            stdout=context["native_log"], stderr=subprocess.STDOUT, shell=False)
            self.console_path = context["work"] / "native_console.log"
            self.owner_creation_time = psutil.Process(self.process.pid).create_time()
        sys.path.insert(0, context["traci_tools_root"])
        import traci
        if sha(Path(traci.__file__)) != capsule_context["runtime"]["traci_init_sha256"]:
            raise RuntimeError("bound_TraCI_source_mismatch")
        traci.init(port=context["port"], numRetries=10, proc=self.process, label=context["run"]["id"])
        self.connection = traci.getConnection(context["run"]["id"])
        actual_version = self.connection.getVersion()
        if list(actual_version) != context["expected_runtime_version"]:
            raise RuntimeError("connected_SUMO_version_mismatch")
        return collect_snapshot(self.connection, initial=True)

    def step(self):
        self.connection.simulationStep()
        # A native error is a stop condition, not identity-level discard proof.
        if getattr(self, "console_path", None) and "Error:" in self.console_path.read_text(encoding="utf-8", errors="replace"):
            raise RuntimeError("native_error_log_stop_preserve_identity_unknown")
        return collect_snapshot(self.connection)

    def before_step(self, now, context):
        schedule = context["run"]["lane_speed_schedule"]
        target = next(x["speed_mps"] for x in schedule if x["start_s"] <= now < x["end_s"])
        record = dict(applied_before_step_s=now,target_mps=target,native_lane_limits={},failures=[])
        self.last_control = record
        try:
            actual_clock = self.connection.simulation.getTime()
            record["native_clock_before_s"] = actual_clock if math.isfinite(actual_clock) else None
            if not math.isfinite(actual_clock) or abs(actual_clock-now)>1e-7: raise ValueError("control_native_clock_mismatch")
        except Exception as error:
            record["failures"].append(type(error).__name__+":"+str(error))
            raise RuntimeError("supply_clock_unavailable_or_mismatched") from error
        for lane in context["run"]["supply_target_lanes"]:
            try:
                self.connection.lane.setMaxSpeed(lane, target)
                value = self.connection.lane.getMaxSpeed(lane)
                record["native_lane_limits"][lane] = value if math.isfinite(value) else None
                if not math.isfinite(value) or abs(value-target)>1e-9: record["failures"].append(lane+":readback_mismatch_or_nonfinite")
            except Exception as error:
                record["failures"].append(lane+":"+type(error).__name__+":"+str(error))
        if record["failures"]:
            raise RuntimeError("supply_not_imposed")
        return record

    def finish(self):
        self.connection.close()
        self.exit_code = self.process.wait(timeout=10)
        if self.exit_code != 0:
            raise RuntimeError("native_nonzero_exit")

    def stop(self):
        # Only the process created by this backend; PID reuse is rejected.
        if self.process is None:
            return
        if self.owner_creation_time is None:
            # Popen's own handle is authoritative before PID metadata commits.
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=5)
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
    """Evidence-derived eight checks; core C6/P2/D1 algorithms remain unchanged."""
    from stage_0_5_acceptance_v3 import assess_capsule
    return assess_capsule(context, identity)


def run_observation_loop(context,backend,observer,journal,supervisor,*,synthetic):
    """Shared production/replay stepping; identity/scientific semantics unchanged."""
    for _ in range(round(context["run"]["duration_s"]/observer.step)):
        control=backend.before_step(observer.time,context) if not synthetic else None
        frame=backend.step()
        if control is not None:frame["controls"]=control
        if not synthetic:
            # The native collector marks every post-step frame as requiring a
            # valid collision getter result.  Keep the check at the execution
            # boundary as well so a custom/native backend cannot silently turn
            # an unavailable value into a zero.
            frame["collision_observation_required"] = True
        try:
            observer.ingest(frame)
        except Exception as error:
            journal.append(dict(frame, observation_rejected=type(error).__name__ + ":" + str(error)))
            raise
        journal.append(observer.frames[-1])
        if not synthetic:
            for kind in ("teleport_start", "teleport_end"):
                if frame.get(kind) is None:
                    raise RuntimeError("identity_observation_missing:" + kind)
            status = frame.get("collision_observation_status")
            count = frame.get("collision_count")
            if status != "available" or type(count) is not int or count < 0:
                raise RuntimeError("collision_observation_missing_or_invalid")
        if frame.get("teleport_start") or (frame.get("collision_count") is not None and frame.get("collision_count") > 0):
            raise RuntimeError("collision_or_teleport_stop")
        supervisor.observe()


class ExecutionAdapter:
    def __init__(self, repo, ledger, report_root):
        self.repo, self.ledger = Path(repo).resolve(), ledger
        self.report_scope = Scope(self.repo, {}, report_root)

    def refuse(self, reasons, run_id):
        report = {"task_id": self.ledger.task_id, "run_id": run_id, "status": "rejected_before_reservation_and_process",
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
        reasons = gate_reasons(proposal, approval, run_id, proposal_sha, task_id=self.ledger.task_id)
        if not synthetic and self.ledger.config.get("execution_allowed") is not True:
            reasons.append("budget_execution_not_allowed")
        if proposal.get("task_id") == "AAD-0.5-READY-TO-ADMIT-V3" and not synthetic:
            from stage_0_5_admission_v3 import technical_preflight
            technical = technical_preflight(self.repo, path, run_id, resource_sample=native_resource_probe(NativeBackend())())
            self.report_scope.create(self.report_scope.output / ("technical_" + uuid.uuid4().hex + ".json"), canonical(technical) + b"\n")
            reasons.extend("technical:" + e for e in technical["technical_errors"])
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
            bindings.update(proposal.get("support_input_sha256", {}))
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
            return dict(proposal=proposal, approval=approval, run=run, proposal_path=proposal_path, proposal_sha256=proposal_sha, budget_task_id=self.ledger.task_id,
                        work=work, scope=scope, validated_inputs={name: validated[src] for name, src in inputs.items()})
        except (ValueError, KeyError, OSError) as error:
            self.refuse([type(error).__name__ + ":" + str(error)], run_id)

    def execute(self, proposal_path, approval, run_id, *, backend=None, resource_probe=None, measurement=None):
        candidate_path=self.report_scope._lexical(proposal_path)
        if json.loads(candidate_path.read_bytes()).get("schema")=="aad.native-admission.v4":
            if backend is not None or resource_probe is not None or measurement is not None:
                self.refuse(["native_test_override_forbidden"],run_id)
            from stage_0_5_linux_execution_v4 import execute_research
            return execute_research(self,proposal_path,approval,run_id)
        backend = NativeBackend() if backend is None else backend
        synthetic = type(backend) is ReplayBackend
        if not synthetic and (resource_probe is not None or measurement is not None):
            self.refuse(["native_test_override_forbidden"],run_id)
        context = self.preflight(proposal_path, approval, run_id, synthetic=synthetic)
        if synthetic and resource_probe is None:
            self.refuse(["synthetic_resource_probe_required"], run_id)
        measurement = measure_completed_capsule if measurement is None else measurement
        context.update(synthetic_only=synthetic, resource_limits=self.ledger.config["single_attempt_limits"],
                       binding_sha256=hashlib.sha256(canonical(context["proposal"])).hexdigest())
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
                scope.check(work / "tmp", writing=True).mkdir(exist_ok=False)
                with socket.socket() as listener:
                    listener.bind(("127.0.0.1", 0))
                    port = listener.getsockname()[1]
                p = context["proposal"]
                binary = p["native_binary"]
                if binary not in p["external_file_sha256"]:
                    raise ValueError("native_binary_not_bound")
                context.update(port=port, traci_tools_root=p["traci_tools_root"], expected_runtime_version=p["native_runtime_version"],
                               native_environment=run.get("native_environment", p["native_environment"]),
                               native_command=[binary, "-c", str(work / "run.sumocfg"), "--remote-port", str(port), "--no-step-log", "true"])
                scope.commands = [context["native_command"]]
                scope.create(work / "native_console.log", b"")
                context["native_log"] = (work / "native_console.log").open("ab")
                watchdog = ResourceWatchdog(supervisor, backend.stop, interval_s=self.ledger.config["single_attempt_limits"]["supervision_poll_s"])
                watchdog.start()
            observer.ingest(backend.start(context))
            journal.append(observer.frames[-1])
            run_observation_loop(context,backend,observer,journal,supervisor,synthetic=synthetic)
            backend.finish()
            if not synthetic or backend.outputs:
                fcd_status = attach_FCD_observations(observer, work / "fcd.xml")
                scope.create(work / "FCD_observation_status.json", canonical(fcd_status) + b"\n")
                trip_status = observer.observe_tripinfo((work / "tripinfo.xml").read_bytes())
                scope.create(work / "TripInfo_observation_status.json", canonical(trip_status) + b"\n")
            summary = observer.finish()
            scope.create(work / "identity_summary.json", canonical(summary) + b"\n")
            verify_journal(work / "identity_events.jsonl")
            supervisor.observe()
            context.update(identity_frames=observer.frames, runtime_evidence=dict(
                resource_samples=[dict(s) for s in supervisor.samples], run_finished_wall_s=supervisor.last["wall_s"],
                exit_code=backend.exit_code, watchdog_failure=None if watchdog is None else watchdog.failure,
                identity_journal_verified=True,
                 sealed_artifacts={name:sha(work / name) for name in ["fcd.xml", "summary.xml", "tripinfo.xml", "identity_events.jsonl", "identity_summary.json"] if (work / name).exists()}))
            if synthetic:
                # Explicit fixture kernel transcript, never native certification.
                for key in ["isolation"]:
                    if key in backend.runtime_evidence:
                        context["runtime_evidence"][key] = backend.runtime_evidence[key]
                context["isolation_transcript_sha256"] = backend.runtime_evidence.get("transcript_sha256", [])
            scope.create(work / "runtime_evidence.json", canonical(context["runtime_evidence"]) + b"\n")
            hashes, size = artifacts(scope, work)
            resource = dict(wall_s=supervisor.last["wall_s"], process_tree_rss_bytes=supervisor.peak_rss, artifact_bytes=size)
            self.ledger.transition(run_id, "completed", resources=resource)
            execution_completed = True
            checks = measurement(context, summary)
            supervisor.observe()
            hashes, _ = artifacts(scope, work)
            if watchdog is not None:
                watchdog.close()
            if measurement is measure_completed_capsule:
                from stage_0_5_acceptance_v3 import resource_acceptance
                context["runtime_evidence"]["resource_samples"] = [dict(s) for s in supervisor.samples]
                context["runtime_evidence"]["run_finished_wall_s"] = supervisor.last["wall_s"]
                final_resources = resource_acceptance(context)
                checks["resource_limits"] = final_resources["passed"]
                checks["verdicts"]["resource_limits"] = final_resources
                scope.create(work / "runtime_final_evidence.json", canonical(context["runtime_evidence"]) + b"\n")
            scope.create(work / "measurement_acceptance.json", canonical(checks) + b"\n")
            hashes, size = artifacts(scope, work)
            resource = dict(wall_s=supervisor.last["wall_s"], process_tree_rss_bytes=supervisor.peak_rss, artifact_bytes=size)
            self.ledger.transition(run_id, "measurement_accepted" if all(checks.get(k) is True for k in CHECKS) else "measurement_rejected",
                                   checks=checks, reason=None if all(checks.get(k) is True for k in CHECKS) else "synthetic_measurement_contract_rejected",
                                   artifact_sha256=hashes, resources=resource)
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
            try:
                if observer is not None:
                    scope.create(work / "interrupted_identity_summary.json", canonical(observer.finish(interrupted=True)) + b"\n")
                if getattr(backend,"last_control",None) is not None:
                    scope.create(work / "failed_or_last_control.json",canonical(backend.last_control)+b"\n")
                if cleanup_errors:
                    scope.create(work / "cleanup_errors.json", canonical(cleanup_errors) + b"\n")
                failure_hashes, size = artifacts(scope, work) if work.exists() else ({}, 0)
            except (OSError,ValueError) as artifact_error:
                cleanup_errors.append("failure_artifact_collection:"+type(artifact_error).__name__+":"+str(artifact_error))
                failure_hashes, size = {}, None
                self.report_scope.create(self.report_scope.output/("failed_capsule_"+uuid.uuid4().hex+".json"),
                    canonical(dict(run_id=run_id,original_error=type(error).__name__+":"+str(error),collection_errors=cleanup_errors))+b"\n")
            if execution_completed:
                self.ledger.transition(run_id, "measurement_rejected", reason=type(error).__name__ + ":" + str(error),
                    checks=dict.fromkeys(CHECKS, False), artifact_sha256=failure_hashes,
                    resources=dict(wall_s=supervisor.last["wall_s"], process_tree_rss_bytes=supervisor.peak_rss, artifact_bytes=size))
            else:
                last = supervisor.last if supervisor is not None and supervisor.last is not None else {}
                self.ledger.transition(run_id, "interrupted" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "failed",
                    reason=type(error).__name__ + ":" + str(error), resources=dict(wall_s=last.get("wall_s"), process_tree_rss_bytes=last.get("process_tree_rss_bytes"), artifact_bytes=size),artifact_sha256=failure_hashes)
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Static gate report only; native launch unavailable")
    parser.add_argument("--proposal", type=Path, required=True)
    args = parser.parse_args()
    data = args.proposal.read_bytes()
    p = json.loads(data)
    print(json.dumps({"reasons": gate_reasons(p, {}, p.get("runs", [{}])[0].get("id"), hashlib.sha256(data).hexdigest()),
                      "native_launch_locked": NATIVE_LAUNCH_LOCKED, "native_processes_created": 0}, ensure_ascii=False))
