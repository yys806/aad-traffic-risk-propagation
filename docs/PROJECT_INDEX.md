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
