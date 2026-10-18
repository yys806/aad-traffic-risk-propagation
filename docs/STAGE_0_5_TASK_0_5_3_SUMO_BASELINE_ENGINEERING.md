# AAD-0.5.3｜SUMO 无消息交通基线构建与测量接口验证

## 1. 状态与边界

本任务建立了独立于 Stage 0.1 的 Stage 0.5 SUMO 工程骨架，并在本地 SUMO 1.26.0 上完成了两个**工程级**无消息 fixture。结果 ID 为 `RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1`，资格仅为 `engineering_only`。

本任务没有访问 locked holdout，没有读取时间验证窗口，没有开展驾驶行为校准，没有使用第三验证窗口进行任何设计迭代，没有修改 Stage 0.2 正式风险定义，没有把工程 fixture 当作 US-101 几何或现实覆盖结论，也没有启动 Stage I/II。

当前状态：

| 项目 | 状态 |
|---|---|
| `stage_0_5.gate` | `pending_simulation_sample` |
| `scientific_claim_eligible` | `false` |
| Stage 0.4 | `pass_limited`（不变） |
| Protocol Lock | 未创建（`protocol_lock_allowed=false`） |
| Stage I / II | 未解锁（`stage_1_1_allowed=false`） |
| 正式 P2 等价性 | `pending_measurement_equivalence_review` |
| 现实覆盖 | 未开始（需 0.5.4 校准与 0.5.5 独立验证） |

工程测试通过只证明工程骨架具备相应能力，不构成 Stage 0.5 科学验收。

## 2. 研究者批准决定的工程落实

AAD-0.5.2 的六项科学原则已写入 `AI_CONTEXT/06_DECISIONS.md` 与可审计配置 `code/configs/stage_0_5_sumo_engineering_v1.json`，并落实为机器约束：

- US-101 前两窗口为 calibration、第三窗口为 temporal validation；`CalibrationValidationGuard` 在**校准角色**请求 `us101__0820_0835` 时 fail-closed 拒绝，并记录到 `access_audit.json`；同时明确该内部隔离**不是**项目原有 locked holdout。
- 明确记录第三窗口摘要此前已公开、只支持同道路有限时间外推、不宣称跨道路泛化、跨窗口车辆 ID 字符串重叠不等于物理身份。
- pNEUMA 的 `forbidden_scope = [ttc, drac, leader, p2, risk_events]` 作为场景 manifest 的机器字段保留。
- 五层必要条件、Energy Distance 辅助角色、P2 数量/暴露/事件率关系、容差制定方法均作为原则记录，**未**转写为任何具体数值。
- 参数三分类 `engineering_fixture_only / researcher_approved_scientific / pending_scientific` 由 `validate_parameter_classification()` 强制；代码一旦出现 `researcher_approved_scientific` 会直接报错，防止工程默认值被自动写成科学冻结。

## 3. 场景架构（任务 A）

### 3.1 三场景职责分离

`SCENARIO_MANIFEST` 为三个逻辑场景分别记录职责、真实参考来源与版本、路网/需求/车型/时间配置版本、评价适用域（含 pNEUMA 禁止域）与工程/科学状态：

| 场景 ID | 职责 | 真实参考 | 本次状态 |
|---|---|---|---|
| `us101_highway_baseline` | 高速公路跟驰风险主线 | `RES-STAGE-0.5-REAL-REF-R2`（US-101 三窗口） | `engineering_fixture_runnable` |
| `lankershim_urban_auxiliary` | 独立城市道路跟驰风险辅助 | R2（`lankershim__complete`） | `candidate_entry_only`，未建路网 |
| `pneuma_urban_kinematics` | 城市混合交通运动学 | R2（`pneuma__athens_d1`） | `candidate_entry_only`，未建路网 |

Lankershim 与 pNEUMA 提供带 schema 的候选配置入口（`CANDIDATE_SCENARIO_CONFIGS`）：`build_status=not_built`、`network.spec=None`、显式 `blocking_decisions` 与 `pending_scientific` 状态，并由 `validate_scenario_candidate_config()` 强制。三类现实参考没有被合并为一个统一场景。

### 3.2 US-101 候选路网（`generic_highway_candidate`）

