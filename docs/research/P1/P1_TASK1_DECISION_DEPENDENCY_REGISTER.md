# P1 Task1 决策依赖登记

日期：2026-11-01
登记原则：P0 Task3 的 D1–D10 全部保持 **Proposed / Awaiting Researcher Decision**。本登记把“理论必须保留什么”和“后续何时冻结什么”分开，不把 Codex 推荐改写为 Agreed。

## 1. 分类规则

- **P1 structural**：影响理论变量或 DAG 基本结构，P1 必须用一般化符号保留；
- **P1 generalizable**：可在多个方案下建模，当前不需要选唯一实现；
- **P2–P6**：属于源事件、消息证据、风险测量、实验设计、统计规划或资源出口；
- **需要研究者确认**：涉及核心研究对象、主 estimand、适用域或主张层级，不能由本文冻结。

## 2. D1–D10 登记

| ID | 当前状态 | 理论变量/结构 | 是否影响本次 P1 | 可否暂留多方案 | 所属阶段 | 推荐 Proposal 及理由 | 需要研究者确认？ |
|---|---|---|---|---|---|---|---|
| D1 | Proposed / Awaiting | 平台适用域 \(H_e\)、证据层级和外推边界 | 是，但只影响适用域，不改变双网络结构 | 可以；模型同时容纳现实封闭场、SUMO、HIL | P1 入口；最终属 P2–P8 | 现实封闭场整场事件随机化作为现实证据目标；SUMO 只作模型准备，避免把仿真写成现实证据 | 是 |
| D2 | Proposed / Awaiting | \(S,C,A\)、四格 \(Y(s,c)\) 与 source-present ITT | 是，决定估计对象层次 | 可以；P1 同时定义四格和两臂 | P1 结构；主次关系属 P5 | 保留长期四格；把两臂作为源存在时的 policy ITT，不把它升级为交互 | 是 |
| D3 | Proposed / Awaiting | Source Event \(S_e,T_E\)、物理链起点 | 是，必须允许 Formal P2 与安全受控扰动两类输入 | 可以；区分真实事件和受控机制域 | P2 | 优先既有 Formal P2；若安全条件不能满足，明确收窄为受控扰动机制研究或停止现实主张，不能降阈值 | 是 |
| D4 | Proposed / Awaiting | \(C,R,W\)、\(Y_\mathcal T\) 和区域 exposure | 是，决定结果节点 | 可以；用固定预列 cohort/region/window 参数化 | P4 | 固定完整实验车队和区域，Formal rho 固定窗、车辆等权作为候选主结果；具体边界待定 | 是 |
| D5 | Proposed / Awaiting | \(T_P,\phi(S_R(t))\)、路径和删失 | 是，决定时间优先性变量 | 可以；P1 保留速度、密度、间距和 Formal 风险候选 | P2/P4 | 独立路侧持续速度变化作为首选候选，间距/密度/rho 辅助；不从距离或假速生成 \(T_P\) | 是 |
| D6 | Proposed / Awaiting | \(T_R,T_P,F_0(t),\eta,H\) | 是，决定总体 vs 个体时间对象 | 可以；P1 同时保留区间与删失 | P2/P5/P6 | 先做总体 early-window effect 与 no-message arrival distribution；个体跨世界提前秒数保持不可识别，除非另有设计 | 是 |
| D7 | Proposed / Awaiting | \(\mathbf A_e\)、\(g_I,g_P\)、干扰域 | 是，决定潜在结果写法 | 可以；整场、车辆级、两阶段均保留 | P5 | 首版单跳/整场或 session assignment，明确域内干扰；未知域外影响时不声称独立车辆效应 | 是 |
| D8 | Proposed / Awaiting | \(D,V,A,U^{cmd},U,T_U\)；人类/控制器对象 | 是，决定机制节点，但不改变 ITT 结构 | 可以；自动可审计控制器与人类代理分别建模 | P3/P5 | 若优先可审计性，候选为自动控制器；主分析仍 ITT，adoption/action 机制需额外鼓励或 IV | 是 |
| D9 | Proposed / Awaiting | SESOI \(\delta\)、方差、样本量和精度 | 不影响 P1 数学结构，但决定可证伪门槛 | 可以；P1 只用符号和敏感性占位 | P6 | 由独立 pilot 估事件/配对方差、ICC、缺失、到达分布后制定；不采用历史 minimum=100 | 是 |
| D10 | Proposed / Awaiting | 结果层级、失败边界、适用域收窄 | 是，决定结果解释和停止规则 | 可以；分别保留 ITT、机制、模型内和 failure-boundary 出口 | P2–P8 | witness 缺失则放弃现实时间优先；缺 adoption 则保留动作/风险 ITT；只有模型则 simulator-only | 是 |

