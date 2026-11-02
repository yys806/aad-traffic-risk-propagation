# P2 Task5 — Final Report

日期：2026-11-02。最终交付状态：COMPLETED_WITH_LIMITATIONS。此为文献、方法与定义操作化完成状态，不是科学假设、Scientific Gate、Protocol Lock或Stage1.1通过。

## 1. 实际完成内容

1. 完整读取用户提供Zhang正式18页PDF，核对六作者、期刊211/103522、日期、10,752,791 bytes和SHA；与SSRN分版本对照。证实Eq9由倒数修为位移/时间、约束列表变化、标注计数单位与正式结果不同；不冒充作者代码/实验复现。见[正式版本审计](P2_TASK5_ZHANG_PUBLISHED_VERSION_AUDIT.md)。
2. [测量与识别方案](P2_TASK5_MEASUREMENT_AND_IDENTIFICATION_PROPOSAL.md)：比较分别报告/联合判定/机制复合，推荐独立micro、macro、cohort时间族；Edie型同域车距/车时测量、边界裁切、稀疏轨迹、W1–W9提取、质量/Unknown、支持域与冲突处理均具体化。
3. 明确Qpre两臂ITT/F0^Q与全体四格交互的不同总体、代数分解和不可识别缺项；提供顺序DAG及源前共同opportunity替代，但不改随机化矩阵。
4. 形成从raw QC、允许时间集合、CDF识别界、风险ITT/全网格同时带、clock/measurement联合错误到最终判定的完整流程；给出有条件可执行的有限样本保守构造及不可适用条件，不机械KM/Turnbull/pointwise CI，不伪造F0。
5. 完整参数路线覆盖baseline、θ/h/q、coverage/recovery、clock、micro质量、macro域窗、η/δ/α/H*及有效独立n。无足够交通依据的推荐值和合理范围保持Unknown，不把V2探索网格称交通经验范围。
6. 统一定义升级[本版入口](../definitions/README.md)为AAD-SCI-DEF-20261102-P2T5-v0.3；原26条保留，新增DEF-TIME-004共27条，每条13字段。新细则J–P、证据E44–E53、符号映射和参数路线登记。Task4 A–D继续Agreed；所有新主对象/融合/估计器/数值仅Proposal/Unknown。
7. 新取得Overleaf三文件字节快照并复用相同字节的Task4全文审计，精确回核关键主冲突；只读、无正文写入。见[论文审计](P2_TASK5_OVERLEAF_AUDIT.md)及[唯一差异表](../definitions/OVERLEAF_ALIGNMENT.md)。

## 2. 文献与Zotero

[文献方法审计](P2_TASK5_LITERATURE_AND_METHOD_AUDIT.md)和[统计方法笔记](P2_TASK5_STATISTICAL_METHOD_NOTES.md)记录实际阅读范围、参数/假设、独立推断和停止依据。正式Zhang复用Q65YUJ89，原件9F39AWXN、双语V72AJRHW、note DXIKHPDP；旧SSRN CLA3GKSX原SHA不变。新增两条：Frangakis–Rubin2002 TVEZQ3UT（完整作者手稿HTML；无可用PDF）和Hoeffding1963 ASAGL6D9/42JXM756（原始扫描关键页PARTIAL_READ）。原Hall26RQQ7EE/XBQFKNWX测量节补核；Edie原文仍未取得，不无限检索。

AAD当前91 unique top-level / 11集合节点；新增前全库281 top-level查重，未重复建parent、删除/移动/合并既有版本。用户称SSRN有独立parent与本地所见不一致：实见正式parent上的独立旧附件，已如实登记，不虚构另一item key。精确DOI书目核对与合法原件/notes/hash读回见[安全清单](../../../doc/literature-notes/P2_TASK5_SOURCE_AUDIT_20261102.json)和[轻量索引](../../../doc/literature-notes/AAD_ZOTERO_INDEX_20261102_TASK5.csv)。原文仅在Zotero，隔离抽取文本/快照Git排除。

新增刊物指标用现有easyScholar工具返回值，不臆造缺项；官方短简称未可靠取得，Crossref返回全名保留并登记限制。Principal无PDF、Hoeffding扫描无OCR未生成双语附件；正式Zhang双语成功并字节核验。PAPER-SKILL helper缺失保留WARN/UNVERIFIED helper gate，不冒称helper或独立reviewer通过。

## 3. 核心科研判断

- 物理意义：三层测量分别有清楚含义，但没有证据支持一个覆盖任意物理影响的统一标量时间。macro算子crossing不等最早真实物理响应；不能减窗即校正所有聚合/阈值延迟。
- 可兼容性：保留Formal P2/rho的pair、gap、TTC/DRAC和确认规则；W1–W9不变，Zhang只作为成熟候选提取工具。纯graph connectivity/score不是Qualified，更不是随机因果证明。
- 因果对象：资格后通信随机化可识别合格两臂策略效应及匹配物理参考；Q对ZS可能为处理后量，不能自动恢复全部有源或四格交互。principal stratum的定义不补齐无源臂Q(1)成员。
- 统计对象：预定H*与同资格分层F0上界、风险同时带及联合预算可形成总体早窗判断；Unknown、信息性缺失、clock、层/时点多重性必须保守进入。两侧边际不构成单事件反事实提前秒数。
- 参数：W/θ/h/q/coverage/宏观窗/clock相互依赖，交通状态、composition和观测机制限制外推。现有证据能定结构与校准路线，不能唯一决定正式数值。
- 创新与NC：变化点、物理图、波前和信息—动作—宏观状态均有先例。候选贡献在联合生命周期/采用动作/区域风险ITT/独立同总体物理参考；目前Hypothesis，未证全球首次、机制规律或核心因果效应。识别支持和测量覆盖缺口足以影响强论文结论。

