"""Zero-launch Round2 Task1 remeasurement and paired offline comparison.

This tool consumes the one sealed Round2 candidate capsule after the native
attempt has finished.  It repairs only the post-run capability-record path
binding, reuses ``measure_completed_capsule`` and the existing state/D1 code,
and never starts SUMO/TraCI.  The original ledger rejection is preserved in
the assessment record; the repaired result is a separate, immutable
zero-launch assessment.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
sys.path.insert(0, str(ROOT / "code" / "scripts"))

from riskprop.stage_0_5_d1_measurement import local_d1_measurement, offset100_cloud
from riskprop import stage_0_5_state_support as state_support
from stage_0_5_execution_v2 import measure_completed_capsule
from stage_0_5_isolation_v2 import Scope
from stage_0_5_native_capsule_v4 import canonical, sha, require
from stage_0_5_research_ledger import CHECKS
from analyze_stage_0_5_offline_mechanism import finite_summary, classify_event


TASK = "AAD-S0.5-ROUND2-TASK1"
RUN_ID = "AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1"
BASE_RUN_ID = "WEEK_0750_B00_IC1_s20261201_A03"
WINDOW = (120.0, 390.0)
SOURCE = (0.0, 150.0)
TARGET = (150.0, 350.0)
LANES = {"1", "2", "3", "4", "5"}
REAL_DOMAIN = Path("code/outputs/formal/calibration/stage_0_5_state_support_v1/real_domain.json")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def route_inventory(path: Path) -> tuple[dict[str, list[str]], dict[str, ET.Element], list[str]]:
    root = ET.fromstring(path.read_bytes())
    routes = {node.get("id"): node.get("edges", "").split()
              for node in root.findall("route")}
    vehicles = {node.get("id"): node for node in root.findall("vehicle")}
    cohort = sorted(
        ident for ident, node in vehicles.items()
        if any(edge in {"main_0", "main_1"} for edge in routes.get(node.get("route"), []))
    )
    return routes, vehicles, cohort


def _link_or_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def _sealed_hashes(work: Path) -> dict[str, str]:
    names = ["fcd.xml", "summary.xml", "tripinfo.xml", "identity_events.jsonl",
             "identity_summary.json"]
    return {name: sha(work / name) for name in names}


def _coordinator_acceptance(work: Path) -> dict:
    data = json.loads((work / "coordinator.stdout").read_bytes())
    accepted = data.get("acceptance")
    require(data.get("status") == "Pass" and isinstance(accepted, dict),
            "native_coordinator_acceptance_missing")
    require(accepted.get("status") == "Pass", "native_coordinator_acceptance_failed")
    return accepted


def offline_remeasure(root: Path, proposal_rel: str, output_rel: str,
                      package_rel: str) -> dict:
    """Re-run the existing assessor against hard-linked sealed artifacts."""
    root = root.resolve()
    proposal_path = root / proposal_rel
    proposal = json.loads(proposal_path.read_bytes())
    require(proposal.get("experiment_id") == TASK, "wrong_round2_experiment")
    run = next(r for r in proposal["runs"] if r.get("id") == RUN_ID)
    source_work = root / run["artifact_path"]
    require(source_work.is_dir(), "sealed_candidate_output_missing")
    isolation = json.loads((source_work / "isolation_runtime.json").read_bytes())
    controller = json.loads((source_work / "controller_receipt.json").read_bytes())
    require(isolation.get("payload_exit_code") == controller.get("exit_code") == 0,
            "completed_native_run_required")
    raw_names = ["fcd.xml", "summary.xml", "tripinfo.xml", "identity_events.jsonl",
                 "identity_summary.json", "network.net.xml", "routes.rou.xml", "run.sumocfg"]
    for name in raw_names:
        require((source_work / name).is_file(), "sealed_artifact_missing:" + name)
    for name, expected in isolation.get("artifact_sha256", {}).items():
        if (source_work / name).is_file():
            require(sha(source_work / name) == expected, "sealed_artifact_hash_drift:" + name)
    capability = source_work / "capability_record.json"
    require(capability.is_file(), "capability_record_missing")

    output = root / output_rel
    candidate_package = root / package_rel
    if output.exists():
        # A failed wrapper attempt may have emitted only derived files before
        # its final export step.  Reuse that exact partial directory after the
        # failure has been recorded; refuse any unexpected content.
        allowed_partial = {"D1_measurement.json", "common_support_v3.json",
                           "state_support_cloud.csv", "measured_state.parquet"}
        require(output.is_dir() and {p.name for p in output.iterdir()} <= allowed_partial,
                "offline_assessment_output_exists")
    else:
        output.mkdir(parents=True)
    require(not candidate_package.exists(), "offline_assessment_package_exists")
    candidate_package.mkdir(parents=True)
    write_json(candidate_package / "parent_run.json", {
        "schema": "aad.stage05.round2.task1.offline-remeasurement-parent.v1",
        "task": TASK, "run_id": RUN_ID,
        "parent_proposal_path": proposal_rel,
        "parent_proposal_sha256": sha(proposal_path),
        "prior_ledger_status": "measurement_rejected",
        "native_launches": 0,
        "reason": "repair capability_evidence_path binding only; raw capsule unchanged",
    })
    _link_or_copy(capability, output / "capability_record.json")
    capability_rel = (output / "capability_record.json").relative_to(root).as_posix()

    temp = root / "code" / "tmp" / "stage05_round2_task1_offline_assessment_work"
    require(not temp.exists(), "offline_assessment_work_exists")
    temp.mkdir(parents=True)
    try:
        for name in raw_names:
            _link_or_copy(source_work / name, temp / name)
        # The current production assessor's output root is the work directory;
        # hard links keep the sealed trajectory immutable without another copy.
        p_eval = copy.deepcopy(proposal)
        p_eval["isolation"] = copy.deepcopy(proposal["isolation"])
        p_eval["isolation"]["capability_evidence_path"] = capability_rel
        p_eval["isolation"]["capability_evidence_sha256"] = sha(output / "capability_record.json")
        source_bindings = {root / name: value for name, value in proposal["source_sha256"].items()}
        scope = Scope(root, source_bindings, temp)
        for name, digest in proposal.get("measurement_reference_sha256", {}).items():
            scope.bindings[root / name] = digest
        accepted = _coordinator_acceptance(source_work)
        runtime_evidence = {
            "resource_samples": controller["resource_samples"],
            "run_finished_wall_s": controller["resource_samples"][-1]["wall_s"],
            "exit_code": controller["exit_code"],
            "watchdog_failure": controller.get("watchdog_failure"),
            "sealed_artifacts": _sealed_hashes(temp),
            "isolation": {
                "kind": "OS_enforced", "backend": "linux-userns",
                "binding_sha256": sha(proposal_path),
                "transcript_sha256": accepted["receipt_sha256"],
                "probes": accepted["probes"],
            },
        }
        context = dict(
            work=temp, scope=scope, run=run, proposal=p_eval,
            validated_inputs={name: (temp / name).read_bytes()
                              for name in run["input_files"]},
            resource_limits=proposal["single_attempt_limits"],
            runtime_evidence=runtime_evidence,
            binding_sha256=sha(proposal_path),
            native_enforcement_verified=True,
            isolation_transcript_sha256=[accepted["receipt_sha256"]],
        )
        identity = json.loads((temp / "identity_summary.json").read_bytes())
        result = measure_completed_capsule(context, identity)
        # The execution adapter normally writes this file after the assessor;
        # this zero-launch path writes the same assessor result explicitly.
        write_json(temp / "measurement_acceptance.json", result)
        for name in ["D1_measurement.json", "common_support_v3.json",
                     "state_support_cloud.csv", "measured_state.parquet",
                     "measurement_acceptance.json"]:
            _link_or_copy(temp / name, output / name)
        assessment = {
            "schema": "aad.stage05.round2.task1.offline-remeasurement.v1",
            "status": "ROUND2_EXECUTED_MEASUREMENT_ACCEPTED" if all(result.get(k) is True for k in CHECKS)
                      else "ROUND2_EXECUTED_MEASUREMENT_LIMITED",
            "task": TASK, "run_id": RUN_ID, "native_launches": 0,
            "trajectory_source": "existing sealed candidate output; raw artifacts unchanged",
            "parent_proposal_sha256": sha(proposal_path),
            "measurement_sha256": sha(output / "measurement_acceptance.json"),
            "capability_record_sha256": sha(output / "capability_record.json"),
            "prior_ledger_status_preserved": "measurement_rejected",
            "checks": {k: result.get(k) for k in CHECKS},
            "repair": {
                "field": "isolation.capability_evidence_path",
                "old_value": proposal["isolation"].get("capability_evidence_path"),
                "new_value": capability_rel,
                "scientific_inputs_changed": False,
                "new_sumo_or_traci_launches": 0,
            },
        }
        write_json(output / "assessment_result.json", assessment)
        write_json(output / "independent_execution_receipt.json", {
            "schema": "aad.stage05.round2.task1.zero-launch-receipt.v1",
            "status": accepted["status"], "kind": accepted["kind"],
            "backend": accepted["backend"], "proposal_sha256": sha(proposal_path),
            "receipt_sha256": accepted["receipt_sha256"],
            "controller_sha256": accepted["controller_sha256"],
            "runtime_manifest_sha256": accepted["runtime_manifest_sha256"],
            "probes": accepted["probes"], "native_launches": 0,
            "raw_artifacts": _sealed_hashes(source_work),
        })
        return assessment
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def _summary(frame: pd.DataFrame) -> dict:
    return {
        "states": int(len(frame)),
        "vehicles": int(frame.vehicle_id.nunique()),
        "speed_mps": finite_summary(frame.speed_mps),
        "speed_sd_mps": float(frame.speed_mps.std(ddof=1)) if len(frame) > 1 else None,
        "low_speed_share": float(frame.speed_mps.lt(5).mean()) if len(frame) else None,
        "closing_speed_mps": finite_summary(frame.closing_speed_mps),
        "closing_negative_share": float(frame.closing_speed_mps.lt(0).mean()) if len(frame) else None,
        "net_gap_m": finite_summary(frame.net_gap_m),
    }


def _segments_all(frame: pd.DataFrame) -> list[dict]:
    """Exploratory risk segments without the formal lane-region restriction."""
    d = frame[frame.time_s.ge(WINDOW[0]) & frame.time_s.lt(WINDOW[1])].copy()
    d = d[d.reliable_following_eligible.astype(bool) & d.ttc_valid.astype(bool)
          & d.measurement_status.eq("valid") & d.ttc_s.gt(0) & d.ttc_s.lt(2)]
    if d.empty:
        return []
    keys = ["vehicle_id", "incarnation_id", "leader_id", "leader_incarnation_id"]
    d = d.sort_values(keys + ["time_s"], kind="stable")
    result: list[dict] = []
    for key, group in d.groupby(keys, dropna=False, sort=False):
        rows = group.to_dict("records")
        current = [rows[0]]
        for row in rows[1:]:
            if abs(float(row["time_s"]) - float(current[-1]["time_s"]) - .1) <= 1e-7:
                current.append(row)
            else:
                result.append(_segment(current, key))
                current = [row]
        result.append(_segment(current, key))
    return result


def _segment(rows: list[dict], key: tuple) -> dict:
    first, last = rows[0], rows[-1]
    native = first.get("native_lane_id")
    edge = str(native).rsplit("_", 1)[0] if native and "_" in str(native) else None
    y = float(first["y_m"])
    spatial = ("source_upstream_main" if edge == "main_0" and 0 <= y < 150 else
               "target_main" if edge in {"main_0", "main_1"} and 150 <= y < 350 else
               "other_mainline" if edge in {"main_0", "main_1"} else
               "auxiliary_or_other_edge")
    return {
        "vehicle_id": str(key[0]),
        "leader_id": None if pd.isna(key[2]) else str(key[2]),
        "onset_s": float(first["time_s"]), "end_s": float(last["time_s"]),
        "span_s": float(last["time_s"] - first["time_s"]), "members": len(rows),
        "qualifies_duration": bool(float(last["time_s"] - first["time_s"]) >= .2 - 1e-9),
        "onset_y_m": y, "onset_native_lane": None if pd.isna(native) else str(native),
        "spatial_class": spatial,
    }


def _formal(frame: pd.DataFrame, cohort: set[str]) -> dict:
    cohort_frame = frame[frame.vehicle_id.astype(str).isin(cohort)]
    source = local_d1_measurement(frame, WINDOW, region=SOURCE, strict=True)
    target_all = local_d1_measurement(frame, WINDOW, region=TARGET, strict=True)
    target_cohort = local_d1_measurement(cohort_frame, WINDOW, region=TARGET, strict=True)
    return {
        "source_all": source, "target_all": target_all,
        "target_cohort": target_cohort,
        "source_events_classified": [classify_event(frame, e) for e in source["events"]],
        "target_events_classified": [classify_event(frame, e) for e in target_cohort["events"]],
        "exploratory_all_segments": _segments_all(frame),
    }


def _macro_rule_a(frame: pd.DataFrame) -> dict:
    real = json.loads((ROOT / REAL_DOMAIN).read_bytes())
    local = frame[frame.time_s.ge(WINDOW[0]) & frame.time_s.lt(WINDOW[1]) &
                  frame.lane_id.astype(str).isin(LANES) & frame.y_m.ge(TARGET[0]) &
                  frame.y_m.lt(TARGET[1])]
    cloud = offset100_cloud(frame, WINDOW)
    if cloud.empty or local.empty:
        return {"status": "INSUFFICIENT_EVIDENCE", "reason": "empty_target_or_block_support"}
    rows = []
    for _, row in cloud.iterrows():
        speed = state_support.envelope_membership(
            float(row.density_veh_km_lane), float(row.speed_mean_mps), real["pooled_envelope"])
        closing = state_support.closing_membership(
            float(row.density_veh_km_lane), float(row.closing_speed_mean_mps),
            real["pooled_closing_envelope"])
        rows.append({
            "t_block": int(row.t_block), "y_block": int(row.y_block),
            "states": int(row.states), "density_veh_km_lane": float(row.density_veh_km_lane),
            "speed_mean_mps": float(row.speed_mean_mps),
            "closing_speed_mean_mps": float(row.closing_speed_mean_mps),
            "low_speed_share": float(row.low_speed_share),
            "speed_inside_pooled_envelope": bool(speed["inside"]),
            "closing_inside_pooled_envelope": bool(closing["inside"]),
            "speed_bounds": {"lower": speed.get("speed_lower_mps"),
                             "upper": speed.get("speed_upper_mps")},
            "closing_bounds": {"lower": closing.get("closing_lower_mps"),
                               "upper": closing.get("closing_upper_mps")},
        })
    baseline = float(real["cross_window_baseline_coverage_min"])
    speed_cov = float(np.mean([r["speed_inside_pooled_envelope"] for r in rows]))
    closing_cov = float(np.mean([r["closing_inside_pooled_envelope"] for r in rows]))
    mean_density = len(local) * .1 / ((WINDOW[1] - WINDOW[0]) * 1.0)
    mean_speed = float(local.speed_mps.mean())
    mean_member = state_support.envelope_membership(mean_density, mean_speed, real["pooled_envelope"])
    low_max = max(float(x["low_speed_share"]) for x in rows)
    insufficient = any(r["states"] < 10 for r in rows)
    status = "INSUFFICIENT_EVIDENCE" if insufficient else (
        "PASS" if mean_member["inside"] and speed_cov >= baseline and closing_cov >= baseline else "FAIL")
    return {
        "status": status,
        "rule": "Rule A strict joint support",
        "definition": "mean state inside pooled density-speed envelope AND pooled block speed coverage >= existing cross-window baseline AND pooled closing coverage >= same baseline",
        "baseline_coverage": baseline,
        "mean_state": {"density_veh_km_lane": mean_density, "speed_mean_mps": mean_speed,
                       "inside_pooled_envelope": bool(mean_member["inside"]),
                       "speed_bounds": {"lower": mean_member.get("speed_lower_mps"),
                                        "upper": mean_member.get("speed_upper_mps")}},
        "block_count": len(rows), "speed_block_coverage": speed_cov,
        "closing_block_coverage": closing_cov,
        "real_low_speed_share_max": low_max,
        "target_summary": _summary(local),
        "blocks": rows,
        "threshold_status": "existing evidence baseline; no new delta/h/B",
    }


def compare(root: Path, candidate_output: Path, comparison_output: Path) -> dict:
    routes_path = root / "evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/inputs/routes.rou.xml"
    _, _, cohort_ids = route_inventory(routes_path)
    require(len(cohort_ids) == 1112, "cohort_count_drift")
    candidate = pd.read_parquet(candidate_output / "measured_state.parquet")
    baseline_path = root / "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs" / BASE_RUN_ID / "measured_state.parquet"
    baseline = pd.read_parquet(baseline_path)
    records = {}
    for label, frame in [("B00_A03", baseline), ("Round2_minGap1.0", candidate)]:
        formal = _formal(frame, set(cohort_ids))
        micro_frame = frame[frame.vehicle_id.astype(str).isin(cohort_ids) &
                            frame.time_s.ge(WINDOW[0]) & frame.time_s.lt(WINDOW[1]) &
                            frame.lane_id.astype(str).isin(LANES) & frame.y_m.ge(TARGET[0]) &
                            frame.y_m.lt(TARGET[1])]
        valid = micro_frame[micro_frame.measurement_status.eq("valid") & micro_frame.ttc_valid.astype(bool)]
        records[label] = {
            "formal": formal,
            "micro": {
                "cohort_target_summary": _summary(micro_frame),
                "valid_ttc_summary": finite_summary(valid.ttc_s),
                "ttc_risk_state_count": int(valid.ttc_s.gt(0).mul(valid.ttc_s.lt(2)).sum()),
                "resolved_leader_fraction": float(micro_frame.leader_id.notna().mean()) if len(micro_frame) else None,
                "native_lane_continuous_fraction": float((~micro_frame.native_lane_id.isna()).mean()) if len(micro_frame) else None,
                "identity_break_count": int(micro_frame.identity_break.astype(bool).sum()) if "identity_break" in micro_frame else None,
                "observation_gap_count": int(micro_frame.observation_gap.astype(bool).sum()) if "observation_gap" in micro_frame else None,
            },
            "macro_rule_a": _macro_rule_a(frame),
        }
    candidate_result = records["Round2_minGap1.0"]
    base_result = records["B00_A03"]
    delta = {
        "target_speed_mean_mps": candidate_result["micro"]["cohort_target_summary"]["speed_mps"]["mean"] - base_result["micro"]["cohort_target_summary"]["speed_mps"]["mean"],
        "target_net_gap_mean_m": candidate_result["micro"]["cohort_target_summary"]["net_gap_m"]["mean"] - base_result["micro"]["cohort_target_summary"]["net_gap_m"]["mean"],
        "target_closing_speed_mean_mps": candidate_result["micro"]["cohort_target_summary"]["closing_speed_mps"]["mean"] - base_result["micro"]["cohort_target_summary"]["closing_speed_mps"]["mean"],
        "target_ttc_risk_states": candidate_result["micro"]["ttc_risk_state_count"] - base_result["micro"]["ttc_risk_state_count"],
        "source_p2_onsets": candidate_result["formal"]["source_all"]["onset_events"] - base_result["formal"]["source_all"]["onset_events"],
        "target_cohort_p2_onsets": candidate_result["formal"]["target_cohort"]["onset_events"] - base_result["formal"]["target_cohort"]["onset_events"],
    }
    result = {
        "schema": "aad.stage05.round2.task1.offline-comparison.v1",
        "task": TASK, "run_id": RUN_ID, "window_s": list(WINDOW),
        "source_region_m": list(SOURCE), "target_region_m": list(TARGET),
        "cohort": "C_INPUT_ROUTE", "cohort_count": len(cohort_ids),
        "formal_rule": {"ttc_lt_s": 2.0, "duration_ge_s": .2, "max_gap_s": .11,
                        "formal_equivalence_accepted": False},
        "baseline_measured_state_sha256": sha(baseline_path),
        "candidate_measured_state_sha256": sha(candidate_output / "measured_state.parquet"),
        "arms": records, "delta_candidate_minus_b00": delta,
        "physical_path": {"status": "Unknown", "reason": "no event-specific witness promotion by offline adapter"},
        "scientific_eligibility": "FAIL_SOURCE_P2_OR_MACRO_RULE_A" if (
            candidate_result["formal"]["source_all"]["onset_events"] == 0 or
            candidate_result["macro_rule_a"]["status"] != "PASS") else "ELIGIBLE_FOR_RESEARCHER_REVIEW_ONLY",
        "native_launches_during_analysis": 0,
    }
    write_json(comparison_output, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--assessment-output", required=True)
    parser.add_argument("--assessment-package", required=True)
    parser.add_argument("--comparison-output", required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    assessment = offline_remeasure(root, args.proposal, args.assessment_output, args.assessment_package)
    comparison = compare(root, root / args.assessment_output / "", root / args.comparison_output)
    print(json.dumps({"assessment": assessment, "comparison_output": args.comparison_output,
                      "native_launches": 0, "source_p2": comparison["arms"]["Round2_minGap1.0"]["formal"]["source_all"]["onset_events"],
                      "macro_rule_a": comparison["arms"]["Round2_minGap1.0"]["macro_rule_a"]["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
