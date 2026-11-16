"""Smoke test: does per-vehicle setTau actually open the following gap in SUMO 1.26?

Path 3 rests on this. If increasing tau does not increase the measured net gap, the whole
response design is void. Run this before any path-3 arm.

Usage:
  python code/scripts/smoke_settau.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

SUMO = "sumo"
STEP = 0.05
END = 60.0
NET = ('<net version="1.20"><edge id="E" from="n0" to="n1" priority="1" numLanes="1" '
       'speed="30.00" length="5000"><lane id="E_0" index="0" speed="30.00" length="5000" '
       'shape="0,0 5000,0"/></edge><junction id="n0" type="dead_end" x="0" y="0"/>'
       '<junction id="n1" type="dead_end" x="5000" y="0"/></net>')


def build(workdir: Path, tau_after: float | None, switch_at: float) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "net.net.xml").write_text(NET, encoding="utf-8")
    vehs = "".join(
        f'<vehicle id="V{i}" type="c" route="r" depart="0" departPos="{2000 - 15 * i}" '
        f'departSpeed="15"/>' for i in range(12))
    (workdir / "r.rou.xml").write_text(
        f'<routes><vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" tau="0.6" '
        f'length="5" minGap="2.5" maxSpeed="30" sigma="0"/>'
        f'<route id="r" edges="E"/>{vehs}</routes>', encoding="utf-8")
    cfg = workdir / "c.sumocfg"
    cfg.write_text(f"""<configuration>
    <input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>
    <time><begin value="0"/><end value="{END}"/><step-length value="{STEP}"/></time>
    <processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>
    <random_number><seed value="20261116"/></random_number>
</configuration>""", encoding="utf-8")
    return cfg


def run(tau_after: float | None, switch_at: float = 10.0):
    scratch = ROOT / f"code/outputs/analysis/_smoke_settau/{'base' if tau_after is None else f'tau{tau_after}'}"
    cfg = build(scratch, tau_after, switch_at)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true"])
    gaps, taus = [], []
    try:
        for k in range(int(round(END / STEP))):
            now = k * STEP
            traci.simulationStep()
            if tau_after is not None and abs(now - switch_at) < STEP / 2:
                for i in range(12):
                    traci.vehicle.setTau(f"V{i}", tau_after)
            if now >= switch_at + 20.0:
                g = [traci.vehicle.getLeader(f"V{i}", 200.0) for i in range(1, 12)]
                g = [x[1] for x in g if x]
                if g:
                    gaps.append(float(np.mean(g)))
                taus.append(float(traci.vehicle.getTau("V5")))
    finally:
        traci.close()
    return (float(np.mean(gaps)) if gaps else None,
            float(np.mean(taus)) if taus else None)


def main() -> int:
    g0, t0 = run(None)
    print(f"baseline:      tau={t0}  平均车距={g0:.3f} m")
    ok = False
    for tau in (1.2, 2.0, 3.0):
        g, t = run(tau)
        d = (g - g0) if (g is not None and g0 is not None) else None
        print(f"setTau({tau}):  tau={t}  平均车距={g:.3f} m  Δ={d:+.3f} m")
        if d is not None and d > 1.0:
            ok = True
    print()
    if ok:
        print("PASS: setTau 能拉开车距，路径三的响应设计成立")
        return 0
    print("FAIL: setTau 没有拉开距离，路径三不能用这个动作")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())