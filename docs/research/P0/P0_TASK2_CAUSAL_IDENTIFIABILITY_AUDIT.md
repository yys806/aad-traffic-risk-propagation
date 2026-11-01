# P0 Task 2：双传播因果链可识别性审计

状态：**COMPLETED_WITH_LIMITATIONS**
日期：2026-11-01
范围：承接 P0 Task 1；不改变 Stage 0.5、Stage 0.6、Protocol Lock、Stage I 或 Stage 1.1 状态。

## 1. 审计结论

AAD 当前最小可识别问题应收窄为：

> 在预先固定的目标车辆 cohort、观察窗口和消息暴露映射下，将消息策略随机分配到道路区段—时间簇，是否改变目标车辆的预先批准风险结果；同时记录消息生成、送达、验证、采用和实际动作，用独立的 no-message 组估计信息策略相对于物理传播的总体效应。

这个问题可以在未来的受控消息实验中识别，但当前真实数据和已完成 Task9/Task19 结果不能识别它。当前数据没有同时观察同源事件的消息分配、完整消息生命周期、控制器采用、实际动作、独立物理到达和区域风险结果。

当前可作出的判断：

- **Fact**：Task9/Task19 是固定 Leader–Follower 条件下的局部响应和执行审计；没有消息分配、消息送达、控制器采用或区域风险结果。
- **Fact**：SPMD 只有 RV_RX 接收状态连续性，不能解释为逐包送达或采用日志。
- **Fact**：MiTra T1 和 NGSIM 提供轨迹及部分跟驰派生量，但没有消息链。
- **Fact**：SUMO Stage I fixture 有完整字段形状，但是合成工程夹具，科学资格为 false。
- **Inference**：AAD 的 C1–C3 在当前资料上不可识别；继续用回归系数或仿真 A/B 差异代替因果效应会违反证据边界。
- **Proposal**：先识别消息策略的 ITT/政策效应，再把 Delivery、Adoption、Mediation 作为有附加设计的次级 estimand。

## 2. 变量角色和处理层级

| 符号 | 变量 | 因果角色 | 观测定义 | 当前状态 |
|---|---|---|---|---|
| E | 源风险事件 | 源变量 | event_id、源车、事件时间/位置/类型 | 部分可由轨迹定义；统一事件质量未冻结 |
| L0 | 初始交通与车辆状态 | 基线混杂 | 速度、加速度、间距、前后车、交通状态、车辆类型 | MiTra/NGSIM 可部分获得 |
| A | message assignment/availability | 首要处理 | 随机分配的消息策略或可用性 | 当前不存在 |
| G | message generation | 处理后过程 | 消息由事件规则生成的时间和版本 | SUMO 可模拟；现实不可观测 |
| S | transmission | 处理后过程 | 发送时间、链路和发送状态 | SPMD 不能完整证明 |
| D | delivery | 处理后中介 | 接收端实际收到 message_id 的时间 | 当前没有可靠逐包记录 |
| V | verification | 处理后中介 | 消息来源、时效和内容验证结果及时间 | 当前不可观测 |
| M | controller adoption | 处理后中介 | 控制器采用、拒绝及理由 | 当前不可观测 |
| U | control action | 中介 | 控制器命令、目标值或动作策略 | SUMO fixture 可造；现实缺失 |
| YU | observed vehicle action | 中介/结果前变量 | 速度、加速度、间距和动作改变 | 轨迹可部分派生；消息归因不可识别 |
| Sphys | 物理状态 | 时间变化中介 | 跟驰交互、速度波、密度和状态改变 | 可部分观察；反事实不可得 |
| Tphys | 物理到达 | 时间结果 | 预定义物理状态首次到达目标 | 当前无独立 witness |
| Yi | 个体风险 | 个体结果 | 已批准 TTC/DRAC/PET 规则下的风险记录 | 可部分派生；缺失边界未冻结 |
| Yr | 区域风险 | 区域结果 | 固定 region/cohort/window 的聚合结果 | 当前不可识别 |
| Q | 观测质量 | 测量变量 | 身份、时钟、空间映射、有效性、缺失原因 | 影响可见性，不应当作安全结果 |
| Xmsg, Xphys | 双暴露映射 | 干扰变量 | 消息邻域暴露、物理交互邻域暴露 | 需预先定义和测量 |

Delivery、Verification、Adoption 和 Action 都是 assignment 之后的变量。将 adopted 与 not-adopted 直接比较，会把基线风险、通信质量、驾驶状态和物理暴露的共同影响混入“采用效应”。

## 3. 识别问题

### 3.1 ITT / policy effect

首要处理应是随机化的 message availability 或消息策略 A，而不是观测到的 delivery 或 adoption。固定目标 cohort C、区域 R 和窗口 W 后：

ITT_window = E[Yr(C,R,W; A=1, πmsg) − Yr(C,R,W; A=0, π0)]

