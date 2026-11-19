"""P3 路线乙 · 第一步：无臂并道瓶颈，看能不能长出会移动的队尾

阶段：P3 ｜ GPT 第四十三/四十四轮拍板的动作顺序第 1 步
脚本：code/scripts/run_p3_bottleneck.py
产物：code/outputs/analysis/P3_bottleneck_<tag>/{queue_profile.json, flows.json, meta.json}

设计（严格照 GPT 给的工程初值）：
  * 路网 10 km，起点坐标递增，约 8 km 处由**两车道并为一车道**（无信号）
  * 需求：1400 辆/h 热身 15 min → 2100 辆/h 运行 25 min → 回落 1400 辆/h 运行 25 min
  * 车型 90% 小客车 / 10% 重车
  * 小客车期望速度以 85 km/h 为中心、截断 80–95；重车 70–85
  * 观测走廊：并道点上游 1–8 km
  * 跟驰用 SUMO 默认 Krauss，**不做任何改造**

验收（GPT 定的，不是看有没有撞车）：
  1. 队列形成
  2. 队尾向上游移动（位置随时间单调后退）
  3. 降流后消散
  4. 上游入口没有被回溢卡住
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

traci = load_traci()
SUMO = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"

LEN_A = 8000.0          # 两车道段
LEN_B = 2000.0          # 单车道段
MERGE_X = LEN_A
STEP = 0.2              # 交通层面用 0.2 s 够用，跑得快
WARM = 900.0            # 15 min
PEAK = 1500.0           # 25 min
COOL = 1500.0           # 25 min
RATE_WARM = 1400.0      # 辆/小时
RATE_PEAK = 3200.0   # = 1.28 × 实测瓶颈容量(约2500辆/h)，按预写规则设定
RATE_COOL = 1400.0
OBS_LO, OBS_HI = 1000.0, 8000.0     # 观测走廊（并道点上游 1–8 km）


def build_net(tmp: Path) -> None:
    """用 netconvert 从节点与边生成路网，避免手写 connection 出错。"""
    nodes = f"""<nodes>
  <node id="a" x="0.00" y="0.00" type="priority"/>
  <node id="m" x="{LEN_A:.2f}" y="0.00" type="priority"/>
  <node id="b" x="{LEN_A + LEN_B:.2f}" y="0.00" type="priority"/>
</nodes>"""
    edges = f"""<edges>
  <edge id="up" from="a" to="m" priority="1" numLanes="2" speed="27.78"/>
  <edge id="down" from="m" to="b" priority="1" numLanes="1" speed="27.78"/>
