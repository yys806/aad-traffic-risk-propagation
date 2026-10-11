# AAD 结果索引

> 核对日期：2026-09-10。以下结果均不能支持核心科学效应声明。

## RES-STAGE-0.1-INFRASTRUCTURE-V3

阶段 0.1工程运行：处理前等价、隔离、时钟和生命周期通过；物理连通路径未接通。便携证据位于同名 `evidence/results/` 目录。

## RES-STAGE-0.1-ENV-COMPARE-V3

阶段 0.1双环境结构一致性结果；只证明结构匹配。

## RES-STAGE-0.2-NGSIM-V2

阶段 0.2迁移前审计包：NGSIM可形成有效跟驰测量与风险事件；holdout未解锁，异常审计和最终分布仍需收口。

## RES-STAGE-0.4-COMM-OBS-V3

阶段 0.4通信可观测性结果：RV_RX只能作为接收状态连续性；packet schema、时延、丢包和采用不可声称已观测。

## RES-STAGE-0.5-REAL-REF-V1

阶段 0.5迁移前部分真实参考。pNEUMA风险指标未纳入、SUMO样本未纳入；按当前“pNEUMA只做运动学”的边界需要重新生成。

## RES-STAGE-0.6-PRELOCK-V2

阶段 0.6数值审计：解析和工程真值检查通过，科学容差仍未冻结。

## RES-PROTOCOL-READINESS-V1

迁移前协议就绪哨兵，结论为未就绪。新阶段键启用后必须重新生成；它不是科学结果。

每个当前结果必须登记便携证据、本机完整产物、配置、数据身份、结论边界和 Gate。旧 pNEUMA 前车复核结果已转入 `evidence/history/legacy_experiment_ids/`。

## RES-STAGE-0.2-TASK-1.4

Verified 工程核查，待研究者验收任务 1。US-101 4,098,933 行测量回归一致；Lankershim 1,607,319 行保留，2,442 个诊断时钟序列，483,098 个有效 TTC 帧，原始/可靠候选事件各 2,777 个、拒绝 0。官方来源时段与物理身份仍 Unverified，Stage 0.2 科学 Gate 仍 Active。报告：`docs/STAGE_0_2_TASK_1_4_RELIABILITY_CLOSURE_2026-10-10.md`；完整包 `code/outputs/formal/calibration/stage_0_2_task_1_4_20261010/`，小型证据在同名结果目录。

## RES-STAGE-0.2-TASK-1.5

跨时钟前车匹配工程核验 Verified。Lankershim 1,226,499 条报告前车均在时钟锚与 Frame_ID 约束下唯一，真实跨时钟匹配 0；四源核心测量和事件结果与任务 1.4 一致。建议关闭任务 1，Stage 0.2 科学 Gate 仍 Active。报告：`docs/STAGE_0_2_TASK_1_5_LEADER_MATCHING_CLOSURE_2026-10-10.md`。

## RES-STAGE-0.2-TASK-2

NGSIM 风险测量质量、真实分布与候选事件规则描述性审计。5,706,252 条 state、2,211,378 条有效 TTC；TTC/DRAC 重尾，极端记录已追溯，6×4 阈值/持续时间网格显示事件数对规则敏感。未冻结科学规则或 Stage 0.2 Gate。报告：`docs/STAGE_0_2_TASK_2_RISK_QUALITY_AUDIT_2026-10-10.md`；完整包保留在 `code/outputs/formal/calibration/stage_0_2_task_2_risk_quality_audit_20261010_r4/`。

## RES-STAGE-0.2-TASK-2.1

极端风险和候选事件案例复核：固定种子抽取 447 个案例，独立前车匹配和 TTC/DRAC 重算全部一致；399 个 C 类极端/阈值敏感案例、48 个 D 类普通对照，未发现确定性 A 类计算冲突。物理真实性与 B 类几何判断仍需人工/独立复核。报告：`docs/STAGE_0_2_TASK_2_1_EXTREME_REVIEW_2026-10-10.md`。

## RES-STAGE-0.2-TASK-2.2

447 个任务 2.1 案例的同车辆对持续性、探索性运动学差分和几何证据边界诊断；自动 C=349、D=98，代表性人工复核包 48 个。人工判断未完成。

## RES-STAGE-0.2-TASK-2.2.1
连续段边界修复：447 案例多帧 297、单帧 3、间歇 1、边界 25、无极端 121；C=349、D=98；48 个案例按显式配额选择。

