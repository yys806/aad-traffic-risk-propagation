# 任务 1：NGSIM 校准数据完整性与基础测量正确性核验

核验日期：2026-10-09。范围仅包含 Stage 0.2 校准文件：US-101 三个窗口和 Lankershim。未访问 I-80、Peachtree 或任何 locked holdout 内容；未修改指标、阈值、配置或历史结果。本报告把研究设计文件视为待落实意图，以 ZIP 内实际成员、当前源码和现有产物为证据。

## 1. ZIP 结构与原始 CSV 核验

逐行流式读取目标 CSV 至 EOF，检查表头、行宽、记录数、车辆数、时间范围、`(Vehicle_ID, Global_Time)` 重复、车辆内时间步，并比较当前 Stage 0.2 parquet 行数。时间均按原始 `Global_Time` 毫秒报告。

| 场景/窗口 | ZIP 内 CSV 记录数 | 当前程序 parquet 行数 | 车辆数 | 时间范围 | 车辆内重复时间 | 时间步异常 | 完整性状态 |
|---|---:|---:|---:|---|---:|---|---|
| US-101 07:50–08:05 | 1,048,575 | 1,048,575 | 1,993 | 1118846979700–1118847869500（889.8 s） | 0 | 全部 100 ms | **Failed/Unverified** |
| US-101 08:05–08:20 | 1,048,575 | 1,048,575 | 1,533 | 1118847843000–1118848631600（788.6 s） | 0 | 全部 100 ms | **Failed/Unverified** |
| US-101 08:20–08:35 | 1,048,575 | 1,048,575 | 1,298 | 1118848757500–1118849475400（717.9 s） | 0 | 全部 100 ms | **Failed/Unverified** |
| Lankershim complete | 1,607,319 | 1,607,319 | 1,506 | 1118935680200–1118937747000（2066.8 s） | 0 | 228 个非递增步；另有 200/300 ms 及 3.1–18.2 s 间隔 | **Failed/Unverified** |

表头结构符合当前读取器：US-101 为 18 列，使用 `Preceeding`、`v_Length`、`Space_Hdwy`；Lankershim 为 25 列，使用 `Preceding`、`v_length`、`Space_Headway`。四个成员均无流式解析错误、无短行；ZIP 外层和 US-101 内层均能正常打开。

### 1.1 US-101 的 1,048,575 行疑点

该数字不是当前程序造成的读取截断：四个程序输出 parquet 的逐窗口行数与 ZIP 内 CSV 完全一致，且流式读取到 CSV EOF，没有 `nrows` 限制或异常提前结束。另一方面，三个 US-101 CSV 各有一个车辆的 `Total_Frames` 与实际出现行数不一致：

| 窗口 | 车辆 | 实际行数 | `Total_Frames` | 差额 |
|---|---:|---:|---:|---:|
| 07:50–08:05 | 2783 | 702 | 760 | 58 |
| 08:05–08:20 | 1914 | 452 | 923 | 471 |
| 08:20–08:35 | 1317 | 67 | 1114 | 1,047 |

其余车辆的 `Total_Frames`、`Frame_ID` 范围和实际行数一致；三份 CSV 均达到相同的 1,048,575 行边界。证据支持“本机 CSV 被完整读取”，但不支持“CSV 与官方原始观测完整一致”；更符合源成员已经按固定行数截取或导出异常的解释。官方原始窗口的完整记录数目前未在本轮独立取得，因此“源文件截断”仍标记 **Unverified**，不能断言官方完整数据规模。

### 1.2 Lankershim 时间与身份异常

Lankershim 有 228 个车辆内非递增时间步；抽样包括 Vehicle 81 从 `1118935715500` 回到 `1118935691500`。另有 220 个 200 ms、3 个 300 ms 及大量 3.1–18.2 s 间隔。936/1506 个车辆编号的 `Total_Frames` 不是单一值或不等于合并记录数；例如 Vehicle 63 有 839 行、`Total_Frames` 为 394 和 445 两组，且观测跨越约 1094.7 s。至少前 12 个多段编号均表现为同一编号的两个时间段，说明 `Vehicle_ID` 在该 CSV 中可能跨段复用，或记录包含未按单一轨迹组织的多个片段。该事实会影响按车辆排序、轨迹边界、前车变化和事件合并，严重程度 **High**。

## 2. 基础测量正确性

### 2.1 Verified：实现和独立真值

