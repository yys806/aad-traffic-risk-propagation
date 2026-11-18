"""pNEUMA 双车回放验收（第 4 步·第一类基线）

阶段：P3-B（两类无消息回放验收）
依据：gpt19.md 第 2 节——「把实现正确和模型像真人分开判」

做两件事：
  实现验收：回放时间对齐、初始速度与净距、前车 ID 是否被后车正确识别
  模型适用性：自由仿真的后车速度与实测后车的 MAE、最小净距及绝对误差

启动门槛（gpt19 给的工程试跑值，明确标注未核实）：
  速度 MAE ≤ 1.5 m/s；最小净距绝对误差 ≤ 3 m

用法：
  TIER=m10 python pneuma_replay_baseline.py --event 308-306 --out <dir>
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
_STEP = 0.05
EDGE_LEN = 3000.0
WARM = 5.0        # t0 之前用于预热的实测历史
POST = 20.0       # 回放时长
lat0, lon0 = 37.9777, 23.7375


def to_xy(lat, lon):
    return ((lon - lon0) * 111320.0 * math.cos(math.radians(lat0)),
            (lat - lat0) * 110540.0)


def load_pair(lead: str, fol: str):
    out = {}
    with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
        rd = csv.reader(f, delimiter=";")
        next(rd)
        for r in rd:
            if len(r) < 16:
                continue
            tid = r[0].strip()
            if tid not in (lead, fol):
                continue
            try:
                vals = np.array([float(x) for x in r[4:] if x.strip() != ""])
            except ValueError:
                continue
            n = len(vals) // 6
            v = vals[: n * 6].reshape(n, 6)
            o = np.argsort(v[:, 5])
            x, y = to_xy(v[o, 0], v[o, 1])
            out[tid] = {"t": v[o, 5], "x": x, "y": y, "v": v[o, 2]}
    return out


def load_traci():
    if "SUMO_HOME" not in os.environ:
        for c in (r"C:\Program Files (x86)\Eclipse\Sumo", r"D:\Program Files (x86)\Eclipse\Sumo"):
            if Path(c).exists():
                os.environ["SUMO_HOME"] = c
                break
    sys.path.append(str(Path(os.environ["SUMO_HOME"]) / "tools"))
    import traci  # noqa
    return traci


SUMO = str(Path(os.environ.get("SUMO_HOME", r"C:\Program Files (x86)\Eclipse\Sumo")) / "bin" / "sumo.exe")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", required=True, help="形如 308-306（后车-前车）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--t0", type=float, default=None, help="不指定则从事件表读")
    ap.add_argument("--tau", type=float, default=0.9)
    ap.add_argument("--mingap", type=float, default=2.0)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    fol, lead = a.event.split("-")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    # t0
    t0 = a.t0
    if t0 is None:
        tier = os.environ.get("TIER", "m10")
        tab = Path(f"D:/shen/TJU/AAD/code/outputs/analysis/P3B_pneuma_{tier}/table_events.csv")
        import csv as _csv
        with tab.open("r", encoding="utf-8-sig") as f:
            for r in _csv.DictReader(f):
                if r["lead_id"] == lead and r["fol_id"] == fol:
                    t0 = float(r["t"]); break
    if t0 is None:
        raise SystemExit("找不到该事件的 t0")
    print(f"事件 {fol}←{lead}  t0={t0:.1f}s")

    rec = load_pair(lead, fol)
    if lead not in rec or fol not in rec:
        raise SystemExit("轨迹缺失")
    gl, gf = rec[lead], rec[fol]

    # 一维化：用前车 t0 前的行驶方向建共同轴
    m = (gl["t"] >= t0 - WARM) & (gl["t"] <= t0 + POST)
    gl_s = gl
    x0, y0 = float(np.interp(t0, gl["t"], gl["x"])), float(np.interp(t0, gl["t"], gl["y"]))
    x1, y1 = float(np.interp(t0 + POST, gl["t"], gl["x"])), float(np.interp(t0 + POST, gl["t"], gl["y"]))
    u = np.array([x1 - x0, y1 - y0]); u = u / max(np.linalg.norm(u), 1e-9)

    def proj(xa, ya):
        return (xa - x0) * u[0] + (ya - y0) * u[1]

    tt = np.arange(t0 - WARM, t0 + POST, _STEP)
    s_lead = proj(np.interp(tt, gl["t"], gl["x"]), np.interp(tt, gl["t"], gl["y"]))
    s_fol = proj(np.interp(tt, gf["t"], gf["x"]), np.interp(tt, gf["t"], gf["y"]))
    v_lead = np.gradient(s_lead, _STEP)
    v_fol = np.gradient(s_fol, _STEP)
    k0 = int(round(WARM / _STEP))
    print(f"  前车 {tt[-1]-tt[0]:.1f}s 行程 {s_lead[-1]-s_lead[0]:.0f} m，速度 {v_lead.min():.1f}–{v_lead.max():.1f} m/s")
    print(f"  后车 实测速度 {v_fol[k0:].min():.1f}–{v_fol[k0:].max():.1f} m/s")
    print(f"  t0 时净距 {s_lead[k0]-s_fol[k0]:.1f} m")

    # ---- SUMO 双车回放 ----
    tmp = out / "sumo"; tmp.mkdir(exist_ok=True)
    (tmp / "net.net.xml").write_text(
        f'<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50">'
        f'<edge id="cor" from="a" to="b" priority="1" numLanes="1" speed="40.00" length="{EDGE_LEN}">'
        f'<lane id="cor_0" index="0" speed="40.00" length="{EDGE_LEN}" shape="0.00,0.00 {EDGE_LEN:.2f},0.00"/>'
        f'</edge><junction id="a" type="dead_end" x="0.00" y="0.00"/>'
        f'<junction id="b" type="dead_end" x="{EDGE_LEN:.2f}" y="0.00"/></net>', encoding="utf-8")
    base = 200.0
    s_l0 = s_lead[0] - s_lead[0]      # 前车起点归零
    s_f0 = s_fol[0] - s_lead[0]
    (tmp / "r.rou.xml").write_text(
        f'<routes><vType id="car" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
        f' tau="{a.tau}" length="4.5" minGap="{a.mingap}" maxSpeed="40" speedFactor="1" speedDev="0"/>'
        f'<route id="rc" edges="cor"/>'
        f'<vehicle id="LEAD" type="car" route="rc" depart="0" departPos="{base + s_l0:.2f}" departSpeed="{max(v_lead[0],0.1):.2f}" departLane="0"/>'
        f'<vehicle id="FOL" type="car" route="rc" depart="0" departPos="{base + s_f0:.2f}" departSpeed="{max(v_fol[0],0.1):.2f}" departLane="0"/>'
        f'</routes>', encoding="utf-8")
    (tmp / "run.sumocfg").write_text(
        f'<configuration><input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{len(tt)*_STEP+5:.1f}"/><step-length value="{_STEP}"/></time>'
        f'<processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>'
        f'<random_number><seed value="1"/></random_number></configuration>', encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(tmp / "run.sumocfg"), "--no-step-log", "true", "--collision.action", "warn"])
    log = []
    try:
        for k in range(len(tt)):
            target = base + s_l0 + (s_lead[k] - s_lead[0])
            if "LEAD" in traci.vehicle.getIDList():
                traci.vehicle.moveTo("LEAD", "cor_0", target)
                traci.vehicle.setSpeed("LEAD", float(max(v_lead[k], 0.0)))
            traci.simulationStep()
            pres = traci.vehicle.getIDList()
            if "LEAD" in pres and "FOL" in pres:
                pl = traci.vehicle.getLanePosition("LEAD")
                pf = traci.vehicle.getLanePosition("FOL")
                lead_read = traci.vehicle.getLeader("FOL")
                log.append({"k": k, "t": k * _STEP,
                            "lead_cmd": base + s_l0 + (s_lead[min(k+1, len(s_lead)-1)] - s_lead[0]),
                            "lead_read": pl, "fol": pf,
                            "v_fol_sim": traci.vehicle.getSpeed("FOL"),
                            "gap": pl - pf - 4.5,
                            "lead_id_read": lead_read[0] if lead_read else None})
    finally:
        traci.close()

    import pandas as pd
    L = pd.DataFrame(log)
    L["pos_err"] = (L["lead_read"] - L["lead_cmd"]).abs()
    post = L[L["t"] >= WARM]
    v_true = v_fol[k0:k0 + len(post)][:len(post)]
    v_sim = post["v_fol_sim"].to_numpy()[:len(v_true)]
    mae = float(np.mean(np.abs(v_sim - v_true))) if len(v_true) else float("nan")
    gap_true = (s_lead - s_fol)[k0:k0 + len(post)][:len(post)]
    gap_sim = post["gap"].to_numpy()[:len(gap_true)]
    gap_err = float(abs(np.min(gap_sim) - np.min(gap_true))) if len(gap_true) else float("nan")

    print(f"\n=== 实现验收 ===")
    print(f"  前车位置误差 中位 {L['pos_err'].median():.4f} m  最大 {L['pos_err'].max():.4f} m")
    print(f"  后车识别前车 ID 为 LEAD 的比例："
          f"{100*np.mean(L['lead_id_read'].fillna('') == 'LEAD'):.1f}%")
    print(f"\n=== 模型适用性（启动门槛：速度 MAE ≤1.5，净距误差 ≤3；未核实）===")
    print(f"  速度 MAE = {mae:.2f} m/s   → {'通过' if mae <= 1.5 else '未通过'}")
    print(f"  最小净距：仿真 {np.min(gap_sim):.1f} m  实测 {np.min(gap_true):.1f} m  "
          f"绝对误差 {gap_err:.1f} m → {'通过' if gap_err <= 3 else '未通过'}")
    print(f"\n注意：实现通过而模型未通过，是有效结论（真人反应与仿真模型本就不同），不要逐事件调参抹平。")

    L.to_csv(out / "replay_log.csv", index=False)
    (out / "summary.json").write_text(json.dumps({
        "event": a.event, "t0": t0, "pos_err_median": float(L["pos_err"].median()),
        "lead_id_ok_pct": float(100 * np.mean(L["lead_id_read"].fillna("") == "LEAD")),
        "v_mae": mae, "gap_min_sim": float(np.min(gap_sim)),
        "gap_min_true": float(np.min(gap_true)), "gap_err": gap_err,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n输出：{out/'replay_log.csv'}  {out/'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
