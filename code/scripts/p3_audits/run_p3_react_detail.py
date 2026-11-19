"""R2 细粒度核查：把「高速事件帧」拆成「独立事件」，并看后车速度与净距分布。

目的：grid.json 只给了帧数（2994/3010 这类），但帧数会重复计数同一辆车连续多帧，
      也可能被极小净距放大（DRAC 在 g→minGap 时分母趋零）。
      本脚本重跑指定格，逐帧导出后车速度、净距、闭合速度，按「连续同一后车」合并为事件。

用法：python run_p3_react_detail.py --react 1.0 --headway 130
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_p3_stop_queue as sq  # noqa: E402

OUT = sq.ROOT / "code/outputs/analysis/P3_react_detail"
VEH_LEN = 5.0
DRAC_THR = 3.4
STEP = 0.05


def per_pair(pos, spd):
    """逐帧列出所有闭合配对：(帧号, 后车索引, 净距, 闭合速度, DRAC, 后车速度)。"""
    rows = []
    n = pos.shape[0]
    for k in range(n):
        x = pos[k].astype(np.float64)
        v = spd[k].astype(np.float64)
        ok = np.isfinite(x) & np.isfinite(v)
        if ok.sum() < 2:
            continue
        idx = np.where(ok)[0]
        x, v = x[ok], v[ok]
        o = np.argsort(x)
        x, v, idx = x[o], v[o], idx[o]
        g = (x[1:] - x[:-1]) - VEH_LEN
        c = v[:-1] - v[1:]
        valid = (g > 0.05) & (c > 0.0)
        for j in np.where(valid)[0]:
            dr = c[j] ** 2 / (2.0 * g[j])
            rows.append((k, int(idx[j]), float(g[j]), float(c[j]), float(dr),
                         float(v[j]), float(v[j + 1])))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--react", type=float, required=True)
    ap.add_argument("--headway", type=float, required=True)
    ap.add_argument("--seed", type=int, default=20261120)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    tag = f"r{args.react:.1f}_hw{args.headway:.0f}"
    tmp = OUT / f"_scratch_{tag}"
    tmp.mkdir(parents=True, exist_ok=True)
    print(f"[{tag}] 跑事件臂 ...", flush=True)
    r = sq.run(tmp, f"{tag}_stop", 0.0, True, args.headway, args.seed, args.react)
    rows = per_pair(r["pos"], r["spd"])
    print(f"  轨迹 {r['pos'].shape}，配对帧 {len(rows)}", flush=True)

    # 独立核验：逐帧最小净距（含负值），用来判别是否真的发生重叠
    neg_frames = 0
    min_gap_all = np.inf
    for k in range(r["pos"].shape[0]):
        x = r["pos"][k].astype(np.float64)
        ok = np.isfinite(x)
        if ok.sum() < 2:
            continue
        xs = np.sort(x[ok])
        g = (xs[1:] - xs[:-1]) - VEH_LEN
        gm = float(g.min())
        min_gap_all = min(min_gap_all, gm)
        if gm < -0.05:
            neg_frames += 1
    print(f"  全文最小净距 {min_gap_all:.3f} m；重叠帧(<-0.05m) {neg_frames}", flush=True)

    # 只看事件发生后
    t0 = r["event_t0"] or 0.0
    arr = np.array([[x[0], x[1], x[2], x[3], x[4], x[5]] for x in rows
                    if x[4] >= DRAC_THR and x[0] * STEP >= t0]) if rows else np.zeros((0, 6))
    print(f"  DRAC≥{DRAC_THR} 帧数（事件后）: {len(arr)}", flush=True)
    if len(arr) == 0:
        print("  无事件级配对")
        return 0

    # 按 (后车索引, 时间连续) 合并成独立事件
    events = []
    by_rear: dict[int, list] = {}
    for row in arr:
        by_rear.setdefault(int(row[1]), []).append(row)
    for rear, rs in by_rear.items():
        rs.sort(key=lambda z: z[0])
        cur = [rs[0]]
        for z in rs[1:]:
            if z[0] - cur[-1][0] <= 2:  # 允许 0.1 s 空档
                cur.append(z)
            else:
                events.append(cur)
                cur = [z]
        events.append(cur)

    print(f"  合并为独立事件: {len(events)} 个，涉及 {len(by_rear)} 辆车", flush=True)
    print(f"\n  {'事件':>4} {'起(s)':>8} {'持续s':>6} {'峰值DRAC':>9} "
          f"{'峰值时后车km/h':>14} {'最小净距':>9} {'最大闭合m/s':>11}")
    ev_out = []
    for i, ev in enumerate(sorted(events, key=lambda e: -max(z[4] for z in e))[:20], 1):
        pk = max(ev, key=lambda z: z[4])
        dur = (ev[-1][0] - ev[0][0]) * STEP
        print(f"  {i:>4} {ev[0][0]*STEP:>8.1f} {dur:>6.2f} {pk[4]:>9.2f} "
              f"{pk[5]*3.6:>14.1f} {min(z[2] for z in ev):>9.2f} {max(z[3] for z in ev):>11.2f}")
        ev_out.append({"t_start": round(ev[0][0] * STEP, 2), "dur_s": round(dur, 2),
                       "peak_drac": round(pk[4], 3), "v_rear_kmh": round(pk[5] * 3.6, 1),
                       "min_gap": round(min(z[2] for z in ev), 2),
                       "max_closing": round(max(z[3] for z in ev), 2)})

    # 高速事件（峰值时后车 ≥60 km/h）
    hi = [e for e in ev_out if e["v_rear_kmh"] >= 60.0]
    print(f"\n  其中峰值时后车 ≥60 km/h 的独立事件: {len(hi)} 个", flush=True)
    if hi:
        gs = sorted(e["min_gap"] for e in hi)
        print(f"    这些事件的最小净距: p10={gs[len(gs)//10]:.2f} "
              f"p50={gs[len(gs)//2]:.2f} p90={gs[int(len(gs)*0.9)]:.2f} 最小={min(gs):.2f}")
        vs = sorted(e["v_rear_kmh"] for e in hi)
        print(f"    后车速度: p10={vs[len(vs)//10]:.0f} p50={vs[len(vs)//2]:.0f} "
              f"p90={vs[int(len(vs)*0.9)]:.0f} km/h")

    (OUT / f"{tag}.json").write_text(json.dumps(
        {"tag": tag, "react": args.react, "headway": args.headway,
         "n_distinct_vehicles": len(by_rear), "n_events": len(ev_out),
         "n_hi_speed_events": len(hi), "top_events": ev_out},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/f'{tag}.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
