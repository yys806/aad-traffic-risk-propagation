# P4工程测量数据契约 v1

schema=aad.p4.measurement.v1；derivation=aad.p4.measurement-implementation.v1。D08 Agreed；P3 aad.p3.controller-evidence.v1保持原字节。Task1 [Proposal](P4_MEASUREMENT_DATA_CONTRACT.md)及247字段原表保留历史，本v1是已实现最小子集及必要新增字段。字段级机器表见[p4_measurement_variable_dictionary_v1.csv](p4_measurement_variable_dictionary_v1.csv)，不宣称旧247项全实现。

## 1. 载体与验证

JSON，无重型依赖。输入对象support、roster（可null）、states、provenance、associations，可带p3_records。输出bundle有schema_version、records十一实体数组、roster、interval_links、p3_records（只读外部P3原记录）、bundle_sha256、usage及scientific_claim_eligible=false。每条输出record携带entity/schema/derivation/record_sha256；SHA采用UTF-8、sort_keys、compact separators、allow_nan=false的canonical JSON。物理来源hash是实际文件字节，不等于JSON对象hash；示例source文件刻意使用canonical字节使二者一致。

validate_bundle检查记录hash、各实体唯一ID、context、外键、固定名单、派生risk/window/outcome重算；有P3动作引用时使用原P3 validator并重新验证桥接链。artifact_root可选：有则逐provenance source_ref相对根路径核验文件与SHA，拒绝越界；无则source_bytes_verified=false，不称已验原始字节。schema_version只接受v1。

## 2. 已实现实体

|实体|PK|核心字段/单位|来源及可空条件|
|---|---|---|---|
|support_manifest|support_id|run/assignment/event/unit；reference_clock；region/version/coordinate；window/version/start/end(s)；cadence(step_s,frame_delta,provenance)；source_quality；scope冻结/assignment时间(s)|上游处理前支持；event可null；未知region/window显式null，不能形成完整Y|
|provenance|provenance_id|source_ref、source_sha256、source_derivation_version、derivation_version|原始/配置/声明来源，保留上游source_derivation_version，不被P4 transport derivation_version覆盖；ref/hash/version不可空；source内容真实性由上游及字节校验分工|
|cohort_member|member_id|role_id、qualification_provenance_id、bindings[{vehicle_id,incarnation_id,provenance_id}]|处理前roster；不因缺观测删除；bindings未能验证的实际状态拒绝|
|state_observation|state_id|run/assignment/support/event/member/vehicle/incarnation；clock/time_s/time_error_s/phase；observation_basis；kinematics_reliable；speed(m/s)、acceleration(m/s²)、lane_position(m)、lane；leader身份/速度、net_gap(m)、TTC(s)、DRAC(m/s²)；region归属/可靠性；source_scope/frame/ms/anchor；previous_state_id、interval来源；QC/version/provenance/readback|实际读回/源观测/明确合成；运动数值缺失为null，不接受估计态冒充；上游非有限TTC由适配器给invalid或封包拒绝，原坏值留source|
|action_execution_bridge|bridge_id|state_id、action_observation_id、execution/command/decision/consumption/message refs；execution_statuses；command_status；native_evidence_ref|显式P3 ID；无命令为NATIVE_NO_COMMAND、refs空；实际execution状态按P3保留，不因有命令宣称执行成功|
|action_comparison|comparison_id|pair/hash/role；baseline/treatment run、assignment、state IDs；共同time(s)；Δv/abs(m/s)、Δa/abs(m/s²)；segment/reasons|独立pair artifact的真实共同观测；Δa可null；跨run引用由pair原始输入验证，不放入单assignment bundle|
|action_timing|action_timing_id|pair/role/comparison refs、共同点数/范围；首次数值非零差异(s)；onset状态、候选区间、确认时间、formal_T_U|独立pair artifact；未批准阈值均THRESHOLD_UNSET，候选/确认/T_U为null；首个差异可null|
|risk_sample|risk_sample_id|state/member/context/time；measurement_status/reason/reliable；region状态；TTC/DRAC/rho；lower/upper_contribution；Formal版本/provenance|测量适配器；ttc/drac/rho可null；贡献界有限且[0,1]|
|risk_action_bridge|risk_action_bridge_id|risk_sample_id、bridge_id、association_scope=EXACT_STATE_ID|多对多显式外键，同state和context；不用近邻时间|
|vehicle_window|vehicle_window_id|member/bindings/context/roster hash；region/window版本与start/end(s)；fixed_window_s；lower/upper_integral(s)、lower/upper_mean(1)；known/unknown/observed_pair_time(s)；risk_sample_refs；coverage/measurement状态|固定成员每人一条；整窗缺失[0,1]；窗口未知为null占位而非0|
|regional_outcome|outcome_id|assignment/event/unit/support；population_scope、expected/received/unique_N；roster hash、vehicle_window_refs；固定region/window；lower/upper_outcome(1)、status、missing_summary、provenance、aggregation_version|完整scope才发布Y；无名单N=null；成员缺窗INCOMPLETE_ROSTER；因果/正式参数冻结标志false|

