"""Evidence-driven capsule acceptance; no launcher and no scientific algorithm.

Unknown evidence is distinct from rejection, and both map to ledger False.
Synthetic kernel transcripts are accepted ONLY inside an explicit replay fixture.
They never establish native isolation.
"""
from __future__ import annotations
import hashlib
import io
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from stage_0_5_input_fidelity import inventory, xml
from stage_0_5_research_ledger import CHECKS, canonical, resource_reason


def verdict(conditions=None, *, reason=None, evidence=None):
    if conditions is not None: conditions = {k:bool(v) for k,v in conditions.items()}
    status = "Unknown" if conditions is None else ("Pass" if all(conditions.values()) else "Reject")
    return dict(status=status, passed=status == "Pass", conditions=conditions, reason=reason, evidence=evidence)


def fcd_structure(data, duration_s, period_s=.1):
    root = xml(data)
    if root.tag != "fcd-export":
        raise ValueError("wrong_FCD_root")
    times, ids_by_time = [], {}
    for step in root.findall("timestep"):
        t = float(step.get("time")); tick = round(t / period_s)
        if not math.isfinite(t) or abs(t - tick * period_s) > 1e-7 or tick in ids_by_time:
            raise ValueError("FCD_duplicate_or_invalid_frame_clock")
        ids = [v.get("id") for v in step.findall("vehicle")]
        if len(ids) != len(set(ids)) or any(not v for v in ids):
            raise ValueError("FCD_duplicate_or_missing_identity")
        ids_by_time[tick] = ids; times.append(tick)
    expected = set(range(round(duration_s / period_s)))
    return dict(parse_complete=True, ordered=times == sorted(times), period_s=period_s,
                ticks=times, missing_ticks=sorted(expected - set(times)), extra_ticks=sorted(set(times) - expected),
                full_grid=set(times) == expected and times == sorted(times),
                identities=sorted({v for ids in ids_by_time.values() for v in ids}),
                empty_frames=sum(not ids for ids in ids_by_time.values()))


def control_acceptance(frames, run):
    lanes = set(run["supply_target_lanes"]); records = []
    for f in frames[1:]:
        c = f.get("controls")
        if not isinstance(c, dict):
            return verdict(None, reason="missing_step_control_observation")
        records.append(c)
    step, duration = run.get("internal_step_s", .05), run["duration_s"]
    good = len(records) == round(duration / step)
    for i, c in enumerate(records):
        t = i * step
        # Values at exact boundaries follow [start,end), without epsilon shifts.
        windows = [s for s in run["lane_speed_schedule"] if s["start_s"] <= round(t, 8) < s["end_s"]]
        if len(windows) != 1:
            good = False; continue
        target = windows[0]["speed_mps"]
        actual = c.get("native_lane_limits", {})
        good &= (abs(c.get("applied_before_step_s", -1) - t) < 1e-7 and c.get("target_mps") == target
                 and abs(c.get("native_clock_before_s", -1) - t) < 1e-7
                 and set(actual) == lanes and all(abs(v - target) < 1e-7 for v in actual.values()) and not c.get("failures"))
    return verdict(dict(all_internal_steps_and_five_lane_readbacks=bool(good)), evidence=dict(records=len(records)))


