# P0 Task 2：Estimand 与网络干扰规范

状态：**Proposal；等待研究者决定最小处理、区域和结果定义**。

## 1. 推荐的最小 estimand

研究单位：一次源事件下、在事件前已定义的目标车辆 cohort 中的车辆—窗口记录。
目标总体：满足身份、时钟、轨迹连续性和风险测量质量要求的目标 cohort；不因处理结果筛选。
处理：道路区段—时间簇级随机的 message availability/strategy assignment A。
对照：同源事件和相同目标 cohort 下的 no-message strategy。
时间窗口：从事件时刻 tE 预先定义的 [tE, tE+W]；W 必须在查看结果前锁定。
结果：经研究者批准的个体风险或固定区域风险 burden；不把 TTC 变化直接称为事故概率变化。
暴露映射：Xmsg,i,t 为消息邻域暴露，Xphys,i,t 为物理交互暴露；两者均由 assignment、轨迹、通信日志和预先锁定版本计算。

最小目标：

ITT_window = E[Yr_i(W,R,C; A=1, πmsg) − Yr_i(W,R,C; A=0, π0)]

优先估计完整策略的 total/policy effect。它允许 delivery 和 adoption 失败，因而回答部署消息策略是否改变结果，而不是只回答“已经采用的人是否更安全”。

## 2. 处理变量不能混用

| 变量 | 可回答的问题 | 是否适合作为首要随机处理 |
|---|---|---|
| Message assignment/availability | 提供消息策略是否改变结果 | 是 |
| Message delivery | 实际收到消息的效应 | 否，除非有通信鼓励或强识别条件 |
| Controller adoption | 采用消息的因果效应 | 否，需 IV/随机鼓励和干扰条件 |
| Actual action change | 动作改变是否导致风险变化 | 否，通常为处理后中介；需纵向中介设计 |

Observed delivery 或 adoption 不是 assignment 的替代品。把它们当作处理会引入 post-treatment selection。

## 3. ITT、直接、间接和总效应

对车辆 i 设本车 assignment ai、消息暴露 gi、物理暴露 hi：

Yi(ai, gi, hi)

- **Direct effect**：Yi(1,g,h) − Yi(0,g,h)；
- **Message spillover**：固定 ai 和 h，改变邻车 message exposure g；
- **Physical spillover**：固定 ai 和 g，改变邻车 physical exposure h；
- **Total effect**：本车和邻车 exposure 共同由策略变化；
- **Policy effect**：完整 πmsg 与 π0 之间的平均区域差异。

只有当 g/h 映射已定义、各状态有正概率、assignment design 已知且跨簇干扰受控时，直接和间接效应才有清楚含义。若映射不可靠，报告 policy effect 并把机制分解标为不可识别。

## 4. 部分干扰与一般干扰

Partial interference 需要：

1. 预先定义道路区段—时间簇；
2. 消息不能跨簇传播；
3. 物理跟驰、冲击波和车辆迁移不能跨簇影响目标窗口；
4. cluster assignment 和 individual exposure probability 可计算；
5. cluster 边界不会因处理改变。

这在现实交通中通常难以证明。若任一条件不满足，使用一般网络 interference 的 exposure mapping，或只估计不依赖簇隔离的 policy effect。映射版本、邻域半径/时间深度和车辆进出规则必须进入记录。

## 5. Delivery effect

若未来采用通信鼓励 Z（例如随机改变可用信道、冗余发送或提示策略），可以考虑：

E[Y(d=1) − Y(d=0)]

但要测量通信质量、距离、密度、状态和时间，并明确 Z 不直接改变驾驶动作或物理邻域。若通信改善本身改变了其他车辆的消息 exposure，则必须把 Z 的网络效应纳入 exposure mapping。

当前 SPMD RV_RX 是接收状态连续性，不是 message-level delivery；因此 Delivery effect = **Not identifiable**。

## 6. Adoption / complier effect

推荐把采用作为次级 IV estimand：

LATE = E[Y(1) − Y(0) | complier]

仅当随机鼓励满足 relevance、independence、exclusion、monotonicity、positivity，并且这些条件在网络干扰版本下成立时才可使用。要记录 rejection_reason、controller_decision 和 commanded_action；否则 adopted/not-adopted 差异只属于描述性相关。

## 7. Mediation estimands

自然直接和间接效应需要 mediator–outcome 混杂不受处理影响且被观测，并依赖跨世界假设。交通动作改变后续物理暴露，使这一条件特别脆弱。推荐：

1. 先估计 ITT/policy effect；
2. 再定义 interventional mediator policy，例如在 assignment 固定时按观测到的 adoption 分布随机干预；
3. 报告 adoption、action、individual risk、regional risk 四个节点的证据缺口；
4. 使用敏感性分析，不把中介分解当成首要结论。

当前数据无法估计 mediation。

## 8. 随机化设计比较

| 设计 | 可识别内容 | 主要风险 |
|---|---|---|
| 车辆个体随机化 | 个体 ITT；若干扰弱 | 消息/物理 spillover 污染 |
| 群组/道路区段随机化 | 直接/间接/区域 policy effect | 需要验证簇隔离 |
| 时间簇随机化 | 控制同一空间的时段差异 | 时间趋势和重复事件 |
| 两阶段随机化 | Hudgens–Halloran 风格直接/间接/总效应 | 需要足够簇和已知概率 |
| 一般网络随机化 | Aronow–Samii exposure-mapping effect | 映射复杂、方差大 |
| 观察性 delivery/adoption 对照 | 仅描述或模型关联 | 内生选择，不能作首要因果证据 |

推荐从道路区段—时间簇的 message availability 随机化开始；若跨簇泄漏无法排除，改用全网络 policy effect。

## 9. 不确定性

不确定性应同时反映：

- cluster/事件级随机化方差，而非把车辆重复行驶当独立样本；
- 暴露映射不确定性和簇边界敏感性；
- 风险指标有效性和缺失窗口；
- Unknown 物理到达时间；
- 多重窗口/多重指标的预注册规则。

不得用插值、零填充或挑选 seed 把不可观测风险变成确定值。

## 10. 推荐估计顺序

1. 结果和 cohort 质量审计；
2. 估计 ITT/policy effect；
3. 检查消息链各节点的覆盖率和失败模式；
4. 在条件满足时估计 exposure-specific spillover；
5. 只有 IV 和中介假设得到审计后，才估计 adoption/mediation。

方法依据：Hudgens & Halloran (2008)；Aronow & Samii (2017)。应用边界和消息/交通模型依据 Schönhof (2006)、Wang et al. (2019)、Jerath et al. (2024) 和 Peng et al. (2026)。
