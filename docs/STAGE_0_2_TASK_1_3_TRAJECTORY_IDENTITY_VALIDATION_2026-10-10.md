# Stage 0.2 任务 1.3：NGSIM 轨迹身份修复与完整测量链验证

核查日期：2026-10-10（Asia/Shanghai）。本轮只读取 US-101 校准 TXT 和 Lankershim 合并 CSV；未读取、解压或分析 I-80、Peachtree、SPMD 或其他 locked holdout。未改变 TTC/DRAC 数学定义、最终阈值、科学事件纳入标准或 Stage 0.2 Gate。

## 结论

- **US-101：Verified。** 三个 TXT 共 4,098,933 行，完整通过 TXT→标准化状态→TTC/DRAC→候选事件→audit/manifest/provenance/SHA256SUMS 链。输出为独立本地产物，未覆盖历史 CSV 产物。
- **Lankershim：部分 Verified。** 原始 1,607,319 行全部保留。根据原始行顺序内 `Frame_ID` 非递增建立确定性诊断片段；时间缺口只标记、不自动断身份。228 行时间回退被标记 `identity_uncertain`，不能进入可靠连续事件。
- **单帧与事件边界已分开。** Lankershim 共有 483,098 个有效 TTC 帧；排除身份不确定或观测缺口后的可靠候选帧为 482,470 个。剩余 628 个有效 TTC 帧仍保留，但不用于可靠连续性统计。
- **任务 1 尚未完全验收。** 基础读取、身份诊断和测量工程链可复现；Lankershim 两个官方时段仍不能从合并文件唯一恢复，且最终科学事件标准尚未冻结。因此可以进入后续 Stage 0.2 科学质量审计，但不能把本轮候选事件数当作最终风险频率或 Gate 结论。

## 1. 实施的工程规则

新增 `annotate_ngsim_trajectory_identity()`，保留 `Vehicle_ID`，并增加：

- `original_row_number`：输入文件顺序的一基索引；
- `original_vehicle_id`：原始编号；
- `source_period`、`source_member`：未知时明确写 `unknown`，不伪造官方时段；
- `segment_index`、`trajectory_id`：由 `site/source_period/source_member/original_vehicle_id/segment_index` 确定性生成；
- `identity_break`：同一原始编号在原始行顺序内出现非递增 `Frame_ID`；
- `observation_gap`：同一编号相邻记录 `Global_Time` 差值大于 100 ms，仅为缺帧/观测缺口标记；
- `identity_uncertain`：同一编号时间回退；
- `identity_status`：`confirmed`、`confirmed_segment` 或 `identity_uncertain`。

该规则不把任意长时间间隔当作换车，不排序覆盖原始顺序，不删除重复或异常记录。标准化输出保持输入行数一致。前车匹配在提供 `trajectory_id` 时使用同一时刻的稳定片段身份，仍保留原始 `leader_id`；无法唯一对应的前车不赋零值。事件合并按片段身份、前车片段身份、时间连续性、身份边界和缺口标记分组，不能跨片段合并。

## 2. Lankershim 全量诊断

证据文件：`code/outputs/formal/calibration/stage_0_2_task_1_3_lankershim_diagnostic_20261010_r2/diagnostic.json`，输入为 `dataset/NGSIM/Lankershim-Boulevard-LosAngeles-CA.zip` 内 `NGSIM__Lankershim_Vehicle_Trajectories.csv`。

| 指标 | 数量 | 状态 |
|---|---:|---|
| 原始记录 | 1,607,319 | **Verified** |
| 原始 Vehicle_ID | 1,506 | **Verified** |
| 确定性诊断片段 | 2,654 | **Verified** |
| `identity_break` 行 | 1,148 | **Verified** |
| `identity_uncertain` 行 | 228 | **Verified** |
| 受影响 Vehicle_ID | 204 | **Verified** |
| `observation_gap` 行 | 1,379 | **Verified** |
| 同 Vehicle_ID/Global_Time 冲突行 | 0 | **Verified** |
| 同 Vehicle_ID/Frame_ID 重复行 | 230,554 | **Verified** |
| Vehicle_ID 内时间回退 | 228 | **Verified** |
| 文件原始行序 Global_Time 回退 | 2,654 | **Verified** |
| 100 ms 间隔 | 1,604,206 | **Verified** |
| 200 ms 间隔 | 220 | **Verified** |
| 300 ms 间隔 | 3 | **Verified** |

