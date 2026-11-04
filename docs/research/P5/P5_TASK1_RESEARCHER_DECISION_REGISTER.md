# P5 Task1 研究者决策登记

Task ID：AAD-P5-TASK1-20261104。日期：2026-11-04。

本表是设计审计登记，不是批准记录。Agreed 只继承有明确来源的决定；Proposal 表示推荐内容；Awaiting Researcher Decision 表示仍待研究者选择；Unknown 是事实或数值尚不可知；Blocked 是特定估计对象当前缺少必要证据，非整个文档任务失败。

## 1. 继承的 Agreed：不重复批准

|编号|已确认内容|正式来源|继承边界|
|---|---|---|---|
|I01|当前 source-present 两臂 ITT，最终保留 Source × Communication 四格|[P1 研究者决定](../P1/P1_TASK2_RESEARCHER_DECISIONS_20261101.md)|资格两臂不等于全部 source-present 或四格交互|
|I02|独立通信盲 Observer 先确认 Qpre，再在 source-present、Qpre=1 内随机通信；主分析不按下游消息/动作/Witness 筛选|[统一定义 DEF-POP-001 与细则 I/M](../definitions/CORE_SCIENTIFIC_DEFINITIONS.md)|Qpre 只对 ZC 是处理前变量，可能受 ZS 影响；具体概率/随机化实现未冻结|
|I03|当前 SUMO、单跳、自动控制器；总体时间优先性；物理三层分别保留|[P1 决定](../P1/P1_TASK2_RESEARCHER_DECISIONS_20261101.md)、[统一定义](../definitions/README.md)|不声称现实迁移、任意最早物理影响或单例反事实提前秒数|
|I04|Adoption 是有效消息纳入具体策略决策输入且有消费回执和 decision_id|[2026-11-03 正式 ratification](../P3/CONTROLLER_ADOPTION_RATIFICATION_20261103.md)|采用不要求动作改变；接收、验证、缓存不是采用|
|I05|Enabled/Disabled 都接收验证，仅 Enabled 可用于策略；运行/交互组方向，本次 P7 运行级固定模式；无新增独立 Safety Layer|[P7 D1–D8](../P7/P7_RESEARCHER_DECISIONS_20261103.md)|固定模式元数据不是随机化器；SUMO 原生约束仍需记录|
|I06|P4 D01–D08 全部 Agreed；Δv 主 / Δa 辅、可靠共同观测、处理前完整资格名单、固定 N 等权同窗平均、Unknown 上下界、源专属 QC、固定窗、P3/P4 分离|[P4 正式决定](../P4/P4_RESEARCHER_DECISIONS_20261104.md)|最终 Y 算子已定；正式区域/窗值、Action 阈值/持续/容差仍未定|
|I07|Formal rho/P2、P3 schema、统一定义 v0.4 / 27 IDs、Gate/Lock/Stage1.1 授权保持|[统一入口](../definitions/README.md)、[当前状态](../../../AI_CONTEXT/00_PROJECT_STATE.md)|本任务无生产代码、配置、定义 ID 或实验变更|

Task6/E61 的最终 Y 聚合历史待决已由 P4 日期增量接续；Task7/E61 是不同的有限物理校准授权。本任务不重新批准或混用两者。

## 2. 本任务新增方案与待决事项

