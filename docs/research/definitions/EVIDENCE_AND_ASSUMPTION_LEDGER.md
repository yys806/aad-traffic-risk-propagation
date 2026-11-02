# AAD Evidence and Assumption Ledger

版本AAD-SCI-DEF-20261102-P2T4-v0.2。类型严格区分Fact、Inference、Hypothesis、Proposal、Agreed、Unknown；证据资格不由任务状态自动提升。L编号见Task3文献审计；H编号为历史复用矩阵；V为本轮测量校准，不是正式因果证据。

| ID | 判断 / 关联定义 | 类型 | 可追溯来源 | 适用范围 / 局限 | 状态 |
|---|---|---|---|---|---|
| E01 | 源A/B分离，Formal A源0；SRC-001 | Fact+Agreed方向 | H2/H3、Task20；formal_risk_measurement.py | SUMO当前；NGSIM计数不可迁移 | Verified |
| E02 | onset/确认/生成资格不同；SRC-002/003、INF-001 | Inference+既有约束 | P2 Task1/2、event_confirm_s、P1生命周期 | onset选为tE仍Proposal；无端到端资格执行验证 | Awaiting |
| E03 | 固定cohort/region/window；COHORT/REGION | Agreed | P1 D4、当前Task3明确确认方向 | 不等于批准所有缺失规则 | Agreed方向 |
| E04 | 主方向为固定cohort持续baseline-relative有符号速度下降；PHY-006–008 | Agreed方向 / Proposal算子 | 当前任务§4.1；P2Task2 | 研究者确认方向；mean算子和参数仍待审 | 分层登记 |
| E05 | 均值首候选，median/比例辅助 | Proposal | V2对照、目标量分析 | 不是普遍经验最优；同一数据不同目标 | Awaiting |
| E06 | g保留net gap，ΔuB替代临时速度符号 | Proposal | Overleaf StageII留存记号、SYMBOL_REGISTER | 无正式Deprecated，无论文修改 | Awaiting |
| E07 | 微观方向与宏观波前不同；PHY-001–004 | Inference / 既有理论 | P1/P2、L1–4、L8实际预印本 | 波图连通不证明leader-follower因果 | Supported direction |
| E08 | W1–W9逐跳准入 | Proposal | P2Task1/2、L8；H3=0 | 质量规则未冻结；模型内witness非现实因果 | Awaiting |
| E09 | 区域外成员是结构性不可用；PHY-007/COHORT | Inference | 固定集合与空间定义、P1 D4 | 不能以插值/缺失界虚构留区；实际适用域待定 | 明确限制 |
| E10 | observed-subset均值不是固定N全体量 | Fact（代数） | CORE细则B；固定分母公式 | 需完整或可辩护缺失模型；coverage不修复MNAR | Verified identity |
| E11 | baseline与F0不同；PHY-005/REF | Fact（定义） | P1/P2Task2 | no-message有源可能已含物理传播 | Preserved |
| E12 | confirmation前物理传播可能开始 | Inference | 两链因果/时间定义 | 不是当前A已观测事实 | Proposal锚点依据 |
| E13 | Qpre子总体F0Q不自动等于全部ZS=1 F0 | Fact（条件概率） | CORE细则D、P1 estimand | 通信前资格支持subset ITT，非源assignment全集 | Identified boundary |
| E14 | 关闭通信不等于无源/发送失败 | Agreed / Fact定义 | P1/P2Task2 | ZC=1交付/验证/采用失败保留ITT | Preserved |
| E15 | 同seed不保证跨策略实体随机性一致 | Inference | L11官方多RNG；分支机制 | 相同输入重复性不等于反事实识别 | Supported limitation |
| E16 | right/interval/Unknown不可混用；CENS | Fact / Proposal估计器 | P1 §8、L14全文 | L14不解决信息性缺失；速度恢复需全段日志 | Boundary preserved |
| E17 | 时钟/采样/统计误差应分别传播；CLOCK | Proposal | L15章节、P2；Task18phase | 无AAD offset/drift数值验证 | Unknown values |
| E18 | 总体早窗用共同目标域和联合覆盖 | Proposal操作化 / Agreed方向 | P1 §7；CORE细则E | 不是每事件TP下界；η/δ/alpha/H*未定 | Awaiting |
| E19 | V1存在持续多算dt、TP误分类、无独立验证 | Fact | 原输出/SUPERSEDED_V1.json及原脚本快照 | 不再支持任何数值推荐；保留原失败 | Withdrawn diagnostic |
| E20 | V2 768面板、42候选、32256评估、1344汇总 | Fact | code/outputs/calibration/p2_task3_20261102_v2/config/summary/provenance/SHA256SUMS；便携evidence/research/P2_TASK3_20261102 | 合成测量；无交通/路径/消息真值 | CALIBRATION_ONLY |
| E21 | V2趋势null中参考配置24/24报警 | Fact观察 / Inference归属限制 | V2 validation/null_trend，θ.5 h1 W5 q1.1dt | 速度真实下降不是数值错测，但无源时不可归属物理传播 | synthetic only |
| E22 | AAD交通参数无法由V2唯一确定 | Inference | V2域、H1–H6、缺独立A标签 | B域只支持本域 operating range，不跨A迁移 | Unknown/Proposal |
| E23 | 核心科学假设：可采纳消息改变区域风险且先于物理到达 | Hypothesis | P1 H1–H4 | 当前无因果效应或时间分离证据 | Unverified |
| E24 | 论文已有行为响应记号但缺F0/状态/删失系统 | Fact（本任务先前读回） | OVERLEAF_ALIGNMENT逐项位置 | 当前原文快照不可恢复，未复核精确行/原句/hash | Limited audit |
| E25 | NC级结论当前存在独立arrival/风险识别接线缺口 | Inference | E01/E13/E18/E23/E24 | 不等于假设被证伪或创新性已证明 | Unresolved blocker |

