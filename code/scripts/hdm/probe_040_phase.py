"""0.4.0 短探针：验证「setPreviousSpeed + setSpeed」能否复现内核的头车步进相位

问题（GPT 指出）：内核头车每步位移 = v_profile(t_k)·dt（步初速度覆写，acc=0）。
草稿脚本只 setSpeed(v_profile(t_k))，SUMO 用梯形 0.5(v_actual_prev + v_new)·dt，
两式不等 → 坡道累计差约 0.478 m。

待验三种做法，看哪一种与内核逐帧一致：
  A 只 setSpeed
  B setPreviousSpeed(v_target) + setSpeed(v_target)   ← 想让梯形退化成 v·dt
  C setSpeed(v_target) 且把 step-method 关掉 ballistic（纯 Euler 用 step-begin 速度）

判据：600 步坡道内，SUMO 头车位置与解析「Σ v_profile(t_k)·dt」差 ≤1e-9。
"""
import os, sys, json
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
SUMO_HOME = r"C:\Program Files (x86)\Eclipse\Sumo"
sys.path.insert(0, os.path.join(SUMO_HOME, "tools"))
import numpy as np
import hdm_core as H
import traci

NET = r"D:/shen/TJU/AAD/code/networks/hdm_recon_long/hdm_recon_long.net.xml"
VT = r"D:/shen/TJU/AAD/code/networks/hdm_recon_long/vtypes.add.xml"
DT = 0.05
WARM, RAMP, VTGT = 40.0, 6.0, 3.0
V_EQ = H.equilibrium_speed(45.0)
NST = 1400          # 70 s（覆盖 40 s 预热 + 6 s 坡道 + 24 s）


def profile(t):
    if t < WARM:
        return V_EQ
    return V_EQ + (VTGT - V_EQ) * (min(t - WARM, RAMP) / RAMP)


def analytic():
    """内核口径：x[k+1] = x[k] + v_profile(t_k)*dt"""
    x = [0.0]
    for k in range(NST):
        x.append(x[-1] + profile(k * DT) * DT)
    return np.array(x)


def run(mode):
    extra = ["--step-method.ballistic", "true"] if mode != "C" else []
    cfg = [os.path.join(SUMO_HOME, "bin", "sumo.exe"), "-n", NET, "-a", VT,
           "--step-length", str(DT), "--collision.mingap-factor", "0",
           "--collision.action", "warn", "--seed", "42", "--random", "false",
           "--no-step-log", "true", "--time-to-teleport", "-1", "--begin", "0"] + extra
    traci.start(cfg)
    try:
        traci.route.add("r0", ["main"])
        traci.vehicle.add("v0", "r0", typeID="CLEAN", departPos="1000",
                          departSpeed=str(V_EQ), departLane="0")
        traci.vehicle.setSpeedMode("v0", 0)
        traci.vehicle.setLaneChangeMode("v0", 0)
        traci.simulationStep()
        xs = [traci.vehicle.getLanePosition("v0")]
        for k in range(NST):
            tgt = profile(k * DT)
            if mode == "B":
                traci.vehicle.setPreviousSpeed("v0", float(tgt))
            traci.vehicle.setSpeed("v0", float(tgt))
            traci.simulationStep()
            xs.append(traci.vehicle.getLanePosition("v0"))
        return np.array(xs)
    finally:
        traci.close()


if __name__ == "__main__":
    ref = analytic() + 1000.0
    out = {}
    for mode in ("A", "B", "C"):
        try:
            x = run(mode)
            d = np.abs(x - ref)
            out[mode] = dict(max_err=float(np.max(d)), err_at_ramp_end=float(d[1120]),
                             final=float(x[-1] - ref[-1]))
        except Exception as e:
            out[mode] = {"error": repr(e)}
        print(mode, json.dumps(out[mode], ensure_ascii=False), flush=True)
    print("analytic_end", float(ref[-1]))
    json.dump(out, open("probe_040_phase.json", "w"), indent=1, ensure_ascii=False)