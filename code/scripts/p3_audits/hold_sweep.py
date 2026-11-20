"""0.2.6 保持时长敏感性扫描（GPT 第八十六轮 Q3 要求的预先声明分析）

【预先声明】这是敏感性分析，不是「找出哪个能越阈就用哪个」。
  - 场景定义 A「急刹后恢复」：T_hold = 0，有限脉冲，前车不停止
  - 场景定义 B「车辆因事故/障碍停车」：T_hold > 0，保持时间应由事件持续时间确定
  - 本次扫描覆盖 T_hold = 0 / 0.5 / 1.0 / 2.0 / 5.0 s，**全部报告，不筛**
  - 同时做 maxSpeed 30 vs 40 的单项对照（GPT 点名要求）

【固定不变】vType: Krauss, accel 2.6, decel 4.5, sigma 0, tau 1.584,
            length 5, minGap 2.5, speedFactor 1, actionStepLength 0.1
            初速 30 m/s 两车同速、设定净距 40 m、前车减速 9.0 m/s²
            后车一律原生、不接管
【唯一变量】T_hold（保持时长）与 maxSpeed
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/p3_audits")
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts")
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

OUT = Path(r"D:/shen/TJU/AAD/code/outputs/analysis/P3_hold_sweep")
STEP = 0.1
VEH_LEN = 5.0
TAU = 1.584
DECEL = 9.0
V0 = 30.0
GAP0 = 40.0
BRAKE_T = 10.0
T_SIM = 45.0


def build(work: Path, vmax: float, tag: str) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    net = ('<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="45">'
           '<lane id="e_0" index="0" speed="45" length="9000" '
           'shape="0.00,0.00 9000.00,0.00"/></edge>'
           '<junction id="a" type="dead_end" x="0" y="0"/>'
           '<junction id="b" type="dead_end" x="9000" y="0"/></net>')
    (work / "net.net.xml").write_text(net, encoding="utf-8")
    x_foll = 2000.0
    x_lead = x_foll + GAP0 + VEH_LEN
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          f' tau="{TAU}" length="5" minGap="2.5" maxSpeed="{vmax}" speedFactor="1"'
          f' actionStepLength="{STEP}"/>')
    rou = (f'<routes>{vt}<route id="r" edges="e"/>'
           f'<vehicle id="lead" type="c" route="r" depart="0" departPos="{x_lead:.2f}"'
           f' departSpeed="{V0}" departLane="0"/>'
           f'<vehicle id="foll" type="c" route="r" depart="0" departPos="{x_foll:.2f}"'
           f' departSpeed="{V0}" departLane="0"/></routes>')
    (work / "r.rou.xml").write_text(rou, encoding="utf-8")
    cfg = work / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_SIM:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="20261101"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")
    return cfg


def run(vmax: float, t_hold: float) -> dict:
    tag = f"vmax{int(vmax)}_hold{t_hold}"
    work = OUT / tag
    cfg = build(work, vmax, tag)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    pulse_steps = int(round(2.0 / STEP))
    hold_steps = int(round(t_hold / STEP))
    n_pulse = 0
    n_hold = 0
    brake = False
    released = False
    peak_d = 0.0
    peak_at = None
    peak_gap = None
    peak_c = 0.0
    peak_c_t = None
    g_brake = None
    lead_end_v = None
    collide = False
    trace = []
    try:
        for k in range(int(T_SIM / STEP)):
            t = round(k * STEP, 3)
            ids = traci.vehicle.getIDList()
            if "lead" not in ids or "foll" not in ids:
                if t < BRAKE_T:
                    traci.simulationStep()   # 车辆尚未插入，推进一步再看
                    continue
                break
            if t >= BRAKE_T:
                if not brake:
                    brake = True
                    traci.vehicle.setSpeedMode("lead", 0)
                    g_brake = round((traci.vehicle.getLanePosition("lead")
                                     - traci.vehicle.getLanePosition("foll")) - VEH_LEN, 3)
                if n_pulse < pulse_steps:
                    v = traci.vehicle.getSpeed("lead")
                    traci.vehicle.setSpeed("lead", max(0.0, v - DECEL * STEP))
                    n_pulse += 1
                elif n_hold < hold_steps:
                    traci.vehicle.setSpeed("lead", traci.vehicle.getSpeed("lead"))
                    n_hold += 1
                elif not released:
                    traci.vehicle.setSpeedMode("lead", 31)
                    released = True
                    lead_end_v = round(traci.vehicle.getSpeed("lead"), 3)
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            if "lead" not in ids or "foll" not in ids:
                break
            if traci.simulation.getCollisions():
                collide = True
            xf = traci.vehicle.getLanePosition("foll")
            vf = traci.vehicle.getSpeed("foll")
            xl = traci.vehicle.getLanePosition("lead")
            vl = traci.vehicle.getSpeed("lead")
            g = (xl - xf) - VEH_LEN
            cc = vf - vl
            if g > 0 and cc > 0:
                d = cc * cc / (2 * g)
                if d > peak_d:
                    peak_d, peak_at, peak_gap = d, t, g
                if cc > peak_c:
                    peak_c, peak_c_t = cc, t
            if brake and len(trace) < 400:
                trace.append({"t": t, "g": round(g, 3), "vf": round(vf, 3),
                              "vl": round(vl, 3), "c": round(cc, 3),
                              "drac": round((cc * cc / (2 * g)) if (g > 0 and cc > 0) else 0.0, 4)})
    finally:
        traci.close()
    return {"vmax": vmax, "t_hold": t_hold, "gap_at_brake": g_brake,
            "lead_v_at_release": lead_end_v, "collision": collide,
            "peak_drac": round(peak_d, 4), "peak_at": peak_at,
            "peak_gap": round(peak_gap, 3) if peak_gap else None,
            "peak_closing": round(peak_c, 3), "peak_closing_t": peak_c_t,
            "min_gap": round(min(x["g"] for x in trace), 3) if trace else None,
            "trace": trace}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== 保持时长扫描（预先声明，全部报告）===")
    print(f"{'maxSpeed':>9}{'T_hold':>8}{'施刹净距':>10}{'释放前车速':>11}"
          f"{'峰值闭合':>10}{'峰值DRAC':>10}{'峰值净距':>10}{'最小净距':>10}{'碰撞':>6}")
    res = []
    for vmax in (30.0, 40.0):
        for th in (0.0, 0.5, 1.0, 2.0, 5.0):
            r = run(vmax, th)
            res.append(r)
            print(f"{vmax:>9.0f}{th:>8.1f}{str(r['gap_at_brake']):>10}"
                  f"{str(r['lead_v_at_release']):>11}{r['peak_closing']:>10.3f}"
                  f"{r['peak_drac']:>10.4f}{str(r['peak_gap']):>10}"
                  f"{str(r['min_gap']):>10}{('是' if r['collision'] else '否'):>6}",
                  flush=True)
    (OUT / "hold_sweep.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/'hold_sweep.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())