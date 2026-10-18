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
