"""AAD 0.5.0 主分析：五臂 × 10 种子（纯 Python，400 s）

臂：
  C0 无源无消息（只用于求 T_phys）
  A0 有源无消息（对照）
  A1 消息给 #60
  A2 消息给 #20,30,…,90（8 辆）
  A3 消息给 #20,24,…,96（20 辆）

时间口径（统一写死，避免与 SUMO 差 1 帧）：
  · 步 k 覆盖 [k·dt, (k+1)·dt)，步末状态写入 hist_*[k+1]，时刻 t_{k+1} = (k+1)·dt
  · 所有对外时间戳一律用**步末绝对时间** (k+1)·dt
  · t_src = 头车速度首次低于 v_eq−0.5 的步末时刻
  · t_deliver = t_src + 0.6 s；落到的第一个满足 (k+1)·dt >= t_deliver 的步开始生效
"""
import os, sys, json, time
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
import numpy as np
import hdm_core_v2 as H
from hdm_msg import MsgState, count_episodes
from concurrent.futures import ProcessPoolExecutor

DT = 0.05
N = 100
HW = 45.0
TP = 1.0
BMAX = 9.0
WARM, RAMP, OBS = 40.0, 6.0, 360.0      # 总 400 s
VTGT = 3.0
X0 = 5000.0                              # 与 SUMO 同坐标系
DRAC_TH = 3.4
MERGE_GAP = 0.30
ZONE = list(range(20, 100))              # 目标区 80 辆
TARGET_ACQ = 0.5                          # T_phys 判据阈值 m/s
ACT_DV = 0.5                              # 动作判据速度差
ACT_DUR = 0.2
MIN_LEAD = 2.0
ARMS = {
    "C0": None,
    "A0": None,
    "A1": [60],
    "A2": [20, 30, 40, 50, 60, 70, 80, 90],
    "A3": list(range(20, 100, 4)),
}


def run_one(args):
    arm, seed = args
    v_target = None if arm == "C0" else VTGT
    ms = None
    if ARMS[arm]:
        ms = MsgState(receivers=ARMS[arm], t_deliver=1e9, factor=0.70, rate=1.0, N=N)
    r = H.run(N=N, hw=HW, n_a=1, Tprime=TP, seed=seed, v_target=v_target,
              ramp=RAMP, warm=WARM, observe=OBS, noise=True, bmax=BMAX,
              record=True, drac_log=True, msg_state=ms, x0=X0)
    return arm, seed, r, ms


def episodes_for(drac, t_from_idx, cars, merge_gap=MERGE_GAP):
    """在给定帧区间统计车级超阈事件段数。"""
    total = 0
    per = {}
    for i in cars:
        seg = drac[t_from_idx:, i]
        runs = count_episodes(seg, DT, th=DRAC_TH, merge_gap_s=merge_gap)
        per[int(i)] = [(int(a) + t_from_idx, int(b) + t_from_idx, float(d)) for a, b, d in runs]
        total += len(runs)
    return total, per


