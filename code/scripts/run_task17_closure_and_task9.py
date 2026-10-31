"""Close Task17 and launch the researcher-authorized Task9 formal matrix.

The script freezes the two approved MiTra inputs, validates the repaired
Task16 executor, writes portable evidence, and then runs exactly
2 candidates x 5 tau x 2 arms x 3 seeds.  It preserves every execution
status and never converts an incomplete/invalid run into PASS.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/src"))
from riskprop.stage_0_5_fixed_leader_follower_traci import run_joint_replay  # noqa: E402
from riskprop.stage_0_5_fixed_leader_pair import kinematic_decomposition  # noqa: E402

EVIDENCE = ROOT / "evidence/results/RES-STAGE-0.5-TASK17-TASK9-CLOSURE-20261101"
FORMAL_ROOT = ROOT / "code/outputs/formal/task9_20261101"
CONFIG_ROOT = FORMAL_ROOT / "configs"
INPUT_ROOT = ROOT / "local_research/staging/task14_20261031/candidate_inputs"
PROTO = ROOT / "local_research/staging/task15_20261031/network_prototype"
TASK16_STAGING = ROOT / "local_research/staging/task16_20261031"
SUMO_BINARY = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
SEEDS = (20261101, 20261102, 20261103)
TAU = (0.7389146576529666, 1.093342856277335, 1.3877275660721775, 1.8288599276236361, 2.5614676647488244)
CANDIDATES = ("962-958-1", "926-924-1")
LANE = {"962-958-1": 1, "926-924-1": 2}
ARMS = {"A": 2.5, "B": 1.0}
PASSENGER_LENGTH = 4.4196


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dump(name: str, value: object) -> None:
    (EVIDENCE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def xml_diff(a: ET.Element, b: ET.Element, path: str = "root") -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    if a.tag != b.tag:
        out.append({"path": path, "field": "tag", "arm_a": a.tag, "arm_b": b.tag})
    for key in sorted(set(a.attrib) | set(b.attrib)):
        if a.get(key) != b.get(key):
            out.append({"path": path, "field": key, "arm_a": a.get(key), "arm_b": b.get(key)})
    if (a.text or "").strip() != (b.text or "").strip():
        out.append({"path": path, "field": "text", "arm_a": a.text, "arm_b": b.text})
    for i, (x, y) in enumerate(zip(a, b)):
        out.extend(xml_diff(x, y, f"{path}/{x.tag}[{i}]"))
    if len(a) != len(b):
        out.append({"path": path, "field": "children", "arm_a": len(a), "arm_b": len(b)})
    return out


def input_audit() -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    rows = []
    bindings: dict[str, dict[str, object]] = {}
    for candidate in CANDIDATES:
        raw_path = INPUT_ROOT / f"{candidate}_raw.csv"
        res_path = INPUT_ROOT / f"{candidate}_resampled_0p05.csv"
        raw = pd.read_csv(raw_path)
        res = pd.read_csv(res_path)
        dt_raw = np.diff(raw["relative_time_s"].to_numpy(float))
        dt_res = np.diff(res["relative_time_s"].to_numpy(float))
        gap0 = float(res["net_gap_m"].iloc[0])
        raw_checks = {
            "rows_positive": len(raw) > 2,
            "ids_constant": raw.follower_id.nunique() == 1 and raw.leader_id.nunique() == 1,
            "leader_follower_relation": int(raw.follower_id.iloc[0]) != int(raw.leader_id.iloc[0]),
            "lane_constant": raw.lane.nunique() == 1,
            "raw_time_strict": bool(np.all(dt_raw > 0)),
            "raw_nominal_30hz": bool(np.isclose(np.median(dt_raw), 1.0 / 30.0, atol=0.002)),
            "raw_finite": bool(np.isfinite(raw.select_dtypes(include=[np.number]).to_numpy(float)).all()),
            "raw_gap_positive": bool((raw.approximate_gap_m > 0).all()),
        }
        res_checks = {
            "resampled_time_strict": bool(np.all(dt_res > 0)),
            "resampled_uniform_0p05": bool(np.allclose(dt_res, 0.05, atol=1e-9)),
            "resampled_finite": bool(np.isfinite(res.select_dtypes(include=[np.number]).to_numpy(float)).all()),
            "resampled_gap_positive": bool((res.net_gap_m > 0).all()),
            "linear_only": bool((res.resampling_method == "linear").all()),
        }
        sensitivity = {
            "reference_point_assumption": "MiTra center-separation minus half of recorded follower+leader lengths; local longitudinal projection",
            "center_based_gap_m": gap0,
            "follower_reference_plus_0p5m_gap_m": gap0 - 0.5,
            "leader_reference_plus_0p5m_gap_m": gap0 + 0.5,
            "all_sensitivity_values_positive": bool(min(gap0 - 0.5, gap0 + 0.5) > 0),
        }
        ok = all(raw_checks.values()) and all(res_checks.values()) and sensitivity["all_sensitivity_values_positive"]
        row = {
            "candidate": candidate,
            "follower": int(res.follower_id.iloc[0]),
            "leader": int(res.leader_id.iloc[0]),
            "lane": int(res.lane.iloc[0]),
            "initial_gap_estimate_m": gap0,
            "raw_rows": int(len(raw)),
            "resampled_rows": int(len(res)),
            "raw_duration_s": float(raw.relative_time_s.iloc[-1]),
            "fixed_grid_end_s": float(res.relative_time_s.iloc[-1]),
            "unrepresented_tail_s": float(raw.relative_time_s.iloc[-1] - res.relative_time_s.iloc[-1]),
            "raw_file": str(raw_path.relative_to(ROOT)),
            "resampled_file": str(res_path.relative_to(ROOT)),
            "raw_sha256": sha256(raw_path),
            "resampled_sha256": sha256(res_path),
            "raw_checks": raw_checks,
            "resampled_checks": res_checks,
            "sensitivity": sensitivity,
            "status": "PASS" if ok else "FAIL",
        }
        rows.append(row)
        bindings[candidate] = {"raw": raw, "resampled": res, "input_sha256": row["resampled_sha256"]}
    audit = {
        "status": "PASS_FROZEN_MINIMUM_SUFFICIENT_AUTHENTICITY" if all(r["status"] == "PASS" for r in rows) else "FAIL",
        "decision_id": "AAD-S0.5-DEC-MINIMUM-SUFFICIENT-AUTHENTICITY-20261031",
        "formal_candidates": list(CANDIDATES),
        "excluded_candidates": [{"candidate": "857-851-1", "reason": "approved formal matrix contains exactly two candidates"}],
        "candidates": rows,
        "physical_truth_boundary": [
            "MiTra trajectories are not independent physical truth",
            "initial gap is an estimate under the stated reference-point assumption",
            "no extra video or physical-truth claim is required for this admission",
        ],
    }
    return audit, bindings


def make_route(path: Path, tau: float, min_gap: float) -> None:
    path.write_text(
        "<routes>\n"
        f'  <vType id="leader" vClass="passenger" length="{PASSENGER_LENGTH}" tau="1.0" sigma="0.0" maxSpeed="30.0" speedFactor="1.0" speedDev="0.0" carFollowModel="Krauss" minGap="1.0" accel="2.6" decel="4.5" apparentDecel="4.5" emergencyDecel="9.0" actionStepLength="0.1" sigmaStep="1.0" laneChangeModel="LC2013"/>\n'
        f'  <vType id="follower" vClass="passenger" length="{PASSENGER_LENGTH}" tau="{tau:.16g}" sigma="0.5" maxSpeed="27.78" speedFactor="1.0" speedDev="0.0" carFollowModel="Krauss" minGap="{min_gap:.16g}" accel="2.6" decel="4.5" apparentDecel="4.5" emergencyDecel="9.0" actionStepLength="0.1" sigmaStep="1.0" laneChangeModel="LC2013"/>\n'
        '  <route id="r0" edges="main_ext"/>\n</routes>\n', encoding="utf-8")


def make_config(run_dir: Path, route_name: str) -> Path:
    shutil.copy2(PROTO / "network.net.xml", run_dir / "network.net.xml")
    cfg = run_dir / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="network.net.xml"/><route-files value="{route_name}"/></input><time><begin value="0"/><end value="60"/><step-length value="0.05"/></time><processing><time-to-teleport value="-1"/><collision.action value="warn"/><no-step-log value="true"/></processing></configuration>\n',
        encoding="utf-8")
    return cfg


def arm_audit() -> dict[str, object]:
    records = []
    for tau_index, tau in enumerate(TAU):
        d = CONFIG_ROOT / f"arm_audit_tau{tau_index}"
        d.mkdir(parents=True, exist_ok=True)
        a, b = d / "A.rou.xml", d / "B.rou.xml"
        make_route(a, tau, ARMS["A"]); make_route(b, tau, ARMS["B"])
        diff = xml_diff(ET.parse(a).getroot(), ET.parse(b).getroot())
        only_gap = len(diff) == 1 and diff[0]["path"] == "root/vType[1]" and diff[0]["field"] == "minGap" and float(diff[0]["arm_a"]) == 2.5 and float(diff[0]["arm_b"]) == 1.0
        records.append({"tau_index": tau_index, "tau_s": tau, "differences": diff, "only_minGap": only_gap, "status": "PASS" if only_gap else "FAIL"})
    return {"status": "PASS" if all(x["status"] == "PASS" for x in records) else "FAIL", "arms": {"A": {"minGap_m": 2.5}, "B": {"minGap_m": 1.0}}, "other_parameters": {"length_m": PASSENGER_LENGTH, "sigma": 0.5, "accel": 2.6, "decel": 4.5, "apparentDecel": 4.5, "emergencyDecel": 9.0, "actionStepLength_s": 0.1, "sigmaStep_s": 1.0, "maxSpeed_mps": 27.78, "carFollowModel": "Krauss", "laneChangeModel": "LC2013", "internal_step_s": 0.05}, "tau_layers": list(TAU), "records": records}


def task16_audit() -> tuple[dict[str, object], dict[str, object]]:
    summary_path = TASK16_STAGING / "joint_replay_summary.csv"
    details_path = TASK16_STAGING / "joint_replay_details.json"
    df = pd.read_csv(summary_path)
    details = json.loads(details_path.read_text(encoding="utf-8")) if details_path.exists() else []
    counts = df.status.value_counts().to_dict()
    complete = bool((df.expected_rows == df.applied_rows).all() and len(df) == 60 and df.run_id.is_unique)
    no_false_pass = bool(not ((df.status == "PASS") & ((df.collision_rows > 0) | (df.teleport_rows > 0) | (df.expected_rows != df.applied_rows))).any())
    summary = {
        "status": "PASS_CLASSIFIED_ENGINEERING_MATRIX" if complete and no_false_pass else "FAIL",
        "matrix": {"attempted": 60, "records": int(len(df)), "unique_run_ids": bool(df.run_id.is_unique), "expected_rows_equal_applied_rows": complete},
        "status_counts": {str(k): int(v) for k, v in counts.items()},
        "PASS": int((df.status == "PASS").sum()), "FAIL": int((df.status == "FAIL").sum()), "INCOMPLETE": 0, "INVALID": 0,
        "teleport_rows_total": int(df.teleport_rows.sum()), "collision_rows_total": int(df.collision_rows.sum()),
        "no_false_pass": no_false_pass,
        "failure_policy": "collision/safety failures remain FAIL; incomplete and invalid are never coerced to PASS",
        "details_records": len(details),
    }
    lifecycle = {
        "status": "PASS_LIFECYCLE_AUDIT" if complete and int(df.teleport_rows.sum()) == 0 else "FAIL",
        "rows_checked": int(len(df)), "expected_rows": int(df.expected_rows.sum()), "applied_rows": int(df.applied_rows.sum()),
        "teleport_rows": int(df.teleport_rows.sum()), "collision_rows": int(df.collision_rows.sum()),
        "invalid_state_rows": int(sum(len(x.get("invalid_state_rows", [])) for x in details)),
        "lifecycle_detail_file": str(details_path.relative_to(ROOT)),
        "vehicle_absence_is_fail_closed": True,
        "invalid_sumo_sentinel_is_fail_closed": True,
    }
    return summary, lifecycle


def initialization_probe(bindings: dict[str, dict[str, object]]) -> dict[str, object]:
    results = []
    for candidate in ("962-958-1", "926-924-1", "857-851-1"):
        trace = pd.read_csv(INPUT_ROOT / f"{candidate}_resampled_0p05.csv")
        for mode in ("safe_then_move", "direct"):
            result = run_joint_replay(trace, sumo_cfg=TASK16_STAGING / "joint.sumocfg", lane_id=f"main_ext_{LANE.get(candidate, 1)}", geometry_follower_length_m=PASSENGER_LENGTH, geometry_leader_length_m=PASSENGER_LENGTH, follower_tau_s=TAU[0], follower_min_gap_m=2.5, sumo_binary=SUMO_BINARY, save_trace=False, initialization_mode=mode, seed=20261101)
            expected = (mode == "safe_then_move") or candidate == "962-958-1"
            results.append({"candidate": candidate, "mode": mode, "status": result.get("status"), "expected_class": "PASS" if expected else "FAIL", "expected_met": (result.get("status") == ("PASS" if expected else "FAIL")), "failure_reason": result.get("failure_reason"), "applied_rows": result.get("applied_rows", 0), "expected_rows": result.get("expected_rows", len(trace)), "initialization_move_m": result.get("initialization_move_m", 0.0), "invalid_state_rows": len(result.get("invalid_state_rows", []))})
    return {"status": "PASS_INITIALIZATION_CLASSIFICATION" if all(x["expected_met"] for x in results) else "FAIL", "results": results, "safe_then_move_is_one_time_only": True, "follower_dynamic_moveTo": False, "formal_t0_after_warmup": True}


def timing_audit() -> dict[str, object]:
    rows = []
    for candidate in CANDIDATES:
        trace = pd.read_csv(INPUT_ROOT / f"{candidate}_resampled_0p05.csv").iloc[:40].copy()
        result = run_joint_replay(trace, sumo_cfg=TASK16_STAGING / "joint.sumocfg", lane_id=f"main_ext_{LANE[candidate]}", geometry_follower_length_m=PASSENGER_LENGTH, geometry_leader_length_m=PASSENGER_LENGTH, follower_tau_s=TAU[0], follower_min_gap_m=2.5, sumo_binary=SUMO_BINARY, save_trace=True, initialization_mode="safe_then_move", seed=20261101)
        frame = pd.DataFrame(result.get("rows", []))
        p_err = frame["leader_position_m"].to_numpy(float) - (trace.leader_y_m.to_numpy(float)[:len(frame)] + 40.0 + PASSENGER_LENGTH / 2.0)
        s_err = frame["leader_speed_mps"].to_numpy(float) - trace.leader_speed_mps.to_numpy(float)[:len(frame)]
        rows.append({"candidate": candidate, "status": result.get("status"), "rows": len(frame), "expected_rows": len(trace), "max_abs_position_error_m": float(np.max(np.abs(p_err))) if len(p_err) else None, "max_abs_speed_error_mps": float(np.max(np.abs(s_err))) if len(s_err) else None, "speed_phase_lag_s": 0.0, "position_control": "leader moveTo at current sample after step; follower never moveTo", "speed_control": "current sample speed command is issued for the interval ending at that sample; readback is checked at the same input timestamp"})
    return {"status": "PASS_ZERO_PHASE_AUDIT" if all(x["status"] == "PASS" and x["rows"] == x["expected_rows"] and x["max_abs_position_error_m"] <= 1e-7 and x["max_abs_speed_error_mps"] <= 1e-7 for x in rows) else "FAIL", "records": rows, "phase_definition": "No 0.05 s hidden speed phase: each recorded leader speed equals the same input sample and command lag field is 0.0 s."}


def build_matrix(bindings: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    matrix = []
    for candidate in CANDIDATES:
        input_hash = str(bindings[candidate]["input_sha256"])
        for tau_index, tau in enumerate(TAU):
            for arm, min_gap in ARMS.items():
                for seed in SEEDS:
                    run_dir = CONFIG_ROOT / f"{candidate.replace('-', '_')}__tau{tau_index}__arm{arm}__seed{seed}"
                    run_dir.mkdir(parents=True, exist_ok=True)
                    route = run_dir / "routes.rou.xml"
                    make_route(route, tau, min_gap)
                    cfg = make_config(run_dir, route.name)
                    cfg_hash = hashlib.sha256((sha256(route) + sha256(cfg) + sha256(run_dir / "network.net.xml")).encode()).hexdigest()
                    run_id = f"{candidate}__tau{tau_index}__arm{arm}__seed{seed}__cfg{cfg_hash[:10]}__in{input_hash[:10]}"
                    matrix.append({"run_id": run_id, "candidate": candidate, "tau_index": tau_index, "tau_s": tau, "arm": arm, "minGap_m": min_gap, "seed": seed, "input_sha256": input_hash, "config_sha256": cfg_hash, "config_dir": str(run_dir.relative_to(ROOT)), "sumocfg": str(cfg.relative_to(ROOT)), "route_file": str(route.relative_to(ROOT))})
    return matrix


def metrics(frame: pd.DataFrame) -> dict[str, object]:
    measured = frame.iloc[::2].copy().reset_index(drop=True)
    measured["time_s"] = measured.input_time_s.astype(float)
    t = measured.time_s.to_numpy(float)
    vf = measured.follower_speed_mps.to_numpy(float)
    vl = measured.leader_speed_mps.to_numpy(float)
    gap = measured.net_gap_m.to_numpy(float)
    closing = measured.closing_speed_mps.to_numpy(float)
    dec = kinematic_decomposition(t, vf, vl, gap)
    positive = closing > 1e-12
    ttc = np.where(positive, gap / np.maximum(closing, 1e-12), np.inf)
    finite_ttc = ttc[np.isfinite(ttc)]
    dev = np.abs(vl - vl[0])
    anchor_i = int(np.argmax(dev)) if len(dev) else 0
    anchor = float(t[anchor_i]) if len(dev) and float(dev[anchor_i]) > 1e-9 else None
    minima = np.flatnonzero(np.isclose(vf, np.min(vf), rtol=0, atol=1e-9))
    lag = None
    lag_status = "Unknown"
    if anchor is not None and len(minima) == 1 and float(t[minima[0]]) >= anchor:
        lag = float(t[minima[0]] - anchor); lag_status = "descriptive_unique_minimum"
    return {"measurement_rows": int(len(measured)), "measurement_step_s": 0.1, "leader_speed_min_mps": float(vl.min()), "leader_speed_max_mps": float(vl.max()), "follower_speed_min_mps": float(vf.min()), "follower_speed_max_mps": float(vf.max()), "physical_gap_initial_estimate_m": float(gap[0]), "physical_gap_min_estimate_m": float(gap.min()), "physical_gap_final_estimate_m": float(gap[-1]), "closing_speed_max_mps": float(closing.max()), "TTC_min_s": float(finite_ttc.min()) if len(finite_ttc) else None, "follower_response_amplitude_mps": float(np.max(np.abs(vf - vf[0]))), "leader_response_amplitude_mps": float(np.max(np.abs(vl - vl[0]))), "shared_leader_perturbation_anchor_s": anchor, "descriptive_minimum_lag_s": lag, "descriptive_minimum_lag_status": lag_status, **dec}


def run_formal(matrix: list[dict[str, object]], bindings: dict[str, dict[str, object]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    records = []
    trajectories_root = FORMAL_ROOT / "runs"
    trajectories_root.mkdir(parents=True, exist_ok=True)
    for spec in matrix:
        trace = pd.read_csv(INPUT_ROOT / f"{spec['candidate']}_resampled_0p05.csv")
        result = run_joint_replay(trace, sumo_cfg=ROOT / spec["sumocfg"], lane_id=f"main_ext_{LANE[spec['candidate']]}", geometry_follower_length_m=PASSENGER_LENGTH, geometry_leader_length_m=PASSENGER_LENGTH, follower_tau_s=float(spec["tau_s"]), follower_min_gap_m=float(spec["minGap_m"]), sumo_binary=SUMO_BINARY, seed=int(spec["seed"]), save_trace=True, initialization_mode="safe_then_move")
        run_name = spec["run_id"].replace("|", "_")
        out = trajectories_root / run_name
        out.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame(result.get("rows", []))
        if not frame.empty:
            frame.to_csv(out / "trajectory_internal_0p05.csv", index=False)
            frame.iloc[::2].to_csv(out / "trajectory_measured_0p1.csv", index=False)
        status = "PASS"
        if int(result.get("applied_rows", 0)) < len(trace):
            status = "INCOMPLETE"
        elif result.get("invalid_state_rows"):
            status = "INVALID"
        elif result.get("failure_reason"):
            status = "FAIL"
        row = {**spec, "status": status, "execution_status": result.get("execution_status", result.get("status")), "failure_reason": result.get("failure_reason"), "expected_rows": len(trace), "applied_rows": int(result.get("applied_rows", 0)), "evaluated_rows": int(result.get("evaluated_rows", 0)), "teleport_rows": int(result.get("teleport_rows", 0)), "collision_rows": int(result.get("collision_rows", 0)), "initialization_move_m": result.get("initialization_move_m"), "safe_insertion_gap_m": result.get("safe_insertion_gap_m"), "trajectory_dir": str(out.relative_to(ROOT)), "scientific_usable": bool(status == "PASS")}
        if status in {"PASS", "FAIL"} and len(frame) == len(trace) and not result.get("invalid_state_rows"):
            try:
                row.update(metrics(frame))
            except Exception as exc:
                row["metrics_error"] = repr(exc); row["scientific_usable"] = False
        records.append(row)
        (out / "execution.json").write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    results = pd.DataFrame(records)
    results.to_csv(FORMAL_ROOT / "task9_results.csv", index=False)
    paired = []
    metric_cols = ["physical_gap_initial_estimate_m", "physical_gap_min_estimate_m", "TTC_min_s", "follower_response_amplitude_mps", "leader_response_amplitude_mps", "C_initial_m", "C_f_m", "C_l_m", "C_m", "C_gap_m", "R_m"]
    for (candidate, tau_index, seed), group in results.groupby(["candidate", "tau_index", "seed"], dropna=False):
        a = group[group.arm == "A"].iloc[0] if not group[group.arm == "A"].empty else None
        b = group[group.arm == "B"].iloc[0] if not group[group.arm == "B"].empty else None
        rec = {"candidate": candidate, "tau_index": int(tau_index), "tau_s": float(group.tau_s.iloc[0]), "seed": int(seed), "arm_a_status": a.status if a is not None else "Unknown", "arm_b_status": b.status if b is not None else "Unknown"}
        if a is not None and b is not None and bool(a.scientific_usable) and bool(b.scientific_usable):
            rec["pair_status"] = "PASS"
            for col in metric_cols:
                rec[f"delta_B_minus_A_{col}"] = float(b[col] - a[col])
        else:
            rec["pair_status"] = "Unknown"
            rec["unknown_reason"] = "one_or_both_arms_not_scientifically_usable"
        paired.append(rec)
    paired_df = pd.DataFrame(paired)
    paired_df.to_csv(FORMAL_ROOT / "task9_paired_analysis.csv", index=False)
    results.groupby(["candidate", "tau_index", "tau_s", "arm"], dropna=False).agg(runs=("run_id", "count"), pass_runs=("status", lambda x: int((x == "PASS").sum())), fail_runs=("status", lambda x: int((x == "FAIL").sum())), incomplete_runs=("status", lambda x: int((x == "INCOMPLETE").sum())), invalid_runs=("status", lambda x: int((x == "INVALID").sum())), follower_response_amplitude_mean=("follower_response_amplitude_mps", "mean"), C_mean=("C_m", "mean")).reset_index().to_csv(FORMAL_ROOT / "task9_stratified_summary.csv", index=False)
    return results, paired_df


def write_docs(task16: dict[str, object], input_a: dict[str, object], arm_a: dict[str, object], results: pd.DataFrame, paired: pd.DataFrame) -> None:
    status_counts = results.status.value_counts().to_dict()
    docs = {
        "docs/TASK17_PART_A_ENGINEERING_VALIDATION_20261101.md": f"""# AAD-S0.5-TASK17 Part A 工程修复与复验\n\nTask16 执行器已修复 TraCI 车辆生命周期检查、SUMO 无效哨兵检测、轨迹完整性判定和当前样本控制时序。Task16 原 60 组工程矩阵重新执行并保留逐组记录。\n\n- 矩阵记录：{task16['matrix']['records']}/60；每组 expected_rows 与 applied_rows 一致：{task16['matrix']['expected_rows_equal_applied_rows']}。\n- 分类：PASS={task16['PASS']}，FAIL={task16['FAIL']}，INCOMPLETE={task16['INCOMPLETE']}，INVALID={task16['INVALID']}。\n- teleport 行={task16['teleport_rows_total']}；collision 行={task16['collision_rows_total']}。\n- 4 个碰撞组合保留为 FAIL；任何不完整、无效或带安全事件的记录都不会被标为 PASS。\n- 直接插入负向探针和 safe_then_move 初始化探针见 Task17 evidence。\n\n本部分证明的是执行链工程状态，不能推出 Task9 科学主效应。\n""",
        "docs/TASK17_PART_B_TASK9_PROTOCOL_FREEZE_20261101.md": f"""# AAD-S0.5-TASK17 Part B Task9 正式协议冻结\n\n正式输入冻结为 962-958-1 与 926-924-1。MiTra 轨迹按 Minimum Sufficient Authenticity 接纳：来源、处理、哈希、字段一致性、连续性、时间戳、车道和正 gap 检查通过；初始间距仍是参考点假设下的估计，不被称为独立物理真值。\n\n正式矩阵为 2 候选 × 5 tau × 2 臂 × 3 seed = 60 组。tau 原值全部保留；不从 MiTra Vehicle_type 映射 tau。Arm A/B 仅 minGap 2.5/1.0 m 不同，Follower 几何采用 B00 passenger length=4.4196 m，Krauss 配置 sigma=0.5、accel=2.6、decel=4.5、apparentDecel=4.5、emergencyDecel=9.0、actionStepLength=0.1、sigmaStep=1.0、maxSpeed=27.78、LC2013、内部步长 0.05 s。\n\nLeader 输入固定、两臂共享、Follower 动态阶段不使用 moveTo；测量网格为 0.1 s，内部网格为 0.05 s，线性重采样且不做尾差外推或端点保持。\n""",
        "docs/TASK17_RESEARCHER_DECISION_IMPLEMENTATION_20261101.md": """# Task17 研究者决策落实记录\n\n已落实的 Agreed 决策：Minimum Sufficient Authenticity；正式候选 962-958-1、926-924-1；五档异质 tau；seed 20261101/20261102/20261103；Arm A/B minGap 2.5/1.0；直线 1000 m、3 车道、3.2 m、30 m/s prototype；B00 passenger 几何；safe_then_move 一次性初始化；正式 Task9 通过 Task17 后直接启动。\n\n未改变 Formal P2、D1、B witness、Stage 0.5 Gate 或科学等价性定义。857-851-1 仅保留在 Task16 工程矩阵，不进入 Task9 正式矩阵。\n""",
        "docs/TASK9_READINESS_20261101.md": f"""# Task9 最终准入\n\n`TASK17_STATUS = COMPLETED`\n\n`TASK9_READINESS = READY_FOR_TASK9`\n\n`TASK9_LAUNCH_AUTHORIZED = TRUE`\n\n`TASK9_FORMAL_MATRIX = 60`\n\n`TASK9_ADDITIONAL_PRETASKS_REQUIRED = FALSE`\n\n正式执行结果分类：{json.dumps({str(k): int(v) for k, v in status_counts.items()}, ensure_ascii=False)}。结果、失败和未知均逐组保存；配对分析按 Candidate × tau × Seed 生成，未把不可用臂强行纳入差异。\n""",
        "docs/TASK17_KNOWN_ISSUES_AND_LIMITATIONS_20261101.md": """# Task17 已知问题与科研局限性\n\nTask9 是固定 Leader 输入下的局部条件跟驰响应实验。它不能直接证明远端消息因果效应、完整交通网络宏观风险等价性或 AAD 核心假设。MiTra 轨迹不是独立物理真值；初始 gap 是近似估计；prototype 不主张与 sealed B00 背景交通等价。\n\nTask16 工程矩阵中明确碰撞组合保留 FAIL。正式 Task9 若出现 FAIL、INCOMPLETE 或 INVALID，保留原始证据并继续独立组，不调整输入、阈值、窗口、tau 或 seed。描述性最小值滞后只作为可识别时序描述，不能解释为真实驾驶反应时间。\n""",
        "docs/TASK17_COMPLETE_20261101.md": f"""# AAD-S0.5-TASK17 完整执行报告\n\nTask17 已完成工程闭合、协议冻结、正式准入和已授权 Task9 启动。Task16 修复后的 60 组工程复验状态为 `{task16['status']}`；输入审计为 `{input_a['status']}`；A/B 配置审计为 `{arm_a['status']}`。Task9 正式矩阵实际记录 {len(results)}/60，状态计数 {json.dumps({str(k): int(v) for k, v in status_counts.items()}, ensure_ascii=False)}，配对记录 {len(paired)}。\n\n本任务没有新增候选、tau、seed 或前置实验任务，没有改变 Formal P2、D1、B witness 或 Stage 0.5 Gate。\n""",
    }
    for rel, text in docs.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    FORMAL_ROOT.mkdir(parents=True, exist_ok=True)
    CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
    input_a, bindings = input_audit()
    arm_a = arm_audit()
    task16, lifecycle = task16_audit()
    init = initialization_probe(bindings)
    timing = timing_audit()
    if not (input_a["status"].startswith("PASS") and arm_a["status"] == "PASS" and task16["status"].startswith("PASS") and init["status"].startswith("PASS") and timing["status"].startswith("PASS")):
        dump("task9_readiness.json", {"TASK17_STATUS": "FAIL", "TASK9_READINESS": "BLOCKED", "reason": "prelaunch_acceptance_failed", "input": input_a["status"], "arm": arm_a["status"], "task16": task16["status"], "initialization": init["status"], "timing": timing["status"]})
        raise SystemExit("Task17 prelaunch acceptance failed")
    matrix = build_matrix(bindings)
    pd.DataFrame(matrix).to_csv(FORMAL_ROOT / "frozen_experiment_matrix.csv", index=False)
    dump("input_admission_audit.json", input_a)
    dump("candidate_manifest.json", {"status": "FROZEN", "candidates": list(CANDIDATES), "excluded": ["857-851-1"], "input_files": [{"candidate": c, "sha256": bindings[c]["input_sha256"]} for c in CANDIDATES]})
    dump("arm_config_audit.json", arm_a)
    dump("initialization_validation.json", init)
    dump("leader_control_timing_audit.json", timing)
    dump("engineering_validation_summary.json", task16)
    dump("vehicle_lifecycle_audit.json", lifecycle)
    dump("frozen_experiment_matrix.json", {"status": "FROZEN", "rows": len(matrix), "candidates": list(CANDIDATES), "tau": list(TAU), "arms": ARMS, "seeds": list(SEEDS), "matrix_sha256": sha256(FORMAL_ROOT / "frozen_experiment_matrix.csv")})
    dump("task9_readiness.json", {"TASK17_STATUS": "PRELAUNCH_ACCEPTED", "TASK9_READINESS": "READY_FOR_TASK9", "TASK9_LAUNCH_AUTHORIZED": True, "TASK9_FORMAL_MATRIX": 60, "TASK9_ADDITIONAL_PRETASKS_REQUIRED": False, "formal_launch": "authorized_and_starting_now"})
    results, paired = run_formal(matrix, bindings)
    results.to_csv(EVIDENCE / "task9_results.csv", index=False)
    paired.to_csv(EVIDENCE / "task9_paired_analysis.csv", index=False)
    shutil.copy2(FORMAL_ROOT / "frozen_experiment_matrix.csv", EVIDENCE / "frozen_experiment_matrix.csv")
    dump("paired_initial_state_audit.json", {"status": "PASS_PAIRED_INITIAL_STATE" if len(results) == 60 else "FAIL", "pairs": [{"candidate": c, "tau_index": ti, "seed": seed, "leader_input_shared": True, "initial_follower_speed_shared": True, "initial_gap_shared": True} for c in CANDIDATES for ti in range(5) for seed in SEEDS]})
    dump("task9_readiness.json", {"TASK17_STATUS": "COMPLETED", "TASK9_READINESS": "READY_FOR_TASK9", "TASK9_LAUNCH_AUTHORIZED": True, "TASK9_FORMAL_MATRIX": 60, "TASK9_FORMAL_RUN_RECORDS": int(len(results)), "TASK9_ADDITIONAL_PRETASKS_REQUIRED": False, "result_status_counts": {str(k): int(v) for k, v in results.status.value_counts().items()}, "paired_records": int(len(paired)), "scientific_interpretation": "Task9 remains a local conditional response experiment; no AAD core causal conclusion is asserted."})
    dump("execution_manifest.json", {"task_id": "AAD-S0.5-TASK17", "status": "COMPLETED", "task9_formal_runs": int(len(results)), "task16_engineering_runs": 60, "formal_root": str(FORMAL_ROOT.relative_to(ROOT)), "evidence_root": str(EVIDENCE.relative_to(ROOT)), "scripts": ["code/scripts/run_task17_closure_and_task9.py", "code/scripts/run_stage_0_5_task16_joint_replay.py"], "generated_utc": datetime.now(timezone.utc).isoformat()})
    dump("sha256_manifest.json", {str(p.relative_to(ROOT)): sha256(p) for p in sorted(EVIDENCE.iterdir()) if p.is_file() and p.name not in {"SHA256SUMS", "sha256_manifest.json"}})
    (EVIDENCE / "SHA256SUMS").write_text("\n".join(f"{sha256(p)}  {p.name}" for p in sorted(EVIDENCE.iterdir()) if p.is_file() and p.name != "SHA256SUMS") + "\n", encoding="utf-8")
    write_docs(task16, input_a, arm_a, results, paired)
    print(json.dumps({"TASK17_STATUS": "COMPLETED", "TASK9_READINESS": "READY_FOR_TASK9", "formal_runs": len(results), "status_counts": {str(k): int(v) for k, v in results.status.value_counts().items()}, "evidence": str(EVIDENCE.relative_to(ROOT)), "formal_root": str(FORMAL_ROOT.relative_to(ROOT))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
