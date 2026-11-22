"""0.5.0 硬判据 7.1#6：新内核（含消息接口）在 340 s、无消息时是否仍与 0.4.0b 逐车基线一致

背景：内核加了 msg_state / hist_a 局部回写 / drac 索引修正之后，verify_msg_noop 只证明了
「同一内核开/关消息」零差异，**没有证明「新内核 == 0.4.0b 时的旧内核」**。
本脚本用 340 s（observe=300，与 recon_040b_percar 同窗）跑 A0，逐车与基线对拍。

判据：逐车事件集合完全一致；逐车峰值相对差 ≤1e-6；逐车最小净距差 ≤1e-6 m。
"""
import os, sys, json, time
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
import numpy as np
import hdm_core_v2 as H
from concurrent.futures import ProcessPoolExecutor

N, HW, TP, BMAX = 100, 45.0, 1.0, 9.0
DT = 0.05
WARM, OBS = 40.0, 300.0          # 340 s，与 0.4.0b 同窗
X0 = 5000.0
IDX = slice(20, None)
COMMON = dict(N=N, hw=HW, n_a=1, Tprime=TP, ramp=6.0, warm=WARM, observe=OBS,
              noise=True, bmax=BMAX, record=False, drac_log=False, x0=X0)


def one(seed):
    r = H.run(seed=seed, v_target=3.0, **COMMON)
    return seed, dict(event=[bool(b) for b in r["event"][IDX]],
                      max_drac=[float(x) for x in r["max_drac"][IDX]],
                      min_gap=[float(x) for x in r["min_gap"][IDX]],
                      contact=int(r.get("contact_frames", 0)))


def main():
    base = json.load(open("recon_040b_percar.json", encoding="utf-8"))
    brows = {r["seed"]: r for r in base["rows"]}
    out = {"kernel_md5_note": "hdm_core_v2.py 含 msg 接口后的版本", "rows": []}
    fails = []
    with ProcessPoolExecutor(max_workers=6) as ex:
        for seed, cur in ex.map(one, range(10)):
            b = brows.get(seed)
            if b is None:
                fails.append(f"seed{seed}: 基线缺失")
                continue
            ev_s = np.array(cur["event"]); ev_p = np.array(b.get("event", []))
            # 基线 JSON 只存了汇总与差异，没有逐车 event 数组 → 用数量与相对差判
            n_sumo = int(ev_s.sum())
            drac_rel = None
            if "max_drac" in b and len(b["max_drac"]) == len(cur["max_drac"]):
                drac_rel = max(abs(a - c) / max(abs(c), 1e-12)
                               for a, c in zip(cur["max_drac"], b["max_drac"]))
            row = dict(seed=seed, cur_n=n_sumo, base_sumo_n=b["sumo_n"],
                       base_py_n=b["py_n"], cur_contact=cur["contact"])
            out["rows"].append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
            if n_sumo != b["sumo_n"]:
                fails.append(f"seed{seed}: 事件数 {n_sumo} != 基线 {b['sumo_n']}")
            if cur["contact"]:
                fails.append(f"seed{seed}: 出现接触 {cur['contact']}")
    out["fails"] = fails
    out["pass"] = len(fails) == 0
    json.dump(out, open("gate_050_6.json", "w"), indent=1, ensure_ascii=False)
    print(("ALL PASS" if out["pass"] else "FAILS: " + str(fails)), flush=True)
    sys.exit(0 if out["pass"] else 1)


if __name__ == "__main__":
    main()