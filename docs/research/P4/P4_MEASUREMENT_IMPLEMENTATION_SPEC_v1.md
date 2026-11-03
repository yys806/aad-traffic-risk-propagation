# P4测量实现规范 v1

Task AAD-P4-TASK2-20261104；工程契约aad.p4.measurement.v1。科研授权为[2026-11-04 D01–D08](P4_RESEARCHER_DECISIONS_20261104.md)，统一定义仍v0.4／27项。本文描述已运行的工程能力，不授予正式实验资格。

## 1. 模块与调用链

|模块|实际入口与职责|
|---|---|
|p4_measurement_contract.py|P4InputError、stamp/check_record、provenance_index、validate_support、validate_states；有限JSON、主键/来源/时钟/显式cadence|
|p4_action_measurement.py|validate_pair_manifest、compare_actions；处理前角色映射、可靠真实共同观测、有符号Δv/Δa及段界|
|p4_regional_risk.py|RegionalEligibilityRoster、measure_vehicle_state、RegionalRiskAssembler、validated_ttc_exposure；名单、源QC、Formal贡献/积分/固定N聚合|
|p4_evidence_bridge.py|p3_index、link_p3_state、native_state_bridge、link_risk_actions；P3原validator加显式ID与读回核对|
|p4_measurement_bundle.py|build_bundle、validate_bundle、write_bundle、assignment_result、unavailable_outcome；11实体JSON、外键、重算、每assignment输出|

源码均在code/src/riskprop/。命令入口code/scripts/validate_p4_measurement.py；合成构造仅在code/scripts/p4_validation_cases.py；独立数值复核code/scripts/verify_p4_mathematical_examples.py，不导入riskprop。

输入support+preassignment roster+actual states+provenance+显式association → 源QC及risk_sample → interval links → 每固定成员vehicle_window → regional_outcome。桥接支路state→action_execution_bridge、risk_sample→risk_action_bridge。配对动作独立以pair_manifest和两run实际states为输入；不把两run混入同一个assignment bundle。

## 2. Action

Δv(t)=v_treat(t)−v_base(t)为主，Δa为辅，均有符号且另存绝对值。两run允许不同vehicle_id；只能通过分配前pair角色映射到稳定incarnation。manifest列明两侧run/assignment/event/clock/phase、参考时钟、offset、映射误差与来源。源state唯一主键为run/vehicle/incarnation/clock/time/phase；全局state_id亦唯一。event必须一致。

只匹配映射后完全相等的真实时间；clock不兼容、误差非零、identity或kinematics可靠性未证实、非PRESENT、无速度均保留不可比原因。无共同点返回UNKNOWN_NO_COMMON_SUPPORT；不插值，不用近邻时间，输出保留完整有符号序列及共同支持数/范围。

采样缺口、显式链缺失、incarnation不匹配/退出导致的缺观测、lane/leader切换、质量不明均分段；不调用旧first_sustained_divergence。段界只描述可用支持，不确认持续效应，不延长末点。时间差1e−12仅检查已声明采样步长的浮点算术误差，不是动作效应阈值。Formal原语自身既有时间数值容差保持不变。

首次非零Δv/Δa仅数值描述，不等于科学动作变化。onset_status=THRESHOLD_UNSET；candidate_onset_lower/upper、persistence_confirmation_time、formal_T_U均null。正式阈值/持续时间/测量容差仍Unknown。T_A/T_C可从P3原记录读取；P4不凭一个读回点推出T_U、T_R或T_P。

## 3. 完整区域资格总体

名单不得从实际轨迹反推。RegionalEligibilityRoster保留处理前成员、role、绑定、rule/version、冻结时间上界、来源和完整性证明；N来自名单。支持/名单冻结上界均必须严格早于assignment时间下界（同一声明参考钟）。重复member/role/binding、声明N不符、额外/错误成员、实际身份不符拒绝；不静默合并。

