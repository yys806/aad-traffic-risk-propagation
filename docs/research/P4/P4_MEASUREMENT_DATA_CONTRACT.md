# P4 测量数据契约（提案）

Task: AAD-P4-TASK1-20261103。版本：aad.p4.measurement.proposed.v0.1。日期：2026-11-03。**Proposal / Awaiting Researcher Decision；未部署，不修改aad.p3.controller-evidence.v1。**

这是外部明细表/manifest方案，不创建新的科研定义；服从[统一v0.4](../definitions/README.md)、[P1 estimand](../P1/ESTIMAND_SPECIFICATION.md)。字段明细以[p4_measurement_variable_dictionary.csv](p4_measurement_variable_dictionary.csv)为本提案同版本的机器可读展开；表内每字段均列type/unit/meaning/source/nullable_when/status。无量纲/标识单位写1，未知值为null并附状态，不能空串代替数值或填0。

## 1. 关系结构及主键

| 表 | 主键 | 必要外键 | 行含义/当前实现对照 |
|---|---|---|---|
| support_manifest | support_id | provenance_id | 单run/assignment/event测量支持，含region/cohort/window；P7目前范围字段未定 |
| provenance | provenance_id | 无 | 原始字节与派生版本，不能只给文件名 |
| cohort_member | member_id | support_id | 处理前名单中的一员，所有成员保留；名单与run中incarnation显式映射 |
| state_observation | state_id | support_id, member_id | 一次实际post-step/原生轨迹读数，不能用policy reference填充 |
| action_execution_bridge | bridge_id | state_id, action_observation_id；execution_id可空 | P3显式引用到实际状态，允许无消息命令时的原生动作 |
| action_comparison | comparison_id | pair_id, baseline_state_id, treatment_state_id | 一个明确可比点或其失败状态；所有对齐/缺口政策可追溯 |
| action_timing | action_timing_id | pair_id, support_id, comparison_refs | 区分命令/执行/首次差异/onset/确认，非正式因果T_U估计器 |
| risk_sample | risk_sample_id | state_id, support_id | 单车单时刻的TTC/DRAC/rho和上下界 |
| risk_action_bridge | risk_action_bridge_id | risk_sample_id, bridge_id | 显式多对多关联；不能仅按近似时间连接 |
| vehicle_window | vehicle_window_id | support_id, member_id, risk_sample_refs | 单预定成员全窗贡献；完全缺失仍一行[0,1] |
| regional_outcome | outcome_id | support_id, vehicle_window_refs | 固定名单汇总及覆盖界；最终算子待批准 |
| macro_observation | macro_id | support_id | 同域D/V/A交通状态，独立于Formal rho |

表均为**拟议结构**，只有来源字段能映射现有生产者时才填Observed。P3 sidecar继续保存其原schema，外部表被observation_ref/hash引用；区域风险可对应多个车辆的Action，不能强制单vehicle关系。

## 2. 共同字段与可空条件

每表共同字段：schema_version:string=本提案版本；record_status:string；source_ref:string；source_sha256:64hex；derivation_version:string。派生行引用输入manifest的哈希及源行/记录定位，不让单个source_sha256模糊表示多文件；多源通过provenance.input_refs数组，每项包含path/hash/selector。

- ID一经发布不可复用或跨run搬移。所有关联检查run/assignment/event/pair scope；可跨run的唯一关系是声明的pair/comparison，且需显式baseline/treatment角色。
- assignment_id是预先分配身份，不由Adoption或Action成功与否生成。尚未正式随机化的工程assignment必须带assignment_source和design_status，不能伪装成随机实验。
- event_id可为null仅当没有可识别事件或本身是无源参照；event_status写NOT_APPLICABLE/UNKNOWN，不新编合格source。source_event_ref与风险测量用的scope_event不可混淆。
- P3 execution/command可为空仅在NATIVE_NO_COMMAND或生命周期事件，给出reason；不能虚构无消息时的控制命令。
- 状态/运动量为null的条件：退出、不在场、测量缺失/无效/不适用；分别保留原因。invalid量可保留raw_ref中的原始坏值，正式数值列不用NaN/Infinity冒充有效值。
- 风险上下界仅在量纲/界定义和scope可解释时填有限数；scope本身未定时event outcome为null+UNKNOWN_SCOPE，不用[0,1]掩盖“连目标对象都没定义”。已确定scope但缺数据才用贡献[0,1]。

