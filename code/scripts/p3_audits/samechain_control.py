"""同口径对照：用与区域场景同一套检测链，复核 0.2.2 单对台架的逐帧峰值。

目的：回答「0.2.2 能出 3.947、区域场景只出 1.958，差别在速度还是在净距」
——必须用同一口径，不能拿 0.2.2 的表格值和区域场景的逐帧值直接比。

复算两类：
  A. 0.2.2 的原条件：两车 30 m/s 起步、净距 40/60/80，前车 9.0 刹 2.0 s
  B. 区域场景条件：两车 21.378 m/s 起步、净距 36.364，前车 9.0 刹 2.0 s
输出：闭合速度峰值、净距峰值时刻、DRAC 峰值，全部逐帧算、同一公式。
"""
import sys
from pathlib import Path
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/p3_audits")
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts")
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

OUT = Path(r"D:/shen/TJU/AAD/code/outputs/analysis/P3_samechain_control")
STEP = 0.1
VEH_LEN = 5.0
TAU = 1.584


def build(work: Path, v0: float, gap0: float, tag: str) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    net = ('<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="40">'
           '<lane id="e_0" index="0" speed="40" length="9000" '
           'shape="0.00,0.00 9000.00,0.00"/></edge>'
           '<junction id="a" type="dead_end" x="0" y="0"/>'
           '<junction id="b" type="dead_end" x="9000" y="0"/></net>')
    (work / "net.net.xml").write_text(net, encoding="utf-8")
    x_foll = 2000.0
    x_lead = x_foll + gap0 + VEH_LEN
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          f' tau="{TAU}" length="5" minGap="2.5" maxSpeed="40" speedFactor="1"'
          f' actionStepLength="{STEP}"/>')
    rou = (f'<routes>{vt}<route id="r" edges="e"/>'
           f'<vehicle id="lead" type="c" route="r" depart="0" departPos="{x_lead:.2f}"'
           f' departSpeed="{v0}" departLane="0"/>'
           f'<vehicle id="foll" type="c" route="r" depart="0" departPos="{x_foll:.2f}"'
           f' departSpeed="{v0}" departLane="0"/></routes>')
    (work / "r.rou.xml").write_text(rou, encoding="utf-8")
    cfg = work / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="40"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="20261101"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")
    return cfg


def run(v0: float, gap0: float, tag: str) -> dict:
    work = OUT / tag
    cfg = build(work, v0, gap0, tag)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    BRAKE_T = 10.0
    PULSE = 2.0
    peak_d = peak_c = 0.0
    peak_gap_at = None
    g_at_brake = None
    n_steps = 0
    brake = False
    try:
        for k in range(int(40 / STEP)):
            t = round(k * STEP, 3)
            ids = traci.vehicle.getIDList()
            if "lead" not in ids or "foll" not in ids:
                traci.simulationStep()
                continue
            if t >= BRAKE_T:
                if not brake:
                    brake = True
                    traci.vehicle.setSpeedMode("lead", 0)
                    g_at_brake = round((traci.vehicle.getLanePosition("lead")
                                        - traci.vehicle.getLanePosition("foll")) - VEH_LEN, 3)
                if n_steps * STEP < PULSE - 1e-9:
                    v = traci.vehicle.getSpeed("lead")
                    traci.vehicle.setSpeed("lead", max(0.0, v - 9.0 * STEP))
                    n_steps += 1
                elif n_steps == int(PULSE / STEP):
                    traci.vehicle.setSpeedMode("lead", 31)
                    n_steps += 1
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            if "lead" not in ids or "foll" not in ids:
                continue
            xf = traci.vehicle.getLanePosition("foll")
            vf = traci.vehicle.getSpeed("foll")
            xl = traci.vehicle.getLanePosition("lead")
            vl = traci.vehicle.getSpeed("lead")
            g = (xl - xf) - VEH_LEN
            cc = vf - vl
            if g > 0 and cc > 0:
                d = cc * cc / (2 * g)
                if d > peak_d:
                    peak_d, peak_gap_at = d, g
                peak_c = max(peak_c, cc)
    finally:
        traci.close()
    return {"tag": tag, "v0": v0, "gap_set": gap0, "gap_at_brake": g_at_brake,
            "peak_drac": round(peak_d, 4), "peak_gap_at_peak": round(peak_gap_at, 2)
            if peak_gap_at else None,
            "peak_closing": round(peak_c, 3)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"{'条件':<34}{'施刹净距':>9}{'峰值闭合':>10}{'峰值DRAC':>10}{'峰值时净距':>11}")
    res = []
    for v0, gap0, tag in [(30.0, 40.0, "A_30_40"), (30.0, 60.0, "A_30_60"),
                          (30.0, 80.0, "A_30_80"), (21.378, 36.364, "B_21_36"),
                          (21.378, 51.91, "B_21_52")]:
        r = run(v0, gap0, tag)
        res.append(r)
        print(f"v0={v0:5.1f} 设定净距={gap0:5.1f}{'':<10}"
              f"{r['gap_at_brake']:>9}{r['peak_closing']:>10}"
              f"{r['peak_drac']:>10}{str(r['peak_gap_at_peak']):>11}", flush=True)
    import json
    (OUT / "samechain.json").write_text(json.dumps(res, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    print(f"\nwritten: {OUT/'samechain.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())