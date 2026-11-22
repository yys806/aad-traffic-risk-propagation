"""0.5.0 硬判据 7.1#8：带消息的双平台烟雾对账（SUMO vs Python）

三次运行：seed0 A0（无消息回归）+ seed0 A3（20 辆高密度）+ seed2 A1（1 辆，净距最极限）
时长 400 s（8000 步），与主分析同窗同参。

判据：
  ① 短窗 0–60 s（1201 帧）逐帧位置差、速度差 ≤1e-9
  ② 逐车事件段数完全一致（gap=0.30 与 gap=0 各比一次）
  ③ 消息状态逐车一致：t_action、cap_bind_frames
  ④ 逐车峰值相对差 ≤1e-6、最小净距差 ≤1e-6 m
  ⑤ 全程零接触、零越界、逐帧 ID 完整、末帧有限值
"""
import os, sys, json
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
SUMO_HOME = r"C:\Program Files (x86)\Eclipse\Sumo"
sys.path.insert(0, os.path.join(SUMO_HOME, "tools"))
import numpy as np
import hdm_core_v2 as H
from hdm_msg import MsgState, count_episodes
import traci

NET = r"D:/shen/TJU/AAD/code/networks/hdm_recon_long/hdm_recon_long.net.xml"
VT = r"D:/shen/TJU/AAD/code/networks/hdm_recon_long/vtypes.add.xml"
DT = 0.05
N = 100
HW = 45.0
TP = 1.0
BMAX = 9.0
WARM, RAMP, OBS = 40.0, 6.0, 360.0
VTGT = 3.0
X0 = 5000.0
NET_LEN = 13000.0
DRAC_TH, MERGE_GAP = 3.4, 0.30
ZONE = list(range(20, 100))
ARMS = {"A0": None, "A1": [60], "A2": [20, 30, 40, 50, 60, 70, 80, 90],
        "A3": list(range(20, 100, 4))}
CASES = [("A0", 0), ("A3", 0), ("A1", 2)]


class GateFail(Exception):
    pass


