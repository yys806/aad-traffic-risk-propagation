# 任务 1.1：NGSIM 数据完整性与轨迹分段依据专项核查

核验日期：2026-10-09。范围仅为 US-101 与 Lankershim Stage 0.2 校准数据。未访问 I-80、Peachtree 或其他 locked holdout 科学内容；未下载大型替代数据；未修改测量逻辑、事件规则或正式配置。

状态标签含义：`Verified` 为本机文件/源码/可复现实验直接支持；`Inference` 为由多项事实推导的工程判断；`Unverified` 为当前证据无法确认。

## 1. US-101 来源与完整性

### 1.1 ZIP 内部版本核查

当前文件：`dataset/NGSIM/US-101-LosAngeles-CA.zip`。外层包含 `us-101-vehicle-trajectory-data.zip`，内层每个窗口同时包含 `.csv` 和 `.txt`：

| 窗口 | CSV 数据行 | TXT 数据行 | CSV 最后一条 | TXT 中紧随 CSV 行数之后的记录 | 结论 |
|---|---:|---:|---|---|---|
| 07:50–08:05 | 1,048,575 | 1,180,597 | `Vehicle_ID=2783, Frame_ID=8702, Global_Time=1118847849100` | `2783, 8703, 760, 1118847849200` | **Verified：CSV 是 TXT 的固定前缀截取** |
| 08:05–08:20 | 1,048,575 | 1,403,094 | `Vehicle_ID=1914, Frame_ID=7373, Global_Time=1118848579300` | `1914, 7374, 923, 1118848579400` | **Verified：CSV 是 TXT 的固定前缀截取** |
| 08:20–08:35 | 1,048,575 | 1,515,239 | `Vehicle_ID=1317, Frame_ID=6111, Global_Time=1118849368100` | `1317, 6112, 1114, 1118849368200` | **Verified：CSV 是 TXT 的固定前缀截取** |

TXT 行数为逐行读取结果；CSV 行数为去表头后的数据记录数。CSV 与 TXT 的首条记录字段一致（仅数值格式化不同），并且 CSV 末尾的下一条 TXT 记录仍属于同一车辆、同一 `Total_Frames` 序列，直接排除了“CSV 恰好自然结束于观测末尾”的解释。此前三个 CSV 各有一个 `Total_Frames` 与实际记录数不一致车辆，正是固定前缀截取的表现。

### 1.2 官方资料

仓库随数据保存的 FHWA 元数据：

- `dataset/NGSIM/1- US 101 Metadata Documentation.pdf`，正文约第 39–41 行：完整数据为三个 15 分钟窗口（07:50–08:05、08:05–08:20、08:20–08:35）。
- 同文件约第 167–171 行：轨迹数据提供 CSV 和 TXT 两种文件，TXT 是原始文件，CSV 是转换文件，并明确建议为保证正确性使用 TXT。
- 同文件约第 182–186 行：`Completeness Report` 明确说明 USDOT 不对数据完整性作保证，数据中可能存在缺口。
- 同文件约第 482–521 行：轨迹字段定义；`Total_Frames` 是车辆在该数据集出现的总帧数，`Global_Time` 为毫秒时间，轨迹每 0.1 秒记录。

官方发布入口记载于元数据：<https://www.its-rde.net/>。项目研究设计中引用的 NGSIM 数据页为 <https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Vehicle-Trajector/8ect-6jqj>。本轮没有重新下载官方数据，因而不把网页当前可访问状态或外部版本假定为已验证事实。

### 1.3 三个完整性层次

1. **本机程序读取完整：Verified。** `run_stage_0_2_ngsim.py` 使用 `pandas.read_csv` 读取指定 CSV 成员；现有 parquet 行数与 CSV 行数逐窗口一致；本轮独立流式读取到 EOF，没有 `nrows` 截断。
2. **当前 CSV 与同 ZIP TXT 一致：Failed。** TXT 是同一 ZIP 内的原始版本，记录数更大，且 CSV 末尾后存在连续 TXT 记录。当前 CSV 明确不是完整窗口。
3. **TXT 与官方全部原始观测完全一致：Unverified。** 官方元数据声明不保证完整性；本轮没有取得另一份官方校验清单或独立原始摄像记录。因此不能把 TXT 行数直接写成官方真实总记录数。