## 3. 哪些问题 P1 已经解决

P1 可以在不选择 D1–D10 的情况下完成以下内容：

1. 用 \(G_P(t)\) 和 \(G_I(t)\) 分开定义物理交互与信息可达；
2. 把消息生命周期、控制器采用、命令、实际动作和区域风险拆成不同变量；
3. 用时间层展开反馈并保留 Unknown/区间/删失；
4. 同时给出四格交互与 source-present 两臂 ITT，并证明二者不等价；
5. 把网络干扰写入 \(Y_i(\mathbf A)\) 或 \(Y_e(\mathbf A_e)\)；
6. 规定 H1–H4 的可证伪出口，而不提前选择正向结果。

## 4. 哪些问题可暂留多个方案

平台、源事件类别、目标区域和物理状态函数都可以先用带索引的泛化模型表示。P1 使用 \(C,R,W,\phi,F_0\) 等符号，并记录每个候选的识别条件；P2–P6 再根据真实证据、资源和研究者决定收窄。

控制器和人类驾驶者也可以共用消息—决策—动作链，但采用的观测语义不同：自动控制器可有 decision receipt；人类只能在明确设计下提供 acknowledgement 或动作代理，不能混称心理采用。

## 5. 属于 P2–P6 的决定

- P2：Formal P2 是否是首版 Source Event、物理路径 witness、\(T_P\) 的状态函数和删失；
- P3：消息端点、验证规则、控制器对象和 adoption 日志；
- P4：目标 cohort/region/window、Formal rho 主结果、动作和风险 onset；
- P5：四格与两臂主次、整场/车辆级/两阶段随机化、干扰 exposure mapping、中介鼓励；
- P6：\(\delta\)、α、power、方差、ICC、样本量、多重时间窗和缺失界限。

## 6. 研究者需要明确确认的最小集合

无需重新批准公式排版、变量命名或文件组织；但以下实质选择必须在未来形成真实 Agreed Decision 后才能冻结：

1. 首版适用平台和主张层级（D1）；
2. 两臂与四格的正式主次关系（D2）；
3. Source Event 和 \(T_P\) 的最终操作定义（D3、D5）；
4. Target Cohort/Region/Window 与主要风险结果（D4）；
5. 是否允许个体时间优先性主张（D6）；
6. 随机化单位和干扰策略（D7）；
7. 自动控制器或人类驾驶者作为首版研究对象（D8）；
8. SESOI、精度和样本量（D9）；
9. 资源或证据失败时的主线收窄（D10）。

## 7. 状态与边界

本登记不改变现有 Agreed 决策，不写 Protocol Lock，不授权新实验，不访问 locked holdout，不启动 Stage 1.1。D1–D10 的推荐只用于组织后续理论和研究者审阅。

依据：[P0_TASK3_RESEARCHER_DECISIONS.md](../P0/P0_TASK3_RESEARCHER_DECISIONS.md)、[P0_CLOSEOUT_AND_P1_ENTRY_NOTE.md](../P0/P0_CLOSEOUT_AND_P1_ENTRY_NOTE.md)。
