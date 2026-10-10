# AAD 项目索引

## AI 快速恢复

- 当前快照：`AI_CONTEXT/00_PROJECT_STATE.md`
- 研究、架构、数据流、模块、实验、决策、问题与重要变化：`AI_CONTEXT/01_RESEARCH_CONTEXT.md` 至 `AI_CONTEXT/08_CHANGELOG.md`

| 想了解什么 | 首选入口 |
|---|---|
| 项目边界和下一步 | `PROJECT_CONTEXT.md` |
| 总体排期 | `docs/论文实验推进/总计划.md` |
| 当前科研状态 | `docs/RESEARCH_STATUS.md` |
| 阶段与 Gate | `docs/STAGE_INDEX.md`、`docs/PROJECT_REGISTRY.json` |
| 结果和证据 | `docs/RESULTS_INDEX.md`、`evidence/` |
| 历史记录 | `docs/HISTORY_INDEX.md`、`docs/归档/项目记录/` |
| 旧编号材料 | `docs/归档/旧实验编号材料/` |
| 原始数据 | `dataset/` |
| Stage 0 基线核查 | `docs/STAGE_0_BASELINE_AUDIT_2026-10-09.md` |
| 任务 1 NGSIM 核验 | `docs/STAGE_0_2_TASK_1_NGSIM_INTEGRITY_2026-10-09.md` |
| 任务 1.1 NGSIM 来源与分段核查 | `docs/STAGE_0_2_TASK_1_1_NGSIM_SOURCE_SEGMENTATION_2026-10-09.md` |
| 任务 1.2 US-101 TXT 接入与 Lankershim 源恢复 | `docs/STAGE_0_2_TASK_1_2_TXT_SOURCE_RECOVERY_2026-10-09.md` |
| 任务 1.3 轨迹身份与完整测量链验证 | `docs/STAGE_0_2_TASK_1_3_TRAJECTORY_IDENTITY_VALIDATION_2026-10-10.md` |
| 论文与文献 | `paper/`、`literature/` |

## 当前代码入口

| 阶段 | 实现 | 脚本 | 测试 |
|---|---|---|---|
| 0.1 | `stage_0_1_sumo.py` | `run/analyze/compare_stage_0_1_*` | `test_stage_0_1_sumo.py` |
| 0.2 | `ngsim_risk_calibration.py` | `run_stage_0_2_ngsim.py` | `test_ngsim_risk_calibration.py` |
| 0.3 | `calibration.py` | 待补运动学统计入口 | `test_calibration.py` |
| 0.4 | `communication_observability.py` | `profile/run_stage_0_4_*` | `test_communication_observability.py` |
| 0.5 | `simulation_real_coverage.py` | `prepare/run_stage_0_5_*` | `test_simulation_real_coverage.py` |
| 0.6 | `prelock_metrics.py`、`prelock_validation.py`、`protocol_lock.py` | `run_stage_0_6_*`、readiness | 对应三组测试 |

## 2026-10-10 任务 1.4

轨迹身份与事件可靠性收尾：[核验报告](STAGE_0_2_TASK_1_4_RELIABILITY_CLOSURE_2026-10-10.md)。复现入口 `code/scripts/verify_ngsim_task_1_4.py`；便携证据 `RES-STAGE-0.2-TASK-1.4`。

| 任务 1.5 跨时钟前车匹配收尾 | `docs/STAGE_0_2_TASK_1_5_LEADER_MATCHING_CLOSURE_2026-10-10.md` |
| 任务 2 NGSIM 风险质量与事件规则审计 | `docs/STAGE_0_2_TASK_2_RISK_QUALITY_AUDIT_2026-10-10.md` |
| 任务 2.1 极端风险值与候选事件真实性复核 | `docs/STAGE_0_2_TASK_2_1_EXTREME_REVIEW_2026-10-10.md` |
