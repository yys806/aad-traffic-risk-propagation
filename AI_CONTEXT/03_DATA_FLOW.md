# AAD Data Flow

## 总览

```text
raw data
-> dataset（本机、Git 忽略）
-> preprocessing / 标准化
-> tabular model input（当前不是 tensor）
-> 确定性测量或 SUMO 运行
-> post-processing / 事件合并或稳定抽样
-> evaluator / Gate
-> metrics + audit + manifest + provenance + SHA256SUMS
-> evidence（Git 内小型只读快照）
```

## NGSIM 数据流

显式校准 ZIP 成员 → `_read_source()`（US-101 无表头 TXT、Lankershim CSV）→ `annotate_ngsim_trajectory_identity()` → `standardize_ngsim_states()` 内调用 `add_ngsim_leader_ttc()` → `extract_rear_end_events()` → 完整 state 与原始/可靠/拒绝 candidate Parquet、audit、配置、provenance 和校验包。

净间距由报告的前向间距减去匹配 leader 车长；仅在 leader 可匹配、净间距为正且 follower 正在闭合时计算 `TTC=g/Δv` 与 `DRAC=(Δv)^2/(2g)`。诊断身份采用 site/source_member/source_period/原始编号/观测帧时钟锚；unknown 来源时段不推断为官方标签。记录冲突传播到整个诊断序列，保留原行号；单帧 TTC 数学有效与 identity/leader 可靠性分别标记。事件在完整状态序列上检查前车变化、片段与 100 ms/帧连续性，缺口后第一帧可以开始新事件；不确定前后车不能进入可靠事件。默认 `extract_rear_end_events()` 返回可靠工程候选，`return_diagnostics=True` 返回原始/可靠/拒绝三表；未冻结科学阈值。

## pNEUMA 数据流

`dataset/pNEUMA/20181101_d1_0800_0830.csv` → `pneuma_urban_kinematics.audit_pneuma_source()` 流式审计与解析（或历史接口 `real_trajectory.read_pneuma_wide()`）→ 逐状态表（速度、纵/横向加速度、时间、车型、元数据）→ `flag_state_quality()` 时间质量标记 → 时间加权/车辆等权统计、敏感性与 bootstrap → `build_stage_0_5_reference_states()` 标准化参考 → Stage 0.5 `write_real_reference_package()`。不推断道路、leader、TTC 或 DRAC。2026-10-12 专用阶段 0.3 汇总入口与验收包已实现。

## SPMD 数据流

`dataset/SPMD/selected/RV_RX.csv.zip` → `communication_observability.profile_rv_rx_calibration()`，按完整 `DeviceID|Trip` 的 SHA-256 首字节划分 calibration/locked holdout → 接收状态连续性 profile → `build_stage_0_4_status_package()`。观察间断不等于丢包，RV_RX 行不等于消息，且当前无已验证 adoption 字段。

## SUMO 数据流

`stage_0_1_sumo.run_real_sumo_stage_0_1()` 生成物理隔离的双走廊网络，对四个 `s/c` cell 分别启动 SUMO；TraCI 状态进入 state/emission 表，消息生命周期进入 protocol 表，控制进入 action 表，风险窗口进入 risk 表。随后 `formal_design` 检查四格、处理前等价、隔离、时钟、生命周期与路径；`formal_artifacts` 封存并校验文件。

## 覆盖与准入数据流

NGSIM 跟驰参考 + pNEUMA 运动学参考 → `write_real_reference_package()` 稳定哈希抽样 → SUMO calibration 样本 → `evaluate_simulation_coverage()` 比较 real-real 与 sim-real energy distance 及类别覆盖 → 阶段 0.6 技术真值 → `protocol_lock_readiness()` → 条件完整时 `write_protocol_lock()`。

## 重要数据结构

- `REAL_STATE_COLUMNS`：dataset/site/window/vehicle/time/位置/速度/加速度/road/lane/leader/net gap/closing speed/measurement status/missing reason。
- `RISK_EVENT_COLUMNS`：事件身份、车辆与 leader、时间边界、持续时间、TTC/DRAC/PET、纳入状态与算法版本。
- 阶段 0.1 五表字段契约：`formal_artifacts.TABLE_REQUIRED_COLUMNS`。
- 当前数据均为行式 DataFrame/Parquet；不存在已确认 tensor shape、dataloader 或 neural model input。