|ID / 状态|决策问题与当前事实|选项及影响|Codex 推荐（均非 Agreed）|需要的后续条件|
|---|---|---|---|---|
|P5-D01：Proposal；Awaiting Researcher Decision|资格两臂与最终四格如何并存；Q(1) 在无源臂不可见|A 当前资格两臂；B 源前共同 source-opportunity 四格；C principal-stratum 四格。A 可保留现行主线，B 回答共同总体交互但需新支持，C 需强假设或宽界|A 为当前主分析对象，B 为最终四格设计候选，C 仅备选敏感性/部分识别；不改变四格方向|共同总体、源前 H0、四格分配和 source-absent 策略须明确|
|P5-D02：Proposal；Awaiting Researcher Decision|源前机会与完整区域资格角色名单如何冻结|预列道路/时段/需求角色机会，或另一共同源前规则；不能按处理后实际入区/发生源倒推|如选择 B，同步源前 roster/region/window/公共 clock，source 未实现也保留 assignment|源分配、实际源和实现失败分开；不得筛 realized-source 后仍称 source-assignment ITT|
|P5-D03：Proposal；Awaiting Researcher Decision|风险 ITT 的通信对照是什么；P7 Disabled 仍接收验证|Enabled vs No Message 测完整通信政策；Enabled vs Disabled 测策略使用开关；可分别定义但不能混池|保留两种对照的不同含义；主对照需研究者明确，未经等价证明不合并|网络负载、计算/时序、原生控制和失效路径的一致性审计|
|P5-D04：Proposal；Awaiting Researcher Decision|具体分配单位与独立重复；P7 只实现运行固定模式|完整 run；道路时间簇；预设 matched-block。车辆级会有强干扰且当前无混合支持|首版优先完整 run，预设 matched-block 保留依赖；道路时间簇为可证隔离时备选|真实随机机制/概率/日志；reset、跨簇信息与物理 carryover 证据；P6 处理方差/ICC|
|P5-D05：Proposal；Awaiting Researcher Decision|同运行多事件的主样本规则|盲法预定 index source / 固定运行级复合结果 / 簇内预列事件分析；事件数受处理影响时不可扩 n|优先预定 index-source 机会并保留无事件/失败记录；未发生事件时的 outcome 规则须先定|不能用未来采用、风险或 Witness 选 index；后续事件不新增独立样本|
|P5-D06：Proposal；Awaiting Researcher Decision|信息域与物理域如何界定，能否 partial interference|整场政策总效果；经证据支持的部分干扰；预定 exposure mapping|主对象先是运行/簇总体政策效应；分别登记信息域和物理域，审查跨域泄漏|direct/spillover 还需混合分配和 exposure 正支持；实际 delivery/adoption 不能冒充分配 exposure|
|P5-D07：Proposal；Awaiting Researcher Decision|Adoption 多消息/多决策处理如何定义|描述性机会级采用率；开关 assignment reduced form；额外假设下 IV/LATE|先保留采用率与开关 ITT；不批准 IV/LATE，先指定 decision/窗口/处理版本|相关性、独立、排除、单调、正支持及干扰条件；日志不证明排除限制|
|P5-D08：Proposal；Awaiting Researcher Decision|Action–Risk 机制识别路线|动作 assignment/鼓励；IV；纵向 g-formula；interventional indirect effects|先保证 H1 测量和随机政策效应；若必须识别 H3，优先论证可定义、安全、被授权的动作干预，其余为条件化备选|动作实际实现、全网时间混杂/反馈、正支持；任何新实验需另外授权|
|P5-D09：Proposal；Awaiting Researcher Decision|H4 的物理主 endpoint、源时间原点及标准化总体|micro/macro/cohort 分别评估；有限机制主 endpoint 或预定检验族|保留三层，按同资格/独立单位/H 权重分别对应 F0；源 onset 区间与 confirmation 分开|不得跨层取最小/最大；具体 endpoint 与时间映射待确认；检测器到真实到达桥接尚缺|
|P5-D10：Proposal；Awaiting Researcher Decision|风险缺失界与 UNKNOWN_SCOPE 如何进入主分析|保留全部 assignment；已知范围下最坏界；另行批准缺失假设才能压窄|P4 区间按臂传播；UNKNOWN_SCOPE 保留运行和原因，不造完整 Y、不删 run；固定总体可证时才用 [0,1] 最坏界|缺失机制/测量支持需审计；识别区间和置信区间分开|
|P5-D11：Proposal；Awaiting Researcher Decision|H1–H4 的联合与独立报告范围|H1 可独立报告，H2/H3 为机制层，H4 为联合时间判断|按各层证据分别报告，不以机制失败抹去 H1，也不靠 H1 自动确认机制/H4|P6 另行确定检验族、SESOI、同时带、持续规则、错误预算、样本量|

## 3. Unknown 与对象级 Blocked

|ID / 状态|缺口|当前可做|不能声称|
|---|---|---|---|
|U01：Unknown|Formal A=0，Independent Qualified=0，F0 / 总体 T_R–T_P Unknown|沿用来源审计和识别设计|已有合格真实因果样本或已分离时间|
|U02：Unknown|正式区域/窗数值、Action 阈值/持续/容差、完整现实总体覆盖|使用 P4 版本化接口、保留 THRESHOLD_UNSET / UNKNOWN_SCOPE|正式 T_U / T_R 已估计；工程数值已冻结|
|B01：Blocked（真实 H1 估计）|无合格随机化 assignment + 完整区域 Y 输入|明确 ITT 对象及数据接口|从 P7 单目标轨迹估完整区域风险效应|
|B02：Blocked（最终四格 / principal-stratum 交互）|共同源前资格、四格正支持、源机制、无源策略及潜在资格条件未满足|比较 A/B/C，构造非识别反例|τQ 等于 τSC，或随机源分配揭示无源 Q(1)|
|B03：Blocked（IV / Action–Risk 因果机制）|缺机制设计及不可由日志证实的额外假设|报告采用/执行事实，提出条件清单|采用率、日志齐全或普通回归就是机制因果效果|
|B04：Blocked（H4 实证判断）|无独立合格 F0；同域检测延迟/漏检桥接与联合风险推断缺失|按 endpoint 保存允许时间集合与 Unknown，给出可检验条件|单个事件的提前秒数；检测器 F0 就是真实最早到达 F0|

## 4. 决策处置与停止边界

本任务不要求现在逐项答复。推荐架构及取舍见[核心设计](P5_TASK1_CAUSAL_IDENTIFICATION_DESIGN.md)。研究者审阅后再决定哪些 Proposal 进入协议；本文完成不改变 Agreed 集合、H1–H4、定义版本、P3/P4/P7、Gate 或任何实验授权。本任务完成后停止，不自动启动 P6、论文同步或组会材料。