`Frame_ID` 非递增包含重复/重置和回退，因此比单纯时间回退更广，形成 2,654 个片段。时间回退全部落在 `identity_uncertain` 标记中；长间隔只影响连续事件资格。由于文件缺少两个独立源成员，`source_period=unknown`，不能把这些片段进一步宣称为官方 08:30–08:45 或 08:45–09:00 轨迹。

### A/B/C 分类边界

- **A 可确认连续轨迹：** 片段内部原始行顺序中 `Frame_ID` 递增、时间不回退且没有身份不确定标记的记录；这是工程可观测性分类，不等同于官方物理轨迹证明。
- **B 可确认分段轨迹：** 同一原始编号出现 `Frame_ID` 非递增的位置，按确定性规则分为相邻 `segment_index`。该分段边界由字段冲突支持，但不证明每一段对应哪一个官方观测时段。
- **C 无法唯一确定轨迹：** 228 个时间回退行及其相邻身份关系，以及缺少源时段成员导致的跨时段归属，保留 `identity_uncertain`/`source_period=unknown`，不强行拼接。

## 3. Lankershim 测量范围

| 状态 | 行数 | 占全部 |
|---|---:|---:|
| `valid` TTC | 483,098 | 30.05% |
| `invalid` | 75,867 | 4.72% |
| `missing` | 380,820 | 23.69% |
| `not_applicable` | 667,534 | 41.53% |
| 有效 TTC 且无身份不确定/缺口 | 482,470 | 30.01% |
| 有效 TTC 但受身份不确定或缺口影响 | 628 | 0.039% |

工程候选事件数为 2,787，使用当前回归参数 TTC < 2.0 s、最大间隔 0.11 s、最小持续时间 0.1 s。该数字只表示诊断产物，不是冻结的科学事件频率。可靠连续候选帧与不确定候选帧分开记录；不确定行仍在状态表中。

## 4. US-101 TXT 全量链

产物目录：`code/outputs/formal/calibration/stage_0_2_task_1_3_us101_txt_20261010_r2/`。

| 窗口 | 输入行 | 车辆数 | 有效 TTC | 候选事件 | 状态 |
|---|---:|---:|---:|---:|---|
| 07:50–08:05 | 1,180,598 | 2,169 | 464,134 | 616 | **Verified** |
| 08:05–08:20 | 1,403,095 | 2,017 | 605,211 | 824 | **Verified** |
| 08:20–08:35 | 1,515,240 | 1,915 | 658,935 | 1,164 | **Verified** |
| 合计 | 4,098,933 | — | 1,728,280 | 2,604 | **Verified** |

三个输入均为 `ngsim_us101_txt_v1`，每个窗口 `raw_row_preservation=1`，无身份边界或不确定行。读取器全量运行时间约为分钟级，生成三个状态 Parquet、风险事件 Parquet、冻结配置、审计、provenance、manifest 和 SHA256SUMS。输入 ZIP SHA-256 与任务 1.2 保持一致。TXT 文件原始行顺序并非全局时间排序；读取器按数据字段处理，不把文件末行当作时间末端。

US-101 旧 CSV 每窗固定 1,048,575 行；本轮 TXT 使用新增行数并生成独立版本，因此新旧候选事件数不能直接作为算法变化对照。当前明确的变化来源首先是输入记录增加；本轮没有修改 TTC/DRAC 数学定义。

## 5. 测试与限制

新增测试覆盖：片段身份确定性、原始行保留、Frame_ID 重置、相邻片段不合并事件、TXT 结构和来源追溯。相关 Stage 0.2/真实轨迹测试通过；全量测试、`compileall`、项目文档校验和便携证据校验在提交前执行。

**Unverified / 待研究者决定：** Lankershim 官方两个观测时段边界、时段内轨迹中断的物理语义、是否将诊断片段作为后续科学事件单位，以及最终风险事件阈值、持续时间和纳入标准。保守筛选会降低连续事件样本覆盖，可能造成按身份可靠性选择的覆盖偏差；本报告不作方向性结论。

**任务 1 状态：部分达到基础工程验收。** US-101 TXT 链已达到工程验证；Lankershim 原始记录保留、身份冲突标记和单帧/连续事件边界已可审计。任务 1.4 需要解决的具体问题是：确定 Lankershim 是否接受当前字段冲突分段作为正式事件单位，或仅将其作为质量诊断，并据此重新定义后续科学质量审计的连续事件纳入范围。此报告不创建 Protocol Lock、不启动 Stage I。
