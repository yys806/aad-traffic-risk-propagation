# AAD Stage 0.2 Task 2.5.2：关键差异案例分析

## 结论摘要

本轮从 Task 2.5.1 的完整事件成员表确定性筛选 11 个关键案例：P2 触发而 P1 不触发 3 个，P3 触发而 P2 不触发 3 个，三套规则均触发且确认时间差异较大的 5 个。所有案例覆盖 source 作用域，中心行号精确匹配；同一车辆对 ±3 s 内的其他事件作为 `nearby_event_count` 单独记录。

三规则均触发案例的绝对确认时刻如下：
- lankershim__complete 原始行 340401：P1/P2/P3 确认时刻 557.3/553.9/553.8 s。
- us101__0750_0805 原始行 1094141：P1/P2/P3 确认时刻 844.0/843.4/841.1 s。
- us101__0805_0820 原始行 1070807：P1/P2/P3 确认时刻 720.6/720.0/717.8 s。
- us101__0820_0835 原始行 292135：P1/P2/P3 确认时刻 205.2/203.1/202.4 s。
- lankershim__complete 原始行 76650：P1/P2/P3 确认时刻 152.2/150.6/149.4 s。

## 中心事件口径

中心事件只有在中心 `original_row_number` 属于该规则事件的成员集合时才计为触发。附近事件不会改变中心触发状态；这修正了旧案例分析中“局部窗口内有事件即归因于中心帧”的风险。每个案例 `center_event_membership_verified=True`，物理真实性仍为 `Unverified`。

## 规则差异

- **P1 strict**（TTC<1.5 s、首末跨度≥0.3 s）识别更严格、事件负担较低，但遗漏 P2-only/P3-only 过程，并使源消息确认更晚。
- **P2 middle**（TTC<2.0 s、首末跨度≥0.2 s）在本案例集中提供中间事件负担和确认延迟。它的“中间”位置是工程折衷，不是独立安全真值支持的优势。
- **P3 sensitive**（TTC<2.5 s、首末跨度≥0.1 s）通常最早确认并覆盖更宽的接近过程，但更容易纳入临近阈值、短持续和测量敏感过程。

未触发原因在本轮只标记为 `threshold_or_duration_or_continuity`，因为要区分具体原因需逐帧重建该规则的失败边界；不把自动标签解释为物理结论。

## 对 AAD 消息时序的含义

`t_confirm` 必须是当前观测帧已经满足连续条件后的实际时间。P3 的更早确认具有消息时序价值，P1 的更严格条件具有减少候选负担的价值；二者之间的漏报/误报代价尚未被研究者定义。

## P2 是否足够明确地值得优先采用？

**目前不足。** 已有证据包括成员级差异、中心事件归属、绝对确认时刻和真实轨迹图册；仍缺少独立事故/近失真值、语义公平的采样稳健性、独立几何真实性，以及对 AAD 消息触发漏报与误报代价的正式权衡。因此 P2 只能作为 `Proposal / Pending Parameters / Not Frozen`，不能自动冻结。

## 产物

- `code/outputs/formal/calibration/stage_0_2_task_2_5_2_20261011_r1/key_difference_casebook.pdf`
- `code/outputs/formal/calibration/stage_0_2_task_2_5_2_20261011_r1/key_difference_cases.csv`
- `code/outputs/formal/calibration/stage_0_2_task_2_5_2_20261011_r1/candidate_rule_decision_table.csv`
- `code/scripts/run_stage_0_2_task_2_5_2_key_difference_cases.py`
