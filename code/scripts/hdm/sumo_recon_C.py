"""测试 C：开环轨迹回放对账（0.3.9 v8 §六C）

做法：
  1. 用 hdm_core.py 跑 5 车 / 120 s / 车头距 45 m / T'=1.0 / n_a=1 / b_max=9 / 无噪声
  2. 把该轨迹的「速度序列」原样作为 setSpeed 指令喂给 SUMO（开环，不回读反馈）
  3. SUMO 自己积分位置；逐帧比对 v 与 x

这是「两边同一条轨迹」的硬证据：SUMO 不参与动力学，只做积分。
任何偏差只能来自积分器 / 粘性 / 裁剪 / 插入，不会来自模型实现差异。
"""
import os, sys, json
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
SUMO_HOME = r"C:\Program Files (x86)\Eclipse\Sumo"
sys.path.insert(0, os.path.join(SUMO_HOME, "tools"))
import numpy as np
import hdm_core as H
import traci

NET = r"D:/shen/TJU/AAD/code/networks/hdm_recon/hdm_recon.net.xml"
DT = 0.05
N = 5
HW = 45.0
TP = 1.0
WARM = 40.0
OBS = 80.0
OFFSET = 1000.0


def build_reference():
    r = H.run(N=N, hw=HW, n_a=1, Tprime=TP, seed=0, v_target=None,
              warm=WARM, observe=OBS, noise=False, bmax=9.0, record=True)
    return r


def replay(ref):
    hv = ref["hist_v"]          # (total+1, N)，hist_v[k] 是第 k 步开始时的速度
    hx = ref["hist_x"]          # 内核自己算出的位置（不是本脚本重积分）
    nsteps = hv.shape[0] - 1
    x = hx

    cfg = [os.path.join(SUMO_HOME, "bin", "sumo.exe"), "-n", NET,
           "--step-length", str(DT), "--step-method.ballistic", "true",
           "--collision.mingap-factor", "0", "--collision.action", "warn",
           "--seed", "42", "--random", "false", "--no-step-log", "true",
           "--time-to-teleport", "-1", "--begin", "0"]
    traci.start(cfg)
    try:
        tid = "CLEAN"
        traci.vehicletype.copy("DEFAULT_VEHTYPE", tid)
        for kk, vv in (("length", 5.0), ("minGap", 2.0), ("maxSpeed", 50.0),
                       ("accel", 3.0), ("decel", 4.5), ("emergencyDecel", 9.0),
                       ("speedFactor", 1.0), ("speedDev", 0.0), ("sigma", 0.0)):
            traci.vehicletype.setParameter(tid, kk, str(vv))
        traci.route.add("r0", ["main"])
        # 下游→上游插入（车 0 最前）
        for i in range(N):
            vid = "c%d" % i
            traci.vehicle.add(vid, "r0", typeID=tid,
                              departPos=str(OFFSET + float(x[0, i])),
                              departSpeed=str(float(hv[0, i])), departLane="0")
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setLaneChangeMode(vid, 0)
            traci.vehicle.setMaxSpeed(vid, 50.0)
        traci.simulationStep()

        # 对齐：hdm_core 的 hist_v[0] 是初态，SUMO 插车后第 0 步开始也应等于它
        ev, ex = [], []
        vanish = []
        for k in range(nsteps):
            ids = traci.vehicle.getIDList()
            if len(ids) != N:
                vanish.append(dict(k=k, ids=list(ids)))
                break
            for i in range(N):
                vid = "c%d" % i
                v_now = traci.vehicle.getSpeed(vid)
                p_now = traci.vehicle.getLanePosition(vid)
                ev.append(abs(v_now - float(hv[k, i])))
                ex.append(abs(p_now - (OFFSET + float(x[k, i]))))
                traci.vehicle.setSpeed(vid, float(hv[k + 1, i]))
            traci.simulationStep()
        return dict(max_err_v=float(max(ev)), max_err_x=float(max(ex)),
                    n_frames=len(ev) // N, vanished=vanish,
                    collisions=traci.simulation.getCollisionCount() if hasattr(traci.simulation, "getCollisionCount") else None,
                    teleports=traci.simulation.getStartingTeleportNumber(),
                    v_eq=float(ref["v_eq"]))
    finally:
        traci.close()


if __name__ == "__main__":
    ref = build_reference()
    out = replay(ref)
    out["N"] = N
    out["hw"] = HW
    out["Tprime"] = TP
    out["warm_s"] = WARM
    out["obs_s"] = OBS
    print(json.dumps(out, ensure_ascii=False, indent=1))
    json.dump(out, open("recon_C_openloop.json", "w"), indent=1, ensure_ascii=False)
