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
