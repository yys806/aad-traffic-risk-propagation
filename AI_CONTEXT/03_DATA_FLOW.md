# AAD Data Flow

## 2026-10-25 政策A失败证据数据流

批准提案→只读输入哈希→独立运行capsule→SUMO在180s失败→保留FCD/getter/summary→D1离线v2/18单元缺失→便携汇总。未观测未来不能补零；完整率不可评价。

依据：`docs/STAGE_0_5_INTERACTION_DIAGNOSTICS_POLICY_A_EXECUTION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/`。以下旧状态保留为历史时点。

## 2026-10-25 政策A与最终计划预检

政策A：两真实canonical源SHA→完整上下文正式D1及独立审计→A绝对窗[240,510)/[300,570)→18个offset100单元；与修复基线对应共同单元核验。配置副本和资源快照→review_ready_plan及提案SHA，非协议锁。

依据：`docs/plans/2026-10-25-stage-0-5-interaction-diagnostics-policy-a-final.md`；`evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1/`。


## 2026-10-25 C6/C7 offline phase

C6离线链：两份授权历史FCD→双坐标解析→同原生车道物理跟驰/无法重建则missing→不变风险核心→完整事件上下文→D1时间空间裁切；新目录保存逐状态TTC及事件成员，便携目录仅聚合与SHA。C7选择仅用FCD身份/位置/时间，不读P2。

依据：`docs/STAGE_0_5_C6_C7_OFFLINE_DECISION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-C6-C7-OFFLINE-V1/`。


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

## B1.1 数据流（2026-10-19）

具名六个历史B1元数据+固定官方SUMO1.26源码→角色/SHA核验→独立胶囊；无NGSIM状态/历史全源/旧C完整状态输入。先解析/合成测试→冻结protocol/测试真值/源码/XML SHA→4个30s上限微型fixture→全边位移统计与有界异常→本地完整状态、Git轻量summary。队列真值独立合成，不在旧C上调阈值；全量回归只在无本地数据的Git克隆，skip不是数据验证通过。

## B1.1-S 数据流（2026-10-19）

具名四个B1.1便携审计元数据+固定官方SUMO1.26源码→角色/SHA核验→新建胶囊；无真实轨迹/旧C状态输入。先解析可观测性测试（决策步判定、重建公式、钳制非单射、负面拒绝）→冻结protocol/源码/XML SHA→3个30s上限微型fixture（自由、0.05停车重启、0.1停车重启）→逐步读`getSpeed/getAcceleration/getLastActionTime`→步初对齐判决策步与`u`重建→按精确/范围/不可评价分类→本地完整状态、Git轻量summary。未使用调试重建；全量回归只在无本地数据Git克隆。


## 2026-10-19 B1.2 分层准入与机制再验证

SHA绑定既有两校准窗口便携摘要及A+车型→独立B1.2胶囊→142合成/停止测试→冻结两个≤60s接入fixture→.05s订阅状态/步初加速度/lastActionTime→分层数值与分域计数/路径坐标/队列快照→19.75s终速不一致自动阻断→D及主矩阵未执行→本地全状态/三图，Git小型协议、反例和统计。停止后官方固定源码请求/哈希独立登记；无新真实轨迹或历史全源读取。


## 2026-10-19 B1.2-N

具名官方源码(11文件SHA)+B1.2具名便携元数据/工程XML bundle→新-S白名单胶囊→203合成→冻结micro→3次30s→checkpoint false→封存。未decode calibration_reference，未读真实轨迹/旧C状态。u_pre→独立后处理上下文→u_final→ballistic→公开钳制；位移仅用于检查，不能反推分支。


## 2026-10-19 B1.2-P

13官方具名源+4项B1.2-N便携元数据→SHA/角色→-S胶囊151合成→5项共同冻结→各2s原生红灯制动→步初v/a独立重建u_pre及上下文证明→公开终速/位移核验→本地全边、Git轻量目标/对照及输入/源码绑定。无真实数据/旧状态读取。


## 2026-10-19 C/D接入

官方13源码与封存工程输入→SHA/角色守卫胶囊→.05s公开状态/步初加速度→N受限数值分层→全网/局部独立计数→路径队列/.05s持续性→本轮D状态离线复核→便携证据。无新增真实轨迹/旧B1 C状态；Python审计非OS绝对隔离。bounded不当Exact，TTC点态不当P2。


## 2026-10-19 LF局部探索

19具名官方源/已安装客户端指纹+封存原尺度C输入→204预检→SHA冻结→120同步/120批处理全字段比较→成本门槛→300局部采集→.1s全网leader/质量→正式核心工程事件/暴露和独立复算→局部归属候选。旧CD C只离线间隙，不重跑/不作比较。原始状态/完整事件本地，Git43轻量文件与封装校验。

## 2026-10-20 LF候选协议整合

LF3点态/事件/交通帧和两个批准校准窗口轻量摘要→SHA/角色白名单→Python -S离线胶囊→逐事件/分母/时间窗审计→五层必要目标与候选协议。无新真实轨迹/第三窗口/holdout；所有新数值只候选，不回写历史。报告 `docs/STAGE_0_5_LOCAL_FOLLOWING_PROTOCOL_DESIGN.md`；计划 `docs/plans/2026-10-20-lf-protocol-consolidation.md`；证据 `evidence/results/RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1/`。

## 2026-10-21 真实交通重建与条件场景数据流

