"""P3 异质场景跑批：车头距与速度从 NGSIM 实测分布成对抽样

阶段：P3（场景改造，GPT 第三十九轮方案）
脚本：code/scripts/run_p3_hetero.py
产物：code/outputs/analysis/P3_hetero_<tag>/arms.npz + meta.json

设计（严格照 GPT 第三十九轮 Q1/Q3/Q6）：
  * (车速, THW) **成对**从 80–105 km/h 实测层抽，不分别抽两个边际
  * THW 用**车头到车头**口径，与 NGSIM 官方 Time_Headway 一致
  * Krauss sigma = 0，**不加额外驾驶噪声**；异质性只来自实测初始化
  * **不写 speedDev，也不写 speedFactor="1"**（旧脚本写死 speedFactor=1 使 speedDev 失效）
  * 动作间隔 actionStepLength = 0.6 s 保持不变
  * 预先填满整条路 + 入口按实测时距续车

当前版本只跑 plain 臂（无源事件），用于 GPT Q6 第 3 步的「8–10 个种子查实现」。
源事件臂等实现审计通过后再加。
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

traci = load_traci()
SUMO = str(Path(r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"))

EDGE_LEN = 8000.0      # 源车 6000、目标区 4000，上游留 4 km 足够
VEH_LEN = 5.0
MAX_SPEED = 30.0
STEP = 0.05
REACT = 0.6
WARMUP = 420.0         # 入口流入填满 6.5 km 需约 280 s，留足余量
OBS = 300.0
POOL = Path("code/outputs/analysis/P3_scenario_check/ngsim_pool.npz")
BAND = (80.0, 105.0)


def load_scene(seed: int) -> tuple[np.ndarray, np.ndarray]:
    """成对抽 (v_mps, thw_s)，返回按发车顺序排好的数组。

    过滤条件：车头到车头间距必须 ≥ 车身 + 最小净距，否则两车重叠、SUMO 插不进去。
    这不是「剪尾部」，是剔除物理上不可能的记录（NGSIM 里有少量错误配对/极近距离记录）。
    """
    d = np.load(POOL)
    thw = d["thw"].astype(np.float64)
    spd = d["spd_mps"].astype(np.float64)
    v_kmh = spd * 3.6
    headway_m = spd * thw
    ok = ((v_kmh >= BAND[0]) & (v_kmh <= BAND[1])
          & (headway_m >= VEH_LEN + 2.5 + 0.5))     # 至少留 0.5 m 余量
    idx = np.where(ok)[0]
    if idx.size == 0:
        raise SystemExit("抽样池里没有目标速度层的可行样本")
    rng = np.random.default_rng(seed)
    pick = rng.choice(idx, size=idx.size, replace=True)
    return spd[pick], thw[pick]


def build_population(v: np.ndarray, h: np.ndarray):
    """只从入口流入，不预填。

    为什么不用预填：实测 SUMO 在中途用显式 departPos 插入异质车流时大量失败
    （后车比前车快、间距不足即被拒），20 辆同速对照全进、异质场景进不到一半。
    入口流入是交通仿真的标准做法，插入由 SUMO 自行按安全条件排队，不会丢车。

    进入时刻按实测 THW 累加；每辆车的期望速度由 speedFactor 表达。
    """
    dep_t, spd = [], []
    t = 0.0
    total = WARMUP + OBS
    for vi, hi in zip(v, h):
        t += hi
        if t > total:
            break
        dep_t.append(t)
        spd.append(vi)
    return np.zeros(len(dep_t)) + 0.1, np.array(dep_t), np.array(spd)


def net_xml() -> str:
    return f"""<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50">
    <edge id="cor" from="a" to="b" priority="1" numLanes="1" speed="{LANE_SPEED:.2f}" length="{EDGE_LEN}">
        <lane id="cor_0" index="0" speed="{LANE_SPEED:.2f}" length="{EDGE_LEN}" shape="0.00,0.00 {EDGE_LEN:.2f},0.00"/>
    </edge>
    <junction id="a" type="dead_end" x="0.00" y="0.00"/>
    <junction id="b" type="dead_end" x="{EDGE_LEN:.2f}" y="0.00"/>
