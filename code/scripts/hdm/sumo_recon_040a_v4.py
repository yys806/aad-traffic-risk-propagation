"""0.4.0a v4：按 GPT 裁定补三处硬门后重跑

v3 → v4 的差异（全部来自 GPT 对 0.4.0a 的裁定）：
  ① 短窗改为 1201 帧（k=0..1200，覆盖到 60.00 s 整，原 1200 帧只到 59.95 s）
  ② 新增速度硬门：短窗内逐帧速度差 ≤1e-9 m/s（原只报不判）
  ③ 末帧补有限值与边界；预热期也查接触（原 M.update 只在观测期统计）
  ④ 存 npz 供事后复算

其余与 v3 相同：共用 hdm_core_v2 的 head_profile / car_accels / Metrics；
硬门失败即 raise GateFail → 非零退出。
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
GATES = dict(stat_rel=1e-6, gap_abs=1e-6,
             early_frames=1201,        # 含 60.00 s
             early_abs_x=1e-9, early_abs_v=1e-9)


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

        nsteps = int(round((WARM + OBS) / DT))       # 6800
        steps_warm = int(round(WARM / DT))           # 800
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
        warm_contact = 0            # 预热期接触单独计
        coll_total = 0; tele_total = 0

        for k in range(nsteps):
            ids = traci.vehicle.getIDList()
            if sorted(ids) != expect_ids:
                raise GateFail("k=%d ID 集合不符：缺 %s 多 %s" %
                               (k, sorted(set(expect_ids) - set(ids))[:5],
                                sorted(set(ids) - set(expect_ids))[:5]))
            x = np.empty(N); v = np.empty(N)
            for i in range(N):
                vid = "c%d" % i
                pi = traci.vehicle.getLanePosition(vid)
                vi = traci.vehicle.getSpeed(vid)
                if not (np.isfinite(pi) and np.isfinite(vi)):
                    raise GateFail("k=%d 车%d 非有限值 pos=%r v=%r" % (k, i, pi, vi))
                x[i] = pi; v[i] = vi
            if x.min() < 0.0 or x.max() > NET_LEN:
                raise GateFail("k=%d 越界：min=%.3f max=%.3f" % (k, x.min(), x.max()))
            if k == 0:
                d0 = float(np.max(np.abs(x - hist_x[0])))
                if d0 > 1e-9:
                    raise GateFail("初态不符：max|Δx|=%.3e" % d0)
            log_x[k], log_v[k] = x, v
            hist_x[k], hist_v[k] = x, v

            # 预热期接触检查（GPT 要求）
            if k < steps_warm:
                for i in range(1, N):
                    if (x[i - 1] - x[i] - H.P.L) <= 0.0:
                        warm_contact += 1

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

            coll_total += len(traci.simulation.getCollisions())
            tele_total += traci.simulation.getStartingTeleportNumber()

            xe = np.array([traci.vehicle.getLanePosition("c%d" % i) for i in range(N)])
            ve = np.array([traci.vehicle.getSpeed("c%d" % i) for i in range(N)])
            M.update(k, xe, ve, steps_warm)
            hist_x[k + 1], hist_v[k + 1] = xe, ve

        # ---- 末帧：精确 ID + 有限值 + 边界 ----
        last_ids = traci.vehicle.getIDList()
        if sorted(last_ids) != expect_ids:
            raise GateFail("末帧 ID 集合不符：%d 辆" % len(last_ids))
        if not (np.all(np.isfinite(xe)) and np.all(np.isfinite(ve))):
            raise GateFail("末帧出现非有限值")
        if xe.min() < 0.0 or xe.max() > NET_LEN:
            raise GateFail("末帧越界：min=%.3f max=%.3f" % (xe.min(), xe.max()))
        if M.contact_frames > 0 or warm_contact > 0:
            raise GateFail("接触：观测期 %d 帧，预热期 %d 帧"
                           % (M.contact_frames, warm_contact))
        if coll_total > 0:
            raise GateFail("碰撞 %d 次" % coll_total)
        if tele_total > 0:
            raise GateFail("瞬移 %d 次" % tele_total)

        log_x[nsteps], log_v[nsteps] = xe, ve
        return dict(log_x=log_x, log_v=log_v, M=M, nsteps=nsteps,
                    coll_total=coll_total, tele_total=tele_total, v_eq=v_eq,
                    contact_obs=M.contact_frames, contact_warm=warm_contact)
    finally:
        traci.close()


def compare(arm, r, ref):
    n = r["nsteps"]
    shift = X0 - ref["hist_x"][0, 0]
    rx = ref["hist_x"][:n + 1] + shift
    rv = ref["hist_v"][:n + 1]
    ex = np.abs(r["log_x"] - rx); ev = np.abs(r["log_v"] - rv)
    per_frame = np.nanmax(ex, axis=1)
    per_frame_v = np.nanmax(ev, axis=1)

    rows = []; worst_rel = 0.0
    for i in range(1, N):
        sd = float(r["M"].max_drac[i]); pd = float(ref["max_drac"][i])
        sg = float(r["M"].min_gap[i]); pg = float(ref["min_gap"][i])
        rel = abs(sd - pd) / max(abs(pd), 1e-12)
        worst_rel = max(worst_rel, rel)
        rows.append(dict(car=i, sumo_drac=sd, py_drac=pd, rel=rel,
                         sumo_gap=sg, py_gap=pg, gap_diff=sg - pg,
                         sumo_event=bool(r["M"].event[i]),
                         py_event=bool(ref["event"][i]),
                         match=bool(r["M"].event[i]) == bool(ref["event"][i])))
    mismatch = [x for x in rows if not x["match"]]
    gap_worst = max(abs(x["gap_diff"]) for x in rows)
    nf = GATES["early_frames"]
    early_x = float(np.max(per_frame[:nf]))
    early_v = float(np.max(per_frame_v[:nf]))
    kk = np.arange(len(per_frame))
    mask = (per_frame > 1e-13) & (kk > 500)
    growth = float(np.polyfit(kk[mask], np.log(per_frame[mask]), 1)[0]) if mask.sum() > 10 else float("nan")

    return dict(arm=arm, frames=n + 1, cars=N,
                events_sumo_80=int(r["M"].event[20:].sum()),
                events_py_80=int(ref["event"][20:].sum()),
                events_sumo_all=int(r["M"].event[1:].sum()),
                events_py_all=int(ref["event"][1:].sum()),
                peak_sumo=float(np.nanmax(r["M"].max_drac[1:])),
                peak_py=float(np.nanmax(ref["max_drac"][1:])),
                min_gap_sumo=float(np.min(r["M"].min_gap[1:])),
                min_gap_py=float(np.min(ref["min_gap"][1:])),
                worst_peak_rel=worst_rel, worst_gap_abs=gap_worst,
                event_mismatch=len(mismatch), mismatch_rows=mismatch[:10],
                early_frames=nf, early_max_err_x=early_x, early_max_err_v=early_v,
                max_err_x=float(np.nanmax(ex)), max_err_v=float(np.nanmax(ev)),
                err_k3000=float(per_frame[3000]) if n >= 3000 else None,
                err_k6000=float(per_frame[6000]) if n >= 6000 else None,
                growth_per_step=growth,
                doubling_time_s=(np.log(2) / abs(growth) * DT) if np.isfinite(growth) and growth != 0 else None,
                contact_obs=r["contact_obs"], contact_warm=r["contact_warm"],
                collisions=r["coll_total"], teleports=r["tele_total"],
                per_car=rows), rx, rv


def gate_check(res):
    f = []
    if res["event_mismatch"] != 0:
        f.append("事件集合不一致 %d 辆" % res["event_mismatch"])
    if res["worst_peak_rel"] > GATES["stat_rel"]:
        f.append("逐车峰值相对差 %.3e > %.0e" % (res["worst_peak_rel"], GATES["stat_rel"]))
    if res["worst_gap_abs"] > GATES["gap_abs"]:
        f.append("逐车净距差 %.3e m > %.0e" % (res["worst_gap_abs"], GATES["gap_abs"]))
    if res["early_max_err_x"] > GATES["early_abs_x"]:
        f.append("前 %d 帧位置差 %.3e > %.0e" % (res["early_frames"], res["early_max_err_x"], GATES["early_abs_x"]))
    if res["early_max_err_v"] > GATES["early_abs_v"]:
        f.append("前 %d 帧速度差 %.3e > %.0e" % (res["early_frames"], res["early_max_err_v"], GATES["early_abs_v"]))
    return f


def main():
    out = {"config": dict(N=N, hw=HW, Tprime=TP, bmax=BMAX, warm=WARM, ramp=RAMP, obs=OBS,
                          v_target=VTGT, x0=X0, dt=DT, net_len=NET_LEN,
                          kernel="hdm_core_v2.py", gates=GATES)}
    fails = []
    for arm, vt in (("source", VTGT), ("control", None)):
        try:
            r = run_arm(vt)
        except GateFail as e:
            print("GATE_FAIL[%s] %s" % (arm, str(e)[:300]), flush=True)
            out[arm] = dict(gate_fail=str(e)); fails.append("%s: %s" % (arm, str(e)[:300])); continue
        ref = H.run(N=N, hw=HW, n_a=1, Tprime=TP, seed=0, v_target=vt,
                    warm=WARM, observe=OBS, noise=False, bmax=BMAX, record=True)
        res, rx, rv = compare(arm, r, ref)
        f = gate_check(res); res["gate_fails"] = f
        fails.extend("%s: %s" % (arm, x) for x in f)
        out[arm] = res
        np.savez_compressed("recon_040a_v4_%s.npz" % arm, log_x=r["log_x"], log_v=r["log_v"],
                            ref_x=rx, ref_v=rv)
        print(arm, json.dumps({k: v for k, v in res.items() if k != "per_car"}, ensure_ascii=False), flush=True)
    json.dump(out, open("recon_040a_v4.json", "w"), indent=1, ensure_ascii=False)
    if fails:
        print("\n=== GATE FAILURES (%d) ===" % len(fails), flush=True)
        for x in fails: print(" -", x, flush=True)
        sys.exit(1)
    print("\n=== ALL GATES PASS (v4) ===", flush=True)


if __name__ == "__main__":
    main()