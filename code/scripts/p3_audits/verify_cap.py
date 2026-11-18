"""核验消息臂的 cap 是否按计划生效——逐秒看实际速度

阶段：P3 ｜ 数据：P3A_pilot_20261118/message.npz ｜ 脚本：code/scripts/p3_audits/verify_cap.py

GPT 要求核验：计划 cap、实际下发 cap、两车实际速度、前车 ID、动作结束后的限速状态。
脚本没记 cap 日志，但可以从实际速度反推：
  动作前速度 v_base（t0+8 那一帧）× 计划系数（1→0.9→0.9→1）
  若实际速度 ≈ v_base × 计划系数，说明 cap 生效；若明显高于，说明 cap 没压住（跟驰约束更强）。
同时用 ∫(v前 − v本)dt 对账净距变化，验证数据自洽。
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

OUT = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P3A_pilot_20261118")
VEH_LEN = 5.0
MSG_START, RAMP_IN, HOLD, RAMP_OUT = 8.0, 3.0, 15.0, 3.0
CAP_RATIO = 0.90


def planned_cap(el: float) -> float | None:
    if el < 0:
        return None
    if el < RAMP_IN:
        return 1.0 - (1.0 - CAP_RATIO) * (el / RAMP_IN)
    if el < RAMP_IN + HOLD:
        return CAP_RATIO
    if el < RAMP_IN + HOLD + RAMP_OUT:
        return CAP_RATIO + (1.0 - CAP_RATIO) * ((el - RAMP_IN - HOLD) / RAMP_OUT)
    return None


def load(arm: str):
    z = np.load(OUT / f"{arm}.npz", allow_pickle=True)
    return (z["pos"], z["spd"], [str(s) for s in z["ids"]],
            [str(s) for s in z["locked"]], float(z["event_t0"]), float(z["step_s"]))


PO, SO, ids_o, locked, t0, step = load("message")
k0 = int(round(t0 / step))
ip = {v: i for i, v in enumerate(ids_o)}
locked = [v for v in locked if v in ip]

print(f"message 臂：t0={t0:.0f}s，锁定 {len(locked)} 车 {locked}\n")

# ---- 1. 逐秒速度 vs 计划 cap ----
print("=== 1. 实际速度 vs 计划上限 ===")
print(f"{'t0后':>5} " + "".join(f"{v:>9}" for v in locked) + "   计划系数")
for t in (0, 6, 8, 9, 10, 11, 15, 20, 26, 28, 30, 35, 40):
    k = k0 + int(round(t / step))
    if k >= SO.shape[0]:
        break
    sp = [SO[k, ip[v]] for v in locked]
    f = planned_cap(t - MSG_START)
    ftxt = "—" if f is None else f"{f:.2f}"
    print(f"{t:>5} " + "".join(f"{s:>9.2f}" if np.isfinite(s) else f"{'--':>9}" for s in sp)
          + f"   {ftxt:>6}")

v_base = np.array([SO[k0 + int(round(MSG_START / step)), ip[v]] for v in locked])
print(f"\nt0+8 时基准速度：{np.round(v_base, 2)}")
print(f"计划 0.9 倍上限：{np.round(v_base * CAP_RATIO, 2)}")
k_hold = k0 + int(round(20.0 / step))
v_hold = np.array([SO[k_hold, ip[v]] for v in locked])
print(f"t0+20 实测速度：{np.round(v_hold, 2)}")
print(f"相对上限的比值（应≈1.00 表示被 cap 压住，>1 表示跟驰约束更松、实际跑得更快）：")
print(f"  {np.round(v_hold / (v_base * CAP_RATIO), 3)}")

# ---- 2. 相对速度积分 vs 净距变化 ----
print("\n=== 2. 净距变化 与 ∫(v前−v本)dt 对账 ===")


def gaps_and_lead(POS, SPD, k):
    row_p, row_v = POS[k], SPD[k]
    live = np.where(np.isfinite(row_p))[0]
    if len(live) < 2:
        return {}, {}
    order = live[np.argsort(row_p[live])]
    g, lv = {}, {}
    for j in range(len(order) - 1):
        me, lead = order[j], order[j + 1]
        g[me] = row_p[lead] - VEH_LEN - row_p[me]
        lv[me] = lead
    return g, lv


print(f"{'车':>5} {'净距@23':>9} {'净距@26':>9} {'Δ净距':>8} {'∫相对速度dt':>12} {'前车变过':>8}")
for v in locked:
    i = ip[v]
    g1, l1 = gaps_and_lead(PO, SO, k0 + int(round(23 / step)))
    g2, l2 = gaps_and_lead(PO, SO, k0 + int(round(26 / step)))
    if i not in g1 or i not in g2:
        print(f"{v:>5} {'无前车/驶离':>9}")
        continue
    k1 = k0 + int(round(23 / step))
    k2 = k0 + int(round(26 / step))
    integ = 0.0
    for k in range(k1, k2):
        gk, lk = gaps_and_lead(PO, SO, k)
        if i in gk and lk.get(i) is not None and lk[i] == l1[i]:
            integ += (SO[k, lk[i]] - SO[k, i]) * step
    changed = "是" if l1.get(i) != l2.get(i) else "否"
    print(f"{v:>5} {g1[i]:>9.2f} {g2[i]:>9.2f} {g2[i]-g1[i]:>8.2f} {integ:>12.2f} {changed:>8}")

print("\n判读：Δ净距 与 ∫相对速度dt 若相等（前车未变），说明数据自洽；")
print("      若某车 t0+20 的速度明显高于计划上限，说明跟驰安全约束比 cap 更强，限速没压住。")