</net>"""


LANE_SPEED = 40.0        # 车道限速放宽到 40，让 speedFactor 能表达 80–105 km/h 的期望速度


def routes_xml(pos, dep_t, spd) -> str:
    # 异质性只来自实测：逐车给 speedFactor 表达期望速度。
    # 不写全局 speedDev（GPT 第三十九轮 Q1：只保留一套异质性来源）。
    # departSpeed 必须用显式速度：实测 departSpeed="max" 与显式 departPos 同用会大量插入失败
    # （20 辆同规模对照：max 只插入 5，显式速度插入 20）。
    vt = (f'<vType id="cal" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          f' tau="{REACT}" length="{VEH_LEN}" minGap="2.5" maxSpeed="{LANE_SPEED}"'
          f' actionStepLength="{REACT}"/>')
    vehs = []
    for i, (p, t, s) in enumerate(zip(pos, dep_t, spd)):
        sf = min(max(s / LANE_SPEED, 0.1), 1.0)
        vehs.append(f'<vehicle id="V{i:05d}" type="cal" route="rc" depart="{t:.2f}"'
                    f' departPos="{p:.2f}" departSpeed="{s:.3f}" departLane="0"'
                    f' speedFactor="{sf:.4f}"/>')
    return (f'<routes>{vt}<route id="rc" edges="cor"/>{"".join(vehs)}</routes>')


def run_plain(tmp: Path, seed: int, tag: str) -> dict:
    v, h = load_scene(seed)
    pos, dep_t, spd = build_population(v, h)
    (tmp / "net.net.xml").write_text(net_xml(), encoding="utf-8")
    (tmp / "routes.rou.xml").write_text(routes_xml(pos, dep_t, spd), encoding="utf-8")
    (tmp / "sumo.cfg").write_text(
        f"""<configuration>
  <input><net-file value="net.net.xml"/><route-files value="routes.rou.xml"/></input>
  <time><begin value="0"/><end value="{WARMUP + OBS:.1f}"/><step-length value="{STEP}"/></time>
  <processing><time-to-teleport value="-1"/></processing>
  <random_number><seed value="{seed}"/></random_number>
  <report><no-step-log value="true"/><duration-log.statistics value="true"/></report>
</configuration>""", encoding="utf-8")

    cmd = [SUMO, "-c", str(tmp / "sumo.cfg"), "--no-warnings"]
    n_steps = int(round((WARMUP + OBS) / STEP))
    spd_arr = np.full((n_steps, 3000), np.nan, dtype=np.float32)
    pos_arr = np.full((n_steps, 3000), np.nan, dtype=np.float32)
    n_veh = len(pos)
    traci.start(cmd)
    try:
        k = 0
        while traci.simulation.getTime() < WARMUP + OBS:
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            for vid in ids:
                try:
                    i = int(vid[1:])
                except (ValueError, IndexError):
                    continue
                # 全局普查：不能只记前 n_veh 辆，否则入口续车全丢
                if i >= spd_arr.shape[1]:
                    continue
                spd_arr[k, i] = traci.vehicle.getSpeed(vid)
                pos_arr[k, i] = traci.vehicle.getPosition(vid)[0]
            k += 1
            if k >= n_steps:
                break
    finally:
        traci.close()

    # 只保留在观测窗内的车
    fin = np.isfinite(spd_arr).any(axis=0)
    spd_arr = spd_arr[:, fin]
    pos_arr = pos_arr[:, fin]
    return {"tag": tag, "seed": seed, "n_veh": int(fin.sum()), "spd": spd_arr,
            "pos": pos_arr, "warmup": WARMUP, "obs": OBS, "react": REACT}


def summarize(r: dict) -> dict:
    sp = r["spd"]
    warm = int(round(r["warmup"] / STEP))
    after = sp[warm:, :]
    vals = after[np.isfinite(after)]
    if vals.size == 0:
        return {"tag": r["tag"], "seed": r["seed"], "error": "观测窗内无数据"}
    per_veh_std = np.array([np.nanstd(after[:, j]) for j in range(after.shape[1])
                            if np.isfinite(after[:, j]).sum() > 20])
    return {
        "tag": r["tag"], "seed": r["seed"], "n_veh": r["n_veh"],
        "speed_kmh": {
            "p10": round(float(np.percentile(vals, 10)) * 3.6, 1),
            "p50": round(float(np.percentile(vals, 50)) * 3.6, 1),
            "p90": round(float(np.percentile(vals, 90)) * 3.6, 1),
            "std": round(float(np.std(vals)) * 3.6, 2),
        },
        "per_veh_std_kmh_median": round(float(np.median(per_veh_std)) * 3.6, 2) if per_veh_std.size else None,
        "n_zero_std_veh": int((per_veh_std < 1e-6).sum()) if per_veh_std.size else None,
        "frac_zero_std": round(float((per_veh_std < 1e-6).mean()), 3) if per_veh_std.size else None,
    }


def main() -> int:
    seeds = [int(s) for s in sys.argv[1:]] or [20261120, 20261121, 20261122]
    out_root = Path("code/outputs/analysis")
    results = []
    for seed in seeds:
        tag = f"P3_hetero_{seed}"
        dst = out_root / tag
        dst.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix=f"sumo_{seed}_"))
        try:
            print(f"[{seed}] 跑 plain 臂 …", flush=True)
            r = run_plain(tmp, seed, tag)
            np.savez_compressed(dst / "arms.npz", plain_spd=r["spd"],
                                plain_pos=r["pos"],
                                step_s=np.float32(STEP), react_s=np.float32(REACT),
                                warmup_s=np.float32(WARMUP))
            s = summarize(r)
            results.append(s)
            (dst / "meta.json").write_text(
                json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"[{seed}] 车辆 {s.get('n_veh')}  "
                  f"车速 p50={s.get('speed_kmh', {}).get('p50')} km/h  "
                  f"零方差车占比 {s.get('frac_zero_std')}", flush=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    (out_root / "P3_hetero_summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n汇总：")
    for s in results:
        print(f"  seed {s['seed']}: n={s.get('n_veh')} "
              f"p50={s.get('speed_kmh', {}).get('p50')} km/h "
              f"零方差占比={s.get('frac_zero_std')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())