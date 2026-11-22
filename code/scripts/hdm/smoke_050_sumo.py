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
from hdm_msg import MsgState, Message, count_episodes
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
        "A3": list(range(20, 100, 4)),
        "A2L": [20, 30, 40, 50, 60, 70, 80, 90],
        "A3L": list(range(20, 100, 4)),
        "A2P": [20, 30, 40, 50, 60, 70, 80, 90],
        "A3P": list(range(20, 100, 4)),
        "A3": list(range(20, 100, 4))}
# 三例已通过（A0/A3/A1）；本轮补四条早晚对照臂，重点验逐车送达在 SUMO 侧一致
CASES = [("A2P", 0), ("A3P", 0), ("A2L", 0), ("A3L", 0)]


class GateFail(Exception):
    pass


def run_sumo(arm, seed, t_deliver, pay):
    v_eq = H.equilibrium_speed(HW)
    bmax_arr = np.full(N, BMAX); Tp = np.full(N, TP)
    rng = np.random.default_rng(seed)
    ws = rng.standard_normal(N); wv = rng.standard_normal(N)
    ms = None
    if ARMS[arm]:
        msg = Message(event_id=seed, t_src=pay["t_src"], x_src=pay["x_src"],
                      v_src=pay["v_src"],
                      receivers=ARMS[arm], t_deliver=t_deliver, factor=0.70, rate=1.0)
        ms = MsgState(receivers=ARMS[arm], t_deliver=t_deliver, factor=0.70, rate=1.0,
                      N=N, message=msg)

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
                v_new, modified = ms.apply(v_new, v, (k + 1) * DT, DT, x=x)
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


