"""0.5.0 硬判据 #1 补证：消息载荷是否真的进入并支配控制行为

Gemini 第二轮指出载荷是死元数据；第三轮指出我上一版的补丁**只证明了 1 个符号位**
（x_src 在车前/车后），把 t_src 改成未来、v_src 改成负数都能静默通过。

本探针因此测六项，判据全部落盘到 JSON：
  T1 正确载荷           → 8 车全部适用、cap_bind 全 > 0、轨迹与无消息不同
  T2 x_src 改到车后方   → 适用性门拒绝、cap_bind 全 0、轨迹与无消息**逐位相同**
  T3 t_src 改成未来     → 构造期 AssertionError
  T4 v_src 改成负数     → 构造期 AssertionError
  T5 v_src 改成荒谬高速 → 构造期 AssertionError
  T6 载荷送达 ≠ 状态机  → 构造期 AssertionError
"""
import sys
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
import json
import numpy as np
import hdm_core_v2 as H
from hdm_msg import MsgState, Message

DT, N, HW, TP, BMAX = 0.05, 100, 45.0, 1.0, 9.0
WARM, RAMP, OBS, VTGT, X0 = 40.0, 6.0, 60.0, 3.0, 5000.0
RECV = [20, 30, 40, 50, 60, 70, 80, 90]
T_SRC, T_DEL = 40.25, 40.85
X_SRC, V_SRC = 5889.56, 21.4661
COMMON = dict(N=N, hw=HW, n_a=1, Tprime=TP, ramp=RAMP, warm=WARM, observe=OBS,
              noise=True, bmax=BMAX, record=True, drac_log=True, x0=X0)

fails, rows = [], []


def run_with(x_src, t_src=T_SRC, v_src=V_SRC, msg_tdel=None):
    msg = Message(event_id=0, t_src=t_src, x_src=x_src, v_src=v_src,
                  receivers=RECV, t_deliver=(T_DEL if msg_tdel is None else msg_tdel))
    ms = MsgState(receivers=RECV, t_deliver=T_DEL, N=N, message=msg)
    return H.run(seed=0, v_target=VTGT, msg_state=ms, **COMMON), ms


rN = H.run(seed=0, v_target=VTGT, **COMMON)       # 无消息基准

# T1 正确载荷
r1, ms1 = run_with(X_SRC)
b1 = ms1.cap_bind_frames[RECV]
rows.append(dict(test="T1_correct", cap_bind=b1.tolist(),
                 all_bound=bool(np.all(b1 > 0)),
                 differs_from_no_message=not bool(np.array_equal(r1["hist_v"], rN["hist_v"])),
                 v_cap={int(i): float(ms1.v_cap[i]) for i in RECV}))
if not np.all(b1 > 0):
    fails.append("T1 控速未介入")
if np.array_equal(r1["hist_v"], rN["hist_v"]):
    fails.append("T1 与无消息相同，消息无效")

# T2 载荷 x_src 在车后方
r2, ms2 = run_with(-9999.0)
b2 = ms2.cap_bind_frames[RECV]
rows.append(dict(test="T2_x_src_behind", cap_bind=b2.tolist(),
                 all_rejected=bool(np.all(ms2.rejected[RECV])),
                 equals_no_message=bool(np.array_equal(r2["hist_v"], rN["hist_v"]))))
if np.any(b2 > 0):
    fails.append("T2 坏载荷仍触发控速")
if not np.all(ms2.rejected[RECV]):
    fails.append("T2 未被适用性门拒绝")
if not np.array_equal(r2["hist_v"], rN["hist_v"]):
    fails.append("T2 与无消息不逐位相同")


def expect_raise(label, **kw):
    try:
        run_with(**kw)
        rows.append(dict(test=label, raised=False))
        fails.append(f"{label} 未抛错（载荷篡改被静默接受）")
    except AssertionError as e:
        rows.append(dict(test=label, raised=True, msg=str(e)[:140]))


expect_raise("T3_t_src_future", x_src=X_SRC, t_src=999999.0)
expect_raise("T4_v_src_negative", x_src=X_SRC, v_src=-500.0)
expect_raise("T5_v_src_absurd", x_src=X_SRC, v_src=1e4)
expect_raise("T6_t_deliver_mismatch", x_src=X_SRC, msg_tdel=999.0)

out = dict(case="payload_causality", rows=rows, fails=fails, ok=(len(fails) == 0))
json.dump(out, open("probe_payload_causal.json", "w"), indent=1, ensure_ascii=False)
for r in rows:
    print(json.dumps(r, ensure_ascii=False), flush=True)
print(json.dumps(dict(ok=out["ok"], n_fail=len(fails), fails=fails), ensure_ascii=False))
if fails:
    sys.exit(1)
print("PAYLOAD CAUSALITY PASS (6/6)")