</edges>"""
    (tmp / "n.nod.xml").write_text(nodes, encoding="utf-8")
    (tmp / "e.edg.xml").write_text(edges, encoding="utf-8")
    netconvert = str(Path(SUMO).parent / "netconvert.exe")
    r = subprocess.run([netconvert, "-n", str(tmp / "n.nod.xml"),
                        "-e", str(tmp / "e.edg.xml"),
                        "-o", str(tmp / "net.net.xml"),
                        "--no-turnarounds", "true",
                        "--junctions.corner-detail", "0"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"netconvert 失败:\n{r.stderr[:2000]}")


def routes_xml() -> str:
    car = ('<vType id="car" vClass="passenger" length="5" minGap="2.5" maxSpeed="26.39"'
           ' accel="2.6" decel="4.5" sigma="0" tau="1.1" speedFactor="normc(1,0.06,0.94,1.12)"/>')
    hv = ('<vType id="hv" vClass="truck" length="12" minGap="2.5" maxSpeed="23.61"'
          ' accel="1.3" decel="3.5" sigma="0" tau="1.4" speedFactor="normc(1,0.05,0.90,1.08)"/>')
    t1, t2 = WARM, WARM + PEAK
    t3 = t2 + COOL
    parts = [car, hv, '<route id="r" edges="up down"/>']
    # 小客车承担 90% 需求，重车承担 10%（周期 ×9）
    for tag, b, e, r in (("w", 0.0, t1, RATE_WARM), ("p", t1, t2, RATE_PEAK),
                         ("c", t2, t3, RATE_COOL)):
        parts.append(f'<flow id="c_{tag}" type="car" route="r" begin="{b:.1f}" end="{e:.1f}"'
                     f' period="{3600.0/(r*0.9):.3f}" departLane="random" departSpeed="max"/>')
        parts.append(f'<flow id="h_{tag}" type="hv" route="r" begin="{b:.1f}" end="{e:.1f}"'
                     f' period="{3600.0/(r*0.1):.3f}" departLane="random" departSpeed="max"/>')
    return "<routes>" + "".join(parts) + "</routes>"


def run(tag: str, seed: int = 20261120) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="bn_"))
    total = WARM + PEAK + COOL
    try:
        build_net(tmp)
        (tmp / "r.rou.xml").write_text(routes_xml(), encoding="utf-8")
        (tmp / "c.cfg").write_text(
            f"""<configuration>
  <input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>
  <time><begin value="0"/><end value="{total:.1f}"/><step-length value="{STEP}"/></time>
  <processing><time-to-teleport value="300"/></processing>
  <random_number><seed value="{seed}"/></random_number>
  <report><no-step-log value="true"/></report></configuration>""", encoding="utf-8")

        traci.start([SUMO, "-c", str(tmp / "c.cfg"), "--no-warnings"])
        rec_every = 10.0            # 每 10 s 记一次
        prof = []                   # (t, 队尾位置, 队内车辆数, 走廊内平均速度, 上游速度)
        next_rec = 0.0
        arrived_cum = 0
        while traci.simulation.getTime() < total:
            t = traci.simulation.getTime()
            if t >= next_rec:
                xs, vs = [], []
                for vid in traci.vehicle.getIDList():
                    p = traci.vehicle.getPosition(vid)
                    xs.append(p[0]); vs.append(traci.vehicle.getSpeed(vid))
                xs = np.array(xs); vs = np.array(vs)
                if xs.size:
                    m = (xs >= OBS_LO) & (xs <= OBS_HI)
                    if m.sum() > 5:
                        xs_o, vs_o = xs[m], vs[m]
                        # 队尾位置：从并道点往上游扫，找第一辆速度 < 2 m/s 的车
                        slow = xs_o[(vs_o < 2.0)]
                        tail = float(slow.min()) if slow.size else float("nan")
                        v_mean = float(vs_o.mean())
                        n_in = int(xs_o.size)
                        # 上游 1–2 km 段的平均速度（判断回溢）
                        up_m = (xs_o >= OBS_LO) & (xs_o <= OBS_LO + 1000)
                        v_up = float(vs_o[up_m].mean()) if up_m.sum() > 2 else float("nan")
                    else:
                        tail, v_mean, n_in, v_up = float("nan"), float("nan"), int(xs.size), float("nan")
                else:
                    tail, v_mean, n_in, v_up = float("nan"), float("nan"), 0, float("nan")
                prof.append({"t": round(t, 1), "queue_tail_x": round(tail, 1),
                             "n_in_corridor": n_in,
                             "v_mean_mps": round(v_mean, 2) if v_mean == v_mean else None,
                             "v_upstream_mps": round(v_up, 2) if v_up == v_up else None,
                             "n_running": len(xs)})
                next_rec += rec_every
            arrived_cum += traci.simulation.getArrivedNumber()
            traci.simulationStep()
        inserted_total = arrived_cum
    finally:
        traci.close()
        shutil.rmtree(tmp, ignore_errors=True)

    dst = Path(f"code/outputs/analysis/P3_bottleneck_{tag}")
    dst.mkdir(parents=True, exist_ok=True)
    meta = {"tag": tag, "seed": seed, "len_upstream_m": LEN_A, "len_downstream_m": LEN_B,
            "merge_x": MERGE_X, "warm_s": WARM, "peak_s": PEAK, "cool_s": COOL,
            "rate_warm_vph": RATE_WARM, "rate_peak_vph": RATE_PEAK, "rate_cool_vph": RATE_COOL,
            "step_s": STEP, "tau_car": 1.1, "tau_hv": 1.4, "arrived_total": inserted_total}
    (dst / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    (dst / "queue_profile.json").write_text(
        json.dumps(prof, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"meta": meta, "profile": prof, "path": str(dst)}


def summarise(r: dict) -> dict:
    prof = [p for p in r["profile"] if p["queue_tail_x"] == p["queue_tail_x"]]
    if not prof:
        return {"verdict": "没有出现任何停驶车辆（队列未形成）"}
    first = prof[0]; last = prof[-1]
    tails = [p["queue_tail_x"] for p in prof]
    print(f"  记录点 {len(r['profile'])}，其中有停驶车的 {len(prof)}")
    print(f"  首次出现停驶车：t={first['t']}s，队尾 x={first['queue_tail_x']} m")
    print(f"  最远队尾：x={min(tails)} m（并道点在 {MERGE_X:.0f} m，"
          f"即向上游延伸 {MERGE_X-min(tails):.0f} m）")
    # 峰段结束与降流后
    t_peak_end = WARM + PEAK
    after = [p for p in prof if p["t"] > t_peak_end + 300]
    print(f"  降流 5 min 后仍有停驶车：{'是' if after else '否'}")
    return {"first_tail_t": first["t"], "first_tail_x": first["queue_tail_x"],
            "min_tail_x": min(tails), "propagation_m": MERGE_X - min(tails),
            "still_queued_after_cool_5min": bool(after)}


def main() -> int:
    print(f"两车道 {LEN_A:.0f} m + 单车道 {LEN_B:.0f} m，并道点 x={MERGE_X:.0f}")
    print(f"需求 {RATE_WARM:.0f} → {RATE_PEAK:.0f} → {RATE_COOL:.0f} 辆/h")
    print(f"时段 热身 {WARM/60:.0f} min / 高峰 {PEAK/60:.0f} min / 回落 {COOL/60:.0f} min\n")
    r = run("s20261120")
    print("\n结果：")
    s = summarise(r)
    print("\n抽样时间序列（每 2 分钟）：")
    for p in r["profile"][::12]:
        tail = p["queue_tail_x"]
        v = p["v_mean_mps"]
        v_txt = "--" if v is None else f"{v:.1f}"
        tail_txt = "--" if tail is None or tail != tail else f"{tail:.0f} m"
        print(f"  t={p['t']:>7.0f}s  运行车 {p['n_running']:>4}  "
              f"走廊内 {p['n_in_corridor']:>4}  平均速度 {v_txt:>5}  队尾 {tail_txt}")
    (Path(r["path"]) / "summary.json").write_text(
        json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwritten: {r['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())