只读重建：两个已批准校准窗口的 canonical 状态 parquet（SHA `684a5f0b96dc4811…` / `7b0ef830c97a981d…`，仅列 21 个字段）→ `stage_0_5_trajectory_reconstruction.load_calibration_states()`（fail-closed 拒绝 `0820_0835`/Lankershim/未批准窗口）→ 车道纵向/横向支撑识别（5 主线 + 匝道 7 + 辅助 6 + 出口 8，规则校验不过即报错）→ 边界跨越（相邻 10 Hz 观测线性插值）→ 守恒（六车道断面闭合区域）→ 50 m × 60 s 与 100 m × 30 s 时空面 → 慢速连通域（阈值 10 m/s）→ 基本图 `(k, q, v)` → 轨迹簇 bootstrap。官方旁证来自数据集内 `us-101-data-analysis.zip` 的两份 PDF（矢量文本缺 ToUnicode，经光栅化 + 本地 OCR + 回读核对，标为 Unverified 直至交叉核对），配置为 `code/configs/stage_0_5_ngsim_official_reference_v1.json`。第三窗口与 holdout 零读取。

条件场景：`stage_0_5_scene_reconstruction` 的观测几何规格 → `netconvert` 建网（`main_0` 5 车道 → `main_1` 6 车道 ← 匝道 → `main_2` 5 车道 + `offramp`）→ 边界需求（观测跨越流量 + 官方匝道流量 + 官方车型比例）→ 初始状态注入（窗口起点真实位置/车道/速度，按边长反缩放，重叠车辆丢弃并计数）→ SUMO 原生 `--fcd-output`（0.1 s 周期）+ `--summary-output` → `parse_fcd()` 用显式反缩放映回真实米制 → 与真实目标同口径的局部指标（`k`/`v`/`q=k·v·3.6`/低速份额/30 s 块）→ 状态支持判定与停止规则。全过程无 TraCI，运行前冻结 `diagnostic_plan.json` + `PLAN_SHA256`；数值分支微审计沿用 2026-10-20 胶囊，不在本批重跑（报告已披露）。

## 2026-10-20 状态定义敏感性与前车重放数据流

主线 A：两个已批准 canonical 状态 parquet → `stage_0_5_jam_definition.cell_speed_grid()`（50 m × 30 s 时空速度格）→ `reference_speeds()`（窗口 p95 / 窗口最大值 / 27.78 工程值）→ `congestion_mask()`（绝对阈值 + Duan `W<0.5` + Saberi `λ<ρ`）→ `describe_mask()`（最大连通域规模/持续/最早位置/方向/反向速度）→ `null_model()`（每时间片内按有效格重排掩码，保留边际、破坏空间排列，1000 次，种子 20261031；缺测格不参与置换且不计为不拥堵）。全部离线，无 SUMO。

主线 B：canonical 状态 → `stage_0_5_leader_replay.prepare_pairs()`（沿用 Stage 0.2 连续性/身份/质量语义切成可靠跟驰段）→ `select_pairs()`（冻结规则：≥8 s、按时长降序、同长按 `trajectory_id`）→ `pair_observations()`（从**后车**行取位置/速度，从前车自身行取前车位置/速度，车长由 `(y_leader − y_follower) − net_gap` 反推取中位数）→ `replay_pair()`（单车道长直边；TraCI 每 0.05 s `moveTo`+`setSpeed` 施加前车并按步长预补偿；后车**不调用** `setSpeed`；记录点用观测时钟标签按索引对齐）→ `pair_metrics()`（Brockfeld Eq. 2、NRMSE(gap)/NRMSE(speed)、偏差/MAE、车头时距、闭合速度；加速度保留为空并附理由）→ `summarise()`（按配置、窗口、口径、车头时距分层，配对 bootstrap 以「对」为重采样单位）。运行前写 `replay_plan.json` + `REPLAY_PLAN_SHA256`。主线 C 由 `phase_c_decision.json` 记录为未执行。

## 2026-10-20 方法扩展数据流

P2 覆盖：canonical 状态 → `leader_replay.prepare_pairs`（沿用 Stage 0.2 连续性/身份/质量语义）→ 逐段阶段时长与标志（探索性阈值）→ `trajectory_coverage_summary.json`（小型便携）+ 本地完整矩阵。样本选择：`stratified_selection`（按 gap/speed 四层轮流取，替换此前「最长优先」）。

P3 初始化：同一批 12 对 × 两条路线（`native` 等待并记录插入延迟后按后车自身时间对齐 / `none` 使用官方 `--insertion-checks none` 在观测时刻精确进入）→ `init_routes.csv`（含每对轨迹 SHA 以支持逐字节一致性对照）→ `init_summary.json`。

P4 响应：9 个单因素配置 × 3 个共同 seed × 12 对 → `replay_pair`（共享 1200 m 单车道网络，TraCI 驱动前车、后车纯模型、记录点用观测时钟标签对齐）→ `pair_metrics` + `slice_record`（局部 5 s / 长期 ≥10 s）+ `response_metrics`（制动事件幅值与滞后）→ `response_metrics.csv`/`response_summary.json`（含 seed 变异、配对差异、seed 稳定性）→ `identifiability_summary.json`（局部灵敏度、参数相关、信号/噪声、tau 剖面）。Newell 原型离线复用同一指标。P5 由 `macro_decision.json` 记录为门控未开。三批运行前各自写 `response_plan.json`/`init_plan.json`/`newell_plan.json` 并绑定 SHA；插入检查与等待策略、配置目录与单因素守卫、共享网络、局部/长期窗与扰动指标定义都在计划中冻结。