def run_sumo(arm, seed, t_deliver):
    v_eq = H.equilibrium_speed(HW)
    bmax_arr = np.full(N, BMAX); Tp = np.full(N, TP)
    rng = np.random.default_rng(seed)
    ws = rng.standard_normal(N); wv = rng.standard_normal(N)
    ms = None
    if ARMS[arm]:
        ms = MsgState(receivers=ARMS[arm], t_deliver=t_deliver, factor=0.70, rate=1.0, N=N)

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
            traci.vehicle.add(vid, "r0", typeID="CLEAN", departPos=str(X0 - i * HW),
                              departSpeed=str(v_eq), departLane="0")
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setLaneChangeMode(vid, 0)
        traci.simulationStep()

        nsteps = int(round((WARM + OBS) / DT)); steps_warm = int(round(WARM / DT))
        hist_x = np.zeros((nsteps + 2, N)); hist_v = np.zeros((nsteps + 2, N))
        hist_a = np.zeros((nsteps + 2, N))
        for i in range(N):
            hist_x[0, i] = X0 - i * HW; hist_v[0, i] = v_eq
        expect = sorted("c%d" % i for i in range(N))
        drac = np.zeros((nsteps + 2, N))
        M = H.Metrics(N, v_eq, DT)
        e = np.exp(-DT / H.P.taur); sq = np.sqrt(2.0 * DT / H.P.taur)
        bad = dict(contact=0, oob=0, nonfinite=0, ids=0)

        for k in range(nsteps):
            if sorted(traci.vehicle.getIDList()) != expect:
                bad["ids"] += 1; raise GateFail(f"{arm}/s{seed} k={k} ID 不完整")
            x = np.empty(N); v = np.empty(N)
            for i in range(N):
                vid = "c%d" % i
                pi = traci.vehicle.getLanePosition(vid); vi = traci.vehicle.getSpeed(vid)
                if not (np.isfinite(pi) and np.isfinite(vi)):
                    bad["nonfinite"] += 1; raise GateFail(f"{arm}/s{seed} k={k} 非有限值")
                x[i] = pi; v[i] = vi
            if x.min() < 0.0 or x.max() > NET_LEN:
                bad["oob"] += 1; raise GateFail(f"{arm}/s{seed} k={k} 越界")
            hist_x[k], hist_v[k] = x, v
            if k < steps_warm:
                for i in range(1, N):
                    if (x[i - 1] - x[i] - H.P.L) <= 0.0:
                        bad["contact"] += 1

            v[0] = H.head_profile(k * DT, v_eq, VTGT, WARM, RAMP)
            na = H.car_accels(k, hist_x, hist_v, hist_a, N, 1, Tp, DT, True, ws, wv,
                              rng, e, sq, bmax_arr)
            na = np.minimum(np.maximum(na, -bmax_arr), H.P.a)
            v_new = np.maximum(v + na * DT, 0.0)
            acc = na
            if ms is not None:
                v_new, modified = ms.apply(v_new, v, k * DT, DT)
                if modified.any():
                    acc = na.copy()
                    acc[modified] = (v_new[modified] - v[modified]) / DT
            for i in range(N):
                vid = "c%d" % i
                traci.vehicle.setPreviousSpeed(vid, float(v[i]))
                traci.vehicle.setSpeed(vid, float(v_new[i]))
            traci.simulationStep()
            hist_a[k + 1] = acc

            xe = np.array([traci.vehicle.getLanePosition("c%d" % i) for i in range(N)])
            ve = np.array([traci.vehicle.getSpeed("c%d" % i) for i in range(N)])
            hist_x[k + 1], hist_v[k + 1] = xe, ve
            if k >= steps_warm:
                for i in range(1, N):
                    g = xe[i - 1] - xe[i] - H.P.L
                    dvv = ve[i] - ve[i - 1]
                    drac[k + 1, i] = (dvv * dvv / (2.0 * g)) if (g > 0 and dvv > 0) else 0.0
            M.update(k, xe, ve, steps_warm)
        return dict(hist_x=hist_x, hist_v=hist_v, drac=drac, M=M, ms=ms,
                    bad=bad, nsteps=nsteps)
    finally:
        traci.close()


def run_py(arm, seed, t_deliver):
    ms = None
    if ARMS[arm]:
        ms = MsgState(receivers=ARMS[arm], t_deliver=t_deliver, factor=0.70, rate=1.0, N=N)
    r = H.run(N=N, hw=HW, n_a=1, Tprime=TP, seed=seed, v_target=VTGT, ramp=RAMP,
              warm=WARM, observe=OBS, noise=True, bmax=BMAX, record=True,
              drac_log=True, msg_state=ms, x0=X0)
    return r, ms


