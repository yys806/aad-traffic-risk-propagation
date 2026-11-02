# Overleaf Alignment Audit

日期2026-11-02；项目AAD，先前连接器返回projectId=6aa63dcd249d9edf8228ca51，host=overleaf.com。本任务早段已分段读取main.tex、supplementary.tex及references.bib全文，未写入。当前工具集切换后原文缓存不可恢复，浏览器也没有已打开的Overleaf页，故下列是**本任务读取记录的审计**，不是提交时刻重新拉取的不可变快照；没有伪造hash、精确行号或完整句子引文。后续改论文前应重新读回并补快照hash。

位置使用已读章节/独特公式记号作定位；历史记录中的main.tex约361–420行包含物理多跳注释段，仅为辅助定位，行号未重新验证。原文栏仅引用实际留存的数学记号，其余是释义，不冒充逐字原文。references.bib先前读回217行；此数目不证明每个DOI都与当前定义一致。

| 研究内容 / 文件定位 | Overleaf当前定义或原文记号 | 当前科研定义 / ID | 差异类型 | 影响与原因 | 建议后续修改 | 状态 |
|---|---|---|---|---|---|---|
| Source Event/Risk；main.tex源事件及message lifecycle | η_ω^src：指定source-risk event | DEF-SRC-001区分ZS与S*、A与B | PAPER_OUTDATED（操作细节） | 事件资格不能由源风险标签推定；不表示现有source-risk概念错误 | 增source_type、资格和观察域 | Awaiting Researcher Decision |
| Source Onset；同上 | 未单列物理onset区间 | DEF-SRC-002 (LS,US] | NOT_YET_IN_PAPER | 确认前物理传播无法时间化 | 增末阴性/首阳性与左删失 | Awaiting |
| Source Confirmation；同上 | 事件正式成立的语义，未见独立tS,confirm字段 | DEF-SRC-003/event_confirm_s | PAPER_OUTDATED（细节） | 正式成立与物理起点可能混同 | 给确认条件及实现映射，不改阈值 | Awaiting |
| Generation；main.tex lifecycle | t_q^gen及后续发送/送达/采用时间 | DEF-INF-001资格≥确认；actual gen另记 | CONSISTENT + NOT_YET_IN_PAPER资格字段 | 现有顺序不等于资格完整定义 | 明确生成资格/实际生成不同 | Awaiting |
| Physical/Information；main.tex双图/physical connected | G^phy(t)、G^info(t)；物理多跳部分在注释草稿 | DEF-PHY-001及G_P/G_I | CONSISTENT方向；PAPER_OUTDATED操作 | 注释公式不是编译正文定义或已执行witness | 更新Methods时区分active/commented | Awaiting |
| Witness；main.tex physical connected | 未见Potential/Observed/Qualified三层 | DEF-PHY-002–004/W1–W9 | NOT_YET_IN_PAPER | 时空可达不等于实际或因果连接 | 增方向、身份、响应、竞争解释 | Awaiting |
| Physical response；main.tex物理隔离/响应段 | t_ω^phy-resp为行为响应候选；隔离情形可设+∞ | DEF-PHY-008/TIME-001为区域速度状态arrival | AWAITING_RESEARCHER_DECISION（对象映射） | 两者是不同量，现有证据不足认定同一量公式矛盾；+∞不能泛用于缺witness | 保留行为量，另说明区域TP及Unknown；不擅自重命名旧变量 | Awaiting |
| φ；main/supplementary methods | 未见active可计算φ | DEF-PHY-008 | NOT_YET_IN_PAPER | 目前不能复现arrival判定 | 批准后加入固定cohort速度状态与持续 | Awaiting |
| Speed；main.tex Stage II | u_v,t为速度 | Δu^B及均值下降；DEF-PHY-006/007 | CONSISTENT基量；NOT_YET_IN_PAPER新量 | 需要与pair closing speed区分 | B上标/适用域明确，采用前审核 | Proposal |
| Net Gap；main.tex Stage II pair公式 | g_t^(v'→v)表示净间距 | g保留给net gap | NOTATION_CONFLICT风险（Task2 g_v^mean映射） | 不同完整下标未必数学同名，但g复用易误读 | Task2历史保留，建议新稿用Δu^B；未正式Deprecated | Awaiting |
| Closing speed/TTC/DRAC；main.tex Stage II | Δu_t^(v'→v)、TTC、DRAC、pair车辆角色 | 沿用既有pair定义，B上标速度变化独立 | CONSISTENT既有语义 | pair角色/单位不能因arrival新增而改动 | 补code/config映射；本轮未逐公式重算论文 | Verified notation mapping; no equivalence claim |
| Formal rho/P2；main.tex风险定义/事件链 | ρ与风险事件；未完整列当前Formal P2配置阈值 | formal_risk_measurement.py与冻结配置 | NOT_YET_IN_PAPER实现细节 | 不能由论文读回断言实现/参数一致性已全证 | 显式列版本/配置，代码事实与候选定义分开 | Awaiting |
| Baseline；main.tex风险比较 | R^tgt,base为风险参考 | B_T为物理状态baseline | CONSISTENT不同角色；NOT_YET_IN_PAPER物理基线 | 用途不同不是已证NOTATION_CONFLICT | 两种基线分别解释，不能用F0作无扰动基线 | Awaiting |
| Cohort；main.tex target vehicles/eligibility | V_ω^tgt等预选目标对象 | 固定N及出区结构性不可用 | PAPER_OUTDATED缺失处理 | 处理后留存筛选/补位改变对象 | 明示full-cohort与observed统计及适用域 | Awaiting |
| Region/window；main.tex区域risk聚合 | source/target regions、early risk window | DEF-REGION-001固定空间/窗口 | CONSISTENT原则；细节待补 | cohort与区域双固定不总可实施 | 增处理前region版本、退出规则 | Awaiting |
| TR；main.tex early risk effect | δ^NL、T^prephy/L^prephy窗口 | P1全网格同时带/SESOI/持续定义 | PAPER_OUTDATED（P1统计对象尚未接入） | early contrast与effect onset不同 | 区分风险起点、动作响应、arrival | Awaiting |
| F0/No-message；main/supplementary | 未见显式F0及source-present arrival估计契约 | DEF-REF-001/002 | NOT_YET_IN_PAPER | 四格有无消息策略不能自动给arrival分布 | 增资格时序、ITT、censoring与总体对齐 | Awaiting |
| Censoring/Unknown；main/supplementary | 未见完整arrival事件时间分类 | DEF-CENS-001/002 | NOT_YET_IN_PAPER | 无观测不能写成+∞或未到达 | 增区间/右/左边界、Unknown及末端待确认 | Awaiting |
| Clock；main/supplementary | 未见offset/drift/step-phase误差契约 | DEF-CLOCK-001 | NOT_YET_IN_PAPER | 时间排序目前缺可审计误差界 | 增统一时间、区间传播和joint coverage | Awaiting |
| Temporal claim；main.tex信息/物理响应及early risk | 信息/行为响应比较；early风险辅助 | P1总体H*判据；禁止个体跨世界秒数 | AWAITING_RESEARCHER_DECISION；ASSUMPTION_CONFLICT/CLAIM_OVERSTATEMENT风险待原句复核 | 不凭没有全文快照的释义断定论文已经做出过度结论 | 后续逐句核查效应层级、总体与联合界；未证实的冲突不标Verified | Pending re-read |
| supplementary.tex data-role table | NGSIM/pNEUMA/SPMD/SUMO高层数据角色 | H1–H6沿用边界 | CONSISTENT高层 | pNEUMA不承担恢复leader/TTC | 保留并补可追溯证据 | Read evidence |
| supplementary.tex methods/calibration | 部分方法/校准位置仍为placeholder | Task3定义/参数/统计Proposal | NOT_YET_IN_PAPER | placeholder不等于已采用推荐 | 研究者审核后另任务填写 | Awaiting |
| references.bib | 已读书目文件，不含本轮完整新增方法链 | L8/L10–12/L14/L15见文献审计 | PAPER_OUTDATED候选书目 | 本轮不直接编辑bib；不能暗示新文献已入论文 | 后续按实际采用内容引文，不盲目加所有文献 | Awaiting |

## 冲突治理与证据限制

差异类型CONSISTENT/PAPER_OUTDATED/NOT_YET_IN_PAPER/NOTATION_CONFLICT/MATHEMATICAL_CONFLICT/ASSUMPTION_CONFLICT/CLAIM_OVERSTATEMENT/AWAITING_RESEARCHER_DECISION均为可用枚举；本次没有足够证据将某项标为Verified MATHEMATICAL_CONFLICT。缺项不是自动数学冲突，不同baseline不是自动重名。

Documented Intent：P1总体风险效应应先于普通物理到达。Actual Implementation：当前无Formal A合格源/独立Qualified witness/F0，论文行为响应记号不能替代这些证据。Evidence：P1 §7、P2Task2、Task20、上述本轮论文读取记录。Affected Files：本审计、definitions、后续Overleaf main/supplementary/bib。Conflict：定义与论文/实现接线未闭合；Status：Awaiting Researcher Decision。没有覆盖论文或改写其结论。

提交前精确源文件hash及原句/行号复核仍未完成（专用连接器在当前工具集缺失）；该限制影响审计可复核粒度，不抹掉先前完整读取，但不得写成最终论文一致性全部验证通过。

## 新增主张范围风险（B域证据，不改论文）

| 研究内容 | Overleaf当前定义 | 最新科研定义 | 差异类型 | 影响 | 建议后续修改 | 状态 |
|---|---|---|---|---|---|---|
| main.tex early/prephysical主张，具体原句待重读 | 先前记录包含信息/物理响应和early risk比较；不伪引原句 | DEF-PHY-008/CORE细则F只测指定cohort阈值状态 | ASSUMPTION_CONFLICT / CLAIM_OVERSTATEMENT风险，非已证原句错误 | B中region内中间车辆先响应而cohort未报警；此T_P不能排除任意普通物理影响 | 后续核实原句、对齐risk/arrival支持域并明确限定claim；若保持强主张则补排除证据 | Awaiting Researcher Decision / Pending re-read |

Documented Intent：在普通物理影响之前识别独立信息策略效应。Actual Implementation：新检测器只验证固定cohort指定阈值速度状态，B60run均无报警。Evidence：B scope_audit及E26–E29。Affected Files：CORE、参数/决策/结果、本审计及未来论文。Conflict：状态未触发不等于任意物理机制未进入区域。Status: Awaiting Researcher Decision。此登记不授权改论文或研究目标。