def run_py(arm, seed, t_deliver, pay):
    ms = None
    if ARMS[arm]:
        msg = Message(event_id=seed, t_src=pay["t_src"], x_src=pay["x_src"],
                      v_src=pay["v_src"],
                      receivers=ARMS[arm], t_deliver=t_deliver, factor=0.70, rate=1.0)
        ms = MsgState(receivers=ARMS[arm], t_deliver=t_deliver, factor=0.70, rate=1.0,
                      N=N, message=msg)
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

        pay = dict(t_src=float(m_src * DT),
                   x_src=float(rA0["hist_x"][m_src, 0]),
                   v_src=float(rA0["hist_v"][m_src, 0]))
        # 逐车物理波到达时刻（与主分析同判据：C0−A0 差分 ≥0.5 m/s）
        if arm in ("A2P", "A3P"):
            dv_all = rC0["hist_v"] - rA0["hist_v"]
            steps_warm = int(round(WARM / DT))
            tarr = np.full(N, np.nan)
            for i in ARMS[arm]:
                idx = np.where(dv_all[steps_warm:, i] >= 0.5)[0]
                if len(idx):
                    tarr[i] = (idx[0] + steps_warm) * DT + 0.6
            for i in ARMS[arm]:
                if np.isnan(tarr[i]):
                    tarr[i] = t_deliver
            t_deliver = tarr
        S = run_sumo(arm, seed, t_deliver, pay)
        P, pms = run_py(arm, seed, t_deliver, pay)
        n = S["nsteps"]
        rx = P["hist_x"][:n + 1]; rv = P["hist_v"][:n + 1]
        ex = np.abs(S["hist_x"][:n + 1] - rx); ev = np.abs(S["hist_v"][:n + 1] - rv)
        nf = 1201
        _td_rec = (float(t_deliver) if np.ndim(t_deliver) == 0
                   else {int(i): float(t_deliver[i]) for i in ARMS[arm]})
        rec = dict(arm=arm, seed=seed, t_deliver=_td_rec,
                   early_max_err_x=float(np.max(ex[:nf])),
                   early_max_err_v=float(np.max(ev[:nf])),
                   max_err_x=float(np.nanmax(ex)), max_err_v=float(np.nanmax(ev)),
                   contact=S["bad"]["contact"])
        # 逐车事件段数（两种合并容差）——必须逐车比，不能只比总段数
        for gname, gap in (("gap030", 0.30), ("gap000", 0.0)):
            per_s, per_p = {}, {}
            for i in ZONE:
                per_s[i] = len(count_episodes(S["drac"][m_src:, i], DT, DRAC_TH, merge_gap_s=gap))
                per_p[i] = len(count_episodes(P["drac"][m_src:, i], DT, DRAC_TH, merge_gap_s=gap))
            diff_cars = [i for i in ZONE if per_s[i] != per_p[i]]
            rec[gname] = dict(sumo=int(sum(per_s.values())), py=int(sum(per_p.values())),
                              per_car_equal=(len(diff_cars) == 0),
                              diff_cars=diff_cars[:10], n_diff=len(diff_cars))
        # 逐车峰值相对差（分母用**该车自身**的 Python 峰值）+ 逐车净距差
        s_pk = np.asarray(S["M"].max_drac[ZONE]); p_pk = np.asarray(P["max_drac"])[ZONE]
        rel_vec = np.abs(s_pk - p_pk) / np.maximum(np.abs(p_pk), 1e-12)
        s_gp = np.asarray(S["M"].min_gap[ZONE]); p_gp = np.asarray(P["min_gap"])[ZONE]
        rec.update(peak_rel=float(np.max(rel_vec)), gap_abs=float(np.max(np.abs(s_gp - p_gp))),
                   worst_peak_car=int(ZONE[int(np.argmax(rel_vec))]))
        # 观测期接触（原稿只查了预热期 bad["contact"]）
        rec["contact_obs"] = int(getattr(S["M"], "contact_frames", 0))
        # 消息状态
        if pms is not None:
            ta_s = {i: (None if np.isnan(S["ms"].t_action[i]) else float(S["ms"].t_action[i])) for i in ARMS[arm]}
            ta_p = {i: (None if np.isnan(pms.t_action[i]) else float(pms.t_action[i])) for i in ARMS[arm]}
            rec["msg_equal"] = bool(ta_s == ta_p)
            rec["bind_equal"] = bool(all(int(S["ms"].cap_bind_frames[i]) == int(pms.cap_bind_frames[i])
                                         for i in ARMS[arm]))
            rec["vcap_equal"] = bool(all(
                (np.isnan(S["ms"].v_cap[i]) and np.isnan(pms.v_cap[i])) or
                (abs(float(S["ms"].v_cap[i]) - float(pms.v_cap[i])) <= 1e-12)
                for i in ARMS[arm]))
            # 载荷字段两侧一致（Gemini：原稿漏比 t_src/x_src）
            ps, pp = S["ms"].message.payload(), pms.message.payload()
            rec["payload_equal"] = bool(all(
                abs(float(ps[k]) - float(pp[k])) <= 1e-9
                for k in ("t_src", "x_src", "v_src")) and ps["event_id"] == pp["event_id"])
            rec["payload"] = pp
            rec["payload_matches_expected"] = bool(all(
                abs(float(pp[k]) - float(pay[k])) <= 1e-9 for k in ("t_src", "x_src", "v_src")))
            rec["sumo_receivers_bound"] = int(sum(int(S["ms"].cap_bind_frames[i]) > 0
                                                  for i in ARMS[arm]))
            # 非接收车零限幅（SUMO 侧）
            rec["nonrecv_bound"] = int(sum(int(S["ms"].cap_bind_frames[i])
                                           for i in range(N) if i not in ARMS[arm]))
            # 末帧有限性：查**实际写入的最后一行** hist[nsteps]，
            # 原版查 hist_x[-1]（索引 nsteps+1）是从未写入的零行（Gemini 第三轮）
            rec["last_finite"] = bool(np.all(np.isfinite(S["hist_x"][n])) and
                                      np.all(np.isfinite(S["hist_v"][n])))
            rec["last_row_is_written"] = bool(np.any(S["hist_x"][n] != 0.0))
        out["cases"].append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)

        if rec["early_max_err_x"] > 1e-9: out["fails"].append(f"{arm}/s{seed} 短窗位置 {rec['early_max_err_x']:.2e}")
        if rec["early_max_err_v"] > 1e-9: out["fails"].append(f"{arm}/s{seed} 短窗速度 {rec['early_max_err_v']:.2e}")
        if not rec["gap030"]["per_car_equal"]:
            out["fails"].append(f"{arm}/s{seed} gap030 逐车段数不等 {rec['gap030']['n_diff']} 辆 {rec['gap030']['diff_cars']}")
        if not rec["gap000"]["per_car_equal"]:
            out["fails"].append(f"{arm}/s{seed} gap000 逐车段数不等 {rec['gap000']['n_diff']} 辆 {rec['gap000']['diff_cars']}")
        if rec["peak_rel"] > 1e-6: out["fails"].append(f"{arm}/s{seed} 峰值相对差 {rec['peak_rel']:.2e}")
        if rec["gap_abs"] > 1e-6: out["fails"].append(f"{arm}/s{seed} 净距差 {rec['gap_abs']:.2e} m")
        if rec["contact"]: out["fails"].append(f"{arm}/s{seed} 预热期接触 {rec['contact']}")
        if rec["contact_obs"]: out["fails"].append(f"{arm}/s{seed} 观测期接触 {rec['contact_obs']}")
        if rec.get("payload_equal") is False:
            out["fails"].append(f"{arm}/s{seed} 载荷字段两侧不一致")
        if rec.get("payload_matches_expected") is False:
            out["fails"].append(f"{arm}/s{seed} 载荷与 A0 推出的事实不符")
        if ARMS[arm] and rec.get("sumo_receivers_bound", 0) < len(ARMS[arm]):
            out["fails"].append(
                f"{arm}/s{seed} SUMO 侧只有 {rec.get('sumo_receivers_bound')}/{len(ARMS[arm])} 辆被限幅")
        if rec.get("last_row_is_written") is False:
            out["fails"].append(f"{arm}/s{seed} 末帧行未写入")
        if rec.get("nonrecv_bound", 0) != 0:
            out["fails"].append(f"{arm}/s{seed} 非接收车被限幅 {rec['nonrecv_bound']}")
        if not rec.get("last_finite", True):
            out["fails"].append(f"{arm}/s{seed} 末帧非有限值")
        if pms is not None and not (rec.get("msg_equal") and rec.get("bind_equal")
                                    and rec.get("vcap_equal") and rec.get("payload_equal")):
            out["fails"].append(f"{arm}/s{seed} 消息状态不一致 msg={rec.get('msg_equal')} bind={rec.get('bind_equal')} vcap={rec.get('vcap_equal')}")

    out["pass"] = len(out["fails"]) == 0
    json.dump(out, open("smoke_050.json", "w"), indent=1, ensure_ascii=False)
    print(("ALL SMOKE PASS" if out["pass"] else "FAILS: " + str(out["fails"][:8])), flush=True)
    sys.exit(0 if out["pass"] else 1)


if __name__ == "__main__":
    main()