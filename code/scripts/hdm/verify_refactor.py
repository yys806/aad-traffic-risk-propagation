"""证明抽取共享件不改变冻结参考：逐元素比对 v1（hdm_core）与 v2（hdm_core_v2）

比对三组：
  base_source_nonoise  有源 / 无噪声 / seed0
  base_control_nonoise 对照 / 无噪声 / seed0
  base_source_seed0    有源 / 有噪声 / seed0
逐元素断言：hist_x / hist_v / hist_a / max_drac / min_gap / event / arrival 全等（0 容差）。
"""
import sys, json
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
import numpy as np
import hdm_core as H1
import hdm_core_v2 as H2

CFG = dict(N=100, hw=45.0, n_a=1, Tprime=1.0, bmax=9.0, warm=40.0, observe=300.0)
cases = [
    ("base_source_nonoise", dict(v_target=3.0, noise=False, seed=0)),
    ("base_control_nonoise", dict(v_target=None, noise=False, seed=0)),
    ("base_source_seed0", dict(v_target=3.0, noise=True, seed=0)),
]

report = {}
all_ok = True
for name, extra in cases:
    r1 = H1.run(**CFG, record=True, **extra)
    r2 = H2.run(**CFG, record=True, **extra)
    d = {}
    for key in ("hist_x", "hist_v", "hist_a"):
        a = r1[key]; b = r2[key]
        d[key] = float(np.max(np.abs(a - b)))
    for key in ("max_drac", "min_gap"):
        a = np.asarray(r1[key])[1:]; b = np.asarray(r2[key])[1:]   # 车 0 无前车，恒 inf
        if np.any(np.isnan(a)) or np.any(np.isnan(b)):
            d[key] = float("nan")
        else:
            d[key] = float(np.max(np.abs(a - b)))
    d["event_equal"] = bool(np.array_equal(r1["event"], r2["event"]))
    d["arrival_equal"] = bool(np.array_equal(np.nan_to_num(r1["arrival"], nan=-1),
                                             np.nan_to_num(r2["arrival"], nan=-1)))
    d["preclip_min_diff"] = float(abs(r1["preclip_min"] - r2["preclip_min"]))
    d["preclip_steps_diff"] = int(r1["preclip_steps"] - r2["preclip_steps"])
    d["v_eq_diff"] = float(abs(r1["v_eq"] - r2["v_eq"]))
    worst = max(d[k] for k in ("hist_x", "hist_v", "hist_a", "max_drac", "min_gap"))
    d["all_zero"] = bool(worst == 0.0 and d["event_equal"] and d["arrival_equal"]
                         and d["preclip_steps_diff"] == 0 and d["v_eq_diff"] == 0.0)
    all_ok = all_ok and d["all_zero"]
    report[name] = d
    print(name, json.dumps(d, ensure_ascii=False), flush=True)

report["_ALL_PASS"] = all_ok
json.dump(report, open("refactor_equivalence.json", "w"), indent=1, ensure_ascii=False)
print("ALL_PASS", all_ok)
sys.exit(0 if all_ok else 1)
