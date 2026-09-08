# AAD 结果索引

> 核对日期：2026-09-08。每项同时给出 Git 内便携证据和本机完整产物。便携证据用于克隆后核验，完整产物用于深度复算；二者都不能越过既有科学 Gate。

## RES-E00-PRIMARY-V3

- 实验：E00；状态：工程验证通过、科学 Gate 未通过。
- 便携证据：`evidence/results/RES-E00-PRIMARY-V3/e00_report.json`、`independent_analysis.json` 及各 cell 审计文件。
- 本地完整产物：`code/outputs/formal/E00/e00_real_sumo_20260907_primary_v3/`。
- 指标/结论：处理前等价、隔离、时钟和生命周期通过；只有 s1c1 的 `adopted_count=1`；物理路径未接通。
- 论文位置：阶段 0 E00 执行记录；`scientific_claim_eligible=false`。

## RES-E00-ENV-COMPARE-V3

- 实验：E00；便携证据：`evidence/results/RES-E00-ENV-COMPARE-V3/environment_comparison.json`。
- 本地完整产物：`code/outputs/formal/E00/e00_real_sumo_environment_comparison_20260907_v3.json`。
- 指标/结论：`structural_match=true`，只证明双环境结构一致；`scientific_claim_eligible=false`。

## RES-E15A-NGSIM-V2

- 实验：E15-A；便携证据：`evidence/results/RES-E15A-NGSIM-V2/`；本地完整产物：`code/outputs/formal/calibration/e15a_ngsim_v2/`。
- 指标：US-101 三窗事件数 470/613/898，有效 TTC 行数 411250/450108/453512；Lankershim 事件 2777、有效 TTC 483098。
- 结论：NGSIM 可形成参考，但 locked holdout 未打开，仍需 pNEUMA 与盲重审；`scientific_claim_eligible=false`。

## RES-E15A-PNEUMA-MAPMATCH-V2

- 实验：E15-A；便携证据：`evidence/results/RES-E15A-PNEUMA-MAPMATCH-V2/`；本地完整产物：`code/outputs/formal/calibration/e15a_pneuma_mapmatch_v2/`。
- 指标：1,239,475 点、601,633 个候选 leader、比例 0.641332、最近道路距离 p95=4.95366 m。
- 结论：候选已生成但未人工验证，TTC 未生成；`scientific_claim_eligible=false`。

## RES-E15A-PNEUMA-QA-V5

- 实验：E15-A；便携证据：`evidence/results/RES-E15A-PNEUMA-QA-V5/`；本地完整产物：`code/outputs/formal/calibration/e15a_pneuma_manual_qa_v5/`。
- 指标：300 条盲样本、四层各 75、48 条 pilot；Round 1 未完成。
- 结论：当前唯一人工任务；密封抽样键不进入 Git，AI 不代替标注；`scientific_claim_eligible=false`。

## RES-E16A-OBS-V3

- 实验：E16-A；便携证据：`evidence/results/RES-E16A-OBS-V3/`；本地完整产物：`code/outputs/formal/calibration/e16a_observability_v3/`。
- 指标：17,481,111 行、7,601 个 device-trip；官方 Packet HTTP 403；packet schema、时延、丢包、采用均不可观测。
- 结论：只支持 `receive_state_continuity_only`；`scientific_claim_eligible=false`。

## RES-E17A-REAL-REF-V1

- 实验：E17-A；便携证据：`evidence/results/RES-E17A-REAL-REF-V1/audit.json`；本地完整产物：`code/outputs/formal/calibration/e17a_real_reference_v1/`。
- 指标：运动学 25,000、跟驰 20,000、风险事件 4,758；pNEUMA TTC 和仿真样本均未纳入。
- 结论：只是部分现实参考；`scientific_claim_eligible=false`。

## RES-E01-PRELOCK-V2

- 实验：E01；便携证据：`evidence/results/RES-E01-PRELOCK-V2/audit.json`；本地完整产物：`code/outputs/formal/calibration/e01_prelock_validation_v2/`。
- 指标：解析真值、物理路径真值、方向一致性通过；0.05 与 0.02 s 差值为 0.0029869451697126514；零容差仍为 null。
- 结论：技术检查不能替代科学容差冻结；`scientific_claim_eligible=false`。

## RES-PROTOCOL-READINESS-V1

- 实验：E01 汇总 Gate；便携证据：`evidence/results/RES-PROTOCOL-READINESS-V1/protocol_lock_readiness_v1.json`。
- 本地完整产物：`code/outputs/formal/calibration/protocol_lock_readiness_v1.json`。
- 指标/结论：`protocol_lock_allowed=false`、`e02_allowed=false`；阻断来自 E15-A、E16-A、E17-A 与 E01。
- 该项是准入哨兵，不是科学结果。

## 双向追踪与证据规则

每个结果必须反向指向一个实验，每个实验必须列全其结果 ID。版本、配置和数据身份从便携证据中的 audit/config/manifest/provenance/SHA256SUMS 核验。大表、原始数据、HTML、图片、日志及密封抽样键留在本地，不进入 Git；其缺失不能被误写成不存在。当前没有 Stage I “最佳科学结果”。
