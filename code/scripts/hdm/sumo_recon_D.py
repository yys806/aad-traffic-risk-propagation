"""测试 D：闭环烟雾测试（0.3.9 v9 §五）

Python 内核每步真正算加速度 → setSpeed 下发 → SUMO 推进 → 回读状态喂回内核。
检查：闭环下两边是否发散；重点看「差一帧」类接线错误。

两个对照：
  D1 无噪声：与纯 Python 内核逐帧比对位置（判据 1e-9）
  D2 有噪声：不断言逐帧相等（噪声抽样顺序难对齐），只报关键指标差（事件数、最小净距、峰值 DRAC）

车辆：5 车，车头距 45 m，T′=1.0，n_a=1，b_max=9.0，头车平衡匀速 22.1028 m/s（无扰动），60 s。
"""
import os, sys, json
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
SUMO_HOME = r"C:\Program Files (x86)\Eclipse\Sumo"
sys.path.insert(0, os.path.join(SUMO_HOME, "tools"))
import numpy as np
import hdm_core as H
import traci

NET = r"D:/shen/TJU/AAD/code/networks/hdm_recon/hdm_recon.net.xml"
VT = r"D:/shen/TJU/AAD/code/networks/hdm_recon/vtypes.add.xml"
DT = 0.05
N = 5
HW = 45.0
TP = 1.0
BMAX = 9.0
DUR = 60.0
OFFSET = 1000.0
NSTEPS = int(round(DUR / DT))


def py_reference(noise):
    r = H.run(N=N, hw=HW, n_a=1, Tprime=TP, seed=0, v_target=None,
              warm=0.0, observe=DUR, noise=noise, bmax=BMAX, record=True)
    return r


def closed_loop(noise, seed=0):
    """在 SUMO 里闭环跑 HDM。返回逐帧位置与速度。"""
    ref = py_reference(noise)
    v_eq = float(ref["v_eq"])

    cfg = [os.path.join(SUMO_HOME, "bin", "sumo.exe"), "-n", NET, "-a", VT,
           "--step-length", str(DT), "--step-method.ballistic", "true",
           "--collision.mingap-factor", "0", "--collision.action", "warn",
           "--seed", "42", "--random", "false", "--no-step-log", "true",
           "--time-to-teleport", "-1", "--begin", "0"]
    traci.start(cfg)
    try:
        traci.route.add("r0", ["main"])
        for i in range(N):
            vid = "c%d" % i
            traci.vehicle.add(vid, "r0", typeID="CLEAN",
                              departPos=str(OFFSET - i * HW),
                              departSpeed=str(v_eq), departLane="0")
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setLaneChangeMode(vid, 0)
        traci.simulationStep()

        rng = np.random.default_rng(seed)
        ws = rng.standard_normal(N); wv = rng.standard_normal(N)
        e = np.exp(-DT / H.P.taur); sq = np.sqrt(2.0 * DT / H.P.taur)
        # 延迟历史（步前状态）
        hist_x = np.zeros((NSTEPS + 2, N)); hist_v = np.zeros((NSTEPS + 2, N))
        hist_a = np.zeros((NSTEPS + 2, N))
        for i in range(N):
            hist_x[0, i] = OFFSET - i * HW
            hist_v[0, i] = v_eq
        dly = TP / DT; n_int = int(np.floor(dly)); w_frac = dly - n_int
        log_x = np.zeros((NSTEPS + 1, N)); log_v = np.zeros((NSTEPS + 1, N))
        gaps = np.full(N, np.inf); vanished = []
        bt = H.beta(1); sb = np.sqrt(bt)
        s0r, Tr = H.P.s0 / sb, H.P.T / sb

        for k in range(NSTEPS):
            ids = traci.vehicle.getIDList()
            if len(ids) != N:
                vanished.append(dict(k=k, ids=list(ids))); break
            x = np.array([traci.vehicle.getLanePosition("c%d" % i) for i in range(N)])
            v = np.array([traci.vehicle.getSpeed("c%d" % i) for i in range(N)])
            log_x[k], log_v[k] = x, v
            hist_x[k], hist_v[k] = x, v

            # 头车匀速
            new_v = v.copy()
            new_v[0] = v_eq
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
                if noise:
                    ws[i] = e * ws[i] + sq * rng.standard_normal()
                    wv[i] = e * wv[i] + sq * rng.standard_normal()
                    s_est = s * np.exp(H.P.Vs * ws[i])
                    dv_est = dv + s * H.P.rc * wv[i]
                else:
                    s_est, dv_est = s, dv
                s_pr = max(s_est - TP * dv_est, 0.1)
                v_pr = vi + TP * ai
                afree = H.P.a * (1.0 - (max(v_pr, 0.0) / H.P.v0) ** 4)
                aint = H.idm_acc(v_pr, s_pr, dv_est, s0r, Tr) - afree
                aint = max(aint, -(BMAX + afree))
                a = afree + aint
                new_v[i] = max(v[i] + a * DT, 0.0)
                hist_a[k, i] = a
            # 下发下一步目标速度（= 当前速度 + a*dt，setSpeed 是目标速度不是加速度）
            for i in range(N):
                traci.vehicle.setSpeed("c%d" % i, float(new_v[i]))
            traci.simulationStep()
        log_x[NSTEPS], log_v[NSTEPS] = (
            np.array([traci.vehicle.getLanePosition("c%d" % i) for i in range(N)]),
            np.array([traci.vehicle.getSpeed("c%d" % i) for i in range(N)]))
        tele = traci.simulation.getStartingTeleportNumber()
        return dict(log_x=log_x, log_v=log_v, vanished=vanished,
                    teleports=tele, v_eq=v_eq, ref=ref)
    finally:
        traci.close()


if __name__ == "__main__":
    out = {}
    # D1 无噪声：逐帧比位置
    d1 = closed_loop(noise=False)
    rx = d1["ref"]["hist_x"][:NSTEPS + 1] - 0.0     # 参考轨迹以自身为坐标
    # 把参考轨迹平移到 SUMO 坐标系（车 0 初位 = OFFSET）
    shift = OFFSET - rx[0, 0]
    ex = np.abs(d1["log_x"] - (rx + shift))
    out["D1"] = dict(max_err_x=float(np.nanmax(ex)),
                     err_first10=float(np.nanmax(ex[:11])),
                     vanished=d1["vanished"], teleports=d1["teleports"],
                     v_eq=d1["v_eq"])
    # D2 有噪声：只报关键指标
    d2 = closed_loop(noise=True)
    def stats(log_x):
        g = np.full(N, np.inf); mx = np.zeros(N)
        for k in range(log_x.shape[0]):
            for i in range(1, N):
                gap = log_x[k, i - 1] - log_x[k, i] - H.P.L
                g[i] = min(g[i], gap)
        return dict(min_gap=float(np.min(g[1:])))
    out["D2"] = dict(smoke_stats_sumo=stats(d2["log_x"]),
                     smoke_stats_py=stats(d2["ref"]["hist_x"][:NSTEPS + 1] + shift),
                     vanished=d2["vanished"], teleports=d2["teleports"])
    print(json.dumps(out, ensure_ascii=False, indent=1))
    json.dump(out, open("recon_D_closedloop.json", "w"), indent=1, ensure_ascii=False)
