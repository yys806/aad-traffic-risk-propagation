"""0.2.19 验证：给司机加反应延迟后，区域场景能否自然产生 DRAC≥3.4

【背景】三家一致结论：原生 Krauss 零反应延迟 → 信息缺口为零 → 消息无价值。
手算（verify_react_delay.py）显示 0.8 s 反应延迟就能让 DRAC 到 3.68，
但那是纯运动学，必须在真实仿真里验证。

【本实验】单车道台架，唯一变量 = 司机的决策更新间隔（actionStepLength）
  0.1 s（= 仿真步长，当前设置，等价零延迟）
  0.4 s
  0.8 s
  1.2 s
  1.6 s（Olson & Sivak 95 分位）

条件固定：两车同速 21.378 m/s、初始净距 36.36 m、前车 9.0 m/s² 减速 2.0 秒、
后车 Krauss decel=4.5、maxSpeed=21.378（锁死防加速）

【重要】SUMO 的 actionStepLength 是「每隔这么久才重新决策一次」，
等价于「采样保持」式延迟，不是严格的人类反应时间。这是近似，
论文里必须说明（GPT 第四十九轮曾反对把 actionStepLength 当反应时间，
但那针对的是「只给某车塞延迟来造风险」；本实验是给全体车统一加，
属于还原真实驾驶局限，不是局部作弊）。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/p3_audits")
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts")
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

OUT = Path(r"D:/shen/TJU/AAD/code/outputs/analysis/P3_react_delay")
STEP = 0.1
V0 = 21.378
GAP0 = 36.36
DECEL = 9.0
PULSE = 2.0
BRAKE_T = 10.0
T_SIM = 45.0
VEH_LEN = 5.0


def build(work: Path, react: float) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    net = ('<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="40">'
           '<lane id="e_0" index="0" speed="40" length="9000" '
           'shape="0.00,0.00 9000.00,0.00"/></edge>'
           '<junction id="a" type="dead_end" x="0" y="0"/>'
           '<junction id="b" type="dead_end" x="9000" y="0"/></net>')
    (work / "net.net.xml").write_text(net, encoding="utf-8")
    x_foll = 2000.0
    x_lead = x_foll + GAP0
    # 前车：不设延迟（它是扰动源，被人为接管）
    vt_lead = (f'<vType id="lead_t" carFollowModel="Krauss" accel="2.6" decel="4.5"'
               f' sigma="0" tau="1.584" length="{VEH_LEN}" minGap="2.5"'
               f' maxSpeed="{V0}" speedFactor="1" actionStepLength="{STEP}"/>')
    # 后车：带反应延迟
    vt_foll = (f'<vType id="foll_t" carFollowModel="Krauss" accel="2.6" decel="4.5"'
               f' sigma="0" tau="1.584" length="{VEH_LEN}" minGap="2.5"'
               f' maxSpeed="{V0}" speedFactor="1" actionStepLength="{react}"/>')
    rou = (f'<routes>{vt_lead}{vt_foll}<route id="r" edges="e"/>'
           f'<vehicle id="lead" type="lead_t" route="r" depart="0"'
           f' departPos="{x_lead:.2f}" departSpeed="{V0}" departLane="0"/>'
           f'<vehicle id="foll" type="foll_t" route="r" depart="0"'
           f' departPos="{x_foll:.2f}" departSpeed="{V0}" departLane="0"/></routes>')
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


def run(react: float) -> dict:
    tag = f"react{react:.1f}"
    config = build(OUT / tag, react)
    traci = load_traci()
    traci.start([SUMO, "-c", str(config), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1",
                 "--collision.mingap-factor", "0",
                 "--step-method.ballistic", "true"])
    brake = False
    n_pulse = 0
    peak = 0.0
    peak_at = None
    peak_gap = None
    peak_vf = None
    min_gap = float("inf")
    collided = 0
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
                if n_pulse * STEP < PULSE - 1e-9:
                    v = traci.vehicle.getSpeed("lead")
                    traci.vehicle.setSpeed("lead", max(0.0, v - DECEL * STEP))
                    n_pulse += 1
                elif n_pulse == int(PULSE / STEP):
                    traci.vehicle.setSpeedMode("lead", 31)
                    n_pulse += 1
            traci.simulationStep()
            collided = max(collided, len(traci.simulation.getCollisions()))
            ids = traci.vehicle.getIDList()
            if "lead" not in ids or "foll" not in ids:
                break
            xf = traci.vehicle.getLanePosition("foll")
            vf = traci.vehicle.getSpeed("foll")
            xl = traci.vehicle.getLanePosition("lead")
            vl = traci.vehicle.getSpeed("lead")
            # 净距 = 前车车头位置 - 后车车头位置 - 前车车长（Claude 指出原实现减了后车车长）
            gap = (xl - xf) - traci.vehicle.getLength("lead")
            min_gap = min(min_gap, gap)
            cc = vf - vl
            if gap > 0 and cc > 0:
                d = cc * cc / (2 * gap)
                if d > peak:
                    peak, peak_at, peak_gap, peak_vf = d, t, gap, vf
    finally:
        traci.close()
    return {"react": react, "peak_drac": round(peak, 4), "peak_at": peak_at,
            "peak_gap": round(peak_gap, 3) if peak_gap else None,
            "peak_vf": round(peak_vf, 3) if peak_vf else None,
            "min_gap": None if min_gap == float("inf") else round(min_gap, 3),
            "collisions": collided}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== 反应延迟对峰值 DRAC 的影响（仿真验证，非手算）===")
    print(f"{'决策间隔':>10}{'峰值DRAC':>12}{'峰值时刻':>10}{'峰值净距':>10}"
          f"{'峰值时后车速':>13}{'最小净距':>10}{'超3.4':>8}{'碰撞':>6}")
    res = []
    for r in (0.1, 0.4, 0.8, 1.2, 1.6):
        d = run(r)
        res.append(d)
        print(f"{r:>10.1f}{d['peak_drac']:>12.4f}"
              f"{str(d['peak_at']):>10}{str(d['peak_gap']):>10}"
              f"{str(d['peak_vf']):>13}{str(d['min_gap']):>10}"
              f"{('是' if d['peak_drac'] >= 3.4 else '否'):>8}"
              f"{d['collisions']:>6}", flush=True)
    (OUT / "react_sweep.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/'react_sweep.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())