`NETWORK_DESIGN_CANDIDATE` 是一个参数化的候选高速公路走廊，明确标记 `classification = generic_highway_candidate`、`claim = not_us101_geometry`。拓扑：

- 主线 3 段：`main_0`、`main_1`、`main_2`，节点位于 x = 0 / 400 / 700 / 1200 m，每段 3 车道、限速 27.78 m/s。
- 入口匝道 `onramp`（hwy_on → hwy_j1，1 车道，13.89 m/s）。
- 出口匝道 `offramp`（hwy_j2 → hwy_off，1 车道，13.89 m/s）。
- 三条路线：`mainline = main_0 main_1 main_2`、`entering = onramp main_1 main_2`、`exiting = main_0 main_1 offramp`，覆盖「进入—行驶—驶出」。
- 无信号、无交叉口（自由流主线跟驰风险范围）。

netconvert 会对网络做偏移/归一化，因此**设计意图节点坐标**与**建成车道几何**不同；建成几何由 TraCI 审计并写入 `runtime_diagnostics.network_facts`：

| edge | 车道数 | 建成车道长度 (m) | 限速 (m/s) |
|---|---:|---:|---:|
| `main_0` | 3 | 386.50 | 27.78 |
| `main_1` | 3 | 312.94 | 27.78 |
| `main_2` | 3 | 483.50 | 27.78 |
| `onramp` | 1 | 239.26 | 13.89 |
| `offramp` | 1 | 277.51 | 13.89 |

`network_design_candidate.json` 的 `approval_table` 逐项列出车道数、限速、总长、匝道存在性和信号控制，全部为 `pending_scientific`，并附设计依据供研究者批准或推翻。没有依据验证窗口结果修改路网；Stage 0.1 的物理断开双走廊与三车辆示例没有被改名复用。

## 4. 无消息运行入口（任务 B）

运行配置强制：

```text
experiment_mode                = no_message_baseline
communication_enabled          = false
source_risk_treatment_enabled  = false
information_adoption_enabled   = false
```

`validate_no_message_config()` 在任一标志为真时直接拒绝运行。运行器不创建消息、不接收、不采用、不执行通信控制器动作、不施加 Stage I source-risk treatment、不注入任何预设目标响应；普通跟驰/加减速/换道行为保留。

两个**工程 fixture**（均标记 `engineering_only`、`scientific_claim_eligible=false`）：

| fixture | 目的 | 刺激 | 运行 |
|---|---|---|---|
| `baseline_mixed_demand` | 无消息基线状态/leader/gap/闭合速度/TTC 链 | 无（`stimulus=none`） | 17 vehicles、90 s |
| `measurement_probe_queue_stop` | 触发并检验 TTC/P2 适配 | SUMO `<stop>` 声明的多车道停驻队列尾（非脚本干预、非远端风险刺激） | 7 vehicles、40 s |

运行控制项：可复现 seed（`--seed`，默认 20260907）、场景/fixture 配置、车辆生成配置、暖机窗口（`warmup_s`，本次 0）、评价窗口、internal step、recorded step、车辆生命周期与运行失败记录。

`no_message_baseline` 明确记录为**不等同于** Stage I 正式反事实四格中的 (0,0)。

## 5. 统一状态输出契约（任务 C）

`state.parquet` 字段（单位见 `config.json` 的 `units`）：

- **身份**：`run_id`、`scenario_id`、`fixture_id`、`experiment_mode`、`configured_seed`、`vehicle_id`、`trajectory_id`、`incarnation_id`、`edge_id`、`lane_id`、`simulation_step`、`observation_index`、`time_s`。
- **运动**：`speed_mps`、`acceleration_mps2`、`x_m`、`y_m`、`longitudinal_position_m`、`vehicle_type`、`original_vehicle_type`、`vtype_mapping_version`、`vtype_mapping_status`。
- **跟驰**：`leader_id`、`leader_incarnation_id`、`leader_identity_status`、`leader_speed_mps`、`leader_reference_position_m`、`leader_length_m`、`follower_min_gap_m`、`leader_traci_distance_m`、`net_gap_m`、`net_gap_crosscheck_residual_m`、`net_gap_xy_m`、`net_gap_xy_residual_m`、`closing_speed_mps`、`following_status`。
- **风险质量**：`ttc_s`、`ttc_valid`、`measurement_status`、`missing_reason`、`reliable_following_eligible`、`p2_evaluable_eligible`、`leader_observed`。

