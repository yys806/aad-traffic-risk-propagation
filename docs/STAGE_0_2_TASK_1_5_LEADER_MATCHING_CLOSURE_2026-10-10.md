# Stage 0.2 任务 1.5：跨时间序列前车匹配核验与任务 1 收尾

日期：2026-10-10（Asia/Shanghai）。本轮只处理 US-101 三个校准 TXT 与 Lankershim 合并 CSV；未访问 locked holdout，未修改原始数据、轨迹分组规则、TTC/DRAC 数学定义、科学阈值或事件纳入标准。任务 1.4 的独立工程包保留不变。

## 结论

**Verified：未发现真实数据中的跨诊断时钟错误匹配。** Lankershim 全部 1,607,319 行中，1,226,499 行报告了前车编号。独立按 `(Global_Time, Vehicle_ID)`、再按 `(Global_Time, Vehicle_ID, clock_anchor)`、最后按 `(Global_Time, Vehicle_ID, clock_anchor, Frame_ID)` 计数，三种口径均为 1,226,499 个唯一前车候选，歧义和缺失均为 0。当前匹配结果中跨时钟成功匹配 0 行，跨时钟有效 TTC 0 行，前车身份不确定的有效 TTC 0 行。

**Verified：实现存在潜在边界缺口，已修复。** 任务 1.4 代码用稳定 `trajectory_id` 防止多数跨时钟混配，但唯一查找键实际只显式使用了来源范围和时间；构造的“相同时间+复用编号+两个时钟”案例会把两个合法前车一起排除。现在匹配键在可用时明确包含 `run/site/window` 作用域、Global_Time、诊断时钟锚和 Frame_ID；同范围重复候选仍全部不匹配，不任意取一条。缺少必要诊断字段时不猜测前车；不含诊断字段的历史调用保留时间/来源兼容路径。

**Verified：任务 1 建议正式关闭。** 四个输入保留全部原始记录，跨序列前车匹配规则明确，TTC/DRAC 和测量状态全量回归一致，候选事件结果未改变。Lankershim 的官方时段标签及物理车辆身份仍是 `Unverified`，但不再构成任务 1 的工程阻断。Stage 0.2 科学 Gate 仍为 Active，最终阈值、事件口径和极端值审计仍待后续科研任务。

## 1. 独立核查

证据：`code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r3/cross_clock_match_audit.json`。输入 Lankershim ZIP SHA-256 为 `757c693ba72b7c8ba7561ee1b5107dfa7119cc4862584a4f033aa445246c56c1`。

| 核查量 | 数量 | 状态 |
|---|---:|---|
| 原始记录 | 1,607,319 | Verified |
| 原始 Vehicle_ID | 1,506 | Verified |
| 报告前车行 | 1,226,499 | Verified |
| 时间+前车编号唯一 | 1,226,499 | Verified |
| 时间+编号+时钟锚唯一 | 1,226,499 | Verified |
| 时间+编号+时钟锚+帧号唯一 | 1,226,499 | Verified |
| 同时刻编号的时钟/帧冲突 | 0 行 | Verified |
| 当前跨时钟匹配 | 0 | Verified |
| 跨时钟有效 TTC | 0 | Verified |
| 前车不确定有效 TTC | 0 | Verified |

独立统计没有需要列出的真实冲突行号，因为冲突集合为空。当前 1,226,499 个前车匹配均能在相同诊断锚和相同 Frame_ID 下找到唯一记录。该结论来自原始 CSV 字段和标准化状态的稳定 leader 记录，不是由候选事件“全部通过”反推。

## 2. 最小修复

`code/src/riskprop/real_trajectory.py::add_ngsim_leader_ttc()` 现在建立内部匹配键：

`scope + Global_Time + diagnostic_clock_anchor_ms + Frame_ID + original/trajectory leader id`。

`diagnostic_clock_anchor_ms` 缺失时，如果存在整数 Frame_ID 则由 `Global_Time - 100*Frame_ID` 得到；诊断字段或 Frame_ID 缺失时，相关记录不被伪造匹配。重复键通过 `drop_duplicates(..., keep=False)` 全部标为不可匹配。前车长度仍来自匹配前车；净间距、闭合速度、TTC、DRAC 公式未改。`leader_trajectory_id`、`leader_frame_id`、`leader_identity_uncertain` 和连续事件边界继续使用同一稳定身份。

新增真值测试覆盖：两个时钟下复用相同前后车编号、同一时钟帧号不一致、缺失诊断锚、同源唯一匹配、同来源重复候选，以及既有事件连续性。潜在缺陷先由测试复现，再实施修复。

## 3. 全量回归

新版独立产物：`code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r3/`。包含四个状态表、原始/可靠/拒绝事件表、`cross_clock_match_audit.json`、`regression_comparison.json`、config、provenance、manifest 和 SHA-256SUMS。完整 Parquet 仅保留本机；便携证据在 `evidence/results/RES-STAGE-0.2-TASK-1.5/`。

| 数据源 | 记录数 | 有效 TTC | 原始/可靠事件 | 与任务 1.4 核心测量差异 |
|---|---:|---:|---:|---:|
| US-101 07:50–08:05 | 1,180,598 | 464,134 | 616/616 | 0 行 |
| US-101 08:05–08:20 | 1,403,095 | 605,211 | 824/824 | 0 行 |
| US-101 08:20–08:35 | 1,515,240 | 658,935 | 1,164/1,164 | 0 行 |
| US-101 合计 | 4,098,933 | 1,728,280 | 2,604/2,604 | 0 行 |
| Lankershim | 1,607,319 | 483,098 | 2,777/2,777 | 0 行 |

Lankershim 全量结果仍为 1,226,499 个前车匹配、483,098 个有效 TTC、2,777 个可靠候选事件、0 个拒绝事件。US-101 三个 TXT 的状态核心和事件数也保持任务 1.4 基线。没有发生测量状态转移、TTC/DRAC 数值变化或事件新增/消失。

## 4. 产物与复现

复现入口：

```powershell
python code/scripts/verify_ngsim_task_1_5.py --output code/outputs/formal/calibration/<独立输出目录>
```

脚本只读取显式列出的四个 NGSIM calibration 源，不下载数据、不访问 holdout；它保存输入哈希、独立匹配统计、状态/事件产物、provenance 和完整 SHA-256SUMS。当前 r3 provenance 绑定本轮实现提交前源码哈希；Git 便携证据只包含小型 JSON，不含原始表或 Parquet。

## 5. 验证与边界

- 任务 1.5 针对性测试：新增跨时钟、同帧冲突和缺失字段测试通过；任务 1.4 测试集继续通过。
- 全量测试、compileall、项目文档验证和 portable evidence verify 在提交前执行。纯 Git 克隆用于 clean 文档检查；主工作区已有无关论文删除/未跟踪改动，继续保留不提交。
- `Verified` 只表示本机数据和工程链证据。`Unverified` 仍包括 Lankershim 官方来源时段和真实物理车辆身份；不把诊断时钟称为官方时段。
- 不生成科学风险发生率，不冻结 TTC 阈值或事件持续时间，不创建 Protocol Lock，不启动 Stage I。

**任务 1 最终建议：关闭。** 已知工程问题均有识别、修复和全量回归证据；后续可在研究者审核后进入任务 2 科学质量审计。本轮执行到此停止。
