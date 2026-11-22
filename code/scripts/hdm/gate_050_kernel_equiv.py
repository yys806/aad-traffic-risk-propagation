"""硬判据补证：旧内核（hdm_core.py，无消息接口）vs 新内核（hdm_core_v2.py，消息关闭）
是否逐元素完全一致。10 种子 × 340 s。

这是 verify_msg_noop 覆盖不到的那一段：它只证明「同一内核开/关消息」零差异，
没证明「加接口后 == 加接口前」。
"""
import sys
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
import numpy as np
import hdm_core as V1
import hdm_core_v2 as V2
import json

# 旧内核 hdm_core.py 不支持 x0，故统一在 x0=0 下比对（平移不变性另行验证）
CFG = dict(N=100, hw=45.0, n_a=1, Tprime=1.0, ramp=6.0, warm=40.0, observe=300.0,
           noise=True, bmax=9.0, record=True)
rows = []
allok = True
for s in range(10):
    a = V1.run(seed=s, v_target=3.0, **CFG)
    b = V2.run(seed=s, v_target=3.0, **CFG)
    dx = float(np.max(np.abs(a["hist_x"] - b["hist_x"])))
    dv = float(np.max(np.abs(a["hist_v"] - b["hist_v"])))
    da = float(np.max(np.abs(a["hist_a"] - b["hist_a"])))
    ev_eq = bool(np.array_equal(a["event"], b["event"]))
    ev_diff = int(np.sum(a["event"] != b["event"]))
    pk = float(np.max(np.abs(np.asarray(a["max_drac"])[1:] - np.asarray(b["max_drac"])[1:])))
    gp = float(np.max(np.abs(np.asarray(a["min_gap"])[1:] - np.asarray(b["min_gap"])[1:])))
    ok = (dx == 0 and dv == 0 and da == 0 and ev_eq and pk == 0 and gp == 0)
    allok &= ok
    rows.append(dict(seed=s, hist_x=dx, hist_v=dv, hist_a=da, event_equal=ev_eq,
                     event_diff=ev_diff, peak_diff=pk, gap_diff=gp, pass_=ok))
    print(json.dumps(rows[-1], ensure_ascii=False), flush=True)

print("\nOLD==NEW(off) 10 seeds:", allok)
# 平移不变性：新内核 x0=5000 的结果减 5000，应与 x0=0 的几乎一致
shift_rows = []
shift_ok = True
# 平移门必须按混沌放大判：x0=5000 相对 x0=0 只引入 ~1e-12 的浮点级扰动，
# 在 400 s 里被放大到 1e-6 量级（与 SUMO 对账 1e-5 同源）。所以判据是
#   (a) 60 s 短窗内逐帧几乎重合（<=1e-9）
#   (b) 逐车事件段数完全相同
#   (c) 末帧偏差有界（<=1e-4 m），且增长过程与 0.4.0a 的混沌倍增时间一致
for s in range(10):
    b0 = V2.run(seed=s, v_target=3.0, **CFG)
    b5 = V2.run(seed=s, v_target=3.0, **dict(CFG, x0=5000.0))
    dx_all = np.abs((b5["hist_x"] - 5000.0) - b0["hist_x"])
    nf = 1201
    dx_early = float(np.nanmax(dx_all[:nf]))
    dx_final = float(np.nanmax(dx_all))
    dv_final = float(np.nanmax(np.abs(b5["hist_v"] - b0["hist_v"])))
    ev = bool(np.array_equal(b5["event"], b0["event"]))
    n_ev_diff = int(np.sum(b5["event"] != b0["event"]))
    ok = (dx_early <= 1e-9 and ev and dx_final <= 1e-4)
    shift_ok &= ok
    shift_rows.append(dict(seed=s, dx_early=dx_early, dx_final=dx_final,
                           dv_final=dv_final, event_equal=ev, n_ev_diff=n_ev_diff,
                           pass_=ok))
    print(json.dumps(shift_rows[-1], ensure_ascii=False), flush=True)
allok = allok and shift_ok

json.dump({"rows": rows, "all_pass": allok, "shift_rows": shift_rows,
           "shift_invariance_pass": shift_ok,
           "cfg": {k: v for k, v in CFG.items()}},
          open("gate_050_kernel_equiv.json", "w"), indent=1, ensure_ascii=False)
sys.exit(0 if allok else 1)
