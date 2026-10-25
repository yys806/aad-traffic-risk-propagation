"""Six named historical FCDs, two verified reuses. No simulator execution.

prepare builds a fixed file/hash allowlist. measure accepts only that manifest,
reuses current scientific functions, writes a new version and refuses overwrite.
"""
from __future__ import annotations
import argparse
import gc
import hashlib
import json
import re
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as ET

from stage_0_5_isolation_v2 import Scope, sha
from stage_0_5_input_fidelity import config_references

CALIBRATION = ("us101__0750_0805", "us101__0805_0820")
LOCAL = Path("code/outputs/formal/calibration/stage_0_5_v2_admission_engineering_v1")
CORE = ["code/src/riskprop/" + name + ".py" for name in
        ["stage_0_5_state_support", "stage_0_5_scene_reconstruction", "stage_0_5_d1_measurement", "stage_0_5_sumo"]]


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write((json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode())


def validate_output(root, path):
    scope = Scope(root, {}, path)
    if not scope.output.is_relative_to((root / LOCAL).resolve()) or scope.output == (root / LOCAL).resolve():
        raise ValueError("offline_output_outside_versioned_task")
    return scope.output


def validate_allowlist(manifest):
    if manifest.get("schema") != "aad.c6-history-allowlist.v1" or manifest.get("new_trajectory_attempts") != 0:
        raise ValueError("allowlist_schema")
    if set(manifest.get("core_sha256", {})) != set(CORE):
        raise ValueError("inexact_scientific_source_roles")
    def bound_file(item, expected):
        if item.get("path") != expected:
            raise ValueError("history_path_scope")
        if not re.fullmatch(r"[0-9a-f]{64}", item.get("sha256", "")):
            raise ValueError("missing_history_hash")
    seen = set()
    for case in manifest["cases"]:
        if case["window"] not in CALIBRATION or case["seed"] != 20261201 or case["id"] in seen:
            raise ValueError("unauthorized_case_or_duplicate")
        seen.add(case["id"])
        expected = ("code/outputs/formal/calibration/stage_0_5_state_support_v1/structural/B_het_" + case["window"] + "_lane_drop_4lane") if case["kind"] == "structural" else (
            "code/outputs/formal/calibration/stage_0_5_boundary_timing_v1/runs/" + case["window"] + "_" + case["arm"] + "_s20261201")
        if case["kind"] not in {"structural", "timing"} or (case["kind"] == "timing" and case["arm"] not in {"U", "E"}):
            raise ValueError("unauthorized_history_kind")
        if case["id"] != f"{case['kind']}_{case['window']}_{case['arm'] if case['kind'] == 'timing' else 'L4'}_s20261201":
            raise ValueError("inexact_case_identity")
        if set(case["files"]) != {"fcd", "routes", "network", "config", "old_measurements"}:
            raise ValueError("inexact_file_roles")
        names = dict(fcd="fcd.xml", routes="routes.rou.xml", config="run.sumocfg", old_measurements="measured_state.parquet",
                     network="network/observed_geometry_supply_" + ("27p78_l4" if case["kind"] == "structural" else "10p0_l5") + ".net.xml")
        for role, item in case["files"].items():
            bound_file(item, expected + "/" + names[role])
    if len(manifest["cases"]) > 6:
        raise ValueError("this_offline_scope_is_six_named_cases_not_a_run_budget")
    reused_windows = set()
    for reuse in manifest.get("reuses", []):
        window = reuse.get("window")
        if window not in CALIBRATION or window in reused_windows or reuse.get("seed") != 20261201:
            raise ValueError("unauthorized_reuse")
        reused_windows.add(window)
        if set(reuse.get("files", {})) != {"repaired_measured_state.parquet", "after_events.json"}:
            raise ValueError("inexact_reuse_roles")
        for name, item in reuse["files"].items():
            bound_file(item, "code/outputs/formal/calibration/stage_0_5_c6_c7_offline_v1/" + window + "/" + name)


def prepare(root, target):
    validate_output(root, target.parent)
    base = root / "evidence/results"
    selected = []
    for row in json.loads((base / "RES-STAGE-0.5-STATE-SUPPORT-V1/structural_results.json").read_text(encoding="utf-8"))["results"]:
        cell = row["cell"]
        if cell["condition"] in CALIBRATION and cell["behaviour"] == "B_het" and row["seed"] == 20261201:
            selected.append(("structural", cell["condition"], None,
                "code/outputs/formal/calibration/stage_0_5_state_support_v1/structural/" + cell["cell_id"].replace("|", "_"), row,
                "RES-STAGE-0.5-STATE-SUPPORT-V1", "Re-evaluate historical lane-drop P2 under physical same-lane support"))
    for row in json.loads((base / "RES-STAGE-0.5-ARRIVAL-TIMING-V1/run_results.json").read_text(encoding="utf-8"))["results"]:
        if row["window"] in CALIBRATION and row["seed"] == 20261201 and row["arm"] in {"U", "E"}:
            selected.append(("timing", row["window"], row["arm"],
                f"code/outputs/formal/calibration/stage_0_5_boundary_timing_v1/runs/{row['window']}_{row['arm']}_s20261201", row,
                "RES-STAGE-0.5-ARRIVAL-TIMING-V1", "Re-evaluate the existing paired arrival experiment, not a new timing experiment"))
    cases, skipped = [], []
    for kind, window, arm, directory, row, result_id, question in selected:
        work = root / directory
        try:
            refs = config_references((work / "run.sumocfg").read_bytes())
            names = {"fcd": "fcd.xml", "routes": refs["route-files"], "network": refs["net-file"],
                     "config": "run.sumocfg", "old_measurements": "measured_state.parquet"}
            files = {role: {"path": (Path(directory) / name).as_posix(), "sha256": sha(work / name), "bytes": (work / name).stat().st_size}
                     for role, name in names.items()}
            cases.append(dict(id=f"{kind}_{window}_{arm or 'L4'}_s20261201", kind=kind, window=window, arm=arm, seed=20261201,
                              origin_result_id=result_id, purpose=question, files=files, current_C6_result_exists=False,
                              action="remeasure", historical_integrity="first current-task SHA capture; pre-capture unchanged status Unknown",
                              frozen_evaluation_window_s=[300, 420], existing_candidate_diagnostic_window_s=[120, 390],
                              published_legacy={"N": row.get("p2_events_eval_window_local"), "rate": row.get("p2_local_rate_per_vehicle_hour"),
                                  "point_exposure_s": row["descriptors"].get("p2_evaluable_exposure_veh_s")}))
        except (OSError, ValueError, KeyError) as error:
            skipped.append(dict(directory=directory, reason=type(error).__name__ + ":" + str(error)))
    old = json.loads((base / "RES-STAGE-0.5-C6-C7-OFFLINE-V1/provenance.json").read_text(encoding="utf-8"))
    raw = {}
    for line in (base / "RES-STAGE-0.5-C6-C7-OFFLINE-V1/raw_artifact_SHA256SUMS.txt").read_text().splitlines():
        digest, name = line.split("  ", 1)
        raw[name] = digest
    reuses = []
    for window in CALIBRATION:
        prefix = Path("code/outputs/formal/calibration/stage_0_5_c6_c7_offline_v1") / window
        files = {name: {"path": (prefix / name).as_posix(), "sha256": raw[window + "/" + name]}
                 for name in ["repaired_measured_state.parquet", "after_events.json"]}
        fcd = next((k, v) for k, v in old["inputs"].items() if window in k and k.endswith("/fcd.xml"))
        reuses.append(dict(window=window, seed=20261201, action="reuse_current_C6_no_remeasurement",
                           origin_result_id="RES-STAGE-0.5-C6-C7-OFFLINE-V1", files=files,
                           original_FCD={"path": fcd[0], "sha256": fcd[1]["sha256"], "opened_again": False},
                           purpose="Existing current-interface matched historical reference"))
    manifest = dict(schema="aad.c6-history-allowlist.v1", new_trajectory_attempts=0, cases=cases, reuses=reuses, skipped=skipped,
                    core_sha256={p: sha(root / p) for p in CORE},
                    origin_core_sha256={p: old["source_sha256"][p] for p in CORE},
                    scientific_windows_unchanged=True, source_access="two approved calibration conditions only; no raw real/third-window/holdout")
    validate_allowlist(manifest)
    write_new(target, manifest)
    return manifest


def summarize(d):
    fields = ["eligibility", "onset_events", "local_evaluable_s", "rate_per_evaluable_vehicle_hour", "rate_status",
              "left_continuing_risk_segments", "right_censored_unconfirmed", "confirmation_after_window", "unavailable_point_counts"]
    return {k: d.get(k) for k in fields}


def measure(root, manifest_path, out):
    validate_output(root, out)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_allowlist(manifest)
    if any(sha(root / name) != expected for name, expected in manifest["core_sha256"].items()):
        raise ValueError("scientific_source_drift")
    if manifest["core_sha256"] != manifest["origin_core_sha256"]:
        raise ValueError("current_C6_interface_not_the_reviewed_version")
    out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root / "code/src"))
    import pandas as pd
    import psutil
    from riskprop import stage_0_5_state_support as ss
    from riskprop.stage_0_5_scene_reconstruction import parse_fcd, network_edge_lengths
    from riskprop.stage_0_5_d1_measurement import local_d1_measurement, inside_region
    import site
    bindings = {name: expected for name, expected in manifest["core_sha256"].items()}
    bindings[manifest_path.as_posix()] = sha(manifest_path)
    for case in manifest["cases"]:
        bindings.update({v["path"]: v["sha256"] for v in case["files"].values()})
    for reuse in manifest["reuses"]:
        bindings.update({v["path"]: v["sha256"] for v in reuse["files"].values()})
    scope = Scope(root, bindings, out, runtime_roots=[Path(sys.base_prefix), Path(site.getusersitepackages()), root / "code/src", root / "code/scripts"])
    sys.dont_write_bytecode = True
    sys.addaudithook(scope.audit)  # no subprocess is authorized, including SUMO.
    results, reused = [], []
    try:
        for reuse in manifest["reuses"]:
            for item in reuse["files"].values():
                if sha(root / item["path"]) != item["sha256"]:
                    raise ValueError("reused_result_hash_drift")
            d = json.loads((root / reuse["files"]["after_events.json"]["path"]).read_text(encoding="utf-8"))
            reused.append(dict(window=reuse["window"], status="verified_current_C6_reused", window_s=[120, 390], result=summarize(d)))
        for case in manifest["cases"]:
            started = time.monotonic()
            destination = out / case["id"]
            destination.mkdir()
            try:
                for item in case["files"].values():
                    if sha(root / item["path"]) != item["sha256"]:
                        raise ValueError("history_input_drift")
                config = ET.parse(root / case["files"]["config"]["path"]).getroot()
                if int(config.find(".//seed").get("value")) != case["seed"]:
                    raise ValueError("historical_seed_lineage_mismatch")
                old = pd.read_parquet(root / case["files"]["old_measurements"]["path"])
                run_id = str(old.run_id.iloc[0])
                scenario = str(old.scenario_id.iloc[0])
                before = local_d1_measurement(old, (300, 420), strict=False)
                before_summary = summarize(before)
                old_members = {e["member_sha256"] for e in before.get("events") or []}
                del old, before
                gc.collect()
                print("C6 offline " + case["id"], flush=True)
                fcd = parse_fcd(root / case["files"]["fcd"]["path"], network_edge_lengths(root / case["files"]["network"]["path"]))
                frame = ss.fcd_to_state_frame(fcd, ss.route_length_map(root / case["files"]["routes"]["path"]), run_id=run_id, scenario_id=scenario, seed=case["seed"])
                del fcd
                measured = ss.measure_state_frame(frame)
                del frame
                measured.to_parquet(destination / "repaired_measured_state.parquet", index=False)
                current = local_d1_measurement(measured, (300, 420), strict=True)
                diagnostic = local_d1_measurement(measured, (120, 390), strict=True)
                write_new(destination / "current_frozen_window_events.json", current)
                write_new(destination / "current_candidate_window_events.json", diagnostic)
                members = {e["member_sha256"] for e in current["events"]}
                mask = inside_region(measured) & measured.time_s.ge(300) & measured.time_s.lt(420)
                result = dict(id=case["id"], window=case["window"], kind=case["kind"], arm=case["arm"], seed=case["seed"],
                    status="rechecked_current_interface_changed" if before_summary != summarize(current) else "rechecked_current_interface",
                    published_legacy=case["published_legacy"], old_table_current_D1=before_summary,
                    repaired_frozen_window=summarize(current), candidate_window_separate_descriptive=summarize(diagnostic),
                    event_member_sets=dict(common=len(old_members & members), old_only=len(old_members - members), new_only=len(members - old_members)),
                    physical_support_counts=measured.loc[mask, "physical_support_status"].value_counts().to_dict(),
                    measured_states=len(measured), max_FCD_time_s=float(measured.time_s.max()),
                    resource=dict(wall_s=time.monotonic() - started, observed_rss_bytes=psutil.Process().memory_info().rss),
                    output_sha256={p.name: sha(p) for p in destination.iterdir() if p.is_file()},
                    interpretation="Geometry, leader support and edge qualification may change together; event decrease is not risk disappearance",
                    scientific_claim_eligible=False)
                results.append(result)
                write_new(destination / "result.json", result)
                del measured, current, diagnostic
                gc.collect()
            except Exception as error:
                result = dict(id=case["id"], status="evidence_insufficient_offline_failure", reason=type(error).__name__ + ":" + str(error))
                results.append(result)
                write_new(destination / "failure.json", result)
        report = dict(schema="aad.c6-admission-review.v1", allowlist_sha256=sha(manifest_path), reuses=reused, results=results,
                      new_trajectories=0, all_historical_P2_valid=False, Gate_changed=False,
                      current_interface_scope="six selected cases only; single seed per condition, no new mechanisms established")
        write_new(out / "comparison_summary.json", report)
        return report
    finally:
        write_new(out / "scope_audit.json", scope.summary())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "measure"])
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        value = prepare(args.repo_root.resolve(), args.allowlist.resolve())
        print(json.dumps({"cases": len(value["cases"]), "reuses": len(value["reuses"]), "skipped": value["skipped"]}))
    else:
        if args.output is None:
            parser.error("measure requires a new output directory")
        value = measure(args.repo_root.resolve(), args.allowlist.resolve(), args.output.resolve())
        print(json.dumps({"results": [{"id": r["id"], "status": r["status"]} for r in value["results"]], "new_trajectories": 0}))
        if any(r["status"] == "evidence_insufficient_offline_failure" for r in value["results"]):
            raise SystemExit(1)