### 5.1 已核验的净间距语义订正（重要工程发现）

TraCI `vehicle.getLeader()` 返回的距离**不是**物理保险杠净间距，而是「物理净间距 − 后车 minGap」。本次以两种独立方式实测核验：

1. 三组 vType 组合（car↔heavy、car↔car、heavy↔car）：残差恒等于**后车** minGap（2.0 / 2.0 / 3.0 m），与限速、间距、前车 minGap 无关。
2. 停驻平衡态探针：后车稳定停在前车之后时，纯几何保险杠间距 = 2.501 m（= minGap），而 TraCI 返回值 = 0.001 m ≈ 0。

因此统一换算规则为：

```text
net_gap_m = leader_traci_distance_m + follower_min_gap_m
```

并同时记录可独立复核的几何量。工程运行中的交叉核对结果：

| 运行 | 同车道配对 | 车道位置残差 max | XY 几何残差 max |
|---|---:|---:|---:|
| baseline | 5,235 | 0.0 m | 0.0024 m |
| probe | 1,520 | 0.0 m | 0.0 m |

若沿用未经换算的 TraCI 返回值，净间距会被系统性低估 2–3 m、TTC 被系统性高估/低估风险，属于必须订正的实现缺陷。该订正记录于 `AI_CONTEXT/08_CHANGELOG.md` 与 `07_KNOWN_ISSUES.md`。

### 5.2 符号统一

```text
closing_speed_mps = follower_speed_mps - leader_speed_mps
```

正值＝后车接近前车，零＝纵向相对速度为零，负值＝前车远离。Stage 0.1 使用 `relative_speed_mps = leader_speed - follower_speed`（符号相反）；Stage 0.5 显式记录 `CLOSING_SPEED_SEMANTICS["stage_0_1_conflict"]`，禁止复用 Stage 0.1 validation risk 的 TTC 解释。

### 5.3 测量状态与缺失原因（修正 A）

`measurement_status ∈ {valid, not_applicable, missing, invalid}`，`missing_reason` 逐行保留：

| 状态 | 触发条件 | `missing_reason` |
|---|---|---|
| `valid` | 前车已观测、身份已解析、净间距 > 0、闭合速度 > 0 | `""` |
| `not_applicable` | 无观测前车 | `no_observed_leader` |
| `not_applicable` | 可靠跟驰但非闭合 | `non_closing` |
| `missing` | 前车身份未解析 | `leader_identity_unresolved` |
| `missing` | 仿真输出缺失（速度/间距非有限） | `simulator_output_missing` |
| `invalid` | 净间距非正 | `non_positive_net_gap` |

`measurement_status_summary.json` 分开报告三类性质完全不同的情况：

- 交通状态导致的不可评价：baseline 7,729 行、probe 1,991 行；
- SUMO 输出自身的工程缺失/错误：两个 fixture 均为 **0** 行；
- 真实数据采集缺陷类原因（`diagnostic_clock_conflict`、`camera_occlusion_or_dropout`、`original_frame_identity_break`、`original_row_ambiguity`）：显式登记为 `not_applicable_to_simulator_observation`，**不伪造**。

无前车、非闭合、缺失与无效状态一律**不**写成有限 TTC，也**不**写成零风险；缺失不补零、不插值。

### 5.4 车辆身份作用域

`incarnation_id = "{run_id}|{vehicle_id}|{incarnation_index}"`，由 `VehicleIdentityTracker` 维护。车辆离开后重新进入会得到新的 incarnation，生命周期表记录 `enter / exit / active_at_observation_end`，不会产生不可审计的身份混淆（单元测试覆盖 re-entry）。

### 5.5 Stage 0.3 canonical 接口

`to_canonical_real_state()` 把 SUMO 状态投影为 `dataset=sumo`、`site=scenario_id`、`window_id=run_id`、`road_id=edge_id` 的 canonical real-state 表，并通过现有 `validate_real_state_table()`（缺失必须带原因、缺失不得写 0）。该投影是 0.5.4 的输入候选接口，**尚未**被接受为正式校准输入。

## 6. TTC / P2 测量适配层（任务 D）

