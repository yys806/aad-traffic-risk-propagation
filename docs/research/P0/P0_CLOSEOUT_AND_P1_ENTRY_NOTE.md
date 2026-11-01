# P0 收口与 P1 入口记录

日期：2026-11-01
状态：`COMPLETED_WITH_LIMITATIONS`（D1–D10 仍待研究者决定；本文不新增阶段枚举）

## 1. 收口范围

P0 Task1–3 的主要研究工作已经完成。本记录把三项工作的事实、证据边界和未决依赖汇总为 P1 的输入；不新增 P0 Task4，不改 Formal P2、Formal rho、D1/B witness、Scientific Equivalence、Gate 或任何正式实验配置。

当前正式状态仍为：Stage 0.5 `CLOSED_WITH_LIMITATIONS` 且 scientific Gate blocked；Stage 0.6 `PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS`；Protocol Lock `BLOCKED`；Stage I `READY_ENGINEERING_ONLY`；Stage 1.1 `NOT_AUTHORIZED`。

## 2. P0 Task1–3 完成情况

| 任务 | 已完成内容 | 证据边界 |
|---|---|---|
| Task1 文献与创新性审计 | 建立 Zotero/检索治理、最近邻矩阵、创新性缺口和 NC 风险定位；复核信息–物理耦合、非局部控制、V2X/BLOS 警告、交通网络传播和干扰因果方法 | 信息传播更快、V2X 改变行为、非局部控制、ZOI/传播波、TTC/DRAC/PET 聚合均不能单独作为 AAD 的新颖性主张；可辩护贡献仍是 Proposal |
| Task2 可识别性与证据契约 | 建立双传播因果链、ITT/四格对象、网络干扰边界、物理反事实审计、区域风险中介边界和八类证据契约 | 现有 NGSIM、MiTra、SPMD、SUMO fixture、Task9/19 不能识别完整 C1–C3 因果链；采用/中介不能靠完整日志自动识别 |
| Task3 最小消息干预与物理基准可行性 | 评估封闭测试场整场事件随机化、独立路侧 witness、随机 no-message 事件、SUMO 和 HIL 的适用范围及资源依赖；形成 D1–D10 清单 | 设计为 `CONDITIONAL GO`，当前现实确认启动为 `NO-GO`；资源、源/区域/时间定义、SESOI、方差和最终样本量仍 Unknown；所有 D1–D10 仍 Proposal / Awaiting Researcher Decision |

## 3. 已有充分证据与仍属 Proposal 的内容

### 3.1 可视为已建立的研究事实

- 信息传播、非局部交通控制、V2X 警告导致行为响应、交通瓶颈/拥堵传播和干扰因果推断已有先行方法与结果。
- AAD 的研究对象必须同时保留物理传播链与信息传播链，并把消息送达、验证、采用、动作和区域风险分开记录。
- Formal rho、Formal P2、固定窗口、缺失上下界和车辆等权聚合已有版本化工程实现；本任务不改变其语义。
- 网络中存在干扰；车辆级结果不能默认只依赖自身处理。整场或簇级随机化、明确 exposure mapping 和正支持是候选识别条件。
- 任务18/19 的局部 Follower 响应是工程/描述性证据，不能当作 AAD 核心信息因果效应或现实物理传播证据。

### 3.2 仍属 Proposal 或 Unknown 的内容

- AAD 是否在普通物理影响到达前产生信息介导的区域风险因果效应；
- 首个适用平台、正式 Source Event、Target Cohort、Region、Observation Window；
- 物理到达操作定义、时间误差和独立物理 witness；
- 自动控制器还是人类驾驶者作为首版研究对象；
- 四格与两臂设计的正式主次关系、网络随机化和干扰处理；
- SESOI、正式样本量、统计准入和资源可用性。

## 4. 创新性定位与收窄边界

信息快于物理传播本身不是独立创新；V2X/BLOS 警告改变行为也不是独立创新。AAD 可能形成的增量是：在同源源事件、固定目标区域和独立物理基准下，审计消息生命周期及控制器采用，估计干扰感知的区域风险效应，并把效应时间与物理到达分布放在同一时钟和不确定性框架内。上述贡献仍是有条件 Proposal，不能用当前工程或仿真结果预先确认。