- `real_trajectory.py::add_ngsim_leader_ttc()` 通过同一 `Global_Time + Preceding` 匹配前车；净间距为 `Space_Headway - matched leader v_Length`，均从英制转换为 SI。
- 闭合速度实现为 `follower_speed - leader_speed`；正闭合速度、正净间距和已匹配前车才进入 TTC/DRAC。
- `TTC = gap / closing_speed`，`DRAC = closing_speed² / (2*gap)`；非闭合运动为 `not_applicable`，非正间距为 `invalid`，无前车/前车未匹配为 `missing`，未填充零值。
- 独立构造案例覆盖匹配前车长度、单位换算、非闭合、非正间距、缺失前车、重复输入索引；现有 `tests/test_real_trajectory.py` 和 `tests/test_ngsim_risk_calibration.py` 通过。
- 重复 `(time, leader_id)` 前车候选在实现中被 `drop_duplicates(..., keep=False)` 排除，分类为前车未匹配，属于保守的不可测处理；没有证据表明它会选择错误前车。

### 2.2 Verified：当前程序读取范围

`run_stage_0_2_ngsim.py` 明确只读取 US-101 三个窗口和 Lankershim 目标成员；`write_stage_0_2_ngsim_package()` 只接受 `ngsim_us101`/`ngsim_lankershim`，不会读取留出集。现有 parquet 行数与原始 CSV 行数逐窗口一致，未发现程序额外丢行。

### 2.3 Failed/Unverified：真实数据身份边界

当前 `standardize_ngsim_states()` 以 `site + window_id + vehicle_id` 作为运行范围内的车辆标识，并按 `vehicle_id, time_s, frame_id` 排序后计算 `leader_changed` 与 `trajectory_boundary`。对 US-101 三窗口，该身份范围与固定窗口基本一致；但 Lankershim 的同一 `Vehicle_ID` 出现多个 `Total_Frames`、非递增时间和大间隔，当前键不能证明“一个 ID 对应一个连续轨迹”。因此：

- 前车同一时刻匹配的局部公式是 **Verified**；
- Lankershim 跨片段的轨迹边界、换道附近变化和风险事件连续性是 **Unverified/Failed**；
- 现有 `leader_changed`（Lankershim 4,738 条）和事件结果不能在身份分段问题解决前作为最终科学统计。

## 3. 异常、影响与建议

| 异常 | 证据 | 影响 | 严重程度 | 建议 |
|---|---|---|---|---|
| US-101 三 CSV 均固定 1,048,575 行 | ZIP EOF 行数；每窗口 1 个 `Total_Frames` 不一致车辆；程序 parquet 完全相同 | 可能缺失窗口尾部记录；当前校准覆盖不能称为官方完整窗口 | **High** | 任务 1.1 核对可信原始版本/官方说明和 ZIP 成员边界；在研究者决定前不拼接、不补齐、不把截取数据改写为完整数据 |
| Lankershim ID 多段复用/时间回退 | 936 个车辆有多组 `Total_Frames`；228 个非递增步；3.1–18.2 s 间隔 | 可能跨片段错误排序、事件合并和前车变化统计 | **High** | 任务 1.1 先确定官方轨迹分段规则或可审计分段键，再重算受影响测量；不得静默按时间排序修复 |
| Lankershim 非均匀采样 | 200/300 ms 和长间隔 | 连续风险事件的时间连续条件可能被误判 | **Medium/High** | 将间隔异常纳入质量审计和事件分段规则；规则需研究者确认 |
| 源字段 `Total_Frames` 与实际记录不一致 | 3 个 US-101 异常车辆、936 个 Lankershim 多值车辆 | `Total_Frames` 不能直接作为本地完整性证明 | **Medium** | 保留原始字段，报告不一致；不要用它覆盖实际观测行数 |

## 4. 未解决问题与验收判断

未完成：官方原始窗口完整性对照；US-101 固定行数来源；Lankershim 多段车辆的正式分段语义；异常间隔对事件规则的处理；异常数据对最终分布和事件频率的影响。本轮按用户限制未进行极端 TTC/DRAC 科学审计，也未生成最终风险分布或事件频率结论。

**任务 1：未达到最终验收条件；建议进入任务 1.1。** 基础公式与程序读取链达到工程核验要求，但校准数据完整性和 Lankershim 身份边界存在高严重度未决问题，不能据此关闭 Stage 0.2。

