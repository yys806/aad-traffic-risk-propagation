"""P3 反应时间网格筛查（2026-11-19，研究者在 GPT+Claude 双方评审后拍板）。

动机（Claude 指出、已核实属实）：历史上从未测过「人的反应时间 1.0–1.6 s」
配「大车头距 50–70 m」。30 组参数扫描里的 tau 是期望车头时距，不是反应时间；
`cf_param_sweep.py` 中 actionStepLength 出现 0 次。

参数依据（全部有实测出处，非调参）：
- 反应时间 1.0 / 1.3 / 1.6 s —— Olson & Sivak (1986) 第 95 分位约 1.6 s
- 车头距 50 / 60 / 70 m —— NGSIM 80–105 km/h 层 THW p25–p50 = 1.44–1.92 s，
  在 30 m/s 下对应 43–58 m；70 m 对应 2.33 s（约 p60）
- 制动能力 4.5 m/s² —— 常规车辆，沿用既有设定

预注册（跑之前写死，跑完不许改）：
- 9 格网格：(react 1.0/1.3/1.6) × (headway 50/60/70)，每格跑 plain + stop 两臂
- 不接消息臂
- 事件：源车在 x=6000 于 WARMUP 后以 4.5 m/s² 降到停，保持到观测窗结束
- 主读数：stop 臂相对 plain 臂新增的 DRAC ≥ 3.4 m/s² 帧与该帧后车速度
- 通过判据：存在后车速度 > 16.7 m/s（60 km/h）的 DRAC ≥ 3.4 帧
- 止损：只跑这一轮。9 格全部零事件 → 关掉「仿真生成遭遇」这条线，不再加参数

复用：run_p3_stop_queue.py 的 run()（建网、建流、事件注入、轨迹采集）
新增：DRAC 逐帧计算（单车道全配对）、接触检测、分速度层统计
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_p3_stop_queue as sq  # noqa: E402

ROOT = sq.ROOT
OUT = ROOT / "code/outputs/analysis/P3_react_grid"
VEH_LEN = 5.0
DRAC_THR = 3.4
SPEED_TIER = 16.7  # 60 km/h


def drac_series(pos: np.ndarray, spd: np.ndarray) -> dict:
    """逐帧算单车道全配对的 DRAC 与后车速度。

    返回每帧的最大 DRAC、对应后车速度、以及 DRAC≥3.4 的配对数。
    """
    n = pos.shape[0]
    out = np.full((n, 4), np.nan, dtype=np.float64)  # max_drac, v_rear, n_evt, min_gap
    for k in range(n):
        x = pos[k].astype(np.float64)
        v = spd[k].astype(np.float64)
        ok = np.isfinite(x) & np.isfinite(v)
        if ok.sum() < 2:
            continue
        x, v = x[ok], v[ok]
        o = np.argsort(x)
        x, v = x[o], v[o]
        g = (x[1:] - x[:-1]) - VEH_LEN
        c = v[:-1] - v[1:]  # 后车快于前车 = 闭合
        valid = (g > 0.05) & (c > 0.0)
        out[k, 3] = float(g.min()) if g.size else np.nan
        if not valid.any():
            out[k, :2] = (0.0, 0.0)
            out[k, 2] = 0
            continue
        gg, cc, vv = g[valid], c[valid], v[:-1][valid]
        dr = cc**2 / (2.0 * gg)
        j = int(np.argmax(dr))
        out[k, 0] = float(dr[j])
        out[k, 1] = float(vv[j])
        out[k, 2] = int((dr >= DRAC_THR).sum())
    return {"per_step": out}


def summarize(ds: dict, event_t0: float, step: float, stop: bool) -> dict:
    r = ds["per_step"]
    finite = np.isfinite(r[:, 0])
    if not finite.any():
        return {"events": 0, "max_drac": None, "frames_evt": 0,
                "v_rear_at_max": None, "min_gap": None, "events_hi_speed": 0}
    # 只看事件发生之后的帧（plain 臂本身也在跑，同一时刻对齐）
    k0 = int(round(event_t0 / step)) if stop else 0
    sub = r[k0:]
    evt = sub[np.isfinite(sub[:, 0])]
    if evt.size == 0:
        return {"events": 0, "max_drac": None, "frames_evt": 0,
                "v_rear_at_max": None, "min_gap": None, "events_hi_speed": 0}
    frames_evt = int((evt[:, 2] > 0).sum())
    hi = evt[(evt[:, 2] > 0) & (evt[:, 1] >= SPEED_TIER)]
    j = int(np.argmax(evt[:, 0]))
    return {
        "events": int(evt[:, 2].sum()),
        "max_drac": round(float(evt[j, 0]), 3),
        "v_rear_at_max_mps": round(float(evt[j, 1]), 2),
        "v_rear_at_max_kmh": round(float(evt[j, 1]) * 3.6, 1),
        "frames_evt": frames_evt,
        "events_hi_speed": int(hi[:, 2].sum()) if hi.size else 0,
        "frames_evt_hi_speed": int(len(hi)),
        "min_gap": round(float(np.nanmin(evt[:, 3])), 2) if np.isfinite(evt[:, 3]).any() else None,
    }


def one(tmp: Path, tag: str, react: float, headway: float, seed: int) -> dict:
    res = {}
    for arm, stop in (("plain", False), ("stop", True)):
        r = sq.run(tmp, f"{tag}_{arm}", 0.0, stop, headway, seed, react)
        ds = drac_series(r["pos"], r["spd"])
        s = summarize(ds, r["event_t0"] or 0.0, r["step_s"], stop)
        s.update({"n_veh": r["n_slots_used"], "wall_s": round(r["wall_seconds"], 1),
                  "source_id": r["source_id"], "source_v0": round(r["source_v_start"], 2)})
        res[arm] = s
        print(f"    {arm}: 车 {s['n_veh']}  DRACmax {s['max_drac']}  "
              f"事件 {s['events']}  高速事件 {s['events_hi_speed']}  "
              f"最小净距 {s['min_gap']}  {s['wall_s']}s", flush=True)
        del r
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--react", nargs="+", type=float, default=[1.0, 1.3, 1.6])
    ap.add_argument("--headway", nargs="+", type=float, default=[50.0, 60.0, 70.0])
    ap.add_argument("--seed", type=int, default=20261120)
    ap.add_argument("--smoke", action="store_true", help="只跑第一格")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    combos = [(r, h) for r in args.react for h in args.headway]
    if args.smoke:
        combos = combos[:1]

    print(f"网格 {len(combos)} 格 × 2 臂，seed={args.seed}", flush=True)
    results = []
    t_all = time.time()
    for i, (react, hw) in enumerate(combos, 1):
        tag = f"r{react:.1f}_hw{hw:.0f}"
        print(f"[{i}/{len(combos)}] react={react} headway={hw} "
              f"(THW={hw/sq.MAX_SPEED:.2f}s) ...", flush=True)
        tmp = OUT / f"_scratch_{tag}"
        tmp.mkdir(parents=True, exist_ok=True)
        try:
            r = one(tmp, tag, react, hw, args.seed)
        except Exception as e:  # noqa: BLE001
            print(f"    FAILED: {type(e).__name__}: {e}", flush=True)
            r = {"error": f"{type(e).__name__}: {e}"}
        results.append({"react_s": react, "headway_m": hw,
                        "thw_s": round(hw / sq.MAX_SPEED, 3), **r})
        (OUT / "grid.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n总耗时 {(time.time()-t_all)/60:.1f} 分钟", flush=True)
    print(f"{'react':>6} {'hw':>4} {'THW':>5} {'车':>5} {'DRACmax':>8} "
          f"{'@km/h':>7} {'事件':>5} {'高速事件':>8} {'最小净距':>8}")
    for r in results:
        if "error" in r:
            print(f"{r['react_s']:>6} {r['headway_m']:>4} ERROR {r['error'][:40]}")
            continue
        s = r["stop"]
        print(f"{r['react_s']:>6} {r['headway_m']:>4.0f} {r['thw_s']:>5.2f} "
              f"{s['n_veh']:>5} {str(s['max_drac']):>8} "
              f"{str(s.get('v_rear_at_max_kmh')):>7} {s['events']:>5} "
              f"{s['events_hi_speed']:>8} {str(s['min_gap']):>8}")
    (OUT / "grid.json").write_text(json.dumps(results, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    print(f"\nwritten: {OUT/'grid.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
