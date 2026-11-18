"""P3 路线 A：消息臂——消息能否促成可测的提前拉开

阶段：P3 ｜ 依据：GPT-6.2-sol 2026-11-18（brief8 → gpt8.md）
主方案：目标区 3.0 km、±50 m、3 s 渐入 + 15 s 保持、主终点取 t0+23…t0+26 的配对平均净距差

三个臂：
  plain    无源事件、无消息（基线）
  event    有源事件、无消息（物理参照）
  message  有源事件 + 在 t0+8 向锁定车辆发消息，限速到其当前速度的 90%

锁定：t0 时刻位于目标区的车辆 ID；各臂追踪同一批车，驶出区仍继续跟踪。

用法：
  python run_p3a_message.py --arm message --seed 20261119 --out <dir>
  python run_p3a_message.py --pair --seed 20261119 --out <dir>     # 跑 event + message 并对比
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

# ---- 与 P2 冻结配置一致 ----
EDGE_LEN = 15000.0
SOURCE_X = 6000.0
HEADWAY = 20.0
V0 = 15.0
STEP = 0.05
WARMUP = 120.0
RAMP = 6.0
HOLD = 300.0
OBS_AFTER = 690.0
MAX_SLOTS = 1600
MAX_SPEED = 30.0
VEH_LEN = 5.0
MIN_GAP = 2.5
TAU = 0.6
STRENGTH = {"strong": 3.0, "weak": 8.0}

# ---- P3 路线 A 参数（GPT 2026-11-18 定）----
TGT_X = 3000.0
TGT_BAND = 50.0
MSG_START = 8.0        # t0 之后何时送达
MSG_RAMP_IN = 3.0
MSG_HOLD = 15.0        # 11 → 26
MSG_RAMP_OUT = 3.0     # 26 → 29
CAP_RATIO = 0.90
MAIN_WIN = (23.0, 26.0)   # 主终点窗


def v_eq(headway: float) -> float:
    return min((headway - VEH_LEN - MIN_GAP) / TAU, MAX_SPEED)


def load_traci():
    if "SUMO_HOME" not in os.environ:
        for cand in (r"D:\Program Files (x86)\Eclipse\Sumo", r"C:\Program Files (x86)\Eclipse\Sumo"):
            if Path(cand).exists():
                os.environ["SUMO_HOME"] = cand
                break
        else:
            raise RuntimeError("SUMO_HOME 未设置")
    sys.path.append(str(Path(os.environ["SUMO_HOME"]) / "tools"))
    import traci  # noqa
    return traci


SUMO = str(Path(os.environ.get("SUMO_HOME", r"D:\Program Files (x86)\Eclipse\Sumo")) / "bin" / "sumo.exe")


def net_xml() -> str:
    return f"""<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50">
    <edge id="cor" from="a" to="b" priority="1" numLanes="1" speed="30.00" length="{EDGE_LEN}">
        <lane id="cor_0" index="0" speed="30.00" length="{EDGE_LEN}" shape="0.00,0.00 {EDGE_LEN:.2f},0.00"/>
    </edge>
    <junction id="a" type="dead_end" x="0.00" y="0.00"/>
    <junction id="b" type="dead_end" x="{EDGE_LEN:.2f}" y="0.00"/>
</net>"""


def routes_xml(sigma: float, headway: float = HEADWAY) -> str:
    n = int((EDGE_LEN - headway) / headway)
    vq = v_eq(headway)
    period = headway / vq
    vt = (f'<vType id="cal" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="{sigma}"'
          f' tau="0.6" length="5" minGap="2.5" maxSpeed="{MAX_SPEED}" speedFactor="1"'
          f' speedDev="0.12"/>')
    vehs = []
    for i in range(n):
        pos = 10.0 + headway * i
        vehs.append(f'<vehicle id="V{i}" type="cal" route="rc" depart="0"'
                    f' departPos="{pos:.2f}" departSpeed="{vq:.3f}" departLane="0"/>')
    # vehicles 必须在 flow 之前（按 depart 时间排序），否则 SUMO 静默丢弃
    return (f'<routes>{vt}'
            f'<route id="rc" edges="cor"/>'
            f'{"".join(vehs)}'
            f'<flow id="in" type="cal" route="rc" begin="{period:.3f}"'
            f' end="{WARMUP + OBS_AFTER:.1f}" period="{period:.3f}"'
            f' departSpeed="{vq:.3f}" departLane="0"/>'
            f'</routes>')


def run(tmp: Path, arm: str, sigma: float, strength: str | None,
        headway: float = HEADWAY, seed: int = 20261119) -> dict:
    (tmp / "net.net.xml").write_text(net_xml(), encoding="utf-8")
    (tmp / f"routes_{arm}.rou.xml").write_text(routes_xml(sigma, headway), encoding="utf-8")
    cfg = tmp / f"run_{arm}.sumocfg"
    cfg.write_text(
        f"""<configuration>
    <input><net-file value="net.net.xml"/><route-files value="routes_{arm}.rou.xml"/></input>
    <time><begin value="0"/><end value="{WARMUP + OBS_AFTER + 30:.1f}"/><step-length value="{STEP}"/></time>
    <processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>
    <random_number><seed value="{seed}"/></random_number>
