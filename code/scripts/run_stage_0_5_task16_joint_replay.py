"""Run engineering-only Leader/Follower joint replay combinations for Task16."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "local_research/staging/task16_20261031"
INPUTS = ROOT / "local_research/staging/task14_20261031/candidate_inputs"
PROTO = ROOT / "local_research/staging/task15_20261031/network_prototype"
SUMO_BINARY = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
TAU = (0.7389146576529666, 1.093342856277335, 1.3877275660721775, 1.8288599276236361, 2.5614676647488244)
CANDIDATES = (("962-958-1", 1), ("926-924-1", 2), ("857-851-1", 1))

sys.path.insert(0, str(ROOT / "code/src"))
from riskprop.stage_0_5_fixed_leader_follower_traci import run_joint_replay  # noqa: E402


def prepare_cfg() -> Path:
    routes = STAGING / "joint_routes.rou.xml"
    cfg = STAGING / "joint.sumocfg"
    routes.write_text("""<routes>\n  <vType id=\"leader\" accel=\"2.6\" decel=\"4.5\" sigma=\"0\" tau=\"1.0\" length=\"5.0\" minGap=\"1.0\" maxSpeed=\"30\"/>\n  <vType id=\"follower\" accel=\"2.6\" decel=\"4.5\" sigma=\"0\" tau=\"1.0\" length=\"5.0\" minGap=\"1.0\" maxSpeed=\"30\"/>\n  <route id=\"r0\" edges=\"main_ext\"/>\n</routes>\n""", encoding="utf-8")
    cfg.write_text("""<configuration><input><net-file value=\"network.net.xml\"/><route-files value=\"joint_routes.rou.xml\"/></input><time><begin value=\"0\"/><end value=\"60\"/><step-length value=\"0.05\"/></time><processing><time-to-teleport value=\"-1\"/><collision.action value=\"warn\"/><no-step-log value=\"true\"/></processing></configuration>\n""", encoding="utf-8")
    return cfg


def main() -> None:
    STAGING.mkdir(parents=True, exist_ok=True)
    cfg = prepare_cfg()
    rows = []
    errors = []
    for candidate, lane in CANDIDATES:
        trace = pd.read_csv(INPUTS / f"{candidate}_resampled_0p05.csv")
        raw = pd.read_csv(INPUTS / f"{candidate}_raw.csv")
        mitra_f = float(raw.follower_length.iloc[0]); mitra_l = float(raw.leader_length.iloc[0])
        geometries = {"M": (mitra_f, mitra_l), "B": (4.4196, 4.4196)}
        for geometry, (follower_length, leader_length) in geometries.items():
            for tau_index, tau in enumerate(TAU):
                for arm, min_gap in (("A", 2.5), ("B", 1.0)):
                    run_id = f"{candidate}|geometry={geometry}|tau_index={tau_index}|arm={arm}"
                    try:
                        result = run_joint_replay(trace, sumo_cfg=cfg, lane_id=f"main_ext_{lane}", geometry_follower_length_m=follower_length, geometry_leader_length_m=leader_length, follower_tau_s=tau, follower_min_gap_m=min_gap, start_offset_m=40.0, sumo_binary=SUMO_BINARY, save_trace=False, initialization_mode="safe_then_move")
                        rows.append({"run_id": run_id, "candidate": candidate, "geometry": geometry, "tau_index": tau_index, "tau_s": tau, "arm": arm, "minGap_m": min_gap, **{k: v for k, v in result.items() if k not in {"rows"}}})
                    except Exception as exc:
                        errors.append({"run_id": run_id, "candidate": candidate, "geometry": geometry, "tau_index": tau_index, "tau_s": tau, "arm": arm, "minGap_m": min_gap, "error": repr(exc)})
    pd.DataFrame(rows).to_csv(STAGING / "joint_replay_summary.csv", index=False)
    (STAGING / "joint_replay_failures.json").write_text(json.dumps(errors, indent=2) + "\n", encoding="utf-8")
    summary = {"status": "COMPLETED_ENGINEERING_MATRIX", "attempted": 60, "completed": len(rows), "failed": len(errors), "formal_task9_runs": 0, "geometries": ["M", "B"], "tau_values": list(TAU), "arms": ["A", "B"], "candidate_replays": [c[0] for c in CANDIDATES]}
    (STAGING / "joint_replay_manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
