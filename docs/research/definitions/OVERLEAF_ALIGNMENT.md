# Overleaf Alignment — Current P2 Task6

版本：AAD-SCI-DEF-20261102-P2T6-v0.4；日期2026-11-02。Task5新取得同一AAD项目三文件快照，UTC 2026-11-02T10:07:46.887013+00:00；ZIP SHA256 7545186b7d040ea407432a7cdd8693846d24faf3d37457af7c6e5621265cf39b。三文件字节/SHA与下方Task4快照相同，故旧逐项位置继续有效，但Task5具体Proposal为本段增量，未在论文中采纳。

[Task5完整差异表](../P2/P2_TASK5_OVERLEAF_AUDIT.md)给出文件字节、物理行号与审计范围。当前研究方向Agreed A–D不等于论文已修改；本任务无Overleaf写入。

| 位置 | 当前论文内容 | v0.3当前科研定义 | 差异类型 | 建议 / 状态 |
|---|---|---|---|---|
| main323–367 | directed chain与区域首车响应 | DEF-TIME-004独立micro/macro/cohort时间族 | AWAITING_RESEARCHER_DECISION / NOT_YET_IN_PAPER | 保留行为对象，待决主arrival；不机械OR/AND |
| main323–367及区域risk段 | 无Edie同域量 | 细则K的D/V/A、lane裁切与operator onset限定 | NOT_YET_IN_PAPER | 补可复算支持，具体公式/窗仍Proposal |
| main673–676 | 实际匹配/四臂QC后整组筛样 | 细则M通信前Qpre，ITT保留处理后失败 | ASSUMPTION_CONFLICT | 先改资格/缺失设计，再改论文；T5-D3 |
| main871–950 | 全体四格interaction | τQ与τSC分解及缺失支持 | NOT_YET_IN_PAPER | Qpre不对ZS共同前定，不用principal名称掩盖识别 |
| main1033、1036 | treated行为主时间，无消息sensitivity | 细则O/P风险同时带、同资格F0主参考 | MATHEMATICAL_CONFLICT / ASSUMPTION_CONFLICT | 主分析对象需实质调整，待另授权 |
| main1134–1136 | early risk与窗validity | 允许集合、Unknown保守界、H*/SESOI、joint错误 | PAPER_OUTDATED / NOT_YET_IN_PAPER | 估计器/检验族仍Proposal，不能写已验证 |
| main87/90/96与references.bib | 强排除措辞，Zhang正式版尚未纳入 | Agreed有限机制范围；正式版事件图非独立因果识别 | CLAIM_OVERSTATEMENT风险 / NOT_YET_IN_PAPER | 引入最近邻、检测范围与联合识别待验证边界 |

## Historical — Task4快照与逐项审计（同字节，继续提供原位置证据）

# Historical Task4 Alignment

版本：AAD-SCI-DEF-20261102-P2T4-v0.2；日期2026-11-02。当前审计取代下方Task3有限快照状态，保留历史，不修改任何Overleaf文件。

## 快照、范围与定位

通过已有合法登录的Edge打开当前AAD项目，使用项目列表Download .zip file只读下载。项目标识：6aa63dcd249d9edf8228ca51；获取时间2026-11-02T08:20:35.613795Z（16:20:35+08）。下载AAD.zip SHA256=3af7b76b05e089bd883a5d5dacc3c0fe83dcb5422b818c70111a4d7c8f7b8760。仅提取三文件到被Git排除的local_research/literature-work/p2_task4/overleaf_snapshot/，作为隔离审计快照，不恢复仓库活动论文编辑流程。

| 文件 | bytes / lines | SHA256 |
|---|---|---|
| main.tex | 213343 / 1759 | 0d8951f34ea64db6b2d3d8489bc119d47166088a3c2ef04e0416cb5753e15225 |
| supplementary.tex | 6892 / 254 | 79c3b5da82c25e02d900a60721375fe6a3eb44bd91acdc3c7c119bd64af9171d |
| references.bib | 8111 / 217 | 1e4738af5d7ab115ca9ea38daa6a091d75e723e7f3395aa907e37ebf7d063904 |

活动正文、公式、补充材料和全部bib已分段读完；导言与相关中文注释亦核查，未逐项审校所有历史注释或所有被引文献。行号为此字节快照1-based物理行，不保证后续Overleaf编辑后稳定。表中短引号为原文短片段，其余为释义；不是论文已经产生实证结果的判断。PDF/HTML/tex原文不入便携证据。

## 当前逐项对照（正式差异入口）

