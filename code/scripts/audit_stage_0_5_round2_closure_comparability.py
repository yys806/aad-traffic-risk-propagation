"""Bounded Round2 closure audit: synthetic interfaces, never trajectories or SUMO.

Historical Task2 generators are imported only for their in-memory fixtures.
No historical generator main, calibration data reader, or native runner is called.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "code/src"), str(ROOT / "code/scripts")]
from riskprop.stage_0_5_sumo import (build_sumo_p2_events, extract_sumo_formal_p2_events,
    build_sumo_formal_source_frame, compute_sumo_measurements)
from riskprop.stage_0_5_d1_measurement import local_d1_measurement
import audit_stage_0_5_round2_task2_measurement_contract as task2

RESULT_ID = "RES-AAD-ROUND2-CLOSURE-COMPARABILITY-20261030"
LOCAL = ROOT / "code/outputs/formal/calibration/round2_closure_comparability_20261030"
PACKAGE = ROOT / "evidence/results" / RESULT_ID
TEST_FILES = ["code/tests/test_stage_0_5_round2_closure_comparability.py",
    "code/tests/test_formal_risk_measurement.py",
    "code/tests/test_stage_0_5_measurement_equivalence.py",
    "code/tests/test_stage_0_5_d1_measurement.py",
    "code/tests/test_stage_0_5_post_r2_offline_diagnostic.py"]
PARQUET_BLOCKED = [
    "code/tests/test_stage_0_5_measurement_equivalence.py::test_guard_denies_row_scoped_reads_outside_the_calibration_windows",
    "code/tests/test_stage_0_5_measurement_equivalence.py::test_calibration_states_read_helper_refuses_a_foreign_window",
    "code/tests/test_stage_0_5_d1_measurement.py::test_actual_state_runner_uses_d1_not_point_exposure"]
SOURCES = ["code/src/riskprop/formal_risk_measurement.py",
    "code/src/riskprop/ngsim_risk_calibration.py", "code/src/riskprop/real_trajectory.py",
    "code/src/riskprop/stage_0_5_sumo.py", "code/src/riskprop/stage_0_5_d1_measurement.py",
    "code/configs/stage_0_2_formal_risk_measurement_p2_v1.json",
    "code/scripts/audit_stage_0_5_round2_task2_measurement_contract.py",
    "code/scripts/align_stage_0_5_round2_task3_measurement_contract.py",
    "code/scripts/audit_stage_0_5_round2_closure_comparability.py", *TEST_FILES]
HISTORY = ["RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029",
    "RES-STAGE-0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029",
    "RES-STAGE-0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030",
    "RES-STAGE-0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-20261030",
    "RES-STAGE-0.5-ROUND2-TASK6-REAL-SIM-MICRO-INTERACTION-20261030",
    "RES-STAGE-0.5-ROUND2-TASK7-INDEPENDENT-PHYSICAL-QUALITY-REVIEW-20261030",
    "RES-STAGE-0.5-ROUND2-TASK7.1-VIDEO-METADATA-AND-MAPPING-FEASIBILITY-20261030",
    "RES-STAGE-0.5-ROUND2-TASK7.2-RESOURCE-METADATA-AND-ACQUISITION-FEASIBILITY-20261030"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(task2._jsonable(value), ensure_ascii=False,
        sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def events(frame):
    columns = ["vehicle_id", "leader_id", "trajectory_id", "leader_trajectory_id",
        "event_start_s", "event_confirm_s", "event_end_s", "raw_frame_count", "exit_reason"]
    return task2.select_events(frame, tuple(columns))


def probe_frame(name):
    case = {"times": [round(i * .1, 10) for i in range(7)], "specs": [task2.spec() for _ in range(7)]}
    _, measured = task2.build_case_frame(case, "closure_" + name)
    # Supply coherent source-domain clock fields on every row before perturbing them.
    measured["frame_id"] = measured.groupby("incarnation_id", sort=False).cumcount()
    measured["global_time_ms"] = (measured.time_s * 1000).round().astype("int64")
    mask = measured.vehicle_id.eq("f")
    at = mask & measured.time_s.eq(.2)
    if name in {"identity_break", "observation_gap"}:
        measured.loc[at, name] = True
    elif name == "source_frame_discontinuity":
        measured.loc[mask & measured.time_s.ge(.2), "frame_id"] += 1
    elif name == "source_clock_discontinuity":
        measured.loc[mask & measured.time_s.ge(.2), "global_time_ms"] += 100
    elif name == "missing_leader_self_rows":
        measured = measured.loc[mask].copy()
    elif name == "unknown_flag":
        measured["observation_gap"] = measured.observation_gap.astype(object)
        measured.loc[at, "observation_gap"] = None
    elif name == "negative_ttc_premeasured":
        measured.loc[mask, "ttc_s"] = -1.
    elif name == "normal":
        pass
    else:
        raise ValueError("undeclared probe:" + name)
    return measured


def evaluate_probe(name):
    measured = probe_frame(name)
    row = {"case": name, "inputs": task2.select_events(measured.loc[measured.vehicle_id.eq("f")],
        ("vehicle_id", "leader_id", "incarnation_id", "leader_incarnation_id", "time_s",
         "frame_id", "global_time_ms", "identity_break", "observation_gap", "ttc_s", "ttc_valid"))}
    for label, function in [
        ("native", lambda: events(build_sumo_p2_events(measured, recorded_observation_step_s=.1)[0])),
        ("formal_aligned", lambda: events(extract_sumo_formal_p2_events(measured, recorded_observation_step_s=.1)[0])),
        ("D1", lambda: local_d1_measurement(measured, (0., 1.), strict=True))]:
        try:
            row[label] = {"result": function(), "error": None}
        except Exception as exc:
            row[label] = {"result": None, "error": f"{type(exc).__name__}: {exc}"}
    if name != "unknown_flag":
        mapped = build_sumo_formal_source_frame(measured, recorded_observation_step_s=.1)
        row["mapped_follower_clock"] = task2.select_events(mapped.loc[mapped.vehicle_id.eq("f")],
            ("time_s", "frame_id", "global_time_ms", "identity_break", "observation_gap"))
    return row


PROBES = ("normal", "identity_break", "observation_gap", "source_frame_discontinuity",
    "source_clock_discontinuity", "missing_leader_self_rows", "unknown_flag", "negative_ttc_premeasured")


def comparability_matrix():
    rows = [
        ("Event qualification", "Verified", "C pair/time qualification is already implemented; lane changes alone do not disqualify a general P2 event.",
         "formal_risk_measurement.extract_formal_source_events; stage_0_5_sumo.build_sumo_p2_events/extract_sumo_formal_p2_events",
         "Task2 native_lane_id_change_no_connection, real_lane_change, threshold and duration cases",
         "Only declared valid, identity-resolved, continuous 100 ms inputs share event semantics; flag endpoints and corrupt premeasured inputs differ."),
        ("Identity", "Verified", "Scoped follower/leader incarnation and formal trajectory identities; no physical identity certification.",
         "formal_risk_measurement.PAIR_KEYS/continuity_is_valid; stage_0_5_sumo.following_link_is_valid/build_sumo_formal_source_frame",
         "Task2 leader_switch/incarnation_change; missing_leader_self_rows probe",
         "Native/D1 accept externally resolved leader labels without self rows; formal alignment needs leader frame evidence. Actual physical identities remain Unknown."),
        ("Continuity", "Unknown", "Explicit flags survive alignment, but native/D1 test both endpoints while formal continuity tests the current flag.",
         "formal_risk_measurement.continuity_is_valid; stage_0_5_sumo.following_link_is_valid; stage_0_5_d1_measurement.local_d1_measurement",
         "identity_break and observation_gap probes at 0.2 s",
         "Same count, different onset/confirmation/membership: native/D1 0.3/0.5/4 versus formal 0.2/0.4/5. No semantic repair is authorized here."),
        ("Time", "Unknown", "NGSIM raw row/frame/anchor and simulator-derived observation/frame/clock are different support domains.",
         "formal_risk_measurement.continuity_is_valid; stage_0_5_sumo.build_sumo_formal_source_frame",
         "source_frame_discontinuity/source_clock_discontinuity; existing late_entry_absolute_clock and coarse cadence cases",
         "Formal projection regenerates frame/clock from time_s and cannot certify supplied raw clocks. Cross-source absolute origins/video PTS mappings remain Unknown."),
        ("Lane/path", "Unknown", "C and D1 are separate. B physical paths require trackable pair identities, timed lane/edge observations, interaction continuity, physical road connection and ordered transitions.",
         "formal_risk_measurement.PAIR_KEYS; stage_0_5_d1_measurement.local_d1_measurement; Task7.1/7.2 mapping evidence",
         "Task2 lane change with and without road_connection_witness",
         "A lane token, topology or a synthetic boolean witness cannot establish real traveled paths. No independently verified physical path/arrival is available."),
        ("Measurement", "Verified", "Valid positive gap/closing inputs use TTC=gap/closing, 0<TTC<2 s, observed span>=0.2 s, 100 ms cadence.",
         "real_trajectory.add_ngsim_leader_ttc; stage_0_5_sumo.compute_sumo_measurements/_risk_mask; formal_risk_measurement.observed_confirmation_time",
         "Task2 threshold/duration boundary cases and negative_ttc_premeasured probe",
         "Native mask trusts ttc_valid and accepts contradictory negative premeasured TTC; formal raises and D1 excludes it. Verified common algebra is not physical measurement equivalence."),
        ("Exposure", "Verified", "D1 local onset and same-native-lane evaluable links are separate from general Formal P2 events/exposure.",
         "stage_0_5_d1_measurement.local_d1_measurement; stage_0_5_sumo.compute_exposure; Task4/5 attribution evidence",
         "Task2 lane changes and window_boundary_onset_outside; existing D1 boundary tests",
         "Never divide C event counts by a D1 denominator. Historical NGSIM source 167/159 and sealed SUMO source 0/0 remain separately attributed."),
        ("Missingness", "Unknown", "Unknown identity, missing observations and not-applicable non-closing/no-leader states are retained, never imputed as safe/zero.",
         "real_trajectory.add_ngsim_leader_ttc; stage_0_5_sumo.compute_sumo_measurements/build_sumo_formal_source_frame; stage_0_5_d1_measurement.local_d1_measurement",
         "Task2 no_leader_boundary_missing; unknown_flag/missing_leader_self_rows probes",
         "Unknown booleans are rejected by formal/D1; native truthiness and deterministic absent-field defaults differ. NGSIM boundary missing and simulator no-leader support are not the same observation."),
    ]
    return {"schema_version": "aad.round2.closure.comparability.v1", "formal_equivalence_accepted": False,
        "scientific_equivalence_status": "Unknown", "rows": [dict(zip(
            ("dimension", "final_status", "current_implementation", "source_functions", "counterexamples", "limits"), row)) for row in rows],
        "status_meaning": "Verified describes only the stated implementation/interface scope, never scientific equivalence; Unknown describes unresolved comparability or physical support."}


def historical_integrity():
    records = []
    for result_id in HISTORY:
        package = ROOT / "evidence/results" / result_id
        sums = package / "SHA256SUMS"
        checked, errors = 0, []
        if not sums.is_file():
            records.append({"result_id": result_id, "status": "Unknown", "reason": "No SHA256SUMS present"})
            continue
        for line in sums.read_text(encoding="utf-8-sig").splitlines():
            expected, name = line.split("  ", 1)
            target = (package / name).resolve()
            if not target.is_relative_to(package.resolve()):
                errors.append("path_outside_package:" + name)
            elif not target.is_file() or digest(target) != expected:
                errors.append(name)
            checked += 1
        records.append({"result_id": result_id, "sha256sums_sha256": digest(sums),
            "files_checked": checked, "status": "Passed" if not errors else "Failed", "errors": errors})
    return records


def package_files():
    payload = sorted(p for p in PACKAGE.iterdir() if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"})
    write_json(PACKAGE / "manifest.json", {"schema_version": "aad.evidence-manifest.v1", "result_id": RESULT_ID,
        "self_reference": False, "payload_files": {p.name: digest(p) for p in payload}})
    (PACKAGE / "SHA256SUMS").write_text("".join(f"{digest(p)}  {p.name}\n" for p in sorted(PACKAGE.iterdir())
        if p.is_file() and p.name != "SHA256SUMS"), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--exclude-known-parquet-tests", action="store_true",
        help="Precisely deselect three independently observed historical missing-Parquet failures; never report them passed")
    args = parser.parse_args()
    LOCAL.mkdir(parents=True, exist_ok=True)
    PACKAGE.mkdir(parents=True, exist_ok=True)
    before_history = historical_integrity()
    inputs, outputs = task2.run_cases()
    probes = [evaluate_probe(name) for name in PROBES]
    for name, value in [("synthetic_case_inputs.json", inputs), ("synthetic_case_results.json", outputs),
        ("additional_probes.json", probes), ("comparability_matrix.json", comparability_matrix())]:
        write_json(PACKAGE / name, value)
    tests = {"status": "Not Run", "command": None}
    attempts_path = PACKAGE / "test_attempts.json"
    attempts = json.loads(attempts_path.read_text(encoding="utf-8")) if attempts_path.is_file() else []
    prior_validation = PACKAGE / "validation_record.json"
    if not attempts and prior_validation.is_file():
        prior = json.loads(prior_validation.read_text(encoding="utf-8"))["tests"]
        if prior.get("command"):
            attempts.append(prior)
    if args.run_tests:
        command = [sys.executable, "-m", "pytest", "-q", "-c", "code/pyproject.toml", *TEST_FILES,
            "-p", "no:cacheprovider", "--basetemp", str(LOCAL / ("pytest_tmp_" + str(len(attempts) + 1)))]
        if args.exclude_known_parquet_tests:
            # Windows node IDs can contain backslashes. Unique test names avoid
            # silently failing to match a POSIX-style --deselect path.
            command.extend(["-k", " and ".join("not " + node.split("::")[-1] for node in PARQUET_BLOCKED)])
        result = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True)
        log = LOCAL / ("pytest_stdout_attempt_" + str(len(attempts) + 1) + ".txt")
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        tests = {"status": "Passed" if result.returncode == 0 else "Failed", "command": command,
            "exit_code": result.returncode, "summary": result.stdout.strip().splitlines()[-1:] or result.stderr.strip().splitlines()[-1:],
            "local_log": str(log.relative_to(ROOT)), "raw_log_in_portable_evidence": False,
            "blocked_not_passed": PARQUET_BLOCKED if args.exclude_known_parquet_tests else [],
            "blocked_reason": "Historical tests require pyarrow/fastparquet, unavailable in this interpreter" if args.exclude_known_parquet_tests else None}
        attempts.append(tests)
    write_json(attempts_path, attempts)
    syntax_errors = []
    for source in ["code/scripts/audit_stage_0_5_round2_closure_comparability.py", TEST_FILES[0]]:
        try:
            ast.parse((ROOT / source).read_text(encoding="utf-8-sig"), filename=source)
        except SyntaxError as exc:
            syntax_errors.append(str(exc))
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).splitlines()
    write_json(PACKAGE / "source_bindings.json", {"git_head": head, "worktree_status_at_execution": dirty,
        "files_sha256": {name: digest(ROOT / name) for name in SOURCES}, "historical_evidence": before_history})
    after_history = historical_integrity()
    write_json(PACKAGE / "validation_record.json", {"schema_version": "aad.round2.closure.validation.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "environment": {"python": sys.version,
            "executable": sys.executable, "platform": platform.platform(), "pandas": pd.__version__, "numpy": np.__version__},
        "command": [sys.executable, str(Path(__file__).relative_to(ROOT)), *sys.argv[1:]],
        "tests": tests, "syntax": {"status": "Passed" if not syntax_errors else "Failed", "errors": syntax_errors},
        "task2_synthetic_cases": len(outputs), "additional_probes": len(probes),
        "historical_evidence_unchanged": before_history == after_history, "historical_integrity": after_history,
        "seed": "Not Applicable: deterministic synthetic fixtures, not randomized experiments", "repetitions": 1,
        "native_launches": 0, "traci_connections": 0, "new_trajectory_reads": 0, "locked_holdout_reads": 0,
        "scientific_equivalence_accepted": False, "production_source_changed": False})
    package_files()
    print(json.dumps({"result_id": RESULT_ID, "tests": tests, "synthetic_cases": len(outputs), "additional_probes": len(probes),
        "history_unchanged": before_history == after_history, "history_failures": [r for r in after_history if r["status"] == "Failed"]}))
    return int(tests["status"] == "Failed" or bool(syntax_errors) or before_history != after_history)


if __name__ == "__main__":
    raise SystemExit(main())
