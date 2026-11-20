"""getLeader() 返回的距离到底是什么口径？——实测判定，不靠文档猜。

背景：GPT 第六十六轮指出，风险审计脚本把 getLeader 返回的距离直接当「物理净距」，
但它可能已经扣掉了 minGap，那样 DRAC = c²/(2g) 会被系统性抬高。

设计：
  在一条直边上放两辆车，位置固定、速度固定（后车 20 m/s，前车 0 m/s），
  读 getLeader 返回值，与「几何车头到车尾距离」对比。

  几何车头到车尾 = 前车位置 − 后车位置 − 后车车长
  若 getLeader 返回 = 几何值            → 是物理净距，脚本原样可用
  若 getLeader 返回 = 几何值 − minGap   → 需在脚本里加回 minGap

预期（两车 minGap=2.5、车长 5）：
  后车在 100 m、前车在 200 m → 几何净距 = 200 − 100 − 5 = 95.0 m
  若返回 95.0 → 物理净距；若返回 92.5 → 已扣 minGap
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

OUT = Path(__file__).resolve().parents[3] / "code/outputs/analysis/P3_gap_probe"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    net = """<net version="1.20" junctionCornerDetail="5">
    <edge id="e" from="n0" to="n1" priority="1" numLanes="1" speed="30" shape="0,0 1000,0">
        <lane id="e_0" index="0" speed="30" length="1000" shape="0,0 1000,0"/>
    </edge>
    <junction id="n0" type="dead_end" x="0" y="0" incLanes="" intLanes="" shape="0,0 0,0"/>
    <junction id="n1" type="dead_end" x="1000" y="0" incLanes="e_0" intLanes="" shape="1000,0 1000,0"/>
</net>"""
    (OUT / "net.net.xml").write_text(net, encoding="utf-8")

    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1"/>')
    rou = (f'<routes>{vt}<route id="r" edges="e"/>'
           f'<vehicle id="lead" type="c" route="r" depart="0" departPos="200"'
           f' departSpeed="0" departLane="0"/>'
           f'<vehicle id="ego" type="c" route="r" depart="0" departPos="100"'
           f' departSpeed="0" departLane="0"/>'
           f'</routes>')
    (OUT / "r.rou.xml").write_text(rou, encoding="utf-8")

    cfg = f"""<configuration>
    <input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>
    <time><begin value="0"/><end value="10"/></time>
    <processing><step-length value="0.1"/></processing>
    <report><no-step-log value="true"/></report></configuration>"""
    (OUT / "c.sumocfg").write_text(cfg, encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(OUT / "c.sumocfg"), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    try:
        # 冻结两车速度，避免跟驰模型把它们拉近/推远
        for _ in range(3):
            traci.simulationStep()
        traci.vehicle.setSpeedMode("ego", 0)
        traci.vehicle.setSpeedMode("lead", 0)
        traci.vehicle.setSpeed("ego", 0.0)
        traci.vehicle.setSpeed("lead", 0.0)
        for _ in range(2):
            traci.simulationStep()

        p_ego = traci.vehicle.getLanePosition("ego")
        p_lead = traci.vehicle.getLanePosition("lead")
        len_ego = traci.vehicle.getLength("ego")
        mgap = traci.vehicle.getMinGap("ego")
        geom = p_lead - p_ego - len_ego
        leader = traci.vehicle.getLeader("ego", 500.0)
    finally:
        traci.close()

    print(f"后车位置 {p_ego:.2f} m，前车位置 {p_lead:.2f} m，后车车长 {len_ego:.2f} m")
    print(f"后车 minGap {mgap:.2f} m")
    print(f"几何车头到车尾 = {p_lead:.2f} − {p_ego:.2f} − {len_ego:.2f} = {geom:.2f} m")
    if leader is None or leader[0] is None:
        print("getLeader 返回空")
        return 1
    lid, dist = leader
    print(f"getLeader 返回：前车 {lid}，距离 {dist:.2f} m")
    print()
    d_geom = abs(dist - geom)
    d_net = abs(dist - (geom - mgap))
    print(f"与几何净距差 {d_geom:.3f} m；与(几何净距−minGap)差 {d_net:.3f} m")
    if d_geom < 0.05:
        print("判定：**返回的是物理净距（未扣 minGap）** → 脚本原样可用")
    elif d_net < 0.05:
        print("判定：**返回值已扣 minGap** → 脚本必须加回 minGap 再算 DRAC")
    else:
        print("判定：两种都不符，需进一步核查")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