## 3. 支持manifest与处理前名单

support_manifest包含run_id、assignment_id/source、event_id、pair_id、randomization_unit_id（未知可空）、design_status、region_version/geometry_ref/hash/coordinate_system/lane_ids、cohort_version/roster_ref/hash/roster_frozen_at、window_version/start/end/time_origin_ref、aggregation_version/status、clock_mapping_ref、measurement_version/config_sha256、expected_step_s。

正式可用记录必须满足window_end>start、同一clock和单位，cohort名单在处理前冻结且N>0。region/cohort/window未批准时declared_scope_status=UNKNOWN_MISSING_FORMAL_SCOPE，不得“按实际跑了多久”补齐。

cohort_member包含pre_treatment_role、vehicle_id、incarnation_id、入场/离开时间界及position_observability、selection_ref。incarnation可在预先名单生成时尚未知，但到实际state关联前必须由真实身份生产者映射；不以leader:entry1字符串推断多次生命周期。跨run角色映射通过pair_manifest_ref/hash，不要求不同run中的ID字符串相同。

固定cohort与全区域总体分别标population_scope，不自动互换。车辆退出不删名单，不补入替代车；可证区域外的风险贡献零与未知位置的贡献界严格区分。

## 4. 原生时间、实际状态与动作

state_observation字段包括：native_time/native_time_unit/clock_id；mapped_time_lower_s/upper_s；step/phase/sequence；observed_at/available_at；vehicle/incarnation/member；x_m/y_m/coordinate_system、road_id/lane_id/lane_position_m、speed_mps/acceleration_mps2、leader_vehicle/incarnation、leader_observed、leader_observability_status、leader_speed_mps、net_gap_m/closing_speed_mps、lifecycle_status/measurement_status/quality_flags。

时间支持不是单timestamp即可证明：

1. 同phase重复主键失败；同step不同phase允许，phase顺序来自明确时序证据，不能按字符串排序当作真实因果先后。
2. observed_at、available_at、mapped-time和原生time分别保存，不能用日志落盘时间替代发生时间。
3. 不同步时钟使用映射区间及误差；不得伪造精确先后。
4. state自身身份/time可用而leader缺失时仍保存运动学观测，risk单独Unknown/不适用；不能整行删掉。

action_execution_bridge明确P3 action_id/execution_id/command_id/decision_id和state_id；核验execution的getter/readback所在文件hash、step/phase/entity。ACK不是Action值。command_tenure_id可标同一个持久约束，避免把连续readback当成多次命令。

action_comparison必须有pair_manifest_hash、两stateID、same_role证据、matching_policy_version、clock_compatibility、common_support_status及Δv/Δa/Δposition/Δgap/lane_change/leader_relation_status。同一leader交互段才解释gap差；换leader分段。两实际值均有效才有差值。无共同支持写Unknown并保留失败原因，不能写Δ=0。

action_timing单存adoption_consumption_time、command_change_time、first_execution_observed_time、first_observed_difference_time、candidate_onset_lower/upper_s、persistence_confirmation_time_s、right_censored、threshold_spec_ref/persistence_spec_ref及coverage_ref。未批准的规则引用为null+PROPOSED_UNSET；不默认启用某个阈值。

## 5. 风险样本、连续性和聚合

risk_sample必须携带TTC/DRAC原始测量status/reason、rho/config/version、空间member状态与独立reliability、lower/upper_contribution、leader interaction id、continuity_prev_state_ref/continuity_status、raw source selector。rho=null不等lower/upper=0；可靠区域外或可靠不适用可[0,0]但rho仍null。

