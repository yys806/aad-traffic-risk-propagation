"""证明「加了消息接口但关闭时」与冻结内核逐元素零差异（目标书 v2 §7.1 第 5 条）

三组场景，逐元素比较：hist_x / hist_v / hist_a / max_drac / min_gap / event / arrival / drac。
任何一项非零即失败（退出码 1）。
"""
import sys, json
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
import numpy as np
import hdm_core_v2 as H
from hdm_msg import MsgState

CFG = dict(N=100, hw=45.0, n_a=1, Tprime=1.0, bmax=9.0, warm=40.0, observe=60.0)
CASES = [
    ("source_noise", dict(v_target=3.0, noise=True, seed=0)),
    ("control_noise", dict(v_target=None, noise=True, seed=0)),
    ("source_clean", dict(v_target=3.0, noise=False, seed=0)),
]


def maxdiff(a, b):
    a = np.asarray(a); b = np.asarray(b)
    if a.shape != b.shape:
        return float("inf")
    return float(np.max(np.abs(a - b))) if a.size else 0.0


def main():
    rep = {}
    ok_all = True
    for name, extra in CASES:
        r_off = H.run(**CFG, record=True, drac_log=True, msg_state=None, **extra)
        # 建一个"送达时刻晚于仿真结束"的消息对象，等价于全程不生效
        ms = MsgState(receivers=[60], t_deliver=1e9, factor=0.7, rate=1.0, N=100)
        r_late = H.run(**CFG, record=True, drac_log=True, msg_state=ms, **extra)
        d = {}
        for k in ("hist_x", "hist_v", "hist_a", "drac"):
            d[k] = maxdiff(r_off[k], r_late[k])
        for k in ("max_drac", "min_gap"):
            d[k] = maxdiff(np.asarray(r_off[k])[1:], np.asarray(r_late[k])[1:])
        d["event_equal"] = bool(np.array_equal(r_off["event"], r_late["event"]))
        d["arrival_equal"] = bool(np.array_equal(
            np.nan_to_num(r_off["arrival"], nan=-1), np.nan_to_num(r_late["arrival"], nan=-1)))
        worst = max(d[k] for k in ("hist_x", "hist_v", "hist_a", "drac", "max_drac", "min_gap"))
        d["worst"] = worst
        d["pass"] = bool(worst == 0.0 and d["event_equal"] and d["arrival_equal"])
        ok_all = ok_all and d["pass"]
        rep[name] = d
        print(name, json.dumps(d, ensure_ascii=False), flush=True)
    rep["_ALL_PASS"] = ok_all
    json.dump(rep, open("verify_msg_noop.json", "w"), indent=1, ensure_ascii=False)
    print("ALL_PASS", ok_all, flush=True)
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()