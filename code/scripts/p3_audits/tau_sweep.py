"""0.2.9 τ 异质性假设检验：真实车流的 THW 分布能否让 DRAC 越阈

【假设】我们全场用单一 τ=1.584 s，等于把所有司机都设成「中等车距」。
真实 NGSIM 的 THW 分布是 p10/p50/p90 = 1.31/2.15/3.70 s，
**有一成司机跟车近得多**。Krauss 稳态净距 = v·τ + minGap，
所以 τ=1.31 的车稳态净距只有 30.5 m（而非 36.4 m）。

【为什么这不算「为了造结果调参」】
τ 的取值不是我挑的，是从 NGSIM 实测 THW 分布反推的（0.0.2 已标定 p50→1.584）。
**用分布代替单值，是让模型更贴近实测，不是让结果好看。**

【本脚本做什么】
固定车速 21.378 m/s、前车减速至停（9.0 m/s²），后车 τ 从 1.0 扫到 3.7，
看每个 τ 下峰值 DRAC 是多少，以及是否越阈。

【注意】这是**台架诊断**，不是区域场景；结果用于判断方向，不作论文数字。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/p3_audits")
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts")
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

OUT = Path(r"D:/shen/TJU/AAD/code/outputs/analysis/P3_tau_sweep")
STEP = 0.1
VEH_LEN = 5.0
V0 = 21.378
DECEL = 9.0
BRAKE_T = 10.0
T_SIM = 45.0


def build(work: Path, tau_lead: float, tau_foll: float) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    net = ('<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="45">'
           '<lane id="e_0" index="0" speed="45" length="9000" '
           'shape="0.00,0.00 9000.00,0.00"/></edge>'
           '<junction id="a" type="dead_end" x="0" y="0"/>'
           '<junction id="b" type="dead_end" x="9000" y="0"/></net>')
    (work / "net.net.xml").write_text(net, encoding="utf-8")
    # 稳态净距由后车 τ 决定：让前车放在「后车稳态净距」处
    gap_eq = V0 * tau_foll + 2.5
    x_foll = 2000.0
    x_lead = x_foll + gap_eq
    # maxSpeed 必须锁 V0，否则前车在施刹前的 10 s 内会加速，净距被拉大（GPT 第八十六轮点名）
    vt_l = (f'<vType id="lead_t" carFollowModel="Krauss" accel="2.6" decel="4.5"'
            f' sigma="0" tau="{tau_lead}" length="5" minGap="2.5" maxSpeed="{V0}"'
            f' speedFactor="1" actionStepLength="{STEP}"/>')
    vt_f = (f'<vType id="foll_t" carFollowModel="Krauss" accel="2.6" decel="4.5"'
            f' sigma="0" tau="{tau_foll}" length="5" minGap="2.5" maxSpeed="{V0}"'
            f' speedFactor="1" actionStepLength="{STEP}"/>')
    rou = (f'<routes>{vt_l}{vt_f}<route id="r" edges="e"/>'
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


def run(tau_foll: float) -> dict:
    tag = f"tau{tau_foll:.2f}"
    cfg = build(OUT / tag, tau_foll, tau_foll)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    brake = False
    stopped = False
    peak_d = 0.0
    peak_at = None
    peak_gap = None
    peak_c = 0.0
    peak_vf = None
    g_brake = None
    min_gap = float("inf")
    collide = False
    try:
        for k in range(int(T_SIM / STEP)):
            t = round(k * STEP, 3)
            ids = traci.vehicle.getIDList()
            if "lead" not in ids or "foll" not in ids:
                if t < BRAKE_T:
                    traci.simulationStep()
                    continue
                break
            if t >= BRAKE_T and not stopped:
                if not brake:
                    brake = True
                    traci.vehicle.setSpeedMode("lead", 0)
                    g_brake = round((traci.vehicle.getLanePosition("lead")
                                     - traci.vehicle.getLanePosition("foll")) - VEH_LEN, 3)
                v = traci.vehicle.getSpeed("lead")
                if v <= 1e-6:
                    stopped = True
                else:
                    traci.vehicle.setSpeed("lead", max(0.0, v - DECEL * STEP))
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
            min_gap = min(min_gap, g)
            if g > 0 and cc > 0:
                d = cc * cc / (2 * g)
                if d > peak_d:
                    peak_d, peak_at, peak_gap, peak_vf = d, t, g, vf
                peak_c = max(peak_c, cc)
    finally:
        traci.close()
    return {"tau": tau_foll, "gap_at_brake": g_brake,
            "peak_drac": round(peak_d, 4), "peak_at": peak_at,
            "peak_vf": round(peak_vf, 3) if peak_vf else None,
            "peak_gap": round(peak_gap, 3) if peak_gap else None,
            "peak_closing": round(peak_c, 3),
            "min_gap": None if min_gap == float("inf") else round(min_gap, 3),
            "collision": collide}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== τ 扫描（车速固定 21.378 m/s，前车减速至停 9.0）===")
    print(f"{'tau':>6}{'稳态净距':>10}{'施刹净距':>10}{'峰值闭合':>10}"
          f"{'峰值DRAC':>10}{'峰值时后车v':>12}{'最小净距':>10}{'超3.4':>7}{'碰撞':>6}")
    res = []
    for tau in (1.0, 1.31, 1.584, 2.15, 3.70):
        r = run(tau)
        res.append(r)
        print(f"{tau:>6.2f}{V0*tau+2.5:>10.1f}{str(r['gap_at_brake']):>10}"
              f"{r['peak_closing']:>10.3f}{r['peak_drac']:>10.4f}"
              f"{str(r['peak_vf']):>12}{str(r['min_gap']):>10}"
              f"{('是' if r['peak_drac'] >= 3.4 else '否'):>7}"
              f"{('是' if r['collision'] else '否'):>6}", flush=True)
    (OUT / "tau_sweep.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/'tau_sweep.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())