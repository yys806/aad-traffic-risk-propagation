# AAD Module Map

## 导航表

| 模块分类 | 核心文件 | 职责 | 核心类 | 核心函数 | 调用关系 | 主要依赖 |
|---|---|---|---|---|---|---|
| experiment | `code/src/riskprop/stage_0_1_sumo.py` | SUMO 四格、五表、路径与独立复算 | 无业务类 | `run_real_sumo_stage_0_1`, `analyze_real_sumo_stage_0_1` | 调用 `formal_design`、`formal_artifacts` | pandas, TraCI, SUMO |
| experiment | `code/src/riskprop/formal_runner.py` | 空 artifact smoke 与确定性 contract fixture | 无 | `run_artifact_smoke`, `run_contract_fixture` | 写入 artifact 层 | pandas |
| evaluation | `code/src/riskprop/formal_design.py` | 四格、消息生命周期、处理前一致、时钟与车辆生命周期检查 | `FormalDesignError` | `validate_four_cell_configs`, `validate_protocol_lifecycle`, `validate_pre_treatment_equivalence` | 被 runner/SUMO 调用 | pandas |
| artifact | `code/src/riskprop/formal_artifacts.py` | 五表 schema、provenance、manifest、校验和、失败账本 | `FormalArtifactError` | `build_run_manifest`, `validate_run_manifest`, `validate_theory_artifact_schema` | 被正式 runner 调用 | pandas, pyarrow, Git |
| data | `code/src/riskprop/calibration.py` | 数据/split 清单、表契约、稳健缩放与 energy distance | `CalibrationContractError` | `build_default_calibration_manifests`, `validate_real_state_table`, `energy_distance` | 被阶段 0.2/0.5 使用 | numpy, pandas |
| data | `code/src/riskprop/real_trajectory.py` | NGSIM 嵌套 ZIP 与 pNEUMA 宽表读取 | 无 | `read_ngsim_nested_csv`, `add_ngsim_leader_ttc`, `read_pneuma_wide` | 为校准模块提供表 | pandas |
| experiment | `code/src/riskprop/pneuma_urban_kinematics.py` | Stage 0.3 pNEUMA 行级解析审计（原始顺序时间/身份标记、统一可靠性掩码）、时间加权/车辆等权统计、敏感性、bootstrap、Stage 0.5 参考接口与验收包 | `CalibrationContractError`（无标志时拒绝默认可靠） | `audit_pneuma_source`, `flag_state_quality`, `integrate_time_weighted`, `compute_track_stats`, `derive_state_quality_status`, `build_stage_0_5_reference_states`, `write_acceptance_package` | 调用 `calibration` | numpy, pandas, matplotlib |
| experiment | `code/src/riskprop/ngsim_risk_calibration.py` | 标准化 NGSIM、合并风险事件、封存阶段 0.2 | 无 | `standardize_ngsim_states`, `extract_rear_end_events`, `write_stage_0_2_ngsim_package` | 调用 data 层 | pandas |
| evaluation | `code/src/riskprop/communication_observability.py` | SPMD trip 分割、RV_RX profile 与字段边界 | `CommunicationEvidenceError` | `spmd_trip_split`, `profile_rv_rx_calibration`, `build_stage_0_4_status_package` | 独立审计模块 | 标准库 |
| evaluation | `code/src/riskprop/simulation_real_coverage.py` | 稳定抽样、真实参考与 sim-real 覆盖 Gate | 无 | `deterministic_state_sample`, `write_real_reference_package`, `evaluate_simulation_coverage` | 调用 `calibration` | numpy, pandas |
| experiment | `code/src/riskprop/stage_0_5_sumo.py` | Stage 0.5 三场景候选 manifest、`generic_highway_candidate` 参数化路网与两个工程 fixture、no-message TraCI runner、SUMO-native measurement、engineering P2/exposure adapter、Stage 0.2 formal-alignment adapter、校准/验证 fail-closed 守卫 | `Stage05EngineeringError`, `Stage05AccessDenied` | `run_stage_0_5_no_message_baseline`, `compute_sumo_measurements`, `build_sumo_p2_events`, `extract_sumo_formal_p2_events`, `CalibrationValidationGuard`, `vehicle_type_mapping_candidate` | 独立于 `stage_0_1_sumo`；输出供 0.5.4 评估 | pandas, numpy, SUMO/TraCI |
| experiment | `code/src/riskprop/stage_0_5_calibration_readiness.py` | Stage 0.5.4-A 测量等价性矩阵、校准窗口统计、需求可识别性、候选分层、簇级不确定性、时间步协议、候选校准协议与准入清单 | `CalibrationReadinessError` | `run_calibration_readiness_audit`, `measurement_equivalence_matrix`, `window_summary`, `demand_identifiability`, `clustered_uncertainty`, `stage_0_5_4b_admission_checklist`, `researcher_decision_matrix` | 调用 `stage_0_5_sumo` 的守卫与适配层；不修改 Stage 0.2 | pandas, numpy |
| evaluation | `code/src/riskprop/prelock_metrics.py` | TTC 暴露、PET、解析真值、时间步、阈值与样本量公式 | 无 | `integrated_ttc_exposure`, `rear_end_analytic_truth`, `evaluate_timestep_convergence` | 被 prelock validation 调用 | numpy, pandas |
| experiment | `code/src/riskprop/prelock_validation.py` | 生成阶段 0.6 技术真值审计包 | 无 | `write_stage_0_6_prelock_validation` | 调用 prelock metrics 与路径审计 | pandas |
| evaluation | `code/src/riskprop/protocol_lock.py` | fail-closed readiness 与协议锁写入 | `ProtocolLockError` | `protocol_lock_readiness`, `write_protocol_lock` | 聚合前置 Gate | 标准库 |
| adapter | `code/src/riskprop/upstream_adapter.py` | 只读映射 DRIFT 状态字段到 AAD schema | `UpstreamAdapterError` | `convert_drift_state_rows`, `validate_drift_mechanism_fields` | 依赖 artifact schema | pandas |
| auxiliary | `code/src/riskprop/project_docs.py` | 注册表、索引、AI_CONTEXT、Git 与证据一致性检查 | 无 | `validate_project_docs` | 由验证脚本/CI 调用 | 标准库, Git |

