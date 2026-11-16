"""Test whether EIDM parameters given as vType XML attributes actually affect behaviour.

SUMO silently ignores unknown keys, so the only trustworthy check is behavioural: run the
same scenario twice, changing one parameter by a large amount, and compare the follower
speed trace. Identical traces mean the parameter is not being read.

Scenario: a slow leader forces a queue of EIDM followers to brake, so car-following
parameters genuinely matter (a free-flowing test cannot detect any difference).

Usage:
  python code/scripts/eidm_attr_probe.py
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
END = 60.0
SEED = 20261116

NET = ('<net version="1.20"><edge id="E" from="n0" to="n1" priority="1" numLanes="1" '
       'speed="30.00" length="4000"><lane id="E_0" index="0" speed="30.00" length="4000" '
       'shape="0,0 4000,0"/></edge><junction id="n0" type="dead_end" x="0" y="0"/>'
       '<junction id="n1" type="dead_end" x="4000" y="0"/></net>')


def run(workdir: Path, attrs: dict[str, str]) -> np.ndarray:
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "net.net.xml").write_text(NET, encoding="utf-8")
    # Base attributes must not be repeated: a duplicate XML attribute makes SUMO abort
    # and TraCI reports only "Connection closed by SUMO", hiding the real cause.
    base = {"carFollowModel": "EIDM", "accel": "2.6", "decel": "4.5", "length": "5",
            "minGap": "1.0", "maxSpeed": "30", "tau": "1.0"}
    base.update(attrs)
    a = " ".join(f'{k}="{v}"' for k, v in base.items())
    routes = f"""<routes>
  <vType id="e" {a}/>
  <vType id="slow" carFollowModel="Krauss" accel="2.6" decel="4.5" length="5" minGap="1.0" maxSpeed="30"/>
  <route id="r" edges="E"/>
  <vehicle id="lead" type="slow" route="r" depart="0" departPos="800" departSpeed="15">
    <stop lane="E_0" duration="15" startPos="1200" endPos="1200" speed="0"/>
  </vehicle>
  <vehicle id="f1" type="e" route="r" depart="0" departPos="790" departSpeed="15"/>
  <vehicle id="f2" type="e" route="r" depart="0" departPos="778" departSpeed="15"/>
  <vehicle id="f3" type="e" route="r" depart="0" departPos="766" departSpeed="15"/>
  <vehicle id="f4" type="e" route="r" depart="0" departPos="754" departSpeed="15"/>
</routes>"""
    (workdir / "r.rou.xml").write_text(routes, encoding="utf-8")
    cfg = f"""<configuration>
    <input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>
    <time><begin value="0"/><end value="{END}"/><step-length value="{STEP}"/></time>
    <processing><time-to-teleport value="-1"/><collision.action value="warn"/><no-step-log value="true"/></processing>
    <random_number><seed value="{SEED}"/></random_number>
</configuration>"""
    (workdir / "c.sumocfg").write_text(cfg, encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(workdir / "c.sumocfg"), "--no-step-log", "true",
                 "--collision.action", "warn"])
    ids = ["lead", "f1", "f2", "f3", "f4"]
    out = {v: [] for v in ids}
    try:
        for _ in range(int(round(END / STEP))):
            traci.simulationStep()
            present = set(traci.vehicle.getIDList())
            for v in ids:
                out[v].append(traci.vehicle.getSpeed(v) if v in present else np.nan)
    finally:
        traci.close()
    return np.array([out[v] for v in ids], dtype=float)


def main() -> int:
    scratch = ROOT / "code/outputs/analysis/_eidm_attr_probe"
    base = run(scratch / "base", {})
    print(f"baseline: f1 min speed {np.nanmin(base[1]):.3f}, mean {np.nanmean(base):.3f}\n")

    trials = [
        ("minGap 1->6 (sanity)", {"minGap": "6.0"}),
        ("tau 1->3 (sanity)", {"tau": "3.0"}),
        ("decel 4.5->1.5", {"decel": "1.5"}),
        ("sigmaerror 0->0.8", {"sigmaerror": "0.8"}),
        ("sigmagap 0->0.9", {"sigmagap": "0.9"}),
        ("sigmaleader 0->0.9", {"sigmaleader": "0.9"}),
        ("treaction 0.5->3.0", {"treaction": "3.0"}),
        ("tPersEstimate 10->0.5", {"tPersEstimate": "0.5"}),
        ("ccoolness 0.99->0.1", {"ccoolness": "0.1"}),
        ("taccmax 1.2->6", {"taccmax": "6.0"}),
        ("jerkmax 3->0.2", {"jerkmax": "0.2"}),
        ("Mbegin 0.7->3", {"Mbegin": "3.0"}),
    ]
    print(f"{'trial':<26}{'max|Δspeed|':>14}{'生效':>6}")
    print("-" * 46)
    res = []
    for label, attrs in trials:
        d = abs(hash(label)) % 100000
        arr = run(scratch / f"t{d}", attrs)
        both = np.isfinite(arr) & np.isfinite(base)
        delta = float(np.max(np.abs(arr[both] - base[both]))) if both.any() else 0.0
        ok = "YES" if delta > 1e-9 else "no"
        print(f"{label:<26}{delta:>14.6e}{ok:>6}")
        res.append({"trial": label, "attrs": attrs, "max_delta": delta,
                    "applied": delta > 1e-9})

    outdir = ROOT / "code/outputs/analysis/eidm_attr_probe_20261116"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "probe.json").write_text(json.dumps(res, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    print(f"\n生效参数: {[r['trial'] for r in res if r['applied']]}")
    print(f"wrote {outdir/'probe.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())