common字段：support_id/run_id/assignment_id/event_id用于单assignment精确上下文。reference_clock表示全部支持/冻结/分配时间的参考钟；原生clock与映射误差另记。不比较未知时钟，不按phase名称推断因果顺序。pair_manifest记录两侧offset、误差和源；有非零误差目前返回无严格共同支持，未选科学容差。

## 3. 名单及外键

roster作为独立输入声明含support/run/assignment/event、region/version、expected_N、members、complete_population、eligibility_rule/version、roster_version、frozen_time_upper_s、provenance_id/completeness_provenance_id。必须由分配前资料覆盖完整资格总体，语义完整性是来源证明责任，软件不能从有限观察证明全交通覆盖。

state.member_id→roster.members；state身份→该member唯一预定binding。risk.state_id→state；bridge.state_id→state；risk_action_bridge两端必须同state；vehicle_window.risk_refs→同member；outcome.vehicle_window_refs→每固定member恰一次、同窗同域。command链通过P3 action→execution→command→decision→{message_id,consumption_receipt_id}显式引用，验证receipt确实POLICY_INPUT_INCLUDED且scope/readback/time支持相符。P3仍负责原生命周期/策略/安全时序验证。

允许多对多；没有消息命令的区域车辆合法，需要native_evidence_ref及provenance，不允许自动补消息链。standalone comparison artifact包含pair_manifest和输出，对应的版本化输入样例同时保存，便于精确重算。

## 4. 状态与错误

POINT_IDENTIFIED、INTERVAL_IDENTIFIED：测量贡献点/区间，非因果识别；UNKNOWN_SCOPE：资格或域/窗未证实，Y界null；INCOMPLETE_ROSTER：缺固定成员窗口，拒绝缩N发布；VALID_WITH_LIMITATIONS：契约/工程验证通过但科研边界保留。坏结构抛P4InputError(code,detail)，按INVALID_INPUT处理，不能用异常fallback零。

measurement_status保留valid、invalid、missing、not_applicable、not_measurable；后者不是前四类的零值。region INSIDE/OUTSIDE/UNKNOWN与region_reliable独立；lifecycle PRESENT/EXITED/UNOBSERVABLE独立；coverage COMPLETE/PARTIAL/FULLY_UNOBSERVED/UNKNOWN_SCOPE。右删失在action observation_end_status=RIGHT_EDGE_NO_EXTENSION表达，onset本身因阈值未设保持null，不能宣称已确认无效应。

所有已发布贡献/均值满足0≤lower≤upper≤1；积分范围[0,L]，固定分母L、N。缺失/未知不能转0；不确定区间太宽时原样报告。不是所有有限数据都能点识别。

## 5. 部分/未实现能力

已实现11逻辑实体；action pair实体单独承载，assignment bundle对应数组为空。macro_observation保持独立方向，v1未实现其序列化/计算。未实现自动完整总体发现、几何穿越插值、原始全数据集自动导入、非零钟误差下配对、正式T_U/阈值/持续性估计、风险因果T_R、ITT/四格/功效；不能把这些写成生产能力。

P5/P6接口assignment_result输出每分配单位结果、源hash与independent_unit=ASSIGNMENT_NOT_VEHICLE_OR_SAMPLE。没有采用/消息失败/Disabled/NoMessage不被筛掉；没有scope亦输出Unknown。P4不执行统计识别。
