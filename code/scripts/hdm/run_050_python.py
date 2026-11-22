"""AAD 0.5.0 主分析：五臂 × 10 种子（纯 Python，400 s）

按 GPT v3 终审四项修正：
  ① run_msg 提到模块级（原为 main 内嵌，ProcessPool 无法序列化，实测崩溃）
  ② 时间戳统一为「索引即时间」：hist_*/drac 的第 m 帧 = 时刻 m·dt（原多算 +1 帧）
  ③ 跨分界段按起点归属，保证 前段 + 后段 = 全窗
  ④ 延误从 t_src 起算（原从预热边界起算）

时钟表（写死）：
  · 步 k 在 [k·dt,(k+1)·dt) 内推进；hist_*[k+1] 与 drac[k+1] 存步末状态
  · 第 m 帧时刻 t_m = m·dt
  · t_src = 第一个 hv[m,0] < v_eq-0.5 的 m，记 t_src = m·dt
"""
import os, sys, json, time
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
import numpy as np
import hdm_core_v2 as H
from hdm_msg import MsgState, Message, count_episodes
from concurrent.futures import ProcessPoolExecutor

DT = 0.05
N = 100
HW = 45.0
TP = 1.0
BMAX = 9.0
WARM, RAMP = 40.0, 6.0
OBS = float(os.environ.get("AAD050_OBS", "360.0"))   # 延长窗用 AAD050_OBS=560
VTGT = 3.0
X0 = 5000.0
MAXSPEED = 50.0   # vType 锁定的 maxSpeed，用于速度上界硬门
NET_LEN = 13000.0  # hdm_recon_long 路网长度；C0 不进 SUMO 故不受此限
DRAC_TH = 3.4
MERGE_GAP = 0.30
ZONE = list(range(20, 100))
TARGET_ACQ = 0.5
ACT_DV = 0.5
ACT_DUR = 0.2
MIN_LEAD = 2.0
FIRSTWAVE_S = 30.0
ARMS = {
    "C0": None,
    "A0": None,
    "A1": [60],
    "A2": [20, 30, 40, 50, 60, 70, 80, 90],
    "A3": list(range(20, 100, 4)),
    # 晚到对照（GPT+Gemini 一致认为这是分离「信息提前量」与「减速动作本身」的关键臂）：
    # 接收车与响应规则与 A2/A3 完全相同，唯一差别是消息在物理波到达该组第一辆车时才送达。
    "A2L": [20, 30, 40, 50, 60, 70, 80, 90],
    "A3L": list(range(20, 100, 4)),
}
MSG_ARMS = ("A1", "A2", "A3", "A2L", "A3L")
LATE_ARMS = ("A2L", "A3L")
COMMON = dict(N=N, hw=HW, n_a=1, Tprime=TP, ramp=RAMP, warm=WARM, observe=OBS,
              noise=True, bmax=BMAX, record=True, drac_log=True, x0=X0)


def run_msg(args):
    """模块级函数，可被 ProcessPoolExecutor 序列化。"""
    arm, seed, t_deliver, t_src, x_src, v_src = args
    msg = Message(event_id=seed, t_src=t_src, x_src=x_src, v_src=v_src,
                  receivers=ARMS[arm], t_deliver=t_deliver, factor=0.70, rate=1.0)
    ms = MsgState(receivers=ARMS[arm], t_deliver=t_deliver, factor=0.70, rate=1.0,
                  N=N, message=msg)
    r = H.run(seed=seed, v_target=VTGT, msg_state=ms, **COMMON)
    return arm, seed, r, ms


def run_base(args):
    arm, seed = args
    r = H.run(seed=seed, v_target=(None if arm == "C0" else VTGT), **COMMON)
    return arm, seed, r, None


def episodes_for(drac, k_from, cars, merge_gap=MERGE_GAP):
    total = 0
    per = {}
    for i in cars:
        seg = drac[k_from:, i]
        runs = count_episodes(seg, DT, th=DRAC_TH, merge_gap_s=merge_gap)
        per[int(i)] = [(int(a) + k_from, int(b) + k_from, float(d)) for a, b, d in runs]
        total += len(runs)
    return total, per


