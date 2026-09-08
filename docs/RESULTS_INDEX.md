# AAD 结果索引

> 最后核对：2026-09-08  
> 本索引记录机器产物和证据边界，不把 calibration 或工程验证提升为科学主效应。

## RES-E00-PRIMARY-V3

- 实验：E00。
- 位置：`code/outputs/formal/E00/e00_real_sumo_20260907_primary_v3/`。
- 关键文件：`e00_report.json`、各 cell 五表、manifest、SHA-256、独立分析。
- 观察：四格唯一科学差异为 `source_present` 与 `channel_enabled`；处理前等价、运行隔离、时钟、生命周期与消息生命周期审计通过；物理路径为断开。
- 证据等级：`Verified engineering only`。
- 科学资格：`scientific_claim_eligible=false`。

## RES-E00-ENV-COMPARE-V3

- 实验：E00。
- 位置：`code/outputs/formal/E00/e00_real_sumo_environment_comparison_20260907_v3.json`。
- 观察：主环境与 clean venv 的结构比较为 `structural_match=true`。
- 证据等级：`Verified engineering reproducibility`。
- 科学资格：`scientific_claim_eligible=false`。

## RES-E15A-NGSIM-V2

- 实验：E15-A。
- 位置：`code/outputs/formal/calibration/e15a_ngsim_v2/audit.json`。
- 数据：US-101 三个完整窗口与 Lankershim 完整窗口。
- 观察：四个来源均形成 state 和 event 统计；locked holdout 未打开。
- 状态：`pending_pneuma_and_blind_reaudit`。
- 科学资格：`scientific_claim_eligible=false`。

## RES-E15A-PNEUMA-MAPMATCH-V2

- 实验：E15-A。
- 位置：`code/outputs/formal/calibration/e15a_pneuma_mapmatch_v2/audit.json`。
- 观察：1,239,475 个点形成地图匹配和候选前车分类；候选前车关系尚未人工验证。
- 状态：`pending_manual_map_and_leader_audit`。
- 科学资格：`scientific_claim_eligible=false`；不得据此计算 pNEUMA TTC。

## RES-E15A-PNEUMA-QA-V5

- 实验：E15-A。
- 位置：`code/outputs/formal/calibration/e15a_pneuma_manual_qa_v5/audit.json`。
- 观察：300条盲样本、四层各75条、48条平衡试标。
- 状态：`pending_human_round1`；当前未发现导出的 completed CSV。
- 科学资格：`scientific_claim_eligible=false`。

## RES-E16A-OBS-V3

- 实验：E16-A。
- 位置：`code/outputs/formal/calibration/e16a_observability_v3/audit.json`。
- 观察：RV_RX 有17,481,111行、7,601个 device-trip；官方 Packet 当前返回 HTTP 403。
- 结论边界：仅 `receive_state_continuity_only`；没有 packet loss、latency 或 adoption 估计。
- 科学资格：`scientific_claim_eligible=false`。

## RES-E17A-REAL-REF-V1

- 实验：E17-A。
- 位置：`code/outputs/formal/calibration/e17a_real_reference_v1/audit.json`。
- 观察：25,000条运动学样本、20,000条跟驰样本、4,758条风险事件记录；pNEUMA TTC 未纳入。
- 状态：`pending_pneuma_manual_and_simulation_sample`。
- 科学资格：`scientific_claim_eligible=false`。

## RES-E01-PRELOCK-V2

- 实验：E01。
- 位置：`code/outputs/formal/calibration/e01_prelock_validation_v2/audit.json`。
- 观察：解析 TTC/DRAC/PET/碰撞与四类物理路径真值通过；时间步方向一致，0.05与0.02秒当前差值约0.00298695。
- 状态：`pending_e15_e17_and_frozen_tolerances`；`zero_tolerance=null`。
- 科学资格：`scientific_claim_eligible=false`。

## RES-PROTOCOL-READINESS-V1

- 实验：E01（汇总 E15-A、E16-A、E17-A、E01 Gate）。
- 位置：`code/outputs/formal/calibration/protocol_lock_readiness_v1.json`。
- 观察：`protocol_lock_allowed=false`，`e02_allowed=false`。
- 用途：每次跨阶段前必须读取的准入哨兵。
- 科学资格：不属于科学结果。

## 结果追踪规则

新增结果必须记录：结果 ID、实验 ID、产物路径、配置/数据/代码版本来源、关键指标、Gate、科学资格、失败边界和对应论文位置。最佳结果只能在比较协议一致且证据可复算时标记；当前没有已确认的 Stage I “最佳科学结果”。
