# P0 Task 2：动作到区域风险的证据链

状态：**Proposal；当前区域因果效应不可识别**。

## 1. 区域结果必须先固定

定义区域 R、目标车辆 cohort C 和观察窗口 W。车辆进入 R 或离开 R 的规则必须在处理前确定，不能因为消息改变了车辆路线或停留时间而事后重定义 cohort。

推荐记录三种互补结果，但只选择一种作为首要结果：

1. **个体风险事件率**：固定有效观测时长内的风险事件数；
2. **车辆时间标准化风险 burden**：风险事件或风险持续时间除以有效 vehicle-time；
3. **区域时间积分 burden**：在固定空间—时间网格内对预先批准的风险量积分。

TTC、DRAC、PET 等只能作为已批准代理指标。TTC 的均值或低分位数变化不等同于事故概率变化；代理指标必须保留 metric、validity_status、阈值版本和观测窗口。

## 2. 个体动作与风险

消息链到个体结果的最小证据为：

Message assignment → delivery → verification → adoption → commanded action → observed speed/acceleration/gap → approved risk metric

每一步都需要：

- 同一 vehicle_id 和 message_id；
- 单调且可校验的时间戳；
- 处理前基线；
- action change 的预定义阈值和持续时间；
- 区分未采用、无动作、动作不可观测和测量失败。

车辆动作改变可能同时改善本车和后车的物理暴露，因此不能把本车风险降低直接当作区域风险机制。

## 3. 区域聚合规则

| 事项 | 推荐规则 | 失败处理 |
|---|---|---|
| 车辆进入/退出 | 由处理前定义的空间边界和时间窗确定 | 出入时间缺失则记录 Unknown，不推断停留 |
| 车辆构成 | 固定 cohort 或固定入区规则 | 处理后改变的构成不作为首要结果 |
| 重复观测 | 以 vehicle_id 和 cluster/event 作为相关结构 | 不把每个采样点当独立样本 |
| 无效风险值 | validity_status=INVALID | 不以零代替 |
| 未观测风险 | missing_reason=UNOBSERVABLE/UNKNOWN | 输出上下界或删失分析 |
| 风险持续时间 | 需满足最小连续时长 | 断裂段不能自动拼接 |
| 车道/区域映射 | 记录空间映射版本 | 映射失败则区域结果为 Unknown |
| 统计不确定性 | 按事件、簇或参与者聚类 | 不使用车辆行数伪造精度 |

若区域内有效车时为零，区域风险结果为 Not identifiable，而不是零风险。

## 4. 中介链证据分层

| 链节点 | 最低证据 | 当前证据 |
|---|---|---|
| Message | assignment、message_id、generation、delivery | 现实缺失；SUMO fixture 合成 |
| Adoption | verification、adoption_status、reject reason、controller decision | 不可观测 |
| Action | command 和轨迹变化的时间锁定 | 轨迹可部分派生，消息归因缺失 |
| Individual risk | 固定指标、连续性和质量状态 | 可部分派生，但无同源处理 |
| Regional risk | 固定 R/C/W、聚合规则、依赖结构 | 当前不可识别 |

任何中介断点都应报告 coverage 和 failure counts。链条完整不等于风险效应已成立；需要随机 assignment 和 no-message counterfactual。

## 5. 区域 estimand

最低推荐是区域 policy effect：

Yr(πmsg) − Yr(π0)

其中 πmsg 包括完整消息策略，π0 是 no-message 对照；效应针对固定 R、C、W 和预定义风险 burden。只有在双暴露映射可测量时，才进一步分解 message spillover 和 physical spillover。

对于时间变化暴露，可以把风险结果写成：

Yr = aggregate over i in C and t in W of ri,t, with valid-time weights

聚合的权重、有效 vehicle-time、区域边界和风险阈值必须进入版本化契约。

## 6. 当前数据和研究结论

- MiTra T1 可提供部分车辆动作和 Leader/Follower 派生量，但没有 message assignment/adoption，也没有现实物理 witness。
- NGSIM 可用于轨迹风险代理的工程核查，但跨窗口身份和时空校准不足，不能支持同源区域因果。
- SPMD 不提供完整 message lifecycle 或 controller action。
- Task9/Task19 的局部 follower response 不是区域 risk effect。
- SUMO fixture 可检验字段和闭环日志，但其区域结果是合成机制结果，当前 scientific_claim_eligible=false。

因此，Message → Adoption → Action → Individual Risk → Regional Risk 的完整中介链当前为 **Not identifiable**。若未来只能获得个体动作而不能获得区域物理 witness，研究应收窄为 action-level causal response 或 failure-boundary study。
