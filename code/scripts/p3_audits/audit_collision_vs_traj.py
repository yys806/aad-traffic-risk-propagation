"""0.0.1 前置核查：SUMO 碰撞告警 与 轨迹净距 为什么对不上。

背景：0.0.0 的 R2 网格里，「反应 1.0 s / 车头 130 m」那一格
       报告最小净距 2.47 m（无重叠），但 SUMO 日志记了 50 次 collision，gap=-0.01。
       两者若指同一批车、同一时间窗，就是不相容的。
       GPT 要求：分别记录 SUMO 碰撞告警、minGap 违规、物理接触/重叠、teleport，
       逐车对齐原生日志与轨迹。

本脚本做三件事：
1. 跑该格事件臂，把 位置/速度/ID/步长/事件时刻 存成 npz；
2. 把 SUMO 的 stderr 全量留存（碰撞告警在里面）；
3. 解析告警，逐条到轨迹里查同一时刻、同一对车的实际净距。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_collision_audit"
VEH_LEN = 5.0


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    react, hw = 1.0, 130.0
    code = f"""
import sys, json, numpy as np
sys.path.insert(0, r"{Path(__file__).resolve().parent}")
sys.path.insert(0, r"{Path(__file__).resolve().parents[1]}")
import run_p3_stop_queue as sq
r = sq.run(r"{OUT/'_scratch'}", "audit_stop", 0.0, True, {hw}, 20261120, {react})
np.savez_compressed(r"{OUT/'traj.npz'}", pos=r["pos"], spd=r["spd"],
                    ids=np.array(r["ids"], dtype=object),
                    event_t0=r["event_t0"], step=r["step_s"])
json.dump({{"event_t0": r["event_t0"], "n_veh": r["n_slots_used"],
            "source_id": r["source_id"]}},
          open(r"{OUT/'meta.json'}", "w", encoding="utf-8"), ensure_ascii=False)
print("SAVED", r["n_slots_used"], r["event_t0"])
"""
    print("跑该格事件臂（约 15 分钟）...", flush=True)
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    (OUT / "sumo_stderr.log").write_text((p.stdout or "") + "\n=== STDERR ===\n" + (p.stderr or ""),
                                         encoding="utf-8")
    warn = (p.stdout or "") + (p.stderr or "")
    print(p.stdout.strip()[-300:], flush=True)

    # 解析碰撞告警
    pat = re.compile(r"Vehicle '([^']+)'; collision with vehicle '([^']+)', "
                     r"lane='([^']+)', gap=([-\d.]+), time=([\d.]+)")
    cols = [(m.group(1), m.group(2), float(m.group(4)), float(m.group(5)))
            for m in pat.finditer(warn)]
    print(f"解析到碰撞告警 {len(cols)} 条", flush=True)

    d = np.load(OUT / "traj.npz", allow_pickle=True)
    pos, spd, ids = d["pos"], d["spd"], list(d["ids"])
    step = float(d["step"])
    slot = {v: i for i, v in enumerate(ids)}
    print(f"轨迹 {pos.shape}，step={step}，事件 t0={float(d['event_t0']):.1f}", flush=True)

    # 逐条核对：碰撞时刻的轨迹净距 vs 告警净距
    print(f"\n{'告警时刻':>9} {'后车':>8} {'前车':>8} {'告警净距':>9} "
          f"{'轨迹净距':>9} {'后车速':>8} {'前车速':>8}")
    rows = []
    for rear, lead, gap_w, tw in cols[:15]:
        k = int(round(tw / step))
        if k >= pos.shape[0]:
            continue
        ri, li = slot.get(rear), slot.get(lead)
        if ri is None or li is None:
            continue
        xr, xl = float(pos[k, ri]), float(pos[k, li])
        vr, vl = float(spd[k, ri]), float(spd[k, li])
        g_traj = (xr - xl) - VEH_LEN
        print(f"{tw:>9.2f} {rear:>8} {lead:>8} {gap_w:>9.2f} {g_traj:>9.2f} "
              f"{vr:>8.2f} {vl:>8.2f}")
        rows.append({"t": tw, "rear": rear, "lead": lead, "gap_warn": gap_w,
                     "gap_traj": round(g_traj, 3), "v_rear": round(vr, 2),
                     "v_lead": round(vl, 2)})

    # 全轨迹统计：有多少帧存在净距 < -0.05 的配对
    neg_frames, neg_min = 0, np.inf
    for k in range(pos.shape[0]):
        x = pos[k].astype(np.float64)
        ok = np.isfinite(x)
        if ok.sum() < 2:
            continue
        xs = np.sort(x[ok])
        g = (xs[1:] - xs[:-1]) - VEH_LEN
        if g.min() < -0.05:
            neg_frames += 1
        neg_min = min(neg_min, float(g.min()))
    print(f"\n全轨迹最小净距 {neg_min:.3f} m；净距<-0.05 的帧数 {neg_frames}", flush=True)

    (OUT / "audit.json").write_text(json.dumps(
        {"n_warn": len(cols), "min_gap_traj": round(neg_min, 3),
         "neg_frames": neg_frames, "sample": rows},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written: {OUT/'audit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
