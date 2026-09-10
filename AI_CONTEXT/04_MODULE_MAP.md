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
| experiment | `code/src/riskprop/ngsim_risk_calibration.py` | 标准化 NGSIM、合并风险事件、封存阶段 0.2 | 无 | `standardize_ngsim_states`, `extract_rear_end_events`, `write_stage_0_2_ngsim_package` | 调用 data 层 | pandas |
| evaluation | `code/src/riskprop/communication_observability.py` | SPMD trip 分割、RV_RX profile 与字段边界 | `CommunicationEvidenceError` | `spmd_trip_split`, `profile_rv_rx_calibration`, `build_stage_0_4_status_package` | 独立审计模块 | 标准库 |
| evaluation | `code/src/riskprop/simulation_real_coverage.py` | 稳定抽样、真实参考与 sim-real 覆盖 Gate | 无 | `deterministic_state_sample`, `write_real_reference_package`, `evaluate_simulation_coverage` | 调用 `calibration` | numpy, pandas |
| evaluation | `code/src/riskprop/prelock_metrics.py` | TTC 暴露、PET、解析真值、时间步、阈值与样本量公式 | 无 | `integrated_ttc_exposure`, `rear_end_analytic_truth`, `evaluate_timestep_convergence` | 被 prelock validation 调用 | numpy, pandas |
| experiment | `code/src/riskprop/prelock_validation.py` | 生成阶段 0.6 技术真值审计包 | 无 | `write_stage_0_6_prelock_validation` | 调用 prelock metrics 与路径审计 | pandas |
| evaluation | `code/src/riskprop/protocol_lock.py` | fail-closed readiness 与协议锁写入 | `ProtocolLockError` | `protocol_lock_readiness`, `write_protocol_lock` | 聚合前置 Gate | 标准库 |
| adapter | `code/src/riskprop/upstream_adapter.py` | 只读映射 DRIFT 状态字段到 AAD schema | `UpstreamAdapterError` | `convert_drift_state_rows`, `validate_drift_mechanism_fields` | 依赖 artifact schema | pandas |
| auxiliary | `code/src/riskprop/project_docs.py` | 注册表、索引、AI_CONTEXT、Git 与证据一致性检查 | 无 | `validate_project_docs` | 由验证脚本/CI 调用 | 标准库, Git |

## 入口与测试

运行入口位于 `code/scripts/`，名称与阶段对应；测试位于 `code/tests/`。历史模块、命令和测试分别位于三个 `legacy/`，仅做历史复现。要定位具体问题，先按上表选择源码，再读取同名测试与 `docs/PROJECT_REGISTRY.json` 对应条目。
