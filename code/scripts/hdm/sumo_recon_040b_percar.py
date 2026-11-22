"""0.4.0b 补证：逐车事件 ID 对比（GPT 指出「总数相同不代表同一批车」）

只跑有源臂 10 种子（对照臂已由 0/80 十组证据覆盖，逐车必全 False）。
每次运行保存 SUMO 侧逐车 event 布尔量、逐车 max_drac、逐车 min_gap（i=20..99 口径），
与 Python 同种子逐车比对；同时保存最后一步回读的有限值/越界检查结果。

判据（GPT 要求补的）：
  · 逐车事件布尔量，两平台每种子必须完全一致（不是总数一致）
  · 逐车峰值 DRAC 相对差 ≤1e-6
  · 逐车最小净距差 ≤1e-6 m
  · 末帧回读有限值 + 越界
  · Python 侧接触也纳入硬门（观测窗 + 预热窗）
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
IDX = slice(20, None)      # 统计口径：车 20..99，共 80 辆


class GateFail(Exception):
    pass


def run_sumo_source(seed):
    v_eq = H.equilibrium_speed(HW)
    bmax_arr = np.full(N, BMAX); Tp = np.full(N, TP)
    rng = np.random.default_rng(seed)
    ws = rng.standard_normal(N); wv = rng.standard_normal(N)

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
        M = H.Metrics(N, v_eq, DT)
        warm_contact = 0; coll = 0; tele = 0
        e = np.exp(-DT / H.P.taur); sq = np.sqrt(2.0 * DT / H.P.taur)
        xe = ve = None

        for k in range(nsteps):
            if sorted(traci.vehicle.getIDList()) != expect:
                raise GateFail("seed%d k=%d ID 集合不符" % (seed, k))
            x = np.empty(N); v = np.empty(N)
            for i in range(N):
                vid = "c%d" % i
                x[i] = traci.vehicle.getLanePosition(vid)
                v[i] = traci.vehicle.getSpeed(vid)
            if not (np.all(np.isfinite(x)) and np.all(np.isfinite(v))):
                raise GateFail("seed%d k=%d 非有限值" % (seed, k))
            if x.min() < 0.0 or x.max() > NET_LEN:
                raise GateFail("seed%d k=%d 越界" % (seed, k))
            hist_x[k], hist_v[k] = x, v
            if k < steps_warm:
                for i in range(1, N):
                    if (x[i-1] - x[i] - H.P.L) <= 0.0:
                        warm_contact += 1
            v[0] = H.head_profile(k * DT, v_eq, VTGT, WARM, RAMP)
            na = H.car_accels(k, hist_x, hist_v, hist_a, N, 1, Tp, DT, True, ws, wv, rng, e, sq, bmax_arr)
            na = np.minimum(np.maximum(na, -bmax_arr), H.P.a)
            vn = np.maximum(v + na * DT, 0.0)
            for i in range(N):
                vid = "c%d" % i
                traci.vehicle.setPreviousSpeed(vid, float(v[i]))
                traci.vehicle.setSpeed(vid, float(vn[i]))
            traci.simulationStep()
            hist_a[k + 1] = na
            coll += len(traci.simulation.getCollisions())
            tele += traci.simulation.getStartingTeleportNumber()
            xe = np.array([traci.vehicle.getLanePosition("c%d" % i) for i in range(N)])
            ve = np.array([traci.vehicle.getSpeed("c%d" % i) for i in range(N)])
            M.update(k, xe, ve, steps_warm)

        # 末帧硬门
        if not (np.all(np.isfinite(xe)) and np.all(np.isfinite(ve))):
            raise GateFail("seed%d 末帧非有限值" % seed)
        if xe.min() < 0.0 or xe.max() > NET_LEN:
            raise GateFail("seed%d 末帧越界 min=%.2f max=%.2f" % (seed, xe.min(), xe.max()))
        if sorted(traci.vehicle.getIDList()) != expect:
            raise GateFail("seed%d 末帧 ID 不全" % seed)
        if M.contact_frames > 0 or warm_contact > 0:
            raise GateFail("seed%d 接触 观测%d 预热%d" % (seed, M.contact_frames, warm_contact))
        if coll or tele:
            raise GateFail("seed%d 碰撞%d 瞬移%d" % (seed, coll, tele))

        return dict(seed=seed,
                    event=[bool(b) for b in M.event[IDX]],
                    max_drac=[float(x) for x in M.max_drac[IDX]],
                    min_gap=[float(x) for x in M.min_gap[IDX]],
                    contact=0, collisions=0, teleports=0)
    finally:
        traci.close()


def run_py_source(seed):
    r = H.run(N=N, hw=HW, n_a=1, Tprime=TP, seed=seed, v_target=VTGT,
              warm=WARM, observe=OBS, noise=True, bmax=BMAX, record=False)
    # Python 侧接触：观测窗
    py_contact_obs = int(r.get("contact_frames", 0))
    return dict(seed=seed,
                event=[bool(b) for b in r["event"][IDX]],
                max_drac=[float(x) for x in r["max_drac"][IDX]],
                min_gap=[float(x) for x in r["min_gap"][IDX]],
                contact_obs=py_contact_obs)


def main():
    seeds = [int(x) for x in sys.argv[1:]] or list(range(10))
    out = {"idx": "20..99", "seeds": seeds, "rows": []}
    fails = []
    for s in seeds:
        su = run_sumo_source(s)
        py = run_py_source(s)
        ev_s = np.array(su["event"]); ev_p = np.array(py["event"])
        id_diff = [int(i) + 20 for i in np.where(ev_s != ev_p)[0]]
        drac_rel = max(abs(a - b) / max(abs(b), 1e-12) for a, b in zip(su["max_drac"], py["max_drac"]))
        gap_abs = max(abs(a - b) for a, b in zip(su["min_gap"], py["min_gap"]))
        row = dict(seed=s, sumo_n=int(ev_s.sum()), py_n=int(ev_p.sum()),
                   event_id_diff=id_diff, drac_rel=drac_rel, gap_abs=gap_abs,
                   py_contact_obs=py["contact_obs"])
        out["rows"].append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        if id_diff:
            fails.append("seed%d 逐车事件不一致，车号 %s" % (s, id_diff[:10]))
        if drac_rel > 1e-6:
            fails.append("seed%d 逐车峰值相对差 %.3e > 1e-6" % (s, drac_rel))
        if gap_abs > 1e-6:
            fails.append("seed%d 逐车净距差 %.3e m > 1e-6" % (s, gap_abs))
        if py["contact_obs"] > 0:
            fails.append("seed%d Python 观测窗接触 %d" % (s, py["contact_obs"]))

    json.dump(out, open("recon_040b_percar.json", "w"), indent=1, ensure_ascii=False)
    if fails:
        print("\n=== GATE FAILURES (%d) ===" % len(fails), flush=True)
        for x in fails: print(" -", x, flush=True)
        sys.exit(1)
    print("\n=== ALL PER-CAR GATES PASS ===", flush=True)


if __name__ == "__main__":
    main()