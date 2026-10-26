# AAD Architecture

## 2026-10-26 WSL OS守卫（最新）

新增Linux namespace/Landlock/seccomp/cgroup限容broker，真实无害进程验证；capability binder从原始观测/内核计数重算，预检区分Linux能力和Windows运行时适用性。第八项缺真实单次receipt仍Unknown；NativeBackend未来解除锁后仍拒绝裸宿主。完整控制器接线因1.26运行时/依赖缺失未成立，锁不变。依据：`docs/STAGE_0_5_WSL_ISOLATION_2026-10-26.md`；下方为历史时点。

## 2026-10-26 V3证据验收链

execution_v2调用新增acceptance_v3，八项Pass/Reject/Unknown由实际产物和原测量器推导，移除八项硬编码；admission_v3把工程阻断与授权未决分开。IdentityObserver增加TripInfo对照，NativeBackend增加逐步原生时钟/五车道回读及错误早停、资源采样历史与最终验收绑定；ResearchLedger新增显式task_id参数以保留旧账本默认语义并支持独立V3。原生OS执行器/证明仍缺，构建锁True，软件Replay不是原生证书。

依据：`code/scripts/stage_0_5_acceptance_v3.py`；`code/scripts/stage_0_5_admission_v3.py`；`docs/STAGE_0_5_READY_TO_ADMIT_V3_2026-10-26.md`。

## 2026-10-25 V2准入适配架构（最新）

新增独立脚本层IdentityObserver、InputFidelity、Scope与ExecutionAdapter，复用不改ResearchLedger及C6/D1。NativeBackend含未来连接/施加/资源/采集接口，但构建常量硬锁，不能靠proposal/环境解锁；只ReplayBackend在合成fixture中运行。测量对未证明保真/隔离保守拒绝。Python守卫不是OS/native认证。

依据：`code/scripts/stage_0_5_execution_v2.py`；`docs/STAGE_0_5_V2_ADMISSION_ENGINEERING_2026-10-25.md`。下方旧描述保留历史时点。

## 2026-10-25 V2预算基础设施

新增ResearchLedger，仅工程准入与追加式事件状态机，无累计attempt/wall上限、无launch API；精确提案/研究者确认/输入源码哈希/隔离/资源守卫。旧确认入口→旧监督器→worker调用链及三次限制保留，不接V2。当前未实现新SUMO执行器，不宣称实验隔离或动态初始化已验收。

依据：`docs/STAGE_0_5_RESEARCH_V2_AUDIT_2026-10-25.md`；`docs/STAGE_0_5_RESEARCH_V2_BUDGET.md`；`docs/plans/2026-10-25-stage-0-5-interaction-research-v2.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-RESEARCH-V2/`。以下内容保留其历史时点。


## 2026-10-25 离线输入候选

新增prepare_stage_0_5_depart_speed_candidate.py，仅prepare/verify，无launch入口；复用既有Boundary并拒绝所有子进程。旧执行/测量/监督源字节不改，候选准备不代表执行适配器已获准。

依据：`docs/STAGE_0_5_DEPART_SPEED_CANDIDATE_2026-10-25.md`；`docs/plans/2026-10-25-stage-0-5-depart-speed-candidate-v1.md`；`evidence/results/RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1/`。以下原内容保留。


## 2026-10-25 任务级隔离入口

run_stage_0_5_policy_a_confirmed.py经interaction_task_boundary.py限制文件/写入/单一进程；原批准执行和测量源码保持字节，新增入口绑定隔离工程。Python审计不等于OS/native完整隔离。review_stage_0_5_interaction_failure.py只离线核验失败轨迹。

依据：`docs/STAGE_0_5_INTERACTION_DIAGNOSTICS_POLICY_A_EXECUTION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/`。以下旧状态保留为历史时点。

## 2026-10-25 政策A与最终计划预检

新增政策A离线准备/绑定验证脚本和监督器。准备器不导入TraCI、不启动SUMO；监督器CLI暂停，API需要精确提案SHA的研究者确认，启动前登记尝试并检查输入/源码/工具/依赖/预算/资源，前次未核验则停止。

依据：`docs/plans/2026-10-25-stage-0-5-interaction-diagnostics-policy-a-final.md`；`evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1/`。


## 2026-10-25 C6/C7 offline phase

物理FCD测量路径：parse_fcd同时输出映射y_m和native_position_m/native_lane_id；state_support用后者重建同原生车道物理净间距，前者只用于区域/offset100；D1测量入口由stage_0_5_sumo.compute_local_d1_measurement转入stage_0_5_d1_measurement。

依据：`docs/STAGE_0_5_C6_C7_OFFLINE_DECISION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-C6-C7-OFFLINE-V1/`。


## 模型总体结构

当前不存在已实现的可训练模型架构。正式系统是一个分阶段的确定性科研工程管线：

```text
NGSIM -> 风险测量 -----+
pNEUMA -> 城市运动学 -+-> 仿真—现实覆盖 -> 数值验证/协议准入 -> 阶段 1.1（未实现）
SPMD -> 通信证据边界 -+
SUMO -> 四格与五表 ----+
```

