# P3 控制器证据接口实现与P7接入说明

Task ID：AAD-P3-TASK2-20261103；日期：2026-11-03。状态：Implemented / Synthetic Contract Verified；尚未接入真实控制器。统一科研定义仍为[27项v0.4](../definitions/README.md)。

## 1. 独立版本与兼容边界

[controller_evidence.py](../../../code/src/riskprop/controller_evidence.py)仅依赖Python标准库，提供独立JSON sidecar，schema_version为 aad.p3.controller-evidence.v1。候选采用边界为 aad.p3.policy-input-adoption.proposed.v0.1，状态固定PROPOSED。schema_description()输出字段/枚举清单，不是标准JSON Schema，也不是Formal artifact schema升级。

旧formal_design生命周期、Formal Parquet schema、stage_i_mechanism八列时间轴和Task20 fixture均未改。不要把新记录送进旧八列投影而丢弃外键；P7应保留sidecar并显式引用。legacy_protocol_observation()只产生HISTORICAL_FIELD_ONLY注释，保留原值，consumption_receipts_created=0；历史adopted=True不能迁移为新凭证。

整个bundle和验证结果的scientific_claim_eligible固定为false；这表示本接口验证不授予科研结论资格。fixture_only由生产者显式声明，合成场景全部为true，不能把false本身当成真实证据认证。

## 2. 公共封装与身份

每条记录由schema_version、kind、context、time、data组成。EventContext含record_id、run_id、pair_id、block_id（可空）、cell_id、source_event_id（可空）、message_id（可空）、vehicle_id、vehicle_incarnation_id、producer_id、producer_role、evidence_ref、fixture_only，以及中立的assignment_id、adoption_mode/source/version。

record_id全局唯一；各类natural ID在各自kind内唯一，message_id、decision_id、command_id、execution_id含义独立。控制器实例与策略版本、理论模型版本分开。跨run、pair/cell/block/assignment、车辆生命周期的错误关联报错；消息广播的发送者和接收者可以不同，控制器/决策/命令/执行仍须匹配对应接收车辆。fixture与非fixture不能合并成同一条证据边。

producer_role约束用于要求输入回执来自controller_input、消费/决策来自policy、安全来自safety_layer、执行来自execution_reader。这是来源声明和溯源接口，不能鉴定日志真实性，也不能阻止外部调用者伪造producer_id。P7必须在真实接收/策略执行边界调用并绑定实际日志。

## 3. 记录类型与字段映射

完整机器可读字段和状态在[独立schema库存](../../../evidence/research/P3_TASK2_20261103/schema.json)。下表列核心body字段；通用身份和时间不再重复。

| kind | 独立ID与核心内容 | record.time的语义名 |
|---|---|---|
| source | source_event_id；source_type、qualification_status、confirmation_ref | confirmation_time |
| message | message_id；sender_id、payload_hash/type/ref、message_kind、valid_from/until、validity_rule_ref | generated_time |
| send | attempt_id；send_status、transport_ref；每次发送独立记录 | sent_time |
| delivery | delivery_id；attempt_id、delivery_status；接收端记录 | delivered_time |
| validation | validation_id；delivery_id、validator_id/version、validation_status、reason | validation_time |
| controller | controller_instance_id；controller_id/version/code_hash、policy_version/config_hash、controlled_vehicle_id | registered_time |
| input | receipt_id；message_id/hash、validation_id、controller_instance_id、available_time、input_schema_version、input_snapshot_ref、input_status | received_time |
| consumption | consumption_receipt_id；input_receipt_id、message_id/hash、controller_instance_id、decision_id、policy_version、input_snapshot_hash、consumption_status、reason、边界版本/状态 | consumption_time |
| decision | decision_id；controller_instance_id、policy_version、input_snapshot_hash、consumed_message_refs、decision_status/output_ref、control_intent、no_change_reason、command_disposition | decision_time |
| command | command_id；decision_id、controller_instance_id、target_vehicle_id、command_type/value/unit、valid_from/until、command_status、execution_interface_ref、ack_time、failure_reason、execution_disposition、可选superseded_by | issue_time |
| safety | intervention_id；command_id、safety_layer_id/version、constraint_version、original/modified_command、intervention_status/reason、可选previous_intervention_id | intervention_time |
| execution | execution_id；command_id、target_vehicle_id、execution_end/status、actual_acceleration/speed/position、state_readback_ref、execution_reason、safety_intervention_refs | execution_start |
| action_observation | action_observation_id；execution_refs、comparison_ref、action_change_status、observation_ref | observation_time |
| risk_observation | risk_observation_id；action_observation_refs、measurement_version、observation_ref、risk_status | observation_time |

