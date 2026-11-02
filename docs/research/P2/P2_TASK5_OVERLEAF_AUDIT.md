# P2 Task5 — Overleaf只读一致性审计

日期2026-11-02，Status: COMPLETED_WITH_LIMITATIONS（审计已完成，论文修订未授权）。唯一正式差异入口为[OVERLEAF_ALIGNMENT](../definitions/OVERLEAF_ALIGNMENT.md)。不修改正文、补充材料、bib或任何Overleaf项目设置。

## 1. 实际读取的版本

使用已有合法登录的Overleaf AAD项目只读下载新ZIP；project ID 6aa63dcd249d9edf8228ca51。取得UTC 2026-11-02T10:07:46.887013+00:00（北京时间18:07:46）。本机下载AAD (1).zip，SHA256 7545186b7d040ea407432a7cdd8693846d24faf3d37457af7c6e5621265cf39b。

| 文件 | bytes / 物理行数 | SHA256 |
|---|---|---|
| main.tex | 213343 / 1759 | 0d8951f34ea64db6b2d3d8489bc119d47166088a3c2ef04e0416cb5753e15225 |
| supplementary.tex | 6892 / 254 | 79c3b5da82c25e02d900a60721375fe6a3eb44bd91acdc3c7c119bd64af9171d |
| references.bib | 8111 / 217 | 1e4738af5d7ab115ca9ea38daa6a091d75e723e7f3395aa907e37ebf7d063904 |

三文件逐字节与Task4已完整分段审计的文件相同；本轮重新下载、核SHA，并定向回读main673–680、1029–1053、1133–1137及既有定位。不是只看摘要；复用相同字节的全文审计避免重复读取所有1759行。ZIP本身hash改变不表示正文改变。原始.tex仅在Git排除的隔离审计区；不恢复活动论文编辑流程。行号为本快照1-based物理行；无后续编辑保障。

## 2. 当前差异表