## 入口与测试

运行入口位于 `code/scripts/`，名称与阶段对应；测试位于 `code/tests/`。历史模块、命令和测试分别位于三个 `legacy/`，仅做历史复现。要定位具体问题，先按上表选择源码，再读取同名测试与 `docs/PROJECT_REGISTRY.json` 对应条目。
| measurement | `code/src/riskprop/formal_risk_measurement.py` | Versioned P2 source events, causal confirmation, rho, bounded burden primitives and DID interval arithmetic | None | `extract_formal_source_events`, `rho_from_ttc`, `contribution_bounds`, `integrate_fixed_window`, `did_interval` | pandas, standard library |


## 2026-10-12 正式测量与收口接口

run_stage_0_2_final_closure.py执行全源检查；stage_0_2_closure_analysis.py提供独立采样/对应；finalize_stage_0_2_closure.py核验当前接口与11案例并组装Gate矩阵。 依据：相应源码及 `docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`。

2026-10-18 AAD-0.5.4-A：新增 `stage_0_5_calibration_readiness.py`、`run_stage_0_5_calibration_readiness.py`、`run_stage_0_5_timestep_sensitivity.py`、`test_stage_0_5_measurement_equivalence.py`；`CalibrationValidationGuard` 增加 `require_row_scoped_read`（行级 fail-closed + SHA 校验）。

