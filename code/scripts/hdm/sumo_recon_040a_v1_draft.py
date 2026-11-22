"""0.4.0a：事件场景的 Python↔SUMO 严格对账（无噪声、单种子、逐车逐帧）

配置与 0.3.5 §4.1 完全一致：100 车 / 45 m / T'=1.0 / n_a=1 / b_max=9.0 / 无噪声
头车：40 s 平衡匀速 -> 6 s 线性降到 3.0 m/s -> 保持；观测 300 s（总 340 s，6800 步）
对照臂：头车全程平衡匀速

SUMO 侧不重新实现 HDM：直接 import hdm_core，用它的 P / beta / idm_acc / equilibrium_speed，
加速度循环体照抄 hdm_core.run（同一套式子、同一套裁剪顺序）。
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
N = 100
HW = 45.0
TP = 1.0
BMAX = 9.0
WARM = 40.0
RAMP = 6.0
OBS = 300.0
V_TARGET = 3.0
X0 = 5000.0
DRAC_TH = 3.4
DRAC_MIN_DUR = 0.2


def run_sumo(v_target):
    """在 SUMO 里跑完整事件场景，返回逐车统计与逐帧轨迹。"""
    v_eq = H.equilibrium_speed(HW)
    bt = H.beta(1); sb = np.sqrt(bt)
    s0r, Tr = H.P.s0 / sb, H.P.T / sb

    cfg = [os.path.join(SUMO_HOME, "bin", "sumo.exe"), "-n", NET, "-a", VT,
           "--step-length", str(DT), "--step-method.ballistic", "true",
           "--collision.mingap-factor", "0", "--collision.action", "warn",
           "--seed", "42", "--random", "false", "--no-step-log", "true",
           "--time-to-teleport", "-1", "--begin", "0"]
    traci.start(cfg)
    try:
        traci.route.add("r0", ["main"])
        for i in range(N):                       # 下游 -> 上游
            vid = "c%d" % i
            traci.vehicle.add(vid, "r0", typeID="CLEAN",
                              departPos=str(X0 - i * HW),
                              departSpeed=str(v_eq), departLane="0")
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setLaneChangeMode(vid, 0)
        traci.simulationStep()

        nsteps = int(round((WARM + OBS) / DT))
        n_int = int(np.floor(TP / DT)); w_frac = TP / DT - n_int
        hist_x = np.zeros((nsteps + 2, N)); hist_v = np.zeros((nsteps + 2, N))
        hist_a = np.zeros((nsteps + 2, N))
        log_x = np.zeros((nsteps + 1, N)); log_v = np.zeros((nsteps + 1, N))

        # 初态对齐内核：x = X0 - i*hw, v = v_eq
        for i in range(N):
            hist_x[0, i] = X0 - i * HW
            hist_v[0, i] = v_eq

        max_drac = np.zeros(N); min_gap = np.full(N, np.inf)
        drac_run = np.zeros(N); drac_max_run = np.zeros(N)
        vanish = []

        for k in range(nsteps):
            ids = traci.vehicle.getIDList()
            if len(ids) != N:
                vanish.append(dict(k=k, n=len(ids))); break
            x = np.array([traci.vehicle.getLanePosition("c%d" % i) for i in range(N)])
            v = np.array([traci.vehicle.getSpeed("c%d" % i) for i in range(N)])
            log_x[k], log_v[k] = x, v
            hist_x[k], hist_v[k] = x, v

            t = k * DT
            # ---- 头车剖面（与内核一致）----
            if v_target is None:
                v_lead = v_eq
            elif t < WARM:
                v_lead = v_eq
            else:
                tt = min(t - WARM, RAMP)
                v_lead = v_eq + (v_target - v_eq) * (tt / RAMP)
            new_v = v.copy()
            new_v[0] = v_lead
            hist_a[k, 0] = 0.0

            kd = max(k - n_int, 0); kd2 = max(k - n_int - 1, 0)
            for i in range(1, N):
                xi = (1 - w_frac) * hist_x[kd, i] + w_frac * hist_x[kd2, i]
                vi = (1 - w_frac) * hist_v[kd, i] + w_frac * hist_v[kd2, i]
                ai = (1 - w_frac) * hist_a[kd, i] + w_frac * hist_a[kd2, i]
                j = i - 1
                xj = (1 - w_frac) * hist_x[kd, j] + w_frac * hist_x[kd2, j]
                vj = (1 - w_frac) * hist_v[kd, j] + w_frac * hist_v[kd2, j]
                s = max(xj - xi - H.P.L, 0.2)
                dv = vi - vj
                s_pr = max(s - TP * dv, 0.1)          # 无噪声：s_est=s, dv_est=dv
                v_pr = vi + TP * ai
                afree = H.P.a * (1.0 - (max(v_pr, 0.0) / H.P.v0) ** 4)
                aint = H.idm_acc(v_pr, s_pr, dv, s0r, Tr) - afree
                aint = max(aint, -(BMAX + afree))
                a = afree + aint
                hist_a[k, i] = a
                new_v[i] = max(v[i] + a * DT, 0.0)

            for i in range(N):                       # 每帧必发（粘性）
                traci.vehicle.setSpeed("c%d" % i, float(new_v[i]))
            traci.simulationStep()

            # ---- 观测期统计（照抄内核）----
            if k >= int(round(WARM / DT)):
                for i in range(1, N):
                    gap = x[i - 1] - x[i] - H.P.L
                    min_gap[i] = min(min_gap[i], gap)
                    dvv = v[i] - v[i - 1]
                    dr = (dvv * dvv / (2.0 * gap)) if (gap > 0 and dvv > 0) else 0.0
                    max_drac[i] = max(max_drac[i], dr)
                    if dr >= DRAC_TH:
                        drac_run[i] += DT
                        drac_max_run[i] = max(drac_max_run[i], drac_run[i])
                    else:
                        drac_run[i] = 0.0

        tele = traci.simulation.getStartingTeleportNumber()
        return dict(log_x=log_x, log_v=log_v, max_drac=max_drac, min_gap=min_gap,
                    event=(drac_max_run >= DRAC_MIN_DUR), vanish=vanish,
                    teleports=tele, v_eq=v_eq, nsteps=nsteps)
    finally:
        traci.close()


def main():
    out = {"config": dict(N=N, hw=HW, Tprime=TP, bmax=BMAX, warm=WARM, ramp=RAMP,
                          obs=OBS, v_target=V_TARGET, x0=X0, dt=DT)}
    for arm, vt in (("source", V_TARGET), ("control", None)):
        r = run_sumo(vt)
        ref = H.run(N=N, hw=HW, n_a=1, Tprime=TP, seed=0, v_target=vt,
                    warm=WARM, observe=OBS, noise=False, bmax=BMAX, record=True)
        n = r["nsteps"]
        rx = ref["hist_x"][:n + 1] - ref["hist_x"][0, 0] + X0   # 平移到 SUMO 坐标
        rv = ref["hist_v"][:n + 1]
        ex = np.abs(r["log_x"] - rx)
        ev = np.abs(r["log_v"] - rv)
        out[arm] = dict(
            sumo_events=int(r["event"][1:].sum()),
            py_events=int(ref["event"][1:].sum()),
            sumo_peak=float(np.nanmax(r["max_drac"][1:])),
            py_peak=float(np.nanmax(ref["max_drac"][1:])),
            sumo_min_gap=float(np.min(r["min_gap"][1:])),
            py_min_gap=float(np.min(ref["min_gap"][1:])),
            max_err_x=float(np.nanmax(ex)),
            max_err_v=float(np.nanmax(ev)),
            event_mismatch=int(np.sum(r["event"][1:] != ref["event"][1:])),
            vanish=r["vanish"], teleports=r["teleports"], frames=n,
        )
        print(arm, json.dumps(out[arm], ensure_ascii=False), flush=True)
    json.dump(out, open("recon_040a.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
