"""Task 1.5 independent NGSIM cross-clock leader matching audit."""
from __future__ import annotations

import argparse
import json
import hashlib
import subprocess
import sys
from pathlib import Path

import pandas as pd

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT / "src"))
from riskprop.calibration import sha256_file, validate_checksum_package  # noqa: E402
from riskprop.ngsim_risk_calibration import (  # noqa: E402
    _read_source, _seal_directory, annotate_ngsim_trajectory_identity,
    write_stage_0_2_ngsim_package,
)
from verify_ngsim_task_1_4 import sources  # noqa: E402


CORE = ["vehicle_id", "time_s", "net_gap_m", "closing_speed_mps", "ttc_valid", "ttc_s", "drac_mps2", "measurement_status", "missing_reason"]


def independent_match_audit(raw: pd.DataFrame, states: pd.DataFrame) -> dict[str, object]:
    annotated = annotate_ngsim_trajectory_identity(raw, site="Lankershim", source_member="NGSIM__Lankershim_Vehicle_Trajectories.csv")
    anchor = (pd.to_numeric(annotated.Global_Time) - 100 * pd.to_numeric(annotated.Frame_ID)).astype("Int64")
    frame = pd.to_numeric(annotated.Frame_ID)
    vehicle = pd.to_numeric(annotated.Vehicle_ID, errors="coerce").astype("Int64").astype("string")
    leader = pd.to_numeric(annotated.Preceding, errors="coerce").astype("Int64").astype("string")
    leaders = pd.DataFrame({"time": annotated.Global_Time, "id": vehicle, "anchor": anchor, "frame": frame, "original_row": range(1, len(raw) + 1)})
    reported = pd.DataFrame({"time": annotated.Global_Time, "id": leader, "anchor": anchor, "frame": frame, "original_row": range(1, len(raw) + 1)})
    reported = reported[reported.id.notna() & reported.id.ne("0")]

    def counts(keys: list[str]) -> dict[str, int]:
        unique = leaders.groupby(keys, dropna=False).size().rename("n").reset_index()
        joined = reported.merge(unique, on=keys, how="left")
        return {"unique": int((joined.n == 1).sum()), "ambiguous": int((joined.n > 1).sum()), "missing": int(joined.n.isna().sum())}

    time_id = counts(["time", "id"])
    time_anchor = counts(["time", "id", "anchor"])
    time_anchor_frame = counts(["time", "id", "anchor", "frame"])
    leader_anchor = pd.to_numeric(states.leader_trajectory_id.astype("string").str.extract(r"\|clock(.+)$")[0], errors="coerce")
    cross = states.leader_matched & leader_anchor.notna() & leader_anchor.ne(states.diagnostic_clock_anchor_ms)
    conflict = leaders.groupby(["time", "id"], dropna=False).agg(rows=("frame", "size"), anchors=("anchor", "nunique"), frames=("frame", "nunique")).reset_index()
    conflict = conflict[(conflict.rows > 1) & ((conflict.anchors > 1) | (conflict.frames > 1))]
    return {
        "raw_rows": len(raw), "vehicle_ids": int(raw.Vehicle_ID.nunique()), "reported_leader_rows": len(reported),
        "independent_counts": {"time_id": time_id, "time_id_anchor": time_anchor, "time_id_anchor_frame": time_anchor_frame},
        "same_time_id_clock_or_frame_conflict_rows": int(len(conflict)),
        "same_time_id_clock_or_frame_conflict_examples": conflict.head(20).to_dict("records"),
        "current_matched_rows": int(states.leader_matched.sum()),
        "current_cross_clock_matched_rows": int(cross.sum()),
        "current_cross_clock_valid_ttc_rows": int((cross & states.ttc_valid).sum()),
        "current_leader_identity_uncertain_valid_ttc_rows": int((states.ttc_valid & states.leader_identity_uncertain).sum()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=CODE_ROOT.parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    output = args.output.resolve()
    source_list = sources(root)
    write_stage_0_2_ngsim_package(output_dir=output, sources=source_list)
    lank = source_list[-1]
    raw = _read_source(lank["path"], lank)
    states = pd.read_parquet(output / "states/ngsim_lankershim__complete.parquet")
    audit = independent_match_audit(raw, states)
    audit["input_sha256"] = sha256_file(lank["path"])
    audit["output_events"] = {name: int(len(pd.read_parquet(output / f"{name}.parquet"))) for name in ("risk_events", "reliable_risk_events", "rejected_risk_events")}
    audit["measurement_status_counts"] = {str(k): int(v) for k, v in states.measurement_status.value_counts().items()}
    audit["valid_ttc_rows"] = int(states.ttc_valid.sum())
    (output / "cross_clock_match_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    provenance_path = output / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["git_base_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
    provenance["implementation_sha256"] = {
        path: hashlib.sha256((root / path).read_bytes()).hexdigest()
        for path in ("code/src/riskprop/real_trajectory.py", "code/src/riskprop/ngsim_risk_calibration.py", "code/scripts/verify_ngsim_task_1_5.py")
    }
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _seal_directory(output)
    validate_checksum_package(output)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