## 2026-10-10 前车匹配收尾

NGSIM leader lookup 在存在诊断字段时使用 run scope、Global_Time、diagnostic_clock_anchor_ms、Frame_ID 和唯一原始前车身份；重复或缺失字段不猜测。任务 1.5 独立核查真实 Lankershim 0 跨时钟匹配，四源回归 0 行核心差异。


## 2026-10-12 Stage 0.3 参考接口

stage_0_3 R2 验收包中的 stage_0_5_reference_states.parquet（含 dataset/site/window_id/vehicle_id/vehicle_type/time_s/speed_mps/acceleration_mps2/quality_status/time_weighting_eligible/source_file_sha256）是 canonical 参考，但当前 write_real_reference_package() 仍读取旧字段 id/longitudinal_accel_mps2；需经显式 adapter 或经批准的原生契约后接入。NGSIM 与 pNEUMA 不拼接为 iid 样本。

## 2026-10-16 R2 质量语义（当前）

R2 起 `quality_status` 逐状态推导（parse_failed/identity_ambiguous/raw_time_anomaly/duplicate_time/raw_parsed），`time_weighting_eligible` 由解析质量、轨迹身份、原始顺序连续性与可靠区间共同决定；`write_real_reference_package()` 读取 pNEUMA 质量字段并将非 raw_parsed 状态 fail-closed 排除出运动学抽样池（计数入 audit），`time_weighting_eligible` 随 kinematics_reference 传递；稳定哈希抽样规则未变。时间加权区间由原始记录顺序邻接定义，排序不定义区间。

## 2026-10-12 正式测量与收口接口

task1.5四源状态→独立全序列/P2在线提取→r4→不可覆盖final_r1验收包；病例与抽稀产物保留成员和断点，便携证据只含小型摘要。 依据：相应源码及 `docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`。

## 2026-10-18 Stage 0.5 场景审计

Stage 0.5 场景设计审计报告为 docs/STAGE_0_5_TASK_0_5_0_SCENARIO_DESIGN_AUDIT.md。Stage 0.3 R2 标准化 pNEUMA 文件实际字段为 vehicle_id/acceleration_mps2/vehicle_type/quality_status/time_weighting_eligible；simulation_real_coverage.write_real_reference_package 当前直接读取 id/longitudinal_accel_mps2，并由 run_stage_0_3_pneuma_kinematics.py 另建旧字段 raw_view 后通过测试。故 canonical Parquet 尚不能直接进入 writer，状态为 Awaiting Researcher Decision；pNEUMA 车型字段也不会进入当前 writer 输出。NGSIM 与 pNEUMA 仍按不同职责和场景分离，旧 Stage 0.5 map-match 包不回接。

2026-10-18 AAD-0.5.1 已修复并验证该接口：`write_real_reference_package(..., pneuma_schema="canonical")` 原生消费 `stage_0_5_reference_states.parquet`，保留原始车型、质量资格和来源 SHA；legacy 仅显式模式。正式 R2 包通过六项输入的 SHA/schema/来源契约，完整 P2 事件仍来自 Stage 0.2 正式表，pNEUMA 时间权重引用 Stage 0.3 封存摘要；稳定哈希/轨迹簇样本仅诊断，不计算正式 P2 率。旧段落描述的是 0.5.0 历史状态，当前事实以 `RES-STAGE-0.5-REAL-REF-R2` 和重建报告为准。

2026-10-18 AAD-0.5.2：覆盖函数事实保持不变——`evaluate_simulation_coverage()` 对 real groups pooled 拟合 median/IQR scaler，计算两两 Energy Distance 分位数上界，并以类别集合交集计算 stratum coverage。R2 的窗口身份重叠、Lankershim 来源限制和 pNEUMA 单文件使 real-real 科学上界当前 `Not Identifiable`；新报告建议按场景、车辆/轨迹簇和可解释单项风险指标约束其用途。未替换函数、未冻结阈值或校准/验证划分。