### 1.4 是否需要替换

**当前 US-101 CSV 需要替换为同 ZIP 内对应 TXT，或转换自 TXT 的完整版本；不应继续把三份 CSV 作为完整窗口。** 这是数据源替换建议，不是本轮自动执行的替换。建议先由研究者确认：Stage 0.2 是否接受同 ZIP TXT 作为校准输入，以及是否需要保留 TXT→标准化表的确定性转换记录。不能补齐 CSV，也不能把 CSV 缺失尾部推测为某种交通状态。

## 2. Lankershim 来源与身份问题

### 2.1 官方时间段与当前 ZIP 内容

仓库 `dataset/NGSIM/3- Lankershim Blvd Metadata Documentation.pdf` 说明：完整数据为两个 15 分钟时期（约 08:30–08:45、08:45–09:00）；轨迹说明处进一步给出两个文件 `trajectories-0830am-0845am` 和 `trajectories-0845am-0900am`，且同样说明 TXT 为原始文件、CSV 为转换文件。当前 `Lankershim-Boulevard-LosAngeles-CA.zip` 的轨迹部分只有一个 `NGSIM__Lankershim_Vehicle_Trajectories.csv`，没有这两个原始 TXT 或两个独立窗口成员。

### 2.2 已验证异常

当前合并 CSV 的独立扫描结果：1,607,319 行、1,506 个 `Vehicle_ID`；228 个车辆内时间步非递增；936 个车辆出现多组 `Total_Frames` 或总帧数与合并行数不一致。典型记录：

- Vehicle 63：第一段 394 行、`Total_Frames=394`，随后在文件后部又出现 445 行、`Total_Frames=445`；两段相隔约 1,094.7 s。
- Vehicle 81：同一 `Vehicle_ID` 的记录中出现时间回退（`1118935715500` 后回到 `1118935691500`），并存在 `Total_Frames=719` 的多块记录。
- 全文件按行读取时 `Global_Time` 有 2,654 次下降，最大下降约 1,001.4 s，说明当前合并 CSV 并非全局按时间单调排序，不能把文件行号当作轨迹时间顺序。

### 2.3 解释状态

- **Verified：** 同一 `Vehicle_ID` 在当前合并 CSV 中对应多组 `Total_Frames`、时间块和/或回退；当前 `site + window + Vehicle_ID` 不能保证唯一连续轨迹。
- **Inference：** 主要原因很可能是两个官方观测时段/源文件被合并后保留了重复的局部 `Vehicle_ID` 编号，或转换时未保留源文件/时段标识。时间块规模与官方两个 15 分钟时期相符，但仅凭当前 CSV 无法证明每一条异常都只由时段边界造成。
- **Unverified：** 当前 ZIP 是否来自官方完整 Lankershim 发布包、两个时段的确切分界记录、跨时段是否允许复用同一编号，以及是否存在时段内部的轨迹中断。

## 3. 推荐的轨迹身份与分段方案

以下是供研究者确认的可复现方案，本轮不写入正式测量代码：

### 3.1 首选方案：恢复源文件边界

优先取得/恢复官方两个独立源成员（每个时段的 TXT 或 CSV），并把源成员名作为身份组成部分：

`trajectory_id = (dataset=NGSIM, site=Lankershim, source_period, source_member, Vehicle_ID)`

US-101 同理保留 `(site, window, source_member, Vehicle_ID)`。前车匹配只在同一 `source_period/source_member` 内按 `(Global_Time, Vehicle_ID)` 进行，不跨窗口或源成员匹配。这样不依赖推测的时间阈值，且直接遵循官方文件分段。

### 3.2 只有合并 CSV 时的保守诊断方案

若暂时无法恢复两个源成员，建议先生成诊断分段表而不覆盖原始 `Vehicle_ID`：

