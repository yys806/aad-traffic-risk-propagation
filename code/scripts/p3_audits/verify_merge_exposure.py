"""核验 P3 合流试的暴露：逐事件定位、逐车连续性、是否落在目标区。

阶段：P3 ｜ 数据：code/outputs/analysis/P3_merge_merge/arms.npz
脚本：code/scripts/p3_audits/verify_merge_exposure.py

回答四件事：
1. TTC<2 s 的帧发生在什么时刻（相对 t0）？
2. 是哪些后车造成的？来自几辆不同的车？
3. 每辆车的暴露是否连续 >= 0.5 s？
4. 这些暴露在合流口还是别处？是否与源事件（下游停车）在时空上相容？

同时核验：无源事件臂（plain）是否真的为零——若为零，说明暴露与源事件同现。
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

VEH_LEN = 5.0
GAP_EPS = 0.5
TTC_THR = 2.0
BAND = 100.0
TARGET_X = 4000.0


def scan(arm: str, d) -> dict:
    pos = d[f"{arm}_pos"]
    spd = d[f"{arm}_spd"]
    road = d[f"{arm}_road"]
    ids = [str(x) for x in d["event_ids"]] if False else None  # placeholder
    t0 = float(d["event_t0"])
    step = float(d["step_s"])
    n_steps = pos.shape[0]

    hits = []            # (t_rel, rear_slot, edge_code, g, dv, ttc)
    for k in range(n_steps):
        x_all = pos[k].astype(np.float64)
        v_all = spd[k].astype(np.float64)
        r_all = road[k]
        ok = np.isfinite(x_all) & np.isfinite(v_all) & (r_all >= 0)
        if ok.sum() < 2:
            continue
        for code in np.unique(r_all[ok]):
            m = ok & (r_all == code)
            x = x_all[m]
            v = v_all[m]
            idxs = np.where(m)[0]
            if x.size < 2:
                continue
            order = np.argsort(x)
            x, v, idxs = x[order], v[order], idxs[order]
            g = (x[1:] - x[:-1]) - VEH_LEN
            dv = v[:-1] - v[1:]
            rear_in = (x[:-1] >= TARGET_X - BAND) & (x[:-1] <= TARGET_X + BAND)
            keep = (dv > 0) & (g > GAP_EPS) & rear_in & ((g / dv) < TTC_THR)
            for j in np.where(keep)[0]:
                hits.append({
                    "t_rel": round((k * step) - t0, 2),
                    "slot": int(idxs[j]),
                    "edge": int(code),
                    "g": round(float(g[j]), 2),
                    "dv": round(float(dv[j]), 2),
                    "ttc": round(float(g[j] / dv[j]), 3),
                })
    # 按后车聚合，算连续时长
    by_slot = defaultdict(list)
    for h in hits:
        by_slot[h["slot"]].append(h["t_rel"])
    per_veh = []
    for slot, ts in by_slot.items():
        ts = sorted(ts)
        # 最长连续段（容差 2 步 = 0.1 s）
        best = cur = 1
        run_start = ts[0]
        best_start = ts[0]
        for a, b in zip(ts, ts[1:]):
            if b - a <= step_tol:
                cur += 1
                if cur > best:
                    best = cur
                    best_start = run_start
            else:
                cur = 1
                run_start = b
        span = best * float(d["step_s"])
        per_veh.append({"slot": slot, "n_frames": len(ts),
                        "first_t": ts[0], "last_t": ts[-1],
                        "max_run_s": round(span, 2), "run_start_t": round(best_start, 2)})
    per_veh.sort(key=lambda r: -r["max_run_s"])
    return {"n_hit_frames": len(hits), "n_distinct_rear": len(by_slot),
            "per_vehicle": per_veh, "sample": hits[:12]}


def main() -> int:
    global step_tol
    src = Path("code/outputs/analysis/P3_merge_merge/arms.npz")
    d = np.load(src)
    step = float(d["step_s"])
    step_tol = step * 2.01

    out = {"source": str(src), "ttc_thr": TTC_THR, "band": BAND,
           "target_x": TARGET_X, "step_s": step}
    for arm in ("plain", "event"):
        out[arm] = scan(arm, d)

    dst = Path("code/outputs/analysis/P3_merge_verify")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "verify.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                     encoding="utf-8")

    for arm in ("plain", "event"):
        r = out[arm]
        print(f"\n=== {arm} ===")
        print(f"TTC<{TTC_THR}s 帧数: {r['n_hit_frames']}  涉及后车数: {r['n_distinct_rear']}")
        for v in r["per_vehicle"][:10]:
            print(f"  slot {v['slot']:5d}  帧 {v['n_frames']:4d}  "
                  f"t {v['first_t']:7.2f}→{v['last_t']:7.2f}  最长连续 {v['max_run_s']:.2f}s "
                  f"（起 {v['run_start_t']:.2f}）")
        if r["sample"]:
            print("  样例（前 5 条）:")
            for h in r["sample"][:5]:
                print(f"    t={h['t_rel']:7.2f} slot={h['slot']:5d} edge={h['edge']} "
                      f"g={h['g']:6.2f} dv={h['dv']:5.2f} TTC={h['ttc']:.2f}")
    print(f"\nwritten: {dst / 'verify.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
