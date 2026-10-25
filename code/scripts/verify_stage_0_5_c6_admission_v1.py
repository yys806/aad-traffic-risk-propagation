"""Independent geometry/event/edge checks on the six newly saved tables only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

from stage_0_5_isolation_v2 import Scope, sha
from review_stage_0_5_c6_admission_v1 import validate_allowlist, validate_output, write_new


def verify(root, manifest_path, measured_root, output):
    validate_output(root, output)
    validate_output(root, measured_root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_allowlist(manifest)
    inputs = {}
    for case in manifest["cases"]:
        folder = measured_root / case["id"]
        for name in ["repaired_measured_state.parquet", "current_frozen_window_events.json", "result.json"]:
            p = folder / name
            inputs[p.as_posix()] = sha(p)
    output.mkdir(parents=True, exist_ok=False)
    import site
    import numpy as np
    import pandas as pd
    scope = Scope(root, inputs, output, runtime_roots=[Path(sys.base_prefix), Path(site.getusersitepackages())])
    sys.addaudithook(scope.audit)
    reports = []
    try:
        for case in manifest["cases"]:
            folder = measured_root / case["id"]
            d = pd.read_parquet(folder / "repaired_measured_state.parquet")
            result = json.loads((folder / "current_frozen_window_events.json").read_text(encoding="utf-8"))
            lookup = d.set_index(["time_s", "vehicle_id"])
            followers = d.loc[d.leader_id.notna()]
            leader = lookup.reindex(pd.MultiIndex.from_arrays([followers.time_s, followers.leader_id])).reset_index(drop=True)
            if not (leader.native_lane_id.to_numpy() == followers.native_lane_id.to_numpy()).all():
                raise AssertionError("leader_native_lane_mismatch")
            expected = leader.native_position_m.to_numpy() - followers.leader_length_m.to_numpy() - followers.native_position_m.to_numpy()
            if not np.allclose(expected, followers.net_gap_m, rtol=0, atol=1e-9):
                raise AssertionError("physical_gap_mismatch")
            # Scalar segment membership oracle, same as the prior independent C6
            # verifier; no call to the production event extractor.
            risk = d.loc[d.reliable_following_eligible & d.ttc_valid & d.measurement_status.eq("valid") & d.ttc_s.gt(0) & d.ttc_s.lt(2)]
            oracle = []
            for _, g in risk.groupby(["vehicle_id", "leader_id", "native_lane_id"]):
                g = g.sort_values("time_s")
                for _, segment in g.groupby(g.time_s.diff().sub(.1).abs().gt(1e-9).cumsum()):
                    if segment.time_s.iloc[-1] - segment.time_s.iloc[0] >= .2 - 1e-9:
                        oracle.append(tuple(zip(segment.vehicle_id, segment.leader_id, segment.time_s)))
            actual = []
            for event in result["events"]:
                members = d.loc[d.vehicle_id.eq(event["vehicle_id"]) & d.leader_id.eq(event["leader_id"]) &
                                d.time_s.between(event["onset_s"], event["end_s"])]
                actual.append(tuple(zip(members.vehicle_id, members.leader_id, members.time_s)))
            if set(oracle) != set(actual):
                raise AssertionError("full_context_event_membership_mismatch")
            q = d.sort_values(["vehicle_id", "time_s"])
            previous = q.shift()
            edges = q.vehicle_id.eq(previous.vehicle_id) & q.leader_id.notna() & q.leader_id.eq(previous.leader_id)
            edges &= q.native_lane_id.eq(previous.native_lane_id) & q.time_s.sub(previous.time_s).sub(.1).abs().le(1e-9)
            quality = q.reliable_following_eligible & q.measurement_status.isin(["valid", "not_applicable"])
            inside = q.lane_id.astype(str).isin(["1", "2", "3", "4", "5"]) & q.y_m.ge(150) & q.y_m.lt(350)
            edges &= quality & quality.shift(fill_value=False) & inside & inside.shift(fill_value=False) & previous.time_s.ge(300) & q.time_s.le(420)
            for flag in ["identity_break", "observation_gap"]:
                if flag in q:
                    edges &= ~q[flag] & ~previous[flag].fillna(True)
            if abs(int(edges.sum()) * .1 - result["local_evaluable_s"]) > 1e-8:
                raise AssertionError("independent_D1_exposure_mismatch")
            reports.append(dict(id=case["id"], physical_gap_rows=len(followers), full_context_event_count=len(oracle),
                                frozen_window_N=result["onset_events"], D1_E_veh_s=result["local_evaluable_s"],
                                physical_gap_match=True, full_context_members_match=True, D1_exposure_match=True))
        value = dict(status="verified_selected_six_only", results=reports, read_sha256=inputs, new_trajectories=0,
                     event_member_sets_scope="full-context lists; window N is separately onset-attributed", Gate_changed=False)
        write_new(output / "independent_verification.json", value)
        return value
    finally:
        write_new(output / "scope_audit.json", scope.summary())


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--allowlist", type=Path, required=True)
    p.add_argument("--measurements", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = verify(a.repo_root.resolve(), a.allowlist.resolve(), a.measurements.resolve(), a.output.resolve())
    print(json.dumps({"status": result["status"], "cases": len(result["results"]), "new_trajectories": 0}))
