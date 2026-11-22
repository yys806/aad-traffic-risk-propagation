"""0.5.0 硬判据 #1 补证：消息载荷是否真的进入控制流（因果性探针）

Gemini/GPT 2026-11-22 审计共同指出：原版 MsgState 的 Message 载荷是**死元数据**——
apply() 零行读取它，把 x_src 改成 -9999 也不会改变任何仿真结果，
所谓"五环溯源"因此只是装饰。

本探针用三个变体证明载荷现在是因果的：
  P0 正确载荷            → 适用，控速介入
  P1 x_src 改到车后方     → 被适用性门拒绝，结果应与"无消息"逐位相同
  P2 t_src 与 t_deliver 矛盾 → 构造期断言直接抛出

判据（任一不满足即非零退出）：
  A. P0 的 cap_bind_frames 全 > 0
  B. P1 的 cap_bind_frames 全 = 0，且 rejected 全 True
  C. P1 的 hist_x/hist_v/hist_a 与"无消息"逐位相同
  D. P2 必须抛 AssertionError
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

fails = []


def go(x_src, t_del):
    msg = Message(event_id=0, t_src=T_SRC, x_src=x_src, v_src=V_SRC,
                  receivers=RECV, t_deliver=t_del)
    ms = MsgState(receivers=RECV, t_deliver=t_del, N=N, message=msg)
    r = H.run(seed=0, v_target=VTGT, msg_state=ms, **COMMON)
    return r, ms


# P0 正确载荷
r0, ms0 = go(X_SRC, T_DEL)
bind0 = ms0.cap_bind_frames[RECV]
print(json.dumps(dict(P0_cap_bind=bind0.tolist(), P0_realized=bool(np.all(bind0 > 0))),
                 ensure_ascii=False), flush=True)
if not np.all(bind0 > 0):
    fails.append("P0 控速未介入")

# P1 载荷 x_src 改到车后方（事件在车后面，不适用于前方预警）
r1, ms1 = go(-9999.0, T_DEL)
bind1 = ms1.cap_bind_frames[RECV]
rej1 = ms1.rejected[RECV]
print(json.dumps(dict(P1_cap_bind=bind1.tolist(), P1_all_rejected=bool(np.all(rej1))),
                 ensure_ascii=False), flush=True)
if np.any(bind1 > 0):
    fails.append("P1 坏载荷仍触发控速")
if not np.all(rej1):
    fails.append("P1 坏载荷未被适用性门拒绝")

# 无消息对照
rN = H.run(seed=0, v_target=VTGT, **COMMON)
same = all(bool(np.array_equal(r1[k], rN[k])) for k in ("hist_x", "hist_v", "hist_a"))
print(json.dumps(dict(P1_equals_no_message=same), ensure_ascii=False), flush=True)
if not same:
    fails.append("P1 与无消息不逐位相同")

# P0 与无消息必须不同（否则消息无效）
differs = not bool(np.array_equal(r0["hist_v"], rN["hist_v"]))
print(json.dumps(dict(P0_differs_from_no_message=differs), ensure_ascii=False), flush=True)
if not differs:
    fails.append("P0 与无消息相同，消息无效")

# P2 载荷与状态机矛盾必须抛错
try:
    bad = Message(event_id=0, t_src=T_SRC, x_src=X_SRC, v_src=V_SRC,
                  receivers=RECV, t_deliver=999.0)
    MsgState(receivers=RECV, t_deliver=T_DEL, N=N, message=bad)
    print(json.dumps(dict(P2_raised=False), ensure_ascii=False), flush=True)
    fails.append("P2 矛盾载荷未抛错")
except AssertionError as e:
    print(json.dumps(dict(P2_raised=True, P2_msg=str(e)[:120]), ensure_ascii=False), flush=True)

out = dict(case="payload_causality", fails=fails, ok=(len(fails) == 0))
json.dump(out, open("probe_payload_causal.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, ensure_ascii=False))
if fails:
    sys.exit(1)
print("PAYLOAD CAUSALITY PASS")
