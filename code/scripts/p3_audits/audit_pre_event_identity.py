"""P3 准入审计 1：事件前两臂一致性核验

阶段：P3 ｜ 数据：code/outputs/analysis/P3_hw40_r06_ids/arms.npz
脚本：code/scripts/p3_audits/audit_pre_event_identity.py
产物：code/outputs/analysis/P3_audit_pre_event/identity.json

为什么必须做：风险门与时间门的全部差值，都建立在「两臂在源事件之前逐车完全一致」这个前提上。
若前提不成立，暴露与 T_L 的差值可能来自初始条件不同，而不是源事件。

判据：t0 之前（预热 120 s 内），同一 ID 的车在两臂的
      位置差、速度差应为 0（浮点容差 1e-6）。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

SRC = Path("code/outputs/analysis/P3_hw40_r06_ids/arms.npz")
TOL = 1e-6


def main() -> int:
    d = np.load(SRC, allow_pickle=False)
    p_ids = [str(x) for x in d["plain_ids"]]
    s_ids = [str(x) for x in d["stop_ids"]]
    p_pos, p_spd = d["plain_pos"], d["plain_spd"]
    s_pos, s_spd = d["stop_pos"], d["stop_spd"]
    t0 = float(d["event_t0"])
    step = float(d["step_s"])
    k0 = int(round(t0 / step))

    p_idx = {v: i for i, v in enumerate(p_ids)}
    common = [v for v in s_ids if v in p_idx]
    print(f"配对车辆 {len(common)}；事件 t0 = {t0} s（第 {k0} 步）")

    # 逐车统计 t0 之前的最大位置差与速度差
    max_pos = 0.0
    max_spd = 0.0
    n_bad = 0
    n_compared = 0
    bad_list = []
    for v in common:
        ip = p_idx[v]
        is_ = s_ids.index(v)
        pp = p_pos[:k0, ip]
        sp = s_pos[:k0, is_]
        pv = p_spd[:k0, ip]
        sv = s_spd[:k0, is_]
        both = np.isfinite(pp) & np.isfinite(sp)
        if not both.any():
            continue
        dp = np.abs(pp[both] - sp[both])
        both_v = np.isfinite(pv) & np.isfinite(sv)
        dv = np.abs(pv[both_v] - sv[both_v]) if both_v.any() else np.array([0.0])
        n_compared += 1
        m_p, m_v = float(dp.max()), float(dv.max())
        max_pos = max(max_pos, m_p)
        max_spd = max(max_spd, m_v)
        if m_p > TOL or m_v > TOL:
            n_bad += 1
            if len(bad_list) < 10:
                bad_list.append({"vehicle": v, "max_pos_diff": round(m_p, 9),
                                 "max_spd_diff": round(m_v, 9)})

    # 逐帧：每步有多少车在网、两臂在网车辆集合是否一致
    set_mismatch = 0
    for k in range(k0):
        a = set(np.where(np.isfinite(p_pos[k]))[0].tolist())
        b = set(np.where(np.isfinite(s_pos[k]))[0].tolist())
        # 只能比较共同 ID 的在网状态
        if len(a) and len(b):
            pa = {p_ids[i] for i in a}
            sb = {s_ids[i] for i in b}
            if pa != sb:
                set_mismatch += 1

    out = {
        "source": str(SRC),
        "event_t0_s": t0,
        "n_common_ids": len(common),
        "n_compared": n_compared,
        "tolerance": TOL,
        "max_pos_diff_m": round(max_pos, 9),
        "max_spd_diff_mps": round(max_spd, 9),
        "n_vehicles_exceeding_tol": n_bad,
        "bad_examples": bad_list,
        "frames_with_different_vehicle_sets": set_mismatch,
        "frames_checked": k0,
        "verdict": "PASS" if (n_bad == 0 and max_pos <= TOL and max_spd <= TOL) else "FAIL",
    }

    dst = Path("code/outputs/analysis/P3_audit_pre_event")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "identity.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                       encoding="utf-8")

    print(f"\n比较车辆数: {n_compared}")
    print(f"最大位置差: {max_pos:.9f} m")
    print(f"最大速度差: {max_spd:.9f} m/s")
    print(f"超容差车辆数: {n_bad}")
    print(f"在网车辆集合不一致的帧: {set_mismatch} / {k0}")
    print(f"\n判定: {out['verdict']}")
    print(f"written: {dst / 'identity.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())