名单完整性须由上游完整需求/预定角色资料证明，hash只能绑定来源，不能自动证明科学覆盖。规则、来源、完整性或处理前冻结不明则UNKNOWN_SCOPE。名单成员齐全但观测缺失，逐成员生成完整窗口记录；整车缺失[0,1]，N不变。aggregate少窗口为INCOMPLETE_ROSTER；同N错身份拒绝。名单根本不存在时unavailable_outcome保留assignment，expected_N=null；不虚构成员。

## 4. 单车Formal风险与质量

复用formal_risk_measurement.py原rho_from_ttc、contribution_bounds、continuity_is_valid、integrate_fixed_window、equal_vehicle_average。rho=exp(−TTC/τ)，既有τ=15.364279197080283 s；不是本次新冻结。P2事件TTC阈值2.0 s、最小时长0.2 s与rho映射不同，绝不据事件阈值截断rho。

源策略QC版本/来源和实际identity可靠性必需。有效TTC须有限正数、可靠leader/incarnation、正gap、可靠速度及正closing；异常valid/NaN转invalid Unknown贡献，原坏值保留上游来源。有限JSON封包拒绝NaN/Inf。源类型SUMO/NGSIM/SYNTHETIC具备限定跟驰能力；pNEUMA/SPMD不会升级Formal风险能力。可选derive_native_measurement只调用已有SUMO纯测量函数，不启动仿真。NGSIM接收有来源且QC一致的上游测量，不重做完整数据审计。

区域可靠性独立于运动学QC。可靠且scope/坐标版本一致的OUTSIDE贡献[0,0]；INSIDE且有效rho为点值；区域未知、invalid、missing、not_measurable保留[0,1]。not_applicable只接受可靠非闭合跟驰关系或SUMO原生无leader证明；未观测leader不是无leader。NGSIM/pNEUMA/SPMD不能冒用原生证明。零只针对该后向跟驰贡献，非全交通安全声明。

## 5. 空间及连续性

本实现消费明确版本的区域成员资格及区间证据，不实现几何插值/自动地图匹配。相邻状态须previous_state_id匹配、可靠相同区域归属、同lane及区域区间来源，随后仍须通过原Formal连续性：相同source_scope五字段、trajectory/leader、时钟anchor、frame/ms步长及可靠身份、明确无gap/break。P4显式传入源cadence，绝不依赖Formal默认0.1。

跨边界、leader/lane切换、钟误差、缺帧、退出/未知位置、区间证据缺失不延长左值；断链区间全界。固定窗首前/末后亦全界。原语只在有证明的相邻区间使用既有左值语义，可在真实括住窗口边界的观测对内裁切，不向观测之外推。无leader点可零，但原Formal连续性要求可靠leader，故不能伪造leader来证明整段零，相关时段保守Unknown。

## 6. 固定窗和Y

每member同W=[start,end)、L=end−start。积分下界J_L、上界J_U；均值J/L。known_time是界收缩成点的时间，unknown_time=L−known_time；observed_pair_time是连续性通过的时间，不等于已知风险时间。每车完整L，不能用有效时长替换。

Y_L=(1/N)Σ J_i,L/L；Y_U=(1/N)Σ J_i,U/L。名单/身份/region/version/window/roster hash和每成员唯一结果核验后才调用原equal_vehicle_average；不增加风险权重、不合成DRAC/PET等。输出单位1，界均在[0,1]。scope未证实则不发布完整区域Y，已知窗口下单车数值仅受限诊断；未知窗口则每成员null占位。

## 7. 使用与边界

python code/scripts/validate_p4_measurement.py --input <符合契约的JSON> --output <独立目录>。用--examples生成标注SYNTHETIC_VALIDATION_ONLY的样例；合成L=3、步长1只验证软件，不是正式参数。validate_bundle可给artifact_root核验真实来源字节；默认只核验哈希格式、ID和派生一致性，明确source_bytes_verified=false。

assignment_result保留所有处理条件及缺失运行的测量结果；车辆/采样点不是额外随机化单位。P5/P6获得固定名单hash、scope/window/N、Y界、缺失质量、版本与source hashes，P4不执行ITT/四格/功效。macro仍独立通道，本v1不实现其工程表。P7已有数据不满足完整区域输入，因此没有新真实区域Y。