| 位置 | 论文当前内容（释义） | 最新科研定义/分析 | 冲突类型 | 建议修改 | 状态 |
|---|---|---|---|---|---|
| main87、90、96 | 排除普通物理传播/在普通影响前 | Agreed A有限预定可观测机制与检测能力 | CLAIM_OVERSTATEMENT / ASSUMPTION_CONFLICT | 限定region/time/机制及未观察部分，不以阴性作全称排除 | 待另行授权改论文 |
| main188–215 | ordered pair、g净间距、TTC/DRAC | 保留Formal既有语义；新速度偏差不能复用g | CONSISTENT / NOTATION_CONFLICT风险 | 保持原符号，按symbol register加层/基线上标 | 未改 |
| main294–300 | 正式成立后可生成；t_evt确认 | onset interval与确认/eligible分开 | CONSISTENT消息资格 / NOT_YET_IN_PAPER onset | 补onset、confirmation、generation eligibility独立字段 | tE具体映射Proposal |
| main323–367 | **活动正文已有**有向物理图/实际链、区域首车phy-resp | W1–W9、三到达对象及Unknown | CONSISTENT框架 / AWAITING_RESEARCHER_DECISION对象 | 不把首车行为时间当cohort或macro时间；分开到达族 | T5-D1 |
| main323–367及区域risk段 | 未给同域macro q/k/u、部分穿越与窗支持 | Edie型过去时空域；operator onset不等raw物理起点 | NOT_YET_IN_PAPER | 补D/V/A、lane裁切/覆盖/检测延迟与独立质量 | T5-D2 |
| main442–461 | generation/send/delivery/adoption | verification需独立，失败仍原assignment ITT | CONSISTENT部分 / NOT_YET_IN_PAPER | 增verification、unknown与clock，不删未采用单元 | Agreed C方向 |
| main673–676 | 完整四运行单元；实际两源匹配和四臂QC，不合格整组剔除 | Qpre在ZC前盲确认，处理后缺失不能改ITT纳入 | ASSUMPTION_CONFLICT / PAPER_OUTDATED | 明确源前/通信前资格；将处理后不可评估纳入缺失界，审计四格支持 | 高优先；T5-D3 |
| main680 | 以无消息有源臂t_evt为公共索引，明确无源臂并非真有源事件 | 该模型公共clock限定可保留；不是实际无源onset | CONSISTENT索引限定 / AWAITING_RESEARCHER_DECISION | 补onset映射和确认前传播；不伪造source-absent Q(1) | 未把该段误报成无源真事件 |
| main684–706 | pre-information风险基线 | 物理基线须早于source onset下界，且同macro算子 | CONSISTENT不同对象 / NOT_YET_IN_PAPER | 分开风险baseline与物理baseline；不能合成一个参考 | T5-D5 |
| main871–950 | 四格interaction δNL/ΔNL | τSC与τQ不同；分解需非Q和S0支持 | CONSISTENT四格 / NOT_YET_IN_PAPER资格总体 | 双 estimand对照和支持域；不以τQ替代τSC | T5-D3 |
| main1033 | 主Temporal precedence在(1,1)内比较两行为响应 | P1风险总体带+同资格无消息F0为主对象 | MATHEMATICAL_CONFLICT（主分析对象） / PAPER_OUTDATED | 行为配对保留作描述机制；重写主统计框架需授权 | 高优先；T5-D6/D7 |
| main1036 | (1,0)只作sensitivity | Agreed C/D无消息总体是主物理参考 | ASSUMPTION_CONFLICT | 列F0,ℓ^Q与允许集合、joint budget；不能用treated物理时钟代替 | 高优先 |
| main1045–1053 | Δlead并明确只属行为响应层，不证明区域risk提前 | 保留这种区别；无个体跨世界提前秒数 | CONSISTENT行为限定 / CLAIM_OVERSTATEMENT风险 | 不把描述量解释成TP(0)−TR(1) | 审计没有歪曲原文 |
| main1121 | 不事后删受物理影响例或缩窗 | 与保留失败原则一致 | CONSISTENT | 与ITT缺失策略协调保留 | 不需撤销该原则 |
| main1134–1136 | early interaction加window validity，总体汇总 | H*、SESOI、全网格风险带、F0上界及联合预算 | PAPER_OUTDATED / NOT_YET_IN_PAPER | 补可执行步骤、观测与统计两种不确定性，不用pointwise代同时带 | T5-D6 |
| main530–543、1033及全文 | 保留未观察/删失，但无完整允许集合和clock契约 | interval/right/Unknown、可恢复状态和双侧对齐误差 | NOT_YET_IN_PAPER | 不机械KM/区间中点；记录raw support与确认 | T5-D4/D6 |
| supplementary161–212 | 各数据源分工/能力边界 | 本轮不新增数据效应结论 | CONSISTENT | 保持，后续按实际测量能力补充 | 未改 |
| references.bib全部217行 | 已有Saberi/Duan；未见Jerath/Zhang正式DOI及本轮两方法来源 | 正式Zhang与预印本版本独立；主联合识别仍Hypothesis | NOT_YET_IN_PAPER / CLAIM_OVERSTATEMENT风险 | 后续补最近邻和对应方法，取消笼统“first/无人建立”论证 | 本轮未加bib |

## 3. 冲突影响与后续顺序

优先处理纳入总体、主时间对象、主张范围，再补宏观测量/统计章节与相关工作；只换符号无法修复识别。论文完整四格unit的定义可保留为模型block，但其处理后整组有效性选择不能自动识别当前Qpre ITT。预先写明剔除规则并不保证它不受处理影响。

当前论文清楚区分行为层与风险层，这一点保留；冲突是主时间比较和参考总体与最新Agreed方向不同，不是诬称论文把行为差已当作风险效应。上述差异不能由Codex在本轮静默修正，任何正文修订待研究者另行授权。