| 研究内容 / Overleaf文件位置 | 当前论文表述或定义 | 最新科研定义 | 差异类型 | 影响 / 冲突原因 | 建议后续修改 | 状态 |
|---|---|---|---|---|---|---|
| 核心主张；main80、87、90、96 | “after excluding ordinary physical propagation”；before ordinary influence | Task4 A / DEF-SCOPE-001：有限预定义且可独立验证物理域 | CLAIM_OVERSTATEMENT / ASSUMPTION_CONFLICT | 若读为排除任何影响，超出可观测支持；有限阴性不支持全称命题 | 加空间/时间/机制/检测能力限定，列未观测机制 | Agreed方向；论文修订待授权 |
| 创新表述；main84 | “a directly attributable link … has not been established” | E36–38/E42：已有信息→动作→macro先例；联合风险证据候选未证 | CLAIM_OVERSTATEMENT风险 | 绝对不存在/首次主张不能由有限检索支持；Jerath与Peng需直接比较 | 限定具体联合缺口，增加最近邻而非泛称已有控制不足 | Awaiting Researcher Decision |
| 四格分配；main614–628 | scr/opn四格、treatment≠event/execution | P1 τSC、ZS/S*/ZC/C* | CONSISTENT | 既有assignment语义可保留 | 显式code/变量映射 | Verified text |
| Formal P2/rho；main247、294–300 | 风险映射/事件规则待lock，未列全部当前正式配置 | 既有正式测量与DEF-SRC-001/003 | PAPER_OUTDATED / NOT_YET_IN_PAPER | 不能称论文已采用当前TTC/持续参数；无证据说明公式相等 | 补实现版本与仍待lock的范围；不更改Formal定义 | Awaiting |
| pair / net gap / TTC / DRAC；main188–215 | ordered vehicle pair；g为net gap，Δu为闭合速度 | SYMBOL_REGISTER保留原语义 | CONSISTENT | 新arrival不能改变这些量的符号与单位 | 新速度偏差保持B上标与车辆索引 | Verified mapping |
| Source onset/confirmation；main294–300 | t_src-int为处理起始，t_evt为首次正式成立 | DEF-SRC-002/003：真实物理crossing区间与确认分开 | NOT_YET_IN_PAPER / PAPER_OUTDATED | intervention计划/启动不保证实际onset；确认前已可传播 | 加实际onset区间与时钟，保留确认 | Awaiting细则 |
| 消息资格；main300 | 事件正式成立后才eligible to generate | DEF-INF-001 | CONSISTENT | 资格不等于实际gen时间 | 加独立eligibility字段 | Agreed约束 |
| directed physical graph；main323–332 | 动态有向图，潜在交互边 | DEF-PHY-001/002 | CONSISTENT方向 | **活动正文已存在**，Task3“主要在注释”描述不再准确 | 保留并增candidate/observed/qualified区分 | Task4已纠正读取事实 |
| 微观传播；main344–360 | 实际变化/响应、有序链；区域最早可归属车辆响应 | DEF-PHY-003/004 W1–W9 | CONSISTENT部分 / NOT_YET_IN_PAPER质量门 | topology不是充分证据；现有对象为micro，不同于cohort阈值 | 加身份/关系/clock/竞争解释与逐跳质量日志 | Framework Agreed；细则Proposal |
| phy-resp与TP；main344–367 | 区域任一车辆最早实际物理响应；结构隔离可+∞ | DEF-PHY-008是cohort速度状态；DEF-PHY-010分层 | AWAITING_RESEARCHER_DECISION（对象映射） | 不同量，不能直接当同一个量而称数学矛盾；缺witness不可+∞ | 保留行为量与cohort量，另声明主arrival endpoint | Proposal |
| 双层macro；main323–367、区域risk段 | 未见Edie型速度/流/密度及micro/macro独立质量体系 | Task4 B、DEF-PHY-009/010 | NOT_YET_IN_PAPER | cohort阴性不能排除region其他响应 | 补macro支持域、覆盖和冲突表；不机械OR/AND | 方向Agreed，算子Proposal |
| φ与速度下降；main/supplementary全活动正文 | 未见可计算cohort baseline-relative持续φ | DEF-PHY-006–008 | NOT_YET_IN_PAPER | 未建立可复现arrival参数；不是将Formula rho重写 | 批准后列算子及未知数值状态 | Proposal |
| g符号；main193及Stage II pair | g_t^(v′→v)为净间距 | 速度下降Δu^B候选，Task2 g_v历史映射 | NOTATION_CONFLICT风险 | 不是同一完整记号的已证重定义，但复用g易误读 | 保留g净间距；新记号需确认，未改论文 | Awaiting |
| target cohort；main266 | 预先固定，不按后续采用/响应选成员 | DEF-COHORT/REGION、Task4 C | CONSISTENT原则 / PAPER_OUTDATED缺失 | 固定区域不自动保证固定车辆全程在区；缺失不能重分母 | 加退出结构性无定义、coverage与missing bounds | Awaiting细则 |
| lifecycle；main442–461 | gen/send/del/adopt，保留未送达 | 完整generation→delivery→verification→adoption | CONSISTENT部分 / NOT_YET_IN_PAPER verification | 送达不等于验证、实际采用；失败留原assignment | 加verification状态/clock/unknown，不按失败剔除 | Agreed ITT方向 |
| 动作链；main483–501 | adoption→command→actuation→motion→risk | TU≠TR；实际动作证据 | CONSISTENT | 轨迹变化不能自动归属信息 | 保留可审计链；日志不证明自然中介效应 | Verified text |
| Qpre与纳入；main673–676 | 四格matched unit，要求(1,1)/(1,0)源匹配和四运行质量有效，不合格整组排除 | Task4 C / DEF-POP-001：通信前盲资格后ITT | ASSUMPTION_CONFLICT / PAPER_OUTDATED | 通信后的实际匹配/质量筛选可能选择处理后变量；预规定不保证无偏；source-absent无同一实际Q | 入组与处理后缺失分离，保留ITT/Unknown；分开τQ与τSC | 实质修订待研究者；未改正文 |
| 公共时钟；main680 | 以(1,0)的t_evt给配对四格共同索引，并明确无源臂不代表真实事件 | onset/确认独立；模型公共比较索引可预定 | CONSISTENT其索引限定 / AWAITING_RESEARCHER_DECISION外推 | 模型配对可用此索引，但不是source-absent真实onset或独立现实事件的个体反事实 | 保留原限定，审计配对/clock映射与确认前物理段 | Awaiting实施 |
| baseline；main684–706 | T_base=[t_evt−L_base,t_evt)，pre-information风险均值 | DEF-PHY-005源onset下界前的物理baseline | CONSISTENT不同对象 / NOT_YET_IN_PAPER | 风险baseline可含源确认前传播，不能冒充无扰动物理baseline | 明确两类baseline，不用F0当无源基线 | Awaiting |
| early window；main155、731–776 | 固定早窗“remains unaffected” | P1 H*、F0^Q上界<η及scope | PAPER_OUTDATED / CLAIM_OVERSTATEMENT风险 | η是总体比例容许，不等于每例无物理效应 | 按scope/η限定总体早窗解释 | Agreed统计方向 |
| 四格effect；main871–950 | δNL、ΔNL四格interaction，非before-after DiD | P1 τSC保留；τQ为另一对象 | CONSISTENT四格 / NOT_YET_IN_PAPER资格层 | τQ不等于τSC；没有非Q与source-absent效应不能恢复全体交互 | 明示细则I分解与支持域 | 代数推断，不冻结新设计 |
| 主时间比较；main1033 | 主检验在同一次(1,1)提取info-resp与phy-resp | P1/Task4 D：风险总体带+无消息F0参考 | MATHEMATICAL_CONFLICT（主分析对象） / PAPER_OUTDATED | 两行为时间不是总体TR与无消息TP；信息也可改变处理组物理链 | 处理内比较降为描述性机制；总体H*判据作为主分析候选修订 | Agreed方向；论文修改待授权 |
| no-message地位；main1036 | (1,0)仅sensitivity，不替代(1,1)主比较 | 同资格随机no-message为主物理参考 | ASSUMPTION_CONFLICT | 处理组物理时钟不能代无消息分布 | 写F0^Q与完整观察契约；同seed只辅助 | Awaiting修订 |
| 个体lead；main1045–1053 | Δtlead=phy-resp−info-resp；明确仅行为层 | P1禁止个体TP(0)−TR(1)识别 | CONSISTENT其行为限定 / CLAIM_OVERSTATEMENT风险 | 可描述同运行两响应差，不能当个体反事实“提前秒数”或风险因果提前 | 明确描述量、区间/clock，保留风险层区别 | Verified distinction |
| risk temporal；main1070–1089、1134–1136 | early四格contrast+物理窗有效性、跨单元汇总 | P1资格两臂TR全网格同时带/F0联合预算 | PAPER_OUTDATED / NOT_YET_IN_PAPER | 没有F0及同时界不能支持Agreed D；两总体不可混用 | 加H*/SESOI/联合覆盖和censor机制；不另建统计体系 | Awaiting |
| physical提前失败；main1121 | 不事后缩窗、不删受影响运行重建四格 | Task4 C/D | CONSISTENT | 保留失败很必要，仍需scope及观察质量 | 保留并与ITT缺失策略协调 | Verified text |
| censor/clock；main530–543、1033与全正文 | 保留未观察/删失；缺完整interval/right/Unknown/offset/drift契约 | DEF-CENS/CLOCK | CONSISTENT保留原则 / NOT_YET_IN_PAPER细则 | 确认不能代onset、不能中点排序或机械KM | 补独立时间对象和误差外扩、信息性缺失界 | Proposal |
| Stage / lock；main1154、1721、1724 | Stage II条件性；calibration/statistics placeholders | 现有Gate和Stage状态不变 | CONSISTENT计划边界 | 论文结构不是Stage1.1授权或已验证结果 | 后续仅按批准内容完善 | 无状态变更 |
| 数据角色；supplementary161–212 | NGSIM/pNEUMA/SPMD/SUMO角色 | 既有数据能力限制 | CONSISTENT高层 | pNEUMA不恢复正式leader/TTC；SPMD不是完整消息链 | 保留并补引用来源 | Verified reading |
| 相关工作书目；references1–19及全217行 | 已有Saberi/Duan；无Jerath/Zhang | E36–38最近邻补充 | PAPER_OUTDATED / NOT_YET_IN_PAPER | 未直接比较最接近ZOI/车辆事件图；绝对创新语句风险 | 后续按真实版本加入；Zhang不借预印本冒称journal精读 | Awaiting bibliography revision |