2026-10-18 AAD-0.5.4-A：新增校准准入数据流。校准窗口状态表经 `guard.require_source_read(role="calibration")` 校验角色与 SHA-256；正式 P2 事件表经 `guard.require_row_scoped_read(column="source")` 以行谓词读取，只物化 `us101__0750_0805` 与 `us101__0805_0820`（本轮 543+732 行），验证窗口行数为 0。随后计算：边缘暴露审计（复现已批准分母）→ 运动学/跟驰/质量构成 → 轨迹簇 bootstrap → 需求可识别性（内部断面通过率与局部密度可测，上游需求/匝道/OD/车型/长度不可识别）→ 候选分层（60 s 片三分位）→ 候选协议与准入清单。SUMO 侧另有独立的 `timestep_sensitivity.json`（内部 0.1/0.05/0.025 s × recorded 0.1 s）。

2026-10-18 AAD-0.5.3：新增 SUMO 无消息数据流：候选场景配置 → `generic_highway_candidate` net/route fixture → TraCI state/lifecycle（run-scoped incarnation 身份） → SUMO-native leader、`net_gap_m = leader_traci_distance_m + follower_min_gap_m`、`closing_speed_mps = follower − leader`、TTC/status/missing_reason → engineering P2/exposure adapter 与 Stage 0.2 formal-alignment adapter → `state_canonical_projection.parquet`（对准 Stage 0.3 canonical real-state 契约） → audit/provenance/runtime diagnostics/manifest/SHA256SUMS。输出字段不伪造 NGSIM source/member/diagnostic clock（`drac_mps2` 保持 NaN）；P2 适配明确 `pending_sumo_adapter_review`/`pending_measurement_equivalence_review`，不进入正式 Stage 0.2 事件率。运行标志固定 `no_message_baseline` 且通信、source treatment、adoption 全关闭；校准入口对 `us101__0820_0835` 与辅助来源 fail-closed 拒绝并记录 `access_audit.json`。

2026-10-18 AAD-0.5.4-A+：已登记archive SHA→两个成员allowlist/校准角色→成员SHA→CalibrationValidationGuard→18列解析→source_member+original_row_number连接→ID/绝对时间/帧/纵向坐标核查→车型/时钟独立摘要，不修改R2。完整批准状态→200m主线每车道逐帧密度（局部空帧0，整源缺帧不补0）→60s覆盖与候选边界资格→合并等片权三分位；完整源连续性先于局部跟驰边筛选，不重归属P2事件。小型摘要→四个预声明工程负载→订阅TraCI+原统一逐行测量+Parquet，不运行正式校准。


## 2026-10-18 B0数据流

A/A+便携摘要→CalibrationValidationGuard来源/角色/SHA→只含两个校准窗口的real_reference_summary；不读取真实轨迹。A+三个既有工程state另按其封存SHA核对，仅用于初态组成诊断。冻结plan/网络/需求/vType/配置→SUMO1.26.0无消息worker→本地完整state/交通帧/发车记录→完整P2适配器+等价暴露→局部200m与全域分账→轻量数值证据。入口待插入与已进入低速车辆分开；局部/分层P2率Unresolved。依据：docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md及source_access_audit、frozen_input_manifest、boundary_response_diagnostics。

B0受控实验数据流与验证执行须分开：根全量pytest会启用历史全源本地事件/案例读取，本轮因此发生B0-VALIDATION-SCOPE-02；全任务验证读取Unknown，不能继承实验层0行声明。后续只在纯Git克隆做全量回归，本任务隔离验收未Accepted。

## 2026-10-19 B1数据流

A+三个封存摘要→预声明来源/SHA→CalibrationValidationGuard→两窗口投影及车型候选→-S胶囊→冻结A/B/C/D输入→无消息SUMO→本地全状态/交通帧/完整TTC/P2→内外队列分账/200m三车道局部量→轻量摘要与工程XML压缩bundle。额外描述分层摘要另有分析用途守卫。无第三窗口/holdout/历史全源产物复制或读取；OS绝对零访问不能认证。B1（RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1）按阻断提前结束：V1失败A后7次未启动，V2 A有效/B警告/C阻断/D未启动，累计4次尝试；无补跑或新seed。A/B局部均速27.1088/26.5152m/s、密度16.3208/16.8197、低速0；C记录2.4007m/s、93.8653veh/km/lane、低速80.1719%、末期未服务252，但停车位移检查与冻结回溢资格阻断，不能作为有效校准样本。D只有静态/空加载检查，动态未知。 依据：`docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md`、`evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1/`中的preflight、execution_stop_observation、numerical_stop_diagnostic、queue_diagnostics、run_manifest和SHA256SUMS。
