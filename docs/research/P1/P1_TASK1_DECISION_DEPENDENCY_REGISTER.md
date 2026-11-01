# P1 Task1–2 决策依赖登记

日期：2026-11-01
状态：P1 Task2 已同步研究者确认的方向；操作参数继续 Awaiting Researcher Decision

## 1. 登记规则

P1 Task1 原始版本把 D1–D10 整体保留为 Proposed。P1 Task2 根据研究者明确提交的任务书，将已经确认的研究方向和仍未冻结的操作参数分开登记。历史 P0/P1 报告保留原状态；本文件作为当前依赖入口。

- Agreed：研究者已经确认的方向或原则。
- Awaiting Researcher Decision：尚未给出正式数值、边界、阈值、精度、随机化或停止规则。
- Unknown：需要未来数据、资源或观测才能判断，不能由文档决定。

## 2. D1–D10 当前登记

| ID | 当前状态 | 已确认研究方向 | 理论变量/结构 | 仍需决定的参数或证据 | 后续归属 |
|---|---|---|---|---|---|
| D1 | Agreed 方向；参数 Awaiting | 当前优先 SUMO；现实封闭场/实车不是前置条件；结论限于模型内 | \(H_e\)、模型内 \(X^*,M^*,Y^*\) 与外推边界 | 场景、模型适用域、未来现实扩展验证 | P1 已同步；P2–P8 |
| D2 | Agreed 方向；参数 Awaiting | 当前 source-present 两臂 ITT；最终保留四格；两者不混淆 | \((Z_S,S^*,Z_C,C^*)\)、\(Y(s,c)\)、\(\tau_{SC}\)、\(\tau_{\mathrm{ITT}}^{S=1}\) | 四格执行时机、分配概率、主次终点、正式统计计划 | P1/P5 |
| D3 | Agreed 方向；参数 Awaiting | Formal P2 为 A 路线优先；B 为独立安全受控扰动机制路线 | \((S^*,T_E)\)、Formal P2 qualification、B mechanism domain | A/B 场景、触发、窗口和适用域 | P2 |
| D4 | Agreed 方向；参数 Awaiting | 固定目标 cohort、region、window；区域总体 Formal rho/P2 为主结果候选 | \((C,R,W,Y_{\mathcal T})\) | 车辆成员、空间边界、窗口、进出规则、辅助指标 | P4 |
| D5 | Agreed 方向；参数 Awaiting | SUMO 只读 Observer；现实扩展用独立路侧传感器；Observer 不参与控制 | \((X^*,\widetilde X,\phi,T_P)\)、观测误差和缺失 | 物理状态函数、阈值、持续性、路径资格、删失 | P2/P4 |
| D6 | Agreed 方向；参数 Awaiting | 首版只研究总体时间优先性；不主张个体跨世界提前秒数 | \(\tau_R(t)\)、\(F_0(t\mid H)\)、\(T_R^{upper}<T_P^{lower}\) | horizon、\(\eta\)、分位数、同时置信水平、持续性 | P2/P5/P6 |
| D7 | Agreed 方向；参数 Awaiting | 单跳直接消息、不转发；保留物理网络干扰和区域 policy effect | \((Z_C,C^*,G_I(t))\)、\((g_I,g_P)\)、\(\mathbf A\) | 链路覆盖、超时/过期、随机化域、exposure mapping | P3/P5 |
| D8 | Agreed 方向；参数 Awaiting | 研究自动控制器；不纳入人类驾驶者心理采用 | \((D^*,V^*,A^*,U^{cmd,*},U^*)\) 与日志观测 | 控制器版本、日志、覆盖/接管、机制鼓励 | P3/P5 |
| D9 | Agreed 方向；参数 Awaiting | 先 Pilot 后功效/样本量；本任务不运行 Pilot | 事件方差、配对方差、ICC、缺失和 \(F_0\) | SESOI、α、power、独立单位、样本量、多重检验 | P6 |
| D10 | Agreed 方向；触发参数 Awaiting | 按 witness、adoption、action、区域覆盖和平台证据收窄主张 | 结果层级、失败边界、适用域 | 缺失比例、停止阈值、替代主线准入 | P2–P8 |

## 3. P1 已经可以执行的理论约束

1. 分配变量和真实状态分开：\(Z_S/Z_C\) 不是 \(S^*/C^*\)。
2. 真实过程和观测记录分开：Observer、日志和风险表带有质量、时钟、身份和缺失语义。
3. SUMO Observer 只能支持模型内物理观测，不升级为现实独立传感器。
4. 当前两臂 ITT 是 assignment-level policy effect；四格交互仍保留且不能由两臂直接替代。
5. Adoption、Command、Action 和区域风险仍是不同的处理后变量；IV/中介需要额外条件。
6. 总体时间优先性使用风险曲线与无消息到达分布，个体处理事件的 \(T_P(0)\) 仍不可观测。
7. 单跳通信不消除物理交互网络中的 spillover 和区域 policy effect。

## 4. 仍需研究者决定或未来证据关闭的内容

- SUMO 场景、源事件实例、目标车辆成员、区域边界和窗口；
- 物理到达状态函数 \(\phi\)、阈值、持续性、路径资格、时钟和删失；
- 消息覆盖、有效期、链路失败和实际 exposure mapping；
- 是否部署 adoption encouragement/IV，以及 IV 的可辩护条件；
- Action–Risk 采用何种干预性或 longitudinal 识别方案；
- SESOI、α、power、ICC、样本量、缺失准入和多重检验；
- D10 的失败边界触发数值和正式停止规则。

## 5. 边界和历史记录

本登记不修改 P0 Task3 原始决策清单的历史内容，不修改 Formal P2、Formal rho、D1/B witness、Scientific Equivalence、Gate 或正式实验配置。它不授权实验、Pilot、locked holdout、Protocol Lock 或 Stage 1.1。

最新同步记录：[P1_TASK2_RESEARCHER_DECISIONS_20261101.md](P1_TASK2_RESEARCHER_DECISIONS_20261101.md)。