## 重大冲突登记（不自动修改）

Documented Intent：研究者A–D与P1总体因果/时间设计。Actual Implementation：此处为当前论文活动设计文本，并非已运行实验；main676处理后整组筛选，1033–1036处理组内行为主比较、无消息仅辅助。Evidence：上述带hash快照、精确行号、CORE细则I及P1 §7。Affected Files：Overleaf main/supplementary/bib的未来修订、当前definitions与Task4报告。Conflict：主分析总体、筛选时序与时间对象未对齐；Status: Awaiting Researcher Decision（论文如何改），已接受A–D不再重复待确认。停止相关科研逻辑修改，继续完成本次只读审计与文档。

下方历史Task3“快照不可恢复”“物理多跳主要注释”不再代表当前事实。当前活动正文323–367已确认包含physical graph/chain；保留历史以便审计，不抹去曾有限读取的记录。

---

## Historical — Task3 v0.1 audit retained verbatim

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

## Task6 当前对照（v0.4；D7只登记、不改正文）

Task6未重新连接/下载Overleaf，未读取新的在线正文；下述只复用Task5在2026-11-02T10:07:46.887013Z的三文件SHA/行号审计，不能宣称此后在线最新版仍相同。Task5全文读取/字节复核不由本任务重复冒称。main SHA 0d8951f34ea64db6b2d3d8489bc119d47166088a3c2ef04e0416cb5753e15225；其余SHA见Task5审计。

