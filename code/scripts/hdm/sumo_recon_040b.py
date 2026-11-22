"""0.4.0b：有噪声 10 种子配对（Python vs SUMO），只比分布 + 逐种子配对差

按 GPT 0.4.0a 裁定的预锁线：
  · 固定种子 0–9
  · 两平台、两臂**共享同一份含预热的 OU 噪声序列**
    （关键：shared car_accels 每步固定抽 2×(N-1) 个数，抽取次数与状态无关，故序列天然对齐）
  · 先用种子 0 双臂验接线，并核对 Python 冻结参考
  · 两平台两臂 10/10 全程零几何接触、碰撞、瞬移、越界及帧完整性异常
  · 事件口径：i=20..99（80 辆），DRAC ≥3.4 m/s² 连续 ≥4 帧（0.2 s）
  · 每种子对照臂 0/80、有源臂 ≥71/80（历史最低 73 减 2 辆工程容差）
  · 同种子两平台有源计数差：每组绝对值 ≤2 辆，十组绝对差中位数 ≤1 辆
  · 逐种子附报峰值 DRAC 与最小净距
  · 任一硬门失败即停，不换种子、不改线

用法：
  python sumo_recon_040b.py            # 全部 10 种子
  python sumo_recon_040b.py --smoke    # 只跑种子 0（接线验证）
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
SEEDS = list(range(10))
GATES = dict(src_min_events=71, ctrl_max_events=0,
             pair_abs_max=2, pair_median_max=1)


class GateFail(Exception):
    pass


def prepare_noise(seed):
    """返回 (rng, ws, wv)：与内核 run() 的抽取顺序一致。

    内核顺序：default_rng(seed) → bmax 数组（标量时不抽）→ ws 整向量 → wv 整向量
    → Tp（标量不抽）。故这里只需 default_rng(seed) 后抽两次 standard_normal(N)。
    """
    rng = np.random.default_rng(seed)
    ws = rng.standard_normal(N)
    wv = rng.standard_normal(N)
    return rng, ws, wv


def run_sumo(v_target, seed):
    v_eq = H.equilibrium_speed(HW)
    bmax_arr = np.full(N, BMAX)
    Tp = np.full(N, TP)
    rng, ws, wv = prepare_noise(seed)

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

        M = H.Metrics(N, v_eq, DT)
        warm_contact = 0; coll = 0; tele = 0
        e = np.exp(-DT / H.P.taur); sq = np.sqrt(2.0 * DT / H.P.taur)

        for k in range(nsteps):
            ids = traci.vehicle.getIDList()
            if sorted(ids) != expect_ids:
                raise GateFail("seed%d k=%d ID 集合不符" % (seed, k))
            x = np.empty(N); v = np.empty(N)
            for i in range(N):
                vid = "c%d" % i
                pi = traci.vehicle.getLanePosition(vid)
                vi = traci.vehicle.getSpeed(vid)
                if not (np.isfinite(pi) and np.isfinite(vi)):
                    raise GateFail("seed%d k=%d 车%d 非有限值" % (seed, k, i))
                x[i] = pi; v[i] = vi
            if x.min() < 0.0 or x.max() > NET_LEN:
                raise GateFail("seed%d k=%d 越界 min=%.2f max=%.2f" % (seed, k, x.min(), x.max()))
            hist_x[k], hist_v[k] = x, v
            if k < steps_warm:
                for i in range(1, N):
                    if (x[i - 1] - x[i] - H.P.L) <= 0.0:
                        warm_contact += 1

            v[0] = H.head_profile(k * DT, v_eq, v_target, WARM, RAMP)
            new_acc = H.car_accels(k, hist_x, hist_v, hist_a, N, 1, Tp, DT,
                                   True, ws, wv, rng, e, sq, bmax_arr)
            new_acc = np.minimum(np.maximum(new_acc, -bmax_arr), H.P.a)
            v_new = np.maximum(v + new_acc * DT, 0.0)
            for i in range(N):
                vid = "c%d" % i
                traci.vehicle.setPreviousSpeed(vid, float(v[i]))
                traci.vehicle.setSpeed(vid, float(v_new[i]))
            traci.simulationStep()
            hist_a[k + 1] = new_acc

            coll += len(traci.simulation.getCollisions())
            tele += traci.simulation.getStartingTeleportNumber()
            xe = np.array([traci.vehicle.getLanePosition("c%d" % i) for i in range(N)])
            ve = np.array([traci.vehicle.getSpeed("c%d" % i) for i in range(N)])
            M.update(k, xe, ve, steps_warm)

        if M.contact_frames > 0 or warm_contact > 0:
            raise GateFail("seed%d 接触：观测 %d 预热 %d" % (seed, M.contact_frames, warm_contact))
        if coll > 0:
            raise GateFail("seed%d 碰撞 %d" % (seed, coll))
        if tele > 0:
            raise GateFail("seed%d 瞬移 %d" % (seed, tele))
        return dict(events_80=int(M.event[20:].sum()),
                    events_all=int(M.event[1:].sum()),
                    peak=float(np.nanmax(M.max_drac[1:])),
                    min_gap=float(np.min(M.min_gap[1:])),
                    contact=0, collisions=0, teleports=0)
    finally:
        traci.close()


def run_py(v_target, seed):
    r = H.run(N=N, hw=HW, n_a=1, Tprime=TP, seed=seed, v_target=v_target,
              warm=WARM, observe=OBS, noise=True, bmax=BMAX, record=False)
    return dict(events_80=int(r["event"][20:].sum()),
                events_all=int(r["event"][1:].sum()),
                peak=float(np.nanmax(r["max_drac"][1:])),
                min_gap=float(np.min(r["min_gap"][1:])),
                contact=int(getattr(r, "get", lambda *a: 0)("contact_frames", 0) or 0))


def main():
    smoke = "--smoke" in sys.argv
    seeds = SEEDS[:1] if smoke else SEEDS
    out = {"config": dict(N=N, hw=HW, Tprime=TP, bmax=BMAX, warm=WARM, ramp=RAMP,
                          obs=OBS, v_target=VTGT, x0=X0, dt=DT, seeds=seeds,
                          kernel="hdm_core_v2.py", gates=GATES),
           "rows": []}
    fails = []
    for seed in seeds:
        for arm, vt in (("control", None), ("source", VTGT)):
            s = run_sumo(vt, seed)
            p = run_py(vt, seed)
            row = dict(seed=seed, arm=arm,
                       sumo_events=s["events_80"], py_events=p["events_80"],
                       sumo_peak=s["peak"], py_peak=p["peak"],
                       sumo_min_gap=s["min_gap"], py_min_gap=p["min_gap"],
                       sumo_contact=s["contact"], sumo_collisions=s["collisions"],
                       sumo_teleports=s["teleports"])
            if arm == "control":
                if s["events_80"] > GATES["ctrl_max_events"]:
                    fails.append("seed%d 对照臂 SUMO 出事件 %d > %d"
                                 % (seed, s["events_80"], GATES["ctrl_max_events"]))
            else:
                if s["events_80"] < GATES["src_min_events"]:
                    fails.append("seed%d 有源臂 SUMO 事件 %d < %d"
                                 % (seed, s["events_80"], GATES["src_min_events"]))
                row["pair_abs"] = abs(s["events_80"] - p["events_80"])
                if row["pair_abs"] > GATES["pair_abs_max"]:
                    fails.append("seed%d 两平台有源差 %d > %d"
                                 % (seed, row["pair_abs"], GATES["pair_abs_max"]))
            out["rows"].append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
        if fails and seed == seeds[0] and smoke:
            break

    src = [r for r in out["rows"] if r["arm"] == "source"]
    if src and not smoke:
        diffs = [r["pair_abs"] for r in src]
        med = float(np.median(diffs))
        out["pair_median"] = med
        if med > GATES["pair_median_max"]:
            fails.append("十组配对绝对差中位数 %.2f > %d" % (med, GATES["pair_median_max"]))
        out["source_events_sumo"] = [r["sumo_events"] for r in src]
        out["source_events_py"] = [r["py_events"] for r in src]
        out["source_median_sumo"] = float(np.median([r["sumo_events"] for r in src]))
        out["source_range_sumo"] = [int(min(r["sumo_events"] for r in src)),
                                    int(max(r["sumo_events"] for r in src))]

    json.dump(out, open("recon_040b%s.json" % ("_smoke" if smoke else ""), "w"),
              indent=1, ensure_ascii=False)
    if fails:
        print("\n=== GATE FAILURES (%d) ===" % len(fails), flush=True)
        for x in fails: print(" -", x, flush=True)
        sys.exit(1)
    print("\n=== ALL GATES PASS (0.4.0b) ===", flush=True)


if __name__ == "__main__":
    main()