"""AAD 0.5.0 共享件：消息响应 + 事件去重

设计原则（R08 / 0.4.0 教训）：
  · 不另写一份循环体。Python 内核与 SUMO 桥接都调用这里的函数。
  · 默认关闭时必须是**零副作用**——由 verify_msg_noop.py 逐元素证明。

消息语义（目标书 §四）：
  · 触发：头车速度首次低于 v_eq-0.5 的那一步 = t_src（外部给定）
  · 送达：t_deliver = t_src + 0.6 s（预锁常量）
  · 响应：v_cap = factor × v(接收时刻)；下降速率限幅 rate m/s²
  · 每步：v_allowed = max(v_cap, v_prev - rate·dt)；v_new = min(v_new_HDM, v_allowed)
    —— 该车自己更猛的刹车不被削弱
"""
import numpy as np

DRAC_TH = 3.4
DRAC_MIN_DUR = 0.2


class Message:
    """一条可追溯的预警消息（目标书 v3 §4.1：载荷只含事实，不下发命令）。

    五环溯源的载体：源事件事实 → 载荷 → 送达回执 → 控速介入 → 动作确认。
    """

    def __init__(self, event_id, t_src, x_src, v_src, receivers,
                 t_deliver, factor=0.70, rate=1.0):
        self.event_id = int(event_id)
        self.t_src = float(t_src)
        self.x_src = float(x_src)
        self.v_src = float(v_src)
        self.receivers = list(receivers)
        self.t_deliver = float(t_deliver)
        # 车端本地响应策略（不是载荷内容）
        self.factor = float(factor)
        self.rate = float(rate)

    def payload(self):
        """对外可审计的载荷：只含事实字段。"""
        return dict(event_id=self.event_id, t_src=self.t_src,
                    x_src=self.x_src, v_src=self.v_src)

    def as_dict(self):
        return dict(payload=self.payload(), receivers=self.receivers,
                    t_deliver=self.t_deliver,
                    local_policy=dict(factor=self.factor, rate=self.rate))


class MsgState:
    """消息状态机。一条消息 = 一批接收车 + 送达时刻 + 速度因子 + 下降速率上限。"""

    def __init__(self, receivers, t_deliver, factor=0.70, rate=1.0, N=100, message=None):
        self.receivers = list(receivers)
        self.t_deliver = float(t_deliver)
        self.factor = float(factor)
        self.rate = float(rate)
        self.N = N
        self.v_cap = np.full(N, np.nan)      # 每辆接收车的速度上限，接收时刻冻结
        self.delivered = False
        self.t_action = np.full(N, np.nan)   # 首次"消息真的改变了指令"的时刻
        self.cap_bind_frames = np.zeros(N, dtype=int)
        # 五环溯源：载荷对象 + 逐车送达回执
        self.message = message if message is not None else Message(
            event_id=0, t_src=np.nan, x_src=np.nan, v_src=np.nan,
            receivers=receivers, t_deliver=t_deliver, factor=factor, rate=rate)
        self.delivered_at = np.full(N, np.nan)   # 第 3 环：逐车送达时刻
        self.v_at_delivery = np.full(N, np.nan)  # 送达时该车速度（载荷用途）
        self.applicable = np.zeros(N, dtype=bool)  # 载荷适用性（x_src 在该车前方）
        self.rejected = np.zeros(N, dtype=bool)    # 被适用性门拒绝的车
        # 载荷与状态机的一致性硬断言（Gemini：原版二者可各说各话）
        if message is not None:
            assert list(message.receivers) == list(receivers), \
                f"载荷接收车 {message.receivers} 与状态机 {receivers} 不一致"
            assert abs(message.t_deliver - t_deliver) < 1e-9, \
                f"载荷送达时刻 {message.t_deliver} 与状态机 {t_deliver} 不一致"

    def apply(self, v_new, v_prev, t, dt, x=None):
        """在 HDM 算出 v_new 之后调用。t 必须是**步末时刻** (k+1)·dt。

        载荷因果性（Gemini 审计 2026-11-22 指出原版载荷是死元数据）：
          · 适用性判定**必须读 self.message.x_src**——只有当源事件在该车前方
            （x_src > x_self + 1.0 m）时消息才被采纳；否则视为不适用、不控速。
          · 因此把载荷的 x_src 改坏会改变行为，由 probe_payload_causal.py 实测证明。

        返回 (v_new, modified)：modified 是布尔数组，标记本步被消息真正限速的车。
        未被限速的车 v_new 保持逐位不变 —— 这是「关闭时零副作用」的基础。
        """
        modified = np.zeros(self.N, dtype=bool)
        if t < self.t_deliver - 1e-12:
            return v_new, modified
        if not self.delivered:
            if x is None:
                raise ValueError("apply() 需要 x 才能做载荷适用性判定")
            for i in self.receivers:
                self.applicable[i] = bool(self.message.x_src > float(x[i]) + 1.0)
                if not self.applicable[i]:
                    self.rejected[i] = True
                    continue
                self.v_cap[i] = self.factor * float(v_prev[i])
                self.delivered_at[i] = t          # 第 3 环：送达回执
                self.v_at_delivery[i] = float(v_prev[i])
            self.delivered = True
        for i in self.receivers:
            if not self.applicable[i]:
                continue
            v_allowed = max(self.v_cap[i], float(v_prev[i]) - self.rate * dt)
            if v_new[i] > v_allowed + 1e-15:
                v_new[i] = v_allowed
                modified[i] = True
                self.cap_bind_frames[i] += 1
                if np.isnan(self.t_action[i]):
                    self.t_action[i] = t          # 第 4 环：控速介入时刻
        return v_new, modified

    def trace(self):
        """五环溯源（逐车）：源事件 → 载荷 → 送达 → 控速介入 → 动作确认。"""
        return dict(
            ring1_event=dict(event_id=self.message.event_id),
            ring2_payload=self.message.payload(),
            ring3_delivered={int(i): (None if np.isnan(self.delivered_at[i]) else float(self.delivered_at[i]))
                             for i in self.receivers},
            ring4_cap_bind={int(i): int(self.cap_bind_frames[i]) for i in self.receivers},
            ring4_first_time={int(i): (None if np.isnan(self.t_action[i]) else float(self.t_action[i]))
                              for i in self.receivers},
            applicable={int(i): bool(self.applicable[i]) for i in self.receivers},
            rejected_by_applicability=[int(i) for i in self.receivers if self.rejected[i]],
            # 第 5 环「动作确认」由轨迹差分在 run_050_python 里注入，此处不自行声称
            ring5_action=None,
            v_cap={int(i): (None if np.isnan(self.v_cap[i]) else float(self.v_cap[i]))
                   for i in self.receivers},
            v_at_delivery={int(i): (None if np.isnan(self.v_at_delivery[i]) else float(self.v_at_delivery[i]))
                           for i in self.receivers})

    def summary(self):
        return dict(receivers=self.receivers, t_deliver=self.t_deliver,
                    factor=self.factor, rate=self.rate, trace=self.trace(),
                    t_action={int(i): (None if np.isnan(self.t_action[i]) else float(self.t_action[i]))
                              for i in self.receivers},
                    cap_bind_frames={int(i): int(self.cap_bind_frames[i]) for i in self.receivers})