## B域新增事实与主张边界

| ID | 判断 / 关联定义 | 类型 | 可追溯来源 | 适用范围 / 局限 | 状态 |
|---|---|---|---|---|---|
| E26 | 60run工程PASS，2520候选均无报警 | Fact | B run_audits/calibration_summary/measurement_audit/provenance/SHA；便携controlled_B_summary | 独立CALIBRATION_ONLY，不是Formal A或F0；候选不算独立n | Verified controlled_B_sumo |
| E27 | region内s1–s4有响应候选、cohort无报警 | Fact观察 | scope_audit/response_locations.csv、来源轨迹SHA；Task3结果§5 | 描述性例，单车阈值规则非Qualified；非现实因果 | Verified model record |
| E28 | phi=0不能排除任意普通物理影响进入region | Inference | E27、DEF-PHY-008、CORE细则F | 小幅/非cohort/gap/density可早于主状态；影响核心claim | Awaiting Researcher Decision on scope |
| E29 | 先限制为指定状态主张并对齐risk/arrival支持域 | Proposal | E09/E10/E13/E18/E28 | 更强物理排除需要额外证据；不擅改P1或论文 | Awaiting |
| E30 | B无阳性不足以校准θ/h/q；停止不追阳性 | Inference | E26；B预定协议、θ≥0.25、峰值mean≤0.028063 | 不证明A无传播或假设失败；无最佳阈值 | Unknown numeric parameters |
| E31 | JSS原文及双语已导入，五新增来源已建 | Fact | Zotero QUH3LUP3/TIWGTN2S/4TMXFKYB及文献审计§5 | 非全部旧文献全文精读；未返回指标仍Unknown | Verified local API |

## 参数 / 证据映射

θ/h/q/W/coverage/恢复→PARAMETER_REGISTER各行及V2；B域输出和后续结果表另见Task3校准结果。所有Definition ID的文献/实验/假设字段已在CORE逐项列出，不另设竞争定义。参数表中的探索网格不是Agreed值，标准化阈值未测试。

## 关键假设及失败条件

A1身份/时钟/道路坐标足以判定方向；失败→Unknown。A2预定窗口内全cohort存在区域支持；退出→结构性不可用，不能删人。A3基线无源预兆且趋势模型在处理前拟合；失稳→重设适用域或Unknown，不事后调到有利结果。A4随机化单位独立或按已定义干扰簇处理；帧/车行数非n。A5F0与风险曲线使用同一资格总体和H权重。A6删失/inspection假设有审计证据；不成立→界限/敏感性，不机械KM。A7微观path和速度状态各自独立合格；一方不能补另一方。A8B与A迁移需额外动力学/交通背景/测量等价性，当前未证。A9同时带和clock联合覆盖控制总体错误；点wise CI不能替代扫描。

