"""Audit the approved reliable-following exposure denominator edge by edge."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STATES = ROOT / "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states"

def main() -> None:
    scope = ["dataset", "site", "window_id", "source_member", "source_period"]
    pair = scope + ["trajectory_id", "leader_trajectory_id"]
    rows = []
    total = 0
    for path in sorted(STATES.glob("*.parquet")):
        d = pd.read_parquet(path).sort_values(
            scope + ["trajectory_id", "global_time_ms", "frame_id"], kind="stable"
        ).reset_index(drop=True)
        prev = d.shift()
        adjacent = pd.Series(True, index=d.index)
        for key in pair + ["diagnostic_clock_anchor_ms"]:
            adjacent &= d[key].notna() & prev[key].notna() & d[key].eq(prev[key]).fillna(False)
        adjacent &= d.global_time_ms.diff().eq(100)
        adjacent &= d.frame_id.diff().eq(1)
        adjacent &= (d.time_s.diff() - 0.1).abs().lt(1e-9)
        adjacent &= ~d.identity_break.fillna(True) & ~d.observation_gap.fillna(True)
        reliable = (
            d.leader_matched.fillna(False)
            & ~d.identity_uncertain.fillna(True)
            & ~d.leader_identity_uncertain.fillna(True)
        )
        edge = adjacent & reliable & reliable.shift(fill_value=False)
        transitions = (
            pd.crosstab(prev.measurement_status[edge], d.measurement_status[edge])
            .rename_axis(index="from_status", columns="to_status")
            .stack()
            .reset_index(name="edges")
        )
        transition_records = transitions.to_dict("records")
        edge_count = int(edge.sum())
        total += edge_count
        rows.append({
            "source": path.stem.removeprefix("ngsim_"),
            "state_rows": int(len(d)),
            "reliable_following_edges": edge_count,
            "reliable_following_exposure_s": edge_count * 0.1,
            "non_100ms_edges": int((d.global_time_ms.diff()[edge] != 100).sum()),
            "identity_or_clock_invalid_edges": int((~reliable[edge] | ~reliable.shift(fill_value=False)[edge]).sum()),
            "status_transitions": transition_records,
            "interpretation": "Edges are reliable follower/leader/time links; TTC measurement status is not required to be valid, so non-closing and invalid-TTC states remain eligible exposure when identity and continuity are reliable.",
        })
    result = {
        "schema_version": "stage_0_2.reliable_following_exposure.edge_audit.v1",
        "rule": "adjacent 100 ms frame, same source/diagnostic clock/follower/leader pair, exact frame and time increments, no identity break or observation gap, reliable identities at both endpoints",
        "sources": rows,
        "total_reliable_following_edges": total,
        "total_reliable_following_exposure_s": total * 0.1,
        "matches_sealed_denominator_s": abs(total * 0.1 - 512043.2) < 1e-9,
        "missing_or_identity_uncertain_edges_included": False,
        "cross_gap_or_cross_identity_accumulation": False,
        "endpoint_weighting": "each edge contributes 0.1 s; final frame has no extrapolated interval",
    }
    out = ROOT / "code/outputs/formal/calibration/stage_0_2_exposure_edge_audit_20261012.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