### 6.1 TTC

```text
ttc_s = net_gap_m / closing_speed_mps   仅当 net_gap_m > 0 且 closing_speed_mps > 0
```

- 单位：m / (m/s) = s（`units` 与 `ttc_s` 均为 s）；
- 零/负闭合速度：`ttc_valid=false`、`ttc_s=NaN`、`measurement_status=not_applicable`、`missing_reason=non_closing`；
- 非正净间距：`invalid` / `non_positive_net_gap`，不当作正常风险；
- 前车切换、incarnation 变化、记录节奏断裂：不跨边界拼接；
- 不可评价一律保留状态与原因。

### 6.2 两个 P2 适配器

**(1) SUMO-native 工程适配器** `build_sumo_p2_events()`：复用 Stage 0.2 的 P2 定义（`TTC < 2.0 s`、最小连续观测首末跨度 0.2 s、实际观测确认时刻、前车/incarnation/时间连续性）与 `stage_0_2.formal_risk_measurement.v2` 算法版本；记录 `measurement_equivalence_status = pending_sumo_adapter_review`、`inclusion_status = engineering_only`。

**(2) Stage 0.2 formal-alignment 适配器** `extract_sumo_formal_p2_events()`：把 SUMO 状态映射到 Stage 0.2 正式字段契约后直接调用**未修改**的 `extract_formal_source_events()` / `observed_confirmation_time()` / `continuity_is_valid()`。逐项字段对应记录在 `sumo_formal_field_map.json`：

| 正式字段 | SUMO 来源 | 状态 |
|---|---|---|
| `dataset/site/window_id` | `sumo` / `scenario_id` / `run_id` | 适配器提供 |
| `source_member` / `source_period` | `incarnation_id` / `experiment_mode` | 适配器提供 |
| `trajectory_id` / `leader_trajectory_id` | `incarnation_id` / `leader_incarnation_id` | 适配器提供 |
| `original_row_number` / `frame_id` | 观测计数 `observation_index` | `adapter_defined_simulator_frame_index`（明确不是 NGSIM 行号/Frame_ID） |
| `global_time_ms` | `round(time_s × 1000)` | 适配器提供 |
| `diagnostic_clock_anchor_ms` | 常量 0 | `definitional_constant`：单进程单调仿真时钟，NGSIM 时钟冲突类原因在此 `not_applicable_to_simulator_observation` |
| `identity_uncertain` / `identity_break` / `observation_gap` | 常量 False / incarnation 变化 / 记录节奏断裂 | 适配器提供 |
| `leader_matched` / `leader_identity_uncertain` | 前车已观测且 incarnation 已解析 | 适配器提供 |
| `drac_mps2` | 未实现 | `not_implemented_adapter_carries_nan`（保持 NaN，不伪造） |

该适配器**不**虚构 NGSIM 行号、官方 `Frame_ID`、诊断时钟锚点或原始车辆身份；因为 SUMO 不是 NGSIM，其等价性仍显式标记 `pending_measurement_equivalence_review`，`formal_comparability=false`。

### 6.3 P2 可评价暴露

`compute_exposure()` 分别统计三个分母：

- `reliable_following_exposure_s`：连续两端均 `reliable_following_eligible`；
- `reliable_closing_exposure_s`：连续两端均 `ttc_valid`；
- `p2_evaluable_following_exposure_s`：连续两端均 `p2_evaluable_eligible` 且质量状态属 `{valid, not_applicable}`。

可靠且净间距为正的**非闭合**跟驰状态保留在 P2 可评价暴露中（baseline 中 609.4 s vs 可靠闭合 71.7 s），事件率分母不是「只有有效闭合 TTC 的观测」。事件率公式固定为：

```text
p2_event_rate_per_vehicle_hour = p2_event_count / p2_evaluable_following_vehicle_hours
```

并标记 `formal_rate_eligible=false`、`status=pending_measurement_equivalence`；工程事件率（本次 baseline 0.0 / probe 23.75 per vehicle-hour）只用于说明接口可用，不代表真实风险率，也不得作为正式事件率。

### 6.4 时间分辨率

`internal_step_s` 与 `recorded_observation_step_s` 分离，`observation_decimation_factor` 显式记录（要求 recorded 为 internal 的整数倍，否则拒绝运行）。本次两个正式工程包均为 internal 0.1 s / recorded 0.1 s，`observation_cadence_check.max_abs_error_s = 5.7e-15`。

