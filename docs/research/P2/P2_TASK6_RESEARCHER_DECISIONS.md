# P2 Task6 — 研究者集中决策记录

日期：2026-11-02。授权来源：研究者本次 P2 Task6 任务书 D1–D7。统一定义入口：[README](../definitions/README.md)。

本文件记录研究者决定及待决事项，不创建第二套科研定义。方向接受不等于数值、估计器、实现或实验启动获准；本任务只设计，不运行新的 SUMO/TraCI、Pilot 或校准。

## 1. 已确认方向（Agreed）

| ID | 已确认内容 | 尚未冻结的范围 | 对 Task5 的覆盖关系 |
|---|---|---|---|
| D1 | Micro、Macro、Cohort 分别报告；Micro 沿用 W1–W9 与 Potential/Observed/Qualified；固定 Cohort/Region/Window，signed baseline-relative speed decline 不独自排除全部区域物理影响 | 层内检测器、质量门、数值、具体算子、机制覆盖和标签规则 | 接受 T5-D1 分层方向，不接受机械 OR/AND 标量 |
| D2 | 同向分车道 Edie-type 作为 Macro 主要候选；同域累计实际车距 D、车时 V、面积 A，q=D/A、k=V/A、u=D/V；V=0 时 u undefined | 区域/窗口/空间与时间分辨率、状态阈值、持续、抽样机制与适用域 | 接受 T5-D2 测量方向；不是宏观数值验证 |
| D3 | Qpre 后随机 ZC 的 Source-present 两臂 ITT 与 Source×Communication 四格交互为不同 estimand；不改变已有随机化矩阵 | 四格共同资格、非 Q 支持、源前 opportunity、随机单位/干扰/正概率的实际落实 | 接受 T5-D3 识别边界；不添加 principal-stratum 识别假设 |
| D4 | 同时记录实际 onset、首次阳性观察、confirmation、availability、完整消息生命周期、动作和风险时间；保留删失/Unknown，offset、drift、step phase 分开 | t_E 的最终映射、时间误差数值、各层独立延迟界 | 接受 T5-D4 时间区分；不改变 Formal P2 确认规则 |
| D5 | 先科学下限，再固定其他参数逐项实验，最后关键交互及独立验证；选择稳定参数区域 | 科学损失容忍度、SESOI、H*、η、预算、数值参考配置/候选与样本量 | 接受 T5-D5 分阶段原则；不恢复 V1 撤回值，不把 V2/B 网格写成交通范围 |
| D6 | 沿用 P1 总体早窗、Risk ITT 全网格同时带、同资格 No-Message 分层 CDF 识别界与联合错误控制；Unknown 保留不确定性 | 具体估计器、检验族、误差分配、结果范围与测量漏检界 | 接受 T5-D6 保守方向，不自动接受特定概率模型 |
| D7 | 本次不修改 Overleaf 正文；只登记一致性差异和未来修订范围 | 后续论文集中修订须另有研究者授权 | 覆盖 T5-D7 的立即改论文建议；本次 main/supplementary/bib 均不改 |

## 2. 证据与科研权限边界

- Fact：正式 A 源事件 0、独立 Qualified source→cohort Witness 0；F0 与总体 TR/TP 未验证。Task3 V2/B60 仍为测量/校准域，不能用于正式效应结论。
- Agreed：本节 D1–D7 的研究方向；不由文档完成升级任何数值或科学证据。
- Proposal / Awaiting Researcher Decision：最终协议中的具体技术推荐与集中科学选择。
- Unknown：没有独立真值、代表性交通 null 或风险方差等支持的数值。缺失不补零。
- Stage 0.5 CLOSED_WITH_LIMITATIONS；Stage 0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock BLOCKED；Stage I READY_ENGINEERING_ONLY；Stage 1.1 NOT_AUTHORIZED，均保持。

## 3. 一次性完整待决清单（全部为Proposal，未自动Agreed）

只有“校准前必需”事项影响下一参数实验启动；其余按所列阶段冻结，不以完整四格、正式风险SESOI未知无限阻塞测量校准。无新Task6.1/6.2。这里是集中科学选择，技术manifest/数值计算由执行者在下一实验内完成。