def input_acceptance(context, identity, controls):
    scope, work, run = context["scope"], context["work"], context["run"]
    unchanged = all((work / name).read_bytes() == data for name, data in context["validated_inputs"].items())
    _, vehicles, initial, _, routes = inventory(context["validated_inputs"]["routes.rou.xml"])
    rows = identity.get("vehicles", {})
    identities = set(rows) == set(vehicles)
    insertion_geometry = []
    ramp = []
    net = xml(context["validated_inputs"]["network.net.xml"])
    lanes = {l.get("id"): l for e in net.findall("edge") for l in e.findall("lane")}
    for ident, vehicle in vehicles.items():
        r = rows.get(ident, {})
        t = r.get("actual_departure_s")
        if t is not None:
            lane, pos, speed = r.get("actual_depart_lane"), r.get("actual_depart_position_m"), r.get("actual_insertion_speed_mps")
            edge = routes[vehicle.get("route")].get("edges").split()[0]
            valid = lane in lanes and lane.rsplit("_", 1)[0] == edge and pos is not None and speed is not None
            if valid:
                valid &= 0 <= pos <= float(lanes[lane].get("length")) and speed >= 0
                if ident in initial:
                    valid &= lane == edge + "_" + vehicle.get("departLane") and abs(pos - float(vehicle.get("departPos"))) < 1e-5
                desired = vehicle.get("departSpeed")
                if desired == "max":
                    limit = float(lanes[lane].get("speed"))
                    if lane in run["supply_target_lanes"]:
                        target = [s["speed_mps"] for s in run["lane_speed_schedule"] if s["start_s"] <= t < s["end_s"]]
                        limit = min(limit, target[0]) if len(target) == 1 else -1
                    valid &= speed <= limit + 1e-5
                elif desired is not None:
                    valid &= abs(speed - float(desired)) < 1e-5
            insertion_geometry.append(bool(valid))
        if vehicle.get("route") == "entering" and ident not in initial:
            ramp.append(dict(id=ident, planned_depart_s=float(vehicle.get("depart")), actual_depart_s=t,
                             first_FCD_s=r.get("first_FCD_s"), delay_s=r.get("depart_delay_s"),
                             state=r.get("state", "Unknown"), right_censored=r.get("right_censored")))
    ramp_report = dict(planned_count=len(ramp), entered_count=sum(r["actual_depart_s"] is not None for r in ramp),
                       not_entered_ids=[r["id"] for r in ramp if r["actual_depart_s"] is None], vehicles=ramp,
                       ninety_percent_rule="Proposed diagnostic only, not an acceptance threshold")
    ramp_rule = run.get("ramp_acceptance", {}).get("researcher_decision")
    ramp_evidence = (not run["factors"]["ramp"]) or (ramp_rule is not None and identities and
                    all(r["actual_depart_s"] is not None for r in ramp))
    # A pulse-completeness scientific rule is required for R arms; no invented 90% gate.
    if run["factors"]["ramp"]:
        ramp_evidence = False if ramp_rule is None else (ramp_rule.get("kind") == "all_planned_depart_in_bound_block"
            and ramp_rule.get("confirmed") is True and all(r["actual_depart_s"] is not None and
                int(r["actual_depart_s"] // 60) == int(r["planned_depart_s"] // 60) for r in ramp))
    return verdict(dict(staged_bytes_unchanged=unchanged, exact_identity_set=identities,
                        observed_insertion_geometry=bool(insertion_geometry) and all(insertion_geometry),
                        supply_observed=controls["passed"], ramp_contract_satisfied=bool(ramp_evidence)), evidence=ramp_report)


def resource_acceptance(context):
    runtime = context.get("runtime_evidence", {})
    samples = runtime.get("resource_samples")
    if not samples:
        return verdict(None, reason="resource_history_missing")
    limits = context["resource_limits"]
    try:
        safe = all(resource_reason(limits, s, startup=i == 0) is None for i, s in enumerate(samples))
        clocks = [s["wall_s"] for s in samples]
        covered = (len(samples) >= 2 and clocks == sorted(clocks) and
                   max(b - a for a, b in zip(clocks, clocks[1:])) <= limits["supervision_poll_s"])
        final = runtime["run_finished_wall_s"]
        covered &= clocks[-1] >= final and runtime.get("watchdog_failure") is None
        return verdict(dict(all_samples_within_limits=safe, supervision_covered=covered,
                            clean_process_exit=runtime.get("exit_code") == 0), evidence=dict(samples=len(samples), peak_rss=max(s["process_tree_rss_bytes"] for s in samples)))
    except (KeyError, ValueError, TypeError):
        return verdict(None, reason="resource_record_incomplete")


def isolation_acceptance(context):
    capability = None
    declared = context.get("proposal", {}).get("isolation", {})
    if declared.get("capability_evidence_path"):
        from stage_0_5_isolation_admission import capability_report
        try:
            capability = capability_report(context["scope"].repo, declared["capability_evidence_path"], declared["capability_evidence_sha256"])
        except (ValueError, KeyError, OSError) as error:
            return verdict(dict(capability_binding=False), reason=str(error))
    report = context.get("runtime_evidence", {}).get("isolation")
    if not isinstance(report,dict) or not report:
        return verdict(None, reason="OS_runtime_evidence_missing", evidence=capability)
    native_kind = (report.get("kind") == "OS_enforced" and report.get("backend") in {"linux-userns", "windows-appcontainer"}
                   and context.get("native_enforcement_verified") is True)
    synthetic_kind = report.get("kind") == "synthetic_kernel_transcript" and context.get("synthetic_only") is True
    required = {"files_read_only", "exclusive_output", "forbidden_resources_denied", "children_confined", "process_tree_limited", "network_confined"}
    probes = report.get("probes", {})
    return verdict(dict(provenance_kind_allowed=native_kind or synthetic_kind,
                        exact_bindings=bool(context.get("binding_sha256")) and report.get("binding_sha256") == context.get("binding_sha256"),
                        enforcement_probes=required == set(probes) and all(v is True for v in probes.values()),
                        transcript_bound=bool(report.get("transcript_sha256")) and report.get("transcript_sha256") in context.get("isolation_transcript_sha256", [])),
                   evidence=dict(kind=report.get("kind"), native_certificate=native_kind, capability=capability))


def assess_capsule(context, identity):
    """All eight ledger fields come from inspectable evidence and core functions."""
    import pandas as pd
    from riskprop.stage_0_5_scene_reconstruction import parse_fcd, network_edge_lengths
    from riskprop.stage_0_5_state_support import fcd_to_state_frame, measure_state_frame, route_length_map
    from riskprop.stage_0_5_d1_measurement import local_d1_measurement, offset100_cloud
    work, run, scope = context["work"], context["run"], context["scope"]
    reports = {}
    identity_rebuilt = False
    journal_verified = False
    runtime = context.get("runtime_evidence", {})
    sealed = runtime.get("sealed_artifacts", {})
    try:
        for name in ["fcd.xml", "tripinfo.xml", "identity_events.jsonl", "identity_summary.json"]:
            if name not in sealed or hashlib.sha256((work / name).read_bytes()).hexdigest() != sealed[name]:
                raise ValueError("artifact_not_sealed_or_hash_drift:" + name)
        structure = fcd_structure((work / "fcd.xml").read_bytes(), run["duration_s"])
        fcd = parse_fcd(work / "fcd.xml", network_edge_lengths(work / "network.net.xml"))
        if set(fcd.vehicle_id) - set(identity["vehicles"]):
            raise ValueError("FCD_unknown_identity")
        from stage_0_5_identity_observation import IdentityObserver
        from stage_0_5_execution_v2 import verify_journal
        journal = verify_journal(work / "identity_events.jsonl")
        _, declared, _, _, _ = inventory(context["validated_inputs"]["routes.rou.xml"])
        rebuilt = IdentityObserver([dict(id=k,depart_s=float(v.get("depart"))) for k,v in declared.items()])
        for line in (work / "identity_events.jsonl").read_bytes().splitlines():
            rebuilt.ingest(json.loads(line)["payload"])
        for row in fcd.itertuples(): rebuilt.observe_fcd(str(row.vehicle_id),float(row.time_s))
        rebuilt.observe_tripinfo((work / "tripinfo.xml").read_bytes())
        replayed = rebuilt.finish()
        # JSON numeric 0 and 0.0 are equivalent; availability flags remain typed.
        identity_rebuilt = replayed == identity and all(type(identity.get(k)) is bool for k in
            ["identity_accounting_complete","native_departure_clock_complete"])
        journal_verified = journal["events"] == round(run["duration_s"]/.05)+1
        context["identity_frames"] = rebuilt.frames
        measured = measure_state_frame(fcd_to_state_frame(fcd, route_length_map(work / "routes.rou.xml"),
            run_id=run["id"], scenario_id=run["condition"], seed=run["seed"]))
        result = local_d1_measurement(measured, run["evaluation_elapsed_s"], strict=True)
        full = local_d1_measurement(measured, (0, run["duration_s"]), strict=True)
        full_ids = {(e["event_id"], e["member_sha256"]) for e in full["events"]}
        event_match = all((e["event_id"], e["member_sha256"]) in full_ids for e in result["events"])
        reports["full_context_events"] = verdict(dict(XML_and_all_record_times_complete=structure["full_grid"],
            full_context_members_match=event_match, onset_attribution=result["onset_events"] == sum(e["onset_in_window"] and e["onset_inside"] for e in result["events"])), evidence=structure)
        reports["D1_contract"] = verdict(dict(current_contract=result["eligibility"] == "D1_contract_implemented",
            positive_qualified_exposure=result["local_evaluable_s"] > 0, continuous_clock=structure["ordered"]),
            evidence={k:v for k,v in result.items() if k != "events"})
        cloud = offset100_cloud(measured, run["evaluation_elapsed_s"])
        cells = []
        expected_cells = {(t, y) for t in range(9) for y in range(2)}
        for _, row in cloud.iterrows():
            lo, hi = row.block_start_s, row.block_end_s
            ticks = set(range(round(lo * 10), round(hi * 10) + 1))
            d1 = local_d1_measurement(measured, (lo, hi), region=(row.y_start_m, row.y_end_m), strict=True)
            cells.append(dict(t_block=int(row.t_block), y_block=int(row.y_block), states=int(row.states),
                D1_E_veh_s=d1["local_evaluable_s"], time_support_complete=ticks <= set(structure["ticks"]),
                right_endpoint_observed=round(hi * 10) in structure["ticks"], elapsed_start_s=lo))
        refs = []
        for name in run.get("common_support_references", []):
            ref = pd.read_csv(io.BytesIO(scope.read_bound(name)))
            keys = list(zip(ref.t_block, ref.y_block))
            good = len(keys) == 18 and set(keys) == expected_cells and len(keys) == len(set(keys))
            good &= ref.states.ge(10).all() and ref.D1_E_veh_s.gt(0).all() and ref.support_status.eq("observed").all()
            good &= all(abs(float(r.elapsed_start_s) - (120 + int(r.t_block) * 30)) < 1e-7 and
                        float(r.duration_s) == 30 and float(r.y_start_m) == 150 + int(r.y_block) * 100 and
                        float(r.y_end_m) == 250 + int(r.y_block) * 100 for _, r in ref.iterrows())
            refs.append(dict(path=name, support_valid=bool(good)))
        reports["all18_common_cells"] = verdict(dict(exact_9_by_2=set((c["t_block"],c["y_block"]) for c in cells) == expected_cells,
            all_cell_time_and_right_edges=all(c["time_support_complete"] and c["right_endpoint_observed"] for c in cells),
            state_and_D1_support=all(c["states"] >= 10 and c["D1_E_veh_s"] > 0 for c in cells),
            every_bound_reference=bool(refs) and all(r["support_valid"] for r in refs)), evidence=dict(cells=cells,references=refs))
        scope.create(work / "D1_measurement.json", canonical(result) + b"\n")
        scope.create(work / "common_support_v3.json", canonical(cells) + b"\n")
        scope.create(work / "state_support_cloud.csv",cloud.to_csv(index=False).encode())
        if context.get("synthetic_only") is not True:
            measured.to_parquet(work/"measured_state.parquet",index=False)
    except (ValueError, KeyError, OSError, ET.ParseError) as error:
        for name in ["D1_contract", "all18_common_cells", "full_context_events"]:
            reports[name] = verdict(dict(parse_and_artifact_contract=False), reason=type(error).__name__ + ":" + str(error))
    frames = context.get("identity_frames", [])
    controls = control_acceptance(frames, run)
    reports["input_fidelity"] = input_acceptance(context, identity, controls)
    rows = identity.get("vehicles", {})
    reports["initialization_accounting"] = verdict(dict(native_identity_accounting=identity.get("identity_accounting_complete") is True,
        sealed_journal_summary_matches=identity_rebuilt,
        tripinfo_for_inserted=bool(rows) and all(r.get("tripinfo") is not None for r in rows.values() if r.get("actual_departure_s") is not None),
        no_unaccounted_discard=all(r.get("state") != "discarded_explicit_evidence" for r in rows.values())), evidence=dict(states=identity.get("states"), declared=identity.get("declared_count")))
    reports["identity_clock"] = verdict(dict(native_clock=identity.get("native_departure_clock_complete") is True,
        complete_run_clock=identity.get("last_native_observation_s") == run["duration_s"],
        native_event_journal=journal_verified and identity_rebuilt))
    reports["resource_limits"] = resource_acceptance(context)
    reports["task_isolation"] = isolation_acceptance(context)
    checks = {name: reports[name]["passed"] for name in CHECKS}
    return dict(checks, verdicts=reports, controls=controls,
                acceptance_scope="synthetic_replay_only" if context.get("synthetic_only") else "native_evidence",
                formal_scientific_equivalence=False)
