## Current — P4 Task2最小实现 (2026-11-04)

IMPLEMENTATION_COMPLETE_WITH_LIMITATIONS。D01–D08全Agreed；固定处理前完整资格名单、固定N等权Y上下界及严格Action/独立P4v1/P3外桥已实现。172项离线测试（88新+84历史）和15项独立数学检查通过；不发布缺乏完整真实scope的区域Y。

P7验收保持ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS；Formal A/Qualified仍0，F0/总体T_R–T_P Unknown；Gate/Protocol Lock不变，Stage1.1 NOT_AUTHORIZED。无新增SUMO/seed/Pilot/V/holdout读取。统一定义仍v0.4/27项；正式region/window/Action数值未冻结。

[报告](docs/research/P4/P4_TASK2_FINAL_REPORT.md) · [规范/契约入口](docs/research/P4/README_v1.md) · [决定](docs/research/P4/P4_RESEARCHER_DECISIONS_20261104.md) · [便携证据](evidence/research/P4_TASK2_20261104/README.md)。下方保留各历史时点记录，不据旧待决状态覆盖本次Agreed。

## Current — P4 Task1测量审计 (2026-11-03)

AUDIT_AND_OPERATIONALIZATION_COMPLETE_WITH_LIMITATIONS。完成Action→Formal风险贡献→固定区域/窗口/名单的操作化；12表247字段契约仍Proposal。已复现动作持续性/名单守卫/辅助暴露输入限制，未改科学核心。84项定向测试及27项离线例子通过，新增交通运行0；不是新增正式实验结果。

P7 Task2.1工程验收保持ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS。Formal A/独立Qualified仍0；风险/F0/总体T_R–T_P Unknown；Gate/Protocol Lock不变，Stage1.1 NOT_AUTHORIZED。统一定义仍[v0.4/27项](docs/research/definitions/README.md)。

[报告](docs/research/P4/P4_TASK1_FINAL_REPORT.md) · [规范](docs/research/P4/P4_ACTION_AND_RISK_MEASUREMENT_SPEC.md) · [数据契约](docs/research/P4/P4_MEASUREMENT_DATA_CONTRACT.md) · [待决](docs/research/P4/P4_RESEARCHER_DECISIONS.md) · [证据](evidence/research/P4_TASK1_20261103/README.md)。下方保留历史任务状态。

## Current — P7 Task2.1工程验收 (2026-11-03)

ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS。唯一Enabled v2复验通过（1次、seed20261103），基准未重跑。最大实际减速度1.0 m/s²，无emergency/碰撞/teleport；52次实际采用、39命令、326执行、352动作。首次命令2.8 s、首个实际差异2.9 s；8.0 s过期恢复20 m/s且后续无消息输入。共同351点比较有效，最大速度差2.649473720 m/s、加速度差2.719870887 m/s²，仅ENGINEERING_DIAGNOSTIC_ONLY。 v1失败不改，正式科研资格/阶段不升级。

[复验报告](docs/research/P7/P7_TASK2_1_FINAL_REPORT.md) · [证据](evidence/research/P7_TASK2_1_20261103/README.md)。后续P5等不在本任务启动；下方保留历史状态。

## Current — P7 Task2 (2026-11-03)

消息驱动纵向策略、Enabled/Disabled gate、真实TraCI执行与P3/P4接线已实现，Adoption边界已Agreed。三条件各运行一次；Enabled v1异常制动使整体验收阻塞，v2修正仅离线测试；不是正式科研实验就绪。

[当前报告](docs/research/P7/P7_TASK2_FINAL_REPORT.md) · [八项决策](docs/research/P7/P7_RESEARCHER_DECISIONS_20261103.md) · [统一科研定义v0.4/27项](docs/research/definitions/README.md)。Formal A/Qualified仍0，风险效应Unknown，Gate/Protocol Lock与Stage1.1授权不变。下方保留旧任务历史。

## P2 Task7 source timestamp backfill — 2026-11-02