## 4. 集中待决事项

[研究者决策清单](P2_TASK5_RESEARCHER_DECISIONS.md)T5-D1–D7给出依据、反对证据、替代和后果：主arrival时间族及有限机制范围；macro算子/支持和状态规则；资格两臂与四格的共同机会/非Q支持；tE onset区间映射；参数科学损失与未来独立校准；允许集合/估计器/检验族/联合预算；后续Overleaf修订。已Agreed A–D不再待授权，亦未被本轮具体Proposal静默改写。

## 5. 现有证据及下一步条件

Formal A source=0、独立Qualified source→cohort=0，F0、TR/TP总体时间优先性Unknown。Task3 V2 768面板/42候选/32,256评估、B60 CALIBRATION_ONLY/2,520评估和区域内中间响应均保留原证据域；B目标cohort无阳性，不能提供检测率/延迟真值或选θ。无新数据推翻或证实主假设。

下一步须由研究者先审核主对象/支持/估计器，再决定是否授权实现或独立null/阳性校准。需要合格源、独立W1–W9/全域macro记录、随机同资格无消息和风险曲线、可靠clock/漏检能力，才能估F0和时间优先性。本轮不自动启动下一P2任务、Pilot、Protocol Lock或Stage1.1。

## 6. 变更范围与最小充分验证

范围仅文档、科研定义、文献元数据、索引与研究注册；生产模块/数据接口/科研逻辑均不改。按AGENTS文档任务要求，检查strict-git文档、JSON/CSV、Markdown本地链接、27×13字段/符号/状态、来源SHA/Zotero读回、项目注册和Gate不变、git diff。研究audit清单变化后运行evidence exporter及verify；不运行全量pytest/compileall或新实验。

验证执行记录在本节收尾追加；执行前不声称通过。任务中一次本地索引脚本因Python换行字符串SyntaxError在解析阶段停止，未执行API/文件写入；改用显式换行字符后成功，原失败保留于任务工具记录。

## 7. 禁止事项与状态保护

新SUMO/TraCI/Pilot/CALIBRATION_ONLY=0；不重跑Task9/18/19、不读locked holdout、不改生产科研代码/正式config、Formal P2/rho、Gate、Protocol Lock、Stage1.1、AGENTS、长期路线或Overleaf。没有降低阈值，没有用B升级Formal A或把模型证据当现实因果。

Stage0.5=CLOSED_WITH_LIMITATIONS；Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock=BLOCKED；StageI=READY_ENGINEERING_ONLY；Stage1.1=NOT_AUTHORIZED。

## 8. 交付文件与上下文

本任务7份专项报告（含方法阅读笔记）、1份原Zhang笔记dated更新、统一定义6文件、P0文献登记/相关矩阵/创新/NC增量、2个安全索引、AI_CONTEXT00–08与3项目索引/PROJECT_REGISTRY同步。架构/数据流描述的是提案契约，未声称已实现Detector/Observer新接口。历史Task3/4原报告和实验结果不追溯改写。

基线commit 003e463d8b0e551e9ecf24efde0c731fb235e980。最终Conventional Commit和Push后在用户报告给出真实SHA及远端核验；本文件不自引用其尚不存在的commit SHA。

## 9. 实际验证结果（2026-11-02）

- 影响范围复核：34个文档/CSV/JSON文件；0生产代码/config/AGENTS/活动tex/实验输出变更。注册表原experiments、results、history及既有Task1–4 audit对象逐项相等；六项Stage/Gate/Protocol字段不变。
- 定向内容检查：27 Definition IDs唯一、每条13字段；20条PAPER_REGISTER/91条Zotero索引JSON/CSV解析；3个目标DOI大小写不敏感各唯一；85个当前/新增本地Markdown链接存在；6文件统一v0.3。原正式PDF与三Overleaf文件bytes/lines/SHA匹配。
- Zotero实际读回：3个目标parent、4个原件/双语附件hash与5条notes的parent归属均通过；六位正式作者、主题归属和正式/SSRN版本身份核对。旧附件SHA不变，正式版双语附件已成功。
- 项目严格校验：python code/scripts/validate_project_docs.py --strict-git → PROJECT_DOCS_OK。便携导出 → PORTABLE_EVIDENCE_EXPORTED results=92 files=1391；--verify → PORTABLE_EVIDENCE_OK。没有新增科学结果或改写92个历史结果。
- git diff --check最终通过；初次发现CORE末尾空行已局部修正。自编定向检查曾因正则转义/DOI大小写比较的检查器错误中断，修正检查器后通过，不能伪装为全部首次通过。Git既有CRLF/LF提示未扩展成全仓库清理。
- 按文档任务风险分级，不运行pytest/compileall/实验。PAPER-SKILL缺失helper仍WARN/UNVERIFIED，Edie/简称/部分指标、真实交通参数与F0识别缺口仍明确保留。

最终提交前对报告和格式收尾再执行strict-git与差异检查；Commit/Push实际返回另见用户交付记录。以上不是科学验证、外部论文复现或Gate通过。