def main():
    out = {"cases": [], "fails": []}
    for arm, seed in CASES:
        # 先跑 Python 拿 t_deliver（与主分析同口径）
        rC0 = H.run(seed=seed, v_target=None, **dict(N=N, hw=HW, n_a=1, Tprime=TP,
                    ramp=RAMP, warm=WARM, observe=OBS, noise=True, bmax=BMAX,
                    record=True, x0=X0))
        rA0 = H.run(seed=seed, v_target=VTGT, **dict(N=N, hw=HW, n_a=1, Tprime=TP,
                    ramp=RAMP, warm=WARM, observe=OBS, noise=True, bmax=BMAX,
                    record=True, x0=X0))
        dv = rC0["hist_v"] - rA0["hist_v"]
        hv0 = rA0["hist_v"][:, 0]
        m_src = next(m for m in range(800, hv0.shape[0]) if hv0[m] < rA0["v_eq"] - 0.5)
        t_deliver = m_src * DT + 0.6

        S = run_sumo(arm, seed, t_deliver)
        P, pms = run_py(arm, seed, t_deliver)
        n = S["nsteps"]
        rx = P["hist_x"][:n + 1]; rv = P["hist_v"][:n + 1]
        ex = np.abs(S["hist_x"][:n + 1] - rx); ev = np.abs(S["hist_v"][:n + 1] - rv)
        nf = 1201
        rec = dict(arm=arm, seed=seed, t_deliver=t_deliver,
                   early_max_err_x=float(np.max(ex[:nf])),
                   early_max_err_v=float(np.max(ev[:nf])),
                   max_err_x=float(np.nanmax(ex)), max_err_v=float(np.nanmax(ev)),
                   contact=S["bad"]["contact"])
        # 逐车事件段数（两种合并容差）
        for gname, gap in (("gap030", 0.30), ("gap000", 0.0)):
            es, ep = 0, 0
            for i in ZONE:
                es += len(count_episodes(S["drac"][m_src:, i], DT, DRAC_TH, merge_gap_s=gap))
                ep += len(count_episodes(P["drac"][m_src:, i], DT, DRAC_TH, merge_gap_s=gap))
            rec[gname] = dict(sumo=es, py=ep, equal=(es == ep))
        # 逐车峰值/净距
        pk = np.max(np.abs(S["M"].max_drac[ZONE] - np.asarray(P["max_drac"])[ZONE]))
        gp = np.max(np.abs(S["M"].min_gap[ZONE] - np.asarray(P["min_gap"])[ZONE]))
        pkl = max(abs(pk) / max(abs(np.asarray(P["max_drac"])[ZONE]).max(), 1e-12), 0)
        rec.update(peak_rel=float(pkl), gap_abs=float(gp))
        # 消息状态
        if pms is not None:
            ta_s = {i: (None if np.isnan(S["ms"].t_action[i]) else float(S["ms"].t_action[i])) for i in ARMS[arm]}
            ta_p = {i: (None if np.isnan(pms.t_action[i]) else float(pms.t_action[i])) for i in ARMS[arm]}
            rec["msg_equal"] = bool(ta_s == ta_p)
            rec["bind_equal"] = bool(all(int(S["ms"].cap_bind_frames[i]) == int(pms.cap_bind_frames[i])
                                         for i in ARMS[arm]))
        out["cases"].append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)

        if rec["early_max_err_x"] > 1e-9: out["fails"].append(f"{arm}/s{seed} 短窗位置 {rec['early_max_err_x']:.2e}")
        if rec["early_max_err_v"] > 1e-9: out["fails"].append(f"{arm}/s{seed} 短窗速度 {rec['early_max_err_v']:.2e}")
        if not rec["gap030"]["equal"]: out["fails"].append(f"{arm}/s{seed} gap030 事件段数不等")
        if not rec["gap000"]["equal"]: out["fails"].append(f"{arm}/s{seed} gap000 事件段数不等")
        if rec["peak_rel"] > 1e-6: out["fails"].append(f"{arm}/s{seed} 峰值相对差 {rec['peak_rel']:.2e}")
        if rec["gap_abs"] > 1e-6: out["fails"].append(f"{arm}/s{seed} 净距差 {rec['gap_abs']:.2e} m")
        if rec["contact"]: out["fails"].append(f"{arm}/s{seed} 接触 {rec['contact']}")
        if pms is not None and not (rec.get("msg_equal") and rec.get("bind_equal")):
            out["fails"].append(f"{arm}/s{seed} 消息状态不一致")

    out["pass"] = len(out["fails"]) == 0
    json.dump(out, open("smoke_050.json", "w"), indent=1, ensure_ascii=False)
    print(("ALL SMOKE PASS" if out["pass"] else "FAILS: " + str(out["fails"][:8])), flush=True)
    sys.exit(0 if out["pass"] else 1)


if __name__ == "__main__":
    main()