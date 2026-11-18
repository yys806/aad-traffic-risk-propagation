"""P3-B 配对验收·第二道门槛：空干预一致

阶段：P3-B（配对验收）｜ 依据：GPT 2026-11-18（gpt12.md 第 6 节、gpt13.md 第 4 节）

三条验收（GPT 指定）：
  1. 无消息 vs 无消息：两次运行必须完全可重复（同种子同输入 → 逐步相同）
  2. 消息 vs 无消息：在「消息首次可能改变控制」之前，两臂后车状态必须逐步一致
  3. 分支后不再用实测后车轨迹重置（本脚本本来就不重置）

实现：同一前车轨迹回放两次/两臂，逐帧比对后车位置与速度。
消息时刻取「前车制动起点 + 1.5 s」（检测与通信延迟），两臂共用同一时刻。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ZIP = Path(r"D:\shen\TJU\AAD\local_research\staging\task11_20261031\mitra\Data_T1.zip")
EV = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P3B_candidates\candidate_events_v2.json")
STEP = 0.05
EDGE_LEN = 6000.0
MSG_DELAY = 1.5      # 前车制动起点后多久消息生效（检测 + 通信）
CAP = 0.90


def load_event(key: str) -> dict:
    for s in json.loads(EV.read_text(encoding="utf-8")):
        if f"{s['follower']}-{s['leader']}" == key:
            return s
    raise SystemExit(f"找不到片段 {key}")


def load_pair(fol: str, led: str, t0: float, t1: float):
    want = {fol, led}
    with zipfile.ZipFile(ZIP) as z, z.open("T1_DAll.csv") as f:
        it = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                         usecols=["Vehicle_ID", "Time [s]", "x [m]", "y [m]", "Speed [km/h]",
                                  "Vehicle_length [m]"],
                         chunksize=400_000)
        parts = []
        for ch in it:
            ch["vid"] = ch["Vehicle_ID"].astype(int).astype(str)
            sel = ch[ch["vid"].isin(want)]
            if len(sel):
                parts.append(sel)
    d = pd.concat(parts).sort_values(["vid", "Time [s]"])
    out = {}
    for v in want:
        g = d[(d["vid"] == v) & (d["Time [s]"] >= t0 - 3) & (d["Time [s]"] <= t1 + 3)]
        if len(g) < 10:
            raise SystemExit(f"{v} 数据不足")
        out[v] = g
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


def run_arm(tmp: Path, s_lead, v_lead, s_fol0, v_fol0, t_msg, use_msg: bool, seed: int):
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "net.net.xml").write_text(
        f'<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50">'
        f'<edge id="cor" from="a" to="b" priority="1" numLanes="1" speed="30.00" length="{EDGE_LEN}">'
        f'<lane id="cor_0" index="0" speed="30.00" length="{EDGE_LEN}" shape="0.00,0.00 {EDGE_LEN:.2f},0.00"/>'
        f'</edge><junction id="a" type="dead_end" x="0.00" y="0.00"/>'
        f'<junction id="b" type="dead_end" x="{EDGE_LEN:.2f}" y="0.00"/></net>', encoding="utf-8")
    x0 = 100.0
    (tmp / "r.rou.xml").write_text(
        f'<routes><vType id="car" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
        f' tau="0.6" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" speedDev="0.12"/>'
        f'<route id="rc" edges="cor"/>'
        f'<vehicle id="LEAD" type="car" route="rc" depart="0" departPos="{x0:.2f}" departSpeed="{max(v_lead[0],0.1):.2f}" departLane="0"/>'
        f'<vehicle id="FOL" type="car" route="rc" depart="0" departPos="{x0+s_fol0:.2f}" departSpeed="{max(v_fol0,0.1):.2f}" departLane="0"/>'
        f'</routes>', encoding="utf-8")
    (tmp / "run.sumocfg").write_text(
        f'<configuration><input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{len(s_lead)*STEP+5:.1f}"/><step-length value="{STEP}"/></time>'
        f'<processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number></configuration>', encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(tmp / "run.sumocfg"), "--no-step-log", "true",
                 "--collision.action", "warn"])
    log = []
    v_base = None
    try:
        for k in range(len(s_lead)):
            t = k * STEP
            if "LEAD" in traci.vehicle.getIDList():
                traci.vehicle.moveTo("LEAD", "cor_0", x0 + s_lead[k])
                traci.vehicle.setSpeed("LEAD", float(max(v_lead[k], 0.0)))
            if use_msg and "FOL" in traci.vehicle.getIDList():
                if t >= t_msg:
                    if v_base is None:
                        v_base = traci.vehicle.getSpeed("FOL")
                    traci.vehicle.setMaxSpeed("FOL", max(0.5, v_base * CAP))
            traci.simulationStep()
            pres = traci.vehicle.getIDList()
            if "LEAD" in pres and "FOL" in pres:
                log.append({"k": k, "t": t,
                            "lead": traci.vehicle.getLanePosition("LEAD"),
                            "fol": traci.vehicle.getLanePosition("FOL"),
                            "vol": traci.vehicle.getSpeed("FOL")})
    finally:
        traci.close()
    return pd.DataFrame(log)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", default="1133-1122")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    fol, led = a.event.split("-")
    s = load_event(a.event)
    pair = load_pair(fol, led, s["t_start"], s["t_end"])
    gf, gl = pair[fol], pair[led]

    lx, ly = gl["x [m]"].to_numpy(), gl["y [m]"].to_numpy()
    fx, fy = gf["x [m]"].to_numpy(), gf["y [m]"].to_numpy()
    u = np.array([lx[-1] - lx[0], ly[-1] - ly[0]]); u = u / np.linalg.norm(u)
    org = np.array([lx[0], ly[0]])
    s_lead_raw = (np.column_stack([lx, ly]) - org) @ u
    s_fol_raw = (np.column_stack([fx, fy]) - org) @ u
    t_lead = gl["Time [s]"].to_numpy(); t_fol = gf["Time [s]"].to_numpy()

    t0 = max(t_lead.min(), t_fol.min()); t1 = min(t_lead.max(), t_fol.max())
    tt = np.arange(t0, t1, STEP)
    s_lead = np.interp(tt, t_lead, s_lead_raw); s_lead -= s_lead[0]
    s_fol = np.interp(tt, t_fol, s_fol_raw) - s_lead_raw[0]
    v_lead = np.gradient(s_lead, STEP); v_fol = np.gradient(s_fol, STEP)

    # 前车制动起点（用原始速度差分定位）
    vl_raw = gl["Speed [km/h]"].to_numpy() / 3.6
    a_raw = np.gradient(vl_raw, t_lead)
    k_brake = np.where(a_raw < -3.0)[0]
    t_brake = float(t_lead[k_brake[0]] - t0) if len(k_brake) else 10.0
    t_msg = t_brake + MSG_DELAY
    print(f"片段 {a.event}：回放 {(tt[-1]-t0):.1f} s，前车制动起点 t={t_brake:.2f} s，"
          f"消息生效 t={t_msg:.2f} s")

    A1 = run_arm(out / "s1", s_lead, v_lead, s_fol[0], v_fol[0], t_msg, False, 1)
    A2 = run_arm(out / "s2", s_lead, v_lead, s_fol[0], v_fol[0], t_msg, False, 1)
    B = run_arm(out / "s3", s_lead, v_lead, s_fol[0], v_fol[0], t_msg, True, 1)

    n = min(len(A1), len(A2), len(B))
    d_pos_r = (A1["fol"][:n] - A2["fol"][:n]).abs()
    d_vel_r = (A1["vol"][:n] - A2["vol"][:n]).abs()
    print(f"\n=== 门槛 1：无消息 vs 无消息（可重复性）===")
    print(f"  逐帧位置最大差 {d_pos_r.max():.6f} m    速度最大差 {d_vel_r.max():.6f} m/s")
    print(f"  → {'通过' if d_pos_r.max() < 1e-6 and d_vel_r.max() < 1e-6 else '不通过'}")

    idx = np.searchsorted(B["t"][:n].to_numpy(), t_msg)
    d_pos_m = (A1["fol"][:idx] - B["fol"][:idx]).abs()
    d_vel_m = (A1["vol"][:idx] - B["vol"][:idx]).abs()
    print(f"\n=== 门槛 2：消息 vs 无消息，在 t={t_msg:.2f}s 之前（{idx} 帧）===")
    print(f"  逐帧位置最大差 {d_pos_m.max():.6f} m    速度最大差 {d_vel_m.max():.6f} m/s")
    print(f"  → {'通过' if d_pos_m.max() < 1e-6 and d_vel_m.max() < 1e-6 else '不通过'}")

    after = B["t"][:n].to_numpy() >= t_msg
    print(f"\n=== 分支后（应当出现差异）===")
    print(f"  位置差 最大 {d_pos_r.max():.3f}")
    dp = (A1["fol"] - B["fol"]).abs()
    print(f"  全额逐帧位置差 最大 {dp.max():.3f} m，末帧 {dp.iloc[-1]:.3f} m")
    print(f"  说明：差值出现在分支之后即为预期（消息确实改变了后车行为）")

    pd.concat([A1.assign(arm="none1"), A2.assign(arm="none2"), B.assign(arm="msg")]).to_csv(
        out / "compare_log.csv", index=False)
    print(f"\n日志：{out/'compare_log.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
