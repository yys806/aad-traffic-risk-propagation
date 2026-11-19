"""0.0.5 诊断：路网在不同需求下是否保持自由流。

校准表暴露：需求 1600 辆/时时，主路自由流本应 133.2 s，实测却是 205–286 s。
说明路网在事件发生之前就已经堵了——那所有对比都被污染。

本脚本：不加任何瓶颈，只在不同需求下放一辆探测车，
测它从改道点走到终点要多久，找出「还能保持自由流」的需求上限。

用法：python diag_freeflow.py
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_fork_diag"

STEP = 0.1
V_LIM = 30.0
FORK_X = 3000.0
FREE_MAIN = 133.2
FREE_DETOUR = 183.3


def one(net: Path, work: Path, demand: float, route: str, t_dep: float, seed: int) -> float | None:
    period = 3600.0 / demand
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1"/>')
    rou = (f'<routes>{vt}'
           f'<route id="main" edges="in mid bn out tail"/>'
           f'<route id="byp"  edges="in bypass tail"/>'
           f'<route id="pmain" edges="mid bn out tail"/>'
           f'<route id="pbyp" edges="bypass tail"/>'
           f'<flow id="f" type="c" route="main" begin="0" end="{t_dep+600:.0f}"'
           f' period="{period:.3f}" departSpeed="max" departLane="0"/>'
           f'<vehicle id="probe" type="c" route="{("pmain") if route=="main" else ("pbyp")}"'
           f' depart="{t_dep:.1f}" departPos="0" departSpeed="max" departLane="0"/></routes>')
    (work / f"r_{route}_{int(demand)}.rou.xml").write_text(rou, encoding="utf-8")
    tp = work / f"trip_{route}_{int(demand)}.xml"
    cfg = work / f"run_{route}_{int(demand)}.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r_{route}_{int(demand)}.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{t_dep+600:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report>'
        f'<output><tripinfo-output value="{tp}"/></output></configuration>',
        encoding="utf-8")
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    try:
        for _ in range(int((t_dep + 600) / STEP)):
            traci.simulationStep()
    finally:
        traci.close()
    if tp.exists():
        for tri in ET.parse(tp).getroot().iter("tripinfo"):
            if tri.get("id") == "probe":
                return round(float(tri.get("duration")), 1)
    return None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    work = OUT / "_net"
    net = build_net(50.0, work)
    print(f"不加瓶颈。探测车在 t=480 s 从改道点出发。理论自由流：主路 {FREE_MAIN} s、绕行 {FREE_DETOUR} s",
          flush=True)
    print(f"{'需求(辆/时)':>11} {'T主路':>8} {'主路/理论':>10} {'T绕行':>8} {'绕行/理论':>10}",
          flush=True)
    for demand in [600.0, 900.0, 1200.0, 1600.0]:
        tm = one(net, work, demand, "main", 480.0, 20261120)
        td = one(net, work, demand, "byp", 480.0, 20261120)
        rm = None if tm is None else round(tm / FREE_MAIN, 2)
        rd = None if td is None else round(td / FREE_DETOUR, 2)
        print(f"{demand:>11.0f} {str(tm):>8} {str(rm):>10} {str(td):>8} {str(rd):>10}",
              flush=True)
    print("\n判据：比值接近 1.00 表示自由流；>1.15 说明该需求下路网已经开始拥堵。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
