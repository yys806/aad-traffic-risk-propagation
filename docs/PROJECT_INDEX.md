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
| 论文与文献 | `paper/`；文献在 Zotero（`TJU → AAD`），索引见 `doc/literature-notes/` |

## 当前代码入口

| 阶段 | 实现 | 脚本 | 测试 |
|---|---|---|---|
| 0.1 | `stage_0_1_sumo.py` | `run/analyze/compare_stage_0_1_*` | `test_stage_0_1_sumo.py` |
| 0.2 | `ngsim_risk_calibration.py` | `run_stage_0_2_ngsim.py` | `test_ngsim_risk_calibration.py` |
| 0.3 | `pneuma_urban_kinematics.py` | `run_stage_0_3_pneuma_kinematics.py`、`verify_stage_0_3_independent.py` | `test_pneuma_urban_kinematics.py`、`test_real_trajectory.py`、`test_simulation_real_coverage.py`（0.5 接口质量契约） |
| 0.4 | `communication_observability.py` | `profile/run_stage_0_4_*` | `test_communication_observability.py` |
| 0.5 | `simulation_real_coverage.py` | `prepare/run_stage_0_5_*` | `test_simulation_real_coverage.py` |
| 0.6 | `prelock_metrics.py`、`prelock_validation.py`、`protocol_lock.py` | `run_stage_0_6_*`、readiness | 对应三组测试 |

## 2026-10-10 任务 1.4

轨迹身份与事件可靠性收尾：[核验报告](STAGE_0_2_TASK_1_4_RELIABILITY_CLOSURE_2026-10-10.md)。复现入口 `code/scripts/verify_ngsim_task_1_4.py`；便携证据 `RES-STAGE-0.2-TASK-1.4`。

| 任务 1.5 跨时钟前车匹配收尾 | `docs/STAGE_0_2_TASK_1_5_LEADER_MATCHING_CLOSURE_2026-10-10.md` |
| 任务 2 NGSIM 风险质量与事件规则审计 | `docs/STAGE_0_2_TASK_2_RISK_QUALITY_AUDIT_2026-10-10.md` |
| 任务 2.1 极端风险值与候选事件真实性复核 | `docs/STAGE_0_2_TASK_2_1_EXTREME_REVIEW_2026-10-10.md` |
| Stage 0.3 pNEUMA 城市运动学校准与验收准备 | `docs/STAGE_0_3_PNEUMA_KINEMATICS_2026-10-12.md` |
| Stage 0.3 R2 边界修复与验收准备 | `docs/STAGE_0_3_BOUNDARY_REPAIR_R2_2026-10-16.md` |
| Stage 0.3 最终科学验收与正式关闭（当前） | `docs/STAGE_0_3_SCIENTIFIC_ACCEPTANCE_2026-10-16.md` |


## Stage 0.2 综合收口入口

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。
