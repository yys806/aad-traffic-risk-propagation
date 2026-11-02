# Controller Adoption Contract

Task：AAD-P3-TASK1-20261102。版本：P3-CA-v0.1。状态：**Proposed / Awaiting Researcher Ratification**。本契约只提出证据接口，不批准新策略、通信模型、采用实验、参数或科学定义。遵循[统一定义](../definitions/README.md)和[P1估计对象](../P1/ESTIMAND_SPECIFICATION.md)；不新增Definition ID。

## 1. 三个层级

| 层级 | 要证明的事实 | 充分性边界 |
|---|---|---|
| Message Validated | 接收端已对指定消息、目标及有效期执行规定检查 | transport ACK、validated=True均不能替代实际检查记录 |
| Controller Adopted | 特定版本控制器在特定决策实例中消费了该有效消息作为指定策略输入 | 日志可证明消费；不要求动作一定改变，不证明消息产生因果效应 |
| Adoption-induced Action Effect | 对采用机制的适当干预造成实际动作差异 | 必须依靠P5机制实验、随机化及适用识别假设；消费日志、时序或配对轨迹差异单独不足 |

建议采用边界是“有效消息被纳入本次决策的策略输入并留下消费凭证”，而非网络接收、入队、反序列化或仅被拒绝过滤器读取。considered/rejected、queued、cached、consumed分别记；缓存消息重复消费须逐决策登记。**该更细操作边界仍需研究者确认，不能反向改写历史adopted。**

## 2. 推荐证据记录

| 记录 | 必须能回答的字段/问题 | 产生者 |
|---|---|---|
| Controller instance | controller_id、instance_id、controller_version/code_hash、policy_version/config_hash、受控车辆incarnation、运行/随机化块 | 初始化与策略装载记录；theory_version不替代controller_version |
| Input receipt | receipt_id、message_id/载荷hash、validation_id、接收/入队/可用时间、controller instance、输入schema、input_state_snapshot_ref | 控制器边界，不能由发送端回填 |
| Consumption/adoption receipt | receipt_id、decision_id、实际读取且纳入策略的message引用集合、input_snapshot_hash、消费时间/phase、used/considered/rejected及原因 | 策略执行路径；不能由事后轨迹差异反推 |
| Decision | decision_id、controller/policy版本、状态与消息输入引用、decision time、output/control intent、no-change/failed状态 | 真正执行的策略实例；不只存策略名称 |
| Command | command_id、decision_id、车辆、API/执行接口、输出值/单位/有效区间、issue/ack时间、拒绝/覆盖/取消状态 | 调度器及实际API调用点；call returned不证明执行动作 |
| Safety intervention | intervention_id、command_id、约束版本、before/after command、reason、执行先后、可观测状态 | 安全层；未知时不得默认False |
| Execution | execution_id、command_id、受控车辆incarnation、ack/status、actual execution interval、实测v/a/x、native/安全约束与readback引用 | 执行器与独立状态记录；执行完成及未知必须分开 |
| Risk attachment | risk_observation_id、原状态数据hash、Formal测量版本、固定Region/Cohort/Window、观察/可用时间、质量状态 | P4只读测量；risk-effect onset不由该行产生 |

同一decision可能输出零个或多个command；一个command可能跨多步执行、被新命令替代或被安全层截断。关系应显式表示，不能强行一消息一动作。Actual Action的实测与“该命令对动作的因果贡献”也不同；共时的native跟驰或安全层影响须保留。

## 3. 无动作、安全覆盖和失败

必须能区分：有效消息未采用；已采用但决策保持不变；决策改变但未发命令；命令被拒绝；安全层修改命令；命令确认但执行状态未知；执行动作发生但未检出相对对照差异；车辆退出/失踪；动作变化来源不明。

安全覆盖不抹去已发生的消费事实，也不从ITT删除。无动作差异只能在预先定义的比较对象、时间支持、质量与阈值下判断；本任务不冻结这些参数。控制器输出与实际加速度不同不自动证明安全覆盖；两者相同也不能替代安全层审计。

## 4. 时间和身份

沿用[消息时间契约](MESSAGE_LIFECYCLE_CONTRACT.md)：原时钟、映射、误差、phase、available_at、允许区间必须保留。decision、command、execution分别有实际时间；不将计划控制周期当成执行时间。命令在step前下发、step后读取状态时，两者时间支持应如实保存，不能人为加极小量排序。

联合轴通过run/instance/incarnation和message→receipt→decision→command→execution的引用构造；风险另由相同预定空间时间支持关联，不因“时间更晚”而宣称是该命令造成的风险。多run/多消息应分别审计，不能全表取最早message与最早action拼成一条路径。

风险观察时间、风险状态onset、总体因果风险效应T_R、实际动作候选T_U、物理到达T_P及其误差分别保存。没有独立P2支持时，信息/动作/风险先于物理到达的结论仍Unknown。

## 5. Adoption Enabled/Disabled的因果边界

继承P1：完整assignment-level ITT包含送达、采用和安全失败；不得按实际adopted筛选主分析。四格Source×Channel识别对象与采用机制的因果效应不同。

推荐后续由研究者审查一项有界机制对照：在机制试验预先定义且在Z_A之前确定的消息资格总体中，随机分配采用Enabled/Disabled，消息载荷、交付/验证、其他控制模式与初态保持可审计一致。此资格子总体的结果不自动代表主ITT总体；不能在随机化后剔除无动作、安全覆盖或消费失败。

这首先识别采用开关/鼓励分配的reduced form。若进一步称为实际采用的IV/LATE，仍须审查相关性、排除限制、单调性、正支持及网络干扰。Disabled是否改变其他策略分支是实质性科研问题；日志不能证明排除限制。本任务不执行该实验，也不默认其条件成立。

## 6. 当前能力与推荐改动位置

| 文件 | 已有能力 | 拟议改动（未实施） |
|---|---|---|
| formal_design.py L138–237 | 生命周期逻辑一致性 | 独立receipt/decision/command关联验证；显式Unknown；不要直接破坏历史boolean契约 |
| formal_artifacts.py L113–149、213–240 | protocol/action列与Parquet schema检查；manifest字节校验 | 版本化关联表、receipt数据、事件级外键和内容验证；保留旧schema读回 |
| stage_i_mechanism.py L29–38、152–208 | 八列事件轴、动作轨迹差异及Unknown物理到达 | 保留消息/决策/命令/执行ID与时间包络；按run/链审计；风险观察与效应起点分开 |
| formal_runner.py L132–169、306–321 | 合成生命周期和动作表 | 可复用为有标签的兼容fixture，不能将硬编码adopted或applied值当controller receipt |
| stage_0_1_sumo.py L247–256、287–324 | 工程烟测中调用setAcceleration并读实际加速度 | 下一次授权集成须记录实际控制路径/消费/命令回执；当前adopted_time按时程赋值，safety_intervened=False为写定值 |

上述改动会增加数据接口并可能影响采用的操作语义，需在契约获接受及单独工程授权后实施。本任务没有修改上述文件。

## 7. 最小后续验收（待授权）

不再扩展当前Task20七事件fixture来声称闭环。优先一次有界接口实现与最小合成契约验证：正常消费、验证后拒绝、采用无动作、安全覆盖、孤儿/跨run引用、重复过期、同step不同phase、未知时钟/缺状态。只验证记录和关联，不评估H1–H4，不启动SUMO。

这些接口验证完成后可直接交P7接线；实际自动控制器策略、采用边界、Enabled/Disabled设计及通信模型参数须经研究者确认。生产端到端试运行、先导及正式验证分别授权，不自动串行启动。
