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
| Stage 0.3 最终科学验收与正式关闭 | `docs/STAGE_0_3_SCIENTIFIC_ACCEPTANCE_2026-10-16.md` |
| Stage 0.4 通信数据源下载前调查（当前） | `docs/STAGE_0_4_TASK_0_4_1_DATASET_SURVEY.md` |


## Stage 0.2 综合收口入口

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。

Stage 0.5 场景设计审计：docs/STAGE_0_5_TASK_0_5_0_SCENARIO_DESIGN_AUDIT.md。只读审计确认真实职责分离、正式输入候选、pNEUMA schema 接口冲突、SUMO 工程缺口和覆盖统计限制；未生成 SUMO 样本、未通过 Stage 0.5 Gate。

Stage 0.5.1 正式真实参考重建：`docs/STAGE_0_5_TASK_0_5_1_REAL_REFERENCE_REBUILD.md`、`RES-STAGE-0.5-REAL-REF-R2`。Stage 0.5.2 分场景覆盖协议候选：`docs/STAGE_0_5_TASK_0_5_2_COVERAGE_PROTOCOL_DESIGN.md`。两项均保持 `pending_simulation_sample`，未运行 SUMO、未冻结阈值或验证划分。

Stage 0.5.4-A 校准准入审计：`docs/STAGE_0_5_TASK_0_5_4A_CALIBRATION_READINESS.md`、`RES-STAGE-0.5-CALIBRATION-READINESS-V1`。给出 P2 测量等价性矩阵（0 阻断）、校准窗口统计与需求可识别性、候选网络/车型/时间/容差协议与准入清单（`ready_to_start_stage_0_5_4b=false`）。未读取验证窗口、未冻结科学参数、Gate 不变。

Stage 0.5.3 SUMO 工程基线：`docs/STAGE_0_5_TASK_0_5_3_SUMO_BASELINE_ENGINEERING.md`、`RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1`。US-101 `generic_highway_candidate` 完成 baseline 与 measurement probe 两个 engineering-only fixture，状态/跟驰/净间距/闭合速度/TTC/暴露/工程 P2 与校准验证隔离均已接通；正式网络、需求、车型映射、时间步、暖机窗口、P2 正式等价性、覆盖容差和独立验证仍未完成。

Stage0.5.4-A+定向补充入口：docs/STAGE_0_5_TASK_0_5_4A_SUPPLEMENT_CALIBRATION_GAPS.md、RES-STAGE-0.5-CALIBRATION-GAPS-V1；脚本run_stage_0_5_calibration_gaps.py、benchmark_stage_0_5_calibration_loads.py、finalize_stage_0_5_calibration_gaps.py。所有科研配置Proposal，停在研究者决策节点。


B0入口：`docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md`、`RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1`；执行`code/scripts/run_stage_0_5_exploratory_response.py`，模块`stage_0_5_exploratory_response.py`/`stage_0_5_exploratory_analysis.py`，测试`test_stage_0_5_exploratory_response.py`。旧批次封闭，哈希不允许以修复后源码继续。2026-10-18 AAD-0.5.4-B0（RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1）：受限探索完成19/23次，4次高输入seed20261019响应未运行。统一27.78m/s上限、空初态、ballistic显式、internal.05/recorded.1、action.1、sigmaStep1；三个基准输入1087.364/1449.818/1648veh/h/lane仅实现局部密度10.37–15.75、均速约27.1，局部低速/P2均0。tau2三次末期未服务21/22/71，入口main0约2.5–20.1m有低速插入/加速，局部段无拥堵。B0-EXEC-STOP-01：原调度器未因completed+blocker停止，发现后人工停止，源码停止后修复并测试；最后worker峰值内存Unverified。推荐先批准需求边界/最小结构对照，不继续参数搜索掩盖状态支持缺口。所有结果exploratory_diagnostic_only、scientific_claim_eligible=false；Gate=pending_simulation_sample、Calibration Ready=false、Reality Coverage Accepted=false、正式容差Tolerance Not Yet Justified、Energy Distance上界Not Identifiable；B0实验验证输入0；根全量回归无过滤打开历史Stage0.2全源事件/案例产物，任务级验证访问不能认证（B0-VALIDATION-SCOPE-02）；数据隔离验收不Accepted。无holdout/正式校准/锁/Stage I。依据：docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md、同ID证据和execution_ledger。

