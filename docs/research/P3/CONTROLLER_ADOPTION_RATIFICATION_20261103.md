# Controller Adoption Ratification Amendment

Task ID: `AAD-P7-TASK2-20261103`；日期：2026-11-03。
版本：`aad.p3.policy-input-adoption.agreed.v1`；状态：`AGREED`。

研究者明确批准：**有效消息实际纳入某次具体策略决策的输入，并有可追溯消费回执和对应 decision_id，即认定为 Adoption**。接收、验证、入队、缓存、过滤器读取及拒绝均不等于 Adoption。决策不变或不产生新命令，不抹去已经发生的消费。不得由动作差异反推采用。

每次纳入保留 message_id、payload_hash、input receipt_id、controller_instance_id、decision_id、policy_version、input_snapshot_hash、消费时间、simulation_step、phase、边界版本和 AGREED 状态。多消息/多决策关系仍由 P3 v1 schema 表达；本修订不改变字段结构。

历史 [P3-CA-v0.1 Proposed 契约](CONTROLLER_ADOPTION_CONTRACT.md) 及 `aad.p3.policy-input-adoption.proposed.v0.1 / PROPOSED` 原记录保留。双版本读取不得修改历史字节或把 Proposed 记录升级；新 P7 消费明确使用本版本。P3 历史合成构造器仅显式选择 legacy 边界以保持原语义。

本修订批准操作边界，不认证合成源的 Formal 资格，不证明 Adoption-induced Action/Risk Effect。正式消息资格总体、TTL、P5 随机化和 P4 阈值仍待研究者；不修改统一定义 v0.4 / 27 项，也不改变四格、P1 ITT、Gate 或 Stage1.1。

依据：[P7 八项研究者决策](../P7/P7_RESEARCHER_DECISIONS_20261103.md)。
