# P0 Task 2：数据源能力审计

日期：2026-11-01。审计依据为当前仓库源码、AI_CONTEXT、Task10–20 证据和已有数据审计，不启动新实验。

## 1. 能力矩阵

状态词：Directly Observed、Derivable、Proxy、Unobservable、Not identifiable。

| 数据源 | 信息链 | 物理链 | 风险结果 | 身份/时钟 | 可支持的结论 | 主要缺口 |
|---|---|---|---|---|---|---|
| NGSIM | Unobservable | Directly Observed trajectory；Leader/Follower 需条件核验 | Derivable proxy TTC/DRAC/PET，不能自动映射事故 | 车辆轨迹在单窗口可用；跨源/跨窗口身份和视频/PTS/Global_Time 未核实 | 轨迹测量与指标工程核查 | 无消息 assignment/delivery/adoption；无同源物理反事实；源/目标窗口不精确交叉 |
| MiTra T1 | Unobservable | Directly Observed 高频轨迹；Leader/Follower 派生 | Derivable proxy，需连续性 | 1,578,393 行、1,456 辆车、1,308,347 leader/follower 行；道路坐标、参考点、视频绑定仍 Unknown | 条件跟驰输入和动作测量 | 无消息链、无独立物理 witness、空间校准和真实物理间距未锁定 |
| SPMD | Partial/Proxy：RV_RX 接收状态连续性 | 无配对物理传播 | 无同源风险结果 | 不能证明逐包接收时间；通信状态边界有限 | 接收状态工程审计 | 行不是消息；缺送达/验证/采用/控制器动作；通信缺失不能解释为丢包 |
| SUMO | Directly generated lifecycle fields in fixture | Directly generated state and no-message model path | Derivable synthetic risk fields | 仿真时钟、身份和日志完整；现实等价性未证明 | 受控机制和证据契约工程验证 | 当前实现没有现实消息闭环；scientific_claim_eligible=false；不能替代现实因果 |
| Task9/Task19 | 无 message treatment | Leader motion 输入，Follower response 可观察 | 局部风险代理描述 | 仿真身份/时钟可复现 | 固定 Leader–Follower 条件下局部响应描述 | 无源事件物理传播、无区域风险、无采用和无独立 no-message witness |

## 2. 变量级状态

| 必需变量 | NGSIM | MiTra | SPMD | SUMO | 当前判断 |
|---|---|---|---|---|---|
| event_id/source event | Proxy/需规则 | Proxy/需规则 | Unobservable | Directly generated | 现实事件契约未锁定 |
| message_assignment | Unobservable | Unobservable | Unobservable | Directly generated fixture | Causal treatment 缺失 |
| generation/transmission | Unobservable | Unobservable | Partial/未配对 | Directly generated fixture | 现实生命周期缺失 |
| delivery_time/message_id | Unobservable | Unobservable | Unobservable | Directly generated fixture | SPMD RV_RX 不足 |
| verification | Unobservable | Unobservable | Unobservable | Directly generated fixture | 当前现实不可观测 |
| controller adoption | Unobservable | Unobservable | Unobservable | Directly generated fixture | 不能比较 adopted/not-adopted |
| commanded action | Unobservable | Unobservable | Unobservable | Directly generated fixture | 现实动作归因缺失 |
| observed action | Directly Observed trajectory | Directly Observed trajectory | Unobservable | Directly generated | 现实有轨迹但无消息连接 |
| physical arrival | Proxy/窗口内轨迹 | Proxy/候选段 | Unobservable | Directly generated model state | 无同源独立反事实 |
| individual risk | Derivable proxy | Derivable proxy | Unobservable | Synthetic derivation | 仍需固定指标与质量规则 |
| regional risk | Not identifiable | Not identifiable | Not identifiable | Synthetic only | 当前 C3 不可识别 |

## 3. 可否组合数据集

NGSIM、MiTra、SPMD 和 SUMO 不能直接拼接为同一事件的因果链。它们的事件时间、车辆身份、空间坐标、通信状态和处理策略不共享统一键；跨数据集的相关性只能作为方法背景或测量校准，不能当作同源事件的因果证据。

可接受的组合方式：

1. NGSIM/MiTra 用于轨迹和风险指标的工程测量验证；
2. SPMD 用于检查通信状态字段的可观测边界；
3. SUMO 用于检查生命周期字段、no-message 机制和分析代码；
4. 未来同一随机化消息实验同时记录通信、控制器、轨迹和区域 witness，才形成因果链。

## 4. C1–C3 当前状态

| 主张 | 当前状态 | 不可替代的补充证据 |
|---|---|---|
| C1 信息链可审计并改变个体动作/风险 | **Not identifiable** | 同源随机 assignment、message_id 生命周期、adoption/controller log、动作时间锁定、固定风险指标 |
| C2 信息到达早于独立物理传播并产生可归因差异 | **Not identifiable** | 同源 no-message 物理 witness、统一时钟、Tdelivery/Tverification/Taction/Tphys |
| C3 个体动作变化形成区域风险因果效应 | **Not identifiable** | 多簇随机化、固定区域/cohort/window、双 exposure mapping、区域 risk burden 和 cluster-level uncertainty |

## 5. 最小数据补充

- 每个源事件、消息、车辆、控制器和风险窗口的稳定键；
- monotonic clock 或可验证跨设备时钟偏差；
- message assignment、generation、send、delivery、verification、adoption、rejection 和 command；
- 轨迹的 position、speed、acceleration、leader_id、net_gap 及身份连续性；
- 同源 no-message 对照的物理状态和区域 witness；
- 事件/簇级随机化元数据、exposure_mapping_version、缺失原因和 SHA256。

这些是未来设计输入，不代表已经授权采集或实验。
