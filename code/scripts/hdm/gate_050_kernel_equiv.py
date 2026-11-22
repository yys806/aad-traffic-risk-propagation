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
json.dump({"rows": rows, "all_pass": allok}, open("gate_050_kernel_equiv.json", "w"),
          indent=1, ensure_ascii=False)
sys.exit(0 if allok else 1)
