"""Offline R0 only: bind accepted A03, audit full context, prepare proposals.

No simulator, ledger, authorization, protocol lock or scientific Gate is written.
The CLI refuses an existing packet destination. Identical candidate input bytes
may be reused read-only. All new controls remain Proposed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
TASK = "AAD-S0.5-R0-20261028"
RESULT = "RES-STAGE-0.5-R0-DESIGN-PACKET-20261028"
RUN = "WEEK_0750_B00_IC1_s20261201_A03"
WEEK = Path("evidence/results/RES-AAD-WEEK-20261027-V1")
RAW = Path("code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs") / RUN
ENTRY = Path("docs/audits/stage_0_5_r0_20261028_v1/entry_baseline.json")
PROPOSAL = Path("evidence/admission/AAD-WEEK-2026-10-27-TO-STAGE-I-V1/candidate-v3/proposal.json")
CANDIDATE = Path("evidence/admission") / TASK / "candidate-v1"
OUTPUT = Path("code/outputs/formal/calibration/stage_0_5_r0_20261028_v2/portable")
LANES = [f"main_2_{i}" for i in range(5)]
BASE_SCHEDULE = [dict(start_s=0, end_s=420, speed_mps=10)]
PULSE_SCHEDULE = [dict(start_s=0, end_s=180, speed_mps=10),
                  dict(start_s=180, end_s=240, speed_mps=5),
                  dict(start_s=240, end_s=420, speed_mps=10)]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked(root, relative, expected, verified):
    path = root / relative
    require(path.is_file(), "BLOCKED_MISSING_FULL_CONTEXT_EVIDENCE:" + str(relative))
    actual = sha(path)
    require(actual == expected, "binding_hash_drift:" + str(relative))
    verified[Path(relative).as_posix()] = actual
    return path


def ramp_candidate(source_bytes):
    """Existing policy-A algorithm, explicitly Proposed, never actual insertion.

    Original (depart,id) order in each 60s block -> [20,25]s by endpoint
    interpolation; Python ties-to-even rounding onto the native .05s grid.
    XML vehicle elements are globally sorted by (new declared depart,id).
    """
    root = ET.fromstring(source_bytes)
    vehicles = root.findall("vehicle")
    before = {v.get("id"): dict(v.attrib) for v in vehicles}
    require(len(before) == len(vehicles), "duplicate_vehicle_id")
    groups = {}
    for v in vehicles:
        if v.get("route") == "entering" and not v.get("id").startswith("i"):
            depart = float(v.get("depart"))
            require(math.isfinite(depart) and 0 <= depart < 420, "illegal_depart")
            groups.setdefault(int(depart // 60), []).append(v)
    records = []
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    for block, group in sorted(groups.items()):
        group.sort(key=lambda v: (float(v.get("depart")), v.get("id")))
        for rank, v in enumerate(group):
            raw = block * 60 + 20 + (5 * rank / (len(group) - 1) if len(group) > 1 else 0)
            candidate = round(raw / .05) * .05
            original = float(v.get("depart"))
            v.set("depart", f"{candidate:.2f}")
            records.append(dict(vehicle_id=v.get("id"), original_depart=original,
                block_id=block, block_start_s=block * 60, candidate_depart_s=float(v.get("depart")),
                candidate_offset_s=float(v.get("depart")) - block * 60, block_rank=rank,
                source_input_sha256=source_hash, status="Proposed"))
    for v in vehicles:
        root.remove(v)
    root.extend(sorted(vehicles, key=lambda v: (float(v.get("depart")), v.get("id"))))
    data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return data, records, compare_routes(source_bytes, data, allow_ramp=True)


def compare_routes(before_bytes, after_bytes, *, allow_ramp):
    a, b = ET.fromstring(before_bytes), ET.fromstring(after_bytes)
    # All nonvehicle children, including every vType and route, are invariant.
    def nonvehicles(tree):
        return [ET.tostring(x) for x in tree if x.tag != "vehicle"]
    require(nonvehicles(a) == nonvehicles(b), "extra_nonvehicle_delta")
    old = {v.get("id"): dict(v.attrib) for v in a.findall("vehicle")}
    new = {v.get("id"): dict(v.attrib) for v in b.findall("vehicle")}
    require(len(new) == len(b.findall("vehicle")), "duplicate_vehicle_id")
    require(old.keys() == new.keys(), "vehicle_identity_delta")
    old_children = {v.get("id"): [ET.tostring(x) for x in v] for v in a.findall("vehicle")}
    new_children = {v.get("id"): [ET.tostring(x) for x in v] for v in b.findall("vehicle")}
    require(old_children == new_children, "extra_vehicle_child_delta")
    changed = []
    old_blocks, new_blocks = Counter(), Counter()
    for vid, attrs in old.items():
        candidate = new[vid]
        is_ramp = attrs.get("route") == "entering" and not vid.startswith("i")
        if is_ramp:
            old_blocks[int(float(attrs["depart"]) // 60)] += 1
            new_blocks[int(float(candidate["depart"]) // 60)] += 1
        if attrs != candidate:
            require(allow_ramp and is_ramp, "unallowed_vehicle_delta:" + vid)
            require({k: v for k, v in attrs.items() if k != "depart"} ==
                    {k: v for k, v in candidate.items() if k != "depart"}, "extra_attribute_delta:" + vid)
            t = float(candidate["depart"])
            block = int(float(attrs["depart"]) // 60)
            require(0 <= t < 420 and int(t // 60) == block and 20 <= t - block * 60 <= 25,
                    "candidate_depart_outside_contract:" + vid)
            require(abs(t / .05 - round(t / .05)) < 1e-8, "depart_off_grid")
            changed.append(vid)
    require(old_blocks == new_blocks, "ramp_block_count_delta")
    for block in old_blocks:
        ids = [v for v in old if old[v].get("route") == "entering" and not v.startswith("i")
               and int(float(old[v]["depart"]) // 60) == block]
        require(sorted(ids, key=lambda v: (float(old[v]["depart"]), v)) ==
                sorted(ids, key=lambda v: (float(new[v]["depart"]), v)), "block_order_delta")
    require([(float(v.get("depart")), v.get("id")) for v in b.findall("vehicle")] ==
            sorted((float(v.get("depart")), v.get("id")) for v in b.findall("vehicle")), "xml_not_depart_sorted")
    return dict(verified=True, vehicle_count=len(old), initial_count=sum(x.startswith("i") for x in old),
        ramp_count=sum(old_blocks.values()), changed_departures=len(changed), changed_vehicle_ids=changed,
        blocks=dict(sorted(old_blocks.items())), nonvehicle_elements_equal=True,
        other_vehicle_attributes_equal=True, within_block_order_preserved=True,
        serialization="Global vehicle XML order is (candidate declared depart,vehicle_id); not observed insertion order")


def validate_arms(arms, baseline):
    require([a["arm"] for a in arms] == ["B00", "B10", "B01", "B11"], "arm_set_or_order")
    for arm, supply, ramp in [("B00", False, False), ("B10", True, False), ("B01", False, True), ("B11", True, True)]:
        a = next(x for x in arms if x["arm"] == arm)
        require(a["execution_allowed"] is False, "R0_cannot_authorize_launch")
        require(a["factors"] == dict(supply=supply, ramp=ramp), "extra_or_wrong_factor")
        for field, value in dict(seed=20261201, duration_s=420, internal_step_s=.05,
                                 recording_step_s=.1, evaluation_window_s=[120, 390], supply_target_lanes=LANES).items():
            require(a[field] == value, "unallowed_arm_delta:" + field)
        require(a["lane_speed_schedule"] == (PULSE_SCHEDULE if supply else BASE_SCHEDULE), "unallowed_speed_schedule")
        expected_inputs = dict(baseline["input_files"])
        if ramp:
            expected_inputs["routes.rou.xml"] = (CANDIDATE / "ramp_routes.rou.xml").as_posix()
        require(a["input_files"] == expected_inputs, "unallowed_input_delta")
    return True


def verify_packet(root=ROOT, *, require_local=False):
    root = Path(root)
    packet = root / "evidence/results" / RESULT
    manifest = load(packet / "manifest.json")
    missing_local = []
    for name, expected in manifest["output_sha256"].items():
        require(sha(packet / name) == expected, "packet_output_drift:" + name)
    for field in ["source_sha256", "candidate_input_sha256", "input_sha256", "offline_validation_record_sha256"]:
        for name, expected in manifest.get(field, {}).items():
            p = root / name
            if p.is_file():
                require(sha(p) == expected, "packet_bound_file_drift:" + name)
            else:
                require(field == "input_sha256" and name.startswith("code/outputs/"), "missing_required_file:" + name)
                missing_local.append(name)
    require(not require_local or not missing_local, "missing_local_accepted_evidence")
    for line in (packet / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        require(sha(packet / name) == expected, "packet_SHA256SUMS_drift:" + name)
    baseline = load(packet / "baseline_binding.json")
    arms = load(packet / "arm_input_candidates.json")["arms"]
    validate_arms(arms, baseline)
    before = (root / baseline["input_files"]["routes.rou.xml"]).read_bytes()
    after = (root / CANDIDATE / "ramp_routes.rou.xml").read_bytes()
    _, records, _ = ramp_candidate(before)
    import csv
    with (packet / "ramp_departure_map_candidate.csv").open(encoding="utf-8", newline="") as f:
        mapped = list(csv.DictReader(f))
    require(len(records) == len(mapped) == 60, "ramp_mapping_count")
    for expected, actual in zip(records, mapped):
        require({k: str(v) for k, v in expected.items()} == actual, "ramp_mapping_drift")
    regenerated, _, _ = ramp_candidate(before)
    require(after == regenerated, "nondeterministic_or_changed_ramp_candidate")
    for a in arms:
        for name, path in a["input_files"].items():
            require(sha(root / path) == a["input_sha256"][name], "arm_input_hash_drift")
    gate = load(packet / "r0_gate_report.json")
    require(gate["R1_execution_allowed"] is False and gate["new_SUMO_launches"] == 0, "R0_execution_boundary")
    registry = load(root / "docs/PROJECT_REGISTRY.json")
    current = {e["id"]: e["gate"] for e in registry["experiments"] if e["id"] in gate["scientific_gate_snapshot_unchanged"]}
    require(current == gate["scientific_gate_snapshot_unchanged"], "scientific_Gate_drift")
    return dict(status="Pass", portable_hashes_and_candidates=True,
                local_baseline_complete=not missing_local, absent_local_outputs=len(missing_local), new_SUMO_launches=0)


def complete_topology_audit(root=ROOT):
    """Append the offline topology review before first export; retain prior seal hash.

    No trajectory measurement is repeated. The new file is exclusive and this
    completion step refuses repetition; only this task's unexported draft seal
    is refreshed. Accepted B00 and candidate route bytes are read-only.
    """
    root = Path(root).resolve()
    out = root / OUTPUT
    guard = offline_guard([out])
    require(not (out / "topology_candidate_audit.json").exists(), "topology_audit_already_completed")
    baseline = load(out / "baseline_binding.json")
    source = load(out / "source_target_candidates.json")
    previous = load(out / "manifest.json")
    for name, digest in previous["output_sha256"].items():
        require(sha(out / name) == digest, "pre_completion_packet_drift:" + name)
    edges = baseline["network_edges"]
    successor = {e["id"]: sorted({c["to"] for c in baseline["network_connections"] if c["from"] == e["id"]}) for e in edges}
    def path(start, end):
        queue = [[start]]
        seen = {start}
        while queue:
            p = queue.pop(0)
            if p[-1] == end:
                return p
            for nxt in successor.get(p[-1], []):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(p + [nxt])
        return None
    rows = []
    for spec in source["source_candidates"]:
        paths = {target: path(spec["edges"][0], target) for target in ["main_0", "main_1"]}
        rows.append(dict(source_candidate=spec["id"], target_candidate="lanes1-5 y[150,350)",
            road_travel_edge_paths=paths, road_travel_reachable=any(paths.values()),
            road_scope="edge-level only; source and target physical lane/position qualification still required",
            native_lane_qualification=("onramp_0 connects to main_1_0 auxiliary, outside target lanes; observed later lane change is required" if spec["id"] == "S_ONRAMP" else
                                       "same-edge longitudinal order or verified native lane connection required"),
            influence_reachability="Uncertain: no P2 source witness; contemporaneous leader->follower chain is distinct from forward road travel",
            downstream_source_note=("No forward road path from main_2 to upstream target; this is not proof of absence of upstream leader/follower influence" if spec["id"] == "S_DOWNSTREAM_MAIN" else None),
            actual_earliest_physical_arrival_s=None, reason="No confirmed source event in B00; no source/target pair chosen",
            status="Verified road paths / Proposed influence qualification"))
    write(out / "topology_candidate_audit.json", dict(status="Verified offline topology; scientific arrival rule pending",
        network_sha256=baseline["input_sha256"]["network.net.xml"], successor_edges=successor, candidates=rows,
        source_target_definition_file="source_target_candidates.json", no_message_time_used=True,
        gap_and_identity_policy=source["physical_path"]["statuses"],
        prior_unexported_manifest_sha256=sha(out / "manifest.json"), no_measurement_reexecution=True, guard=guard))
    previous["source_sha256"] = {name:sha(root/name) for name in previous["source_sha256"]}
    previous["output_sha256"] = {p.name:sha(p) for p in sorted(out.iterdir()) if p.name not in ["manifest.json", "SHA256SUMS"]}
    previous["completion"] = "One exclusive offline topology appendix, no source-event remeasurement or simulation"
    (out / "manifest.json").write_text(json.dumps(previous, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    (out / "SHA256SUMS").write_text("".join(sha(p) + "  " + p.name + "\n" for p in sorted(out.iterdir()) if p.name != "SHA256SUMS"), encoding="utf-8", newline="\n")
    print(json.dumps(dict(topology_appendix="Pass", final_manifest_sha256=sha(out/"manifest.json"), new_SUMO_launches=0)))


def seal_validation(root=ROOT):
    """Bind completed offline software checks once, before final commit/export."""
    root = Path(root).resolve()
    out = root / OUTPUT
    offline_guard([out])
    path = Path("docs/audits/stage_0_5_r0_20261028_v1/final_validation.json")
    record = load(root/path)
    require(record["status"] == "Pass" and record["new_SUMO_launches"] == 0, "offline_validation_not_passed")
    require(all(x == "Pass" for x in record["checks"].values()), "offline_check_not_passed")
    validation = load(out/"validation_record.json")
    require("final_validation_sha256" not in validation, "validation_already_sealed")
    validation["final_validation_sha256"] = sha(root/path)
    validation["final_validation_path"] = path.as_posix()
    validation["software_checks"] = record["checks"]
    validation["targeted_tests"] = record["targeted_tests"]
    validation["full_software_tests"] = record["full_software_tests"]
    (out/"validation_record.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    manifest = load(out/"manifest.json")
    names = set(manifest["source_sha256"]) | {"code/scripts/export_project_evidence.py", "code/scripts/validate_stage_0_5_research_v2.py"}
    manifest["source_sha256"] = {n:sha(root/n) for n in sorted(names)}
    manifest["offline_validation_record_sha256"] = {path.as_posix():sha(root/path)}
    manifest["output_sha256"] = {p.name:sha(p) for p in sorted(out.iterdir()) if p.name not in ["manifest.json", "SHA256SUMS"]}
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    (out/"SHA256SUMS").write_text("".join(sha(p)+"  "+p.name+"\n" for p in sorted(out.iterdir()) if p.name!="SHA256SUMS"),encoding="utf-8",newline="\n")
    print(json.dumps(dict(validation_sealed=True,final_manifest_sha256=sha(out/"manifest.json"),new_SUMO_launches=0)))


def source_specs():
    # Geometry-based candidates, fixed before inspecting P2 outcomes. No selected arm.
    return [dict(id="S_UPSTREAM_MAIN", edges=["main_0"], lanes=["1", "2", "3", "4", "5"],
                 y_m=[0, 150], spatially_disjoint_from_target=True),
            dict(id="S_DOWNSTREAM_MAIN", edges=["main_2"], lanes=["1", "2", "3", "4", "5"],
                 y_m=[399.22, 669.18], spatially_disjoint_from_target=True),
            dict(id="S_ONRAMP", edges=["onramp"], lanes=["7"], y_m=None,
                 spatially_disjoint_from_target=True)]


def input_route_cohort(source_bytes):
    """Pre-treatment eligibility only; no actual P2, rho or entry outcomes."""
    tree = ET.fromstring(source_bytes)
    routes = {r.get("id"): set(r.get("edges").split()) for r in tree.findall("route")}
    included, excluded = [], []
    for v in tree.findall("vehicle"):
        require(v.get("route") in routes, "unresolved_input_route")
        (included if routes[v.get("route")] & {"main_0", "main_1"} else excluded).append(v.get("id"))
    included.sort()
    excluded.sort()
    return dict(declared_ID_count=len(included), initial_ID_count=sum(x.startswith("i") for x in included),
        noninitial_ID_count=sum(not x.startswith("i") for x in included),
        included_sorted_IDs_sha256=hashlib.sha256(("\n".join(included) + "\n").encode()).hexdigest(),
        route_only_excluded_count=len(excluded), route_only_excluded_IDs=excluded,
        exclusion_reason="Fixed input route contains neither main_0 nor main_1; cannot traverse proposed target; no outcome used",
        source_input_sha256=hashlib.sha256(source_bytes).hexdigest())


def region_mask(frame, spec):
    mask = frame.edge_id.isin(spec["edges"]) & frame.lane_id.astype(str).isin(spec["lanes"])
    if spec["y_m"] is not None:
        mask &= frame.y_m.ge(spec["y_m"][0]) & frame.y_m.lt(spec["y_m"][1])
    return mask


def audit_full_context(frame):
    """Call the existing P2 implementation on ALL rows before any attribution.

    Generic edge summaries use identical both-end D1 qualification; they do not
    alter the formal local implementation or assert cross-junction observations.
    """
    import numpy as np
    import pandas as pd
    from riskprop.stage_0_5_d1_measurement import local_d1_measurement
    d = frame.copy()
    d["edge_id"] = d.native_lane_id.str.rsplit("_", n=1).str[0]
    all_measure = local_d1_measurement(d, (0, 420), region=(0, 669.18), strict=True)
    local = local_d1_measurement(d, (120, 390), strict=True)
    keys = ["run_id", "scenario_id", "vehicle_id", "incarnation_id"]
    ordered = d.sort_values(keys + ["time_s"], kind="stable").reset_index(drop=True)
    p = ordered.shift()
    identity = lambda x: x.notna() & ~x.astype(str).isin(["", "None", "nan", "<NA>"])
    resolved = identity(ordered.leader_id) & identity(ordered.leader_incarnation_id)
    adjacent = resolved & resolved.shift(fill_value=False)
    for k in keys + ["leader_id", "leader_incarnation_id", "native_lane_id"]:
        adjacent &= ordered[k].eq(p[k])
    adjacent &= ordered.time_s.sub(p.time_s).sub(.1).abs().le(1e-9)
    for flag in ["identity_break", "observation_gap"]:
        if flag in ordered:
            adjacent &= ordered[flag].eq(False) & p[flag].eq(False)
    valid = ordered.measurement_status.isin(["valid", "not_applicable"])
    evaluable = adjacent & valid & valid.shift(fill_value=False)
    evaluable &= ordered.reliable_following_eligible & ordered.reliable_following_eligible.shift(fill_value=False)
    risk = ordered.reliable_following_eligible & ordered.ttc_valid & ordered.measurement_status.eq("valid")
    risk &= ordered.ttc_s.gt(0) & ordered.ttc_s.lt(2)
    # Independent scalar segmentation checks the official full-context event list.
    segments, current = [], []
    for idx in np.flatnonzero(risk.to_numpy()):
        if current and not (idx == current[-1] + 1 and bool(adjacent.iloc[idx])):
            segments.append(current)
            current = []
        current.append(int(idx))
    if current:
        segments.append(current)
    confirmed = []
    incomplete = []
    for indices in segments:
        g = ordered.iloc[indices]
        onset = float(g.time_s.iloc[0])
        confirmations = g.loc[g.time_s.sub(onset).ge(.2 - 1e-9)]
        if confirmations.empty:
            last = indices[-1]
            next_usable = last + 1 < len(ordered) and bool(adjacent.iloc[last + 1]) and bool(valid.iloc[last + 1])
            incomplete.append(dict(vehicle_id=str(g.vehicle_id.iloc[0]), leader_id=str(g.leader_id.iloc[0]),
                onset_s=onset, last_s=float(g.time_s.iloc[-1]),
                status="observed_short_risk" if next_usable else "right_censored_unconfirmed"))
        else:
            confirmed.append((str(g.vehicle_id.iloc[0]), str(g.leader_id.iloc[0]), onset, float(confirmations.time_s.iloc[0])))
    official = [(e["vehicle_id"], e["leader_id"], e["onset_s"], e["confirm_s"]) for e in all_measure["events"]]
    require(confirmed == official, "independent_full_context_event_mismatch")
    indexed = d.set_index(["vehicle_id", "time_s"], verify_integrity=True)
    events = []
    for event in all_measure["events"]:
        first = indexed.loc[(event["vehicle_id"], event["onset_s"])]
        confirm = indexed.loc[(event["vehicle_id"], event["confirm_s"])]
        events.append(dict(event, onset_position_m=float(first.y_m), confirmation_position_m=float(confirm.y_m),
            onset_native_lane=str(first.native_lane_id), confirmation_native_lane=str(confirm.native_lane_id),
            onset_edge=str(first.edge_id), incarnation_id=str(first.incarnation_id),
            leader_incarnation_id=str(first.leader_incarnation_id),
            observation_quality="both-end reliable; same follower/leader incarnation and native lane; contiguous100ms",
            maximum_adjacent_gap_s=.1, first_confirmation_is_actual_observation=True,
            source_attribution=[s["id"] for s in source_specs() if
                bool(region_mask(pd.DataFrame([first]), s).iloc[0]) and 120 <= event["onset_s"] < 390]))
    def support(mask, window):
        low, high = window
        time_mask = ordered.time_s.ge(low) & ordered.time_s.lt(high)
        edges = evaluable & mask & mask.shift(fill_value=False) & p.time_s.ge(low - 1e-9) & ordered.time_s.le(high + 1e-9)
        selected = ordered.loc[mask & time_mask]
        return dict(observed_states=len(selected), observed_vehicle_count=int(selected.vehicle_id.nunique()),
            D1_E_veh_s=float(edges.sum()) * .1, D1_links=int(edges.sum()),
            measurement_status=selected.measurement_status.value_counts().to_dict(),
            physical_support_status=selected.physical_support_status.value_counts().to_dict(),
            missing_points=int(selected.measurement_status.eq("missing").sum()),
            invalid_points=int(selected.measurement_status.eq("invalid").sum()),
            without_reliable_following_points=int((~selected.reliable_following_eligible).sum()))
    candidates = []
    for spec in source_specs():
        member_ids = [e["event_id"] for e in events if spec["id"] in e["source_attribution"]]
        candidates.append(dict(spec, window_s=[120, 390], status="Proposed", P2_onset_count=len(member_ids),
            event_ids=member_ids, support=support(region_mask(ordered, spec), (120, 390)),
            source_event_support="Verified present" if member_ids else "Verified no confirmed event in observed eligible context",
            source_vehicle_selection="No vehicle ID selected from outcomes"))
    finite_ttc = d.loc[d.reliable_following_eligible & d.ttc_valid & d.measurement_status.eq("valid"), "ttc_s"]
    full_support = support(pd.Series(True, index=ordered.index), (0, 420))
    full_support["scope"] = "Diagnostic same-native-lane both-end reliable exposure over all recorded lanes; not a new frozen global D1 estimand. Approved local D1 stays9778.4veh-s."
    return dict(schema="aad.r0.full-context-source-support.v1", status="Verified",
        rule=dict(TTC_strictly_below_s=2, minimum_observed_span_s=.2, maximum_allowed_gap_s=.11,
                  native_record_grid_s=.1, confirmation="first actual observation attaining .2s; not onset+.2 synthetic clock",
                  attribution="full-context extraction, then onset position and onset time; confirmation retained for sensitivity"),
        full_context=dict(rows=len(d), vehicles=int(d.vehicle_id.nunique()), time_s=[float(d.time_s.min()), float(d.time_s.max())],
                          recording_times=int(d.time_s.nunique()), P2_events=len(events),
                          risk_points=int(risk.sum()), minimum_valid_reliable_TTC_s=float(finite_ttc.min()) if len(finite_ttc) else None,
                          support=full_support),
        events=events, incomplete_candidates=incomplete, candidate_regions=candidates,
        independent_event_reconstruction=dict(pass_=True, event_count=len(confirmed),
            method="independent contiguous risk-run scan compared with official full-context event identities/times"),
        existing_target_local_measurement={k: v for k, v in local.items() if k not in ["events", "incomplete_candidates"]},
        source_diagnosis_supported=bool(events),
        interpretation="Observed eligible trajectories only. Missing same-lane/junction support is not zero risk. No claim about unobserved pairs or future treated arms.",
        boundary="An empty confirmed-event list does not establish absence of physical hazards or scientific equivalence; no source-specific tau_p can be assigned without an event.")


def offline_guard(output_roots):
    """Task-owned Python operations: no external processes/network/native import.

    This is an audit of this offline builder, not a claim of OS isolation.
    """
    audit = dict(process_attempts=[], network_attempts=[], forbidden_imports=[], external_writes=[], sumo_launches=0)
    roots = [Path(p).resolve() for p in output_roots]
    def hook(event, args):
        if event in ["subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn"]:
            audit["process_attempts"].append(event)
            raise PermissionError("R0 forbids process launch")
        if event in ["socket.connect", "socket.bind"]:
            audit["network_attempts"].append(event)
            raise PermissionError("R0 forbids network/TraCI connection")
        if event == "import" and str(args[0]).split(".")[0] in ["traci", "libsumo"]:
            audit["forbidden_imports"].append(str(args[0]))
            raise PermissionError("R0 forbids native simulation adapters")
        if event == "open" and isinstance(args[0], (str, bytes)):
            mode, flags = args[1], args[2]
            writing = isinstance(mode, str) and any(x in mode for x in "wax+")
            writing |= isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if writing and not any(Path(os.fsdecode(args[0])).resolve().is_relative_to(p) for p in roots):
                audit["external_writes"].append(os.fsdecode(args[0]))
                raise PermissionError("R0 write outside new destinations")
    sys.dont_write_bytecode = True
    sys.addaudithook(hook)
    return audit


def prepare(root=ROOT):
    root = Path(root).resolve()
    out, candidate = root / OUTPUT, root / CANDIDATE
    require(not out.exists(), "immutable_destination_already_exists")
    guard = offline_guard([out, candidate])
    sys.path.insert(0, str(root / "code/src"))
    import pandas as pd
    from riskprop.stage_0_5_scene_reconstruction import parse_fcd, network_edge_lengths, REAL_SPAN_M
    entry, prov, accepted = load(root / ENTRY), load(root / WEEK / "provenance.json"), load(root / WEEK / "audit.json")
    verified = {}
    for name, digest in entry["accepted_package_files"].items():
        checked(root, WEEK / name, digest, verified)
    proposal = load(checked(root, PROPOSAL, prov["native_execution_proposal_sha256"], verified))
    run = proposal["runs"][0]
    require(run["id"] == RUN and accepted["run_id"] == RUN and accepted["status"] == "B00_EXECUTED_MEASUREMENT_ACCEPTED", "wrong_baseline")
    require(all(accepted["checks"].values()), "accepted_checks_not_passed")
    for name, digest in prov["input_sha256"].items():
        checked(root, RAW / name, digest, verified)
        checked(root, Path(run["input_files"][name]), digest, verified)
    for name, digest in prov["raw_artifact_sha256"].items():
        checked(root, RAW / name, digest, verified)
    measured = entry["derived_measured_state"]
    checked(root, Path(measured["path"]), measured["sha256"], verified)
    checked(root, RAW / "isolation_runtime.json", prov["source_file_sha256"][(RAW / "isolation_runtime.json").as_posix()], verified)
    for name, digest in prov["native_controller_source_sha256"].items():
        checked(root, Path("code/scripts") / name, digest, verified)
    # Only the task-relevant current analyzer closure; no Stage0.6 data reads.
    for name in ["code/scripts/analyze_stage_0_5_week_scene_v1.py", "code/scripts/assess_stage_0_5_existing_capsule_v1.py"]:
        checked(root, Path(name), prov["source_file_sha256"][name], verified)
    measurement_proposal_path = Path("evidence/admission/AAD-WEEK-2026-10-27-TO-STAGE-I-V1/candidate-v4-measurement/proposal.json")
    measurement_proposal = load(checked(root, measurement_proposal_path,
        prov["source_file_sha256"][measurement_proposal_path.as_posix()], verified))
    for name in ["code/src/riskprop/stage_0_5_d1_measurement.py", "code/src/riskprop/stage_0_5_scene_reconstruction.py",
                 "code/src/riskprop/stage_0_5_state_support.py", "code/src/riskprop/stage_0_5_sumo.py"]:
        expected = measurement_proposal.get("assessment_source_sha256", {}).get(name) or proposal["source_sha256"][name]
        checked(root, Path(name), expected, verified)
    executed = Path("docs/audits/aad_week_20261027/a03_executed_coordinator_source.py")
    checked(root, executed, load(root / WEEK / "failure_archive.json")["A03_coordinator_failure"]["source_snapshot_sha256"], verified)
    # Frozen constants must come from actual run/proposal/receipt, not a plan.
    require(run["seed"] == 20261201 and run["duration_s"] == 420 and run["internal_step_s"] == .05 and
            run["evaluation_elapsed_s"] == [120, 390] and run["supply_target_lanes"] == LANES and
            run["lane_speed_schedule"] == BASE_SCHEDULE, "baseline_design_drift")
    config = ET.parse(root / RAW / "run.sumocfg").getroot()
    config_values = {x.tag: dict(x.attrib) for x in config.iter() if "value" in x.attrib}
    network = ET.parse(root / RAW / "network.net.xml").getroot()
    routes_path = root / RAW / "routes.rou.xml"
    source_bytes = routes_path.read_bytes()
    routes = ET.fromstring(source_bytes)
    vehicle_ids = [v.get("id") for v in routes.findall("vehicle")]
    require(len(vehicle_ids) == 1150 and sum(x.startswith("i") for x in vehicle_ids) == 117, "baseline_population_drift")
    require(float(config_values["device.fcd.period"]["value"]) == .1, "recording_contract_drift")
    require(config_values["seed"]["value"] == "20261201", "config_seed_drift")
    # First tangible output: immutable candidate input, with no runnable envelope.
    out.mkdir(parents=True)
    ramp_bytes, mapping, ramp_diff = ramp_candidate(source_bytes)
    require(ramp_diff["ramp_count"] == 60 and len(mapping) == 60, "expected60_ramp_vehicles")
    if candidate.exists():
        require(sorted(p.name for p in candidate.iterdir()) == ["ramp_routes.rou.xml"] and
                (candidate / "ramp_routes.rou.xml").read_bytes() == ramp_bytes, "existing_candidate_input_drift")
    else:
        candidate.mkdir(parents=True)
        with (candidate / "ramp_routes.rou.xml").open("xb") as f:
            f.write(ramp_bytes)
    import csv
    with (out / "ramp_departure_map_candidate.csv").open("x", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(mapping[0]))
        writer.writeheader()
        writer.writerows(mapping)
    arms = []
    for arm, supply, ramp in [("B00", False, False), ("B10", True, False), ("B01", False, True), ("B11", True, True)]:
        inputs = dict(run["input_files"])
        if ramp:
            inputs["routes.rou.xml"] = (CANDIDATE / "ramp_routes.rou.xml").as_posix()
        arms.append(dict(arm=arm, status="Verified accepted evidence reused" if arm == "B00" else "Proposed",
            execution_allowed=False, seed=run["seed"], duration_s=420, internal_step_s=.05, recording_step_s=.1,
            evaluation_window_s=[120, 390], input_files=inputs,
            input_sha256={k: sha(root / v) for k, v in inputs.items()},
            factors=dict(supply=supply, ramp=ramp), supply_target_lanes=LANES,
            lane_speed_schedule=PULSE_SCHEDULE if supply else BASE_SCHEDULE,
            controller="NativeBackend.before_step: lane.setMaxSpeed then lane.getMaxSpeed on every native step",
            control_semantics="Road lane maxSpeed only. At t180 apply5 before step180->180.05; at t240 restore10 before step240->240.05. Native vehicles entering/leaving/changing lanes follow current lane maxSpeed; no per-vehicle override or forced instantaneous actual speed. Preserve car-following/vehicle limits; future receipt must record set/get plus actual vehicle trajectories.",
            future_output_directory="Required exclusive run directory at R1 admission; none reserved in R0",
            bound_baseline_run_id=RUN))
    validate_arms(arms, run)
    write(out / "arm_input_candidates.json", dict(schema="aad.r0.arm-candidates.v1", task_id=TASK, arms=arms,
        warning="Not an execution proposal, approval, envelope or Protocol Lock; no launch entrypoint."))
    write(out / "scenario_diff_matrix.json", dict(status="Verified candidate deltas; scientific freeze pending", arms=[
        dict(arm=a["arm"], allowed_differences=(["lane_speed_schedule"] if a["factors"]["supply"] else []) +
             (["noninitial entering vehicle declared depart; explicit XML resort"] if a["factors"]["ramp"] else []),
             route_comparison=ramp_diff if a["factors"]["ramp"] else compare_routes(source_bytes, source_bytes, allow_ramp=False),
             network_sha256=a["input_sha256"]["network.net.xml"], config_sha256=a["input_sha256"]["run.sumocfg"],
             routes_sha256=a["input_sha256"]["routes.rou.xml"], lane_speed_schedule=a["lane_speed_schedule"],
             unchanged=["117 initial vehicles including DS38/IC1", "all1150 identities/routes/types", "seed/time/grid/window", "network topology/vTypes/behaviour", "stop/observation rules"],
             unexplained_extra_differences=[]) for a in arms],
        B11_is_exact_union=True, ramp_mapping_status="Proposed", no_new_run=True,
        design_identity="Stage0.5 supply x ramp diagnosis, not StageI source x communication"))
    controller = load(root / RAW / "controller_receipt.json")
    receipt = load(root / WEEK / "independent_execution_receipt.json")
    baseline = dict(schema="aad.r0.baseline-binding.v1", status="Verified", task_id=TASK,
        repository_entry_commit=entry["actual_entry_HEAD"], origin_main_at_entry=entry["origin_main"],
        native_execution_base_commit=prov["execution_base_commit"], native_execution_dirty_source_semantics=prov["execution_dirty_sources"],
        source_roadmap=entry["roadmap"], run_id=RUN, scene_id="US-101 0750", condition=run["condition"],
        seed=run["seed"], duration_s=run["duration_s"], internal_step_s=run["internal_step_s"],
        recording_step_s=float(config_values["device.fcd.period"]["value"]), evaluation_window_s=run["evaluation_elapsed_s"],
        input_files=run["input_files"], input_sha256=run["capsule_input_sha256"], actual_config=config_values,
        network_edges=[dict(e.attrib, lanes=[dict(x.attrib) for x in e.findall("lane")]) for e in network.findall("edge") if not e.get("id").startswith(":")],
        network_connections=[dict(e.attrib) for e in network.findall("connection") if not e.get("from", "").startswith(":")],
        vehicle_types=[dict(v.attrib) for v in routes.findall("vType")], route_definitions=[dict(v.attrib) for v in routes.findall("route")],
        declared_population=dict(total=1150, initial=117, noninitial=1033, noninitial_entering=60),
        population_accounting=accepted["population"], native_controller_source_sha256=prov["native_controller_source_sha256"],
        executed_coordinator_snapshot=executed.as_posix(), executed_coordinator_sha256=sha(root / executed),
        current_analyzer="code/scripts/analyze_stage_0_5_week_scene_v1.py", accepted_analyzer_sha256=prov["source_file_sha256"]["code/scripts/analyze_stage_0_5_week_scene_v1.py"],
        runtime=dict(SUMO="1.26.0", TraCI_protocol=22, getVersion=controller["getVersion"],
                     sumo_binary_sha256=controller["sumo_binary_sha256"], traci_source_sha256=controller["traci_source_sha256"],
                     environment=proposal["environment"],
                     runtime_manifest_sha256=prov["runtime_manifest_sha256"],
                     evidence="accepted raw controller_receipt version and sealed independent execution receipt"),
        execution_receipt=receipt, accepted_execution=accepted["accepted_run"], accepted_measurement_checks=accepted["checks"],
        measured_state=measured, raw_artifact_sha256=prov["raw_artifact_sha256"], verified_bindings=verified,
        historical_run_distinction=dict(A03="Accepted only after zero-launch independent postrun measurement; original ledger rejection retained",
            A01_A02="Full420s but resource-gap acceptance failed; never substituted for A03",
            earlier_candidate_v8="Initial slow-lane-ahead failure retained; not accepted baseline",
            B10_B01_B11="Unexecuted candidates in this R0 task"))
    # Version attribution checked against the actual receipt, not assumed by label.
    require(controller["getVersion"] == [22, "SUMO 1.26.0"], "runtime_receipt_mismatch")
    write(out / "baseline_binding.json", baseline)
    d = pd.read_parquet(root / measured["path"])
    fcd = parse_fcd(root / RAW / "fcd.xml", network_edge_lengths(root / RAW / "network.net.xml"))
    fields = ["vehicle_id", "time_s", "native_lane_id", "native_position_m", "speed_mps", "y_m"]
    left = d.sort_values(["time_s", "vehicle_id"])[fields].reset_index(drop=True)
    right = fcd[fields].reset_index(drop=True)
    pd.testing.assert_frame_equal(left, right, check_dtype=False, check_exact=True)
    del fcd, left, right
    source_audit = audit_full_context(d)
    source_audit["raw_FCD_to_measured_state_crosscheck"] = dict(pass_=True, matched_rows=len(d), fields=fields,
        method="All raw FCD rows parsed by accepted coordinate adapter; exact equality before P2 extraction")
    require(source_audit["existing_target_local_measurement"]["local_evaluable_s"] == accepted["D1"]["local_evaluable_s"], "local_D1_drift")
    write(out / "source_event_support.json", source_audit)
    target = dict(status="Proposed", real_lanes=["1", "2", "3", "4", "5"], y_m=[150, 350], window_s=[120, 390],
        actual_edges=dict(main_0="mapped y [150,187.58)", main_1="mapped y [187.58,350) excluding native lane0"),
        coordinate_rule="main_0/1/2 inverse native-edge scaling via parse_fcd REAL_SPAN_M; not raw SUMO x/y or lane-pos",
        not_formal_StageI_freeze=True)
    path_rules = dict(status="Proposed / Awaiting Researcher Decision", implementation="code/src/riskprop/stage_0_1_sumo.py::analyze_physical_path_from_archived_tables",
        actual_semantics="Forward road topology precheck; same-vehicle forward-time edges; contemporaneous leader -> follower edges. tau_p is absolute earliest visited target clock, not duration or message arrival.",
        limitations=["Existing helper does not enforce max temporal gap or incarnation/leader quality; a returned path is not by itself a qualified scientific physical arrival",
                     "Forward traffic reachability precheck rejects downstream->upstream before leader influence traversal; this cannot establish that an upstream shock path is physically impossible",
                     "Internal-junction lane and native boundary leaders in A03 measured state are unresolved; no cross-edge leader imputation",
                     "No confirmed B00 P2 source exists in observed eligible context; event-specific tau_p is undefined, never filled with zero"],
        proposed_qualified_rule="Use archived incarnation-resolved, reliable both-end same-native-lane links at .1s (<=.11s), forward vehicle continuity only with verified lane connections; influence leader->follower at actual clock. Separate road reachability from influence reachability. No production change in R0.",
        statuses=dict(finite_arrival="actual connected witness, earliest target clock >= chosen source onset/confirmation clock",
                      uncertain_missing_identity="source/target missing or unresolved incarnation",
                      uncertain_missing_links="identity present but unobserved/junction/gapped leader chain; not proof of unreachable",
                      topology_disconnected="Only verified disconnection of specified directed graph, with graph type explicitly stated",
                      right_censored="No observed target witness before observation end; incomplete graph remains uncertain"),
        source_clock_candidates=["onset_s for physical-source origin; confirmation_s for usable detected source; retain both and never call message time physical"],
        actual_A03_event_specific_tau_p=None, source_event_available=bool(source_audit["events"]))
    write(out / "source_target_candidates.json", dict(status="Proposed", source_candidates=source_audit["candidate_regions"],
        target_region=target, source_vehicle_rule="All predeclared vehicles satisfying prespecified region/time and formal P2; no favorable-ID selection; exact region/cohort not frozen",
        cohort_candidates=[dict(id="C_INPUT_ROUTE", status="Proposed", primary_preferred=True,
            rule="Before treatment, include every declared ID whose fixed route has main_0 or main_1 mainline support intersecting target, including eligible117 initial and1033 noninitial as route permits. Actual target-window observations determine measurement support, never ID eligibility.",
            pre_treatment_determinable=True, **input_route_cohort(source_bytes),
            exclusions="No exclusions by P2/rho/outcome; entering route includes main_1 and exiting route includes main_0/main_1",
            missing_policy="Retain planned IDs; report native pending/undeparted/no-target-entry separately; D1 only qualified observed links, missing never zero"),
            dict(id="C_PRE_PULSE_STATE", status="Proposed", primary_preferred=False,
            rule="Fixed IDs present in prespecified region at an actual pre180s clock, same across paired arms before either manipulation; exact clock/region awaits decision",
            pre_treatment_determinable=True, declared_ID_count=None,
            limitation="Excludes later entrants and changes estimand; do not select after inspecting treatment P2 or rho")],
        cohort_qualification="Follower and leader incarnations resolved, reliable following, native lane continuity, both-end .1s observation; no valid following -> unevaluable, not zero event",
        route_geometry_map=REAL_SPAN_M, physical_path=path_rules, formal_selection=None))
    decisions = [
        ("SOURCE_REGION", "S_UPSTREAM_MAIN / S_DOWNSTREAM_MAIN / S_ONRAMP; none selected", "Geometry-separated candidates all have0 observed confirmed events; choose mechanism-relevant region before R1 outcomes"),
        ("SOURCE_CLOCK", "onset attribution primary; confirmation sensitivity; physical-origin clock vs actionable clock explicit", "Roadmap/P2: confirmation is first actual sustained observation; no message-clock substitution"),
        ("TARGET_REGION", "Existing lanes1-5 y[150,350) t[120,390) candidate", "Accepted B00 local support18/18; default implementation is not a universal frozen scientific region"),
        ("COHORT", "Prefer C_INPUT_ROUTE; alternative C_PRE_PULSE_STATE", "ID eligibility must precede treatment, report actual-entry/support separately"),
        ("PHYSICAL_PATH", "Qualified time-expanded influence witness and uncertainty rules; no helper output autoacceptance", "Archived helper direction/gap limitations documented; no source-specific B00 witness possible"),
        ("B10_CONTROL", "Existing lane.setMaxSpeed on main_2_0..4, zero-order steps [0,180):10/[180,240):5/[240,420):10", "Existing prepared schedule and NativeBackend set/get evidence; high-level pulse fixed, exact lane scope/boundary semantics await explicit freeze"),
        ("B01_COMPRESSION", "Stable (original_depart,id) endpoint interpolation [20,25] rounded ties-even to .05s", "Existing pulse_routes implementation; mathematical algorithm is Proposed, not approved by code existence"),
        ("RAMP_REALIZATION_INTERPRETATION", "Prestate how actual insertion delay, pending/undeparted and missing support limit ramp diagnostic interpretation; do not automatically use legacy90percent threshold", "Roadmap fixes the three-arm budget and all-zero-event stop already; this remaining decision concerns measurement interpretation only"),
    ]
    write(out / "decision_register.json", dict(status="AWAITING_RESEARCHER_DECISION", scientific_parameters_frozen=False,
        fixed_high_level=dict(B10="Five downstream mainline lanes10->5->10 within[180,240)", B01="Same60 noninitial ramp IDs and60s block counts; proposed20..25s compression", B11="Exact union only",
            R1_diagnostic_budget=dict(B10=1,B01=1,B11=1,additional_parameter_search=False),
            R1_stop_rule="If all three diagnostic arms lack source P2, stop; no seed/intensity search",
            formal_P2_attribution="Full context first, then onset position and onset time; confirmation sensitivity retained"),
        decisions=[dict(id=k, status="AWAITING_RESEARCHER_DECISION", candidate=c, basis=b, approved_value=None) for k,c,b in decisions],
        no_changes_to=["P2/D1", "seed/time/window", "delta_R/delta_plan/h/SESOI/alpha/n", "scientific Gates", "historical Not Accepted", "Protocol Lock"],
        source_authority=entry["roadmap"], authorization_source="Current researcher chat: offline preparation only; no asserted signature or independent identity authentication"))
    write(out / "r0_gate_report.json", dict(status="READY_FOR_RESEARCHER_REVIEW", design_freeze_status="AWAITING_RESEARCHER_DECISION",
        requirements=dict(baseline_exact=True, full_context_P2=True, source_target_separate=True, cohort_and_path_candidates_explicit=True,
                          arm_diffs_audited=True, ramp60_mapping_complete=True, unresolved_decisions_explicit=True, offline_only=True),
        R1_execution_allowed=False, R1_executed=False, source_event_support_in_B00=bool(source_audit["events"]),
        R1_release_conditions=["Researcher resolves listed source/target/cohort/path and exact manipulation candidates", "New exact run-specific source/runtime/input/policy/envelope admission for R1, without reusing A03 approval", "Roadmap diagnostic budget and stopping rules retained"],
        scientific_gate_snapshot_unchanged=entry["gate_snapshot"],
        no_scientific_effect_claim=True, no_Protocol_Lock=True, new_SUMO_launches=0,
        review_scope="Complete candidate packet for review only; no source-support or scientific Gate pass inferred"))
    validation = dict(schema="aad.r0.offline-validation.v1", recorded_at=datetime.now(timezone.utc).isoformat(),
        task_label_date="2026-10-28", actual_clock_used=True, new_SUMO_launches=0, new_TraCI_connections=0,
        no_ledger_reserve=True, no_envelope_written=True, no_protocol_lock=True, guard=guard,
        exact_verified_bindings=len(verified), raw_full_context_crosscheck=True, candidate60_contract_pass=True,
        full_context_independent_event_scan_pass=True, candidate_inputs_not_executed=True,
        software_test_record="docs/audits/stage_0_5_r0_20261028_v1/final_validation.json (written after isolated checks)",
        scientific_gates_changed=False)
    write(out / "validation_record.json", validation)
    source_names = ["code/scripts/prepare_stage_0_5_r0_design_packet.py", "code/tests/test_stage_0_5_r0_design_packet.py",
        "code/src/riskprop/stage_0_5_d1_measurement.py", "code/src/riskprop/stage_0_5_sumo.py",
        "code/src/riskprop/stage_0_5_scene_reconstruction.py", "code/src/riskprop/stage_0_5_state_support.py",
        "code/src/riskprop/stage_0_1_sumo.py", "code/scripts/prepare_stage_0_5_policy_a.py",
        "code/scripts/prepare_stage_0_5_admission_v3.py", "code/scripts/stage_0_5_execution_v2.py", ENTRY.as_posix()]
    write(out / "manifest.json", dict(schema="aad.r0.manifest.v1", task_id=TASK, result_id=RESULT,
        baseline_entry_commit=entry["actual_entry_HEAD"], input_sha256=verified,
        source_sha256={n: sha(root/n) for n in source_names}, candidate_input_sha256={(CANDIDATE/"ramp_routes.rou.xml").as_posix():sha(candidate/"ramp_routes.rou.xml")},
        output_sha256={p.name:sha(p) for p in sorted(out.iterdir())},
        self_hash_rule="manifest excluded from its own output map; SHA256SUMS binds manifest and all packet files"))
    with (out / "SHA256SUMS").open("x", encoding="utf-8", newline="\n") as f:
        for p in sorted(out.iterdir()):
            if p.name != "SHA256SUMS":
                f.write(sha(p) + "  " + p.name + "\n")
    print(json.dumps(dict(output=str(out), candidate=str(candidate), status="READY_FOR_RESEARCHER_REVIEW",
        full_context_P2=len(source_audit["events"]), total_states=len(d), ramp_candidate_count=len(mapping), new_SUMO_launches=0)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--verify", action="store_true", help="Verify packet, candidates and all present bindings; no regeneration")
    parser.add_argument("--require-local", action="store_true", help="Verification must include sealed local outputs")
    parser.add_argument("--complete-topology", action="store_true", help="Append one exclusive offline topology audit and final draft seal before export")
    parser.add_argument("--seal-validation", action="store_true", help="Bind the final passed offline validation before commit/export")
    args = parser.parse_args()
    require(sum([args.verify, args.complete_topology, args.seal_validation]) <= 1, "select_one_operation")
    if args.seal_validation:
        seal_validation(args.repo_root)
    elif args.complete_topology:
        complete_topology_audit(args.repo_root)
    elif args.verify:
        offline_guard([])
        print(json.dumps(verify_packet(args.repo_root, require_local=args.require_local)))
    else:
        prepare(args.repo_root)
