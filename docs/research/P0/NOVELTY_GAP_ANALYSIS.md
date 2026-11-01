# 创新性威胁与研究空白

## 已经不能单独主张的内容

1. 信息可以比车辆运动更早到达：Schönhof、Wang 及后续 V2V IFPW 工作已经给出动态网络、传播速度和服务率模型。
2. 远端/遮挡警告能改变驾驶反应：BLOS 和 in-vehicle warning 研究已测量反应时、制动和状态异质性；Peng 2026 已将因果机器学习用于 BLOS 警告响应。
3. 非局部信息可以改变交通流稳定性：Huang–Du 等非局部模型已经给出稳定性条件和波耗散结果。
4. 车辆或信息有空间作用区域：Jerath 2024 已在瓶颈—容量下降场景提出 ZOI、event horizon、null horizon。
5. 拥堵和瓶颈可在网络上时空传播：Saberi 2020 与 Duan 2023 已有 NC 级实证/理论证据。
6. TTC/DRAC/PET 可作为风险代理：指标有效性、语境依赖和预测能力已有系统综述与 naturalistic 评估。

## 仍可能成立的空白（均为 Proposal）

### A. 可审计的消息介导风险机制

源事件 → 消息生成 → 发送 → 送达 → 验证 → 控制器采用 → 实际动作 → 个体风险 → 区域风险，这个完整生命周期在交通风险研究中尚未被同一设计逐段观测。空白不在“有消息”，而在每个中间节点可被独立失败、审计和反事实替换。

### B. 信息到达与物理扰动到达的独立时序识别

已有信息波工作给出信息传播速度，已有交通流工作给出冲击波/瓶颈传播；但 AAD 所需的是同一源事件、同一车辆群体、同一时间轴上的竞争到达时间，并且要排除 leader 变化、测量漂移和自然跟驰。当前项目自身仍明确缺少独立 time-indexed physical witness，因此这个空白尚未被 AAD 证据填补。

### C. 干扰下的网络级风险效应

网络干扰文献已经提供 estimand 和 exposure mapping；AAD 的潜在增量是把“消息暴露”和“物理邻接/跟驰暴露”拆成两个可观测暴露，并报告 direct、indirect/spillover、total 或 policy effect。只有在随机或准随机干预、明确邻域、时间顺序和 positivity 成立时，区域风险效应才可超出相关性描述。

### D. 作用边界的可迁移机制

Jerath 的 ZOI 针对瓶颈总延误，Peng 的 BLOS 研究针对驾驶反应。可能的新问题是：在通信时延、丢包、渗透率、交通状态和道路拓扑变化下，消息介导风险效应是否存在可迁移的边界函数。需要跨状态/跨道路验证，不能预设单调关系。

## 关键反例

- 控制器可能收到消息但不采用；采用可能只改变期望速度，不改变风险指标。
- 观察到的早期响应可能由原始 leader 速度变化、视线/测量误差或自然反应造成。
- 区域风险下降可能来自样本构成、拥堵回归或评价窗变化，而不是消息。
- 网络干扰使普通 A/B 比较的 estimand 不再是个体效应；把 treated vehicle 与 untreated vehicle 直接相减可能失真。
- 没有独立物理基准时，“比物理传播更早”不可识别。

## 现阶段判断

AAD 最可能形成的原创性不是“类超距”现象本身，而是一个可失败、可审计、可因果识别的双传播机制：消息链与物理链在同一事件级时间轴上竞争，并通过采用—动作—风险路径影响网络级 outcome。该判断是 `Proposal`，不是 Agreed scientific contribution。
## P0 Task 2 可识别性更新

全文核对后，创新性威胁进一步具体化：

1. Schönhof 已在同一模型中说明车辆运动和消息拓扑相互耦合，并给出 1 km 上游消息到达概率/时间分布；AAD 不能把“信息早到”作为新现象。
2. Peng 已在随机化被试内模拟器中估计 BLOS warning 的 ORS +6.73 points（95% CI [1.36, 11.99]）和 response-conditioned RT −2.28 s（95% CI [−3.17, −1.14]），并报告瞬时控制状态异质性；AAD 不能把远端警告改变动作作为首次因果发现。
3. Jerath 已在 LWR 瓶颈模型中定义联网车辆的 ZOI、event horizon 和 null horizon；AAD 只能提出风险时序和独立物理基准上的可检验增量。
4. Hudgens–Halloran 与 Aronow–Samii 已提供 interference estimand、assignment design 和 exposure mapping；AAD 不能声称发明一般网络干扰因果理论。

因此，Proposal A–D 只有在同源随机 assignment、完整消息生命周期、独立 no-message physical witness、双暴露映射和区域 risk burden 同时成立时才有可能成为科学贡献。现有 NGSIM、MiTra、SPMD、Task9/19 和 SUMO fixture 均不能单独满足这些条件，详见 Task2 可识别性审计。
