"""探针：实测各臂送达时刻的 v_cap（0.70 × 送达瞬间车速），用于图注核实。
A0 轨迹与臂无关，每种子只算一次并复用。
"""
import json
import sys

import numpy as np

sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
import hdm_core_v2 as H      # noqa: E402

CFG = dict(noise=True, bmax=9.0, record=True, drac_log=True, x0=5000.0)
FACTOR = 0.70
DT = 0.05
SRC = r"D:/shen/TJU/AAD/code/scripts/hdm/recon_050_a2s.json"


def base_cache(seed):
    a0 = H.run(seed=seed, v_target=3.0, **CFG)
    return a0["hist_v"], a0["hist_x"]


if __name__ == "__main__":
    d = json.load(open(SRC, encoding="utf-8"))
    res = {}
    for seed in range(10):
        hv, hx = base_cache(seed)
        for arm in ("A2", "A2S", "A2P"):
            m = d["seeds"][str(seed)]["arms"][arm]["msg"]
            out = {}
            for car, t in m["t_deliver_per_car"].items():
                if t is None:
                    continue
                k = min(max(int(round(t / DT)), 0), hv.shape[0] - 1)
                c = int(car)
                out[int(car)] = dict(t_deliver=float(t), v_at=float(hv[k, c]),
                                     v_cap=float(FACTOR * hv[k, c]),
                                     x_at=float(hx[k, c]))
            res.setdefault(arm, {})[str(seed)] = out
        print(f"seed {seed} done", flush=True)

    for arm in res:
        allv = [v["v_cap"] for s in res[arm].values() for v in s.values()]
        allt = [v["t_deliver"] for s in res[arm].values() for v in s.values()]
        print(f"{arm:4} v_cap {min(allv):.2f} – {max(allv):.2f} m/s "
              f"(median {np.median(allv):.2f})   t_deliver {min(allt):.2f} – {max(allt):.2f} s")
    json.dump(res, open(r"D:/shen/TJU/AAD/code/scripts/hdm/probe_vcap.json", "w"), indent=1)
    print("saved probe_vcap.json")