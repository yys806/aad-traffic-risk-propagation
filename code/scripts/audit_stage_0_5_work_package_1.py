"""Issue #1: deterministic offline audit; never launches a simulator or changes a Gate.

Only the two previously accessed calibration sources and their existing simulation
outputs are read. Temporal-validation trajectories are deliberately excluded.
Outputs are aggregate audit evidence, not a replacement scientific result.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/src"))
from riskprop import stage_0_5_state_support as ss

WINDOWS = {"us101__0750_0805": (120., 840.), "us101__0805_0820": (180., 840.)}
STATE = "evidence/results/RES-STAGE-0.5-STATE-SUPPORT-V1"
TIMING = "evidence/results/RES-STAGE-0.5-ARRIVAL-TIMING-V1"
CLOSURE = "evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1"
CANONICAL = "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Reader:
    def __init__(self, root):
        self.root = root.resolve()
        self.inputs = {}

    def path(self, relative):
        p = (self.root / relative).resolve()
        if not p.is_relative_to(self.root):
            raise ValueError("outside_repository")
        # Do not even enumerate the temporal trajectory directory or other sources.
        allowed_data = [f"{CANONICAL}/ngsim_{w}.parquet" for w in WINDOWS]
        allowed_prefixes = [
            "code/outputs/formal/calibration/stage_0_5_state_support_v1/" + k + "/"
            for k in ("grid", "seeds", "structural")
        ] + ["code/outputs/formal/calibration/stage_0_5_boundary_timing_v1/runs/"]
        if relative.startswith("code/outputs/") and relative not in allowed_data:
            if not any(relative.startswith(k) for k in allowed_prefixes):
                raise ValueError("unauthorised_data_path")
            if not any(w in relative for w in WINDOWS) or "0820_0835" in relative:
                raise ValueError("unauthorised_window")
        self.inputs[relative] = {"sha256": sha(p), "bytes": p.stat().st_size}
        return p

    def js(self, relative):
        return json.loads(self.path(relative).read_text(encoding="utf-8-sig"))


def region(d):
    return d.lane_id.astype(str).isin(["1", "2", "3", "4", "5"]) & d.y_m.ge(150) & d.y_m.lt(350)


def edge_and_event_audit(frame, window, *, real):
    """Independent vector audit of D1 incoming links and complete-context P2.

    Missing identities fail closed. Real break flags describe the incoming edge.
    Simulation flags, if present, retain the native adapter's both-end semantics.
    No scientific measurement/model function is modified or called here.
    """
    follower = "trajectory_id" if real else "incarnation_id"
    leader = "leader_trajectory_id" if real else "leader_incarnation_id"
    # Early grid files predate the explicit leader-incarnation columns. Their
    # observed ID is auditable, but does not prove resolved-incarnation identity.
    missing_leader_incarnation = not real and leader not in frame
    if missing_leader_incarnation:
        leader = "leader_id"
    keys = [follower]
    if real:
        keys = ["dataset", "site", "window_id", follower]
    else:
        keys = [k for k in ["run_id", "scenario_id", "vehicle_id", follower] if k in frame]
    d = frame.sort_values(keys + ["time_s"], kind="stable").reset_index(drop=True)
    if d.duplicated(keys + ["time_s"]).any():
        raise ValueError("duplicate_identity_clock")
    p = d.shift()
    same_follower = pd.Series(True, index=d.index)
    for k in keys:
        same_follower &= d[k].notna() & p[k].notna() & d[k].eq(p[k])
    adjacent = same_follower & d[leader].notna() & p[leader].notna() & d[leader].eq(p[leader])
    adjacent &= d.time_s.sub(p.time_s).sub(.1).abs().lt(1e-9)
    if real:
        adjacent &= d.diagnostic_clock_anchor_ms.eq(p.diagnostic_clock_anchor_ms)
        adjacent &= d.global_time_ms.sub(p.global_time_ms).eq(100) & d.frame_id.sub(p.frame_id).eq(1)
        for k in ["identity_break", "observation_gap", "leader_matched", "identity_uncertain", "leader_identity_uncertain"]:
            if d[k].isna().any() or not d[k].map(lambda v: isinstance(v, (bool, np.bool_))).all():
                raise ValueError("unknown_boolean:" + k)
        adjacent &= ~d.identity_break & ~d.observation_gap
        reliable = d.leader_matched & ~d.identity_uncertain & ~d.leader_identity_uncertain
    else:
        adjacent &= d.leader_id.notna() & p.leader_id.notna() & d.leader_id.eq(p.leader_id)
        for k in ["identity_break", "observation_gap"]:
            if k in d:
                adjacent &= ~d[k].fillna(True) & ~p[k].fillna(True)
        for k in ["observation_index", "frame_id", "original_row_number"]:
            if k in d:
                adjacent &= d[k].sub(p[k]).eq(1)
        if "global_time_ms" in d:
            adjacent &= d.global_time_ms.sub(p.global_time_ms).eq(100)
        if not d.reliable_following_eligible.map(lambda v: isinstance(v, (bool, np.bool_))).all():
            raise ValueError("unknown_reliability")
        reliable = d.reliable_following_eligible
    quality = d.measurement_status.isin(["valid", "not_applicable"])
    eligible = adjacent & reliable & reliable.shift(fill_value=False) & quality & quality.shift(fill_value=False)
    inside = region(d)
    low, high = window
    full_window = p.time_s.ge(low - 1e-9) & d.time_s.le(high + 1e-9)
    local_edge = eligible & inside & inside.shift(fill_value=False) & full_window
    local_point = inside & d.time_s.ge(low) & d.time_s.lt(high)
    # Extract complete risk segments before attributing onset to the region/window.
    risk = reliable & d.measurement_status.eq("valid") & d.ttc_valid & d.ttc_s.gt(0) & d.ttc_s.lt(2)
    starts = risk & ~(risk.shift(fill_value=False) & adjacent)
    segment = starts.cumsum()
    events = []
    trailing_short = 0
    for _, g in d.loc[risk].groupby(segment[risk], sort=False):
        a, b = float(g.time_s.iloc[0]), float(g.time_s.iloc[-1])
        first_inside = bool(inside.iloc[g.index[0]])
        if b - a < .2 - 1e-9:
            last = int(g.index[-1])
            if (last == len(d) - 1 or not same_follower.iloc[last + 1]) and first_inside and low <= a < high:
                trailing_short += 1
            continue
        c = float(g.loc[g.time_s.sub(a).ge(.2 - 1e-9), "time_s"].iloc[0])
        ci = g.index[g.time_s.sub(c).abs().lt(1e-9)][0]
        events.append({"onset": a, "confirm": c, "onset_inside": first_inside,
                       "confirm_inside": bool(inside.iloc[ci]),
                       "through_confirm": bool(inside.loc[g.index[g.time_s.le(c + 1e-9)]].all()),
                       "through_end": bool(inside.loc[g.index].all())})
    selected = [e for e in events if low <= e["onset"] < high]
    n = sum(e["onset_inside"] for e in selected)
    exposure = int(local_edge.sum()) / 10
    return {
        "rows": len(d), "full_context_confirmed": len(events), "onset_N": n,
        "confirmation_position_N_same_onset_window": sum(e["confirm_inside"] for e in selected),
        "through_confirmation_N_same_onset_window": sum(e["through_confirm"] for e in selected),
        "through_end_N_same_onset_window": sum(e["through_end"] for e in selected),
        "confirmation_time_sensitivity_N": sum(e["confirm_inside"] and low <= e["confirm"] < high for e in events),
        "confirmation_after_window": sum(e["onset_inside"] and e["confirm"] >= high for e in selected),
        "right_censored_unconfirmed": trailing_short,
        "local_links": int(local_edge.sum()), "D1_E_veh_s": exposure,
        "full_source_E_veh_s": int(eligible.sum()) / 10,
        "diagnostic_point_E_veh_s": int((local_point & quality).sum()) / 10,
        "diagnostic_no_reliable_following_point_s": int((local_point & quality & ~reliable).sum()) / 10,
        "onset_rate_D1_audit": 3600 * n / exposure if exposure else None,
        "zero_filled_missing": False,
        "identity_evidence": "observed_leader_id_only_not_formal_equivalence" if missing_leader_incarnation else "stored_resolved_leader_identity",
    }


def cloud(frame, span, mode):
    d = frame.loc[region(frame) & frame.time_s.ge(span[0]) & frame.time_s.lt(span[1])].copy()
    d["tb"] = np.floor((d.time_s - span[0]) / 30).astype(int)
    if mode == "offset100":
        d["yb"] = np.floor((d.y_m - 150) / 100).astype(int)
        widths = {0: 100, 1: 100}
    elif mode == "global_intersection":
        d["yb"] = np.floor(d.y_m / 100).astype(int)
        widths = {1: 50, 2: 100, 3: 50}
    elif mode == "whole200":
        d["yb"] = 0
        widths = {0: 200}
    else:
        raise ValueError("unknown_partition")
    rows = []
    for (tb, yb), g in d.groupby(["tb", "yb"], sort=True):
        if len(g) < 10:
            continue
        rows.append({"density_veh_km_lane": len(g) * .1 / 30 / (widths[yb] / 1000 * 5),
                     "speed_mean_mps": g.speed_mps.mean(), "closing_speed_mean_mps": g.closing_speed_mps.mean(),
                     "low_speed_share": g.speed_mps.lt(5).mean()})
    return pd.DataFrame(rows)


def reference_stats(frame, span):
    d = frame.loc[region(frame)].copy()
    if span:
        d = d[d.time_s.ge(span[0]) & d.time_s.lt(span[1])]
    g = d[d.net_gap_m.gt(0) & d.net_gap_m.le(80)]
    close = d.closing_speed_mps.dropna()
    return {"states": len(d), "fit_states": len(g),
            "tau_eff_ratio_s": (g.net_gap_m.sum() - 2.5 * len(g)) / g.speed_mps.sum(),
            "closing_mean_all_nonmissing": close.mean(),
            "negative_share_all_local_points": d.closing_speed_mps.lt(0).mean(),
            "negative_share_nonmissing_closing": close.lt(0).mean(),
            "closing_nonmissing": len(close), "gap_nonmissing": int(d.net_gap_m.notna().sum()),
            "independently_dropna_indices_equal": d.net_gap_m.dropna().index.equals(close.index),
            "fit_unmatched_leader_states": int((~g.leader_matched).sum()),
            "fit_status_counts": g.measurement_status.value_counts().to_dict()}


def plan_counterfactual(record, real):
    desc = record["descriptors"]
    condition = record.get("cell", {}).get("condition", record.get("window"))
    other = next(w for w in WINDOWS if w != condition)
    blocks = pd.DataFrame(desc["blocks"])
    mean_inside = ss.envelope_membership(desc["density_veh_km_lane"], desc["speed_mean_mps"], real["pooled_envelope"])["inside"]
    pooled = ss.envelope_coverage(blocks, real["pooled_envelope"])
    reference = ss.envelope_coverage(blocks, real["per_window_envelopes"][other])
    minimum = real["cross_window_baseline_coverage_min"]
    directional = real["cross_window_baseline_detail"][f"{condition}_inside_envelope_of_{other}"]
    closing = np.mean([ss.closing_membership(b["density_veh_km_lane"], b["closing_speed_mean_mps"], real["pooled_closing_envelope"])["inside"] for b in desc["blocks"]])
    return {"mean_inside": bool(mean_inside), "coverage_pooled": pooled, "coverage_other": reference,
            "minimum_baseline": minimum, "directional_baseline": directional,
            "plan_primary": bool(mean_inside and pooled >= minimum),
            "executed_primary": bool(mean_inside and reference >= directional),
            "plan_closing_coverage_ok": bool(closing >= minimum),
            "executed_closing_coverage_ok": bool(closing >= directional)}


def run(output):
    if output.exists():
        raise ValueError("output_exists_no_overwrite")
    r = Reader(ROOT)
    real = r.js(f"{STATE}/real_domain.json")
    sealed = r.js(f"{CLOSURE}/real_local_reference_summary.json")
    real_frames, real_clouds, c1, c4 = {}, {}, [], {}
    for w, span in WINDOWS.items():
        path = r.path(f"{CANONICAL}/ngsim_{w}.parquet")
        if sha(path) != sealed[w]["provenance"]["state_sha256"]:
            raise ValueError("canonical_sha_mismatch")
        d = pd.read_parquet(path)
        if set(d.window_id.unique()) != {w.removeprefix("us101__")} and set(d.window_id.unique()) != {w}:
            raise ValueError("canonical_window_mismatch")
        result = edge_and_event_audit(d, span, real=True)
        old = sealed[w]["interior"]
        assert result["onset_N"] == old["counts"]["onset"]
        assert abs(result["D1_E_veh_s"] - old["local_evaluable_vehicle_s"]) < 1e-8
        assert result["full_context_confirmed"] == old["event_rows"]
        assert abs(result["full_source_E_veh_s"] - old["full_source_evaluable_exposure_s"]) < 1e-8
        c1.append(dict(task="formal_real_reference", window=w, run=w, **result))
        real_frames[w] = d[["lane_id", "y_m", "time_s", "speed_mps", "closing_speed_mps"]].copy()
        real_clouds[w] = {mode: cloud(d, span, mode) for mode in ["offset100", "global_intersection", "whole200"]}
        c4[w] = {"interior": reference_stats(d, span), "full_acquisition": reference_stats(d, None),
                 "sealed_machine": {"following_relation": real["following_relation"][w], "window": real["windows"][w]}}
        del d
    # Candidate geometry comparisons: descriptive sensitivity only; no rule is approved.
    candidate_domains = {}
    c2 = []
    for mode in ["offset100", "global_intersection", "whole200"]:
        envs = {w: ss.support_envelope(real_clouds[w][mode]) for w in WINDOWS}
        pooled = ss.support_envelope(pd.concat([real_clouds[w][mode] for w in WINDOWS]))
        cross = {w: ss.envelope_coverage(real_clouds[w][mode], envs[next(x for x in WINDOWS if x != w)]) for w in WINDOWS}
        candidate_domains[mode] = (pooled, min(cross.values()))
        for w in WINDOWS:
            c2.append({"mode": mode, "window": w, "blocks": len(real_clouds[w][mode]),
                       "cross_coverage": cross[w], "minimum_cross_baseline": min(cross.values()),
                       "pooled_density_min": pooled["density_min_veh_km_lane"], "pooled_density_max": pooled["density_max_veh_km_lane"]})
    all_records = []
    for file, group in [("grid_results", "grid"), ("seed_repeats", "seeds"), ("structural_results", "structural")]:
        data = r.js(f"{STATE}/{file}.json")
        for record in data["results"]:
            name = record["cell"]["cell_id"].replace("|", "_")
            if group == "seeds":
                name += f"_s{record['seed']}"
            relative = f"code/outputs/formal/calibration/stage_0_5_state_support_v1/{group}/{name}/measured_state.parquet"
            all_records.append((group, name, record, relative, record["cell"]["condition"]))
    for record in r.js(f"{TIMING}/run_results.json")["results"]:
        name = f"{record['window']}_{record['arm']}_s{record['seed']}"
        all_records.append(("timing", name, record, f"code/outputs/formal/calibration/stage_0_5_boundary_timing_v1/runs/{name}/measured_state.parquet", record["window"]))
    c5, c2_sim = [], []
    for task, name, record, relative, w in all_records:
        if w not in WINDOWS:
            raise ValueError("unauthorised_window")
        path = r.path(relative)
        d = pd.read_parquet(path)
        result = edge_and_event_audit(d, (300., 420.), real=False)
        result["recorded_onset_N"] = record.get("p2_events_eval_window_local")
        result["recorded_point_E"] = record["descriptors"]["p2_evaluable_exposure_veh_s"]
        result["recorded_point_rate"] = record.get("p2_local_rate_per_vehicle_hour")
        assert abs(result["diagnostic_point_E_veh_s"] - result["recorded_point_E"]) < 1e-7
        if result["recorded_onset_N"] is not None:
            assert result["onset_N"] == result["recorded_onset_N"]
        c1.append(dict(task=task, window=w, run=name, **result))
        c5.append(dict(task=task, window=w, run=name, **plan_counterfactual(record, real)))
        for mode, (envelope, baseline) in candidate_domains.items():
            blocks = cloud(d, (300., 420.), mode)
            coverage = ss.envelope_coverage(blocks, envelope)
            mean = ss.envelope_membership(record["descriptors"]["density_veh_km_lane"], record["descriptors"]["speed_mean_mps"], envelope)["inside"]
            c2_sim.append({"task": task, "window": w, "run": name, "mode": mode,
                           "blocks": len(blocks), "pooled_coverage": coverage, "minimum_cross_baseline": baseline,
                           "mean_inside": bool(mean), "candidate_primary": bool(mean and coverage >= baseline)})
        del d
        print(f"audited {task}/{name}", flush=True)
    # Bind code, declared plans, and original reports to line-numbered source evidence.
    source_files = ["code/src/riskprop/" + f + ".py" for f in [
        "stage_0_5_state_support", "stage_0_5_final_closure", "stage_0_5_sumo", "formal_risk_measurement",
        "stage_0_5_leader_replay", "stage_0_5_trajectory_reconstruction", "stage_0_5_boundary_timing"]]
    source_files += ["code/scripts/run_stage_0_5_state_support.py", "code/scripts/run_stage_0_5_boundary_timing.py", "code/scripts/audit_stage_0_5_work_package_1.py"]
    sources = {}
    for file in source_files:
        source = r.path(file).read_text(encoding="utf-8-sig")
        sources[file] = {n.name: [n.lineno, n.end_lineno] for n in ast.parse(source).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    for base in [STATE, TIMING, CLOSURE]:
        for file in ["SHA256SUMS", "experiment_plan.json", "candidate_experiment_plan.json", "candidate_run_ledger.json", "freeze_manifest.json", "temporal_validation.json", "state_support_verdict.json", "verdict.json"]:
            if (ROOT / base / file).is_file():
                r.path(f"{base}/{file}")
    # Recheck every consumed input after the computation; never update old SHA files.
    for name, info in r.inputs.items():
        if sha(ROOT / name) != info["sha256"]:
            raise ValueError("input_changed:" + name)
    output.mkdir(parents=True)
    for file, rows in [("C1_exposure_events.csv", c1), ("C2_real_candidates.csv", c2),
                       ("C2_simulation_candidates.csv", c2_sim), ("C5_plan_execution.csv", c5)]:
        pd.DataFrame(rows).to_csv(output / file, index=False, lineterminator="\n")
    (output / "C4_reference_reconciliation.json").write_text(json.dumps(c4, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    provenance = {"schema": "aad.wp1.offline-audit.v1", "issue": "https://github.com/yys806/aad-traffic-risk-propagation/issues/1",
                  "baseline_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  "worktree_at_run": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).splitlines(),
                  "command": "python code/scripts/audit_stage_0_5_work_package_1.py --output " + str(output.relative_to(ROOT)).replace("\\", "/"),
                  "environment": {"python": sys.version, "executable": sys.executable, "platform": platform.platform(), "pandas": pd.__version__, "numpy": np.__version__},
                  "seed": "not applicable; deterministic offline recomputation", "source_functions": sources,
                  "inputs": r.inputs, "limits": ["aggregate audit only; not Gate acceptance", "no SUMO process or new experiment",
                  "two calibration sources only; no temporal trajectories, sealed data or locked holdout", "candidate partitions and plan counterfactual are unapproved sensitivity analyses", "simulator measurement equivalence is not physical validation", "no new delta/h/B/window/seed/budget approval"]}
    (output / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sums = "".join(f"{sha(p)}  {p.name}\n" for p in sorted(output.iterdir()))
    (output / "SHA256SUMS").write_text(sums, encoding="utf-8")
    print(f"WP1_AUDIT_OK real=2 simulation={len(all_records)} inputs={len(r.inputs)}")


def verify(output):
    for line in (output / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        p = (output / name).resolve()
        if p.parent != output.resolve() or sha(p) != digest:
            raise ValueError("audit_checksum_mismatch")
    provenance = json.loads((output / "provenance.json").read_text(encoding="utf-8"))
    absent = 0
    for name, info in provenance["inputs"].items():
        p = ROOT / name
        if p.is_file():
            if sha(p) != info["sha256"]:
                raise ValueError("input_checksum_mismatch:" + name)
        elif name.startswith("code/outputs/"):
            absent += 1
        else:
            raise ValueError("missing_portable_input:" + name)
    print(f"WP1_CHECKSUM_OK absent_local_inputs={absent}; absence is not recomputation success")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    destination = args.output.resolve()
    if not destination.is_relative_to(ROOT):
        raise ValueError("output_must_be_in_repository")
    (verify if args.verify else run)(destination)
