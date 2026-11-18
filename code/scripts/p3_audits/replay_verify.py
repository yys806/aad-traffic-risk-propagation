"""P3-B 配对验收：真实前车轨迹回放 —— 第一道门槛（回放对齐）

阶段：P3-B（配对验收）｜ 依据：GPT 2026-11-18（gpt12.md 第 3、6 节）

做什么：
  取一个真实急刹片段，把前车的实测轨迹作为外生输入强制写入 SUMO，
  后车由仿真跟驰模型自由响应，逐帧核对「后车实际读到的前车状态」是否等于「期望值」。

三条要核对的（GPT 指定）：
  1. 前车在两臂全程同轨（这里先做单臂，两臂一致性在下一步）
  2. 后车读到的净距、相对速度、前车身份与预期一致
  3. 初始化与接缝不凭空制造跳变或急刹

做法要点：
  - 二维轨迹压成一维弧长（片段内两车同车道，可以一维化）
  - 位置为主动量，速度由位置的一阶差分得到，保证运动学一致（不做两套独立插值）
  - 每个仿真步：moveTo 定位置、setSpeed 给速度，再 simulationStep

用法：
  python replay_verify.py --event 891-887 --out code/outputs/analysis/P3B_replay_verify
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
EDGE_LEN = 4000.0
LEAD_LEN = 12.5   # 仅作默认值，实际从数据读取


def load_event(key: str) -> dict:
    segs = json.loads(EV.read_text(encoding="utf-8"))
    for s in segs:
        if f"{s['follower']}-{s['leader']}" == key:
            return s
    avail = ", ".join(f"{x['follower']}-{x['leader']}" for x in segs[:8])
    raise SystemExit(f"找不到片段 {key}；前几个可用：{avail}")


def load_pair(fol: str, led: str, t0: float, t1: float):
    want = {fol, led}
    with zipfile.ZipFile(ZIP) as z, z.open("T1_DAll.csv") as f:
        df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                         usecols=["Vehicle_ID", "Time [s]", "x [m]", "y [m]", "Speed [km/h]",
                                  "Vehicle_length [m]", "Lane"],
                         chunksize=400_000)
        parts = []
        for ch in df:
            ch["vid"] = ch["Vehicle_ID"].astype(int).astype(str)
            parts.append(ch[ch["vid"].isin(want)])
    d = pd.concat(parts).sort_values(["vid", "Time [s]"])
    out = {}
    for vid in want:
        g = d[(d["vid"] == vid) & (d["Time [s]"] >= t0 - 2) & (d["Time [s]"] <= t1 + 2)].copy()
        if len(g) < 5:
            raise SystemExit(f"{vid} 数据不足")
        out[vid] = g
    return out


def arc_length(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    ds = np.hypot(np.diff(x), np.diff(y))
    return np.concatenate([[0.0], np.cumsum(ds)])


def load_traci():
    if "SUMO_HOME" not in os.environ:
        for cand in (r"C:\Program Files (x86)\Eclipse\Sumo", r"D:\Program Files (x86)\Eclipse\Sumo"):
            if Path(cand).exists():
                os.environ["SUMO_HOME"] = cand
                break
        else:
            raise RuntimeError("SUMO_HOME 未设置")
    sys.path.append(str(Path(os.environ["SUMO_HOME"]) / "tools"))
    import traci  # noqa
    return traci


SUMO = str(Path(os.environ.get("SUMO_HOME", r"C:\Program Files (x86)\Eclipse\Sumo")) / "bin" / "sumo.exe")


def net_xml() -> str:
    return f"""<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50">
    <edge id="cor" from="a" to="b" priority="1" numLanes="1" speed="30.00" length="{EDGE_LEN}">
        <lane id="cor_0" index="0" speed="30.00" length="{EDGE_LEN}" shape="0.00,0.00 {EDGE_LEN:.2f},0.00"/>
    </edge>
    <junction id="a" type="dead_end" x="0.00" y="0.00"/>
    <junction id="b" type="dead_end" x="{EDGE_LEN:.2f}" y="0.00"/>