这里的 π 是完整消息策略，包括生成规则、通信规则和控制器规则。该效应回答“部署消息策略是否改变区域风险”，允许送达和采用失败自然发生。识别条件是已知随机化概率、基线后处理、无跨簇泄漏或采用一般网络干扰映射、结果窗口预先固定、结果测量规则不随处理改变。

### 3.2 Delivery-related effect

Delivery 由距离、密度、通信拥塞、车辆状态和消息策略共同决定。它不是天然随机。若研究者要回答“实际送达的额外效应”，至少需要：

1. 随机化或可信外生的通信鼓励；
2. 对通信质量、距离、交通状态和基线风险进行充分测量；
3. 明确 delivery 版本的 exposure mapping；
4. 对送达缺失和未观测严格保留 Unknown。

当前 SPMD RV_RX 不能满足逐包 delivery 的观测要求，因此 delivery effect 当前标记 **Not identifiable**。

### 3.3 Adoption / complier effect

Adoption 是控制器或驾驶者对已验证消息的采用，不等于收到消息。采用效应需要随机鼓励或其他工具变量 Z。IV 版本至少要求：

- relevance：Z 能改变 adoption 概率；
- independence：Z 与潜在结果独立，或在预先定义的基线/簇条件下独立；
- exclusion：Z 只通过 adoption 影响结果；
- monotonicity：不存在反向服从者，或明确建模不同服从类型；
- interference-compatible versions：Z 对邻居的直接网络效应已纳入 exposure mapping；
- positivity：各相关暴露状态具有正概率。

现有 Task9、MiTra、NGSIM、SPMD 和 SUMO fixture 都没有满足上述条件的可用鼓励设计，因此不能报告 complier effect。

### 3.4 Mediation

链条为 A → D → V → M → U/YU → Yi → Yr。自然直接/间接效应还要求没有未测量的处理后 mediator–outcome 混杂，并要承担跨世界假设；车辆动作本身又改变后续物理暴露，形成时间变化混杂。推荐先使用 interventional direct/indirect effects 或明确的 stochastic mediator policy，并只在中介和混杂均被记录时估计。当前数据不能识别 mediation decomposition。

## 4. 网络干扰

单位 i 的结果应写成：

Yi(ai, gi(A−i), hi(P−i))

其中 g 是消息暴露映射，h 是物理交互暴露映射。g 和 h 必须按时间展开，因为车辆进出、通信邻居和跟驰关系都会变化。

Partial interference 只在以下条件下可接受：道路区段—时间簇之间没有消息链泄漏，没有物理跟驰/冲击波跨簇传播，目标窗口内车辆不跨簇迁移，且映射规则在实验前锁定。交通网络通常更接近一般干扰；若不能验证簇隔离，应使用全网络 policy effect 或 Aronow–Samii 风格的 assignment→exposure mapping。

需要分别定义：

- **Direct effect**：本车消息处理变化、其他暴露固定；
- **Indirect/spillover effect**：邻车 message/physical exposure 变化、本车处理固定；
- **Total effect**：本车和邻车暴露共同变化；
- **Policy effect**：整套消息策略相对于 no-message 策略的区域结果差异。

普通车辆级 A/B 不足以识别区域效应，因为一个车辆的动作会改变邻车的物理状态，消息也可能多跳传播。

## 5. 识别状态矩阵

| 效应 | 当前数据 | 最小新增条件 | 结论 |
|---|---|---|---|
| 消息策略 ITT | 无随机消息 assignment | 预注册簇/时间随机化、no-message 对照、完整结果窗口 | 未来可识别 |
| Delivery effect | 无逐包送达和时钟 | 可验证通信鼓励或完整链路日志 | 当前不可识别 |
| Adoption effect | 无 adoption/controller log | 随机鼓励、IV 条件、动作日志 | 当前不可识别 |
| Individual action mediation | 轨迹可部分获得，但无消息归因 | message_id 到动作窗口的审计链 | 当前不可识别 |
| Individual risk effect | 轨迹风险代理可部分派生 | 固定指标、连续性和同源处理 | 当前不可识别 |
| Regional ITT/policy | 无固定 cohort、区域和干扰映射 | 多簇事件、预定义区域结果和双暴露映射 | 当前不可识别 |
| Natural mediation | 没有处理后混杂和跨世界条件 | 纵向中介设计、敏感性分析 | 不推荐作为首个 estimand |
| T_information − T_physical | 物理反事实缺失 | 同源 no-message witness/随机化对照 | 当前不可识别 |

## 6. 审计边界

本文件不授权新实验，不冻结 Protocol Lock，不改变风险指标，不读取 locked holdout。任何未来实验先由研究者确认处理、区域结果、网络簇和物理到达定义，再进入下一 Task。

## 7. 文献依据

Hudgens & Halloran (2008), DOI 10.1198/016214508000000292；Aronow & Samii (2017), DOI 10.1214/16-AOAS1005；Peng et al. (2026), DOI 10.1016/j.aap.2026.108642；Schönhof et al. (2006), DOI 10.1016/j.physa.2006.01.057。逐篇阅读状态和局限见 paper_notes 及 PAPER_REGISTER.csv。