主事件时间统一存于record.time，表中语义名是别名，不是重复顶层字段。附属available_time、valid_from/until、ack_time、execution_end也是完整TimeEvidence对象或显式null。

## 4. 输入、消费与候选采用

input_status区分RECEIVED、QUEUED、AVAILABLE、NOT_RECEIVED、UNKNOWN、RIGHT_CENSORED。AVAILABLE要求引用有效的验证记录；实际可用时间单独保留，未测得则Unknown。

consumption_status区分RECEIVED、CONSIDERED、REJECTED、POLICY_INPUT_INCLUDED、UNKNOWN。缓存、过滤器、反序列化只能按实情记录前三者，不生成虚假的POLICY_INPUT_INCLUDED。未观察到消费回执产生MISSING_CONSUMPTION_OBSERVATION，不能推出永远未采用。

POLICY_INPUT_INCLUDED要求输入AVAILABLE，关联同一controller、policy_version、input_snapshot_hash的具体decision_id，并由decision.consumed_message_refs反向引用。recorded_policy_input_receipts保留生产者声称的纳入事实；candidate_policy_input_receipts进一步要求payload/snapshot/controller代码/策略配置hash和输入snapshot引用等关键证据齐全。缺失时保留记录并产生UNKNOWN_POLICY_INPUT_EVIDENCE，不补hash。

候选清单仅指版本化Proposed策略输入边界，**不是正式Adopted科学定义、真实消息作用或独立采用证明**。时间映射缺失/重叠另外报告Unknown；候选清单不能充当完整时间资格或因果认证。哈希由生产者提供，验证器核验格式、关联和一致性；外部payload/snapshot文件的字节真实性由P7的manifest/hash绑定负责。

## 5. 关联、决策、命令和安全

显式图为Source→Message→Send/Delivery/Validation→Input→Consumption→Decision→Command→Safety/Execution；Execution→Action Observation→Risk Observation。验证输出edges保留record_id及关系，timeline保留完整字段和记录顺序，不通过临近时间戳补链。

decision.consumed_message_refs是message_id与consumption_receipt_id对的列表，支持一决策多消息、同消息多周期消费。command通过decision_id支持一决策零/多命令；execution通过command_id支持多执行区间；safety通过command_id及previous_intervention_id支持多次处理。决策与命令/执行中的可选message别名必须属于相应决策消费清单。

command_disposition和execution_disposition显式区分EXPECTED、NONE、UNKNOWN、RIGHT_CENSORED。预期子记录缺失产生Missing Command/Execution Unknown；显式悬空外键是结构错误。UNCHANGED决策可消费消息但零命令，FAILED决策不得发出命令。命令状态区分CREATED、ISSUED、ACKNOWLEDGED、REJECTED、CANCELLED、SUPERSEDED、UNKNOWN。

safety状态为NOT_OBSERVED、CONFIRMED_NONE、MODIFIED、REJECTED、UNKNOWN；无记录不能默认False。修改保留原命令/修改后命令及前一干预引用；安全层不删除消费或决策。execution独立记录EXECUTED、PARTIAL、NOT_EXECUTED、MODIFIED_EXECUTED、UNKNOWN、VEHICLE_EXITED、UNOBSERVABLE、RIGHT_CENSORED。实际状态读回缺失仍保留MISSING_STATE_READBACK；接口声明执行与读回证据是否齐全分别报告。