def tphys_from(dv, thr, steps_warm):
    out = {}
    for i in range(N):
        idx = np.where(dv[steps_warm:, i] >= thr)[0]
        out[i] = float((idx[0] + steps_warm) * DT) if len(idx) else None
    return out


def main(out_json=None):
    out_json = out_json or os.environ.get("AAD050_OUT", "recon_050.json")
    t0 = time.time()
    steps_warm = int(round(WARM / DT))

    res = {}
    tasks1 = [(arm, s) for arm in ("C0", "A0") for s in range(10)]
    with ProcessPoolExecutor(max_workers=6) as ex:
        for arm, seed, r, ms in ex.map(run_base, tasks1):
            res[(arm, seed)] = (r, ms)
            print(f"pass1 {arm} seed{seed}", flush=True)

    timing = {}
    for seed in range(10):
        rA0 = res[("A0", seed)][0]
        hv0 = rA0["hist_v"][:, 0]
        v_eq = rA0["v_eq"]
        m_src = None
        for m in range(steps_warm, hv0.shape[0]):
            if hv0[m] < v_eq - 0.5:
                m_src = m
                break
        t_src = m_src * DT
        timing[seed] = dict(t_src=t_src, t_deliver=t_src + 0.6,
                            x_src=float(rA0["hist_x"][m_src, 0]),
                            v_src=float(rA0["hist_v"][m_src, 0]),
                            m_src=m_src, k_eff=int(np.ceil((t_src + 0.6) / DT)))

    # 晚到时刻：该组接收车中**最早**被波触及的那辆的 T_phys + 0.6 s（最宽松的晚到条件）
    tasks2 = []
    for s in range(10):
        for arm in MSG_ARMS:
            td = timing[s]["t_deliver"]
            if arm in LATE_ARMS:
                rA0s = res[("A0", s)][0]
                rC0s = res[("C0", s)][0]
                dv_s = rC0s["hist_v"] - rA0s["hist_v"]
                tps = tphys_from(dv_s, TARGET_ACQ, steps_warm)
                arr = [tps[i] for i in ARMS[arm] if tps[i] is not None]
                timing[s][f"tphys_min_{arm}"] = min(arr) if arr else np.nan
                td = (min(arr) if arr else td) + 0.6
            tasks2.append((arm, s, td, timing[s]["t_src"],
                           timing[s]["x_src"], timing[s]["v_src"]))
    with ProcessPoolExecutor(max_workers=6) as ex:
        for arm, seed, r, ms in ex.map(run_msg, tasks2):
            res[(arm, seed)] = (r, ms)
            print(f"pass2 {arm} seed{seed}", flush=True)

    out = {"config": dict(N=N, hw=HW, Tprime=TP, bmax=BMAX, warm=WARM, ramp=RAMP,
                          obs=OBS, total=WARM + OBS, dt=DT, x0=X0, drac_th=DRAC_TH,
                          merge_gap=MERGE_GAP, zone=[ZONE[0], ZONE[-1]], target_acq=TARGET_ACQ,
                          act_dv=ACT_DV, act_dur=ACT_DUR, min_lead=MIN_LEAD,
                          firstwave_s=FIRSTWAVE_S, arms={k: v for k, v in ARMS.items()}),
           "seeds": {}}
    fail = []

    for seed in range(10):
        rC0, _ = res[("C0", seed)]
        rA0, _ = res[("A0", seed)]
        dv = rC0["hist_v"] - rA0["hist_v"]
        Tp5 = tphys_from(dv, TARGET_ACQ, steps_warm)
        Tp1 = tphys_from(dv, 0.1, steps_warm)
        tm = timing[seed]
        t_src = tm["t_src"]; k_src = tm["m_src"]
        k_20 = int(round(Tp5[20] / DT)) if Tp5[20] else None
        rec = dict(t_src=t_src, t_deliver=tm["t_deliver"], x_src=tm["x_src"], v_src=tm["v_src"],
                   Tphys_20=Tp5[20], Tphys_60=Tp5[60], Tphys_99=Tp5[99],
                   Tphys_20_sens01=Tp1[20], arms={})

        for arm in ARMS:
            r, ms = res[(arm, seed)]
            drac = r["drac"]
            ep_all, ep_per = episodes_for(drac, k_src, ZONE)
            if k_20 is not None:
                ep_pre = sum(len([1 for (a, b, d) in ep_per[i] if a < k_20]) for i in ZONE)
                ep_post = ep_all - ep_pre
            else:
                ep_pre, ep_post = ep_all, 0
            veh_hit = int(np.sum(np.asarray(r["event"])[ZONE]))
            peak = float(np.nanmax(np.asarray(r["max_drac"])[ZONE]))
            mgap = float(np.min(np.asarray(r["min_gap"])[ZONE]))
            vv = r["hist_v"][k_src:, :]
            delay = float(np.sum((1.0 - vv[:, ZONE] / r["v_eq"]) * DT))
            tail0 = int(round(390 / DT))
            active_tail = sum(len([1 for (a, b, d) in ep_per[i] if b >= tail0]) for i in ZONE)
            open_tail = sum(len([1 for (a, b, d) in ep_per[i] if b >= len(drac) - 2]) for i in ZONE)
            fw = 0
            for i in ZONE:
                if Tp5[i] is None:
                    continue
                a0 = int(round(Tp5[i] / DT)); a1 = int(round((Tp5[i] + FIRSTWAVE_S) / DT))
                fw += len([1 for (a, b, d) in ep_per[i] if a0 <= a <= a1])
            vs = float(np.sum(drac[k_src:, ZONE] >= DRAC_TH) * DT)
            # 拥堵暴露（v<10 m/s 的车·秒）与暴露归一率 —— 排除「入队晚」混杂
            jam_exp = float(np.sum(vv[:, ZONE] < 10.0) * DT)
            rate_per_100 = (100.0 * ep_all / jam_exp) if jam_exp > 0 else None
            # 各臂自身的拥堵起始时刻（用于首波锚定，避免用 A0 的 T_phys 误伤）
            tcong = {}
            for i in ZONE:
                idx = np.where(r["hist_v"][k_src:, i] < 10.0)[0]
                tcong[i] = float((idx[0] + k_src) * DT) if len(idx) else None
            fw_self = 0
            for i in ZONE:
                if tcong[i] is None:
                    continue
                a0 = int(round((tcong[i] - 10.0) / DT)); a1 = int(round((tcong[i] + FIRSTWAVE_S) / DT))
                fw_self += len([1 for (a, b, d) in ep_per[i] if a0 <= a <= a1])
            # 接收车 vs 非接收车拆分（判断效应是否传播给未收消息的车）
            # A0 也按 A2/A3 的接收名单分区，才能同口径对比
            recv_set = set(ARMS[arm]) if ms is not None else set()
            ref_set = set(ARMS["A3"]) if arm != "A3" else set(ARMS["A2"])
            def _rate(cars):
                ev = sum(len(ep_per[i]) for i in cars)
                jx = float(np.sum(vv[:, cars] < 10.0) * DT) if cars else 0.0
                return dict(events=ev, jam=jx,
                            rate=(100.0 * ev / jx) if jx > 0 else None)
            split = dict(all=_rate(ZONE))
            if recv_set:
                split["recv"] = _rate([i for i in ZONE if i in recv_set])
                split["nonrecv"] = _rate([i for i in ZONE if i not in recv_set])
            else:
                # A0：按 A3 与 A2 的接收名单各拆一次，供对照
                split["recv_A3"] = _rate([i for i in ZONE if i in set(ARMS["A3"])])
                split["nonrecv_A3"] = _rate([i for i in ZONE if i not in set(ARMS["A3"])])
                split["recv_A2"] = _rate([i for i in ZONE if i in set(ARMS["A2"])])
                split["nonrecv_A2"] = _rate([i for i in ZONE if i not in set(ARMS["A2"])])
            last_ev = max([b for i in ZONE for (a, b, d) in ep_per[i]], default=-1)
            arm_rec = dict(safety=r.get("safety"), episodes_total=ep_all,
                           episodes_pre=ep_pre, episodes_post=ep_post,
                           jam_exposure_car_sec=jam_exp, episodes_per_100_car_sec=rate_per_100,
                           first_wave_self_anchored=fw_self,
                           last_event_time=(last_ev * DT if last_ev >= 0 else None),
                           split=split,
                           pre_plus_post_eq_total=bool(ep_pre + ep_post == ep_all),
                           episodes_lowhalf=sum(len(ep_per[i]) for i in range(20, 60)),
                           episodes_highhalf=sum(len(ep_per[i]) for i in range(60, 100)),
                           veh_hit=veh_hit, peak=peak, min_gap=mgap, delay=delay,
                           drac_car_seconds=vs, first_wave_events=fw,
                           active_tail_segments=active_tail, open_tail_segments=open_tail,
                           contact=int(r.get("contact_frames", 0)))
            if ms is not None:
                arm_rec["msg"] = dict(
                    receivers=ARMS[arm], t_deliver=float(ms.t_deliver),
                    t_action_cap={int(i): (None if np.isnan(ms.t_action[i]) else float(ms.t_action[i]))
                                  for i in ARMS[arm]},
                    cap_bind_frames={int(i): int(ms.cap_bind_frames[i]) for i in ARMS[arm]},
                    non_receiver_bound=int(sum(ms.cap_bind_frames[i] for i in range(N)
                                               if i not in ARMS[arm])))
                dvv = rA0["hist_v"] - r["hist_v"]
                need = int(round(ACT_DUR / DT))
                act = {}
                for i in ARMS[arm]:
                    ok = dvv[:, i] >= ACT_DV
                    t_act = None
                    for k in range(len(ok) - need):
                        if ok[k:k + need].all():
                            t_act = k * DT
                            break
                    act[int(i)] = dict(t_action=t_act,
                                       lead=(Tp5[i] - t_act) if (t_act is not None and Tp5[i]) else None)
                arm_rec["msg"]["action"] = act
                lo = min(ARMS[arm])
                if lo > 0:
                    arm_rec["isolation_maxdiff"] = float(
                        np.max(np.abs(r["hist_x"][:, :lo] - rA0["hist_x"][:, :lo])))
                    arm_rec["isolation_maxdiff_v"] = float(
                        np.max(np.abs(r["hist_v"][:, :lo] - rA0["hist_v"][:, :lo])))
                    arm_rec["isolation_maxdiff_a"] = float(
                        np.max(np.abs(r["hist_a"][:, :lo] - rA0["hist_a"][:, :lo])))
                else:
                    arm_rec["isolation_maxdiff"] = 0.0
                    arm_rec["isolation_maxdiff_v"] = 0.0
                    arm_rec["isolation_maxdiff_a"] = 0.0
                # 五环溯源（第 5 环用轨迹差分动作时刻，不用内核自报）
                tr = ms.trace()
                tr["ring5_action"] = {int(i): v["t_action"]
                                      for i, v in arm_rec["msg"]["action"].items()}
                tr["ring5_definition"] = "Δv>=0.5 m/s 持续>=0.2 s 且相对 C0-A0 差分（预锁）"
                arm_rec["trace"] = tr
            rec["arms"][arm] = arm_rec
        out["seeds"][seed] = rec
        try:                      # 增量落盘：任何后段异常都不会丢已完成的结果
            json.dump(out, open(out_json + ".partial", "w"), indent=1, ensure_ascii=False)
        except Exception:
            pass

    base = [out["seeds"][s]["arms"]["A0"]["episodes_total"] for s in range(10)]
    base_peak = [out["seeds"][s]["arms"]["A0"]["peak"] for s in range(10)]
    ssum = {}
    for arm in MSG_ARMS:
        vals = [out["seeds"][s]["arms"][arm]["episodes_total"] for s in range(10)]
        pks = [out["seeds"][s]["arms"][arm]["peak"] for s in range(10)]
        diffs = [v - b for v, b in zip(vals, base)]
        med = float(np.median(diffs))
        rel = med / float(np.median(base)) if np.median(base) else 0.0
        down = int(sum(1 for d in diffs if d < 0)); up = int(sum(1 for d in diffs if d > 0))
        pdiff = [a - b for a, b in zip(pks, base_peak)]
        pmed = float(np.median(pdiff)); prel = pmed / float(np.median(base_peak))
        pdown = int(sum(1 for d in pdiff if d < 0)); pup = int(sum(1 for d in pdiff if d > 0))
        q = "③ 实质无差"
        if abs(rel) >= 0.05 and ((med < 0 and down >= 7) or (med > 0 and up >= 7)):
            q = "① 降险信号" if med < 0 else "④ 反升"
        elif abs(prel) >= 0.05 and ((pmed < 0 and pdown >= 7) or (pmed > 0 and pup >= 7)):
            q = "② 波幅阻尼（事件段数无差）"
        rates = [(out["seeds"][s]["arms"][arm]["episodes_per_100_car_sec"] or 0.0) for s in range(10)]
        rates0 = [(out["seeds"][s]["arms"]["A0"]["episodes_per_100_car_sec"] or 0.0) for s in range(10)]
        rdiff = [a - b for a, b in zip(rates, rates0)]
        rrel = float(np.median(rdiff)) / float(np.median(rates0)) if np.median(rates0) else 0.0
        rdow = int(sum(1 for d in rdiff if d < 0))
        delays = [out["seeds"][s]["arms"][arm]["delay"] for s in range(10)]
        delays0 = [out["seeds"][s]["arms"]["A0"]["delay"] for s in range(10)]
        ddiff = [a - b for a, b in zip(delays, delays0)]
        ssum[arm] = dict(median=float(np.median(vals)), range=[int(min(vals)), int(max(vals))],
                         diffs=[int(d) for d in diffs], diff_median=med, rel=rel,
                         seeds_down=down, seeds_up=up,
                         peak_median=float(np.median(pks)), peak_rel=prel, quadrant=q,
                         rate_median=float(np.median(rates)), rate_rel=rrel, rate_seeds_down=rdow,
                         delay_median=float(np.median(delays)), delay_diff_median=float(np.median(ddiff)))
    out["summary"] = ssum
    out["A0"] = dict(median=float(np.median(base)), range=[int(min(base)), int(max(base))],
                     peak_median=float(np.median(base_peak)))

    for seed in range(10):
        s = out["seeds"][seed]
        # 硬门 7：五臂全程安全（含 C0/A0、含预热期、含非有限值与越界）
        for arm in ARMS:
            sf = s["arms"][arm].get("safety") or {}
            if sf.get("contact_warm", 0) != 0:
                fail.append(f"seed{seed} {arm}: 预热期接触 {sf['contact_warm']}")
            if sf.get("contact_obs", 0) != 0:
                fail.append(f"seed{seed} {arm}: 观测期接触 {sf['contact_obs']}")
            if sf.get("nonfinite", 0) != 0:
                fail.append(f"seed{seed} {arm}: 非有限值 {sf['nonfinite']}")
            if sf.get("min_speed", 0) < -1e-9:
                fail.append(f"seed{seed} {arm}: 负速度 {sf.get('min_speed')}")
            if sf.get("max_speed", 0) > MAXSPEED + 1e-6:
                fail.append(f"seed{seed} {arm}: 速度超上限 {sf.get('max_speed')}")
            if arm != "C0" and sf.get("max_abs_x", 0) > NET_LEN:
                fail.append(f"seed{seed} {arm}: 超出路网 {sf.get('max_abs_x'):.1f} > {NET_LEN}")
            if sf.get("oob", 0) != 0:
                fail.append(f"seed{seed} {arm}: 越界帧 {sf.get('oob')} min_x={sf.get('min_x')} max|x|={sf.get('max_abs_x')}")
            if sf.get("teleport", 0) != 0:
                fail.append(f"seed{seed} {arm}: 瞬移帧 {sf.get('teleport')}")
            if s["arms"][arm]["open_tail_segments"] > 0:
                fail.append(f"seed{seed} {arm}: 末帧未闭合段 {s['arms'][arm]['open_tail_segments']}")
        for arm in MSG_ARMS:
            a = s["arms"][arm]
            late = arm in LATE_ARMS
            if not a["pre_plus_post_eq_total"]:
                fail.append(f"seed{seed} {arm}: 前段+后段 != 全窗")
            if a["msg"]["non_receiver_bound"] != 0:
                fail.append(f"seed{seed} {arm}: 非接收车被限速 {a['msg']['non_receiver_bound']}")
            for key in ("isolation_maxdiff", "isolation_maxdiff_v", "isolation_maxdiff_a"):
                if a.get(key, 0.0) > 1e-12:
                    fail.append(f"seed{seed} {arm}: 隔离区{key} 漂移 {a[key]:.3e}")
            # 硬门 1：五环溯源逐车闭合
            tr = a.get("trace") or {}
            pl = tr.get("ring2_payload") or {}
            if not all(np.isfinite(pl.get(k, float("nan"))) for k in ("t_src", "x_src", "v_src")):
                fail.append(f"seed{seed} {arm}: 载荷字段缺失 {pl}")
            for i in ARMS[arm]:
                d3 = (tr.get("ring3_delivered") or {}).get(i)
                d4 = (tr.get("ring4_cap_bind") or {}).get(i, 0)
                d5 = (tr.get("ring5_action") or {}).get(i)
                if d3 is None:
                    fail.append(f"seed{seed} {arm} 车{i}: 未记录送达时刻")
                if d4 <= 0 and not late:
                    fail.append(f"seed{seed} {arm} 车{i}: 控速从未介入")
                if d5 is None and not late:
                    fail.append(f"seed{seed} {arm} 车{i}: 动作未确认")
                if not (tr.get("applicable") or {}).get(i, False):
                    fail.append(f"seed{seed} {arm} 车{i}: 载荷适用性判定为否")
            if not late:
                for i, act in a["msg"]["action"].items():
                    if act["t_action"] is None:
                        fail.append(f"seed{seed} {arm} 车{i}: 动作未确认（差分判据）")
                    elif act["lead"] is None or act["lead"] < MIN_LEAD:
                        fail.append(f"seed{seed} {arm} 车{i}: 提前量 {act['lead']}")

    # 早报 vs 晚报：同接收车、同规则，唯一差别是送达时刻
    pairs = {}
    for early, late in (("A2", "A2L"), ("A3", "A3L")):
        e = [out["seeds"][s]["arms"][early]["episodes_total"] for s in range(10)]
        l = [out["seeds"][s]["arms"][late]["episodes_total"] for s in range(10)]
        b = [out["seeds"][s]["arms"]["A0"]["episodes_total"] for s in range(10)]
        de = [x - y for x, y in zip(e, b)]
        dl = [x - y for x, y in zip(l, b)]
        d = [x - y for x, y in zip(e, l)]          # 早 − 晚（负 = 早报更好）
        pairs[f"{early}_vs_{late}"] = dict(
            early_median=float(np.median(e)), late_median=float(np.median(l)),
            A0_median=float(np.median(b)),
            early_rel=float(np.median(de)) / float(np.median(b)),
            late_rel=float(np.median(dl)) / float(np.median(b)),
            early_minus_late_median=float(np.median(d)),
            early_minus_late_diffs=[int(x) for x in d],
            early_better_seeds=int(sum(1 for x in d if x < 0)),
            late_better_seeds=int(sum(1 for x in d if x > 0)),
            tie_seeds=int(sum(1 for x in d if x == 0)),
            late_deliver=[out["seeds"][s]["arms"][late]["msg"]["t_deliver"] for s in range(10)],
            early_deliver=[out["seeds"][s]["arms"][early]["msg"]["t_deliver"] for s in range(10)])
    out["early_vs_late"] = pairs

    out["gates"] = dict(fails=fail, ok=(len(fail) == 0))
    json.dump(out, open(out_json, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({"summary": ssum, "early_vs_late": pairs, "A0": out["A0"],
                      "gate_pass": len(fail) == 0, "n_fail": len(fail)},
                     ensure_ascii=False, indent=1), flush=True)
    if fail:
        print("FAILS:", fail[:12], flush=True)
        sys.exit(1)
    print(f"ALL GATES PASS ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()