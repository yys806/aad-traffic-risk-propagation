# P7 消息驱动纵向控制器工程规格

Task ID：AAD-P7-TASK2-20261103；2026-11-03。状态：Implemented / SUMO acceptance blocked。研究方向见 [D1–D8](P7_RESEARCHER_DECISIONS_20261103.md)，数值和具体策略仍 ENGINEERING_CANDIDATE_NOT_FORMAL。

## 架构及控制权

SUMO Krauss/local state → receiver/validator → input gate → longitudinal_policy → target_speed_reference_mps → vehicle.setMaxSpeed → simulationStep → actual readback。

SUMO 始终负责原生跟驰、速度演化、加减速和前车交互。策略纯函数不调用 TraCI、不生成实际加速度、不读取未来轨迹。只有 MessageController 命令适配器对目标车调用 setMaxSpeed，无第二个 setter 争夺控制权；不新增换道、路径规划、RL 或独立 Safety Layer。

无有效消息或 Disabled 时输出 None/NATIVE_FOLLOWING。此前有消息上限时，None 触发恢复初始化保存的单车原始最大速度；否则不发命令。相同参考值可重复消费消息而不发新命令。

实现：[策略](../../../code/src/riskprop/message_driven_longitudinal_controller.py)、[运行时](../../../code/src/riskprop/p7_message_runtime.py)、[SUMO 入口](../../../code/scripts/run_p7_task2_engineering.py)。Stage0.1 固定时程、Stage0.5 replay/native Follower、Task16、Task20 不改；只复用原网络构建函数，不调用 Stage0.1 _run_cell。

## Payload 与单跳传输

版本 aad.p7.risk-payload.engineering.v1；字段：payload_schema_version、parameter_status、source_event_id、event_type、risk_level、affected_edge_id、lane_position_min/max_m、target_vehicle_ids、generated_time、valid_from、valid_until。

event_type 仅 SYNTHETIC_REMOTE_RISK；LOW/MEDIUM/HIGH 是独立工程测试枚举，不代表 Formal P2 事件资格。空间范围仅工程适用范围，不是正式 Region/Cohort/Window。消息不含加速度命令、未来真实轨迹；额外字段、重复 JSON key、非有限值、错误版本/hash/source/target 均拒绝。保存原始 UTF-8 bytes 和 SHA256。

时效为 [valid_from, valid_until)。每次决策重新验证缓存消息，过期、尚未有效、不适用、无效消息不得进入策略。有效期是生成时已知的配置值；当前实现的 DECLARED_VALIDITY_END 以生成时刻为 observed_at/available_at，不假称观察到未来。历史 v1 capture 的附属 expiry observed_at 元数据保留原值，只按声明的配置区间解释，不作未来实际观测。

进程内单跳 transport 明确 sender/receiver、独立 attempt、receiver delivery 和 validator receipt，支持 FAILED/UNKNOWN/CONFIRMED_FAILURE。它是 SUMO 模型内部通信机制，不是无线链路；未冻结 delay/loss/coverage、TTL 或消息资格总体。

## 可解释策略与版本

输入包括实际速度/加速度、位置/edge/lane、原单车最大速度、lane speed limit、可观察 leader speed/net gap，以及门控后有效消息。

工程基础参考 b=min(original_vehicle_max, lane_max, leader_speed+net_gap/headway_reference)；无前车时省略最后一项。desired=b*min(risk_speed_factor)。同一本地状态下更高风险不产生更高参考；多消息取最严格 factor。这是局部参考规则，不是独立安全算法或认证。

v1 factor=0.9/0.7/0.5、headway=1 s；三条件烟测中 Enabled 上限突降至10 m/s时出现 emergency braking，v1 不获验收。当前 SUMO 入口拒绝没有参考值变化约束的 v1 配置。

修正 v1.1/v2：target=min(original_vehicle_max, lane_max, max(desired, current_speed-reference_deceleration*step_s))。工程配置 reference_deceleration=1.0 m/s²、step_s=0.1 s；仅约束策略参考值下降幅度，不直接施加加速度、不伪造 actual acceleration，不产生 safety record。对同状态仍单调。此修正仅离线单元验证，未重跑 SUMO，不能声明已消除异常或通过验收。

参数原件：[v1 历史候选](../../../code/configs/p7_task2_engineering_candidate_v1.json)、[v2 当前候选](../../../code/configs/p7_task2_engineering_candidate_v2.json)。所有数值均有独立 config/policy 版本和来源，标记 ENGINEERING_CANDIDATE_NOT_FORMAL；无搜索、优化、seed sweep 或正式 config 写入。

## Adoption 门控

每运行显式提供 adoption_mode、assignment_id、adoption_mode_source/version，缺失 fail-closed。冻结 dataclass 与逐周期一致性检查拒绝运行中模式/assignment 改变；无随机化器或默认 Enabled。

两组使用同一 receiver/validator。Disabled 在策略输入组装处移除风险消息，snapshot.messages=[]；有效消息仍有 AVAILABLE input、REJECTED/ADOPTION_DISABLED consumption，关联实际 decision。Enabled 只对真正传入策略的有效消息产生 POLICY_INPUT_INCLUDED。失败/不变/零新命令不抹去消费。见 [Agreed Amendment](../P3/CONTROLLER_ADOPTION_RATIFICATION_20261103.md)。

## SUMO 1.26.0 与 API

选择单车 vehicle.setMaxSpeed，保持原生 speedMode=31，不使用 setSpeed、setAcceleration、setSpeedMode、moveTo 驱动目标轨迹。maxSpeed 是单车参数，不是每步强制速度；API 返回/getMaxSpeed 不等于实际动作。

官方 v1_26_0 Change_Vehicle_State、_vehicle.py、_vehicletype.py 的 URL/hash 见 [来源清单](../../../evidence/research/P7_TASK2_20261103/official_sumo_api_sources.json)。setSpeed(-1) 是 setSpeed 覆盖的释放方式；本实现未使用此覆盖。setMaxSpeed 无对应 -1 释放语义，须写回原单车上限。speedMode 检查不保证 maxSpeed 突降仅使用常规减速度，v1 真实异常证明其限制。

原生参与事实：route XML 为 Krauss、speedMode 始终31、实际速度与 getSpeedWithoutTraCI 一致、有前车且实际速度低于单车上限；无强制轨迹 setter。以上不覆盖全部交通域的安全性，也不能让异常烟测获通过。

## 执行、生命周期和停止

pre-step 决策/命令 → simulationStep → post-step actual state。原始动作含 time/step/vehicle/incarnation、edge/lane、x/y/lane position、speed/acceleration、leader/gap、existence/readback status、native speed/max/mode。目标实际进入后创建 entry1；实际 arrived 确认退出，之后不再决策；重新出现报错，缺状态不补零。

一 command 跨多步 execution；新命令 raw replaces_command_id 与 command_tenures 显式记录替代/结束。P3 command 保存 issue/ack 时快照，不回写旧事实。提前终止使用 RIGHT_CENSORED，不假称未执行。

当前入口新增 collision/teleport/emergency getter、实际异常减速度及日志检查，停止前尽可能保留该步读回。v1 原入口漏检 warning，直到运行结束后发现；保留这一事实，不伪称即时停止。发现后新增 SUMO=0。
