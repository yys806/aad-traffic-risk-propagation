# P0 Task 2：独立物理传播基准与反事实审计

## 1. 四个概念必须分开

| 名称 | 定义 | 能否直接作为物理反事实 |
|---|---|---|
| Independent Physical Witness | 独立传感器/未参与消息控制的车辆或区域观察到的物理状态 | 不能自动等同；需证明不受消息干预 |
| Observed Physical Arrival | 实际轨迹中预定义物理状态到达目标的时间 | 只描述观察到的路径 |
| No-message Physical Reference | 同源事件、相同策略框架下明确不发送消息的对照路径 | 可支持反事实比较，前提是随机化/可比性成立 |
| Counterfactual Physical Arrival | 同一事件在另一消息策略下本应到达的时间 | 需要随机化对照或可信结构模型；单条轨迹无法提供 |

如果消息改变了车辆动作，那么干预组物理轨迹本身已经被处理改变。把干预后的 Tphys 当作 no-message Tphys 会把中介当作基线。

## 2. 到达事件的操作性定义

### 信息到达

根据研究问题分三层报告：

- T_delivery：接收端首次记录有效 message_id 的时间；
- T_verification：消息通过来源、时效和内容校验的时间；
- T_action：可观测动作相对于未处理基线首次达到预定义改变阈值的时间。

若只记录了接收状态而没有 message_id，T_delivery = Unknown。

### 物理到达

以源事件 tE 为时间零点，在目标 cohort/区域定义物理状态 φ(Spt)，例如预先批准的速度、密度、跟驰间距或风险状态越过阈值。Tphys 是 φ 首次满足且连续性达到规则的时间：

Tphys = inf { t ≥ tE : φ(Spt) = 1 for the required duration }

必须同时记录 source event、target cohort、空间窗口、采样频率、时钟来源和连续性规则。首次状态满足但后续观测缺失时，保留 Unknown 或区间，不插值成确定到达。

### 双传播比较

ΔT = Tphys − Tinformation

只有当两者来自同一事件、同一 cohort、同一统一时钟和同一观察窗口时，ΔT 才有意义。Tinformation 的层级必须在分析前锁定（delivery、verification 或 action），不能根据结果选择最有利的定义。

## 3. 基准设计比较

| 设计 | 支持的结论 | 不能支持的结论 | 当前可行性 |
|---|---|---|---|
| 随机化 no-message control | 同源事件下消息策略对物理到达和风险的 ITT/policy effect | 采用者的局部效应，除非另有设计 | 推荐但尚未实施 |
| 独立物理观测车辆/未干预区域 | 某路径上的物理状态观测 | 若车辆受消息或邻车动作影响，不能称 no-message 反事实 | 当前 MiTra/NGSIM 不满足 |
| 同源事件配对 | 减少事件间异质性 | 非随机配对仍可能有未测混杂 | 可作为补充 |
| 预定义物理传播模型 | 结构模型下的 counterfactual arrival | 现实物理真值、模型外推和模型误设 | SUMO/理论可做辅助 |
| SUMO no-message counterfactual | 受控机制路径和完整日志 | 现实世界独立证据、现实通信/驾驶有效性 | 现有 fixture 仅工程级 |
| 真实随机化消息实验 + 物理 witness | 同源双传播时序和区域 ITT | 超出实验适用域的普遍规律 | 未来必要设计 |

## 4. 当前数据判断

- MiTra T1 有高频轨迹和部分 Leader/Follower 关系，但道路坐标、参考点、视频绑定和真实物理间距仍为 Unknown；没有消息链。
- NGSIM 的源/目标窗口身份不能精确跨窗口匹配，缺少视频/PTS/Global_Time 验证；不能提供同源独立物理 witness。
- SPMD 没有已验证的逐包 receive time、发送—接收配对、采用或动作日志。
- Task9/Task19 的 leader motion 是输入，结果是局部 follower response；没有物理源事件到达目标区域的独立基准。
- SUMO 可以产生 no-message 结构反事实，但当前 stage_0_5_sumo.py 只具备 no-message 基线和工程字段；不证明现实因果。

因此当前 T_information、T_physical、ΔT 的现实同源估计均为 **Not identifiable**。

## 5. 研究者必须先决定的细节

1. 源事件是突发减速、冲击波前沿、瓶颈激活还是风险代理事件；
2. 目标是单车、固定 cohort 还是区域；
3. 物理状态是速度阈值、密度阈值、间距变化还是风险状态；
4. 状态连续多长时间才算到达；
5. 统一时钟是设备 monotonic clock、GNSS/PTP 还是仿真时钟；
6. 无法判定时报告 Unknown、区间还是删失；
7. 是否把 action arrival 与 message arrival 分开作为两个 Tinformation。

这些决定没有写入现行 Gate 或 Protocol Lock；本文件只提供 Proposal。
