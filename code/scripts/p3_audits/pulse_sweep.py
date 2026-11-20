"""0.2.6b 脉冲时长敏感性扫描（修正 0.2.6 的方向错误）

【为什么重做】0.2.6 扫的是「刹停后的保持时长 T_hold」，结果五个值完全相同
——说明 T_hold 不是关键变量。真正不同的是**脉冲本身的时长**：
  0.2.2 一直刹到 0（30 m/s ÷ 9.0 = 3.33 s），我只刹 2.0 s。
  所以 0.2.2 是 3.33 s 脉冲，我是 2.0 s 脉冲，这才是 3.947 vs 1.05 的差异来源。

【预先声明】扫 T_pulse = 2.0 / 2.5 / 3.0 / 3.33 / 4.0 / 6.0 s，全部报告不筛。
  前车一律 maxSpeed=30（固定，不再改），刹到 0 即止（触零后保持 0）。
【固定】Krauss accel 2.6 decel 4.5 sigma 0 tau 1.584 length 5 minGap 2.5
        actionStepLength 0.1；两车同速 30 m/s、设定净距 40 m；后车不接管
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/p3_audits")
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts")
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

OUT = Path(r"D:/shen/TJU/AAD/code/outputs/analysis/P3_pulse_sweep")
STEP = 0.1
VEH_LEN = 5.0
TAU = 1.584
DECEL = 9.0
V0 = 30.0
GAP0 = 40.0
BRAKE_T = 10.0
T_SIM = 45.0


def build(work: Path) -> Path:
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
          f' tau="{TAU}" length="5" minGap="2.5" maxSpeed="{V0}" speedFactor="1"'
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


def run(t_pulse: float) -> dict:
    tag = f"pulse{t_pulse}"
    work = OUT / tag
    cfg = build(work)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    n_steps_max = int(round(t_pulse / STEP))
    n = 0
    brake = False
    released = False
    peak_d = 0.0
    peak_at = None
    peak_gap = None
    peak_c = 0.0
    g_brake = None
    lead_min_v = None
    collide = False
    trace = []
    try:
        for k in range(int(T_SIM / STEP)):
            t = round(k * STEP, 3)
            ids = traci.vehicle.getIDList()
            if "lead" not in ids or "foll" not in ids:
                if t < BRAKE_T:
                    traci.simulationStep()
                    continue
                break
            if t >= BRAKE_T:
                if not brake:
                    brake = True
                    traci.vehicle.setSpeedMode("lead", 0)
                    g_brake = round((traci.vehicle.getLanePosition("lead")
                                     - traci.vehicle.getLanePosition("foll")) - VEH_LEN, 3)
                if n < n_steps_max:
                    v = traci.vehicle.getSpeed("lead")
                    v_new = max(0.0, v - DECEL * STEP)
                    traci.vehicle.setSpeed("lead", v_new)
                    n += 1
                    lead_min_v = v_new
                elif not released:
                    traci.vehicle.setSpeedMode("lead", 31)
                    released = True
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
                peak_c = max(peak_c, cc)
            if brake and len(trace) < 500:
                trace.append({"t": t, "g": round(g, 3), "vf": round(vf, 3),
                              "vl": round(vl, 3), "c": round(cc, 3),
                              "drac": round((cc * cc / (2 * g)) if (g > 0 and cc > 0) else 0.0, 4)})
    finally:
        traci.close()
    return {"t_pulse": t_pulse, "gap_at_brake": g_brake,
            "lead_min_v": lead_min_v, "collision": collide,
            "peak_drac": round(peak_d, 4), "peak_at": peak_at,
            "peak_gap": round(peak_gap, 3) if peak_gap else None,
            "peak_closing": round(peak_c, 3),
            "min_gap": round(min(x["g"] for x in trace), 3) if trace else None,
            "trace": trace}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== 脉冲时长扫描（预先声明，全部报告）===")
    print(f"{'T_pulse':>9}{'施刹净距':>10}{'前车最低速':>11}{'峰值闭合':>10}"
          f"{'峰值DRAC':>10}{'峰值净距':>10}{'最小净距':>10}{'碰撞':>6}{'超3.4':>7}")
    res = []
    for tp in (2.0, 2.5, 3.0, 3.33, 4.0, 6.0):
        r = run(tp)
        res.append(r)
        print(f"{tp:>9.2f}{str(r['gap_at_brake']):>10}{str(r['lead_min_v']):>11}"
              f"{r['peak_closing']:>10.3f}{r['peak_drac']:>10.4f}"
              f"{str(r['peak_gap']):>10}{str(r['min_gap']):>10}"
              f"{('是' if r['collision'] else '否'):>6}"
              f"{('是' if r['peak_drac'] >= 3.4 else '否'):>7}", flush=True)
    (OUT / "pulse_sweep.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/'pulse_sweep.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())