实际加速度不等于命令值，差异本身不证明安全介入。动作comparison_ref由P4提供，本模块不冻结动作差异阈值、不推反事实效应；风险measurement_version只引用既有测量，不重算Formal rho/P2。

## 6. 时间与结构异常

TimeEvidence保留native_timestamp、clock_id、time_unit、simulation_step、phase、sequence、time_lower/upper、reference_clock_id、clock_mapping_version、observed_at、available_at、reason。native时间使用time_unit；映射区间、observed_at、available_at按参考时钟秒。未知时钟/映射/区间不填零。

compare_times仅在共同映射且U_left < L_right时返回BEFORE。同一clock/step/native timestamp下，phase及明确sequence可给CALL_ORDER；phase名没有隐含排序，CALL_ORDER不是严格物理时刻证书。区间重叠为OVERLAP，无映射为UNKNOWN，不添加epsilon。右删失和车辆退出不是永久未执行。

明确错误通过EvidenceError(code, detail)抛出：ORPHAN_REFERENCE、CROSS_RUN_REFERENCE、CROSS_VEHICLE_REFERENCE、DUPLICATE_ID、CONFLICTING_PAYLOAD_HASH、INVALID_STATE_TRANSITION、MISSING_DECISION、MISSING_COMMAND、INVALID_TIME_INTERVAL等。UNKNOWN_TIMESTAMP、UNKNOWN_TEMPORAL_ORDER、MISSING_EXECUTION等不可确认事实进入issues，status=UNKNOWN。多对多有向关系另检查环，未知时钟不能隐藏结构环。

## 7. P7直接复用方式

~~~python
from riskprop.controller_evidence import EvidenceJournal, EventContext, TimeEvidence
journal = EvidenceJournal()
# 在真实producer边界构造context/time和对应body；不根据旧adopted值补写。
# journal.append(kind, context, time, **body)
audit = journal.validate()
# journal.write(Path(new_sidecar_path))  # 先验证、独占创建，不覆盖旧输出
~~~

P7需接六个真实插入点：接收端/验证后输入边界、策略实际组装输入与决策执行路径、命令API、实际安全层、simulationStep后状态读回、P4动作/风险观测引用。Source/Message/发送/接收另绑定已有身份与日志。先生成具体decision_id再引用；消费与决策可前向引用，在完整capture的validate时解析。

append只检查单记录，跨记录完整性由validate检查；write在完整性检查后独占创建。记录为不可覆盖的capture快照，不是自动状态机执行器；需要保存状态变迁时P7应保留原始producer日志/独立命令或执行记录，不用重复natural ID覆盖旧事实。records返回深拷贝；完全相同record_id的幂等重放须显式idempotent=True，冲突仍报错。

adoption_mode/source/version仅存元数据；本模块不决定Enabled/Disabled的通路、资格总体或随机化。assignment-level ITT仍保留送达失败、未采用、安全修改、无动作结果，不能按候选采用筛样本。

本任务未提供真实adapter、SUMO运行、通信校准或机制实验。P7接线/先导仍需各自授权；采用边界、P5开关定义与随机化、P4动作比较和时间误差资格仍由研究者决定。

## 8. 可复现验证入口

~~~powershell
python -X utf8 -m pytest code/tests/test_controller_evidence.py -q
python -X utf8 code/scripts/run_p3_task2_controller_evidence_fixture.py --output <new-directory>
python -X utf8 evidence/research/P3_TASK2_20261103/verify_evidence.py --repo-root .
~~~

runner只构造确定性合成数据；数值/TTL均为fixture，不是冻结参数。[最终报告](P3_TASK2_FINAL_REPORT.md)记录A–H及失败保留口径；[便携证据](../../../evidence/research/P3_TASK2_20261103/README.md)保存schema、fixture、关联复算、测试摘要与hash。