上述为待检验识别条件或Proposal，不统一标Agreed。科研结论保持Unknown，Gate与阶段不变。

A10（新增范围限制）：指定阈值速度状态与“任意物理机制进入region”不可等同。强主张需独立排除证据；当前该条件未满足，见E27–E29。

## Task4研究者接受记录（覆盖同事项历史状态）

| ID | 当前判断 | 类型 / 状态 | 日期与直接来源 | 适用范围与未决边界 |
|---|---|---|---|---|
| E32 | A 有限且独立可验证物理观测域下研究时间优先性 | Agreed | 2026-11-02，Task4任务书§四A | 接受E28所指出范围限制，不主张排除全部机制；不是实证支持 |
| E33 | B W1–W9微观框架+宏观区域状态双层测量 | Agreed方向 | 同日§四B | cohort指标不单独排除；证据融合、数值与新macro定义仍Proposal |
| E34 | C communication-blind Qpre后随机ZC，资格子总体ITT/F0 | Agreed | 同日§四C | risk/F0同支持，四格保留，不能用该子总体代全ZS=1；不按处理后链路/Witness筛选 |
| E35 | D P1预定H*、同时带/arrival上界和联合错误控制 | Agreed原则 | 同日§四D、P1 Estimand§7 | 非个体提前秒数；δ/η/α等数值及具体估计器未定 |

E08的W1–W9框架继续使用方向已被E33接受，逐条操作质量条件仍Proposal；E18/E29的原则层由E32/E35更新，不追溯改写Task3。E13的子总体不等同边界继续成立。


## Task4直接证据与推断增量

| ID | 判断 | 类型 | 来源、数据/代码/报告 | 边界 / 状态 |
|---|---|---|---|---|
| E36 | Jerath已完成信息→车辆控制→宏观延误及ZOI映射 | Fact | 2024期刊正文§3–6；ZAHRLZ56/HSQNJHQL；Task4 paper note | 模型结果，非AAD风险ITT或随机F0；Verified reading |
| E37 | Saberi宏观拥堵contagion、Duan早期预测已有先例 | Fact | 两篇期刊正文/Methods；YA2ACMZV、5DE6L9RS；Task4 notes | 物理传播/预测不等于信息干预；不构成首次排他检索证明 |
| E38 | Zhang正式六作者、现有附件四作者SSRN；正式全文未取得 | Fact / Unknown | DOI元数据、TDM coredata、CLA3GKSX SHA及Task4版本表 | 正式方法/数据/结论变更Unknown；PARTIAL_READ |
| E39 | 宏观时空交通状态算子应明示支持/部分穿越与抽样 | Proposal / Inference | 官方Hall章§2.1–2.2，Zotero26RQQ7EE；DEF-PHY-009 | Edie1963原文未取得；未验证AAD数值 |
| E40 | τQ不自动等于四格τSC；Q(1)在无源臂潜在不可见 | Inference | P1 Estimand§2/3/7；CORE细则I全期望分解；P0 interference审计 | 数学分解非经验识别；跨源principal strata仍未决 |
| E41 | 当前论文post-treatment整组筛选与主时间分析不对齐Agreed C/D | Fact（文本）/Inference（后果） | Overleaf 2026-11-02快照main676、1033–1053；Task4论文审计 | 保留原文，不自行改论文结论；Awaiting revision decision |
| E42 | 消息生命周期+实际采用/动作+区域风险ITT+独立F0联合证据可能有差异 | Hypothesis / Proposal | 最近邻矩阵、P0相关工作及Task4创新性审计 | 未发现完整覆盖组合不等于不存在；AAD尚无合格A/witness/F0，不称NC创新成立 |
| E43 | Task4当前Overleaf三文件字节快照已取得并审计 | Fact | 快照时间/hash见P2_TASK4_OVERLEAF_AUDIT.md；只读下载 | 覆盖Task3快照缺失限制；不追溯改写Task3记录 |

E32–E35为四项研究者接受方向；E36–E43不因此成为新的Agreed科研结论。当前Formal A=0、独立Qualified Witness=0、F0/TR/TP仍Unknown，Gate不变。
