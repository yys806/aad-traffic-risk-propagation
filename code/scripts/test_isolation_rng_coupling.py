"""Test whether two physically disconnected roads stay causally independent in SUMO.

Why this matters: the paper's Stage I identifies the information effect "under physically
isolated conditions". That is only valid if a change on the source road provably cannot
alter anything on the target road. SUMO's Krauss model draws driver imperfection (sigma)
from a random stream; if that stream is shared between edges, changing source-road traffic
would perturb target-road vehicles through the random-number generator rather than through
physics — a silent coupling that would invalidate the whole isolated design.

Method: build a two-edge network with no junction between them. Run the same seed twice,
identical on the target edge (B), but different on the source edge (A): once with a normal
flow, once with the same flow plus a hard braking vehicle. Then compare B's per-step
positions and speeds sample by sample.

PASS  = B is bit-identical in both runs.
FAIL  = B differs, so isolated conditions need per-vehicle RNG isolation or sigma=0.

Usage:
  python code/scripts/test_isolation_rng_coupling.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

SUMO = "sumo"
EDGE_LEN = 2000.0
STEP = 0.05
END = 40.0
SEED = 20261116


def net_xml() -> str:
    return f"""<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50">
    <edge id="src" from="s0" to="s1" priority="1" numLanes="1" speed="30.00" length="{EDGE_LEN}">
        <lane id="src_0" index="0" speed="30.00" length="{EDGE_LEN}"
              shape="0.00,-10.00 {EDGE_LEN:.2f},-10.00"/>
    </edge>
    <edge id="tgt" from="t0" to="t1" priority="1" numLanes="1" speed="30.00" length="{EDGE_LEN}">
        <lane id="tgt_0" index="0" speed="30.00" length="{EDGE_LEN}"
              shape="0.00,10.00 {EDGE_LEN:.2f},10.00"/>
    </edge>
    <junction id="s0" type="dead_end" x="0.00" y="-10.00"/>
    <junction id="s1" type="dead_end" x="{EDGE_LEN:.2f}" y="-10.00"/>
    <junction id="t0" type="dead_end" x="0.00" y="10.00"/>
    <junction id="t1" type="dead_end" x="{EDGE_LEN:.2f}" y="10.00"/>
</net>"""


def flow_xml(start: float, count: int, spacing: float, brake: bool) -> str:
    """Identical target-edge traffic; source edge optionally gets one hard-braking vehicle."""
    vtypes = (
        '<vType id="cal" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0.5"'
        ' tau="0.6" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" speedDev="0"/>'
    )
    vehs = []
    for i in range(count):
        pos = start - spacing * i
        if pos < 0:
            break
        vehs.append(f'<vehicle id="B{i}" type="cal" route="rt" depart="0" departPos="{pos:.2f}"'
                    f' departSpeed="15" departLane="0"/>')
    for i in range(count):
        pos = start - spacing * i
        if pos < 0:
            break
        vehs.append(f'<vehicle id="A{i}" type="cal" route="rs" depart="0" departPos="{pos:.2f}"'
                    f' departSpeed="15" departLane="0"/>')
    if brake:
        # a single strongly braking vehicle on the SOURCE edge only
        vehs.append('<vehicle id="A_brake" type="cal" route="rs" depart="0" departPos="1500.00"'
                    ' departSpeed="15" departLane="0"><stop lane="src_0" duration="12"'
                    ' startPos="1700" endPos="1700" speed="0"/></vehicle>')
    routes = ('<route id="rs" edges="src"/><route id="rt" edges="tgt"/>')
    return f"<routes>{vtypes}{routes}{''.join(vehs)}</routes>"


def run(tmp: Path, brake: bool, tag: str):
    route = tmp / f"routes_{tag}.rou.xml"
    route.write_text(flow_xml(1900.0, 60, 15.0, brake), encoding="utf-8")
    cfg = tmp / f"run_{tag}.sumocfg"
    cfg.write_text(
        f"""<configuration>
    <input><net-file value="net.net.xml"/><route-files value="routes_{tag}.rou.xml"/></input>
    <time><begin value="0"/><end value="{END}"/><step-length value="{STEP}"/></time>
    <processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>
    <random_number><seed value="{SEED}"/></random_number>
</configuration>""", encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true", "--collision.action", "warn"])
    steps = int(round(END / STEP))
    ids = [f"B{i}" for i in range(60)]
    rec = {v: {"x": [], "v": []} for v in ids}
    try:
        for _ in range(steps):
            traci.simulationStep()
            present = set(traci.vehicle.getIDList())
            for v in ids:
                if v in present:
                    rec[v]["x"].append(traci.vehicle.getLanePosition(v))
                    rec[v]["v"].append(traci.vehicle.getSpeed(v))
                else:
                    rec[v]["x"].append(np.nan)
                    rec[v]["v"].append(np.nan)
    finally:
        traci.close()
    return rec


def main() -> int:
    scratch = ROOT / "code" / "outputs" / "analysis" / "_iso_scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="iso_", dir=str(scratch)))
    (tmp / "net.net.xml").write_text(net_xml(), encoding="utf-8")

    a = run(tmp, brake=False, tag="plain")
    b = run(tmp, brake=True, tag="brake")

    same_x = same_v = total = 0
    max_dx = 0.0
    for v in a:
        ax, bx = np.array(a[v]["x"]), np.array(b[v]["x"])
        av, bv = np.array(a[v]["v"]), np.array(b[v]["v"])
        m = np.isfinite(ax) & np.isfinite(bx)
        if not m.any():
            continue
        total += int(m.sum())
        same_x += int(np.sum(ax[m] == bx[m]))
        same_v += int(np.sum(av[m] == bv[m]))
        max_dx = max(max_dx, float(np.max(np.abs(ax[m] - bx[m]))))

    print(f"target edge samples compared : {total}")
    print(f"identical positions          : {same_x} ({100*same_x/max(total,1):.4f}%)")
    print(f"identical speeds             : {same_v} ({100*same_v/max(total,1):.4f}%)")
    print(f"max position difference (m)  : {max_dx:.6g}")
    verdict = "PASS" if same_x == total and same_v == total else "FAIL"
    print(f"\nVERDICT: {verdict}")
    if verdict == "FAIL":
        print("Two disconnected edges are NOT causally independent under a shared seed;")
        print("the isolated design needs per-vehicle RNG isolation (or sigma=0) before use.")
    out = {"verdict": verdict, "samples": total, "identical_positions": same_x,
           "identical_speeds": same_v, "max_position_difference_m": max_dx,
           "seed": SEED, "sigma": 0.5}
    (ROOT / "code/outputs/analysis").mkdir(parents=True, exist_ok=True)
    p = ROOT / "code/outputs/analysis/isolation_rng_coupling_20261116.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())