## 5. 平台和实验适用范围

- **现实封闭测试场**：若资源和安全审批存在，是首选现实证据目标；需要整场事件随机化、完整端点日志和独立路侧测量。当前访问与许可 Unknown。
- **SUMO/TraCI**：可复用四格、消息生命周期、动作比较、联合时间轴和 Formal rho 接口，适合模型内机制和接口核验；不能直接提供现实因果、现实物理真值或 Stage 1.1 证据。
- **HIL/驾驶模拟器**：可研究人类响应或模型交通物理的组合；多驾驶者网络、完整 adoption 和现实区域风险仍需额外平台与伦理条件。
- **自然观测数据**：没有随机/外生处理和完整消息链时，只能支持描述或明确假设下的观察性分析。

## 6. P1 研究输入与真正推进

P1 直接复用 Task2 的双传播模型、变量字典、证据契约、ITT/干扰规格、区域风险聚合和物理反事实限制；不重复做文献全面搜索或 Task9/18/19 实验。

P1 的新增工作是把这些审计结果组织成：

1. 两张不混淆的动态网络和统一状态转移；
2. 从生成到动作、风险和物理到达的时间事件语义；
3. 保持无环的完整因果 DAG；
4. 四格交互、source-present 两臂 ITT、干扰潜在结果和时间优先性对象的严格区分；
5. H1–H4 的数学表达、观测量、证伪规则和 Unknown 处理；
6. D1–D10 对 P1 与 P2–P6 的决策依赖登记。

P1 不冻结具体平台、Source Event、Target Cohort、Region、Window、物理到达阈值、控制器对象、干扰方案、SESOI 或样本量。

## 7. D1–D10 的 P1 入口分类

| 类别 | 决策 | P1 处理 |
|---|---|---|
| 影响模型基本结构 | D2、D7、D8 | 在一般化模型中保留 source×strategy、整网分配和 adoption/action 层次；不把某一设计写成已批准 |
| 可由一般化模型暂保留 | D1、D3、D4、D5、D6 | 使用带索引、区间和删失的变量定义；明确可选平台、源、区域、物理状态和总体时间比较 |
| 主要属于后续阶段 | D3、D4、D5 的最终操作参数；D7 的最终随机化；D9 的 SESOI/n；D10 的资源出口 | 分别留给 P2–P6；P1 只记录识别条件和失败边界 |
| 需要研究者确认后才能冻结 | D1–D10 的实质方案选择 | 继续标记 `Proposed / Awaiting Researcher Decision`，不把推荐写成 `Agreed` |

逐项依赖、后果和推荐见 [P1_TASK1_DECISION_DEPENDENCY_REGISTER.md](../P1/P1_TASK1_DECISION_DEPENDENCY_REGISTER.md)。

## 8. P0 与 P1 的边界

P0 回答“已有工作覆盖什么、当前数据能否识别、最小设计是否可行”；P1 回答“在尚未冻结平台和参数的前提下，怎样用数学、DAG、estimand 和可证伪假设表达问题”。P1 的模型是研究设计输入，不是 Protocol Lock，也不授权 Stage I 或 Stage 1.1。

## 9. 依据

- [P0 Task1 最终报告](P0_TASK1_FINAL_REPORT.md)
- [P0 Task2 最终报告](P0_TASK2_FINAL_REPORT.md)
- [P0 Task2 双传播模型](P0_TASK2_DUAL_PROPAGATION_CAUSAL_MODEL.md)
- [P0 Task2 estimand 与干扰规格](P0_TASK2_ESTIMAND_AND_INTERFERENCE_SPEC.md)
- [P0 Task2 证据契约](P0_TASK2_EVIDENCE_CONTRACT.md)
- [P0 Task3 最终报告](P0_TASK3_FINAL_REPORT.md)
- [P0 Task3 研究者决策清单](P0_TASK3_RESEARCHER_DECISIONS.md)
- [Formal risk measurement](../../../code/src/riskprop/formal_risk_measurement.py)