| ID / 待决科学项目 | Codex最优推荐 | 依据与反对证据 | 尚存Unknown / 替代及科研后果 | 必须冻结时间 / 下一阶段影响 |
|---|---|---|---|---|
| T6-R1 测量对象、主算子、时间映射及scope | 分层已Agreed；具体推荐Micro首版同lane纵向链、Macro同域速度下降主候选且q/k补充、Cohort full-N等车signed mean且median/比例辅助；t_E用物理onset允许区间，confirmation仅资格/信息轴；固定region/lane/cohort/观察域 | Task3区域/cohort反例；Hall支持不同测量对象；W1–W9；P1时序。反对：均值可抵消异质变化，Macro会稀释，严格W6漏近同步边；均无普适最优证据 | 具体区域/机制/边界Unknown。替代median/比例会改变群体对象；confirmation轴丢确认前传播，宜只敏感性；复杂交互需独立真值不能默认并入 | 对应层校准前必须接受具体对象/边界/算子/映射；不需再批准D1/D2方向 |
| T6-R2 科学损失、真值最小范围和稳定标准 | SAC面向早窗首选审阅event FPR≤1%、FAR≤1%、power90%，及时漏检m_delay≤η/4、Unknown≤η/4（η=1%时timely sensitivity≥99.75%、Unknown≤.25%，均Proposal）；独立物理a*/b*/误差界、绝对d*与ε_stab/γ_int需按科学后果填定；d*≤.1H*仅H*可用时的预算Proposal | 数值是审慎损失方案，不是文献交通经验；B无阳性，V2不识别交通损失。代价：严格FPR/recall需大量独立n；95%灵敏度或Unknown5%的证书都不足以支持η1%，还须为真实早期到达质量和统计界留余量 | 替代一般测量档FPR5%/sensitivity95%或90%/Unknown5%或10%/power80%、d*≤.2H*降低资源，但只能给相应状态测量推荐，不能冒称支持η1%的真实到达上界。a*/b*不能用θ/h反定；任意微小变化不可保证。正式H*未知可先固定独立H_cal和绝对d*，不冒充正式早窗 | 校准选参前必须接受损失/truth/d*/稳定性；无标注证据保持Unknown，不靠新前置任务解决 |
| T6-R3 统计主方法与联合错误控制 | 主用允许时间集合/CDF保守界+有界Risk ITT全网格同时带；正式α=.05，R/P/clock/measure=.02/.02/.005/.005为推荐Proposal；β_V与正式证书失败预算分开，主V按实际J_V Bonferroni；确定性界不消耗概率 | P1和Hoeffding有清楚充分条件，源码已有[0,1]贡献及定长积分界。反对：保守到样本量很大；真实簇/不均分配不适用简单iid式；方法存在不等覆盖已验证 | 可选cluster max-t/设计相容bootstrap但需独立覆盖/矩条件，不默认取代。最终randomization/独立单位/family/风险聚合仍Unknown；不截断DRAC | 校准前冻结β_V/单位/family；用于正式早窗前再冻结联合α与实际估计器，不能拿.05验证证书假装.005测量保证 |
| T6-R4 正式早窗科学值（不强迫现在猜数值） | η首选1%、资源替代5%仅损失情景；H*按独立物理范围/观察能力预定；δ按P1既有风险积分原单位的实际科学后果确定，附δ/L解释；网格/风险持续规则预定 | P1既有框架，无F0/风险价值/方差或A onset证据。反对：η1%与可观测Unknown不相容时再大n也无用，不能以文档猜H*/δ | H*/δ/备择gap/最终正式n仍Unknown。更大η允许更多普通物理到达；更长H*改变对象/多重族；更小δ可能科学意义不足。不得从TR<TP或p值反选 | 正式风险/总体早窗前必须冻结；只做测量校准可保留Unknown，先接受独立H_cal/d* |
| T6-R5 四格共同资格与政策支持 | 当前Qpre两臂为合格通信效应入口；最终四格保留，在共同源前opportunity总体另审完整政策/positivity；不默认principal-stratum点识别或跨Q运输 | F–R潜在成员不可见；τSC分解缺τ_nonQ/τ_S0；formal_design只是配置/日志契约。反对：源前opportunity是不同资格，需明确目标；来源若非随机四格仅情景对比 | 替代principal-stratum只能在额外明确接受的识别/敏感性假设下研究；不能填0、事后筛样、用seed补齐。本任务不改变矩阵、不接受新增假设 | 后续四格因果分析前必须选择并有支持；不阻塞独立参数测量校准或资格两臂设计 |
| T6-R6 校准域、验证资源与执行授权 | 按协议三密度、两类null、有限truth-positive/归属对照；探索≤576计划单位为Proposal，大量参数在同raw离线重算；验证n由精确power/族求，按run/最大依赖block，独立新V只一次 | 复用raw可降成本，依赖矩阵代全积。反对：现有标签不能保证全部格可实现，探索24/格非有功效；跨场景推广需新独立场景而非更多帧 | 具体安全场景/基准需求/seed命名空间、资源cap和实际n待下一实验启动manifest。若cap不足，报告精度不足，不能调松标准后声称原验收通过 | 本次无运行；下一实验一次接受范围/资源并授权后，直接执行现成协议；不启动Stage1.1/正式Gate |

已接受D7不再待决：本次不修改论文。未来Methods需资格/ITT/三层测量/clock/统计接线，Results需待真证据、保持A0与Unknown，Discussion需有限scope/迁移/个体反事实限制；任何正式文字另获授权。

## 4. 数值仍Unknown的完整原因分组

- Cohort：W/model/θ/h/q/c/recovery/hysteresis与missing界无交通null+独立目标positive联合验证；V1撤回值不恢复。
- Micro：反应窗、响应强度、gap/closing/clock质量、ID/leader缺失和归属能力无完整独立Qualified链真值；框架Agreed不是质量数值已定。
- Macro：区域/lane/w/Δx/Δt、状态θ/持续、sampling/coverage与归属无独立全域标签；未知p_i不外推全交通，V=0速度undefined。
- 科学/统计：a*/b*/d*/ε_stab/γ_int、δ/H*/η/α分配、最终randomization/独立n/power依赖科学损失和真实数据。已有源码范围可推，但最终Y聚合/窗口未接受；DRAC上界不得猜。

## 5. 审核后直接执行及状态

[协议](P2_TASK6_PARAMETER_DETERMINATION_EXPERIMENT_PROTOCOL.md)已覆盖标签/矩阵/参考/单因素/交互/robustness/样本量/split/指标/统计/停止/复现/冻结和结果格式。先一次填定R1/R2/R3的校准项与R6授权/预算，执行者在同一参数实验内生成具体候选manifest、跑校准、冻候选、新V、推荐稳定区域；R4正式风险值与R5四格支持在使用它们的阶段前冻结，不新增设计任务。

本任务完成状态是DESIGN_COMPLETE_WITH_LIMITATIONS，不是科学假设成立。Gate/Protocol/Stage1.1原状态保留；实验是否可无条件立即运行：否（本次禁止运行，启动科学项与授权尚待研究者）；是否需要额外实验设计任务：否。