研究者已授权全575完成轨迹源时间回溯，576计划逐条保留（1原失败Unknown、72 N0 Not Applicable、503实际干预签名成立）；288区间提前1.75s。原359/47/0不改，本次版本化派生overlay359/119/0；Task8的119已独立逐单位复现。W8/Qualified未知资格不升级，1728原标签、原audit/detector/参数、V与双η结论不改；新增SUMO/seed/V均0。

Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS；Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock BLOCKED；StageI READY_ENGINEERING_ONLY；Stage1.1 NOT_AUTHORIZED。

[独立更正附录](docs/research/P2/P2_TASK7_SOURCE_TIMESTAMP_BACKFILL_REPORT.md)；原Task7/Task8报告保留历史字节，本任务无新实验或独立样本。

## P2 Task8 — 2026-11-02

Task8 bounded recovery：268计划/267完成/1失败或未执行；仅源端调整、原域/a1b1不变。Low Micro、Medium Macro、High Macro2a与High局部非Cohort支持恢复；Low Cohort/Macro、Medium Cohort仍缺支持。三中心配置仅候选，J78（state63）固定配置V NOT_EXECUTED_TRUTH_SUPPORT_INSUFFICIENT，seeds0；W8/Qualified/真实最早物理桥接不足，两η情景Not established。

Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS；Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock BLOCKED；StageI READY_ENGINEERING_ONLY；Stage1.1 NOT_AUTHORIZED。

[报告](docs/research/P2/P2_TASK8_FINAL_REPORT.md)；CALIBRATION/SUPPLEMENTARY_ONLY，不新增正式结果资格。

## P2 Task7 — 2026-11-02

Task7探索576计划单位，575完成、1次TraCI启动失败保留Unknown；三层独立truth先冻结，83候选/47808主评价及条件单因素/交互/压力完成。W9/constant/θ1/h1/q.05、Macro w2仅C候选，无独立V或稳定性认证。J765下有限域乐观V需54534运行/14.6h/69.5GiB，未运行V、未消耗V seed。Macro目标强度格、局部点和低/中密度阳性支持不足；Qualified/F0及任意最早物理桥接仍Unknown。

Formal A=0、独立Qualified=0、F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS，Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS，Protocol Lock BLOCKED，StageI READY_ENGINEERING_ONLY，Stage1.1 NOT_AUTHORIZED。

[Task7报告](docs/research/P2/P2_TASK7_FINAL_REPORT.md)；本项是CALIBRATION_ONLY研究记录，不新增正式结果资格或阶段通过。

# AAD 项目交接

> 状态快照日期：2026-10-12（**历史交接信息**，部分阶段描述已过时）。当前阶段、Gate 与下一步以 `AI_CONTEXT/00_PROJECT_STATE.md` 和 `docs/RESEARCH_STATUS.md` 为准；本文件只保留稳定边界和当时的精确继续点，实时文件状态仍需用 Git 和机器产物核验。

## 1. 项目目标

验证来源可追溯且被控制器采用的远端风险消息，能否在普通物理影响到达目标区域前改变车辆动作与区域总体风险。

## 2. 当前阶段（2026-10-12 快照，历史）

当前位于阶段 0。主任务是阶段 0.2 NGSIM风险审计，阶段 0.3 pNEUMA城市运动学分布同步整理；阶段 1.1未启动。

本段为 2026-10-12 快照时点的事实；其后进展（阶段 0.3 已关闭、阶段 0.5 现被交互相容层阻断）不在此追写，请读 `AI_CONTEXT/00_PROJECT_STATE.md`。

## 3. 当前事实

阶段 0.1工程链已验证；Stage 0.2 已在研究者批准的有限范围内 `Completed / Closed`（四源 NGSIM、100 ms、P2=4,545）；Stage 0.3 pNEUMA 描述性统计、质量审计与 Stage 0.5 参考接口已完成并通过独立复算，为 Gate Pass Candidate，科学验收与未冻结参数待研究者。SPMD RV_RX只支持接收状态连续性；其他科学参数未冻结。

## 4. 当前未知