2026-10-18 AAD-0.5.3：新增 `stage_0_5_sumo.py`、`run_stage_0_5_sumo_baseline.py`、`test_stage_0_5_sumo.py` 和版本化候选配置；Lankershim/pNEUMA 仅注册入口，US-101 `generic_highway_candidate` fixture 可运行。TraCI `getLeader` 距离语义已核验并给出显式换算规则；工程 P2 与 formal-alignment P2 双路一致，正式等价性保持 pending。

2026-10-18：新增独立stage_0_5_calibration_gaps.py，负责raw policy binding、受控来源行连接、车型/时间、断面相邻跨越、局部连续暴露和统一分层。入口run_stage_0_5_calibration_gaps.py、benchmark_stage_0_5_calibration_loads.py、finalize_stage_0_5_calibration_gaps.py；测试test_stage_0_5_calibration_gaps.py。工程RSS测量依赖psutil（dev依赖）。既有已批准测量模块未修改。


## 2026-10-18 B0模块

`stage_0_5_exploratory_response.py`负责有界计划、SHA冻结、守卫摘要输入、TraCI观测、单参数配对、资源/守恒/测量检查与停止；`stage_0_5_exploratory_analysis.py`负责固定时片、全批次表图、原A+初态复用与来源追踪。入口`code/scripts/run_stage_0_5_exploratory_response.py`；测试`code/tests/test_stage_0_5_exploratory_response.py`。16个边界暴露与原compute_exposure等价，停止调度修复有集成回归。未改变既有科学测量模块。

## 2026-10-19 B1模块

`stage_0_5_b1_isolation.py`为摘要/路径/角色/SHA与Python审计；`stage_0_5_boundary_bottleneck.py`为胶囊、固定机制、TraCI、守恒及停止；`stage_0_5_b1_analysis.py`为分域表图、内外队列和便携包。入口run/finalize_stage_0_5_boundary_bottleneck.py，verify_stage_0_5_boundary_evidence.py纯Git核验；两个B1测试文件。依据：`docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md`、`evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1/`中的preflight、execution_stop_observation、numerical_stop_diagnostic、queue_diagnostics、run_manifest和SHA256SUMS。

## B1.1 测量模块与入口

- `code/src/riskprop/stage_0_5_stopping_contract.py`：ballistic分支、终点停车范围、身份/坐标资格、全边最大值与有界异常/哈希分位。
- `code/src/riskprop/stage_0_5_queue_contract.py`：旧网格/候选分车道网格/车辆物理连接，观测与时间/入口资格分离。
- `code/src/riskprop/stage_0_5_contract_fixtures.py`：14个独立合成案例与Candidate配置。
- `code/src/riskprop/stage_0_5_contract_analysis.py`：描述性证据打包，不改变冻结规则。
- `code/scripts/run_stage_0_5_stopping_spillback.py`：prepare/tests/freeze/run/worker/finalize受控入口。
- `code/scripts/verify_stage_0_5_stopping_evidence.py`：纯Git协议/SHA/微型输入及历史/科学边界校验。
- 测试：`test_stage_0_5_stopping_contract.py`、`test_stage_0_5_queue_contract.py`、`test_stage_0_5_b11_evidence.py`。

## B1.1-S 停车可观测性模块与入口

- `code/src/riskprop/stage_0_5_stopping_observability.py`：`step_is_action`（步初对齐）、`reconstruct_signed_vnext`（非决策步任意符号精确、决策步v1>0精确/停车bounded）、`expected_displacement`（官方getDeltaPos）、`prove_clamp_non_injective`；不提供任何位移反推API。
- `code/scripts/run_stage_0_5_stopping_observability.py`：prepare/tests/freeze/run/worker/finalize受控入口，最多3运行。
- `code/scripts/stage_0_5_observability_analysis.py`：描述性证据打包，不改变冻结规则。
- `code/scripts/finalize_stage_0_5_stopping_observability.py`、`code/scripts/verify_stage_0_5_observability_evidence.py`：冻结源绑定与纯Git便携校验。
- 测试：`test_stage_0_5_stopping_observability.py`、`test_stage_0_5_b11s_evidence.py`。