## RES-STAGE-0.2-TASK-2.2.1-FINAL-FIX
连续风险边界与段统计修复，447 案例重新验证，48 案例人工复核包重绘。产物：`code/outputs/formal/calibration/stage_0_2_task_2_2_1_20261011_r9/`；报告：`docs/STAGE_0_2_TASK_2_2_1_FINAL_FIX_2026-10-11.md`。

## RES-STAGE-0.2-TASK-2.3
NGSIM 风险测量质量与稳健性综合收口；完成风险段 oracle、447 案例精确中心定位、四源全量质量分母与 S0/S1/S2 探索性事件重提取。报告：`docs/STAGE_0_2_TASK_2_3_QUALITY_ROBUSTNESS_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_3_20261011_r3/`。

## RES-STAGE-0.2-TASK-2.4

正式事件提取等价性与风险稳健性最终验证。四源独立重提取与正式 5,381 事件逐成员一致；S1 真实质量条件重跑不改变事件数；S2a/b/c/d 事件数为 5,366/5,353/5,263/5,235；连续暴露分段完成。报告：`docs/STAGE_0_2_TASK_2_4_EVENT_EQUIVALENCE_2026-10-11.md`；完整包：`code/outputs/formal/calibration/stage_0_2_task_2_4_20261011_r2/`。科学 Gate、Protocol Lock 和正式风险规则仍未通过/冻结。

## RES-STAGE-0.2-TASK-2.5

源端风险事件阈值、最小持续时间与物理合理性联合验证。复用任务 2 的 6×4 正式网格，新增事件级特征、参数对应、因果确认时刻、采样敏感性、文献矩阵和 24 个案例。报告：`docs/STAGE_0_2_TASK_2_5_THRESHOLD_VALIDATION_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_5_20261011_r1/`。参数仍为 Proposal，科学 Gate 未通过。


## RES-STAGE-0.2-TASK-2.5.1

P1/P2/P3 源端风险事件规则针对性验证：成员级跨参数对应、24 个真实案例新图册、实际观测确认时刻、极端值压力诊断、采样公平性状态和文献元数据更正。P1=1,900、P2=4,545、P3=8,523、工程参考=5,381；参数仍为 Proposal，科学 Gate 未通过。报告：`docs/STAGE_0_2_TASK_2_5_1_TARGETED_VALIDATION_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_5_1_20261011_r2/`。


## RES-STAGE-0.2-TASK-2.5.2

关键差异案例分析：中心事件精确成员归属与附近事件分离，P2-only、P3-only 和三规则确认时刻差异案例，P2 仍为 Proposal。报告：`docs/STAGE_0_2_TASK_2_5_2_KEY_DIFFERENCE_CASES_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_5_2_20261011_r1/`。


## RES-STAGE-0.2-DECISION-RATIFICATION

研究者已确认的 Stage 0.2 风险设计归档及四来源 tau/P2 实证核定：tau=15.364279 s，来源中位数与实现冲突见报告；Scientific Gate 和正式实现仍未完成。报告：`docs/STAGE_0_2_DECISION_RATIFICATION_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_decision_ratification_20261011_r1/`。


## RES-STAGE-0.2-RHO-TIMESCALE

rho 时间尺度合理性诊断：tau=15.364279 s，完成四源分布、TTC 分箱暴露/贡献、tau/2/2tau 和极端压力分析；正式区域 burden 仍 Unresolved。

## RES-STAGE-0.2-FORMAL-RISK-MEASUREMENT

隔离式正式风险测量接口与 P2 独立复核：4,545 个事件与 Task 2.5.1 参考一致；包含 rho、状态贡献上下界、固定窗口原语和 100/200 ms 语义构造审计。目标区域和评价窗口仍未决。报告：`docs/STAGE_0_2_FORMAL_RISK_MEASUREMENT_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_formal_risk_measurement_20261011_r1/`。

## RES-STAGE-0.2-FORMAL-RISK-MEASUREMENT-CONSISTENCY-REPAIR

正式风险测量三个确定性实现问题修复：区域外贡献顺序、完整车辆对统计、NGSIM 诊断时钟连续性。P2=4,545，唯一后车=2,512，唯一车辆对=3,072。报告：`docs/STAGE_0_2_FORMAL_RISK_MEASUREMENT_CONSISTENCY_REPAIR_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_formal_risk_measurement_20261011_r2/`。
