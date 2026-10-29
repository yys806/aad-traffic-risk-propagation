"""Offline Round2 Task2 measurement-contract audit.

The script only constructs deterministic in-memory fixtures and reads the already
sealed post-R2 diagnostic indexes.  It never starts SUMO/TraCI, reads a holdout, or
changes a production measurement rule.  Its output is a portable evidence package
for researcher adjudication of formal P2, SUMO-native, formal-aligned and D1 rules.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))

from riskprop.stage_0_5_d1_measurement import local_d1_measurement  # noqa: E402
from riskprop.stage_0_5_sumo import (  # noqa: E402
    _synthetic_states,
    build_sumo_formal_source_frame,
    build_sumo_p2_events,
    compute_sumo_measurements,
    extract_sumo_formal_p2_events,
    following_link_is_valid,
)


PACKAGE = ROOT / "evidence" / "results" / "RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029"
DIAG = ROOT / "evidence" / "results" / "RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029"


def _jsonable(value: Any) -> Any:
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not math.isfinite(float(value)) else float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(_jsonable(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def spec(*, leader: str | None = "l", gap: float = 1.0, leader_speed: float = 11.4,
         lane: str = "main_0_0", edge: str = "main_0", connection: bool = False) -> dict[str, Any]:
    return {
        "leader_id": leader,
        "leader_speed_mps": leader_speed,
        "net_gap_m": gap,
        "lane_id": lane,
        "native_lane_id": lane,
        "edge_id": edge,
        "road_connection_witness": connection,
    }


def case_specs() -> dict[str, dict[str, Any]]:
    risk = lambda n: [spec() for _ in range(n)]
    return {
        "normal_continuous_following": {"times": [0.0, .1, .2, .3, .4], "specs": risk(5)},
        "native_lane_id_change_no_connection": {
            "times": [0.0, .1, .2, .3, .4],
            "specs": [spec(lane="main_0_0") for _ in range(3)] + [spec(lane="main_0_1") for _ in range(2)],
        },
        "connected_road_boundary": {
            "times": [0.0, .1, .2, .3, .4],
            "specs": [spec(lane="main_0_0", edge="main_0") for _ in range(3)]
            + [spec(lane="main_1_0", edge="main_1", connection=True) for _ in range(2)],
        },
        "real_lane_change": {
            "times": [0.0, .1, .2, .3, .4],
            "specs": [spec(lane="main_0_0") for _ in range(2)]
            + [spec(lane="main_0_1", connection=False) for _ in range(3)],
        },
        "leader_switch": {
            "times": [0.0, .1, .2, .3, .4],
            "specs": [spec(leader="l1") for _ in range(2)] + [spec(leader="l2") for _ in range(3)],
        },
        "incarnation_change": {
            "times": [0.0, .1, .2, .3, .4],
            "specs": risk(5),
            "incarnation_switch_at": 3,
        },
        "identity_break": {
            "times": [0.0, .1, .2, .3, .4],
            "specs": risk(5),
            "identity_break_at": 3,
        },
        "observation_gap_flag": {
            "times": [0.0, .1, .2, .3, .4],
            "specs": risk(5),
            "observation_gap_at": 3,
        },
        "missing_recorded_frame": {
            "times": [0.0, .1, .3, .4, .5],
            "specs": risk(5),
        },
        "non_positive_ttc_input": {
            "times": [0.0, .1, .2, .3],
            "specs": risk(4),
            "override_negative_ttc": True,
        },
        "threshold_exactly_2s": {
            "times": [0.0, .1, .2, .3],
            "specs": [spec(gap=1.2) for _ in range(4)],
        },
        "minimum_duration_exactly_0_2s": {"times": [0.0, .1, .2], "specs": risk(3)},
        "minimum_duration_below_0_2s": {"times": [0.0, .1], "specs": risk(2)},
        "risk_exit_then_reentry": {
            "times": [round(.1 * i, 10) for i in range(9)],
            "specs": risk(3) + [spec(leader_speed=14.0) for _ in range(2)] + risk(4),
        },
        "window_boundary_onset_outside": {
            "times": [0.0, .1, .2, .3, .4],
            "specs": risk(5),
            "window": [0.1, .5],
        },
        "no_leader_boundary_missing": {
            "times": [0.0, .1, .2],
            "specs": [spec(leader=None) for _ in range(3)],
        },
    }


def build_case_frame(case: dict[str, Any], name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_rows = [{"time_s": float(t), **dict(s)} for t, s in zip(case["times"], case["specs"])]
    if case.get("incarnation_switch_at") is not None:
        switch = int(case["incarnation_switch_at"])
        for i, row in enumerate(raw_rows):
            row["incarnation_id"] = "run|f|1" if i >= switch else "run|f|0"
    frame = _synthetic_states(raw_rows, fixture_id=f"task2_{name}")
    frame["y_m"] = 200.0
    frame["lane_id"] = "1"
    frame["native_lane_id"] = frame["vehicle_id"].astype(str).map(lambda x: "leader" if x != "f" else "main_0_0")
    frame["road_connection_witness"] = False
    frame["identity_break"] = False
    frame["observation_gap"] = False
    # Apply the follower's lane/edge/path annotations at each timestamp to both the
    # follower row and its contemporaneous leader row.
    annotations = {float(t): s for t, s in zip(case["times"], case["specs"])}
    for idx, row in frame.iterrows():
        t = float(row["time_s"])
        ann = annotations[t]
        if str(row["vehicle_id"]) == "f":
            frame.at[idx, "native_lane_id"] = ann.get("native_lane_id", ann.get("lane_id", "main_0_0"))
            frame.at[idx, "edge_id"] = ann.get("edge_id", "main_0")
            frame.at[idx, "road_connection_witness"] = bool(ann.get("road_connection_witness", False))
        else:
            frame.at[idx, "native_lane_id"] = ann.get("native_lane_id", ann.get("lane_id", "main_0_0"))
            frame.at[idx, "edge_id"] = ann.get("edge_id", "main_0")
    if case.get("identity_break_at") is not None:
        i = int(case["identity_break_at"])
        frame.loc[(frame.vehicle_id == "f") & frame.time_s.eq(float(case["times"][i])), "identity_break"] = True
    if case.get("observation_gap_at") is not None:
        i = int(case["observation_gap_at"])
        frame.loc[(frame.vehicle_id == "f") & frame.time_s.eq(float(case["times"][i])), "observation_gap"] = True
    measured = compute_sumo_measurements(frame)
    if case.get("override_negative_ttc"):
        mask = measured.vehicle_id.eq("f")
        measured.loc[mask, "ttc_s"] = -1.0
        measured.loc[mask, "ttc_valid"] = True
        measured.loc[mask, "measurement_status"] = "valid"
    return frame, measured


def select_events(frame: pd.DataFrame, columns: tuple[str, ...]) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    return [{key: _jsonable(row.get(key)) for key in columns} for row in frame.to_dict("records")]


def candidate_rule_summary(measured: pd.DataFrame) -> dict[str, Any]:
    d = measured.loc[measured.vehicle_id.eq("f")].sort_values("time_s", kind="stable").reset_index(drop=True)
    results: dict[str, Any] = {}
    for rule, lane_policy in (("A_strict_native_lane", "same"), ("B_connected_boundary", "connected"), ("C_pair_time_continuity", "any")):
        segments: list[list[int]] = []
        current: list[int] = []
        for i, row in d.iterrows():
            risk = bool(row.get("ttc_valid")) and str(row.get("measurement_status")) == "valid" and float(row.get("ttc_s", np.nan)) > 0 and float(row.get("ttc_s", np.nan)) < 2.0
            if not risk:
                if current:
                    segments.append(current); current = []
                continue
            if not current:
                current = [i]; continue
            prev = d.iloc[current[-1]].to_dict(); cur = row.to_dict()
            link = following_link_is_valid(prev, cur, cadence_s=0.1)
            lane_same = str(prev.get("native_lane_id")) == str(cur.get("native_lane_id"))
            connected = bool(cur.get("road_connection_witness", False)) or bool(prev.get("road_connection_witness", False))
            allowed = link and (lane_same if lane_policy == "same" else (lane_same or connected) if lane_policy == "connected" else True)
            if allowed:
                current.append(i)
            else:
                segments.append(current); current = [i]
        if current:
            segments.append(current)
        events = []
        incomplete = []
        for idxs in segments:
            first, last = d.iloc[idxs[0]], d.iloc[idxs[-1]]
            span = float(last.time_s - first.time_s)
            if span >= 0.2 - 1e-9:
                events.append({"onset_s": float(first.time_s), "confirmation_s": float(first.time_s + 0.2),
                               "end_s": float(last.time_s), "members": len(idxs),
                               "leader_id": str(first.leader_id), "lane_start": str(first.native_lane_id),
                               "lane_end": str(last.native_lane_id)})
            else:
                incomplete.append({"onset_s": float(first.time_s), "end_s": float(last.time_s),
                                   "status": "observed_short_risk"})
        exposure_links = 0
        unknown_links = 0
        for a, b in zip(d.iloc[:-1].to_dict("records"), d.iloc[1:].to_dict("records")):
            if not (bool(a.get("reliable_following_eligible")) and bool(b.get("reliable_following_eligible"))):
                continue
            if str(a.get("measurement_status")) not in {"valid", "not_applicable"} or str(b.get("measurement_status")) not in {"valid", "not_applicable"}:
                continue
            link = following_link_is_valid(a, b, cadence_s=0.1)
            same = str(a.get("native_lane_id")) == str(b.get("native_lane_id"))
            connected = bool(a.get("road_connection_witness")) or bool(b.get("road_connection_witness"))
            if not link:
                continue
            if lane_policy == "same" and not same:
                unknown_links += 1
            elif lane_policy == "connected" and not same and not connected:
                unknown_links += 1
            else:
                exposure_links += 1
        results[rule] = {"events": events, "event_count": len(events), "incomplete": incomplete,
                         "exposure_s": exposure_links * 0.1, "unknown_boundary_links": unknown_links,
                         "physical_path_qualification": ("same_native_lane" if lane_policy == "same" else
                             "connected_boundary_witness" if lane_policy == "connected" else "separate_from_pair_P2")}
    return results


def run_cases() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inputs, outputs = [], []
    event_cols = ("event_id", "vehicle_id", "incarnation_id", "leader_id", "leader_incarnation_id",
                  "event_start_s", "event_confirm_s", "event_end_s", "event_observed_span_s", "exit_reason",
                  "ttc_min_s", "raw_frame_count", "inclusion_status")
    for name, case in case_specs().items():
        raw, measured = build_case_frame(case, name)
        window = tuple(case.get("window", [0.0, 1.0]))
        native, native_exposure = build_sumo_p2_events(measured, recorded_observation_step_s=0.1)
        formal_error = None
        try:
            formal, formal_audit = extract_sumo_formal_p2_events(measured, recorded_observation_step_s=0.1)
        except Exception as exc:  # expected for the inconsistent negative-TTC fixture
            formal = pd.DataFrame(); formal_audit = {"equivalence_status": "error", "error": f"{type(exc).__name__}:{exc}"}
            formal_error = f"{type(exc).__name__}:{exc}"
        d1_error = None
        try:
            d1 = local_d1_measurement(measured, window, strict=True)
        except Exception as exc:
            d1 = {"events": [], "incomplete_candidates": [], "local_evaluable_s": None, "onset_events": None}
            d1_error = f"{type(exc).__name__}:{exc}"
        inputs.append({"case": name, "specification": case,
                       "follower_rows": select_events(measured.loc[measured.vehicle_id.eq("f")],
                           ("vehicle_id", "incarnation_id", "time_s", "leader_id", "leader_incarnation_id",
                            "native_lane_id", "edge_id", "road_connection_witness", "identity_break",
                            "observation_gap", "measurement_status", "ttc_valid", "ttc_s", "reliable_following_eligible"))})
        outputs.append({
            "case": name,
            "native": {"events": select_events(native, event_cols), "exposure": native_exposure},
            "formal_aligned": {"events": select_events(formal, ("event_id", "vehicle_id", "leader_id", "trajectory_id", "leader_trajectory_id", "event_start_s", "event_confirm_s", "event_end_s", "event_duration_s", "raw_frame_count", "exit_reason")),
                               "audit": formal_audit, "error": formal_error},
            "D1": {"onset_events": d1.get("onset_events"), "local_links": d1.get("local_links"),
                   "local_evaluable_s": d1.get("local_evaluable_s"), "events": d1.get("events", []),
                   "incomplete_candidates": d1.get("incomplete_candidates", []),
                   "unavailable_point_counts": d1.get("unavailable_point_counts", {}), "error": d1_error},
            "candidate_rules": candidate_rule_summary(measured),
            "interface_semantics": {
                "formal_P2": "approved source estimator; formal-aligned adapter is a simulator field projection and remains pending",
                "SUMO_native": "engineering event/exposure adapter; native exit reasons retained",
                "D1": "local onset attribution plus same-native-lane exposure; physical path not inferred",
            },
        })
    return inputs, outputs


def contract_matrix() -> dict[str, Any]:
    return {
        "schema_version": "aad.stage0.5.round2.task2.contract-audit.v1",
        "status": "verified_offline_scientific_equivalence_pending",
        "rows": [
            {"dimension": "ttc_positive_finite_direction", "formal_P2": "positive finite TTC from positive gap and positive closing", "SUMO_native": "compute_sumo_measurements requires finite gap/closing and ttc_valid", "formal_aligned": "reuses projected ttc_valid but does not repair inconsistent input", "D1": "requires ttc_valid, status=valid and TTC>0", "evidence": "synthetic/non_positive_ttc; source report rule table", "verdict": "interface_difference_reproduced"},
            {"dimension": "threshold_duration_cadence", "formal_P2": "0<TTC<2; span>=0.2; 100ms; max gap 0.11s", "SUMO_native": "same threshold/span and cadence guard", "formal_aligned": "same extractor; nonstandard cadence explicitly non-comparable", "D1": "100ms grid and 0.2 span with 1e-9 tolerance", "evidence": "existing_boundary_matrix + synthetic threshold/duration/missing-frame cases", "verdict": "engineering_consistent_only"},
            {"dimension": "identity_pair_incarnation", "formal_P2": "trajectory/leader trajectory scope", "SUMO_native": "run-scoped incarnation and resolved leader", "formal_aligned": "incarnation mapped to trajectory_id", "D1": "run/scenario/vehicle/incarnation plus leader pair", "evidence": "leader_switch and incarnation_change cases", "verdict": "continuity_split_verified"},
            {"dimension": "explicit_flags", "formal_P2": "identity_break/observation_gap block links", "SUMO_native": "flags are consumed by following_link_is_valid", "formal_aligned": "build_sumo_formal_source_frame resets both flags false", "D1": "both endpoints must be false", "evidence": "identity_break and observation_gap cases", "verdict": "not_equivalent_pending_researcher"},
            {"dimension": "clock_frame_order", "formal_P2": "original row/frame and absolute clock are auditable", "SUMO_native": "observation_index and time_s are checked", "formal_aligned": "row/frame are adapter-defined and renumbered", "D1": "requires ordered 100ms grid and frame increments", "evidence": "late-entry/missing-frame existing matrix; task2 inputs", "verdict": "time_delta_comparable_absolute_origin_different"},
            {"dimension": "lane_and_path", "formal_P2": "formal source does not silently infer physical path", "SUMO_native": "general pair continuity does not require same native lane", "formal_aligned": "lane is mapped but no path witness is created", "D1": "same native lane required", "evidence": "native_lane_id_change and connected_road_boundary cases", "verdict": "candidate_A_B_C_pending"},
            {"dimension": "missing_unknown", "formal_P2": "missing/no leader/boundary remain unknown", "SUMO_native": "no leader=not_applicable; unresolved identity=missing", "formal_aligned": "field projection preserves status but not all provenance", "D1": "missing and not_applicable excluded from reliable risk", "evidence": "no_leader_boundary_missing; source 1061/1409 boundary missing", "verdict": "unknown_preserved"},
            {"dimension": "P2_vs_D1_exposure", "formal_P2": "formal event qualification is separate from local D1 denominator", "SUMO_native": "compute_exposure reports engineering exposure", "formal_aligned": "formal event count only; no scientific rate acceptance", "D1": "local same-lane evaluable links and onset attribution", "evidence": "all synthetic outputs and post-R2 exposure 8457.4/8900.0 veh-s", "verdict": "not_interchangeable"},
            {"dimension": "censoring_and_reentry", "formal_P2": "threshold exit/leader switch/continuity break/right censoring separated", "SUMO_native": "exit_reason vocabulary emitted", "formal_aligned": "extractor emits exit_reason", "D1": "short/right-censored incomplete candidates retained; no universal exit reason", "evidence": "right-censored and risk_exit_then_reentry existing cases plus task2 cases", "verdict": "native_detail_exceeds_D1"},
        ],
    }


def candidate_comparison(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for out in outputs:
        rules = out["candidate_rules"]
        rows.append({"case": out["case"], "A": rules["A_strict_native_lane"], "B": rules["B_connected_boundary"], "C": rules["C_pair_time_continuity"],
                     "interpretation": "B admits only an explicit connected-boundary witness; C keeps physical-path qualification separate"})
    return {"schema_version": "aad.stage0.5.round2.task2.candidate-rules.v1", "candidates": {
        "A": "strict same native lane; conservative path proxy; candidate only",
        "B": "allow connected road boundary with continuous pair/time witness; candidate only",
        "C": "general pair/time continuity for P2, lane/path qualification reported separately; candidate only",
    }, "rows": rows, "recommendation": "No formal recommendation is accepted by this package. Preserve current Rule A and ask the researcher to choose whether B or C is scientifically estimand-aligned before any production change.", "scientific_equivalence_accepted": False}


def literature_ledger() -> dict[str, Any]:
    reg = PACKAGE / "zotero_registration_result.json"
    results = json.loads(reg.read_text(encoding="utf-8"))["results"] if reg.exists() else []
    sources = {
        "pu_joshi_2008_ssam_manual": "https://www.fhwa.dot.gov/publications/research/safety/08050/",
        "gettman_pu_sayed_shelby_2008_ssam_validation": "https://www.fhwa.dot.gov/publications/research/safety/08051/08051.pdf",
        "gettman_head_2003_surrogate_measures": "https://www.fhwa.dot.gov/publications/research/safety/03050/",
        "arun_2021_systematic_conflict_review": "https://doi.org/10.1016/j.amar.2021.100185",
        "lu_2021_smos_naturalistic": "https://doi.org/10.1016/j.aap.2021.106403",
        "hu_2022_conflict_risk_copula": "https://doi.org/10.1093/tse/tdac017",
        "tang_2026_ettc_conflicts": "https://doi.org/10.1371/journal.pone.0344623",
        "hale_2021_trajectory_calibration": "https://www.fhwa.dot.gov/publications/research/operations/21071/21071.pdf",
    }
    rows = []
    for item in results:
        rows.append({**item, "official_source": sources.get(item["id"]), "metadata_status": "verified_from_official_or_publisher_listing",
                     "attachment_status": "not_acquired_in_this_environment", "reason": "PowerShell/Python outbound sockets are blocked; no PDF was copied into the repository or Zotero attachment store."})
    rows.append({"id": "sharma_2019_trajectory_completeness", "title": "Is more always better? The impact of vehicular trajectory completeness on car-following model calibration and validation", "doi": "10.1016/j.trb.2018.12.016", "item_key": "B8J8W6P2", "action": "existing_reused", "collection_key": "PWZDPXEE", "official_source": "https://doi.org/10.1016/j.trb.2018.12.016", "metadata_status": "verified_existing_zotero_item", "attachment_status": "existing_item_attachment_state_not_modified"})
    return {"schema_version": "aad.stage0.5.round2.task2.literature-ledger.v1", "collection_roots": {"risk": "NXNARCWW", "trajectory": "PWZDPXEE", "validation": "2BMKNCD3"}, "rows": rows, "deduplication": "DOI/title checked against local Zotero API; no duplicate item created; Sharma 2019 reused as B8J8W6P2."}


def sealed_trace_reuse() -> dict[str, Any]:
    return {
        "schema_version": "aad.stage0.5.round2.task2.sealed-reuse.v1",
        "source_package": "evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/",
        "report": "docs/STAGE_0_5_POST_R2_OFFLINE_DIAGNOSTIC_20261029.md",
        "reused_artifacts": ["diagnostic.json", "existing_boundary_matrix.json", "existing_equivalence_matrix.json", "adapter_counterexamples.json", "B00_A03_source_segments.csv", "Round2_minGap1.0_source_segments.csv", "source_time_space_blocks.csv"],
        "verified_metrics": {"B00_source_observations": 86234, "candidate_source_observations": 91058, "B00_D1_exposure_s": 8457.4, "candidate_D1_exposure_s": 8900.0, "B00_formal_risk_states": 0, "candidate_formal_risk_states": 0, "B00_near_threshold_states_2_to_3s": 30, "candidate_near_threshold_states_2_to_3s": 29, "new_SUMO_launches": 0, "holdout_reads": 0},
        "impact_statement": "Synthetic cases establish interface behavior only. They do not attribute the current source zero-event result to lane, flag, or invalid-TTC differences; sealed source risk states remain zero with all observed valid TTC >= 2 s.",
    }


def source_bindings() -> dict[str, Any]:
    paths = ["code/configs/stage_0_2_formal_risk_measurement_p2_v1.json", "code/src/riskprop/formal_risk_measurement.py", "code/src/riskprop/stage_0_5_sumo.py", "code/src/riskprop/stage_0_5_d1_measurement.py", "code/scripts/stage_0_5_acceptance_v3.py", "docs/STAGE_0_5_POST_R2_OFFLINE_DIAGNOSTIC_20261029.md"]
    return {"schema_version": "aad.stage0.5.round2.task2.source-bindings.v1", "git_head": __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "files": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}}


def package_hashes() -> None:
    files = sorted(p for p in PACKAGE.iterdir() if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"})
    manifest = {"schema_version": "aad.evidence-manifest.v1", "result_id": PACKAGE.name, "self_reference": False, "files": [{"path": p.name, "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    write_json(PACKAGE / "manifest.json", manifest)
    rows = []
    for p in sorted(PACKAGE.iterdir()):
        if p.name == "SHA256SUMS":
            continue
        rows.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    (PACKAGE / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    inputs, outputs = run_cases()
    write_json(PACKAGE / "synthetic_case_inputs.json", {"schema_version": "aad.stage0.5.round2.task2.synthetic-inputs.v1", "cases": inputs})
    write_json(PACKAGE / "synthetic_case_results.json", {"schema_version": "aad.stage0.5.round2.task2.synthetic-results.v1", "interfaces": ["SUMO_native", "formal_aligned", "D1"], "cases": outputs})
    write_json(PACKAGE / "contract_audit_matrix.json", contract_matrix())
    write_json(PACKAGE / "candidate_rule_comparison.json", candidate_comparison(outputs))
    write_json(PACKAGE / "sealed_trace_reuse.json", sealed_trace_reuse())
    write_json(PACKAGE / "literature_dedup_acquisition.json", literature_ledger())
    write_json(PACKAGE / "source_bindings.json", source_bindings())
    full_failures = [
        "tests/legacy/test_pneuma_mapmatch.py::test_mapmatch_package_is_sealed_and_remains_candidate_only",
        "tests/legacy/test_pneuma_mapmatch.py::test_csv_mapmatch_package_streams_wide_tracks",
        "tests/legacy/test_pneuma_qa.py::test_pneuma_manual_qa_pack_is_balanced_reviewable_and_not_a_ttc_result",
        "tests/test_formal_artifacts.py::test_manifest_rejects_a_run_missing_a_required_artifact",
        "tests/test_formal_artifacts.py::test_manifest_records_hashes_and_round_trips_all_run_artifacts",
        "tests/test_formal_artifacts.py::test_manifest_rejects_an_untracked_extra_file_after_build",
        "tests/test_formal_artifacts.py::test_manifest_rejects_non_parquet_tabular_artifacts",
        "tests/test_formal_artifacts.py::test_theory_schema_requires_source_lifecycle_and_attribution_columns",
        "tests/test_formal_artifacts.py::test_theory_schema_accepts_all_frozen_columns_even_for_an_empty_channel",
        "tests/test_formal_artifacts.py::test_stage_0_1_artifact_smoke_writes_a_sealed_theory_aligned_run",
        "tests/test_formal_artifacts.py::test_stage_0_1_artifact_smoke_cli_is_a_one_command_reproducibility_entrypoint",
        "tests/test_formal_artifacts.py::test_stage_0_1_cli_records_a_failed_rerun_without_overwriting_the_first_run",
        "tests/test_formal_artifacts.py::test_stage_0_1_contract_fixture_writes_four_nonempty_theory_audited_runs",
        "tests/test_formal_artifacts.py::test_stage_0_1_contract_fixture_cli_is_a_one_command_nonempty_contract_entrypoint",
        "tests/test_ngsim_risk_calibration.py::test_stage_0_2_package_reads_only_requested_calibration_member",
        "tests/test_simulation_real_coverage.py::test_real_reference_package_propagates_pneuma_quality_fields",
        "tests/test_simulation_real_coverage.py::test_real_reference_package_keeps_pneuma_risk_pending",
        "tests/test_simulation_real_coverage.py::test_canonical_pneuma_schema_is_consumed_directly_and_preserved",
        "tests/test_simulation_real_coverage.py::test_canonical_pneuma_quality_contract_is_fail_closed",
        "tests/test_simulation_real_coverage.py::test_legacy_pneuma_schema_requires_explicit_mode",
        "tests/test_simulation_real_coverage.py::test_sealed_stage_0_3_canonical_parquet_directly_reaches_writer",
        "tests/test_stage_0_1_sumo.py::test_real_sumo_stage_0_1_seals_nonempty_four_cell_package_and_read_only_audit",
        "tests/test_stage_0_2_task_2_5_threshold_validation.py::test_confirmation_is_causal_and_delayed",
        "tests/test_stage_0_5_boundary_bottleneck.py::test_synthetic_parquet_metadata_roundtrip_under_guard",
        "tests/test_stage_0_5_calibration_gaps.py::test_benchmark_plan_is_bounded_and_preserves_loads_before_simulation",
        "tests/test_stage_0_5_d1_measurement.py::test_actual_state_runner_uses_d1_not_point_exposure",
        "tests/test_stage_0_5_measurement_equivalence.py::test_guard_denies_row_scoped_reads_outside_the_calibration_windows",
        "tests/test_stage_0_5_measurement_equivalence.py::test_calibration_states_read_helper_refuses_a_foreign_window",
        "tests/test_stage_0_5_sumo.py::test_sumo_baseline_engineering_run_is_sealed_and_contract_complete",
        "tests/test_stage_0_5_sumo.py::test_sumo_probe_fixture_confirms_a_p2_event_in_both_adapters",
        "tests/test_stage_0_5_sumo.py::test_sumo_run_is_reproducible_for_the_same_seed_and_config",
        "tests/test_stage_0_5_sumo.py::test_sumo_internal_and_recorded_steps_are_separately_configurable",
        "tests/test_stage_0_5_sumo.py::test_sumo_warmup_window_is_respected_and_unbuilt_scenarios_are_refused",
        "tests/test_stage_0_5_sumo.py::test_sumo_smoke_runs_never_change_the_stage_gate",
        "tests/test_stage_0_6_error_budget_v1.py::test_observed_sensitivity_reports_missing_and_boundary_support",
    ]
    validation = {
        "schema_version": "aad.stage0.5.round2.task2.validation.v1",
        "synthetic_case_count": len(outputs),
        "all_cases_have_three_rule_outputs": all(set(x["candidate_rules"]) == {"A_strict_native_lane", "B_connected_boundary", "C_pair_time_continuity"} for x in outputs),
        "negative_ttc_rejection_visible": any(x["case"] == "non_positive_ttc_input" and x["formal_aligned"]["error"] for x in outputs),
        "lane_rule_divergence_visible": any(x["case"] == "native_lane_id_change_no_connection" and (
            x["candidate_rules"]["A_strict_native_lane"]["exposure_s"] != x["candidate_rules"]["C_pair_time_continuity"]["exposure_s"] or
            x["candidate_rules"]["A_strict_native_lane"]["events"] != x["candidate_rules"]["C_pair_time_continuity"]["events"])
            for x in outputs),
        "connected_boundary_rule_visible": any(x["case"] == "connected_road_boundary" and x["candidate_rules"]["B_connected_boundary"]["event_count"] == 1 for x in outputs),
        "formal_equivalence_accepted": False,
        "new_native_launches": 0,
        "new_trajectories": 0,
        "holdout_reads": 0,
        "full_text_attachments_created": 0,
        "status": "PASS_FOR_OFFLINE_CONTRACT_AUDIT_WITH_SCIENTIFIC_DECISION_PENDING",
        "full_pytest": {"passed": 1416, "failed": len(full_failures), "skipped": 4, "failure_cause": "missing pyarrow/fastparquet Parquet engine in every recorded failure traceback", "sumo_home_warning": True},
        "targeted_measurement_tests": {"passed": 62, "failed": 2, "failure_cause": "missing pyarrow/fastparquet"},
        "project_docs_tests": {"passed": 13, "failed": 0},
        "compileall": {"status": "passed", "cache": "isolated writable PYTHONPYCACHEPREFIX"},
        "limitations": ["No production rule was changed.", "Synthetic fixtures cannot prove physical path truth or formal scientific equivalence.", "The parent diagnostic's 28 dependency failures remain historical; this task's independent full regression recorded 35 dependency failures and preserves the complete inventory.", "Literature PDFs were not downloaded because outbound sockets are blocked in this execution environment."],
    }
    write_json(PACKAGE / "full_pytest_failure_inventory.json", {"schema_version": "aad.stage0.5.round2.task2.pytest-failures.v1", "command_scope": "code: python -m pytest -q", "common_traceback_cause": "missing pyarrow/fastparquet Parquet engine", "failures": full_failures})
    write_json(PACKAGE / "validation_record.json", validation)
    package_hashes()
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