| 条件 | 数值列 | 状态及要求 |
|---|---|---|
| reliable valid positive TTC | TTC/rho有限；贡献两界相同 | Formal版本/config相符 |
| reliable outside | 两界0 | region可靠，与measurement_reliable独立 |
| known scope / unknown member or measurement | 两界0/1、rho null | 原missing/invalid/unknown原因保留 |
| scope未定义 | 不创建可引用的正式区域Y | outcome null，UNKNOWN_SCOPE |
| 右删失 | 单点若有效仍保留；未观测时段按界 | censor_time/status，不删全窗尾部 |

vehicle_window需固定W及L、lower/upper_integral_s、lower/upper_mean、known_time_s/unknown_time_s/observed_pair_time_s、sample_refs/hash、边界/缺口审计、coverage_status。对整车无观测，在scope和bound合法时形成[0,L]/[0,1]，raw refs空+FULLY_UNOBSERVED，不删车。

regional_outcome需expected_N/received_N/unique_N、roster_hash、一一对应的vehicle_window列表、同region/window/config校验、lower/upper、aggregation_status/version、unit_id、outcome_status及missing_summary。只有expected_N=received_N=unique_N且成员完全一致可聚合；相同数量但错名单也失败。**最终聚合算子为待决Proposal**，正式资格不由此契约自动授予。

multi-leader/冲突对象不可直接按数目叠加同一车辆贡献；现有后向跟驰投影只使用经过资格检查的实际leader段。拓展到多冲突属于新科学对象，超出本任务。

macro_observation独立保存area_length_time、lane_normalization、distance_sum_m、time_sum_s、q/k/u及composition_coverage。V=0时u=null、reason=ZERO_VEHICLE_TIME；有车辆未观测时不能把可见子样本的D/V当全域真值。Macro不是risk_sample，不能作为缺失rho的填充值。

## 6. 输入一致性与失败规则（拟议可执行验收条款）

| 检查 | 失败时处理 |
|---|---|
| 同run引用闭合、外部path/hash/row真实存在 | REFERENCE_ERROR，禁止正式结局发布 |
| 身份唯一、incarnation/pair角色映射、clock支持一致 | IDENTITY_OR_CLOCK_ERROR，不用最近时间替代 |
| 实际v/a源于readback；reference/ACK与actual分列 | INVALID_ACTION_SOURCE |
| valid TTC须有限正值且leader/gap/closing条件相容 | INVALID_MEASUREMENT_INPUT，保留原行/Unknown界 |
| 同scope同窗、固定成员全量且唯一 | INCOMPLETE_FIXED_ROSTER，不改变分母 |
| 连续性与几何边界有证明 | 否则该段Unknown，不默认左值跨界 |
| 0≤lower≤upper≤1，积分单位s、均值单位1 | INVALID_BOUNDS_OR_UNIT |
| 未定主指标/算子/窗口不冒充Agreed | PROPOSED_NOT_FORMAL |

这些是本任务提出的验收规则，不表示已有生产验证器全部实现；[审计表](p4_implementation_audit.json)逐项标partial/missing。P3通用validator通过只说明其自身图契约。

## 7. P5/P6输出接口及识别边界

输出应包含全部分配单位的outcome/status、固定名单和范围、同预定时间网格上的界序列、缺失/失败/删失、measurement/derivation/source hashes、assignment/design来源及pre-treatment资格。未采用/无命令/动作不明显的单位不因机制失败被丢弃。

P4不产生Adoption因果效应、source-present ITT、四格效应、同时置信带、SESOI或功效结果。did_interval不是统计置信区间。T_R/T_P通过外部经授权估计接口引用，当前Unknown。是否插值、最终Y算子、人口覆盖、正式Action规则等集中列入[研究者待决事项](P4_RESEARCHER_DECISIONS.md)，无需另建重复接口设计任务。