`validate_observation_cadence()` 对记录节奏 fail-closed：把 0.2 s 序列声明为 0.1 s 会直接报错。0.2 s 记录会把链路容差按比例缩放到 0.22 s，且 formal-alignment 适配器默认**拒绝**非 0.1 s 节奏（须显式 `allow_nonstandard_cadence=True`，此时等价性标记为 `pending_measurement_equivalence_nonstandard_cadence` 且不产生正式可比事件）。不做插值、补帧或时间重标记。

## 7. 车型与需求配置机制（任务 E）

`vehicle_type_mapping_candidate()`：

- 工程 vType（`engineering_car`、`engineering_heavy_fixture`、`engineering_queue_fixture`）全部标记 `engineering_fixture_only`；
- pNEUMA 六类原始车型（Car、Taxi、Motorcycle、Bus、Medium Vehicle、Heavy Vehicle）全部 `unmapped`、`sumo_vtype=None`，并进入 `mapping_gaps` 报告映射缺口；
- `scientific_mapping_approved=false`；`validate_vehicle_type_mapping()` 拒绝任何「已批准」或静默映射。

需求配置（`demand_config.json`）提供结构化入口（mode、vehicle_count、depart_interval、lane composition、车型比例、seeds、状态与来源），并由 `validate_demand_config()` 强制：拒绝 `researcher_approved_scientific`、拒绝从时间验证窗口或辅助窗口反推、车型比例必须归一。本次需求为显式工程 departure，`depart_interval_s=3.0`、`derived_from=[]`、`flow_density_calibration_status=pending_scientific`。

参数三分类由 `parameter_status` 逐项记录，本次全部为 `engineering_fixture_only` 或 `pending_scientific`。

## 8. 校准/验证隔离的机器约束（任务 F）

`CalibrationValidationGuard`（fail-closed + 可审计）：

- `calibration` 角色请求 `us101__0820_0835` → 拒绝（`restricted_source_for_role`）；
- `calibration` 角色请求 `lankershim__complete` / `pneuma__athens_d1` → 拒绝；
- `temporal_validation` 角色请求 calibration 来源 → 拒绝；
- 未知角色（含 `locked_holdout`）→ 拒绝（`unknown_access_role`）；
- `require_source_read()` 在读取前同时校验角色权限与绑定 SHA-256，任一不符即拒绝且**不读取**文件。

工程运行自检产生 `access_audit.json`：4 次请求、3 次拒绝、`fail_closed=true`、`locked_holdout_accessed=false`、`validation_window_read=false`。策略同时声明 `internal_window_isolation_is_not_project_locked_holdout=true`、`validation_window_previously_published=true`、`validation_is_same_site_time_extrapolation_only=true`、`cross_road_generalization_claimed=false`、`leave_one_window_analysis_role=preregistered_sensitivity_diagnostic_only`。本次没有读取任何真实参考窗口数据，也没有开展正式验证。

## 9. 有限工程 smoke test（任务 G）

### 9.1 测试范围与结果

`code/tests/test_stage_0_5_sumo.py`：**34 项**（28 项确定性解析/契约测试 + 6 项 SUMO 集成测试），全部通过；本地无 SUMO 时 6 项集成测试标记 skipped，不伪造通过。

确定性解析测试覆盖任务要求的六条断言：

1. 后车速度快于前车且净间距为正 → `closing_speed_mps > 0`、`ttc = gap/closing`、`measurement_status=valid`。
2. 前车更快或等速 → 不产生有限闭合 TTC（`ttc_valid=false`、`missing_reason=non_closing`），同时仍是 P2 可评价暴露。
3. 无前车 → 不视为可靠零风险（`not_applicable` + `no_observed_leader`，既非 0 风险也非有限 TTC）。
4. 前车切换、记录节奏断裂、incarnation 变化 → 不跨边界拼接 P2；两段各自成立时才各自成事件（`[0.0, 0.5]` 而非跨接的 0.6 s 事件）。
5. 满足正式持续时间定义的连续风险只有在实际观测确认时刻之后才被确认（onset 0.0 → confirm 0.2；仅 2 帧跨度 0.1 s 时无事件）。
6. 有效非闭合跟驰暴露不被丢弃（稳健分母 ≥ 可靠闭合分母）。

