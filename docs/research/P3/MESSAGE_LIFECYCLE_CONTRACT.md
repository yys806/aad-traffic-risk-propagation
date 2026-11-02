# Message Lifecycle Contract

Task：AAD-P3-TASK1-20261102。版本：P3-ML-v0.1。状态：**Proposed / Awaiting Researcher Ratification**。文档契约，不修改旧schema或生产执行器。继承[统一定义v0.4](../definitions/README.md)中的DEF-INF-001、DEF-TIME系列及细则R；不新增Definition ID。

## 1. 对象、身份和证据

九阶段分别记录：Source Event Confirmed → Message Generated → Message Sent → Message Delivered → Message Validated → Message Adopted → Controller Decision → Control Command Issued → Actual Action Executed。物理onset可早于source confirmation；消息生成资格不等于实际生成。消息链不替代P2独立物理到达证据。

以下是推荐逻辑字段，不要求实际接口采用完全相同名称。未来接线须给出schema映射、版本和验证依据，不能仅添加空列后宣布满足契约。

| 记录 | 必要逻辑字段 | 最小证据来源 |
|---|---|---|
| 公共事件信封 | schema_version、record_id、run_id、pair_id/block_id、cell/assignment、event_type、producer_id/version、status、reason、evidence_ref/hash | 产生该事件的组件日志；fixture必须标fixture_only |
| Source引用 | source_event_id、source_type（Formal A/controlled B/sham）、source_vehicle_id及incarnation、qualification_status/version、confirmation_record_ref、generation_eligibility_ref | communication-blind源资格记录；不能由消息布尔值替代 |
| 消息本体 | message_id、logical_message_id、attempt_id、source_event_id、sender/receiver实体与incarnation、target/cohort/region引用、payload_type、payload/schema/version、payload_hash、created/valid_from/expires信息 | 不可变消息实体与序列化后载荷；同ID不同载荷为冲突 |
| 生成 | generation_record_ref、actual生成时间、资格检查结果 | 消息生成器产生本体后的记录；不能写planned time充当完成时间 |
| 发送 | message_id、attempt_id、sender、transport/queue、actual发送时间、send_status、bytes、failure_reason | 发送组件回执；enqueue和真正send分别记录 |
| 送达 | message_id/attempt_id、receiver、receive_record_ref、delivery_observation_time、receiver可用时间 | 接收端日志；sender成功或仿真计划到达不足以证明送达 |
| 验证 | validation_id、接收记录引用、source/target/freshness及payload/integrity检查、validator/version、结论与原因 | 实际验证执行记录；不凭source_valid=True推定源资格成立 |
| 采用 | consumption/adoption_receipt_id、validation_id、message_id及payload_hash、controller_instance/version、decision_id、采用时间/可用时间、结果原因 | [控制器契约](CONTROLLER_ADOPTION_CONTRACT.md)中的策略消费记录 |
| 决策/命令/执行 | decision_id→command_id→execution_id及车辆状态引用、安全覆盖记录 | 同一控制器及执行接口的实测日志；详见控制器契约 |

消息和决策允许多对多：一个决策可消费多个消息，一个有效消息可被多个周期消费；关联表逐项保存引用、消费次数与载荷版本。重传、广播多接收者、重复到达不得共用一个不分接收者的“成功”标志。事件record_id与message_id不同；时间相近不是外键。

## 2. 时间与不确定性

每个实际事件至少保留：native timestamp/unit、clock_id、reference mapping/version、允许时间区间/集合、simulation_step、phase/sequence、observed_at、available_at、误差来源/上界状态。不可观测的时间为空并附Unknown原因，不能用0代替。时间不确定性沿用统一时间登记，不在此冻结数值。

生成、发送、接收、验证、采用、决策、命令、执行分别来自各自组件；API调用前后和simulationStep前后必须区分。同一仿真步内可同标量时间，但须有phase/sequence支持逻辑先后，不能靠稳定排序或伪造小时间差建立严格先后。重叠区间仅说明顺序尚不可判定；不能把W6严格物理判据直接改成消息链通用宽容规则。

