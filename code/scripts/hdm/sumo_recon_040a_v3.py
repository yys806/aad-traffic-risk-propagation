"""0.4.0a v3：事件场景 Python↔SUMO 对账（补全 GPT 要求的四项硬门）

相对 v2 的修改：
  ① 失败出口：任一硬门不过 → 打印首个差异 + sys.exit(1)，不再静默输出
  ② 逐车判定表：99 辆逐行比 max_drac / min_gap / 连续超阈时长 / 事件布尔量，写入 JSON
  ③ 硬门补全：逐帧精确 ID 集合、逐帧有限值、首末帧、碰撞与瞬移**逐步累积**
  ④ 真正共用：import hdm_core_v2 的 head_profile / car_accels / Metrics，桥接不再自写循环体

另加：误差指数增长率拟合（说明逐帧 300 s 一致性的物理上限）。
"""
import os, sys, json
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
SUMO_HOME = r"C:\Program Files (x86)\Eclipse\Sumo"
sys.path.insert(0, os.path.join(SUMO_HOME, "tools"))
import numpy as np
import hdm_core_v2 as H
import traci

NET = r"D:/shen/TJU/AAD/code/networks/hdm_recon_long/hdm_recon_long.net.xml"
VT = r"D:/shen/TJU/AAD/code/networks/hdm_recon_long/vtypes.add.xml"
DT = 0.05
N = 100
HW = 45.0
TP = 1.0
BMAX = 9.0
WARM, RAMP, OBS = 40.0, 6.0, 300.0
VTGT = 3.0
X0 = 5000.0
NET_LEN = 13000.0
GATES = dict(stat_rel=1e-6, early_frames=1200, early_abs=1e-9, gap_abs=1e-6)


class GateFail(Exception):
    pass