其他新增覆盖：净间距换算与交叉核对、canonical 投影契约、情景/候选 schema、车型缺口、参数分类拒绝越权、需求反推拒绝、校准隔离与读取 SHA 拒绝、incarnation re-entry、internal/recorded 步分离与非法步长拒绝、暖机窗口、未建场景拒绝、同 seed 可重复性、SHA256SUMS 校验、以及「Gate 不因工程 smoke 改变」。

### 9.2 两个工程运行的客观结果

**baseline_mixed_demand（90 s，seed 20260907）**

| 指标 | 值 |
|---|---:|
| state rows | 8,453 |
| vehicles / incarnations | 17 / 17 |
| 进入并驶出（`arrived_vehicles`） | 17 |
| `insertion_failures` | 0 |
| collisions | 0 |
| leader-observed rows | 6,118 |
| valid TTC rows | 724；min TTC 6.971 s；median 19.09 s |
| following_status | closing 724 / opening 5,379 / steady 15 / no_leader 2,335 |
| measurement_status | valid 724 / not_applicable 7,729 / missing 0 / invalid 0 |
| 工程 P2 事件 | 0 |
| formal-alignment 可靠候选事件 | 0 |
| reliable following exposure | 609.4 s |
| reliable closing exposure | 71.7 s |
| P2-evaluable following exposure | 609.4 s（0.1693 veh-h） |
| 工程事件率 | 0.0 /veh-h（`formal_rate_eligible=false`） |
| 速度 / 加速度范围 | 0–27.78 m/s / −4.5–2.0 m/s² |

在自由流高速条件下该 fixture 的最小 TTC 为 6.97 s：SUMO 默认安全跟驰模型不会自发产生 `TTC < 2 s` 的连续状态，因此工程 P2 事件为 0。这是客观工程事实，不构成真实风险率结论。

**measurement_probe_queue_stop（40 s，seed 20260907）**

| 指标 | 值 |
|---|---:|
| state rows | 2,720 |
| vehicles | 7 |
| leader-observed rows | 1,520 |
| valid TTC rows | 729；min TTC 1.794 s |
| 工程 P2 事件 | 1 |
| formal-alignment 事件 | 1（边界完全一致） |
| 事件 | `probe_follow_1` 跟 `probe_lead_0`：onset 3.1 s、确认 3.3 s、结束 5.5 s、持续 2.4 s、TTC min 1.79431 s、25 帧、退出原因 `observed_threshold_exit` |
| P2-evaluable exposure | 151.6 s（0.0421 veh-h） |

该 probe 的刺激是多车道停驻队列尾（SUMO `<stop>` 声明），用于检验测量适配，不是真实交通证据，也不是远端风险处理。

### 9.3 可重复性

同 seed、同配置、同 fixture 重复运行后，`state.parquet`、`p2_engineering_events.parquet`、`p2_exposure_summary.json`、`config.json` 的 SHA-256 完全一致。

## 10. 工程输出与可复现证据（任务 H）

本地结果包（大型 parquet 保留在本机，不进 Git）：

- `code/outputs/formal/calibration/stage_0_5_sumo_baseline_engineering_v1_baseline/`
- `code/outputs/formal/calibration/stage_0_5_sumo_baseline_engineering_v1_probe/`

便携证据：`evidence/results/RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1/`（baseline 扁平文件 + `probe/` 子目录），含 `access_audit.json`、`audit.json`、`calibration_validation_policy.json`、`config.json`、`demand_config.json`、`formal_adapter_audit.json`、`manifest.json`、`measurement_status_summary.json`、`measurement_support_matrix.json`、`network_design_candidate.json`、`p2_exposure_summary.json`、`provenance.json`、`runtime_diagnostics.json`、`scenario_manifest.json`、`SHA256SUMS`、`sumo_formal_field_map.json`、`vehicle_type_config.json`。

