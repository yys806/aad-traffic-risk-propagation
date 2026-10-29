# AAD-S0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029

状态：**Verified minimal alignment; source P2 remains zero; researcher decision pending for simulator equivalence and physical-path evidence**。

本任务没有启动 SUMO/TraCI、生成新轨迹、运行独立 seed 或读取 locked holdout。Task 2 的 16 个合成案例和 post-R2 封存诊断均复用；新增证据包位于 [RES-STAGE-0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029](../evidence/results/RES-STAGE-0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029/)。

## 最终采用的契约

正式 P2 继续使用已有 `stage_0_2.formal_risk_measurement.v2`：同一 follower/leader trajectory pair、incarnation、原始时钟和帧连续性，`0<TTC<2 s`，首末观测跨度至少 `0.2 s`，100 ms 采样和 0.11 s 最大间隔。`identity_break`、`observation_gap`、身份不确定和 leader 未匹配均保持 fail-closed，不能解释成风险已经解除。

现有正式 extractor 已按 **C 的一般 pair/time 连续性**确定事件资格；它不把 `native_lane_id` 作为 Formal P2 事件条件。D1 的 same-native-lane 条件继续只用于局部诊断暴露和物理路径支持，不能冒充正式 P2 事件资格或正式 P2 发生率。A/B 没有被写入生产规则：B 仍需要独立、时间化的道路连接和交互见证，C 的物理路径资格仍单独报告。

## 必要最小修正

修改 [stage_0_5_sumo.py](../code/src/riskprop/stage_0_5_sumo.py) 的 `build_sumo_formal_source_frame()`：

- 保留上游提供的 `identity_uncertain`、`identity_break`、`observation_gap`、`leader_identity_uncertain`、`leader_matched` 布尔证据；
- 只有在输入没有对应字段时，才使用确定性 SUMO recorder 的默认值；
- 非 100 ms cadence 仍强制设置 `observation_gap=True`，不把粗采样伪装成 formal evidence；
- 没有改变 TTC 阈值、持续时间、研究空间、窗口、cohort、Rule A 或 D1 定义。

新增回归覆盖显式中断标记的保真，并更新已有 post-R2 反例期望。lane/path 分层测试确认：native/formal pair 事件可以成立，而 D1 same-native-lane onset/exposure 可以不同；没有任何物理路径被自动推断为连续。

## 合成案例前后对比

`flag_preservation_before_after.json` 记录 Task 2 旧输出和当前源码输出：

| 案例 | Task 2 formal-aligned | Task 3 formal-aligned | 映射标记 | 含义 |
|---|---:|---:|---|---|
| `identity_break` | 1 个事件，映射标记 0 | 0 个确认事件，`identity_break=1` | 保真 | 三帧反例不再跨越显式身份中断 |
| `observation_gap` | 1 个事件，映射标记 0 | 0 个确认事件，`observation_gap=1` | 保真 | 缺失观测不再被适配器清除 |

`lane_path_separation_recheck.json` 复核 `native_lane_change`：修正前后 native/formal pair 事件仍为 1，D1 onset 仍为 0。该结果支持“事件资格与 D1/物理路径资格分离”，不支持任何换道因果解释。

## B00 与 Round2 候选封存复核

`sealed_trace_reanalysis_reuse.json` 复用 post-R2 诊断中的封存统计和源码路径。B00 与候选的源区正式风险行均为 0，source onset 均为 0；D1 暴露分别为 8457.4 和 8900.0 veh-s，源观察分别为 86234 和 91058。修正不改变这些数字，依据是封存重建路径 `fcd_to_state_frame → measure_state_frame` 没有输出显式 continuity flags，因此适配器对这两份封存重建使用的 absent-field 默认值仍为 false；修正只影响显式提供 flags 的外部预测量输入。

因此：

1. 必要修正没有改变正式源区 P2 计数或事件资格；
2. 改变点只发生在带有显式 `identity_break`/`observation_gap` 的适配器输入；
3. 当前源区“可靠可评价支持内无正式 P2 命中”仍成立，但不能推出整个物理源区没有风险；
4. Round2 候选仍未满足原先冻结的源事件条件。它的 Rule A 和目标区次级事件结果继续按 Task 1 记录，不能启动独立 seed 确认；
5. 物理到达时刻、跨 edge/lane 的真实路径见证仍为 `Unknown`。

## 文献附件收尾

复用上一任务已登记的 8 个 Zotero item，不创建重复条目，也没有把 PDF 放入 Git。当前执行环境的 PowerShell/Python 外联 socket 仍受限，8 个附件未能下载或挂接；每条记录的官方/合法来源、item key 和未获取原因保留在 Task 2 的 `literature_dedup_acquisition.json`。这项资料收尾不影响本任务的测量修正和封存判断。

## 验证和阶段状态

- 新增显式 flag 对齐测试：通过；
- post-R2 反例回归：通过；
- local-following 回归：17 passed；
- measurement-equivalence 选定边界回归：36 passed；2 个 Parquet guard 测试因缺少 `pyarrow/fastparquet` 未执行成功；
- 新证据包含 `validation_record.json`、`manifest.json`、`SHA256SUMS` 和源码绑定。

`round2_candidate_passes_original_source_condition=false`。Formal simulator-vs-NGSIM scientific equivalence 仍未接受。Stage 0.5 Gate、Stage 0.6、Protocol Lock、Stage I 和第三轮均保持原状态。

待研究者裁决的事项只有两项：

1. 在显式输入契约已对齐后，是否接受 simulator formal-aligned 输出与 NGSIM Formal P2 的科学可比性；
2. 什么样的时间化道路连接、leader/follower 交互见证足以授予跨 native lane/edge 的物理路径资格。