</net>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", default="891-887")
    ap.add_argument("--out", required=True)
    ap.add_argument("--warmup", type=float, default=2.0, help="回放开始前的预热秒数")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fol, led = a.event.split("-")
    s = load_event(a.event)
    print(f"片段 {a.event}  道{s['lane']}  {s['t_start']}–{s['t_end']}s  D峰{s['D_max']}  净距min{s['gap_min_m']}")

    pair = load_pair(fol, led, s["t_start"], s["t_end"])
    gf, gl = pair[fol], pair[led]

    # ---- 一维化：用前车的行驶方向建立公共坐标轴，两车都投影到同一根轴上 ----
    # 早先把后车投影到「前车轨迹」上会失败：后车在起始时刻还没走到前车轨迹覆盖的范围，
    # 只能投到起点，两车位置重合（实测出 -12.5 m 的假净距）。改用共同方向轴。
    lx, ly = gl["x [m]"].to_numpy(), gl["y [m]"].to_numpy()
    fx, fy = gf["x [m]"].to_numpy(), gf["y [m]"].to_numpy()
    u = np.array([lx[-1] - lx[0], ly[-1] - ly[0]])
    u = u / np.linalg.norm(u)
    org = np.array([lx[0], ly[0]])
    s_lead_raw = (np.column_stack([lx, ly]) - org) @ u
    s_fol_raw = (np.column_stack([fx, fy]) - org) @ u
    t_lead = gl["Time [s]"].to_numpy()
    t_fol = gf["Time [s]"].to_numpy()
    lens_lead = float(gl["Vehicle_length [m]"].iloc[0])
    lens_fol = float(gf["Vehicle_length [m]"].iloc[0])

    # ---- 统一时间轴：0.05 s 步长，位置为主，速度由位置差分 ----
    t_start = max(t_lead.min(), t_fol.min())
    t_end = min(t_lead.max(), t_fol.max())
    tt = np.arange(t_start, t_end, STEP)
    s_lead = np.interp(tt, t_lead, s_lead_raw)
    s_fol = np.interp(tt, t_fol, s_fol_raw)
    offset = s_lead[0]          # 两车必须减同一偏移，否则相对位置丢失
    s_lead = s_lead - offset
    s_fol = s_fol - offset
    v_lead = np.gradient(s_lead, STEP)
    v_fol = np.gradient(s_fol, STEP)

    print(f"回放时长 {len(tt)} 步 = {(tt[-1]-tt[0]):.1f} s")
    print(f"前车行程 {s_lead[-1]:.0f} m，速度 {v_lead.min():.1f}–{v_lead.max():.1f} m/s")
    print(f"实测后车行程 {s_fol[-1]:.0f} m，速度 {v_fol.min():.1f}–{v_fol.max():.1f} m/s")
    gap_true = s_lead - s_fol - (lens_lead + lens_fol) / 2.0
    print(f"实测净距 首 {gap_true[0]:.1f} m  末 {gap_true[-1]:.1f} m  最小 {gap_true.min():.1f} m")

    # ---- 建 SUMO 场景 ----
    tmp = out / "sumo"
    tmp.mkdir(exist_ok=True)
    (tmp / "net.net.xml").write_text(net_xml(), encoding="utf-8")
    x0 = 100.0
    (tmp / "r.rou.xml").write_text(
        f'<routes><vType id="car" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
        f' tau="0.6" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" speedDev="0.12"/>'
        f'<route id="rc" edges="cor"/>'
        f'<vehicle id="LEAD" type="car" route="rc" depart="0" departPos="{x0:.2f}" departSpeed="{max(v_lead[0],0.1):.2f}" departLane="0"/>'
        f'<vehicle id="FOL" type="car" route="rc" depart="0" departPos="{x0 + s_fol[0]:.2f}" departSpeed="{max(v_fol[0],0.1):.2f}" departLane="0"/>'
        f'</routes>', encoding="utf-8")
    (tmp / "run.sumocfg").write_text(
        f'<configuration><input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{len(tt)*STEP+5:.1f}"/><step-length value="{STEP}"/></time>'
        f'<processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>'
        f'<random_number><seed value="1"/></random_number></configuration>', encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(tmp / "run.sumocfg"), "--no-step-log", "true", "--collision.action", "warn"])
    log = []
    try:
        for k in range(len(tt)):
            target = x0 + s_lead[k]
            if "LEAD" in traci.vehicle.getIDList():
                traci.vehicle.moveTo("LEAD", "cor_0", target)
                traci.vehicle.setSpeed("LEAD", float(max(v_lead[k], 0.0)))
            traci.simulationStep()
            present = traci.vehicle.getIDList()
            if "LEAD" in present and "FOL" in present:
                pl = traci.vehicle.getLanePosition("LEAD")
                pf = traci.vehicle.getLanePosition("FOL")
                vv = traci.vehicle.getSpeed("FOL")
                lead_read = traci.vehicle.getLeader("FOL")
                log.append({
                    "k": k, "t": k * STEP,
                    "lead_pos_cmd": x0 + s_lead[min(k + 1, len(s_lead) - 1)], "lead_pos_read": pl,
                    "fol_pos": pf, "fol_v": vv,
                    "gap_read": (pl - pf - 5.0),
                    "lead_id_read": lead_read[0] if lead_read else None,
                    "gap_expected": (x0 + s_lead[min(k + 1, len(s_lead) - 1)]) - pf - 5.0,
                })
    finally:
        traci.close()

    L = pd.DataFrame(log)
    L["pos_err"] = (L["lead_pos_read"] - L["lead_pos_cmd"]).abs()
    L["gap_err"] = (L["gap_read"] - L["gap_expected"]).abs()
    print(f"\n=== 回放对齐验收（{len(L)} 步有效）===")
    print(f"  前车位置误差：中位 {L['pos_err'].median():.4f} m  最大 {L['pos_err'].max():.4f} m")
    print(f"  净距读数误差：中位 {L['gap_err'].median():.4f} m  最大 {L['gap_err'].max():.4f} m")
    print(f"  后车识别到的前车 ID 全为 LEAD：{(L['lead_id_read'] == 'LEAD').mean()*100:.1f}%")
    print(f"  仿真后车行程 {L['fol_pos'].iloc[-1] - L['fol_pos'].iloc[0]:.0f} m vs 实测 {s_fol[-1]:.0f} m")
    print(f"  仿真最小净距 {L['gap_read'].min():.1f} m vs 实测 {(s_lead-s_fol-LEAD_LEN).min():.1f} m")
    L.to_csv(out / "replay_log.csv", index=False)
    print(f"\n逐步日志：{out/'replay_log.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
