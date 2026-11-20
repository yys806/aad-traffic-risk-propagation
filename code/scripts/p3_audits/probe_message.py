"""0.1.8 单探针：消息能否把「必须的急刹」降回车辆能力之内。

设计依据：`docs/tasks/0.1.8_单探针规格_预注册.md`（GPT 第七十二轮五条裁决后的修订版）

【骨架复用 0.0.3b 台架 three_layer_bench_v2.py】
行为层、安全层、记录方式、步长 0.05 s、常量全部沿用，不重造。

【GPT 第七十三轮要求补齐的四项】
1. 起刹口径对齐规格：BRAKE_THR 从 0.3 改成 **0.1**（规格写 ≤ −0.1 m/s²，脚本原来用 0.3）
2. 8b 改用**限幅前的目标速度**验收，不用起刹时刻/峰值/停车位置（那些只作诊断）
3. A 与 C 做**未取整逐帧对拍**
4. 补「无前车 + 通用提示」的零制动对照

【臂】
  a         R=∞ 无报文        长视距正对照（参照）
  b         R=80 无报文       本地感知不足，必撞（复现 0.0.3b）
  c         R=80 真报文       报「队尾在真实位置、速度 0」
  d         R=80 报近(100 m)  同格式但坐标报近 → 应更早更狠
  far600    R=80 报远(600 m)  同格式但坐标报远 → 收包后仍维持 30 m/s
  e         R=80 空报文       同帧同格式、无状态内容 → 应与 b 逐帧一致
  blind     R=80 报文被屏蔽   报文照发但字段不可读 → 提前降速必须消失
  nopre     无前车 无报文     无刺激对照
  nopre_msg 无前车 + 通用提示 验证空路收到提示也不制动

用法：
  python probe_message.py
  python probe_message.py --only c b d far600
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_probe_message"

# ---- 与 0.0.3b 台架一致的常量 ----
V0 = 30.0
B_COMF = 4.5
B_EMERG = 9.0
ACC_MAX = 2.6
TAU_C = 1.584
MIN_GAP = 2.5
VEH_LEN = 5.0
STEP = 0.05
T_END = 70.0
# GPT 第七十三轮：口径对齐规格（规格写 ≤ −0.1 m/s²，原脚本用 0.3）
BRAKE_THR = 0.1
EPS = 0.05

# ---- 本号专有 ----
R_MAIN = 80.0
MSG_DIST = 300.0
WRONG_NEAR = 100.0
WRONG_FAR = 600.0
GAP_INIT = 400.0

ARMS = {
    "a":         {"R": float("inf"), "msg": None,      "pre": True},
    "b":         {"R": R_MAIN,       "msg": None,      "pre": True},
    "c":         {"R": R_MAIN,       "msg": "true",    "pre": True},
    "d":         {"R": R_MAIN,       "msg": "near",    "pre": True},
    "far600":    {"R": R_MAIN,       "msg": "far",     "pre": True},
    "e":         {"R": R_MAIN,       "msg": "generic", "pre": True},
    "blind":     {"R": R_MAIN,       "msg": "masked",  "pre": True},
    "nopre":     {"R": R_MAIN,       "msg": None,      "pre": False},
    "nopre_msg": {"R": R_MAIN,       "msg": "generic", "pre": False},
}


def safe_speed(gap: float, v_lead: float, tau: float, b: float) -> float:
    """Krauss 式安全速度，与台架逐字相同。"""
    if gap <= 0:
        return 0.0
    return -b * tau + math.sqrt(max(b * b * tau * tau + v_lead * v_lead + 2.0 * b * gap, 0.0))


def run(arm: str, seed: int = 20261120) -> dict:
    cfg_arm = dict(ARMS[arm])
    R = cfg_arm["R"]
    msg_kind = cfg_arm["msg"]
    has_pre = cfg_arm["pre"]

    tmp = OUT / f"_s_{arm}_{int(seed)}"
    tmp.mkdir(parents=True, exist_ok=True)
    net = ('<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="40">'
           '<lane id="e_0" index="0" speed="40" length="9000" shape="0.00,0.00 9000.00,0.00"/>'
           '</edge><junction id="a" type="dead_end" x="0" y="0"/>'
           '<junction id="b" type="dead_end" x="9000" y="0"/></net>')
    (tmp / "net.net.xml").write_text(net, encoding="utf-8")

    x_lead = 1000.0 + GAP_INIT + VEH_LEN
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="{ACC_MAX}" decel="{B_COMF}" sigma="0"'
          f' tau="{TAU_C}" length="5" minGap="{MIN_GAP}" maxSpeed="{V0}" speedFactor="1"'
          f' actionStepLength="0.05"/>')
    lead_xml = ""
    if has_pre:
        lead_xml = (f'<vehicle id="lead" type="c" route="r" depart="0" departPos="{x_lead:.2f}"'
                    f' departSpeed="0" departLane="0"/>')
    rou = (f'<routes>{vt}<route id="r" edges="e"/>{lead_xml}'
           f'<vehicle id="foll" type="c" route="r" depart="0" departPos="1000.00"'
           f' departSpeed="{V0}" departLane="0"/></routes>')
    (tmp / "r.rou.xml").write_text(rou, encoding="utf-8")
    cfg = tmp / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.1f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "none", "--time-to-teleport", "-1"])
    rows = []          # 上报表（三位小数）
    raw = []           # 逐帧对拍表（未取整）
    cue_t = msg_t = use_t = req_t = brake_t = contact_t = None
    v_at_contact = None
    min_gap = float("inf")
    max_dec_actual = 0.0
    v_prev = None
    v_end = None
    reported_tail_x = None
    msg_state_readable = False
    snapped = False
    mode_set = False
    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 3)
            ids = traci.vehicle.getIDList()
            if has_pre and "lead" in ids:
                traci.vehicle.setSpeedMode("lead", 0)
                traci.vehicle.setSpeed("lead", 0.0)
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            if "foll" not in ids:
                break
            if not mode_set:
                traci.vehicle.setSpeedMode("foll", 0)
                mode_set = True

            xf = traci.vehicle.getLanePosition("foll")
            vf = traci.vehicle.getSpeed("foll")
            xl = float("inf")
            vl = 0.0
            gap = float("inf")
            if has_pre and "lead" in ids:
                xl = traci.vehicle.getLanePosition("lead")
                vl = traci.vehicle.getSpeed("lead")
                gap = (xl - xf) - VEH_LEN
            if gap != float("inf"):
                min_gap = min(min_gap, gap)
                if gap < 0 and contact_t is None:
                    contact_t = round(t, 2)
                    v_at_contact = round(vf, 2)

            seen = bool(gap <= R) if gap != float("inf") else False
            if seen and cue_t is None:
                cue_t = round(t, 2)

            # ---- 报文：净距首次 ≤ MSG_DIST 时投递一次性快照 ----
            if (msg_kind is not None) and (not snapped) and gap != float("inf") \
                    and gap <= MSG_DIST:
                snapped = True
                msg_t = round(t, 2)
                if msg_kind == "true":
                    reported_tail_x = xl
                    msg_state_readable = True
                elif msg_kind == "near":
                    reported_tail_x = xf + WRONG_NEAR + VEH_LEN
                    msg_state_readable = True
                elif msg_kind == "far":
                    reported_tail_x = xf + WRONG_FAR + VEH_LEN
                    msg_state_readable = True
                elif msg_kind == "generic":
                    msg_state_readable = False
                elif msg_kind == "masked":
                    reported_tail_x = None
                    msg_state_readable = False

            # ---- 行为层：目标速度（限幅前）----
            v_no_msg = V0 if not seen else min(V0, safe_speed(gap, vl, TAU_C, B_COMF))
            v_target = v_no_msg
            used_msg = False
            rgap = None
            if (not seen) and msg_state_readable and reported_tail_x is not None:
                rgap = (reported_tail_x - xf) - VEH_LEN   # 只读快照 + 自车状态
                v_msg = min(V0, safe_speed(rgap, 0.0, TAU_C, B_COMF))
                if v_msg < v_no_msg - 1e-9:
                    v_target = v_msg
                    used_msg = True
            if used_msg and use_t is None:
                use_t = round(t, 2)

            if v_target > vf:
                v_cmd = min(v_target, vf + ACC_MAX * STEP)
            else:
                v_cmd = max(v_target, vf - B_COMF * STEP)

            if req_t is None and v_target < V0 - 1e-9:
                req_t = round(t, 2)

            traci.vehicle.setSpeed("foll", v_cmd)

            if v_prev is not None:
                dec_actual = (v_prev - vf) / STEP
                max_dec_actual = max(max_dec_actual, dec_actual)
                if brake_t is None and dec_actual > BRAKE_THR:
                    brake_t = round(t, 2)
            v_prev = vf
            v_end = round(vf, 2)

            rows.append({"t": t, "gap": (None if gap == float("inf") else round(gap, 3)),
                         "seen": seen, "v_target": round(v_target, 3),
                         "v_cmd": round(v_cmd, 3), "v_actual": round(vf, 3),
                         "rgap": (None if rgap is None else round(rgap, 3)),
                         "used_msg": used_msg})
            raw.append((t, xf, vf, v_target, (None if gap == float("inf") else gap)))
    finally:
        traci.close()

    return {"arm": arm, "R": (None if R == float("inf") else R), "msg": msg_kind,
            "has_lead": has_pre,
            "cue_t": cue_t, "msg_t": msg_t, "use_t": use_t,
            "req_t": req_t, "brake_t": brake_t,
            "contact_t": contact_t, "v_at_contact": v_at_contact,
            "min_gap": (None if min_gap == float("inf") else round(min_gap, 3)),
            "max_dec_actual": round(max_dec_actual, 3), "v_end": v_end,
            "stopped": bool(v_end is not None and v_end < 0.05),
            "_rows": rows, "_raw": raw}


def at_frame(rows: list[dict], t: float) -> dict | None:
    for r in rows:
        if abs(r["t"] - t) < 1e-6:
            return r
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", default=None)
    ap.add_argument("--seed", type=int, default=20261120)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    names = args.only or list(ARMS.keys())
    res = {}
    for a in names:
        print(f"跑 {a} …", flush=True)
        r = run(a, args.seed)
        res[a] = r
        print(f"  {a}: cue={r['cue_t']} msg={r['msg_t']} use={r['use_t']} "
              f"req={r['req_t']} brake={r['brake_t']} "
              f"minGap={r['min_gap']} vContact={r['v_at_contact']} "
              f"maxDec={r['max_dec_actual']} vEnd={r['v_end']}", flush=True)

    checks = {}

    def chk(name, ok, detail):
        checks[name] = {"pass": bool(ok), "detail": detail}

    if "a" in res:
        r = res["a"]
        chk("1_A无接触且停稳", r["min_gap"] is not None and r["min_gap"] >= 0 and r["stopped"],
            f"minGap={r['min_gap']} vEnd={r['v_end']}")
    if "b" in res:
        r = res["b"]
        chk("2_B复现接触", r["min_gap"] is not None and r["min_gap"] < 0,
            f"minGap={r['min_gap']} vContact={r['v_at_contact']}")
    if "c" in res:
        r = res["c"]
        chk("3_C无接触且停稳", r["min_gap"] is not None and r["min_gap"] >= 0 and r["stopped"],
            f"minGap={r['min_gap']} vEnd={r['v_end']}")
    if "b" in res and "c" in res:
        b, c = res["b"], res["c"]
        if b["cue_t"] is not None:
            ok = all(c[k] is not None and c[k] < b["cue_t"]
                     for k in ("use_t", "req_t", "brake_t"))
            chk("4_C三个时刻早于B首次可见", ok,
                f"B cue={b['cue_t']}；C use={c['use_t']} req={c['req_t']} brake={c['brake_t']}")
            row_c = at_frame(c["_rows"], c["brake_t"]) if c["brake_t"] else None
            g_at = row_c["gap"] if row_c else None
            chk("5_C起刹时仍看不见", g_at is not None and g_at > R_MAIN,
                f"C 起刹时净距={g_at}（阈值 >{R_MAIN}）")
            fb = at_frame(b["_rows"], b["cue_t"])
            fc = at_frame(c["_rows"], b["cue_t"])
            if fb and fc and fb["gap"] and fb["gap"] > 0 and fc["gap"] and fc["gap"] > 0:
                db = fb["v_actual"] ** 2 / (2 * fb["gap"])
                dc = fc["v_actual"] ** 2 / (2 * fc["gap"])
                chk("6_同帧能力对照", db > B_COMF and dc <= B_COMF,
                    f"B {db:.2f} >4.5 且 C {dc:.2f} ≤4.5（同帧 t={b['cue_t']}）")
    if "b" in res and "e" in res:
        b, e = res["b"], res["e"]
        same = len(b["_raw"]) == len(e["_raw"]) and all(
            (rb[1] == re_[1]) and (rb[2] == re_[2]) and (rb[3] == re_[3])
            for rb, re_ in zip(b["_raw"], e["_raw"]))
        chk("7_E与B逐帧一致", same, f"帧数 {len(b['_raw'])}/{len(e['_raw'])}（未取整对拍）")
    if "a" in res and "c" in res:
        a, c = res["a"], res["c"]
        same = len(a["_raw"]) == len(c["_raw"]) and all(
            (ra[1] == rc[1]) and (ra[2] == rc[2]) and (ra[3] == rc[3])
            for ra, rc in zip(a["_raw"], c["_raw"]))
        chk("附_A与C逐帧一致（未取整）", same,
            f"帧数 {len(a['_raw'])}/{len(c['_raw'])}；req {a['req_t']}/{c['req_t']}；"
            f"peak {a['max_dec_actual']}/{c['max_dec_actual']}")
    if "blind" in res and "c" in res:
        r = res["blind"]
        chk("8a_屏蔽报文后提前降速消失",
            r["req_t"] is None or (res["c"]["req_t"] is not None and r["req_t"] > res["c"]["req_t"]),
            f"blind req={r['req_t']} vs C req={res['c']['req_t']}；"
            f"blind 与 b 同值={r['req_t'] == res.get('b', {}).get('req_t')}")
    if "d" in res and "c" in res:
        c, d = res["c"], res["d"]
        rc = at_frame(c["_rows"], c["msg_t"]) if c["msg_t"] else None
        rd = at_frame(d["_rows"], d["msg_t"]) if d["msg_t"] else None
        if rc and rd:
            chk("8b_报近使目标速度低于真报（收包帧）", rd["v_target"] < rc["v_target"] - 1e-9,
                f"t={c['msg_t']} 收包帧：真报目标 {rc['v_target']} vs 报近目标 {rd['v_target']}")
    if "far600" in res and "c" in res:
        c, f6 = res["c"], res["far600"]
        rf = at_frame(f6["_rows"], c["req_t"]) if c["req_t"] else None
        if rf:
            chk("8c_报远在真报触发帧仍维持30", abs(rf["v_target"] - V0) < 1e-6,
                f"t={c['req_t']}（真报首次触发）：报远目标 {rf['v_target']}")
    for k in ("nopre", "nopre_msg"):
        if k in res:
            r = res[k]
            chk(f"9_{k}_零制动", r["brake_t"] is None and abs(r["max_dec_actual"]) < 0.01,
                f"brake={r['brake_t']} maxDec={r['max_dec_actual']} vEnd={r['v_end']}")

    print("\n=== 判据 ===")
    for k, v in checks.items():
        print(f"  {'✅' if v['pass'] else '❌'} {k}：{v['detail']}")

    out = {"seed": args.seed,
           "config": {"V0": V0, "B_COMF": B_COMF, "TAU": TAU_C, "STEP": STEP,
                      "R_main": R_MAIN, "MSG_DIST": MSG_DIST, "GAP_INIT": GAP_INIT,
                      "BRAKE_THR": BRAKE_THR, "REV": "gpt73 口径对齐"},
           "arms": {k: {kk: vv for kk, vv in v.items() if kk not in ("_rows", "_raw")}
                    for k, v in res.items()},
           "checks": checks}
    (OUT / "probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
    print(f"\nwritten: {OUT/'probe.json'}")
    n_pass = sum(1 for v in checks.values() if v["pass"])
    print(f"判据 {n_pass}/{len(checks)} 通过")
    return 0 if n_pass == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