def run_arm(v_target):
    v_eq = H.equilibrium_speed(HW)
    bmax_arr = np.full(N, BMAX)
    Tp = np.full(N, TP)
    ws = np.zeros(N); wv = np.zeros(N)

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
                              departPos=str(X0 - i * HW),
                              departSpeed=str(v_eq), departLane="0")
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setLaneChangeMode(vid, 0)
        traci.simulationStep()

        nsteps = int(round((WARM + OBS) / DT))
        steps_warm = int(round(WARM / DT))
        hist_x = np.zeros((nsteps + 2, N))
        hist_v = np.zeros((nsteps + 2, N))
        hist_a = np.zeros((nsteps + 2, N))
        for i in range(N):
            hist_x[0, i] = X0 - i * HW
            hist_v[0, i] = v_eq
        expect_ids = sorted("c%d" % i for i in range(N))

        log_x = np.full((nsteps + 1, N), np.nan)
        log_v = np.full((nsteps + 1, N), np.nan)
        M = H.Metrics(N, v_eq, DT)
        coll_total = 0
        tele_total = 0
        first_diff = None

        for k in range(nsteps):
            # ---- 硬门 1：精确 ID 集合 ----
            ids = traci.vehicle.getIDList()
            if sorted(ids) != expect_ids:
                raise GateFail("k=%d ID 集合不符：缺 %s 多 %s" %
                               (k, set(expect_ids) - set(ids), set(ids) - set(expect_ids)))
            x = np.empty(N); v = np.empty(N)
            for i in range(N):
                vid = "c%d" % i
                pi = traci.vehicle.getLanePosition(vid)
                vi = traci.vehicle.getSpeed(vid)
                # ---- 硬门 2：逐帧有限值 ----
                if not (np.isfinite(pi) and np.isfinite(vi)):
                    raise GateFail("k=%d 车%d 出现非有限值 pos=%r v=%r" % (k, i, pi, vi))
                x[i] = pi; v[i] = vi
            # ---- 硬门 3：越界（上下界都查）----
            if x.min() < 0.0 or x.max() > NET_LEN:
                raise GateFail("k=%d 越界：min=%.3f max=%.3f（路网 0..%.0f）"
                               % (k, x.min(), x.max(), NET_LEN))
            # ---- 硬门 4：首帧初态 ----
            if k == 0:
                d0 = float(np.max(np.abs(x - hist_x[0])))
                if d0 > 1e-9:
                    raise GateFail("初态不符：max|Δx|=%.3e（判据 1e-9）" % d0)
            log_x[k], log_v[k] = x, v
            hist_x[k], hist_v[k] = x, v

            # ---- 共用件：头车剖面 + 各车加速度 ----
            v[0] = H.head_profile(k * DT, v_eq, v_target, WARM, RAMP)
            new_acc = H.car_accels(k, hist_x, hist_v, hist_a, N, 1, Tp, DT,
                                   False, ws, wv, None, 0.0, 0.0, bmax_arr)
            new_acc = np.minimum(np.maximum(new_acc, -bmax_arr), H.P.a)
            v_new = np.maximum(v + new_acc * DT, 0.0)

            for i in range(N):
                vid = "c%d" % i
                traci.vehicle.setPreviousSpeed(vid, float(v[i]))
                traci.vehicle.setSpeed(vid, float(v_new[i]))
            traci.simulationStep()
            hist_a[k + 1] = new_acc

            # ---- 硬门 5：碰撞与瞬移逐步累积 ----
            coll_total += len(traci.simulation.getCollisions())
            tele_total += traci.simulation.getStartingTeleportNumber()

            # ---- 共用件：统计（用步末回读）----
            xe = np.array([traci.vehicle.getLanePosition("c%d" % i) for i in range(N)])
            ve = np.array([traci.vehicle.getSpeed("c%d" % i) for i in range(N)])
            M.update(k, xe, ve, steps_warm)
            hist_x[k + 1], hist_v[k + 1] = xe, ve

        # ---- 硬门 6：末帧完整 ----
        last_ids = traci.vehicle.getIDList()
        if sorted(last_ids) != expect_ids:
            raise GateFail("末帧 ID 集合不符：%d 辆" % len(last_ids))
        # ---- 硬门 7：接触 ----
        if M.contact_frames > 0:
            raise GateFail("出现几何净距 <=0 的接触：%d 帧" % M.contact_frames)
        if coll_total > 0:
            raise GateFail("出现碰撞：%d 次" % coll_total)
        if tele_total > 0:
            raise GateFail("出现瞬移：%d 次" % tele_total)

        log_x[nsteps], log_v[nsteps] = xe, ve
        return dict(log_x=log_x, log_v=log_v, M=M, nsteps=nsteps,
                    coll_total=coll_total, tele_total=tele_total, v_eq=v_eq,
                    contact_frames=M.contact_frames)
    finally:
        traci.close()


