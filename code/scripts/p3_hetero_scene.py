"""P3 异质场景生成：车头距与目标速度从 NGSIM 实测分布抽样

阶段：P3（场景改造）
脚本：code/scripts/p3_hetero_scene.py
依赖：code/outputs/analysis/P3_scenario_check/ngsim_pool.npz（extract_ngsim_pool.py 产物）

设计原则（GPT 第三十八、三十九轮要求）：
  * 异质性必须来自实测分布，不能为了「让阈值不为零」去调参数
  * 抽样维度、速度层、样本量都要能写进论文
  * 所有随机都走固定种子，可复现

本脚本只做两件事：
  1. 从池子里抽一批 (车速, THW)，检查抽出来的分布是否还像真实分布
  2. 生成 SUMO 的 routes 片段，供 run_p3_hetero.py 使用
不跑仿真。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

POOL = Path("code/outputs/analysis/P3_scenario_check/ngsim_pool.npz")
OUT_DIR = Path("code/outputs/analysis/P3_hetero")


def load_pool() -> tuple[np.ndarray, np.ndarray]:
    d = np.load(POOL)
    return d["thw"].astype(np.float64), d["spd_mps"].astype(np.float64)


def sample_scene(thw: np.ndarray, spd: np.ndarray, n_veh: int,
                 seed: int, band: tuple[float, float] = (80.0, 105.0)):
    """从实测池里**成对**抽样（速度与 THW 一起抽，保留二者的经验相关性）。"""
    v_kmh = spd * 3.6
    mask = (v_kmh >= band[0]) & (v_kmh <= band[1])
    idx = np.where(mask)[0]
    if idx.size < n_veh:
        raise ValueError(f"带宽 {band} 内只有 {idx.size} 个样本，不够抽 {n_veh} 辆")
    rng = np.random.default_rng(seed)
    # 有放回抽样：池子样本量有限，无放回会让场景退化
    pick = rng.choice(idx, size=n_veh, replace=True)
    return spd[pick], thw[pick]


def build_layout(v_mps: np.ndarray, thw_s: np.ndarray,
                 x_start: float = 10.0) -> tuple[np.ndarray, np.ndarray]:
    """按抽到的 (速度, THW) 依次排布车辆位置。

    车头到车头间距 = v * THW，净距 = v*THW - 车长。
    逐辆向后累加（最前面那辆放在 x_start）。
    """
    headway_m = v_mps * thw_s
    pos = np.empty(v_mps.size)
    x = x_start
    for i in range(v_mps.size):
        pos[i] = x
        x += headway_m[i]
    return pos, headway_m


def describe(v_mps: np.ndarray, thw_s: np.ndarray, label: str) -> dict:
    return {
        "label": label,
        "n": int(v_mps.size),
        "spd_kmh": {
            "p10": round(float(np.percentile(v_mps * 3.6, 10)), 1),
            "p50": round(float(np.percentile(v_mps * 3.6, 50)), 1),
            "p90": round(float(np.percentile(v_mps * 3.6, 90)), 1),
            "std": round(float(np.std(v_mps * 3.6)), 2),
        },
        "thw_s": {
            "p10": round(float(np.percentile(thw_s, 10)), 2),
            "p25": round(float(np.percentile(thw_s, 25)), 2),
            "p50": round(float(np.percentile(thw_s, 50)), 2),
            "p90": round(float(np.percentile(thw_s, 90)), 2),
            "std": round(float(np.std(thw_s)), 3),
        },
    }


def main() -> int:
    thw_pool, spd_pool = load_pool()
    print(f"抽样池：{thw_pool.size} 对")
    v_kmh = spd_pool * 3.6
    print(f"车速 {v_kmh.min():.1f}–{v_kmh.max():.1f} km/h")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {"pool_size": int(thw_pool.size),
              "pool_speed_kmh_range": [round(float(v_kmh.min()), 1),
                                       round(float(v_kmh.max()), 1)],
              "scenes": []}

    # 抽样池自身在 80–105 km/h 层的描述（作为对照组）
    m = (v_kmh >= 80.0) & (v_kmh <= 105.0)
    report["pool_hi_band"] = describe(spd_pool[m], thw_pool[m], "池内 80–105 km/h")
    print("\n池内 80–105 km/h：", report["pool_hi_band"])

    # 抽三个种子，看抽出来的分布稳不稳
    for seed in (20261120, 20261121, 20261122):
        v, t = sample_scene(thw_pool, spd_pool, 400, seed)
        pos, hw = build_layout(v, t)
        d = describe(v, t, f"seed {seed} (400 辆)")
        d["span_m"] = round(float(pos[-1] - pos[0]), 1)
        d["headway_m_p50"] = round(float(np.median(hw)), 1)
        report["scenes"].append(d)
        print(f"\nseed {seed}: 车速 p50={d['spd_kmh']['p50']} km/h  "
              f"THW p50={d['thw_s']['p50']} s  车队长度 {d['span_m']} m")
        print(f"           THW p25={d['thw_s']['p25']} / p90={d['thw_s']['p90']}")

    (OUT_DIR / "sampling_check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwritten: {OUT_DIR / 'sampling_check.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())