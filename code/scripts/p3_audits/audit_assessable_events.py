"""可评分事件与独立块清点（按原协议 + 修订口径两套）

阶段：P3-B（可行性审计 · 决定主分析能否成立）
GPT 第五轮要求：现在就审计，不等 S/L 结果。

两套口径都算，分开报：
  A. 原协议口径：事件要求 20 s 全程可判直跟（沿用此前回放的前置要求）
  B. 修订口径：只要求「报警机会区间」内前车可识别、特征可算
     —— 资格由可观测性决定，不由模型是否报警决定

输出：各口径的可评分事件数、独立块数、样本流失原因。
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
OUT = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P3B_audit")
OUT.mkdir(parents=True, exist_ok=True)

DT = 0.04
LAT0, LON0 = 37.9777, 23.7375

# 标签参数（协议冻结）
LAB_W = 0.48            # 居中回归窗
LAB_K = int(round(LAB_W / DT))      # 12 → 13 样本
D_LOW = 0.30            # 持续减速低阈值
D_MAIN = 1.00           # 主事件门槛
MIN_DUR = 0.50          # 最短持续
MIN_FRAMES = int(math.ceil(MIN_DUR / DT)) + 1   # 首末差 >=0.50s → 14 帧（GPT 第七轮定）

# 报警机会
T_MIN_LEAD = 1.0        # 最短有效提前量
T_MAX_LEAD = 3.0        # 最远有效预警时间
LOOKBACK = 0.48         # 因果回看窗
LOOK_K = int(round(LOOKBACK / DT))
LEAD_MAX_DIST = 60.0    # 前车搜索半径
LANE_HALF_W = 2.0       # 同车道横向容差
GRID = 0.2              # 报警机会采样步长


def load():
    cars = []
    with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
        rd = csv.reader(f, delimiter=";")
        next(rd)
        for r in rd:
            if len(r) < 16:
                continue
            try:
                vals = np.array([float(x) for x in r[4:] if x.strip() != ""])
            except ValueError:
                continue
            n = len(vals) // 6
            if n < 4 * LAB_K + 10:
                continue
            v = vals[: n * 6].reshape(n, 6)
            cars.append({
                "id": r[0].strip(),
                "type": r[1].strip(),
                "x": (v[:, 1] - LON0) * 111320.0 * math.cos(math.radians(LAT0)),
                "y": (v[:, 0] - LAT0) * 110540.0,
                "speed": v[:, 2] / 3.6,      # 仅用于标签
                "t": v[:, 5],
            })
    return cars


def centered_slope(t, s, k):
    """居中回归斜率，返回 -斜率 = 减速度。窗口不完整处为 nan。"""
    n = len(s)
    d = np.full(n, np.nan)
    if n < 2 * k + 1:
        return d
    # 用滑动求和公式加速：斜率 = cov(t,s)/var(t)，窗口等间隔时 var 为常数
    tw = t[k:n - k]
    idx = np.arange(-k, k + 1)
    ssum = np.zeros(n - 2 * k)
    tssum = 0.0
    for j, off in enumerate(idx):
        ssum += s[k + off: n - k + off]
    mean_s = ssum / (2 * k + 1)
    tbar = tw  # 等间隔，窗口中心即 tw
    num = np.zeros(n - 2 * k)
    for j, off in enumerate(idx):
        num += (t[k + off: n - k + off] - tbar) * (s[k + off: n - k + off] - mean_s)
    den = np.sum((np.arange(-k, k + 1) * DT) ** 2)
    d[k:n - k] = -(num / den)
    return d


def find_events(car):
    """按协议定义找事件：d>=D_LOW 的连续区间，时长>=MIN_DUR，且含 d>=D_MAIN。"""
    d = centered_slope(car["t"], car["speed"], LAB_K)
    ok = d >= D_LOW
    ev = []
    n = len(d)
    i = 0
    while i < n:
        if not ok[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and ok[j + 1]:
            j += 1
        if (j - i + 1) >= MIN_FRAMES and np.nanmax(d[i:j + 1]) >= D_MAIN:
            ev.append({
                "start_idx": i,
                "end_idx": j,
                "start_t": float(car["t"][i]),
                "dur": float(car["t"][j] - car["t"][i]),
                "dmax": float(np.nanmax(d[i:j + 1])),
            })
        i = j + 1
    return ev, d


def main():
    cars = load()
    print(f"载入轨迹（≥{4*LAB_K+10} 帧）：{len(cars)}")

    # ---- 事件检出 ----
    all_ev = []
    for ci, c in enumerate(cars):
        ev, _ = find_events(c)
        for e in ev:
            e["car_idx"] = ci
            e["car_id"] = c["id"]
            all_ev.append(e)
    print(f"检出事件（d≥{D_MAIN}，持续≥{MIN_DUR}s）：{len(all_ev)}")

    # ---- 帧索引（用于找前车）----
    # 全局时间轴，按 GRID 采样
    t_all = np.concatenate([c["t"] for c in cars])
    t_min, t_max = float(t_all.min()), float(t_all.max())
    n_grid = int((t_max - t_min) / GRID) + 1
    print(f"全局时间轴 {t_min:.1f}–{t_max:.1f} s，网格 {n_grid} 帧")

    # 每辆车在自己帧上的网格位置（取最近）
    for c in cars:
        c["gidx"] = np.round((c["t"] - t_min) / GRID).astype(int)

    frame_buckets = {}
    for ci, c in enumerate(cars):
        for fi in c["gidx"]:
            frame_buckets.setdefault(int(fi), []).append(ci)

    print(f"非空网格帧：{len(frame_buckets)}")

    # ---- 报警机会评估 ----
    def lead_at(ci, fi):
        """在网格帧 fi 上找 ci 的前车；返回 (前车idx, 距离) 或 None。"""
        c = cars[ci]
        # 该车在 fi 附近有观测吗
        k = np.searchsorted(c["gidx"], fi)
        for cand in (k - 1, k, k + 1):
            if 0 <= cand < len(c["gidx"]) and abs(int(c["gidx"][cand]) - fi) <= 1:
                pos = cand
                break
        else:
            return None
        # 因果朝向：用后向位移
        p0 = max(0, pos - LOOK_K)
        if pos - p0 < 2:
            return None
        hx = c["x"][pos] - c["x"][p0]
        hy = c["y"][pos] - c["y"][p0]
        norm = math.hypot(hx, hy)
        if norm < 0.3:          # 近静止，朝向不可判
            return None
        hx, hy = hx / norm, hy / norm

        best = None
        for cj in frame_buckets.get(fi, []):
            if cj == ci:
                continue
            o = cars[cj]
            kj = np.searchsorted(o["gidx"], fi)
            for cand in (kj - 1, kj, kj + 1):
                if 0 <= cand < len(o["gidx"]) and abs(int(o["gidx"][cand]) - fi) <= 1:
                    pj = cand
                    break
            else:
                continue
            dx = o["x"][pj] - c["x"][pos]
            dy = o["y"][pj] - c["y"][pos]
            along = dx * hx + dy * hy
            if along <= 0 or along > LEAD_MAX_DIST:
                continue
            lat = abs(-dx * hy + dy * hx)
            if lat > LANE_HALF_W:
                continue
            if best is None or along < best[1]:
                best = (cj, along)
        return best

    def has_opportunity(ev):
        """报警机会：[t0-3, t0-1] 内是否存在前车可识别且回看窗可算的时刻。"""
        c = cars[ev["car_idx"]]
        t0 = ev["start_t"]
        t_lo, t_hi = t0 - T_MAX_LEAD, t0 - T_MIN_LEAD
        if t_lo < c["t"][0] + LOOKBACK:
            return False, "历史窗不足"
        # 该车在 [t_lo, t_hi] 内的网格帧
        f_lo = int(round((t_lo - t_min) / GRID))
        f_hi = int(round((t_hi - t_min) / GRID))
        for fi in range(f_lo, f_hi + 1):
            r = lead_at(ev["car_idx"], fi)
            if r is not None:
                # 前车回看窗是否也在观测内
                cj = r[0]
                o = cars[cj]
                kj = np.searchsorted(o["gidx"], fi)
                if kj - LOOK_K >= 0:
                    return True, "ok"
        return False, "报警机会内无可用前车"

    n_ok = 0
    reasons = {}
    ok_events = []
    for ev in all_ev:
        ok, why = has_opportunity(ev)
        if ok:
            n_ok += 1
            ok_events.append(ev)
        reasons[why] = reasons.get(why, 0) + 1

    print("\n" + "=" * 68)
    print("B. 修订口径（报警机会内可评估）")
    print("=" * 68)
    print(f"  检出事件：{len(all_ev)}")
    print(f"  可评分事件：{n_ok}")
    print(f"  流失原因：{reasons}")

    # ---- 独立块（按 30 s 时间块粗算）----
    BLOCK = 30.0
    blocks = set()
    for e in ok_events:
        blocks.add(int((e["start_t"] - t_min) // BLOCK))
    print(f"\n  按 {BLOCK:.0f} s 时间块：独立块数 {len(blocks)}")
    if blocks:
        from collections import Counter
        cc = Counter(int((e["start_t"] - t_min) // BLOCK) for e in ok_events)
        top = cc.most_common(1)[0]
        print(f"  最大块含 {top[1]} 个事件（占 {100*top[1]/len(ok_events):.1f}%）")

    # ---- 事件按车辆分布 ----
    car_cnt = {}
    for e in ok_events:
        car_cnt[e["car_id"]] = car_cnt.get(e["car_id"], 0) + 1
    print(f"  涉及车辆数：{len(car_cnt)}，单车最多 {max(car_cnt.values()) if car_cnt else 0} 个事件")

    # ---- 判据 ----
    print("\n" + "=" * 68)
    print("协议继续条件核对（条件二：样本量）")
    print("=" * 68)
    print(f"  可评分主事件 ≥100 ：{n_ok} → {'通过' if n_ok >= 100 else '未通过'}")
    print(f"  独立分析块 ≥30    ：{len(blocks)} → {'通过' if len(blocks) >= 30 else '未通过'}")
    print(f"  单块占比 ≤20%     ：{100*top[1]/len(ok_events) if ok_events else 0:.1f}% → "
          f"{'通过' if ok_events and top[1]/len(ok_events) <= 0.2 else '未通过'}")
    print(f"  （无目标事件的可评分车辆小时 ≥20：待算，需先定报警器）")

    json.dump({"n_events": len(all_ev), "n_ok": n_ok, "reasons": reasons,
               "n_blocks": len(blocks),
               "events": [{k: v for k, v in e.items()} for e in ok_events[:50]]},
              (OUT / "assessable_events.json").open("w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=str)
    print(f"\n已保存 {OUT/'assessable_events.json'}")


if __name__ == "__main__":
    main()
