# Communication Assumptions and Evidence Register

Task：AAD-P3-TASK1-20261102。版本：P3-COM-v0.1。状态：**Proposed登记 / 不冻结数值**。只复用内部既有证据，不开展新通信文献调查、下载或原始通信数据复核。

## 1. 来源类别

| 类别 | 使用含义 |
|---|---|
| Measured | 实际记录直接测量；必须同时说明记录对象、分母、时钟和适用域，不能自动解释成潜在真实量 |
| Documented | 官方资料明确记录的定义/配置；本任务引用的是项目既有核查，未重新在线复核 |
| Controlled-Test Reference | 受控通信试验的有限参考，不代表自然交通校准 |
| Literature Prior | 文献先验/范围，须说明研究对象与AAD差异；不能写成AAD实测 |
| Engineering Assumption | 为使工程模型可执行而提出的假设，不是经验证的环境事实 |
| Sensitivity Only | 仅用于将来预先规划的敏感性，不得按主效应选择有利值 |
| Unknown | 当前证据不足以识别目标量；不能以默认值或fixture填补 |

同一参数可有多种来源，但每一具体数值记录只绑定自己的来源、版本、分母、时钟及域。历史数值不在本表升级为正式参数。通信Availability与Controller Adoption分别登记。

## 2. 参数—证据—限制

| 参数 | 现有证据与类别 | 当前可支持的对象 | 不可支持/仍Unknown | 后续使用边界 |
|---|---|---|---|---|
| Communication Latency | SEE-V2X记录时延及tx/rx差值的一致性：Measured（日志量）/Controlled-Test Reference；Bristol仅历史Documented候选 | 已登记受控样本的记录时延、单位及有限相对排序 | SPMD无完整车辆侧接收时钟；SEE绝对时延/跨设备同步；Bristol创建时刻不当接收时刻 | 不冻结自然交通时延分布；工程设定须标Engineering Assumption/Sensitivity Only |
| Packet Delivery / Loss | SEE消息身份配对及完整运行日志接收比例：Measured/Controlled-Test Reference | 已记录发送分母下的描述性接收比例 | 接收机会、无线模块全程在线、真实链路PDR/PER；RV_RX间断不等于Packet Loss | 发送/接收完整性及无线接收机会未证时，不给真实丢包率 |
| Message Duplication | 现有message_id/seq关联方法可复用；AAD端到端重复处理缺证 | 未来可区分同消息重试、重复接收、重复消费 | AAD重复概率与处理语义Unknown | 去重键/缓存/重传规则先登记；不由重复行直接估网络重复率 |
| Message Reordering | 标量时间顺序检查已实现；不是乱序观测 | 可对有完整sequence及匹配身份的记录定义乱序审计 | 当前没有AAD乱序分布或处理证据 | 序号回绕、重传与时钟误差先区分；未来Sensitivity Only |
| Message Expiration | freshness_valid/message_age_s字段已有；TTL执行与规则未证 | 工程字段一致性检查 | 不存在已冻结的有效期/过期率；age相等不证明freshness检查 | TTL规则/时钟/decision可用时间需批准，不能填任意数值 |
| Channel Capacity | SEE受控配置有Documented/Measured应用负载参考 | 原试验的包大小、发送模式与记录速率 | 应用频率不是信道容量；AAD容量、拥塞和队列模型Unknown | 不以受控应用速率冻结自然交通容量 |
| Communication Availability | SPMD RV_RX仅receive-state continuity（Measured）；SEE GNSS有限记录 | 已登记接收状态连续性，不重新读holdout | 无线在线、可达范围、真实接收机会；GNSS覆盖不证明radio在线 | topology候选与实际可用性分开；缺证Unknown |
| Message Adoption | Stage I及formal_runner合成赋值：Engineering Assumption；THEA/WYDOT行为结果仅历史Literature Prior/Documented描述 | fixture逻辑、自控器契约设计参考 | 自然自动控制器消费概率/机制；驾驶员响应不能替代自动控制器采用 | 不冻结采用率；需controller receipt，因果效应另需P5设计 |

## 3. 必须继承的纠错链

最晚的[Stage0.4有限验收](../../STAGE_0_4_LIMITED_SCIENTIFIC_ACCEPTANCE_2026-10-17.md)及[0.4.7.2修正](../../STAGE_0_4_TASK_0_4_7_2_GNSS_VALIDITY_REPAIR.md)优先于[早期0.4.4调查](../../STAGE_0_4_TASK_0_4_4_COMMUNICATION_EVIDENCE_SEARCH.md)摘要。本任务没有重开已收口的Stage0.4。

- Bristol：0.4.4早期“可算绝对时延”的说法已被0.4.5纠正，Timestamp是创建时刻，未有跨设备同步精度证据；仅PDR/RSSI方法候选，不在此认定已实测校准。
- SEE-V2X：消息关联和日志接收比例保持既有事实；(rx−tx)/1000与latency数值一致，不证明绝对端到端时延已校准。早期0.4.6.2对时钟/运行差异的过强解释不得恢复；0.4.7.2保留绝对时延及同步Unverified。
- SEE-V2X：三设备GNSS逐点复制、RSU静态、室内无有效GNSS，不能构造可信距离—PDR/时延关系；GNSS覆盖不证明接收机在线。
- SPMD RV_RX：接收远车状态行不是消息发送/接收逐包清单；间断≠丢包；不能估controller adoption。现有Packet访问失败是历史可达性记录，不等同schema不合格。本任务不读取通信原始数据或locked holdout。
- THEA/WYDOT：0.4.4的站点与响应比例曾纠正；本任务不重新传播早期混淆数值。驾驶员对告警减速不是自动控制器消息消费，也不单独证明告警因果作用。
- Stage0.4整体pass_limited为既有有限可观测性验收，不等于自然交通V2V参数或采用机制校准。

## 4. 未来数值登记的最小字段（未填值）

参数名/单位、来源类别、数据或文献版本/hash、测量对象、发送分母、接收机会、独立单位/依赖块、消息身份键、时钟/误差、交通与通信环境、采样/缺失/删失、估计方法/区间、拟议用途、不可外推范围、研究者接受状态及敏感性设置。

对延迟仅成功接收者可观测的选择、对消息丢失的未知分母、对重复/乱序的日志完整性、对采用的处理后选择应分别说明。本任务不补任何未知参数为零，不将fixture的固定时差作为通信校准。

## 5. 与当前源码的关系

[communication_observability.py](../../../code/src/riskprop/communication_observability.py) L78–173、192–227限制为接收状态连续性，明确packet_loss_estimated/latency_estimated/adoption_inferred=False。其字段门和split纪律可复用；P3不调用RV_RX profiler读取真实数据。

[生命周期契约](MESSAGE_LIFECYCLE_CONTRACT.md)和[采用契约](CONTROLLER_ADOPTION_CONTRACT.md)给后续日志需求；[Task1报告](P3_TASK1_FINAL_REPORT.md)给实施优先级。没有新通信参数、实际采用证据或科学Gate升级。
