# P4 Task2实现及兼容性审计

日期2026-11-04。Task1源码审计是前置事实，Task2在独立适配层实现批准方案，不改变历史Stage I语义。[机器审计](p4_implementation_audit_v1.json)和[函数溯源](p4_measurement_traceability_v1.csv)给出当前源码行号与版本。

|要求|实际实现|状态/限制|
|---|---|---|
|严格动作测量|p4_action_measurement.compare_actions|Verified：显式role/incarnation、时钟映射、exact共同观测、分段；不输出正式T_U|
|处理前完整资格名单|RegionalEligibilityRoster|Verified：重复/错成员/额外/N不符拒绝；scope证明依赖上游完整资料|
|车辆Formal贡献|measure_vehicle_state→contribution_bounds/rho_from_ttc|Verified：有效TTC有限正、源QC、独立空间质量；既有rho/config不变|
|固定窗口|vehicle_windows→continuity_is_valid/integrate_fixed_window|Verified：显式源步长，缺口/首尾/边界留界；不实现几何插值|
|最终Y|aggregate→equal_vehicle_average|Verified：固定N、同窗域、每member唯一、上下界分别等权；不是总和|
|P3外部桥|link_p3_state→原validate_records|Verified：消费ref是{message_id,consumption_receipt_id}，不是消息ID字符串；检查精确读回与实体/时钟支持|
|P4独立契约|p4_measurement_bundle|Verified：11实体，JSON/hash/PK/FK、派生复算、源字节可选核验；pair输出独立|
|辅助TTC暴露|validated_ttc_exposure|Verified：P4入口valid/NaN拒绝；旧prelock_metrics原函数未改，旧直接调用限制仍保留|
|macro/跨源全自动|未实现|Unknown/明确未部署，不纳入FormalY|

## 保持原字节的模块

formal_risk_measurement.py、stage_0_5_sumo.py、stage_i_mechanism.py、prelock_metrics.py、controller_evidence.py、P7源码/config和既有测试均不改。P4仅新增5个模块、3个脚本与1个专项测试文件。测试fixture和完整失败日志在本机独立audit目录，不污染核心源码。

Task1发现的原equal_vehicle_average缺名单守卫，由新assembler前置校验解决；原first_sustained_divergence跨缺口/延长末点不用于P4正式路径。原integral不做几何裁切，由P4要求上游成员资格/区间证据并对不确定段保留界，未擅自实现边界插值。

## P7现有资料核对

只读enabled_v2/actual_trajectory.json为352条，vehicle_id仅p7_target；existing_measurement_states.csv有该target的速度/加速度、leader、TTC/DRAC/质量，但无完整区域资格名单、处理前完整性证明或正式region/window。Risk Observation是状态附件及引用，不能当作已经生成完整区域Y。历史NoMessage/Disabled同样不是本次完整总体输入，未重跑。

新增专项测试直接读取既有Enabled v2 controller_evidence，用实际消费receipt/decision/command/execution/action ID成功桥到同一state；错误readback_ref被拒绝。此项验证链路适配，不增加独立运行，不证明因果效应。

## 科研事实状态

Agreed：D01–D08及最终等权算子；Verified：离线实现、确定性数学及源代码约束；Unknown：真实资格总体覆盖、正式几何/窗/动作阈值及误差、现实可观测性、因果区域风险。P4协议可使用不等于Formal Algorithm全部批准。Formal A/Qualified仍0，F0及总体T_R–T_P Unknown。

不改DAG、source-present ITT、四格效应、Adoption、P3schema、Formal参数、Gate/Lock/Stage1.1及Overleaf。Task1原文/字典/便携记录均保留，新增_v1机器文件接续。四个定义文件仅追加日期决策，不改历史Task6/E61或Task7/E61原行。
