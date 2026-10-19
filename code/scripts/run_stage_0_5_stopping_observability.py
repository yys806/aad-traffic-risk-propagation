"""B1.1-S: public-interface observability of SUMO ballistic stopping (<=3 declared runs).

Reuses the B1/B1.1 controlled-capsule, source whitelist, SHA binding and frozen
plan pattern. No real traffic data, no debug binary, no Stage 0.5 change, no B1.2.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/src"))
RESULT_ID = "RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1"
SUMO_SOURCE_COMMIT = "fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3"
# Named, SHA-bound B1.1 audit summaries (metadata only, no traffic states).
B11_SUMMARY = ["stopping_source_audit.json", "displacement_branch_contract.json",
               "micro_sumo_numerical_audit.json", "future_experiment_preconditions.json"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, d):
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare(batch):
    if (batch / "experiment_plan.json").exists():
        raise ValueError("sealed observability batch cannot be prepared again")
    from riskprop.stage_0_5_boundary_bottleneck import _copy_runtime
    from riskprop.stage_0_5_sumo import _sumo_binary, _netconvert_binary
    batch.mkdir(parents=True, exist_ok=True)
    (batch / "inputs/history").mkdir(parents=True, exist_ok=True)
    base = ROOT / "evidence/results/RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1"
    manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    bindings = {}
    for name in B11_SUMMARY:
        bindings[name] = dict(path=name, role="engineering_metadata", kind="historical_b11_summary",
                              sha256=next(f["sha256"] for f in manifest["files"] if f["path"] == name))
        if sha(base / name) != bindings[name]["sha256"]:
            raise PermissionError("B1.1 summary SHA mismatch")
        shutil.copyfile(base / name, batch / "inputs/history" / name)
    write(batch / "source_staging_manifest.json", dict(sources=bindings, declared_before_reads=True,
        no_real_data_inputs=True, no_old_C_states=True,
        prohibited=["us101__0820_0835", "locked_holdout", "historical Stage0.2 full-source artifacts",
                    "old B1 C full state table"]))
    write(batch / "historical_source_manifest.json", bindings)
    # Re-fetch official sources immutably for the audit (tag -> resolved commit cross-check).
    sources = batch / "official_source"
    sources.mkdir(exist_ok=True)
    source_manifest = {}
    for tail in ["microsim/MSVehicle.cpp", "microsim/MSVehicle.h", "libsumo/Vehicle.cpp", "utils/common/SUMOTime.h"]:
        url = "https://raw.githubusercontent.com/eclipse-sumo/sumo/" + SUMO_SOURCE_COMMIT + "/src/" + tail
        target = sources / tail.replace("/", "_")
        source_manifest[target.name] = dict(url=url, tag="v1_26_0", resolved_commit=SUMO_SOURCE_COMMIT,
                                            purpose="official implementation audit only")
    write(batch / "official_source_request_manifest.json", source_manifest)
    for name, entry in source_manifest.items():
        target = sources / name
        if not target.exists() or not (sources / "immutable_verified.json").exists():
            old_sha = sha(target) if target.exists() else None
            with urllib.request.urlopen(entry["url"], timeout=30) as response:
                raw = response.read(2_000_000)
            target.write_bytes(raw)
            entry["initial_tag_fetch_sha256"] = old_sha
            entry["tag_and_immutable_fetch_equal"] = (old_sha == sha(target)) if old_sha else None
        entry["sha256"] = sha(target)
        entry["bytes"] = target.stat().st_size
    write(batch / "official_source_manifest.json", source_manifest)
    write(sources / "immutable_verified.json",
          dict(commit=SUMO_SOURCE_COMMIT, files={n: e["sha256"] for n, e in source_manifest.items()}))
    _copy_runtime(ROOT, batch)
    for name in ["stage_0_5_stopping_contract.py", "stage_0_5_stopping_observability.py"]:
        shutil.copyfile(ROOT / "code/src/riskprop" / name, batch / "runtime/code/src/riskprop" / name)
    for name in ["test_stage_0_5_stopping_contract.py", "test_stage_0_5_stopping_observability.py"]:
        shutil.copyfile(ROOT / "code/tests" / name, batch / "runtime/code/tests" / name)
    shutil.copyfile(Path(__file__), batch / "runtime/code/scripts" / Path(__file__).name)
    dependencies = []
    links = batch / "dependency_links"
    links.mkdir(exist_ok=True)
    for name in ["numpy", "pandas", "pyarrow", "psutil", "matplotlib", "pytest", "packaging", "dateutil"]:
        __import__(name)
    import _winapi
    for name, module in list(sys.modules.items()):
        if "." in name or not getattr(module, "__file__", None):
            continue
        source = Path(module.__file__).resolve()
        if "site-packages" not in source.parts or source.is_relative_to(Path(sys.prefix).resolve()):
            continue
        if source.name == "__init__.py":
            targets = [source.parent] + list(source.parent.parent.glob(name.replace("_", "-") + "-*.dist-info"))
            if (source.parent.parent / (name + ".libs")).is_dir():
                targets.append(source.parent.parent / (name + ".libs"))
            for target in targets:
                link = links / target.name
                if not link.exists():
                    _winapi.CreateJunction(str(target), str(link))
                dependencies.append(str(target))
        else:
            shutil.copyfile(source, links / source.name)
    write(batch / "isolation_policy.json", dict(
        runtime_read_roots=[str(Path(sys.prefix).resolve()), str(Path(_sumo_binary()).resolve().parent.parent),
                            os.environ.get("WINDIR", "C:/Windows")] + dependencies,
        executables=[sys.executable, str(Path(_sumo_binary()).resolve()), str(Path(_netconvert_binary()).resolve())],
        no_real_data_sources=True, os_complete_monitoring=False))
    write(batch / "preparation_manifest.json", dict(
        base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        b11_git_tree=subprocess.check_output(
            ["git", "rev-parse", "HEAD:evidence/results/RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1"],
            cwd=ROOT, text=True).strip()))
    print("B11S_CAPSULE_PREPARED", flush=True)


def environment(batch):
    (batch / "runtime_cache/tmp").mkdir(parents=True, exist_ok=True)
    (batch / "test_tmp").mkdir(exist_ok=True)
    os.environ.update(AAD_B1_CAPSULE=str(batch), PYTHONPATH=str(batch / "runtime/code/src"),
                      PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                      PYTHONPYCACHEPREFIX=str(batch / "runtime_cache/pycache"),
                      TEMP=str(batch / "runtime_cache/tmp"), TMP=str(batch / "runtime_cache/tmp"))


def tests(batch):
    environment(batch)
    probe = subprocess.run([sys.executable, "-S", str(batch / "runtime/code/scripts/b1_guard_probe.py"), str(batch)],
                           capture_output=True, text=True, timeout=30)
    if probe.returncode:
        raise RuntimeError("synthetic forbidden-path probe failed")
    names = ["test_stage_0_5_stopping_observability.py", "test_stage_0_5_stopping_contract.py",
             "test_stage_0_5_boundary_bottleneck.py"]
    paths = [str(batch / "runtime/code/tests" / n) for n in names if (batch / "runtime/code/tests" / n).exists()]
    cmd = [sys.executable, "-S", str(batch / "runtime/code/scripts/b1_test_entry.py"), *paths, "-q",
           "-c", str(batch / "runtime/code/pytest.ini"), "--rootdir", str(batch / "runtime/code"),
           "--basetemp", str(batch / "test_tmp" / str(time.time_ns())), "-o", f"cache_dir={batch/'runtime_cache/pytest'}"]
    r = subprocess.run(cmd, cwd=batch / "runtime/code", capture_output=True, text=True, timeout=120)
    name = f"test_{time.time_ns()}"
    (batch / (name + ".log")).write_text(r.stdout + r.stderr, encoding="utf-8")
    write(batch / (name + ".json"), dict(command=cmd, exit_code=r.returncode, output=r.stdout + r.stderr,
        test_sha256={str(p): sha(p) for p in paths},
        access_audit=json.loads((batch / "preflight_test_access_audit.json").read_text(encoding="utf-8"))))
    write(batch / "preflight.json", dict(passed=r.returncode == 0, last_test=name))
    write(batch / "data_isolation_preflight.json", dict(passed=r.returncode == 0,
        history_metadata_manifest=json.loads((batch / "historical_source_manifest.json").read_text(encoding="utf-8")),
        official_code_manifest=json.loads((batch / "official_source_manifest.json").read_text(encoding="utf-8")),
        real_data_inputs=[], old_C_state_access=False, historical_Stage0_2_full_source_access=False,
        synthetic_path_probe=json.loads((batch / "guard_probe_result.json").read_text(encoding="utf-8")),
        controlled_python_no_site=True, unexpected_test_denials=0 if r.returncode == 0 else "see test access audit",
        os_complete_monitoring=False, native_access_monitored=False, test_log=name))
    print(r.stdout + r.stderr, flush=True)
    if r.returncode:
        raise RuntimeError("observability tests failed; micro execution forbidden")


def freeze(batch):
    if (batch / "experiment_plan.json").exists():
        raise ValueError("never overwrite a frozen observability plan")
    if not json.loads((batch / "preflight.json").read_text())["passed"]:
        raise PermissionError("synthetic preflight not passed")
    from riskprop.stage_0_5_sumo import _sumo_binary, _netconvert_binary
    inputs = batch / "inputs"
    # One straight 250 m single-lane edge reused by all three runs.
    straight = inputs / "straight"
    straight.mkdir(parents=True, exist_ok=True)
    (straight / "nodes.nod.xml").write_text('<nodes><node id="n0" x="0" y="0"/><node id="n1" x="250" y="0"/></nodes>',
                                            encoding="utf-8")
    (straight / "edges.edg.xml").write_text(
        '<edges><edge id="e0" from="n0" to="n1" numLanes="1" speed="27.78"/></edges>', encoding="utf-8")
    r = subprocess.run([_netconvert_binary(), "-n", str(straight / "nodes.nod.xml"), "-e", str(straight / "edges.edg.xml"),
                        "-o", str(straight / "micro.net.xml"), "--no-turnarounds", "true"],
                       capture_output=True, text=True, timeout=30)
    (straight / "build.log").write_text(r.stdout + r.stderr, encoding="utf-8")
    if r.returncode:
        raise RuntimeError("micro network generation failed")
    fixed = dict(carFollowModel="Krauss", tau=1., minGap=2.5, accel=2.6, decel=4.5, apparentDecel=4.5,
                 emergencyDecel=9., sigma=.5, maxSpeed=27.78, speedFactor=1., speedDev=0.,
                 actionStepLength=.1, sigmaStep=1., laneChangeModel="LC2013", length=5.)
    # Three declared runs: free motion (action+non-action accel/cruise), and two
    # ordinary stop/restart runs at the two internal steps (both straddle dt/dt2).
    specs = [("motion_005", .05, False), ("stop_restart_005", .05, True), ("stop_restart_010", .1, True)]
    runs = []
    for name, step, stop in specs:
        route = ET.Element("routes")
        ET.SubElement(route, "vType", dict(id="fixed", **{k: str(v) for k, v in fixed.items()}))
        vehicle = ET.SubElement(route, "vehicle", dict(id="micro_v", type="fixed", depart="0",
                                                       departSpeed="10", departLane="0"))
        ET.SubElement(vehicle, "route", dict(edges="e0"))
        if stop:
            ET.SubElement(vehicle, "stop", dict(lane="e0_0", endPos="80", duration="3", parking="false"))
        demand = inputs / (name + ".rou.xml")
        ET.ElementTree(route).write(demand, encoding="utf-8", xml_declaration=True)
        config = inputs / (name + ".sumocfg")
        config.write_text(
            f'<configuration><input><net-file value="straight/micro.net.xml"/>'
            f'<route-files value="{name}.rou.xml"/></input>'
            f'<time><begin value="0"/><end value="30"/><step-length value="{step}"/></time>'
            f'<processing><step-method.ballistic value="true"/><threads value="1"/>'
            f'<time-to-teleport value="-1"/><collision.action value="warn"/></processing>'
            f'<seed value="20261019"/></configuration>', encoding="utf-8")
        runs.append(dict(run_id=name, config=config.relative_to(batch).as_posix(),
                         network="inputs/straight/micro.net.xml", demand=demand.relative_to(batch).as_posix(),
                         step_s=step, action_step_s=.1, duration_s=30., seed=20261019,
                         expected_ordinary_stop=stop))
    write(batch / "micro_fixture_manifest.json", dict(runs=runs, fixed=fixed,
        mode="public_interface_observability_only", no_debug_binary=True, no_risk_experiment=True,
        P2_computed=False, driving_parameter_search=False, real_data_inputs=False,
        note="free/probe instances only; no vehicle control (myInfluencer None)"))
    frozen = {p.relative_to(batch).as_posix(): sha(p)
              for folder in [batch / "runtime", batch / "inputs", batch / "official_source"]
              for p in sorted(folder.rglob("*")) if p.is_file() and "__pycache__" not in p.parts
              and p.name != "stage_0_5_observability_analysis.py"}
    for name in ["isolation_policy.json", "official_source_manifest.json", "historical_source_manifest.json",
                 "preflight.json", "data_isolation_preflight.json", "micro_fixture_manifest.json"]:
        frozen[name] = sha(batch / name)
    plan = dict(result_id=RESULT_ID, mode="public_interface_observability_only", runs=runs, fixed=fixed,
        scientific_claim_eligible=False, ready_to_start_stage_0_5_4b=False, reality_coverage_accepted=False,
        gate="pending_simulation_sample", protocol_lock_allowed=False, stage_1_1_allowed=False,
        tolerances="Tolerance Not Yet Justified", energy_distance_upper_bound="Not Identifiable",
        limits=dict(max_runs=3, per_run_wall_s=120, batch_wall_s=1800, memory_bytes=2 * 1024**3,
                    artifact_bytes=256 * 1024**2, per_run_duration_s=30),
        stopper=dict(any_engineering_blocker_stops_all_following=True, exact_residual_tolerance_m=1e-6,
                     decision_stop_is_bounded_not_exact=True,
                     identity_clock_conservation_collision_teleport_resource_SHA_errors="blocker"),
        debug_binary_used=False, frozen_files=frozen,
        analysis_renderer="separate unfrozen descriptive packaging only; cannot change measurements or rules")
    write(batch / "experiment_plan.json", plan)
    (batch / "PLAN_SHA256").write_text(sha(batch / "experiment_plan.json") + "  experiment_plan.json\n", encoding="utf-8")
    write(batch / "execution_ledger.json", dict(plan_sha256=sha(batch / "experiment_plan.json"), closed=False,
                                                runs=[dict(run_id=r["run_id"], status="not_attempted") for r in runs]))
    print("B11S_FROZEN " + sha(batch / "experiment_plan.json"), flush=True)


def read_plan(batch):
    from riskprop.stage_0_5_exploratory_response import verify_frozen
    digest = (batch / "PLAN_SHA256").read_text().split()[0]
    if sha(batch / "experiment_plan.json") != digest:
        raise ValueError("observability plan SHA mismatch")
    plan = json.loads((batch / "experiment_plan.json").read_text(encoding="utf-8"))
    verify_frozen(batch, plan["frozen_files"])
    return plan


def worker(batch, run_id):
    from riskprop.stage_0_5_stopping_observability import (
        step_is_action, reconstruct_signed_vnext, expected_displacement)
    from riskprop.stage_0_5_sumo import _sumo_binary, _ensure_traci_importable
    _ensure_traci_importable()
    import traci
    plan = read_plan(batch)
    spec = next(r for r in plan["runs"] if r["run_id"] == run_id)
    out = batch / "runs" / run_id
    if (out / "summary.json").exists():
        raise ValueError("no micro retries")
    out.mkdir(parents=True, exist_ok=True)
    h = spec["step_s"]
    adt = spec["action_step_s"]
    previous = {}
    edges = []
    departed, arrived = set(), set()
    collision, teleports = set(), set()
    observations = 0
    failure = None
    conn = None
    settings = {}
    command = [_sumo_binary(), "-c", str(batch / spec["config"]), "--no-step-log", "true",
               "--duration-log.disable", "true", "--error-log", str(out / "sumo_errors.log")]
    with (out / "observability_states.jsonl").open("w", encoding="utf-8") as raw:
        try:
            traci.start(command, label=run_id)
            conn = traci.getConnection(run_id)
            settings = {k: conn.simulation.getOption(k) for k in
                        ["step-method.ballistic", "step-length", "seed", "threads", "time-to-teleport"]}
            settings["sumo_version"] = conn.getVersion()
            settings["actual_action_step_s"] = conn.vehicletype.getActionStepLength("fixed")
            checks = [settings["step-method.ballistic"].lower() in ["1", "true"],
                      abs(float(settings["step-length"]) - h) < 1e-12,
                      int(settings["seed"]) == spec["seed"], int(settings["threads"]) == 1,
                      abs(settings["actual_action_step_s"] - adt) < 1e-12]
            settings["verified"] = all(checks)
            if not settings["verified"]:
                raise ValueError("micro runtime settings mismatch")
            for tick in range(1, round(spec["duration_s"] / h) + 1):
                conn.simulationStep()
                now = conn.simulation.getTime()
                if abs(now - tick * h) > 1e-9:
                    raise ValueError("runtime cadence")
                new = set(conn.simulation.getDepartedIDList())
                gone = set(conn.simulation.getArrivedIDList())
                if new & departed:
                    raise ValueError("vehicle identity reused")
                departed |= new
                arrived |= gone
                collision.update(conn.simulation.getCollidingVehiclesIDList())
                teleports.update(conn.simulation.getStartingTeleportIDList())
                if collision or teleports:
                    raise ValueError("collision/teleport")
                for vid in conn.vehicle.getIDList():
                    row = dict(run_id=run_id, vehicle_id=vid, incarnation_id=f"{run_id}|{vid}|0", time_s=now,
                               edge_id=conn.vehicle.getRoadID(vid), lane_id=conn.vehicle.getLaneID(vid),
                               position_m=conn.vehicle.getLanePosition(vid), speed_mps=conn.vehicle.getSpeed(vid),
                               a_pub=conn.vehicle.getAcceleration(vid),
                               last_action_time_s=conn.vehicle.getLastActionTime(vid))
                    raw.write(json.dumps(row) + "\n")
                    observations += 1
                    if vid in previous:
                        prev = previous[vid]
                        # identity / coordinate / clock guards before any subtraction
                        same = all(prev[k] == row[k] for k in ["run_id", "vehicle_id", "incarnation_id",
                                                               "edge_id", "lane_id"])
                        step_ok = abs(row["time_s"] - prev["time_s"] - h) <= 1e-9
                        if not same:
                            edges.append(dict(before=prev, after=row, branch="edge_or_lane_transition",
                                              classification="Not Evaluable", reason="coordinate_transition"))
                        elif not step_ok:
                            edges.append(dict(before=prev, after=row, branch="insufficient_observation",
                                              classification="Not Evaluable", reason="clock_step_mismatch"))
                        else:
                            # Action-step test: the step [t_prev -> now] is an action step
                            # iff lastActionTime read at `now` equals t_prev (the decision
                            # was taken at the step start).
                            is_act = step_is_action(row["last_action_time_s"], prev["time_s"], h, adt)
                            v0 = prev["speed_mps"]
                            v1 = row["speed_mps"]
                            a_pub_start = prev["a_pub"]
                            dx = row["position_m"] - prev["position_m"]
                            if is_act is None:
                                edges.append(dict(before=prev, after=row, branch="insufficient_observation",
                                                  classification="Not Evaluable", reason="action_step_unknown"))
                                previous[vid] = row
                                continue
                            if v0 == 0 and v1 == 0:
                                # rest-to-rest: displacement is exactly 0 regardless of hidden u
                                edges.append(dict(before=prev, after=row, is_action_step=is_act,
                                                  branch="already_stopped",
                                                  classification="Exact Observable",
                                                  reason="rest_to_rest_zero_displacement",
                                                  candidate_u=None, actual_dx_m=dx,
                                                  old_trapezoid_dx_m=0.0,
                                                  expected_dx_m=0.0, residual_m=dx,
                                                  exact_evaluable=True, exact_pass=abs(dx) <= 1e-6))
                                previous[vid] = row
                                continue
                            recon = reconstruct_signed_vnext(v0, a_pub_start, h, is_action=is_act, v1=v1)
                            if v0 > 0 and v1 == 0:
                                branch = "terminal_stop"
                            elif v0 == 0:
                                branch = "starting_from_rest"
                            elif 0 < v1 < v0:
                                branch = "decelerating_without_stop"
                            else:
                                branch = "normal_motion"
                            edge = dict(before=prev, after=row, is_action_step=is_act, branch=branch,
                                        classification=recon["classification"], reason=recon["reason"],
                                        candidate_u=recon["candidate"], actual_dx_m=dx,
                                        old_trapezoid_dx_m=.5 * (v0 + v1) * h)
                            if recon["candidate"] is not None:
                                u = recon["candidate"]
                                # cross-check: reported terminal speed must equal max(u,0)
                                v1_consistent = abs(max(u, 0.0) - v1) <= 1e-9
                                exp = expected_displacement(v0, u, h)
                                resid = dx - exp
                                edge.update(expected_dx_m=exp, residual_m=resid,
                                            v1_consistency=v1_consistent,
                                            exact_evaluable=v1_consistent,
                                            exact_pass=(abs(resid) <= 1e-6) and v1_consistent,
                                            exact_u_ge_0=u >= 0)
                            else:
                                # bounded consistency only for a clamped decision stop
                                upper = .5 * v0 * h
                                viol = max(0., -dx, dx - upper)
                                edge.update(dx_bounds_m=[0., upper], bound_violation_m=viol,
                                            exact_evaluable=False,
                                            exact_pass=None,
                                            within_bounds=viol <= 1e-6)
                            edges.append(edge)
                    previous[vid] = row
        except Exception as exc:
            failure = f"{type(exc).__name__}: {exc}"
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
    # aggregate per classification / branch
    branches = {}
    exact_checked = exact_passed = 0
    bounded = not_evaluable = 0
    max_resid = None
    anomalies = 0
    for e in edges:
        b = e["branch"]
        s = branches.setdefault(b, dict(count=0, exact=0, exact_pass=0, bounded=0, not_evaluable=0,
                                        max_abs_residual_m=None, anomalies=0))
        s["count"] += 1
        if e.get("exact_evaluable"):
            exact_checked += 1
            s["exact"] += 1
            ar = abs(e["residual_m"])
            s["max_abs_residual_m"] = ar if s["max_abs_residual_m"] is None else max(s["max_abs_residual_m"], ar)
            max_resid = ar if max_resid is None else max(max_resid, ar)
            if e["exact_pass"]:
                exact_passed += 1
                s["exact_pass"] += 1
            else:
                s["anomalies"] += 1
                anomalies += 1
        elif e["classification"] == "Bounded Consistency Only":
            bounded += 1
            s["bounded"] += 1
            if not e.get("within_bounds", True):
                s["anomalies"] += 1
                anomalies += 1
        else:
            not_evaluable += 1
            s["not_evaluable"] += 1
    blockers = [failure] if failure else []
    # a reconstruction anomaly is an engineering blocker
    if anomalies:
        blockers.append(f"{anomalies} exact/bound anomalies")
    write(out / "summary.json", dict(run_id=run_id, engineering_blockers=blockers,
        status="failed" if failure else ("completed_with_anomaly" if anomalies else "completed_valid"),
        edges=len(edges), exact_checked=exact_checked, exact_passed=exact_passed,
        bounded_consistency_only=bounded, not_evaluable=not_evaluable,
        max_abs_residual_m=max_resid, anomalies=anomalies, branches=branches,
        runtime_settings=settings, observed_states=observations, vehicles=len(departed), arrived=len(arrived),
        collisions=list(collision), teleports=list(teleports), numerical_tolerance_m=1e-6,
        no_debug_binary=True, no_P2_calculation=True, scientific_claim_eligible=False,
        plan_sha256=sha(batch / "experiment_plan.json")))


def run(batch):
    from riskprop.stage_0_5_boundary_bottleneck import execute_commands
    plan = read_plan(batch)
    ledger = json.loads((batch / "execution_ledger.json").read_text())
    if ledger["closed"] or any(r["status"] != "not_attempted" for r in ledger["runs"]):
        raise PermissionError("no reopening observability batch")
    commands = [dict(run_id=r["run_id"],
                     verify_files={str(batch / n): plan["frozen_files"][n] for n in [r["config"], r["network"], r["demand"]]},
                     command=[sys.executable, "-S", str(Path(__file__)), "worker", "--batch", str(batch),
                              "--run-id", r["run_id"]]) for r in plan["runs"]]
    environment(batch)
    started = time.time()
    result = execute_commands(batch / "runs", commands, limits=plan["limits"])
    write(batch / "execution_ledger.json", dict(plan_sha256=sha(batch / "experiment_plan.json"), closed=True,
                                                runs=result["runs"],
                                                stop_reason=result["stop_reason"] or "all declared observability runs completed",
                                                elapsed_wall_s=time.time() - started))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["prepare", "tests", "freeze", "run", "worker", "finalize"])
    p.add_argument("--batch", type=Path, required=True)
    p.add_argument("--run-id")
    a = p.parse_args()
    batch = a.batch.resolve()
    audit = None
    if a.command != "prepare":
        if not Path(__file__).resolve().is_relative_to(batch / "runtime"):
            raise PermissionError("use capsule entrypoint")
        from riskprop.stage_0_5_b1_isolation import install_guard
        audit = install_guard(batch)
    try:
        if a.command == "prepare":
            prepare(batch)
        elif a.command == "tests":
            tests(batch)
        elif a.command == "freeze":
            freeze(batch)
        elif a.command == "run":
            run(batch)
        elif a.command == "worker":
            worker(batch, a.run_id)
        else:
            import importlib.util
            analysis = batch / "runtime/code/scripts/stage_0_5_observability_analysis.py"
            spec = importlib.util.spec_from_file_location("b11s_analysis", analysis)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.finalize(batch)
    finally:
        if audit is not None:
            folder = batch / "access_logs"
            folder.mkdir(exist_ok=True)
            write(folder / f"{a.command}_{a.run_id or time.time_ns()}.json", audit)
            if audit["denied"]:
                raise PermissionError("unexpected capsule denial")
