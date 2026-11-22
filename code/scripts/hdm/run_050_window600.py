"""0.5.0 补证：风险是否被推出窗口（600 s 延长窗）

GPT 要求：A2/A3 末次事件迟至 398.70/398.50 s，末帧无未闭合段不等于 400 s 后没有反弹。
做法：把观测从 360 s 延长到 560 s（总 600 s），重跑 A0/A2/A3 × 10 种子，
看两件事：
  ① 600 s 全窗的事件段数配对差是否仍在（效应没被推出去）
  ② 400–600 s 区间是否有反弹（A2/A3 比 A0 多出事件）

注意：C0 不跑（600 s 会远超 13000 m 路网；本测试纯 Python，无路网限制，但仍不必要）。
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
WARM, RAMP, OBS = 40.0, 6.0, 560.0     # 总 600 s
VTGT = 3.0
X0 = 5000.0
DRAC_TH = 3.4
MERGE_GAP = 0.30
ZONE = list(range(20, 100))
ARMS = {"A0": None, "A2": [20, 30, 40, 50, 60, 70, 80, 90], "A3": list(range(20, 100, 4))}
COMMON = dict(N=N, hw=HW, n_a=1, Tprime=TP, ramp=RAMP, warm=WARM, observe=OBS,
              noise=True, bmax=BMAX, record=True, drac_log=True, x0=X0)


def run_one(args):
    arm, seed, t_deliver = args
    ms = None
    if ARMS[arm]:
        ms = MsgState(receivers=ARMS[arm], t_deliver=t_deliver, factor=0.70, rate=1.0, N=N)
    r = H.run(seed=seed, v_target=VTGT, msg_state=ms, **COMMON)
    return arm, seed, r, ms


def eps(drac, k_from, cars):
    tot = 0; per = {}
    for i in cars:
        runs = count_episodes(drac[k_from:, i], DT, th=DRAC_TH, merge_gap_s=MERGE_GAP)
        per[i] = [(a + k_from, b + k_from) for a, b, _ in runs]
        tot += len(runs)
    return tot, per


def window_count(per, k0, k1):
    return sum(len([1 for (a, b) in per[i] if a >= k0 and a < k1]) for i in per)


def main():
    t0 = time.time()
    k_src = 805
    # t_deliver 与 400 s 版一致（源事件时刻不随观测长度变）
    td = {}
    for seed in range(10):
        r = H.run(seed=seed, v_target=VTGT, **dict(COMMON, observe=60.0))
        hv0 = r["hist_v"][:, 0]
        m = next(m_ for m_ in range(800, hv0.shape[0]) if hv0[m_] < r["v_eq"] - 0.5)
        td[seed] = m * DT + 0.6
    tasks = [(arm, s, td[s]) for arm in ARMS for s in range(10)]
    res = {}
    with ProcessPoolExecutor(max_workers=6) as ex:
        for arm, seed, r, ms in ex.map(run_one, tasks):
            res[(arm, seed)] = r
            print(f"done {arm} seed{seed}", flush=True)

    out = {"config": dict(warm=WARM, obs=OBS, total=WARM + OBS, dt=DT, x0=X0,
                          drac_th=DRAC_TH, merge_gap=MERGE_GAP, arms=ARMS), "seeds": {}}
    for seed in range(10):
        rec = {}
        for arm in ARMS:
            drac = res[(arm, seed)]["drac"]
            tot, per = eps(drac, k_src, ZONE)
            k400 = int(round(400 / DT))
            rec[arm] = dict(total_600=tot,
                            to_400=window_count(per, k_src, k400),
                            after_400=window_count(per, k400, drac.shape[0]),
                            contact=int(res[(arm, seed)].get("contact_frames", 0)))
        out["seeds"][seed] = rec

    base600 = [out["seeds"][s]["A0"]["total_600"] for s in range(10)]
    base400 = [out["seeds"][s]["A0"]["to_400"] for s in range(10)]
    baseaft = [out["seeds"][s]["A0"]["after_400"] for s in range(10)]
    summ = {}
    for arm in ("A2", "A3"):
        v600 = [out["seeds"][s][arm]["total_600"] for s in range(10)]
        v400 = [out["seeds"][s][arm]["to_400"] for s in range(10)]
        vaft = [out["seeds"][s][arm]["after_400"] for s in range(10)]
        d600 = [a - b for a, b in zip(v600, base600)]
        d400 = [a - b for a, b in zip(v400, base400)]
        daft = [a - b for a, b in zip(vaft, baseaft)]
        summ[arm] = dict(
            med_600=float(np.median(v600)), med_A0_600=float(np.median(base600)),
            diff600=float(np.median(d600)), rel600=float(np.median(d600)) / float(np.median(base600)),
            down600=int(sum(1 for d in d600 if d < 0)),
            med_to400=float(np.median(v400)), diff400=float(np.median(d400)),
            rel400=float(np.median(d400)) / float(np.median(base400)),
            down400=int(sum(1 for d in d400 if d < 0)),
            med_after400=float(np.median(vaft)), med_A0_after400=float(np.median(baseaft)),
            diff_after400=float(np.median(daft)))
    out["summary"] = summ
    json.dump(out, open("recon_050_window600.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(summ, ensure_ascii=False, indent=1), flush=True)
    print(f"DONE {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()