def main(out_json="recon_050.json"):
    t0 = time.time()
    steps_warm = int(round(WARM / DT))

    # ===== 第一趟：C0 + A0（A0 用来定 t_src）=====
    res = {}
    tasks1 = [(arm, s) for arm in ("C0", "A0") for s in range(10)]
    with ProcessPoolExecutor(max_workers=6) as ex:
        for arm, seed, r, ms in ex.map(run_one, tasks1):
            res[(arm, seed)] = (r, ms)
            print(f"pass1 {arm} seed{seed} ({len(res)}/{len(tasks1)})", flush=True)

    # ===== 定每种的 t_src / t_deliver =====
    timing = {}
    for seed in range(10):
        hv0 = res[("A0", seed)][0]["hist_v"][:, 0]
        v_eq = res[("A0", seed)][0]["v_eq"]
        t_src = None
        for k in range(steps_warm, hv0.shape[0]):
            if hv0[k] < v_eq - 0.5:
                t_src = (k + 1) * DT
                break
        timing[seed] = dict(t_src=t_src, t_deliver=t_src + 0.6)

    # ===== 第二趟：A1–A3 =====
    def run_msg(args):
        arm, seed = args
        v_target = VTGT
        ms = MsgState(receivers=ARMS[arm], t_deliver=timing[seed]["t_deliver"],
                      factor=0.70, rate=1.0, N=N)
        r = H.run(N=N, hw=HW, n_a=1, Tprime=TP, seed=seed, v_target=v_target,
                  ramp=RAMP, warm=WARM, observe=OBS, noise=True, bmax=BMAX,
                  record=True, drac_log=True, msg_state=ms, x0=X0)
        return arm, seed, r, ms

    tasks2 = [(arm, s) for arm in ("A1", "A2", "A3") for s in range(10)]
    with ProcessPoolExecutor(max_workers=6) as ex:
        for arm, seed, r, ms in ex.map(run_msg, tasks2):
            res[(arm, seed)] = (r, ms)
            print(f"pass2 {arm} seed{seed}", flush=True)

    out = {"config": dict(N=N, hw=HW, Tprime=TP, bmax=BMAX, warm=WARM, ramp=RAMP,
                          obs=OBS, total=WARM + OBS, dt=DT, x0=X0,
                          drac_th=DRAC_TH, merge_gap=MERGE_GAP, zone=ZONE,
                          target_acq=TARGET_ACQ, act_dv=ACT_DV, act_dur=ACT_DUR,
                          min_lead=MIN_LEAD, arms={k: v for k, v in ARMS.items()}),
           "seeds": {}}
    fail = []

    for seed in range(10):
        rC0, _ = res[("C0", seed)]
        rA0, _ = res[("A0", seed)]
        dv = rC0["hist_v"] - rA0["hist_v"]
        Tphys = {}
        for i in range(N):
            idx = np.where(dv[steps_warm:, i] >= TARGET_ACQ)[0]
            Tphys[i] = float((idx[0] + steps_warm + 1) * DT) if len(idx) else None
        t_src = timing[seed]["t_src"]
        t_deliver = timing[seed]["t_deliver"]
        k_src = int(round(t_src / DT)) - 1
        k_20 = int(round(Tphys[20] / DT)) - 1
        rec = dict(t_src=t_src, t_deliver=t_deliver,
                   x_src=float(rA0["hist_x"][k_src, 0]),
                   Tphys_20=Tphys[20], Tphys_60=Tphys[60], Tphys_99=Tphys[99], arms={})

        for arm in ARMS:
            r, ms = res[(arm, seed)]
            drac = r["drac"]
            ep_all, ep_per = episodes_for(drac, k_src, ZONE)
            ep_pre = sum(len([1 for (a, b, d) in ep_per[i] if b < k_20]) for i in ZONE)
            ep_post = sum(len([1 for (a, b, d) in ep_per[i] if a >= k_20]) for i in ZONE)
            veh_hit = int(np.sum(np.asarray(r["event"])[ZONE]))
            peak = float(np.nanmax(np.asarray(r["max_drac"])[ZONE]))
            mgap = float(np.min(np.asarray(r["min_gap"])[ZONE]))
            vv = r["hist_v"][steps_warm:, :]
            delay = float(np.sum((1.0 - vv[:, ZONE] / r["v_eq"]) * DT))
            tail0 = int(round(390 / DT)) - 1
            active_tail = sum(len([1 for (a, b, d) in ep_per[i] if b >= tail0]) for i in ZONE)
            arm_rec = dict(episodes_total=ep_all, episodes_pre=ep_pre, episodes_post=ep_post,
                           episodes_lowhalf=sum(len(ep_per[i]) for i in range(20, 60)),
                           episodes_highhalf=sum(len(ep_per[i]) for i in range(60, 100)),
                           veh_hit=veh_hit, peak=peak, min_gap=mgap, delay=delay,
                           active_tail_segments=active_tail,
                           contact=int(r.get("contact_frames", 0)))
            if ms is not None:
                arm_rec["msg"] = dict(
                    receivers=ARMS[arm],
                    t_action_cap={int(i): (None if np.isnan(ms.t_action[i]) else float(ms.t_action[i]) + DT)
                                  for i in ARMS[arm]},
                    cap_bind_frames={int(i): int(ms.cap_bind_frames[i]) for i in ARMS[arm]},
                    non_receiver_bound=int(sum(ms.cap_bind_frames[i] for i in range(N)
                                               if i not in ARMS[arm])))
                dvv = rA0["hist_v"] - r["hist_v"]
                need = int(round(ACT_DUR / DT))
                act = {}
                for i in ARMS[arm]:
                    col = dvv[:, i]
                    ok = col >= ACT_DV
                    t_act = None
                    for k in range(len(ok) - need):
                        if ok[k:k + need].all():
                            t_act = (k + 1) * DT
                            break
                    act[int(i)] = dict(t_action=t_act,
                                       lead=(Tphys[i] - t_act) if (t_act and Tphys[i]) else None)
                arm_rec["msg"]["action"] = act
                lo = min(ARMS[arm])
                arm_rec["isolation_maxdiff"] = float(
                    np.max(np.abs(r["hist_x"][:, :lo] - rA0["hist_x"][:, :lo]))) if lo > 0 else 0.0
            rec["arms"][arm] = arm_rec
        out["seeds"][seed] = rec

    # ---- 汇总与判据 ----
    summary = {}
    base = [out["seeds"][s]["arms"]["A0"]["episodes_total"] for s in range(10)]
    for arm in ("A1", "A2", "A3"):
        vals = [out["seeds"][s]["arms"][arm]["episodes_total"] for s in range(10)]
        diffs = [v - b for v, b in zip(vals, base)]
        med = float(np.median(diffs))
        rel = med / float(np.median(base)) if np.median(base) else None
        same_dir = int(sum(1 for d in diffs if d < 0)) if med < 0 else int(sum(1 for d in diffs if d > 0))
        summary[arm] = dict(median=float(np.median(vals)), range=[int(min(vals)), int(max(vals))],
                            diffs=[int(d) for d in diffs], diff_median=med,
                            rel_change=rel, same_direction=same_dir)
        if rel is not None and abs(rel) >= 0.05 and same_dir >= 7:
            summary[arm]["quadrant"] = "① 降险信号" if med < 0 else "④ 反升"
        else:
            summary[arm]["quadrant"] = "②③ 实质无差（或仅波幅阻尼）"
    out["summary"] = summary
    out["A0_median"] = float(np.median(base))
    out["A0_range"] = [int(min(base)), int(max(base))]

    # ---- 硬门检查 ----
    for seed in range(10):
        s = out["seeds"][seed]
        for arm in ("A1", "A2", "A3"):
            a = s["arms"][arm]
            if a["msg"]["non_receiver_bound"] != 0:
                fail.append(f"seed{seed} {arm}: 非接收车被限速 {a['msg']['non_receiver_bound']} 次")
            if a.get("isolation_maxdiff", 0.0) > 1e-12:
                fail.append(f"seed{seed} {arm}: 下游隔离区漂移 {a['isolation_maxdiff']:.3e}")
            for i, act in a["msg"]["action"].items():
                if act["t_action"] is None:
                    fail.append(f"seed{seed} {arm} 车{i}: 动作未确认")
                elif act["lead"] is None or act["lead"] < MIN_LEAD:
                    fail.append(f"seed{seed} {arm} 车{i}: 提前量 {act['lead']} < {MIN_LEAD}s")
            if a["contact"]:
                fail.append(f"seed{seed} {arm}: 接触 {a['contact']}")

    out["gates"] = {"fails": fail, "pass": len(fail) == 0}
    json.dump(out, open(out_json, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({"summary": summary, "A0_median": out["A0_median"],
                      "A0_range": out["A0_range"], "gate_pass": len(fail) == 0,
                      "n_fail": len(fail)}, ensure_ascii=False, indent=1), flush=True)
    if fail:
        print("FAILS:", fail[:10], flush=True)
        sys.exit(1)
    print(f"ALL GATES PASS ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()