## 2026-10-19 B1.2 分层准入与机制再验证

新增code/src/riskprop/stage_0_5_b12_observation.py（audit_transition/NumericalCoverage/ScopedAccounting/queue_snapshot/QueueTracker）、stage_0_5_b12_network.py（coordinate_support）、stage_0_5_b12_runtime.py（胶囊/冻结/准入/停止）、stage_0_5_b12_worker.py（只读订阅）。入口run/finalize_stage_0_5_boundary_revalidation.py，纯Gitverify_stage_0_5_revalidation_evidence.py，测试test_stage_0_5_b12_integration.py/test_stage_0_5_b12_evidence.py。stopping_observability仅严格布尔/时钟防御，近零适用域未修复且fail-closed。


## 2026-10-19 B1.2-N

新增code/src/riskprop/stage_0_5_near_zero_observability.py（context_from_public/candidate_speeds/audit_transition/Coverage），stage_0_5_b12n_runtime.py（prepare/tests/freeze_micro/micro_checkpoint/分范围停止），stage_0_5_b12n_worker.py（只读.05s运行）；run/finalize_stage_0_5_near_zero_integration.py及verify_stage_0_5_near_zero_evidence.py；测试test_stage_0_5_near_zero_observability.py、test_stage_0_5_b12n_runtime.py、test_stage_0_5_b12n_evidence.py。旧模块广泛适用域叙述保留历史，当前接口使用独立版本。


## 2026-10-19 B1.2-P

code/src/riskprop/stage_0_5_positive_near_zero.py（classify_edge/admission/check_plan）；stage_0_5_positive_runtime.py（源码/准备/冻结/执行/checkpoint）；stage_0_5_positive_worker.py（只读观测）。入口run/finalize/verify_stage_0_5_positive_near_zero.py；测试test_stage_0_5_positive_near_zero.py及test_stage_0_5_positive_evidence.py。无C/D或主矩阵命令。


## 2026-10-19 C/D接入

新增stage_0_5_cd_observation.py（QueueContinuity/entry_evidence/movement/journey_audit/validate_summary）、stage_0_5_cd_runtime.py（胶囊/冻结/执行/分范围停止）、stage_0_5_cd_worker.py（只读）。入口run/finalize/verify_stage_0_5_cd_integration.py；测试test_stage_0_5_cd_observation.py/test_stage_0_5_cd_evidence.py。


## 2026-10-19 LF局部探索

新增stage_0_5_local_following.py（decorate/formal_frame_preserving_flags/analyse）、stage_0_5_lf_transport.py（只读协议/VehicleReader）、stage_0_5_lf_runtime.py（准备/冻结/配对/预算）、stage_0_5_lf_worker.py。run/finalize/verify_stage_0_5_local_following.py、audit_stage_0_5_lf_extension.py；4个LF测试模块。旧正式核心/旧适配器/CD/P/N代码不改。

## 2026-10-20 LF候选协议整合

候选模块code/src/riskprop/stage_0_5_lf_protocol.py；执行design_stage_0_5_lf_protocol.py仅prepare/tests/freeze/inspect/analyse，无SUMO运行命令；package_stage_0_5_lf_protocol.py负责轻量协议与便携语义复核；新protocol和protocol_evidence测试。报告 `docs/STAGE_0_5_LOCAL_FOLLOWING_PROTOCOL_DESIGN.md`；计划 `docs/plans/2026-10-20-lf-protocol-consolidation.md`；证据 `evidence/results/RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1/`。

收口补充：prepare_stage_0_5_lf_protocol_summaries.py封装v1已记录的冻结前A+两摘要补入步骤，3合成准备测试验证；冻结分析未重跑。有限周期精确平衡非统计稳态必要/充分条件，v1辅助标签不能作正式准入，候选协议已澄清。