发送→接收时延与生成→接收、接收→控制器可用、验证→采用、命令→执行时延分开。跨时钟没有可辩护映射时保留Unknown；无绝对误差证书不得将相同UTC纪元当作同步证据。记录时延不等于已校准真实时延。

消息过期须依据预先批准的validity rule及同一载荷版本判定；有区间误差时可能为Unknown。不能将message_age_s这一差值当成已执行过期校验或数值TTL。没有事先规定的到期点不得补造TTL。

## 3. 状态与失败语义

“观测状态”和“生命周期阶段”分别存储。以下是展示分类，底层不将同一消息不同接收者、尝试、决策压成互斥单列。

| 状态 | 可使用的条件 | 不可推断的内容 |
|---|---|---|
| Not Generated | 生成器在完整指定机会/窗口内明确记录未生成及原因 | 没有一行日志≠未生成 |
| Sent but Not Delivered | 发送已证；交付结果另列pending/confirmed failure/censored/Unknown | 接收记录缺失不自动成为Packet Loss |
| Delivered but Invalid | 接收与实际验证失败均有证据，保留失败项目 | 无验证记录不当作invalid |
| Validated but Not Adopted | 验证成功，控制器在完整决策机会内明确拒绝/未消费 | 接收ACK不证明采用；观测截止前未消费可能只是待处理 |
| Adopted | 有关联具体决策的策略消费凭证，符合待批准的采用边界 | 不自动要求动作变化，更不证明因果作用 |
| Adopted but No Action Change | 已采用且完整规定动作观察支持下未检出预先定义的动作差异 | 不等于无风险效应；动作阈值/反事实尚缺时应Unknown |
| Unknown | 缺日志、时钟、身份、可用性、载荷或消费证据，原因单列 | 不能转成False、Negative或默认失败 |
| Right-Censored | 确认观察支持至截止时仍未发生目标阶段，之后未观察 | 观察中断不一定是合法非信息性右删失 |
| Not Applicable | 设计上未分配该阶段，例如无源机会或关闭相关通道 | 不等同无线链路丢包；sham有自己的生命周期 |

另记lost_confirmed、duplicate、reordered、expired、cancelled、safety_overridden等事件/原因。lost_confirmed必须有已定义发送分母、接收机会、截止规则及接收端完整性证据；否则只能记录“未观察到接收”。通道禁用/未尝试不能计入无线丢包分母。

## 4. 后续实现的验收断言（本任务不实现）

- 相同run/实体incarnation内外键可追溯；孤儿、重复冲突、跨run错误关联均报错或Unknown，不能按最近时间补链。
- 源资格、消息验证、控制器采用分别有证据；sham不产生真实源资格，source-absent不伪造source_event_id。
- 显式记录阶段true/false/Unknown/NA及原因；禁止对生产证据直接fillna(False)或对字符串做宽泛bool转换。
- 时间必须有限或明确为未知；保留interval/phase；无源确认不可凭消息生成倒推源物理onset。
- 跨版本转换不可写回历史协议表；旧message_dropped/ adopted的含义由原producer决定，缺新凭证时不得升级。
- 每项汇总报告分母：计划机会、实际生成、实际发送、已证接收、已验证、具有决策消费凭证分别统计；延迟同时报告删失/未知，不能只报成功者时延。
- assigned处理后发生的任何链路失败、安全覆盖、未采用、无动作均保留在预定ITT；描述性采用率不是因果效应。

## 5. 当前实现兼容性

[formal_design.py](../../../code/src/riskprop/formal_design.py) L138–237已实现布尔依赖、标量时间顺序、message_age一致性检查，但不验证控制器消费、消息ID唯一性、过期规则或源资格外键；fillna(False)不能承载本契约的Unknown。

[formal_artifacts.py](../../../code/src/riskprop/formal_artifacts.py) L113–149已有source_event_id/message_id、payload与command/applied/safety列；列存在及文件SHA不证明对应事件发生。[stage_i_mechanism.py](../../../code/src/riskprop/stage_i_mechanism.py)联合表仅保留八列，丢弃传入表的其他关联字段，不能无损承载本契约。本任务不改变旧schema。

参见[完整审计及后续建议](P3_TASK1_FINAL_REPORT.md)。