## B1隔离与边界机制入口

报告`docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md`；执行`code/scripts/run_stage_0_5_boundary_bottleneck.py`；隔离/停止/分析模块`code/src/riskprop/stage_0_5_boundary_bottleneck.py`、`code/src/riskprop/stage_0_5_b1_isolation.py`、`code/src/riskprop/stage_0_5_b1_analysis.py`；便携验证`code/scripts/verify_stage_0_5_boundary_evidence.py`。旧批次封闭，仅已授权新计划可执行。B1（RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1）按阻断提前结束：V1失败A后7次未启动，V2 A有效/B警告/C阻断/D未启动，累计4次尝试；无补跑或新seed。A/B局部均速27.1088/26.5152m/s、密度16.3208/16.8197、低速0；C记录2.4007m/s、93.8653veh/km/lane、低速80.1719%、末期未服务252，但停车位移检查与冻结回溢资格阻断，不能作为有效校准样本。D只有静态/空加载检查，动态未知。

## B1.1 独立测量契约入口

报告：`docs/STAGE_0_5_TASK_0_5_4B1_1_STOPPING_AND_SPILLBACK_CONTRACT.md`；计划：`docs/plans/2026-10-19-stage-0-5-4b1-1.md`；入口：`code/scripts/run_stage_0_5_stopping_spillback.py`；便携校验：`code/scripts/verify_stage_0_5_stopping_evidence.py`。结果`RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1`；精确停车Pending、队列阈值Candidate、旧B1状态不变。

## B1.1-S 停车可观测性入口

报告：`docs/STAGE_0_5_TASK_0_5_4B1_1S_STOPPING_OBSERVABILITY.md`；计划：`docs/plans/2026-10-19-stage-0-5-4b1-1s.md`；入口：`code/scripts/run_stage_0_5_stopping_observability.py`；便携校验：`code/scripts/verify_stage_0_5_observability_evidence.py`。结果`RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1`；非决策步停车精确可核验、决策步停车仍Bounded、无调试二进制、旧B1/B1.1状态不变。


## 2026-10-19 B1.2 分层准入与机制再验证

报告docs/STAGE_0_5_TASK_0_5_4B1_2_BOUNDARY_BOTTLENECK_REVALIDATION.md；计划docs/plans/2026-10-19-stage-0-5-4b1-2.md；入口code/scripts/run_stage_0_5_boundary_revalidation.py；便携校验code/scripts/verify_stage_0_5_revalidation_evidence.py；结果RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2。前置近零终速异常阻断，主矩阵0/8。


## 2026-10-19 B1.2-N（独立工程观测）

`RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1`：独立B1.2-N工程任务。固定SUMO1.26源码完整谓词和调用顺序已审计；无停车任务的fresh/immutable生命周期可用doubleMax不变量，同edge常规停车仅非决策步可作充分条件。一般myStopDist不能由公开getter等价恢复。新候选`b12n-near-zero-observability-v1`不以位移/终速选择上下文，1e-6m不变。3个30s微型运行：2879边，2876精确全过（其中1负近零后处理），3 bounded，0近零未决/不可评价/工程错误；最大残差1.3988810110276972e-14m。冻结前203项受控合成通过。

正近零非决策步清零运行边未出现（Not Observed），未满足运行前冻结的共同准入条件；integration_allowed=false，C/D计划冻结被拒绝，均Not Attempted，未追加试验/搜索。新主矩阵禁止且0次。旧B1.2阻断/0-8/D未运行和所有历史证据不变。下一步由研究者决定正近零覆盖设计与未来政策，再另批接入/主矩阵；不自动继续。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2N_NEAR_ZERO_AND_INTEGRATION.md`；证据同ID目录。科研Gate/ready/现实覆盖/锁/StageI状态不变，科学阈值未批准。