| 章节/历史快照定位 | 当前统一定义/未来修改范围 | 影响 | 当前状态 |
|---|---|---|---|
| Methods：main673–680、871–950 | Qpre资格ITT与最终四格分别说明；处理后四运行完整性不作ITT筛选；共同opportunity/政策/positivity明确 | 总体与识别，不能只改符号 | Awaiting Researcher Decision / 后续授权修订 |
| Methods：main323–367/物理传播、source/lifecycle | 三层分别，Edie裁切D/V/A、W1–W9、固定N；onset/confirmation/available与全部消息阶段及clock | 新测量定义/参数版本，未验证Proposal不能写已采用 | D1–D4方向Agreed；具体方法/数值Proposal |
| Methods/主时间：main1033–1053、1134–1136 | 总体risk ITT同时带+同资格分层F0/允许集/联合预算为主；行为时差只描述 | 原主时间对象与当前方向冲突保留，不擅改 | D6方向Agreed；统计数值待定 |
| Results | 只能写真正完成的数据/运行及独立n；A0、Qualified0、F0/总体TR-TP Unknown；Task3域不升级 | 不能将Task6设计或calibration性能写成核心科学结果 | 无本次新实验，不补虚构结果 |
| Discussion/claims | 有限测量机制、漏检/时钟/迁移、Qpre总体/四格支持和个体反事实限制 | 不宣称排除任意普通物理影响或个体提前秒数 | 接受限定方向，不证明假设 |
| supplementary/references | 将来仅补实际采用的协议、标签、验收、failure和对应方法引用 | 不把候选全部写成论文事实，不误引Edie为已精读 | 本次零正文/bib修改 |

Documented Intent：P1总体早窗与匹配no-message参考。Actual Implementation：历史论文快照使用处理后完整单元和within-treated行为主时间；现有实现/实验尚无Formal A和F0。Evidence：Task5逐行审计、CORE当前D1–D7、Task3白名单、源码有界贡献。Affected Files：未来Overleaf main/supplementary/references及本对照。Conflict：纳入总体、主时间对象及有限物理范围尚未接线。Status: Awaiting Researcher Decision。相关正文逻辑修改停止，仅按授权完成本任务设计；不修改main.tex、supplementary.tex、references.bib。
