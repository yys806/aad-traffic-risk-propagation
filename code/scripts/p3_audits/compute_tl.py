"""P3 时间门：逐车计算本地可观测时刻 T_L（P0 预注册第 1 节的可执行实现）

阶段：P3 ｜ 数据：code/outputs/analysis/P3_hw40_r06_ids/arms.npz（含车辆 ID）
脚本：code/scripts/p3_audits/compute_tl.py
产物：code/outputs/analysis/P3_timegate/tl.json + tl.csv

T_L 定义（P0 预注册 §1）：
  对某一辆车、某一次运行，它的**本地输入**（感知范围内的前车状态：本车速度、与前车净距、前车速度）
  第一次与「没有发生源事件的世界」出现差别的时刻。

  T_L 之前，任何本地控制器收到的输入与无事世界完全相同，在数学上无法区分有没有事件。

实现：
  1. 两臂按车辆 ID 配对（只取两臂都存在的 ID）。
  2. 逐车、逐步比较三个本地输入：本车速度、与前车净距、前车速度。
  3. 第一次超出容差（速度 0.05 m/s、净距 0.1 m）的时刻 = 该车的 T_L。
  4. 前车按「同一 edge 内位置紧邻前方」重建（单车道直路，与 SUMO 内部 leader 一致）。

时间门判定（docs/P3_场景准入规则_20261119.md 门 2）：
  对产生新增暴露的后车，须有可追溯消息**早于其 T_L**，且领先量覆盖控制器的响应与执行时间。
  本脚本只算 T_L 与「消息可用时刻」的差，不代替设计决策。
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


def leader_state(pos_row: np.ndarray, spd_row: np.ndarray):
    """返回每个 slot 的前车 (净距, 前车速度)；无前车则为 (nan, nan)。单车道按位置排序。"""
    n = pos_row.size
    g = np.full(n, np.nan)
    vl = np.full(n, np.nan)
    ok = np.isfinite(pos_row) & np.isfinite(spd_row)
    if ok.sum() < 2:
        return g, vl
    idxs = np.where(ok)[0]
    order = idxs[np.argsort(pos_row[idxs])]      # 位置从小到大
    for a, b in zip(order[:-1], order[1:]):      # a 在后，b 在前
        g[a] = (pos_row[b] - pos_row[a]) - VEH_LEN
        vl[a] = spd_row[b]
    return g, vl


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

    p_idx = {v: i for i, v in enumerate(p_ids)}
    s_idx = {v: i for i, v in enumerate(s_ids)}
    common = [v for v in s_ids if v in p_idx]

    n_steps = min(p_pos.shape[0], s_pos.shape[0])
    k0 = int(round(t0 / step))

    tl = {}
    for v in common:
        ip, is_ = p_idx[v], s_idx[v]
        found = None
        for k in range(max(0, k0 - 200), n_steps):     # 从 t0 前 10 s 开始查
            pv, sv = p_spd[k, ip], s_spd[k, is_]
            if not (np.isfinite(pv) and np.isfinite(sv)):
                continue
            if abs(pv - sv) > TOL_V:
                found = (k * step) - t0
                break
            # 净距与前车速度
            pg, pvl = leader_state(p_pos[k], p_spd[k])
            sg, svl = leader_state(s_pos[k], s_spd[k])
            if np.isfinite(pg[ip]) and np.isfinite(sg[is_]):
                if abs(pg[ip] - sg[is_]) > TOL_G:
                    found = (k * step) - t0
                    break
                if np.isfinite(pvl[ip]) and np.isfinite(svl[is_]) \
                        and abs(pvl[ip] - svl[is_]) > TOL_V:
                    found = (k * step) - t0
                    break
        tl[v] = found

    # 找出产生 TTC<2 暴露的后车（与 T_L 对照）
    exposed = {}
    for k in range(k0, n_steps):
        ok = np.isfinite(s_pos[k]) & np.isfinite(s_spd[k])
        if ok.sum() < 2:
            continue
        idxs = np.where(ok)[0]
        order = idxs[np.argsort(s_pos[k][idxs])]
        for a, b in zip(order[:-1], order[1:]):
            xa, xb = s_pos[k, a], s_pos[k, b]
            g = (xb - xa) - VEH_LEN
            dv = s_spd[k, a] - s_spd[k, b]
            if g > GAP_EPS and dv > 0 and (TARGET_X - BAND) <= xa <= (TARGET_X + BAND):
                if g / dv < TTC_THR:
                    vid = s_ids[a]
                    if vid not in exposed:
                        exposed[vid] = (k * step) - t0

    rows = []
    for v in common:
        rows.append({"vehicle": v, "t_L_s": tl[v],
                     "exposed_first_s": exposed.get(v),
                     "t_L_minus_exposure_s": (None if tl[v] is None or v not in exposed
                                              else round(exposed[v] - tl[v], 2))})

    out = {"source": str(src), "event_t0": t0, "step_s": step,
           "tol_v_mps": TOL_V, "tol_g_m": TOL_G,
           "n_common": len(common),
           "n_tL_found": sum(1 for v in common if tl[v] is not None),
           "n_exposed": len(exposed),
           "exposed_detail": [
               {"vehicle": v, "first_exposure_s": round(t, 2),
                "t_L_s": (None if tl[v] is None else round(tl[v], 2)),
                "lead_s": (None if tl[v] is None else round(t - tl[v], 2))}
               for v, t in sorted(exposed.items(), key=lambda kv: kv[1])],
           "vehicles": rows}

    dst = Path("code/outputs/analysis/P3_timegate")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "tl.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    with (dst / "tl.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["vehicle", "t_L_s", "exposed_first_s",
                                          "t_L_minus_exposure_s"])
        w.writeheader()
        w.writerows(rows)

    print(f"配对车辆: {len(common)}  找到 T_L: {out['n_tL_found']}  产生暴露: {len(exposed)}")
    print(f"\n{'vehicle':>10} {'T_L(s)':>9} {'首次暴露(s)':>12} {'暴露−T_L(s)':>13}")
    for e in out["exposed_detail"]:
        print(f"{e['vehicle']:>10} {str(e['t_L_s']):>9} {e['first_exposure_s']:>12} "
              f"{str(e['lead_s']):>13}")
    # T_L 分布
    vals = [r["t_L_s"] for r in rows if r["t_L_s"] is not None]
    if vals:
        a = np.array(vals)
        print(f"\nT_L 分布（秒，相对事件）：中位 {np.median(a):.2f}  "
              f"p10 {np.percentile(a,10):.2f}  p90 {np.percentile(a,90):.2f}  "
              f"min {a.min():.2f}  max {a.max():.2f}")
    print(f"\nwritten: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())