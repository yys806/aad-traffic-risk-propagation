"""Verify that EIDM car-following parameters are actually being read by SUMO.

SUMO silently ignores unknown ``<param>`` keys, so a typo looks exactly like "the parameter
had no effect". This test sets each candidate key to an extreme value and checks whether the
simulated trajectory changes. If the trajectory is bit-identical to the default run, the key
name is wrong and the parameter is not being applied.

Attribute names taken from SUMO's own definition table
(src/utils/xml/SUMOXMLDefinitions.cpp): vehdynamics, tpreview, tPersDrive, treaction,
tPersEstimate, ccoolness, sigmaleader, sigmagap, sigmaerror, jerkmax, epsilonacc, taccmax,
Mflatness, Mbegin.

Usage:
  python code/scripts/verify_eidm_params.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

SUMO = "sumo"
STEP = 0.05
END = 30.0
SEED = 20261116

# (attribute suffix, extreme value used to provoke a visible change, default value)
CANDIDATES = [
    ("sigmaerror", 0.60, 0.04),
    ("sigmagap", 0.90, 0.10),
    ("sigmaleader", 0.60, 0.02),
    ("treaction", 2.50, 0.50),
    ("tPersEstimate", 1.00, 10.00),
    ("tPersDrive", 0.50, 3.00),
    ("tpreview", 0.50, 4.00),
    ("ccoolness", 0.10, 0.99),
    ("jerkmax", 0.20, 3.00),
    ("epsilonacc", 5.00, 1.00),
    ("taccmax", 6.00, 1.20),
    ("Mflatness", 0.20, 2.00),
    ("Mbegin", 3.00, 0.70),
]


def net_xml() -> str:
    return """<net version="1.20"><edge id="E" from="n0" to="n1" priority="1" numLanes="1" speed="30.00" length="2000"><lane id="E_0" index="0" speed="30.00" length="2000" shape="0,0 2000,0"/></edge><junction id="n0" type="dead_end" x="0" y="0"/><junction id="n1" type="dead_end" x="2000" y="0"/></net>"""


def run_once(workdir: Path, params: dict[str, float]) -> np.ndarray | None:
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "net.net.xml").write_text(net_xml(), encoding="utf-8")

    extra = "".join(f'<param key="cf.eidm.{k}" value="{v}"/>' for k, v in params.items())
    routes = f"""<routes>
  <vType id="e" carFollowModel="EIDM" accel="2.6" decel="4.5" length="5" minGap="1.0" maxSpeed="30">{extra}</vType>
  <route id="r" edges="E"/>
  <vehicle id="lead" type="e" route="r" depart="0" departPos="1400" departSpeed="18"/>
  <vehicle id="f0" type="e" route="r" depart="0" departPos="1380" departSpeed="18"/>
  <vehicle id="f1" type="e" route="r" depart="0" departPos="1360" departSpeed="18"/>
  <vehicle id="f2" type="e" route="r" depart="0" departPos="1340" departSpeed="18"/>
  <vehicle id="f3" type="e" route="r" depart="0" departPos="1320" departSpeed="18"/>
  <vehicle id="f4" type="e" route="r" depart="0" departPos="1300" departSpeed="18"/>
</routes>"""
    (workdir / "r.rou.xml").write_text(routes, encoding="utf-8")
    cfg = f"""<configuration>
    <input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>
    <time><begin value="0"/><end value="{END}"/><step-length value="{STEP}"/></time>
    <processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>
    <random_number><seed value="{SEED}"/></random_number>
</configuration>"""
    (workdir / "c.sumocfg").write_text(cfg, encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(workdir / "c.sumocfg"), "--no-step-log", "true",
                 "--collision.action", "warn"])
    ids = ["lead", "f0", "f1", "f2", "f3", "f4"]
    out = {v: [] for v in ids}
    try:
        for _ in range(int(round(END / STEP))):
            traci.simulationStep()
            present = set(traci.vehicle.getIDList())
            for v in ids:
                out[v].append(traci.vehicle.getSpeed(v) if v in present else np.nan)
    except Exception:  # noqa: BLE001
        return None
    finally:
        traci.close()
    return np.array([out[v] for v in ids], dtype=float)


def main() -> int:
    scratch = ROOT / "code/outputs/analysis/_eidm_param_check"
    base = run_once(scratch / "base", {})
    if base is None:
        print("baseline run failed")
        return 1
    print(f"baseline: mean speed {np.nanmean(base):.4f} m/s, shape {base.shape}\n")

    print(f"{'param':<16}{'value':>8}{'max |Δspeed|':>14}{'生效?':>8}")
    print("-" * 48)
    results = []
    for key, extreme, default in CANDIDATES:
        arr = run_once(scratch / f"p_{key}", {key: extreme})
        if arr is None or arr.shape != base.shape:
            print(f"{key:<16}{extreme:>8}{'run failed':>14}{'?':>8}")
            results.append({"param": key, "applied": None})
            continue
        both = np.isfinite(arr) & np.isfinite(base)
        d = float(np.max(np.abs(arr[both] - base[both]))) if both.any() else 0.0
        ok = "YES" if d > 1e-9 else "NO"
        print(f"{key:<16}{extreme:>8}{d:>14.6e}{ok:>8}")
        results.append({"param": key, "value": extreme, "max_delta_speed": d,
                        "applied": d > 1e-9})

    outdir = ROOT / "code/outputs/analysis/eidm_param_check_20261116"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "check.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    n_ok = sum(1 for r in results if r.get("applied"))
    print(f"\n{n_ok}/{len(results)} 个参数确认生效")
    print(f"wrote {outdir/'check.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())