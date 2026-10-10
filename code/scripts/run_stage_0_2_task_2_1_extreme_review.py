"""Read-only, stratified review of NGSIM extreme measurements and candidates."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
sys.path.insert(0, str(ROOT / "code" / "scripts"))
from riskprop.ngsim_risk_calibration import _read_source  # noqa: E402
from verify_ngsim_task_1_5 import sources  # noqa: E402

SEED = 20261011
N_PER_CATEGORY = 12
CORE = ["vehicle_id", "time_s", "net_gap_m", "closing_speed_mps", "ttc_valid", "ttc_s", "drac_mps2"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def finite(s):
    return pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).notna()


def sample_cases(frame: pd.DataFrame, source: str) -> pd.DataFrame:
    valid = frame["ttc_valid"].fillna(False)
    ttc = pd.to_numeric(frame["ttc_s"], errors="coerce")
    drac = pd.to_numeric(frame["drac_mps2"], errors="coerce")
    gap = pd.to_numeric(frame["net_gap_m"], errors="coerce")
    closing = pd.to_numeric(frame["closing_speed_mps"], errors="coerce")
    categories = {
        "ttc_lt_0_5": valid & (ttc < 0.5),
        "drac_gt_10": valid & (drac > 10),
        "nonpositive_gap": frame["measurement_status"].eq("invalid") & gap.notna() & (gap <= 0),
        "near_zero_positive_gap": valid & gap.between(0, 1, inclusive="left"),
        "closing_speed_gt_15": valid & (closing > 15),
        "threshold_near_1_0": valid & (ttc.sub(1.0).abs() <= 0.05),
        "threshold_near_1_5": valid & (ttc.sub(1.5).abs() <= 0.05),
        "threshold_near_2_0": valid & (ttc.sub(2.0).abs() <= 0.05),
        "threshold_near_3_0": valid & (ttc.sub(3.0).abs() <= 0.05),
        "ordinary_valid": valid & (ttc >= 5) & (ttc <= 30) & (gap >= 2) & (closing > 0) & (drac <= 2),
    }
    rng = np.random.default_rng(SEED)
    selected = {}
    for category, mask in categories.items():
        pool = frame.loc[mask]
        if pool.empty:
            continue
        deterministic = pool.nsmallest(min(3, len(pool)), "ttc_s") if category in {"ttc_lt_0_5", "drac_gt_10", "near_zero_positive_gap"} else pool.iloc[0:0]
        remain = pool.drop(index=deterministic.index)
        take = min(N_PER_CATEGORY - len(deterministic), len(remain))
        random_rows = remain.iloc[np.sort(rng.choice(len(remain), take, replace=False))] if take else remain.iloc[0:0]
        for idx in pd.concat([deterministic, random_rows]).index:
            selected.setdefault(idx, set()).add(category)
    rows = []
    for idx, labels in selected.items():
        row = frame.loc[idx].copy()
        row["review_source"] = source
        row["review_categories"] = ";".join(sorted(labels))
        row["selection_seed"] = SEED
        row["selection_basis"] = "deterministic_extreme_plus_seeded_stratified_sample"
        rows.append(row)
    return pd.DataFrame(rows)


def independent_recompute(raw: pd.DataFrame, state_row: pd.Series) -> dict[str, object]:
    raw = raw.copy()
    time = pd.to_numeric(raw["Global_Time"], errors="coerce")
    frame = pd.to_numeric(raw["Frame_ID"], errors="coerce")
    anchor = time - 100 * frame
    vehicle = pd.to_numeric(raw["Vehicle_ID"], errors="coerce").astype("Int64").astype("string")
    keys = pd.DataFrame({"time": time, "frame": frame, "anchor": anchor, "vehicle": vehicle})
    target_time = int(state_row["global_time_ms"])
    target_frame = int(state_row["frame_id"])
    follower_id = str(state_row["vehicle_id"])
    leader_id = str(state_row["leader_id"])
    candidates = keys[(keys.time == target_time) & (keys.frame == target_frame) & (keys.vehicle == leader_id)]
    result = {"independent_candidate_count": int(len(candidates)), "independent_match_status": "unique" if len(candidates) == 1 else ("missing" if len(candidates) == 0 else "ambiguous")}
    if len(candidates) != 1:
        return result
    leader = raw.loc[candidates.index[0]]
    follower = raw.loc[(keys.time == target_time) & (keys.frame == target_frame) & (keys.vehicle == follower_id)]
    if len(follower) != 1:
        result["independent_match_status"] = "follower_missing_or_ambiguous"
        return result
    follower = follower.iloc[0]
    headway_col = next(c for c in ("Space_Hdwy", "Space_Headway", "space_headway") if c in raw.columns)
    speed_col = next(c for c in ("v_Vel", "v_vel") if c in raw.columns)
    length_col = next(c for c in ("v_Length", "v_length") if c in raw.columns)
    gap = (float(follower[headway_col]) - float(leader[length_col])) * 0.3048
    closing = (float(follower[speed_col]) - float(leader[speed_col])) * 0.3048
    ttc = gap / closing if gap > 0 and closing > 0 else np.nan
    drac = closing ** 2 / (2 * gap) if gap > 0 and closing > 0 else np.nan
    result.update({"independent_net_gap_m": gap, "independent_closing_speed_mps": closing, "independent_ttc_s": ttc, "independent_drac_mps2": drac, "independent_leader_length_m": float(leader[length_col]) * 0.3048})
    return result


def local_sequence(states: pd.DataFrame, row: pd.Series, seconds: float = 3.0) -> pd.DataFrame:
    trajectory = states[states["trajectory_id"].eq(row["trajectory_id"])].copy()
    leader = states[states["trajectory_id"].eq(row["leader_trajectory_id"])].copy()
    trajectory["local_role"] = "follower"
    leader["local_role"] = "leader"
    center = float(row["time_s"])
    local = pd.concat([trajectory, leader], ignore_index=True)
    local = local[local["time_s"].between(center - seconds, center + seconds)].copy()
    local["is_review_row"] = local["original_row_number"].eq(row["original_row_number"])
    return local.sort_values(["time_s", "frame_id"])


def continuity_label(local: pd.DataFrame, row: pd.Series) -> tuple[str, str]:
    follower_local = local[local.get("local_role", "follower").eq("follower")] if "local_role" in local else local
    if follower_local.empty or len(follower_local) < 2:
        return "E", "insufficient_local_sequence"
    ordered = follower_local.sort_values(["time_s", "frame_id"])
    dt = ordered["global_time_ms"].diff().dropna()
    df = ordered["frame_id"].diff().dropna()
    if (dt.eq(100) & df.eq(1)).mean() < 0.8:
        return "E", "local_sequence_has_gaps_or_frame_irregularity"
    if bool(row["review_categories"].startswith("ordinary")):
        return "D", "no_automated_extreme_or_continuity_conflict"
    return "C", "mathematically_extreme_or_threshold_sensitive; physical_truth_requires_manual_review"


def run(input_dir: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=False)
    task1 = input_dir
    state_paths = sorted((task1 / "states").glob("*.parquet"))
    source_list = sources(ROOT)
    event_path = input_dir / "../stage_0_2_task_1_5_20261010_r4/risk_events.parquet"
    event_rows = pd.read_parquet(event_path) if event_path.exists() else pd.DataFrame()
    source_by_name = {Path(str(s.get("trajectory_member", s.get("csv_member", "")))).name: s for s in source_list}
    # Use source order and state source_member to map the four approved calibration inputs.
    all_cases = []
    case_locals = []
    summary = []
    for state_path in state_paths:
        states = pd.read_parquet(state_path)
        source_name = state_path.stem.replace("ngsim_", "")
        cases = sample_cases(states, source_name)
        raw_source = next(s for s in source_list if str(s["window_id"]) == str(states["window_id"].iloc[0]) and str(s["site"]) == str(states["site"].iloc[0]))
        raw = _read_source(raw_source["path"], raw_source)
        reviewed = []
        for _, row in cases.iterrows():
            result = independent_recompute(raw, row)
            local = local_sequence(states, row)
            label, reason = continuity_label(local, row)
            result.update({"quality_class": label, "automated_class_reason": reason, "local_rows": len(local), "local_start_s": float(local.time_s.min()) if not local.empty else None, "local_end_s": float(local.time_s.max()) if not local.empty else None})
            if not event_rows.empty:
                matching = event_rows[event_rows["trajectory_id"].eq(row["trajectory_id"]) & event_rows["original_row_numbers"].apply(lambda values: int(row["original_row_number"]) in values if values is not None else False)]
                result["baseline_event_id"] = matching["event_id"].iloc[0] if not matching.empty else ""
                result["baseline_event_position"] = "member" if not matching.empty else "none"
            else:
                result["baseline_event_id"] = ""
                result["baseline_event_position"] = "unavailable"
            result.update({"source": source_name, "original_row_number": int(row["original_row_number"]), "trajectory_id": row["trajectory_id"], "leader_trajectory_id": row["leader_trajectory_id"], "vehicle_id": row["vehicle_id"], "leader_id": row["leader_id"], "global_time_ms": int(row["global_time_ms"]), "frame_id": int(row["frame_id"]), "time_s": float(row["time_s"]), "review_categories": row["review_categories"], "ttc_s": float(row["ttc_s"]) if np.isfinite(row["ttc_s"]) else None, "drac_mps2": float(row["drac_mps2"]) if np.isfinite(row["drac_mps2"]) else None, "net_gap_m": float(row["net_gap_m"]) if np.isfinite(row["net_gap_m"]) else None, "closing_speed_mps": float(row["closing_speed_mps"]) if np.isfinite(row["closing_speed_mps"]) else None, "measurement_status": row["measurement_status"], "selection_seed": SEED, "selection_basis": row["selection_basis"]})
            reviewed.append(result)
            local.to_parquet(output_dir / f"local_{source_name}_{int(row['original_row_number'])}.parquet", index=False)
        all_cases.extend(reviewed)
        summary.append({"source": source_name, "rows": len(states), "sampled_cases": len(reviewed), "valid_ttc": int(states.ttc_valid.sum()), "invalid": int(states.measurement_status.eq("invalid").sum()), "nonpositive_gap_rows": int(states.net_gap_m.le(0).fillna(False).sum()), "ttc_lt_0_5": int((states.ttc_valid & (states.ttc_s < .5)).sum()), "drac_gt_10": int((states.ttc_valid & (states.drac_mps2 > 10)).sum())})
    cases_df = pd.DataFrame(all_cases)
    cases_df.to_csv(output_dir / "review_cases.csv", index=False)
    pd.DataFrame(summary).to_csv(output_dir / "source_summary.csv", index=False)
    # One page per source with risk and geometry traces for the first six selected cases.
    figures = []
    for source, group in cases_df.groupby("source", sort=True):
        fig, axes = plt.subplots(3, 2, figsize=(13, 10), sharex=False)
        for ax, (_, case) in zip(axes.flat, group.head(6).iterrows()):
            local_path = output_dir / f"local_{source}_{int(case.original_row_number)}.parquet"
            local = pd.read_parquet(local_path)
            ax2 = ax.twinx()
            ax.plot(local.time_s, local.ttc_s.replace([np.inf, -np.inf], np.nan), color="tab:red", label="TTC")
            ax2.plot(local.time_s, local.net_gap_m, color="tab:blue", alpha=.8, label="net gap")
            ax.axvline(case.time_s, color="black", linewidth=.8)
            ax.set_title(f"row {int(case.original_row_number)} | {case.review_categories} | class {case.quality_class}", fontsize=8)
            ax.set_ylabel("TTC (s)"); ax2.set_ylabel("gap (m)"); ax.grid(alpha=.2)
        fig.suptitle(f"{source}: selected local risk traces", fontsize=12); fig.tight_layout()
        path = output_dir / f"{source}_casebook.png"; fig.savefig(path, dpi=140); plt.close(fig); figures.append(path.name)
    config = {"schema_version": "stage_0_2.task_2_1.review.v1", "input_dir": str(task1), "seed": SEED, "cases_per_category": N_PER_CATEGORY, "local_window_s": 3.0, "categories": ["ttc_lt_0_5", "drac_gt_10", "nonpositive_gap", "near_zero_positive_gap", "closing_speed_gt_15", "threshold_near_1_0", "threshold_near_1_5", "threshold_near_2_0", "threshold_near_3_0", "ordinary_valid"], "quality_labels": {"A": "formula_or_source_key_conflict", "B": "explicit_geometry_or_motion_conflict", "C": "mathematically_extreme_or_suspicious; manual review required", "D": "no automated conflict in checked fields", "E": "insufficient evidence"}, "scientific_claim_eligible": False, "locked_holdout_opened": False}
    (output_dir / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit = {"schema_version": "stage_0_2.task_2_1.audit.v1", "created_at": datetime.now(UTC).isoformat(), "input_sources": [{"path": str(p), "sha256": sha256_file(p)} for p in state_paths], "cases": len(cases_df), "quality_class_counts": {str(k): int(v) for k, v in cases_df.quality_class.value_counts().items()}, "independent_unique_matches": int((cases_df.independent_match_status == "unique").sum()), "independent_nonunique_or_missing": int((cases_df.independent_match_status != "unique").sum()), "figures": figures, "manual_review_required": True, "scientific_status": "descriptive_case_review_only; no_threshold_or_gate_frozen"}
    (output_dir / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    provenance = {"schema_version": "stage_0_2.task_2_1.provenance.v1", "created_at": datetime.now(UTC).isoformat(), "python": sys.version, "platform": platform.platform(), "script_sha256": sha256_file(Path(__file__))}
    (output_dir / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = []
    for p in sorted(x for x in output_dir.rglob("*") if x.is_file() and x.name not in {"manifest.json", "SHA256SUMS"}):
        files.append({"path": p.relative_to(output_dir).as_posix(), "bytes": p.stat().st_size, "sha256": sha256_file(p)})
    (output_dir / "manifest.json").write_text(json.dumps({"schema_version": "stage_0_2.task_2_1.manifest.v1", "files": files}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "SHA256SUMS").write_text("\n".join(f"{x['sha256']}  {x['path']}" for x in files) + "\n", encoding="utf-8")
    return output_dir


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.input, args.output))
