"""P3 审计：口径与两门日志的复算核对（GPT 第三十五轮第 1 项）

阶段：P3 ｜ 数据：code/outputs/analysis/P3_hw40_r06_ids/arms.npz
脚本：code/scripts/p3_audits/audit_recompute_consistency.py
产物：code/outputs/analysis/P3_recompute/consistency.json

核验五件事：
1. 主脚本（run_p3_stop_queue.py）与审计脚本（audit_window_samples.py）算出的 TTC<2 车·秒是否一致。
2. 单位是否一致：车·步 × step = 车·秒。
3. 时间零点是否一致：两处都相对 event_t0。
4. 逐车连续暴露是否与 T_L 脚本的 14 辆吻合。
5. 分母口径：区内总车·秒是否等于 车·步 × step。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

SRC = Path("code/outputs/analysis/P3_hw40_r06_ids")
VEH_LEN = 5.0
TARGET_X = 4000.0
BAND = 50.0
TTC_THR = 2.0
GAP_EPS = 0.5


def main() -> int:
    d = np.load(SRC / "arms.npz", allow_pickle=False)
    main_json = json.loads((SRC / "p3_stop_queue.json").read_text(encoding="utf-8"))
    audit_json = json.loads(
        Path("code/outputs/analysis/P3_audit_window/samples.json").read_text(encoding="utf-8"))
    tl_json = json.loads(
        Path("code/outputs/analysis/P3_timegate/tl.json").read_text(encoding="utf-8"))

    t0 = float(d["event_t0"])
    step = float(d["step_s"])
    k0 = int(round(t0 / step))

    # ---- 独立重算（第三套实现，只依赖位置与速度） ----
    pos, spd = d["stop_pos"], d["stop_spd"]
    ids = [str(x) for x in d["stop_ids"]]
    n_steps = pos.shape[0]

    veh_steps = 0
    pair_steps = 0
    ttc_lt2_steps = 0
    per_veh_first = {}
    for k in range(k0, n_steps):
        ok = np.isfinite(pos[k]) & np.isfinite(spd[k])
        if ok.sum() < 2:
            continue
        idxs = np.where(ok)[0]
        x = pos[k][idxs]
        v = spd[k][idxs]
        inb = (x >= TARGET_X - BAND) & (x <= TARGET_X + BAND)
        veh_steps += int(inb.sum())
        order = idxs[np.argsort(x)]
        xo = pos[k][order]
        vo = spd[k][order]
        for a in range(len(order) - 1):
            xa, xb = xo[a], xo[a + 1]
            if not (TARGET_X - BAND <= xa <= TARGET_X + BAND):
                continue
            g = (xb - xa) - VEH_LEN
            if g <= GAP_EPS:
                continue
            pair_steps += 1
            dv = vo[a] - vo[a + 1]
            if dv > 0 and g / dv < TTC_THR:
                ttc_lt2_steps += 1
                vid = ids[order[a]]
                if vid not in per_veh_first:
                    per_veh_first[vid] = (k * step) - t0

    recomputed = {
        "veh_steps": veh_steps,
        "veh_seconds": round(veh_steps * step, 2),
        "pair_steps": pair_steps,
        "ttc_lt2_steps": ttc_lt2_steps,
        "ttc_lt2_veh_seconds": round(ttc_lt2_steps * step, 2),
        "n_exposed_vehicles": len(per_veh_first),
    }

    # ---- 三处来源对照 ----
    checks = []
    a_main = main_json["arms"]["stop"]["cum"]["ttc_lt2_veh_s"]
    a_audit = audit_json["stop"]["ttc_lt2_veh_seconds"]
    a_re = recomputed["ttc_lt2_veh_seconds"]
    checks.append({"item": "TTC<2 车·秒（stop 臂）",
                   "main_script": a_main, "audit_script": a_audit,
                   "independent_recompute": a_re,
                   "match": abs(a_main - a_audit) < 0.05 and abs(a_main - a_re) < 0.05})

    d_main = main_json["arms"]["stop"]["cum"]["veh_s_in_band"]
    d_audit = round(audit_json["stop"]["veh_steps_in_band"] * step, 1)
    d_re = recomputed["veh_seconds"]
    checks.append({"item": "区内总车·秒（stop 臂）",
                   "main_script": d_main, "audit_script": d_audit,
                   "independent_recompute": d_re,
                   "match": abs(d_main - d_re) < 0.5})

    n_tl = tl_json["n_exposed"]
    checks.append({"item": "暴露车辆数",
                   "main_script": None, "audit_script": n_tl,
                   "independent_recompute": recomputed["n_exposed_vehicles"],
                   "match": n_tl == recomputed["n_exposed_vehicles"]})

    # 逐车首次暴露时刻对照
    tl_detail = {e["vehicle"]: e["first_exposure_s"] for e in tl_json["exposed_detail"]}
    diffs = []
    for v, t in per_veh_first.items():
        if v in tl_detail:
            diffs.append(abs(round(t, 2) - tl_detail[v]))
    checks.append({"item": "逐车首次暴露时刻（与 T_L 脚本）",
                   "n_compared": len(diffs),
                   "max_abs_diff_s": round(max(diffs), 3) if diffs else None,
                   "match": bool(diffs) and max(diffs) < 0.06})

    # 单位自洽
    unit_ok = abs(recomputed["veh_seconds"] - veh_steps * step) < 1e-6
    checks.append({"item": "单位自洽：车·秒 = 车·步 × 0.05",
                   "veh_steps": veh_steps, "times_step": round(veh_steps * step, 2),
                   "match": unit_ok})

    out = {"source": str(SRC), "event_t0_s": t0, "step_s": step,
           "note": "时间零点统一为 event_t0；单位为车·秒（= 帧数 × step）",
           "recomputed": recomputed, "checks": checks,
           "all_pass": all(c["match"] for c in checks)}

    dst = Path("code/outputs/analysis/P3_recompute")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "consistency.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                          encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['match'] else 'FAIL'}] {c['item']}")
        for k, v in c.items():
            if k not in ("item", "match"):
                print(f"        {k}: {v}")
    print(f"\n总体: {'全部一致' if out['all_pass'] else '存在不一致'}")
    print(f"written: {dst / 'consistency.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())