每个包内含 `scenario_manifest`、network/route/demand/vType/time 配置、engineering seed、calibration/validation access policy、state/lifecycle/leader-following observations、TTC/measurement status、P2 工程测试结果、runtime diagnostics、unit/integration/smoke 测试、时间与单位检查、身份与前车连续性检查、数据质量与拒绝原因、seed 可复现性、输入/输出 SHA、provenance、manifest 与 SHA256SUMS。`export_project_evidence.py --verify` 返回 `PORTABLE_EVIDENCE_OK`。

## 11. 未完成科学事项（不得填 Completed）

| 事项 | 状态 |
|---|---|
| 真实网络几何是否已确认 | 否 — 仅为 `generic_highway_candidate`，`real_network_geometry_confirmed=false` |
| 正式交通需求是否已批准 | 否 — `scientific_demand_approved=false`，需求为工程 fixture |
| vType 映射是否已批准 | 否 — `vtype_mapping_approved=false`，pNEUMA 六类全部 `unmapped` |
| 正式仿真时间步是否已冻结 | 否 — 0.1 s 仅工程候选，`scientific_time_step_frozen=false` |
| 暖机与评价窗口是否已确定 | 否 — `warmup_and_evaluation_window_fixed=false` |
| SUMO 正式 P2 可比性是否证实 | 否 — `pending_measurement_equivalence_review` |
| 现实覆盖容差是否已批准 | 否 — `reality_coverage_tolerance_approved=false` |
| 独立验证是否已开展 | 否 — `independent_validation_performed=false` |

## 12. 质量检查与回归

- **既有阶段**：Stage 0.1 工程测试、Stage 0.2 正式风险测量、Stage 0.3 canonical 接口、Stage 0.4 有限通信验收、Stage 0.5.1 R2 参考读取、Protocol Lock readiness 全部在最终回归中执行；未修改任何历史封存结果。
- **新工程能力**：无消息标志强制关闭、状态字段齐全、符号统一、单位正确、时间步可配置可审计、P2 时间连续性不可伪造、测量状态与缺失原因可追溯、校准/验证隔离有机器测试、未批准参数无法被标为科学冻结、同配置同 seed 可重复。
- **失败处理**：本地无 SUMO 时集成测试 skipped（不伪造通过）；无法科学等价复用 Stage 0.2 提取器时明确标记 `Pending Measurement Equivalence` 而不宣布接通；涉及未批准科学参数的部分停在候选配置，等待研究者决定。
- **文档事实订正**：注册表移除已被再审计取代的旧结果 id `RES-STAGE-0.4-SEE-V2X-BSM-V1`（权威记录 `RES-STAGE-0.4-SEE-V2X-BSM-REAUDIT-V1`），已封存的历史 gate 报告保留其当时的 id。`doc/literature-notes/*` 的未提交删除与本次任务无关，未处理。

## 13. Stage 0.5 Gate 保持

```text
stage_0_5.gate              = pending_simulation_sample
scientific_claim_eligible   = false
protocol_lock_allowed       = false
stage_1_1_allowed           = false
```

工程 smoke 通过**不改变**上述任何状态；未创建 Protocol Lock，未启动 Stage I/II，未修改 readiness 测试、Gate 名称或默认参数。5.3 的工程结果只证明骨架具备能力；正式现实覆盖仍需 0.5.4 校准与 0.5.5 独立验证。

## 14. 结论

**Verified（工程层）**：独立 `generic_highway_candidate` 网络可建成并可运行；无消息标志可审计；状态/leader/净间距换算/闭合速度/TTC 状态/质量原因可输出且符号与单位正确；净间距换算经同车道几何与 XY 双重交叉核对（残差 0.0 m）；internal/recorded 步分离且节奏可审计；校准入口对验证窗口 fail-closed 拒绝；同 seed 结果可重复；输出可封存并可校验；工程 P2 由 SUMO-native 与 Stage 0.2 formal-alignment 两个适配器一致确认（probe fixture 1 个事件）。

**Engineering Only**：路网、需求、vType、驾驶行为、0.1 s 时间设定、工程事件率与 P2 适配接口。

**Pending**：正式道路/需求现实对应、车型与行为校准、SUMO 正式 P2 等价性、现实覆盖容差与 Stage 0.5 Gate 判据、独立验证。

下一步由研究者决定是否接受该工程骨架、候选路网与时间设定作为 Stage 0.5.4 校准起点；本任务不自动开始科学校准、正式验证或 Stage I 因果实验。
