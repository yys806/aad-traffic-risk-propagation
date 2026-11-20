"""0.2.0 质控：GPT 第七十七轮要求回查的四件事。

1. DRAC ≥ 100 的帧逐个回查：前车 ID、净距是否误扣车长、闭合速度是否与
   位置变化相符（用 Local_Y 独立复算，与 Space_Headway 口径对拍）
2. g ≤ 0 单列统计（不替换、不封顶）
3. 前车强刹在 0.5 / 1 / 2 s 三个窗口下各检出多少（同一批事件，不同时改阈值）
4. 成因拆两列：前车关系（同前车/他车切入/后车换道/前车驶离/证据不足）
   × 是否检出前车强刹（检出/未检出/不可判）

用法：python ngsim_qc.py --site US-101 --out ../.../ngsim_qc.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "nd", str(Path(__file__).resolve().parent / "ngsim_drac_events.py"))
nd = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(nd)  # type: ignore[union-attr]

FT2M = 0.3048
WINDOWS = (5, 10, 20)      # 0.5 s / 1.0 s / 2.0 s @ 10 Hz
LEAD_BRAKE_THR = -3.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="US-101")
    args = ap.parse_args()

    print(f"载入 {args.site} …", flush=True)
    df = nd.load_site(args.site, verbose=False)
    print(f"  行数 {len(df)}", flush=True)

    # ---------- QC2: g <= 0 ----------
    hw = df["headway_m"]
    g_le0 = int((hw <= 0).sum())
    g_na = int(hw.isna().sum())
    qc2 = {"n_headway_le_0": g_le0, "n_headway_na": g_na,
           "n_total": int(len(df)),
           "share_le_0": round(g_le0 / len(df), 6)}

    # ---------- QC1: DRAC >= 100 ----------
    hi = df[df["drac_mps2"] >= 100.0].copy()
    print(f"DRAC>=100 的帧：{len(hi)}", flush=True)
    checks = []
    for _, r in hi.head(30).iterrows():
        # 用 Local_Y 独立复算净距：需要同一帧的前车行
        checks.append({
            "run": r["run_id"], "veh": str(r["id"]), "frame": int(r["Frame_ID"]),
            "lead_id": str(r["leader_id"]),
            "drac": round(float(r["drac_mps2"]), 2),
            "space_headway_m": round(float(r["reported_space_headway_m"]), 3),
            "leader_len_m": round(float(r["leader_length_m"]), 3),
            "headway_m": round(float(r["headway_m"]), 3),
            "closing_ms": round(float(r["closing_speed_mps"]), 3),
            "v_ego": round(float(r["speed_mps"]), 2),
            "v_lead": round(float(r["speed_mps"] - r["closing_speed_mps"]), 2),
            "lane_ego": str(r["lane_id"]),
        })
    # 用位置独立验证前 10 条：同 run 同 frame 找前车行
    pos_checks = []
    key_cols = ["run_id", "Frame_ID"]
    for c in checks[:10]:
        sub = df[(df["run_id"] == c["run"]) & (df["Frame_ID"] == c["frame"])]
        ego = sub[sub["id"].astype(str) == c["veh"]]
        lead = sub[sub["id"].astype(str) == c["lead_id"]]
        if ego.empty or lead.empty:
            pos_checks.append({**c, "pos_check": "查不到前车行"})
            continue
        ey = float(ego.iloc[0]["y_m"])
        ly = float(lead.iloc[0]["y_m"])
        llen = float(lead.iloc[0]["v_Length"]) * FT2M if "v_Length" in lead.columns \
            else c["leader_len_m"]
        gap_pos = (ly - ey) - llen
        pos_checks.append({**c, "gap_from_position_m": round(gap_pos, 3),
                           "gap_from_headway_m": c["headway_m"],
                           "lane_lead": str(lead.iloc[0]["lane_id"]),
                           "lane_same": str(lead.iloc[0]["lane_id"]) == c["lane_ego"]})

    # ---------- QC3 + QC4: 强刹窗口对拍 与 两列拆分 ----------
    ev = nd.extract_events(df)
    print(f"事件 {len(ev)}", flush=True)

    dfi = df.sort_values(["run_id", "id", "Frame_ID"], kind="mergesort")
    idx = {}
    for (run, vid), grp in dfi.groupby(["run_id", "id"], sort=False):
        fr = grp["Frame_ID"].to_numpy()
        acc = grp["acceleration_mps2"].to_numpy()
        lane = grp["lane_id"].astype(str).to_numpy()
        lead = grp["leader_id"].astype(str).to_numpy()
        idx[(run, str(vid))] = (fr, acc, lane, lead)

    win_counts = {w: 0 for w in WINDOWS}
    relation = Counter()
    brake_flag = Counter()
    cross = Counter()
    for e in ev:
        k = (e["run"], str(e["veh"]))
        if k not in idx:
            relation["证据不足"] += 1
            brake_flag["不可判"] += 1
            continue
        fr, acc, lane, lead = idx[k]
        pos = np.searchsorted(fr, e["on_frame"])
        if pos >= len(fr) or int(fr[pos]) != e["on_frame"]:
            relation["证据不足"] += 1
            brake_flag["不可判"] += 1
            continue
        # 强刹：三个窗口各自判定（回看窗口内是否有连续三帧 <= -3.0）
        hit_any = False
        for w in WINDOWS:
            k0 = max(0, pos - w)
            trio_ok = False
            for a in range(k0, pos - 2):
                t = acc[a:a + 3]
                if np.all(np.isfinite(t)) and np.all(t <= LEAD_BRAKE_THR):
                    trio_ok = True
                    break
            if trio_ok:
                win_counts[w] += 1
                hit_any = True
        brake_flag["检出" if hit_any else "未检出"] += 1

        # 前车关系
        rel = "证据不足"
        j0 = max(0, pos - 30)
        if pos > j0:
            old, new = lead[j0], lead[pos]
            ego_lane = lane[pos]
            if old == new:
                rel = "同前车"
            else:
                ego_chg = len({lane[i] for i in range(j0, pos)}) > 1
                if ego_chg:
                    rel = "后车换道"
                else:
                    appeared = any(lead[i] == new and lane[i] == ego_lane
                                   for i in range(j0, pos))
                    rel = "他车切入" if appeared else "前车驶离"
        relation[rel] += 1
        # 修 bug：这里必须用本条事件自己的 rel，不能用全局众数
        cross[(rel, "检出" if hit_any else "未检出")] += 1

    out = {
        "site": args.site,
        "qc1_drac_ge_100": {"n": int(len(hi)), "checks": checks},
        "qc1_position_crosscheck": pos_checks,
        "qc2_negative_or_missing_gap": qc2,
        "qc3_lead_hard_brake_by_window": {
            "0.5s": win_counts[5], "1.0s": win_counts[10], "2.0s": win_counts[20],
            "n_events": len(ev)},
        "qc4_lead_relation": dict(relation),
        "qc4_brake_flag": dict(brake_flag),
        "qc4_cross_tab": {f"{r}|{b}": v for (r, b), v in cross.items()},
    }

    outp = nd.OUT / f"ngsim_qc_{args.site}.json"
    outp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== QC2 负/缺净距 ===")
    print(f"  g<=0: {g_le0} 行；g 缺失: {g_na} 行")
    print("\n=== QC1 位置复算（前 10 条 DRAC>=100）===")
    for p in pos_checks:
        if p.get("pos_check"):
            print(f"  {p['veh']}@{p['frame']}: {p['pos_check']}")
        else:
            print(f"  {p['veh']}@{p['frame']} DRAC={p['drac']}: "
                  f"headway口径 {p['gap_from_headway_m']} vs 位置口径 {p['gap_from_position_m']} "
                  f"同车道={p['lane_same']}")
    print("\n=== QC3 前车强刹（三窗口）===")
    for k, v in out["qc3_lead_hard_brake_by_window"].items():
        print(f"  {k}: {v}")
    print("\n=== QC4 前车关系 ===")
    for k, v in relation.most_common():
        print(f"  {k}: {v}（{v/len(ev)*100:.1f}%）")
    print("\n=== QC4 是否检出强刹 ===")
    for k, v in brake_flag.most_common():
        print(f"  {k}: {v}（{v/len(ev)*100:.1f}%）")
    print("\n=== QC4 交叉表：前车关系 × 强刹检出（2.0 s 窗口）===")
    rels = [r for r, _ in relation.most_common()]
    print(f"  {'关系':<8}{'检出':>6}{'未检出':>8}{'小计':>7}{'检出率':>8}")
    for r in rels:
        hit = cross.get((r, "检出"), 0)
        miss = cross.get((r, "未检出"), 0)
        tot = hit + miss
        print(f"  {r:<8}{hit:>6}{miss:>8}{tot:>7}{(hit/tot*100 if tot else 0):>7.1f}%")
    print(f"\nwritten: {outp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