1. 以 `(site, documented_period, Vehicle_ID)` 为候选身份；`documented_period` 必须来自已确认的官方时段边界，不能由结果反推。
2. 在候选身份内按 `(Global_Time, Frame_ID)` 排序仅用于诊断，并保留原始行号。
3. 当 `Total_Frames` 改变、`Frame_ID` 回退/重置、`Global_Time` 回退，或出现未经研究者批准的长间隔时，增加 `segment_index` 并标记 `segment_break_reason`；不自动删除或拼接。
4. 身份键使用 `(site, documented_period, Vehicle_ID, segment_index)`。无法证明分段唯一的记录标记 `identity_uncertain`，不得进入需要连续时间的风险事件统计。

这里的“长间隔”判定阈值、是否将短暂回退视为新段、以及 `Total_Frames` 改变的解释仍需研究者决定。仅用 `Global_Time` 排序不能修复当前问题，因为官方说明称文件按时间排序，而实际合并 CSV 存在大量全局时间下降，表明行顺序与轨迹顺序不是同一概念。

### 3.3 对前车匹配和事件的保守处理

- 前车匹配应限于同一已确认轨迹段；段边界前后不做跨段匹配。
- 当前无法唯一识别的 `Vehicle_ID` 记录标记为 `identity_uncertain`；不填零、不静默删除。
- 事件合并在段边界强制断开；时间间隔异常按未观测/右删失候选处理，具体纳入规则需研究者确认。
- 在分段依据确认前，现有 Lankershim 的 `leader_changed`、TTC/DRAC 有效行和候选事件不能作为最终科学分布或事件频率。

## 4. 对现有结果和后续校准的影响

### US-101

现有 `stage_0_2_ngsim_v2` 三个 US-101 parquet 只覆盖截断 CSV；其行数、车辆数、TTC 有效行和候选事件数不能代表完整 TXT 窗口。现有测量实现本身未发现公式错误，但需要以完整 TXT 重新生成独立版本后再比较结果。建议保留旧产物为历史/迁移前证据，不覆盖。

### Lankershim

当前 parquet 继承合并 CSV 的身份和顺序问题。`standardize_ngsim_states()` 按 `vehicle_id, time_s, frame_id` 排序并计算 `leader_changed`/`trajectory_boundary`，这会把同一 ID 的多个时间块放入一个候选身份；因此受影响的不仅是事件合并，也包括前车变化、连续风险暴露和按车辆汇总。影响量级至少为 936/1506 个车辆存在多 `Total_Frames`/不一致证据，228 个车辆内有非递增时间步；精确受影响风险行数需要在分段规则确定后重算，当前不推断。

### SUMO 校准

在 US-101 完整版本和 Lankershim 身份边界确认前，不应把现有风险分布或事件频率用于最终 SUMO 跟驰校准，也不应据此冻结现实范围。Stage 0.5 的旧参考包和 Stage 0.6 readiness 不因本报告自动更新。

## 5. 修复条件、待决策与任务 1.2

### 已具备

- 同 ZIP 内存在 US-101 TXT 原始版本，足以开始一个不覆盖旧结果的替代输入验证分支。
- 官方元数据给出了 US-101 三窗口和 Lankershim 两时段的设计分段。
- 当前异常扫描可复现，源码和测试位置明确。

### 仍阻断

- Lankershim 当前包缺少官方两个源 TXT/CSV 成员，无法确认合并边界和编号复用语义。
- USDOT 元数据不保证完整性，不能仅凭 TXT 行数声明官方全部观测已恢复。
- 分段断点、异常时间间隔和 `identity_uncertain` 的纳入规则尚未冻结。

### 需要研究者决定

1. 是否批准将同 ZIP US-101 TXT 作为当前 Stage 0.2 校准输入，并生成新版本产物；
2. 是否要求取得/恢复 Lankershim 两个官方源文件后再继续，还是允许以保守诊断分段方案推进；
3. 长间隔、时间回退和无法唯一分段记录的科学纳入/排除规则；
4. 是否将当前 CSV 结果永久降级为历史/工程验证证据。

**任务 1.1 结论：US-101 截断已确认；Lankershim 编号复用的主要来源有合理解释但尚未由源文件证实；当前不具备关闭任务 1 或直接进入正式重算的条件。建议任务 1.2 先取得/核验 Lankershim 两个源文件及分段键，并由研究者确认 US-101 TXT 替换和异常纳入规则。**

