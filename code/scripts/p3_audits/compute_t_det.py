"""P3-T_det：本地可用触发时刻（只用单车在线可见信号）

阶段：P3 ｜ 数据：code/outputs/analysis/P3_hw40_r06_ids/arms.npz（含车辆 ID）
脚本：code/scripts/p3_audits/compute_t_det.py
产物：code/outputs/analysis/P3_tdet/{calib.json,tdet.json}

为什么要这个：
  T_L 必须比较 plain 与 stop 两条轨迹才能算出来，**单次运行中的控制器拿不到它**。
  所以主对照（本地臂）不能用 T_L 当触发时钟。

T_det 定义（GPT 第三十七轮给的规则，原样实现）：
  仅凭本车**可见的最近同车道前车**，首次确认「前车持续减速」或「本车持续逼近」的采样时刻。

三条硬约束：
  1. 只在**每辆车自身的控制采样相位**取样（actionStepLength = 0.6 s），不用细步数据回填。
  2. 只读三个量：自车速度 v_e、与前车净距 g、闭合速度 c = v_e − v_p。
     不读源车状态、不读全路队列、不读事件起点、不读另一条轨迹。
  3. 量程 50 m（明确的仿真假设，不称真实雷达规格）。

阈值规则（不猜物理常数）：
  * 在**独立无事件标定回合**（plain 臂）上，算每对连续有效样本的
        a⁻ = max(0, (v_p,k-1 − v_p,k) / Δt)      前车减速度
        c⁺ = max(0, c_k)                          闭合速度
    取两者**较小值** m_k = min(a⁻, c⁺)。
  * 各分支阈值 θ = max_k m_k（标定集上的最大值），**严格大于**判越阈。
  * 同一分支连续两次有效采样严格越阈 → 在**第二次越阈的采样时刻**触发。
  * 换前车、丢观测、采样不连续 → 清掉连续计数。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

VEH_LEN = 5.0
GAP_EPS = 0.5
TARGET_X = 4000.0
BAND = 50.0
TTC_THR = 2.0
RANGE_M = 50.0          # 本地感知量程（仿真假设）
NEED_CONSEC = 2         # 连续越阈次数（GPT 规则：连续两次）


def leader_of(x: np.ndarray, ok: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """返回 (每辆车的最近前车 slot 索引, 净距)。无前车则 -1 / nan。"""
    n = x.size
    lead = np.full(n, -1, dtype=np.int64)
    gap = np.full(n, np.nan)
    if ok.sum() < 2:
        return lead, gap
    idxs = np.where(ok)[0]
    order = idxs[np.argsort(x[idxs])]
    for a, b in zip(order[:-1], order[1:]):
        lead[a] = b
        gap[a] = (x[b] - x[a]) - VEH_LEN
    return lead, gap


def sample_frames(t0: float, step: float, n_steps: int, react_s: float) -> list[int]:
    """按控制采样相位取帧：每 react_s 秒一帧。react_s<=0 时退回每步。"""
    if react_s <= 0:
        return list(range(n_steps))
    period = max(1, int(round(react_s / step)))
    k0 = int(round(t0 / step))
    return list(range(k0, n_steps, period))


def build_samples(pos, spd, t0, step, react_s):
    """生成每辆车的本地观测序列：{slot: [(t, ve, gap, vp, lead_slot)]}"""
    n_steps = pos.shape[0]
    frames = sample_frames(t0, step, n_steps, react_s)
    out: dict[int, list] = {}
    for k in frames:
        x = pos[k].astype(np.float64)
        v = spd[k].astype(np.float64)
        ok = np.isfinite(x) & np.isfinite(v)
        if ok.sum() < 1:
            continue
        lead, gap = leader_of(x, ok)
        t = k * step
        for i in np.where(ok)[0]:
            j = lead[i]
            if j < 0:
                continue
            g = gap[i]
            if not np.isfinite(g) or g > RANGE_M or g <= GAP_EPS:
                continue        # 超出量程或无有效前车 -> 该帧无观测
            c = v[i] - v[j]     # 闭合速度，逼近为正
            out.setdefault(int(i), []).append((t, float(v[i]), float(g), float(v[j]), int(j)))
    return out


def calibrate(samples: dict[int, list], step: float, react_s: float) -> dict:
    """在无事件回合上标定 θ_a 与 θ_c（用 min(a⁻, c⁺) 的最大值）。"""
    dt = react_s if react_s > 0 else step
    mvals = []
    per_slot = {}
    for slot, seq in samples.items():
        mmax = 0.0
        for (t0_, ve0, g0, vp0, l0), (t1_, ve1, g1, vp1, l1) in zip(seq[:-1], seq[1:]):
            if l0 != l1:
                continue
            if abs((t1_ - t0_) - dt) > 1e-6:
                continue
            a_minus = max(0.0, (vp0 - vp1) / dt)
            c_plus = max(0.0, ve1 - vp1)
            m = min(a_minus, c_plus)
            if m > mmax:
                mmax = m
        per_slot[slot] = mmax
        mvals.append(mmax)
    if not mvals:
        return {"theta": 0.0, "n_slots": 0}
    arr = np.array(mvals)
    return {
        "theta": float(arr.max()),
        "theta_a": float(arr.max()),
        "theta_c": float(arr.max()),
        "n_slots": int(arr.size),
        "p50": float(np.percentile(arr, 50)),
        "p99": float(np.percentile(arr, 99)),
        "note": "标定集内不因单次尖峰触发；不保证留出集零误报",
    }


def detect(samples: dict[int, list], theta: float, step: float, react_s: float) -> dict:
    """同一分支连续 NEED_CONSEC 次严格越阈，在第 N 次的采样时刻触发。"""
    dt = react_s if react_s > 0 else step
    res = {}
    for slot, seq in samples.items():
        hit = None
        run_a = 0
        run_c = 0
        prev = None
        for cur in seq:
            t1, ve1, g1, vp1, l1 = cur
            if prev is None:
                prev = cur
                continue
            t0_, ve0, g0, vp0, l0 = prev
            if l0 != l1 or abs((t1 - t0_) - dt) > 1e-6:
                run_a = run_c = 0          # 换前车 / 采样不连续 -> 清零
                prev = cur
                continue
            a_minus = max(0.0, (vp0 - vp1) / dt)
            c_plus = max(0.0, ve1 - vp1)
            run_a = run_a + 1 if a_minus > theta else 0
            run_c = run_c + 1 if c_plus > theta else 0
            if hit is None and (run_a >= NEED_CONSEC or run_c >= NEED_CONSEC):
                hit = t1
            prev = cur
        res[slot] = hit
    return res


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1
               else "code/outputs/analysis/P3_hw40_r06_ids/arms.npz")
    d = np.load(src, allow_pickle=False)
    t0 = float(d["event_t0"])
    step = float(d["step_s"])
    react = float(d["react_s"]) if "react_s" in d.files else 0.6

    print(f"源: {src}")
    print(f"事件 t0={t0}s  步长={step}s  反应/动作间隔={react}s  量程={RANGE_M}m")

    out = {"source": str(src), "event_t0_s": t0, "step_s": step,
           "react_s": react, "range_m": RANGE_M}

    # ---- 1) 用 plain 臂（无事件）标定 ----
    plain_samples = build_samples(d["plain_pos"], d["plain_spd"], t0, step, react)
    calib = calibrate(plain_samples, step, react)
    out["calibration"] = calib
    print(f"\n标定（plain 臂，{calib['n_slots']} 辆车有观测）：")
    print(f"  θ = {calib['theta']:.4f}   p50={calib.get('p50',0):.4f}  p99={calib.get('p99',0):.4f}")

    # ---- 2) 在 stop 臂上求 T_det ----
    stop_samples = build_samples(d["stop_pos"], d["stop_spd"], t0, step, react)
    tdet = detect(stop_samples, calib["theta"], step, react)
    stop_ids = [str(x) for x in d["stop_ids"]]
    tdet_named = {stop_ids[k]: v for k, v in tdet.items() if v is not None}
    out["tdet"] = {
        "n_with_obs": len(stop_samples),
        "n_detected": len(tdet_named),
        "examples": [{"vehicle": k, "t_det_s": round(v - t0, 2)}
                     for k, v in sorted(tdet_named.items(), key=lambda kv: kv[1])[:15]],
    }
    print(f"\nstop 臂：{len(stop_samples)} 辆车有本地观测，{len(tdet_named)} 辆触发")
    for e in out["tdet"]["examples"][:8]:
        print(f"  {e['vehicle']:>10}  T_det = t0+{e['t_det_s']:.2f} s")

    # ---- 3) 误报检查：同一阈值跑 plain 臂，理论上应尽量少触发 ----
    plain_det = detect(plain_samples, calib["theta"], step, react)
    n_fp = sum(1 for v in plain_det.values() if v is not None)
    out["false_positive"] = {
        "n_with_obs": len(plain_samples),
        "n_triggered": n_fp,
        "rate": round(n_fp / max(len(plain_samples), 1), 4),
        "note": "标定集与检查集相同，这是乐观估计；真正留出集须另跑",
    }
    print(f"\n误报检查（同一 plain 臂）：{len(plain_samples)} 辆有观测，"
          f"{n_fp} 辆触发（{out['false_positive']['rate']:.1%}）")
    print("  ⚠️ 标定集与检查集相同，这是乐观估计")

    dst = Path("code/outputs/analysis/P3_tdet")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "tdet.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwritten: {dst / 'tdet.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())