def compare(arm, r, ref):
    n = r["nsteps"]
    shift = X0 - ref["hist_x"][0, 0]
    rx = ref["hist_x"][:n + 1] + shift
    rv = ref["hist_v"][:n + 1]
    ex = np.abs(r["log_x"] - rx)
    ev = np.abs(r["log_v"] - rv)
    per_frame = np.nanmax(ex, axis=1)

    # 逐车判定表
    rows = []
    worst_stat = 0.0
    for i in range(1, N):
        sd = float(r["M"].max_drac[i]); pd = float(ref["max_drac"][i])
        sg = float(r["M"].min_gap[i]); pg = float(ref["min_gap"][i])
        se = bool(r["M"].event[i]); pe = bool(ref["event"][i])
        denom = max(abs(pd), 1e-12)
        rel = abs(sd - pd) / denom
        worst_stat = max(worst_stat, rel)
        rows.append(dict(car=i, sumo_drac=sd, py_drac=pd, rel=rel,
                         sumo_gap=sg, py_gap=pg, gap_diff=sg - pg,
                         sumo_event=se, py_event=pe, match=(se == pe)))
    mismatch = [x for x in rows if not x["match"]]
    gap_worst = max(abs(x["gap_diff"]) for x in rows)
    early = float(np.max(per_frame[:GATES["early_frames"]]))
    k = np.arange(len(per_frame))
    mask = (per_frame > 1e-13) & (k > 500)
    growth = float(np.polyfit(k[mask], np.log(per_frame[mask]), 1)[0]) if mask.sum() > 10 else float("nan")

    return dict(arm=arm, frames=n + 1, cars=N,
                events_sumo_80=int(r["M"].event[20:].sum()),
                events_py_80=int(ref["event"][20:].sum()),
                events_sumo_all=int(r["M"].event[1:].sum()),
                events_py_all=int(ref["event"][1:].sum()),
                peak_sumo=float(np.nanmax(r["M"].max_drac[1:])),
                peak_py=float(np.nanmax(ref["max_drac"][1:])),
                min_gap_sumo=float(np.min(r["M"].min_gap[1:])),
                min_gap_py=float(np.min(ref["min_gap"][1:])),
                worst_peak_rel=worst_stat, worst_gap_abs=gap_worst,
                event_mismatch=len(mismatch), mismatch_rows=mismatch[:10],
                early_window_frames=GATES["early_frames"], early_max_err=early,
                max_err_x=float(np.nanmax(ex)), max_err_v=float(np.nanmax(ev)),
                err_at_k1000=float(per_frame[1000]) if n >= 1000 else None,
                err_at_k3000=float(per_frame[3000]) if n >= 3000 else None,
                err_at_k6000=float(per_frame[6000]) if n >= 6000 else None,
                growth_per_step=growth,
                growth_per_s=growth / DT if np.isfinite(growth) else None,
                doubling_time_s=(np.log(2) / abs(growth) * DT) if np.isfinite(growth) and growth != 0 else None,
                contact_frames=r["contact_frames"], collisions=r["coll_total"],
                teleports=r["tele_total"], per_car=rows)


def gate_check(res):
    fails = []
    if res["event_mismatch"] != 0:
        fails.append("事件集合不一致 %d 辆" % res["event_mismatch"])
    if res["worst_peak_rel"] > GATES["stat_rel"]:
        fails.append("逐车峰值 DRAC 相对差 %.3e > %.0e" % (res["worst_peak_rel"], GATES["stat_rel"]))
    if res["worst_gap_abs"] > GATES["gap_abs"]:
        fails.append("逐车最小净距差 %.3e m > %.0e" % (res["worst_gap_abs"], GATES["gap_abs"]))
    if res["early_max_err"] > GATES["early_abs"]:
        fails.append("前 %d 帧逐帧位置差 %.3e > %.0e"
                     % (res["early_window_frames"], res["early_max_err"], GATES["early_abs"]))
    return fails


def main():
    out = {"config": dict(N=N, hw=HW, Tprime=TP, bmax=BMAX, warm=WARM, ramp=RAMP, obs=OBS,
                          v_target=VTGT, x0=X0, dt=DT, net_len=NET_LEN,
                          kernel="hdm_core_v2.py", gates=GATES)}
    fails = []
    for arm, vt in (("source", VTGT), ("control", None)):
        try:
            r = run_arm(vt)
        except GateFail as e:
            print("GATE_FAIL[%s] %s" % (arm, e), flush=True)
            out[arm] = dict(gate_fail=str(e))
            fails.append("%s: %s" % (arm, e))
            continue
        ref = H.run(N=N, hw=HW, n_a=1, Tprime=TP, seed=0, v_target=vt,
                    warm=WARM, observe=OBS, noise=False, bmax=BMAX, record=True)
        res = compare(arm, r, ref)
        f = gate_check(res)
        res["gate_fails"] = f
        fails.extend("%s: %s" % (arm, x) for x in f)
        out[arm] = res
        print(arm, json.dumps({k: v for k, v in res.items() if k != "per_car"},
                              ensure_ascii=False), flush=True)

    json.dump(out, open("recon_040a_v3.json", "w"), indent=1, ensure_ascii=False)
    if fails:
        print("\n=== GATE FAILURES (%d) ===" % len(fails), flush=True)
        for x in fails:
            print(" -", x, flush=True)
        sys.exit(1)
    print("\n=== ALL GATES PASS ===", flush=True)


if __name__ == "__main__":
    main()