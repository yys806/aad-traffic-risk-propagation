"""抽取共享步进前的基线快照（用于证明「抽取不改冻结参考」）

跑三组，存 npz：
  base_source_nonoise  100 车 / 45 m / T'=1.0 / bmax 9 / 无噪声 / 有源事件
  base_control_nonoise 同上，对照臂
  base_source_seed0    同上，加噪声 seed0（对应 0.3.5 §4.3 的 78/80、峰值 7.37、净距 2.46）
"""
import sys, json
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
import numpy as np
import hdm_core as H

CFG = dict(N=100, hw=45.0, n_a=1, Tprime=1.0, bmax=9.0, warm=40.0, observe=300.0)

cases = [
    ("base_source_nonoise", dict(v_target=3.0, noise=False, seed=0)),
    ("base_control_nonoise", dict(v_target=None, noise=False, seed=0)),
    ("base_source_seed0", dict(v_target=3.0, noise=True, seed=0)),
]
out = {}
for name, extra in cases:
    r = H.run(**CFG, record=True, **extra)
    np.savez_compressed(name + ".npz",
                        hist_x=r["hist_x"], hist_v=r["hist_v"], hist_a=r["hist_a"],
                        max_drac=r["max_drac"], min_gap=r["min_gap"],
                        event=r["event"], arrival=r["arrival"])
    out[name] = dict(events_80=int(r["event"][20:].sum()),
                     events_all=int(r["event"][1:].sum()),
                     peak=float(np.nanmax(r["max_drac"][1:])),
                     min_gap=float(np.min(r["min_gap"][1:])),
                     preclip_min=float(r["preclip_min"]),
                     preclip_steps=int(r["preclip_steps"]),
                     v_eq=float(r["v_eq"]))
    print(name, json.dumps(out[name], ensure_ascii=False), flush=True)
json.dump(out, open("baseline_before_refactor.json", "w"), indent=1, ensure_ascii=False)
print("DONE")
