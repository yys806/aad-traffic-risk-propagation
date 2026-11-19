"""0.0.6 模块 0+2 可行性测试：同一状态能否合法二选一，以及 SUMO 能否忠实重放。

规格见 docs/tasks/0.0.6_规格v2_同车同状态单车分支.md

【跑之前写死的预测】（R08 第 3 条）
- 模块 0：在 in 边末端把一辆车的路线从"主路"改成"绕行"后，
  它应当真的走 bypass，且不发生瞬移、不被强制换道。
  预测：改路后该车 100 m 内进入 bypass；不出现 teleport 日志。
- 模块 2：saveState 后 loadState 继续跑，应与连续跑**逐帧完全相同**。
  预测：位置与速度的最大偏差 = 0.000（float 精度内 <1e-6）。
  若不为 0，则"同状态"这个前提不成立，整个方案作废。

只做这两件事，不做分支、不做 Y、不做查表。
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_module02"

STEP = 0.1
V_LIM = 30.0
T_CHECK = 600.0     # 保存状态的时刻
T_AFTER = 60.0      # 保存后再跑多久
DEMAND = 1600.0


def make_routes(work: Path, tag: str, probe_route: str | None = None) -> Path:
    period = 3600.0 / DEMAND
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1"/>')
    extra = ""
    if probe_route:
        extra = (f'<vehicle id="probe" type="c" route="p{probe_route}"'
                 f' depart="{T_CHECK - 12:.1f}" departPos="2700" departSpeed="max" departLane="0"/>')
    rou = (f'<routes>{vt}'
           f'<route id="main" edges="in mid bn out tail"/>'
           f'<route id="byp" edges="in bypass tail"/>'
           f'<route id="pmain" edges="in mid bn out tail"/>'
           f'<route id="pbyp" edges="in bypass tail"/>'
           f'<flow id="f" type="c" route="main" begin="0" end="{T_CHECK + T_AFTER + 300:.0f}"'
           f' period="{period:.3f}" departSpeed="max" departLane="0"/>'
           f'{extra}</routes>')
    p = work / f"r_{tag}.rou.xml"
    p.write_text(rou, encoding="utf-8")
    return p


def make_cfg(work: Path, tag: str, rou_name: str, end: float) -> Path:
    cfg = work / f"run_{tag}.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="{rou_name}"/></input>'
        f'<time><begin value="0"/><end value="{end:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="20261120"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")
    return cfg


def snapshot(work: Path, tag: str, end: float, state_at: float | None) -> dict:
    """跑一段，返回每个采样步的 (id -> (pos, speed))；可选在中途 saveState。"""
    traci = load_traci()
    traci.start([SUMO, "-c", str(make_cfg(work, tag, f"r_{tag}.rou.xml", end)),
                 "--no-step-log", "true", "--collision.action", "warn",
                 "--time-to-teleport", "-1"])
    c = traci.constants
    frames = []
    sub = set()
    try:
        for k in range(int(end / STEP)):
            t = round(k * STEP, 1)
            if state_at is not None and abs(t - state_at) < 1e-6:
                traci.simulation.saveState(str(work / f"state_{tag}.xml.gz"))
            traci.simulationStep()
            if state_at is not None and t < state_at:
                continue
            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_LANEPOSITION, c.VAR_SPEED))
                    sub.add(v)
            res = traci.vehicle.getAllSubscriptionResults()
            frames.append({v: (val.get(c.VAR_LANEPOSITION), val.get(c.VAR_SPEED))
                           for v, val in res.items()})
    finally:
        traci.close()
    return {"frames": frames}


def replay(work: Path, state: Path, extra_s: float) -> dict:
    traci = load_traci()
    traci.start([SUMO, "-c", str(work / "run_replay.sumocfg"), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    traci.simulation.loadState(str(state))
    frames = []
    sub = set()
    try:
        for _ in range(int(extra_s / STEP)):
            traci.simulationStep()
            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_LANEPOSITION, c.VAR_SPEED))
                    sub.add(v)
            res = traci.vehicle.getAllSubscriptionResults()
            frames.append({v: (val.get(c.VAR_LANEPOSITION), val.get(c.VAR_SPEED))
                           for v, val in res.items()})
    finally:
        traci.close()
    return {"frames": frames}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    net = build_net(50.0, OUT)

    # ---------- 模块 0：改路是否合法生效 ----------
    print("=== 模块 0：从 in 边末端改路，能否合法进入 bypass ===", flush=True)
    for r in ("main", "byp"):
        make_routes(OUT, f"m0_{r}", probe_route=r)
        snap = snapshot(OUT, f"m0_{r}", T_CHECK + 20, None)
        roads = []
        for fr in snap["frames"]:
            roads.extend(fr.keys())
        # 从 tripinfo 拿该车走过的边：改用直接检查最后一次出现时所在道路
        print(f"  探针路线={r}: 采集到 {len(snap['frames'])} 帧", flush=True)
    # 用 SUMO 的边输出更可靠：这里改为跑完整段并读 tripinfo 的 routeLength
    for r in ("main", "byp"):
        make_cfg(OUT, f"m0t_{r}", f"r_m0_{r}.rou.xml", T_CHECK + 20)
        cfg = OUT / f"run_m0t_{r}.sumocfg"
        txt = cfg.read_text(encoding="utf-8").replace(
            "</configuration>",
            f'<output><tripinfo-output value="t_m0t_{r}.xml"/></output></configuration>')
        cfg.write_text(txt, encoding="utf-8")
        traci = load_traci()
        traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                     "--collision.action", "warn", "--time-to-teleport", "-1"])
        try:
            for _ in range(int((T_CHECK + 20) / STEP)):
                traci.simulationStep()
        finally:
            traci.close()
        tp = OUT / f"t_m0t_{r}.xml"
        for tri in ET.parse(tp).getroot().iter("tripinfo"):
            if tri.get("id") == "probe":
                print(f"  探针路线={r}: 实测路程={float(tri.get('routeLength')):.0f} m "
                      f"（主路应 ~5000 / 绕行应 ~6500）", flush=True)

    # ---------- 模块 2：saveState / loadState 是否逐帧一致 ----------
    print("\n=== 模块 2：saveState/loadState 是否忠实重放 ===", flush=True)
    make_routes(OUT, "base")
    cont = snapshot(OUT, "base", T_CHECK + T_AFTER, state_at=T_CHECK)
    make_cfg(OUT, "replay", "r_base.rou.xml", T_CHECK + T_AFTER)
    rep = replay(OUT, OUT / "state_base.xml.gz", T_AFTER)

    n = min(len(cont["frames"]), len(rep["frames"]))
    max_dp = max_dv = 0.0
    mismatched_ids = 0
    for a, b in zip(cont["frames"][:n], rep["frames"][:n]):
        if set(a) != set(b):
            mismatched_ids += 1
        for v in set(a) & set(b):
            max_dp = max(max_dp, abs(a[v][0] - b[v][0]))
            max_dv = max(max_dv, abs(a[v][1] - b[v][1]))
    print(f"  对比帧数 {n}（每帧 {len(cont['frames'][0]) if cont['frames'] else 0} 辆车）")
    print(f"  位置最大偏差 {max_dp:.9f} m")
    print(f"  速度最大偏差 {max_dv:.9f} m/s")
    print(f"  车辆集合不一致的帧数 {mismatched_ids}")
    ok = max_dp < 1e-6 and max_dv < 1e-6 and mismatched_ids == 0
    print(f"\n  预测为「偏差 = 0」→ {'通过 ✅' if ok else '不通过 ❌（同状态前提不成立，方案作废）'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
