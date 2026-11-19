"""P3 时间门：逐车计算本地可观测时刻 T_L（向量化版）

阶段：P3 ｜ 数据：code/outputs/analysis/P3_hw40_r06_ids/arms.npz（含车辆 ID）
脚本：code/scripts/p3_audits/compute_tl_v2.py
产物：code/outputs/analysis/P3_timegate/tl.json + tl.csv

T_L 定义（P0 预注册 §1）：
  某辆车、某次运行，它的**本地输入**（本车速度、与前车净距、前车速度）
  第一次与「没有发生源事件的世界」出现差别的时刻。
  T_L 之前，任何本地控制器收到的输入与无事世界完全相同，数学上无法区分有没有事件。

为什么有 v2：v1 在每辆车每一步里重算全路前车，O(n²)，实测 7 分钟未跑完。
v2 先把两臂的 (前车净距, 前车速度) 全时窗表各算一遍，再逐车比对。
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

VEH_LEN = 5.0
GAP_EPS = 0.5
TOL_V = 0.05          # m/s，P0 规定
TOL_G = 0.1           # m，P0 规定
TARGET_X = 4000.0
BAND = 50.0
TTC_THR = 2.0


def leader_tables(pos: np.ndarray, spd: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """一次性算出全时窗的 (前车净距, 前车速度)，形状同 pos。"""
    steps, slots = pos.shape
    g_out = np.full((steps, slots), np.nan, dtype=np.float32)
    vl_out = np.full((steps, slots), np.nan, dtype=np.float32)
    for k in range(steps):
        x = pos[k]
        v = spd[k]
        ok = np.isfinite(x) & np.isfinite(v)
        if ok.sum() < 2:
            continue
        idxs = np.where(ok)[0]
        order = idxs[np.argsort(x[idxs])]      # 位置升序：后 -> 前
        rear = order[:-1]
        front = order[1:]
        g_out[k, rear] = (x[front] - x[rear]) - VEH_LEN
        vl_out[k, rear] = v[front]
    return g_out, vl_out


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1
               else "code/outputs/analysis/P3_hw40_r06_ids/arms.npz")
    d = np.load(src, allow_pickle=False)
    if "plain_ids" not in d.files:
        raise SystemExit("该 npz 没有车辆 ID，需用新版脚本重跑")

    p_ids = [str(x) for x in d["plain_ids"]]
    s_ids = [str(x) for x in d["stop_ids"]]
    p_pos, p_spd = d["plain_pos"], d["plain_spd"]
    s_pos, s_spd = d["stop_pos"], d["stop_spd"]
    t0 = float(d["event_t0"])
    step = float(d["step_s"])

    print("预计算前车表 …", flush=True)
    pg, pvl = leader_tables(p_pos, p_spd)
    sg, svl = leader_tables(s_pos, s_spd)

    p_idx = {v: i for i, v in enumerate(p_ids)}
    s_idx = {v: i for i, v in enumerate(s_ids)}
    common = [v for v in s_ids if v in p_idx]

    n_steps = min(p_pos.shape[0], s_pos.shape[0])
    k_start = max(0, int(round(t0 / step)) - 200)   # 从 t0 前 10 s 开始查

    tl = {}
    for v in common:
        ip, is_ = p_idx[v], s_idx[v]
        pv = p_spd[k_start:n_steps, ip]
        sv = s_spd[k_start:n_steps, is_]
        valid_v = np.isfinite(pv) & np.isfinite(sv)
        dv_hit = valid_v & (np.abs(pv - sv) > TOL_V)

        gri = np.abs(pg[k_start:n_steps, ip] - sg[k_start:n_steps, is_])
        dg_hit = np.isfinite(gri) & (gri > TOL_G)

        vli = np.abs(pvl[k_start:n_steps, ip] - svl[k_start:n_steps, is_])
        dl_hit = np.isfinite(vli) & (vli > TOL_V)

        cands = [int(np.argmax(m)) for m in (dv_hit, dg_hit, dl_hit) if m.any()]
        tl[v] = None if not cands else ((k_start + min(cands)) * step) - t0

    first_exposure = {}
    for k in range(int(round(t0 / step)), n_steps):
        ok = np.isfinite(s_pos[k]) & np.isfinite(s_spd[k])
        if ok.sum() < 2:
            continue
        idxs = np.where(ok)[0]
        order = idxs[np.argsort(s_pos[k][idxs])]
        rear, front = order[:-1], order[1:]
        g = (s_pos[k, front] - s_pos[k, rear]) - VEH_LEN
        dv = s_spd[k, rear] - s_spd[k, front]
        inb = (s_pos[k, rear] >= TARGET_X - BAND) & (s_pos[k, rear] <= TARGET_X + BAND)
        hit = inb & (dv > 0) & (g > GAP_EPS) & ((g / np.maximum(dv, 1e-9)) < TTC_THR)
        for a in rear[hit]:
            vid = s_ids[a]
            if vid not in first_exposure:
                first_exposure[vid] = (k * step) - t0

    rows = [{"vehicle": v, "t_L_s": tl[v],
             "first_exposure_s": first_exposure.get(v)} for v in common]

    detail = []
    for v, te in sorted(first_exposure.items(), key=lambda kv: kv[1]):
        tL = tl.get(v)
        detail.append({"vehicle": v, "first_exposure_s": round(te, 2),
                       "t_L_s": None if tL is None else round(tL, 2),
                       "headroom_s": None if tL is None else round(te - tL, 2)})

    vals = [r["t_L_s"] for r in rows if r["t_L_s"] is not None]
    stats = None
    if vals:
        a = np.array(vals, dtype=float)
        stats = {"median": round(float(np.median(a)), 2),
                 "p10": round(float(np.percentile(a, 10)), 2),
                 "p90": round(float(np.percentile(a, 90)), 2),
                 "min": round(float(a.min()), 2),
                 "max": round(float(a.max()), 2)}

    out = {"source": str(src), "event_t0": t0, "step_s": step,
           "tol_v_mps": TOL_V, "tol_g_m": TOL_G,
           "n_common": len(common), "n_tL_found": len(vals),
           "n_exposed": len(first_exposure),
           "tL_stats": stats, "exposed_detail": detail, "vehicles": rows}

    dst = Path("code/outputs/analysis/P3_timegate")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "tl.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    with (dst / "tl.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["vehicle", "t_L_s", "first_exposure_s"])
        w.writeheader()
        w.writerows(rows)

    print(f"配对车辆 {len(common)}  找到 T_L {len(vals)}  产生暴露 {len(first_exposure)}")
    print(f"\n{'vehicle':>10} {'T_L(s)':>9} {'首次暴露(s)':>12} {'暴露−T_L(s)':>12}")
    for e in detail:
        print(f"{e['vehicle']:>10} {str(e['t_L_s']):>9} {e['first_exposure_s']:>12} "
              f"{str(e['headroom_s']):>12}")
    if stats:
        print(f"\nT_L 分布（秒，相对事件）：中位 {stats['median']}  "
              f"p10 {stats['p10']}  p90 {stats['p90']}  min {stats['min']}  max {stats['max']}")
    print(f"\nwritten: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())