因此当前“模型 forward、训练过程、loss、checkpoint”均为不适用或 `not_determined`，不能按常见深度学习项目补全。

## 主要模块

- 工程实验底座：`stage_0_1_sumo.py`、`formal_runner.py`、`formal_artifacts.py`、`formal_design.py`。
- 数据与测量：`calibration.py`、`real_trajectory.py`、`ngsim_risk_calibration.py`。
- 通信边界：`communication_observability.py`。
- 现实覆盖：`simulation_real_coverage.py`。
- 数值与准入：`prelock_metrics.py`、`prelock_validation.py`、`protocol_lock.py`。
- 项目一致性：`project_docs.py` 与 `code/scripts/export_project_evidence.py`。

## 模块输入输出

- 阶段 0.1 输入 SUMO 配置与固定 seed，输出每格封存目录、五表 Parquet、clock/lifecycle、audit、manifest、provenance 与 SHA256SUMS。
- 阶段 0.2 输入显式列出的 NGSIM calibration 窗口，输出标准化 state Parquet、合并后的 risk events 及封存元数据。
- 阶段 0.3 输入 pNEUMA 原始 CSV，输出解析审计、状态/轨迹统计、速度/加速度分布、敏感性、bootstrap、Stage 0.5 标准化参考与不可覆盖验收包。
- 阶段 0.4 输入 SPMD RV_RX 与访问状态，输出接收连续性 profile 和证据边界 audit。
- 阶段 0.5 输入 NGSIM state/events、pNEUMA 运动学 state 与 SUMO 样本，输出现实参考和 coverage gate。
- 阶段 0.6 输入解析/物理真值与前置 Gate，输出技术 audit、readiness，满足全部条件后才能写协议锁。

## 模块关系

`real_trajectory.py` 为 NGSIM/pNEUMA 读取层；`ngsim_risk_calibration.py` 调用 NGSIM 读取与 `calibration.py` 表契约；`simulation_real_coverage.py` 调用 `calibration.py` 的稳健缩放和 energy distance；`protocol_lock.py` 聚合阶段 0.2/0.4/0.5/0.6 Gate。阶段 0.3 的产物通过阶段 0.5 间接进入准入链。

2026-10-18 AAD-0.5.3 新增 `stage_0_5_sumo.py` 与 `run_stage_0_5_sumo_baseline.py`。该模块独立于 Stage 0.1，提供三场景职责 manifest、`generic_highway_candidate` 参数化走廊（3 主线段 × 3 车道 + 入口/出口匝道）、两个显式工程 fixture（baseline_mixed_demand、measurement_probe_queue_stop）、no-message TraCI runner、internal/recorded 时间步分离、SUMO-native leader/net-gap/closing-speed/TTC 状态、工程 P2/exposure adapter、Stage 0.2 formal-alignment adapter、以及 `CalibrationValidationGuard` fail-closed 访问守卫；不承载消息处理、校准寻优或 Stage I 因果逻辑。Lankershim/pNEUMA 目前仅保留 candidate_entry_only 配置与显式 `unmapped` 车型缺口。

2026-10-18 AAD-0.5.4-A 新增 `stage_0_5_calibration_readiness.py` 与 `run_stage_0_5_calibration_readiness.py`、`run_stage_0_5_timestep_sensitivity.py`。该层不产生任何科学参数，只做三件事：①按 Stage 0.2 正式规范逐项审计 SUMO 测量契约并运行确定性边界矩阵；②在 `CalibrationValidationGuard` 之下只用前两个校准窗口计算运动学/跟驰/暴露/不确定性与需求可识别性；③给出候选协议与机器可读准入清单。测量适配的修复集中在 `stage_0_5_sumo.py`（绝对时钟、前车帧号、退出原因、闭合 epsilon、可靠层定义、DRAC），Stage 0.2 正式模块保持未修改。

## 重要配置

- 当前代码依赖：`code/pyproject.toml`。
- 阶段 0.1 环境证据：`code/environment/`。
- 原始数据与 split 清单生成：`calibration.build_default_calibration_manifests()`。
- 运行时冻结 config 位于各 `code/outputs/formal/**/config_frozen.json`，完整输出不进入 Git。
- `code/configs/feasibility_week_smoke.json` 属于历史 Pilot 配置，不是当前正式阶段配置。

## 关键代码位置

- `code/src/riskprop/stage_0_1_sumo.py::run_real_sumo_stage_0_1()`
- `code/src/riskprop/ngsim_risk_calibration.py::write_stage_0_2_ngsim_package()`
- `code/src/riskprop/real_trajectory.py::read_pneuma_wide()`
- `code/src/riskprop/communication_observability.py::build_stage_0_4_status_package()`
- `code/src/riskprop/simulation_real_coverage.py::evaluate_simulation_coverage()`
- `code/src/riskprop/prelock_validation.py::write_stage_0_6_prelock_validation()`
- `code/src/riskprop/protocol_lock.py::protocol_lock_readiness()` / `write_protocol_lock()`

### Formal Stage 0.2 risk measurement (2026-10-11)