NGSIM独立物理真实性与质量验收标准尚未完成/批准；100/200ms不等价。pNEUMA运动学分布、packet级通信、仿真—现实覆盖、科学容差、样本量和核心效应均未完成或未确认。

## 5. 当前 Gate

阶段 0.2 已在有限范围内通过；阶段 0.3 为 Gate Pass Candidate 待研究者审核；阶段 0.5和0.6未闭合；阶段 0.4受外部 Packet访问限制，可按有限证据边界冻结。协议锁未通过。

## 6. 已确认研究分工

NGSIM负责前车关系、跟驰风险指标和风险事件；研究者已于 2026-09-10 批准 pNEUMA 前车推断与人工复核退役，pNEUMA只负责速度、纵向加速度与车型分布；SPMD负责通信可观测边界。

## 7. 数据位置

原始数据统一位于根目录 `dataset/`，包含 NGSIM、pNEUMA和SPMD。该目录本机保留且不进入 Git。

## 7.1 论文与研究材料位置（2026-10-23 更新）

- 当前最新版论文只在 **Overleaf**，仓库不保留活动 `.tex` 论文源；根目录 `paper/`（`paper/主论文/main.tex`）已于 2026-10-23 退役，不得恢复本地论文编辑流程，未登记真实链接前不写 Overleaf URL。
- 历史论文 PDF、图稿、组会 PPT 与辅助笔记位于本机 `D:\shen\OB\科研\TJU\AAD`：`AAD\`（00–05 辅助笔记）、`历史Paper\paper\`（历史 PDF）、`历史Paper\figure\`（图稿/PPT）、`组会PPT\`、`组会笔记\`。这些材料仅提供历史与辅助上下文，不进入 Git，也不得当作最新版正文或当前状态。
- 当前实现、实验结果与阶段状态仍以本 GitHub 仓库为准；OB 笔记不能覆盖仓库当前状态。导航入口：`docs/PAPER_AND_MATERIAL_SOURCES.md`。

## 8. 当前代码

正式实现位于 `code/src/riskprop/`，入口位于 `code/scripts/`，测试位于 `code/tests/`。新代码使用 `stage_X_Y`或任务语义命名。

## 9. 历史代码与证据

旧实现位于各 `legacy/`；旧编号文档位于 `docs/归档/旧实验编号材料/`；旧输出和证据位于 `code/outputs/history/`、`evidence/history/`。不得默认接回当前路径。

## 10. 证据规则

索引只负责导航。结论应回到 audit、冻结配置、manifest、provenance、SHA256SUMS、原始表和代码交叉核验。

## 11. 科研停止规则

Gate未通过时，不签协议锁、不看 locked holdout、不降低阈值、不挑种子、不运行阶段 1.1，也不把工程或校准结果写成主效应。

## 12. 当前结果边界

现有结果全部不可支持“类超距效应已经存在”。消息交付、采用、动作变化和风险变化必须分别记录与验证。

## 13. 精确继续点

1. 研究者审阅 Stage 0.3 Gate Pass Candidate 包（`code/outputs/formal/calibration/stage_0_3_pneuma_kinematics_20261012_r1/`），裁决连续性容差、描述性阈值、车型映射、适用范围与科学 Gate。
2. 按新分工重建阶段 0.5真实参考并生成 SUMO校准样本。
3. 重算阶段 0.6 readiness；所有 Gate通过后再签协议锁。

## 14. 维护入口

AI 快速恢复入口见 `AI_CONTEXT/00_PROJECT_STATE.md`；计划与执行记录见 `docs/论文实验推进/`；机器状态见 `docs/PROJECT_REGISTRY.json`；阶段、结果、历史分别见 `docs/STAGE_INDEX.md`、`docs/RESULTS_INDEX.md`、`docs/HISTORY_INDEX.md`；论文与材料位置见 `docs/PAPER_AND_MATERIAL_SOURCES.md`。

## 15. 完成定义

文档与注册表同步、真实路径存在、证据可校验、测试覆盖实际入口、失败与不确定记录保留，才可声明相应工程任务完成；科研 Gate仍需独立判定。