</configuration>""", encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true", "--collision.action", "warn"])
    const = traci.constants
    steps = int(round((WARMUP + OBS_AFTER + 30.0) / STEP))

    idx: dict[str, int] = {}
    pos = np.full((steps, MAX_SLOTS), np.nan, dtype=np.float32)
    spd = np.full((steps, MAX_SLOTS), np.nan, dtype=np.float32)

    event_t0 = None
    src_id = None
    src_target = STRENGTH.get(strength or "strong", 3.0)
    src_v_start = V0
    locked: set[str] = set()
    base_v: dict[str, float] = {}
    msg_sent_at = None
    subscribed: set[str] = set()
    n_collision = 0

    try:
        for k in range(steps):
            now = k * STEP
            if now <= WARMUP:
                traci.simulationStep()
            else:
                # 源车扰动
                if src_id is not None and event_t0 is not None:
                    el = now - event_t0
                    if el < RAMP:
                        traci.vehicle.setSpeed(src_id, src_v_start - (src_v_start - src_target) * (el / RAMP))
                    elif el < RAMP + HOLD:
                        traci.vehicle.setSpeed(src_id, src_target)
                    elif el < RAMP + HOLD + 1.0:
                        traci.vehicle.setSpeed(src_id, -1)
                # 消息动作
                if arm == "message" and locked and event_t0 is not None:
                    el = now - (event_t0 + MSG_START)
                    if el >= 0:
                        if not base_v:
                            msg_sent_at = now
                            for v in locked:
                                if v in traci.vehicle.getIDList():
                                    base_v[v] = traci.vehicle.getSpeed(v)
                        cap_f = None
                        if el < MSG_RAMP_IN:
                            cap_f = 1.0 - (1.0 - CAP_RATIO) * (el / MSG_RAMP_IN)
                        elif el < MSG_RAMP_IN + MSG_HOLD:
                            cap_f = CAP_RATIO
                        elif el < MSG_RAMP_IN + MSG_HOLD + MSG_RAMP_OUT:
                            cap_f = CAP_RATIO + (1.0 - CAP_RATIO) * ((el - MSG_RAMP_IN - MSG_HOLD) / MSG_RAMP_OUT)
                        present = set(traci.vehicle.getIDList())
                        for v, vb in base_v.items():
                            if v not in present:
                                continue
                            if cap_f is None:
                                traci.vehicle.setMaxSpeed(v, MAX_SPEED)
                            else:
                                traci.vehicle.setMaxSpeed(v, max(0.5, vb * cap_f))
                traci.simulationStep()

            present = traci.vehicle.getIDList()
            for v in present:
                if v not in subscribed:
                    traci.vehicle.subscribe(v, (const.VAR_LANEPOSITION, const.VAR_SPEED))
                    subscribed.add(v)
            res = traci.vehicle.getAllSubscriptionResults()

            for v in res:
                if v not in idx and len(idx) < MAX_SLOTS:
                    idx[v] = len(idx)
            for v, val in res.items():
                i = idx.get(v)
                if i is None:
                    continue
                pos[k, i] = val.get(const.VAR_LANEPOSITION, np.nan)
                spd[k, i] = val.get(const.VAR_SPEED, np.nan)

            # 锁定目标区车辆
            if strength is not None and src_id is None and now >= WARMUP:
                cands = [(abs(res[v].get(const.VAR_LANEPOSITION, 1e9) - SOURCE_X), v) for v in res]
                if cands:
                    _, src_id = min(cands)
                    event_t0 = now
                    src_v_start = float(res[src_id].get(const.VAR_SPEED, V0))
                    for v in res:
                        x = res[v].get(const.VAR_LANEPOSITION, np.nan)
                        if np.isfinite(x) and abs(x - TGT_X) <= TGT_BAND:
                            locked.add(v)
    finally:
        traci.close()

    used = len(idx)
    return {"arm": arm, "sigma": sigma, "strength": strength, "seed": seed,
            "event_t0": event_t0, "source_id": src_id,
            "locked_ids": sorted(locked), "msg_sent_at": msg_sent_at,
            "n_locked": len(locked), "n_slots": used, "step_s": STEP,
            "pos": pos[:, :used], "spd": spd[:, :used], "ids": list(idx.keys())}


def net_gap_series(POS, SPD, ids, locked_ids, k0, steps_after):
    """锁定车辆相对其前车的净距序列（按位置排序取前车，单车道无换道）"""
    ip = {v: i for i, v in enumerate(ids)}
    rows = [ip[v] for v in locked_ids if v in ip]
    k1 = k0
    k2 = min(k0 + steps_after, POS.shape[0])
    out = {v: np.full(k2 - k1, np.nan) for v in locked_ids}
    for kk, k in enumerate(range(k1, k2)):
        row_p = POS[k]
        row_v = SPD[k]
        live = np.where(np.isfinite(row_p))[0]
        if len(live) < 2:
            continue
        order = live[np.argsort(row_p[live])]
        rank = {s: j for j, s in enumerate(order)}
        for v in locked_ids:
            i = ip.get(v)
            if i is None or not np.isfinite(row_p[i]):
                continue
            j = rank.get(i)
            if j is None or j + 1 >= len(order):
                continue
            lead = order[j + 1]
            out[v][kk] = row_p[lead] - VEH_LEN - row_p[i]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["plain", "event", "message"], default="message")
    ap.add_argument("--pair", action="store_true", help="跑 event 与 message 并直接对比")
    ap.add_argument("--sigma", type=float, default=0.0)
    ap.add_argument("--strength", default="strong")
    ap.add_argument("--headway", type=float, default=HEADWAY)
    ap.add_argument("--seed", type=int, default=20261119)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    out = Path(a.out)
    tmp = out / "sumo"
    tmp.mkdir(parents=True, exist_ok=True)

    if a.pair:
        arms = ("event", "message")
    else:
        arms = (a.arm,)

    data = {}
    for arm in arms:
        t = time.time()
        print(f"[run] arm={arm} seed={a.seed} ...", flush=True)
        d = run(tmp, arm, a.sigma, a.strength, a.headway, a.seed)
        print(f"[run] arm={arm} 完成，{time.time()-t:.1f}s，锁定 {d['n_locked']} 车，源 t0={d['event_t0']}", flush=True)
        data[arm] = d

    # 逐臂存
    for arm, d in data.items():
        np.savez_compressed(out / f"{arm}.npz",
                            pos=d["pos"], spd=d["spd"],
                            ids=np.array(d["ids"]),
                            locked=np.array(sorted(d["locked_ids"])) if d["locked_ids"] else np.array([]),
                            event_t0=np.float64(d["event_t0"] or 0.0),
                            step_s=d["step_s"])

    if a.pair and "event" in data and "message" in data:
        ev, ms = data["event"], data["message"]
        t0 = ev["event_t0"] or ms["event_t0"]
        k0 = int(round(t0 / STEP))
        n_after = int(round(60.0 / STEP))
        locked = sorted(set(ev["locked_ids"]) & set(ms["locked_ids"]))
        print(f"\n锁定车（两臂共有）{len(locked)}：{locked}")

        ge = net_gap_series(ev["pos"], ev["spd"], ev["ids"], locked, k0, n_after)
        gm = net_gap_series(ms["pos"], ms["spd"], ms["ids"], locked, k0, n_after)

        print(f"\n{'时刻':>8} " + "".join(f"{v:>10}" for v in locked))
        print(f"{'(t0后)':>8} " + "".join(f"{'ev/msg':>10}" for _ in locked))
        for t in (0, 8, 11, 20, 23, 25, 26, 30, 40, 50):
            k = int(round(t / STEP))
            if k >= n_after:
                continue
            row = []
            for v in locked:
                a_ = ge[v][k] if k < len(ge[v]) else np.nan
                b_ = gm[v][k] if k < len(gm[v]) else np.nan
                row.append(f"{a_:.2f}/{b_:.2f}" if np.isfinite(a_) and np.isfinite(b_) else "  --  ")
            print(f"{t:>8} " + "".join(f"{r:>10}" for r in row))

        # 主终点
        w1, w2 = MAIN_WIN
        i1, i2 = int(round(w1 / STEP)), int(round(w2 / STEP))
        diffs, base = [], []
        for v in locked:
            a_ = np.nanmean(ge[v][i1:i2]) if i2 <= len(ge[v]) else np.nan
            b_ = np.nanmean(gm[v][i1:i2]) if i2 <= len(gm[v]) else np.nan
            if np.isfinite(a_) and np.isfinite(b_):
                diffs.append(b_ - a_)
                base.append(a_)
        if diffs:
            print(f"\n主终点 t0+{w1:.0f}…{w2:.0f}s：")
            print(f"  每车净距差（message − event）：{['%.2f' % d for d in diffs]}")
            print(f"  事件内平均：{np.mean(diffs):+.3f} m   （无消息臂该窗平均净距 {np.mean(base):.2f} m）")
        else:
            print("\n主终点无法计算（有效车数为 0）")

    (out / "meta.json").write_text(json.dumps(
        {arm: {k: v for k, v in d.items() if k not in ("pos", "spd", "ids")} for arm, d in data.items()},
        ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n输出目录：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