def count_episodes(drac_series, dt, th=DRAC_TH, min_dur=DRAC_MIN_DUR, merge_gap_s=0.30):
    """把一条 DRAC 时间序列切成"超阈片段"，返回合格片段列表。

    一次事件 = 合并短间隙后仍持续 >= min_dur 的片段。
    merge_gap_s: 允许合并的两段之间的最大间隔秒数（预锁 0.30 s，另报 0 作敏感性）。

    注意：帧 k 的 DRAC 代表 [k·dt, (k+1)·dt)；片段长度 = 帧数 × dt。
    """
    mask = np.asarray(drac_series) >= th
    n = len(mask)
    merge_frames = int(round(merge_gap_s / dt))
    # 1) 先找极大连续段
    raw = []
    k = 0
    while k < n:
        if mask[k]:
            j = k
            while j < n and mask[j]:
                j += 1
            raw.append([k, j - 1])
            k = j
        else:
            k += 1
    # 2) 合并间隔 <= merge_frames 的相邻段
    merged = []
    for seg in raw:
        if merged and seg[0] - merged[-1][1] - 1 <= merge_frames:
            merged[-1][1] = seg[1]
        else:
            merged.append([seg[0], seg[1]])
    # 3) 过滤：按**有效超阈帧数** >= min_frames，而不是总跨度
    #    （总跨度会把"两个单帧毛刺夹 6 帧低谷"拼成假事件）
    min_frames = int(round(min_dur / dt))
    runs = []
    for a, b in merged:
        n_valid = int(np.sum(mask[a:b + 1]))
        if n_valid >= min_frames:
            runs.append((a, b, n_valid * dt))
    return runs


def episode_stats(drac_hist, dt, cars):
    """对多辆车统计去重事件数。

    drac_hist: (steps+1, N) 的逐帧 DRAC 数组
    cars: 参与统计的车号序列（如 range(20,100)）
    返回 dict：每车事件数、总事件数、每车最长事件时长
    """
    per_car = {}
    total = 0
    for i in cars:
        runs = count_episodes(drac_hist[:, i], dt)
        per_car[int(i)] = dict(n=len(runs), durations=[float(d) for _, _, d in runs])
        total += len(runs)
    return dict(total=total, per_car=per_car)


def frame_drac(x, v, dt_unused=None):
    """逐帧 DRAC：仅当 gap>0 且 dv>0 时取 dv^2/(2 gap)，否则 0。返回长度 N 的向量（车 0 为 0）。"""
    N = len(x)
    out = np.zeros(N)
    for i in range(1, N):
        gap = x[i - 1] - x[i] - 5.0
        dv = v[i] - v[i - 1]
        if gap > 0 and dv > 0:
            out[i] = dv * dv / (2.0 * gap)
    return out