`riskprop.formal_risk_measurement` is a versioned, isolated interface for approved P2 events, causal observed-frame confirmation, `rho=exp(-TTC/tau)`, bounded contribution semantics, fixed-window integration, equal-vehicle aggregation, and DID interval arithmetic. It does not alter historical `ngsim_risk_calibration.extract_rear_end_events` defaults or `prelock_metrics.integrated_ttc_exposure`.


## 2026-10-12 正式测量与收口接口

formal_risk_measurement.v2与历史0.1s提取/线性指标隔离；正式固定窗口原语需完整来源/时钟/双车身份与真实连续边，区域可靠性独立。 依据：相应源码及 `docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`。


## 2026-10-18 B0独立探索层

新增隔离的B0执行/分析模块，不修改既有Stage0.2/0.3/0.4测量模块或封存包。执行层冻结计划/输入/源码、逐worker资源监测、两阶段checkpoint；分析层只生成描述表图与机制证据。旧执行器completed+blocker未停止缺陷已保留，批次关闭后修复；新源码不可恢复旧计划。正式覆盖Gate仍由原协议readiness约束。依据：`code/src/riskprop/stage_0_5_exploratory_response.py`、`code/src/riskprop/stage_0_5_exploratory_analysis.py`、docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md。

## 2026-10-19 B1隔离执行层

独立胶囊复制最小代码闭包与摘要白名单；-S避免环境.pth，Python审计限制文件/进程/网络，native/OS覆盖有限。父监督器以退出码+工程blocker及资源/SHA决定停止，全部后续not_attempted。冻结执行/测量与可修复描述renderer分离；不修改旧B0/正式测量层。依据：`docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md`、`evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1/`中的preflight、execution_stop_observation、numerical_stop_diagnostic、queue_diagnostics、run_manifest和SHA256SUMS。

## B1.1 独立测量层（2026-10-19）

新增stopping_contract分支/全边轻筛，queue_contract观测与资格分层；contract_fixtures提供先验合成真值，contract_analysis只打包描述。run_stage_0_5_stopping_spillback复用B1最小-S胶囊和停止控制，冻结源码/输入后运行至多4个微型fixture。旧B1执行器、正式TTC/P2和封存状态均未修改。精确停车仍Pending，队列候选未获科学批准；见B1.1报告。

## B1.1-S 公开接口停车可观测性层（2026-10-19）

`stage_0_5_stopping_observability.py`只读观测：`step_is_action`按步初对齐（`lastActionTime`在步末读数`==t_prev`才为决策步），`reconstruct_signed_vnext`对非决策步给出`u=v0+a_pub_start*h`（任意符号，含步内停车`u<0`），对决策步`v1>0`给出`u=v1`、对决策步`v1==0`只给范围。`run_stage_0_5_stopping_observability`复用B1胶囊/白名单/冻结，3个微型fixture；`stage_0_5_observability_analysis.py`仅描述打包。未用调试二进制、未改官方SUMO与正式TTC/P2；决策步停车仍Bounded。


## 2026-10-19 B1.2 分层准入与机制再验证

B1.2新增独立b12_observation/network/runtime/worker：全边.05s分层审计、全网身份与局部边界分账、显式internal lane路径坐标、分车道队列观测/资格、-S胶囊与分阶段准入。旧B1/B1.1执行与P2核心不变。首个真实fixture近零终速不一致使主矩阵阻断；新执行入口不是已验证可用的主机制实验。


## 2026-10-19 B1.2-N

独立near_zero_observability模块只负责分支候选/独立上下文充分条件/audit_transition/Coverage；b12n_runtime负责最多3+2运行与micro checkpoint；b12n_worker只读TraCI。旧B1.1-S/B1.2实现不改。实际3微型运行后缺正近零覆盖，未进入C/D。


## 2026-10-19 B1.2-P

新增独立positive_near_zero目标七项链条分类（一般精确与target Exact Pass分开），positive_runtime仅prepare/tests/freeze/run/worker/checkpoint，positive_worker只读原生信号探针。复用旧数值/监督/胶囊，不改B1.2-N或正式TTC/P2。


## 2026-10-19 C/D接入

独立cd_observation.QueueContinuity逐已验证path关联队列/pending/入口几何，.05s处理/1Hz留存，真实path变更和缺帧重置。旧B12/N模块与证据保留。cd_runtime分场景ledger、schema/plan SHA防御；cd_worker只读。


## 2026-10-19 LF局部探索

独立local_following量测接口保留全网leader上下文再标局部归域；formal_frame_preserving_flags防止旧SUMO通用适配器擦除外来break标志，Stage0.2核心不变。lf_transport只读GET批处理，每车每步仍11项；lf_runtime独立冻结/预算/配对门槛，lf_worker沿用数值和计数。

## 2026-10-20 LF候选协议整合

新增独立候选分析模块stage_0_5_lf_protocol与design/package入口。正式Stage0.2/SUMO/LF核心不改；分析从封存全网点态和事件开始，不能先裁局部重提事件。报告 `docs/STAGE_0_5_LOCAL_FOLLOWING_PROTOCOL_DESIGN.md`；计划 `docs/plans/2026-10-20-lf-protocol-consolidation.md`；证据 `evidence/results/RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1/`。
