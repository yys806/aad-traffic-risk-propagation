# P7 控制器与 P3/P4 证据集成

Task ID：AAD-P7-TASK2-20261103；2026-11-03。实际路径已接线，整体 SUMO 验收被 v1 emergency braking 阻断。唯一事件 schema 为 aad.p3.controller-evidence.v1，不另建重复 Evidence Schema。

## 14 类实际 producer

| P3 kind / producer_role | 实际调用位置 | 适用处理 |
|---|---|---|
| source / source_observer | generate_synthetic_message 测试事件生成 | qualification=UNKNOWN；不是 Formal Qualified |
| message / message_generator | 原始 Payload 生成后 | bytes/ref/hash 与显式 source_event_id |
| send / sender | InProcessSingleHop.send | 独立 attempt；失败不回填 delivery |
| delivery / receiver | MessageController.receive | 接收端实际进程内回执，支持失败/Unknown |
| validation / validator | decide 调用 validate_message | 每周期校验 hash/version/time/target/space |
| controller / controller_registry | MessageController 初始化 | controller/policy/config/code hash、incarnation |
| input / controller_input | 验证后的消息输入边界 | VALID→AVAILABLE；其他已收消息 RECEIVED |
| consumption / policy | 实际 PolicyInput 调用边界 | Enabled included；Disabled rejected |
| decision / policy | 纯策略返回/失败处 | ID/snapshot/message refs、UNCHANGED/FAILED |
| command / command_interface | _issue 实际 setMaxSpeed 调用 | API参数/返回/getter、失败/释放/替代 |
| safety / safety_layer | 无独立 producer | 零记录，NOT_INCLUDED_BY_RESEARCHER_DECISION |
| execution / execution_reader | simulationStep 后 observe/read_state | command关联、实际状态、退出/未知/右删失 |
| action_observation / action_observer | post-step 连续观察 | 原始 trajectory/readback ref；无阈值冻结 |
| risk_observation / risk_observer | existing_measurement_attachment/risk_attachment | 既有 TTC/quality 状态引用；risk effect Unknown |

role 字符串不是认证。真实函数调用、producer_events 原日志、input/decision/command/readback 文件、代码/config/runtime hash 共同构成溯源。源事件仍合成测试事件，全部 fixture_only=true、scientific_claim_eligible=false。

## 关系与时间

source_event_id → message_id → attempt_id → delivery_id → validation_id → receipt_id → consumption_receipt_id → decision_id → command_id → execution_id → action_observation_id → risk_observation_id。

B/C Source/Message 标识及 Payload 原字节相同，run/assignment/incarnation 显式区分。逐周期 validation/input/consumption/decision 支持同消息多决策、一决策多消息、不变且零新命令。command 可跨多个 execution，raw 替代引用/tenure 记录实际结束。退出/右删失不补实际状态。

直接保留 SUMO native clock/time/step、phase 和全运行 sequence；identity mapping 仅针对仿真时钟，不认证墙钟/无线误差。同step INPUT_RECEIVED→AVAILABLE→POLICY_CALL_INPUT→DECISION→API_ISSUE/API_RETURN；动作在后续 step 读回。主事件不人为加 epsilon。有效期为声明配置时间，不当作未来实际观测。

P3 validator 检查 schema/role、外键、run/cell/pair/assignment、incarnation、hash、消费双向引用、decision-command/execution、时间和重复ID。P7 verifier 另复核全部外部 bytes、run mode 一致、Disabled snapshot 无消息、API值与真实 readback；结构通过不等于 Adoption-induced Effect。

## Sidecar 与 manifest

薄层 [p7_evidence_adapter.py](../../../code/src/riskprop/p7_evidence_adapter.py) 只包装 P3 Journal、身份/时间和独占原件；run 目录不覆盖。原件包括 controller_evidence.json、association_validation.json、producer_events.jsonl、payloads/validations/inputs/decisions/commands/readbacks、actual_trajectory.json、existing_measurement_states.csv、risk_observation.json、command_tenures.json、provenance.json、artifact_manifest.json。

provenance 记录 baseline SHA及dirty状态、source/config hash、SUMO 1.26.0 binary hash、TraCI import/bindings、network/routes/launch command、单一 seed、磁盘余量。v1 capture 的9个入口/直接依赖源码已独立保存并复核，不冒称完整传递依赖闭包。当前 runner 扩为已加载 riskprop 模块和依赖版本登记，尚未重跑 SUMO。

便携包含三条件完整 gzip sidecar/association audit、原始 run summary/config/provenance、全部文件hash、选定 Payload/snapshot 原字节、captured v1 源码包、轨迹摘要和测试结果。完整连续轨迹/原始大表/日志仅留本地。便携可复核完整 P3图及所选字节；全部外部字节复核需本机完整输出，不夸大便携范围。

## Agreed 与历史兼容

当前常量 aad.p3.policy-input-adoption.agreed.v1 / AGREED；见 [ratification](../P3/CONTROLLER_ADOPTION_RATIFICATION_20261103.md)。旧 Proposed pair 保留为 LEGACY 常量；header/receipt 必须是已知且相同的 pair。新 P7 Journal 显式选择 Agreed，旧直接调用按首个 receipt 保留原边界；from_dict 原样保留旧 header。

历史 fixture 源只增加显式 legacy 选择，旧输出/evidence/契约字节不改。P3字段结构仍v1；历史 adopted=True 注释适配器不改，不创建消费回执。

## P4 与 Unknown

Action 使用实际连续轨迹，不用参考值/API参数代替实际动作。描述比较仅 ENGINEERING_DIAGNOSTIC_ONLY，不冻结比较窗口/阈值。

风险只复用 Stage0.5 compute_sumo_measurements 的 per-state TTC/quality；不调用正式 event/rho/regional aggregation，不指定正式 Region/Cohort/Window。v1 capture 引用既有 Formal version，但缺少正式适用范围、风险效应 Unknown；当前适配器使用自身 reference version，单列 existing Formal version，避免误当完整 Formal 输出。Formal rho/P2 源码、参数/config不改。

无 Safety producer 不造记录，不把 Krauss、speedMode、参考值变化约束称为独立安全干预。audit保留 UNKNOWN_SAFETY，与设计不包含分别登记。退出、缺读回、右删失、源资格、物理到达和风险因果效应均保留 Unknown。

## 复核入口

python -X utf8 evidence/research/P7_TASK2_20261103/verify_evidence.py --repo-root .

加 --local-output code/outputs/engineering/p7_task2_20261103_v1 可复核全部本地外部字节、captured source、真实轨迹/日志的独立 acceptance audit；不启动 SUMO。

v1 Enabled 完整关联有效，但异常制动拒绝工程验收；原 run_summary PASS 保留，派生 acceptance=BLOCKED_ABNORMAL_BRAKING，不篡改原件。
