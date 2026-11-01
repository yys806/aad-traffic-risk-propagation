# P0 Task 2：推荐研究设计

状态：**Proposal；不授权本文件中的新实验**。

## 1. 最小可行设计

### 研究单位

源事件 × 预先定义的道路区段—时间簇；目标车辆 cohort 在 assignment 前确定。分析单位为车辆—窗口，但方差按事件/簇聚类。

### 处理和对照

- A=1：message availability/strategy πmsg；
- A=0：同源 no-message strategy π0；
- 随机化在消息生成前完成；
- 不把 delivery 或 adoption 作为首要处理。

### 必须记录的链

源事件 → assignment → generation → transmission → delivery → verification → adoption/rejection → command → observed action → individual risk → regional risk。

每个节点都要允许失败、Unknown 和 Invalid；失败记录本身是结果的一部分。

### 目标 estimand

首要 estimand 是固定 R/C/W 下的 ITT/policy effect。次级结果是消息链 coverage、Tdelivery/Tverification/Taction 与 observed Tphys 的删失分布。

### 双暴露映射

在实验前锁定：

- message exposure：直接收到、邻域收到、多跳收到和时间衰减；
- physical exposure：leader/follower、空间邻域、扰动到达和交通状态；
- network cluster：道路区段、方向、时间或组合；
- 映射版本和跨簇泄漏判定。

### 关键设计检查

1. 同源事件在 message 和 no-message arm 可比；
2. assignment probability 已知且为正；
3. 目标 cohort 不由处理后状态定义；
4. 时钟偏差有校准和上界；
5. 物理 witness 具有明确独立性依据；
6. 区域结果的有效 vehicle-time 和缺失边界可审计；
7. 结果窗口、风险指标和阈值在查看结果前固定。

## 2. 扩展设计

若研究者希望识别 Adoption/mediation，可在道路簇内增加随机鼓励 Z：

- Z 改变消息提示、冗余或可用性，但不直接改变动作；
- 记录 Z→delivery→verification→adoption；
- 评估 relevance、independence、exclusion、monotonicity 和网络版本的 spillover；
- 使用按参与者/事件/簇聚类的不确定性；
- 采用 interventional mediation，不把自然直接/间接效应作为默认。

若跨簇消息/物理传播不可避免，放弃 partial interference 的强表述，改估计全网络 policy effect，并把 exposure mapping 当作主要敏感性对象。

## 3. 现实数据与 SUMO 的分工

| 目标 | 现实/实验数据 | SUMO |
|---|---|---|
| 消息生命周期 | 必须由真实日志提供 | 可先验证字段和状态机 |
| 采用与动作 | 必须有 controller/vehicle log | 可验证机制闭环 |
| 物理 arrival | 同源 no-message witness 优先 | 可生成结构 counterfactual |
| 区域 risk | 真实轨迹和固定指标 | 只能作为机制和代码测试 |
| 普遍性 | 需要独立场景/数据 | 不能替代现实证据 |

SUMO no-message 结果不能自动称作现实独立物理真值；当前项目保持 scientific_claim_eligible=false。

## 4. 估计和报告顺序

1. 数据完整性、身份和时钟审计；
2. assignment balance 和跨簇泄漏审计；
3. 消息链覆盖率与失败模式；
4. ITT/policy effect；
5. physical arrival 与 information arrival 的删失/区间分布；
6. exposure-specific direct/indirect effect；
7. 只有 IV/中介条件满足时才估计 adoption/mediation；
8. 报告适用域、Unknown 边界和失败边界。

## 5. 最小失败边界

- 若 assignment 可随机但 delivery/verification 不可观测：保留 ITT，放弃 delivery/adoption 机制结论；
- 若动作可观测但 no-message physical witness 缺失：只报告 action-level response，不报告信息早于物理传播；
- 若个体风险可测但区域 cohort 不稳定：只报告个体或固定 cohort；
- 若区域风险没有显著 ITT：仍可报告 message lifecycle failure、state-dependent response 和作用边界；
- 若 message effect 被 physical propagation 遮蔽：报告可区分性边界，不宣称不存在作用；
- 若 controller adoption 近零：报告 adoption bottleneck，而不是把无效归因于消息内容。

## 6. 现阶段执行限制

本文件不启动新 SUMO 矩阵、现实数据采集、Stage 1.1 或 Protocol Lock。下一步应先由研究者确认处理单位、区域结果、物理到达定义和是否允许未来消息实验。
