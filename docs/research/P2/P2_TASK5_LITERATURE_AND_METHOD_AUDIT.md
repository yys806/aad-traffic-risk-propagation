# P2 Task5 — 文献与方法审计

2026-11-02；COMPLETED_WITH_LIMITATIONS。只补实际缺口，不重新全面检索P0干扰/因果理论。方法结论集中于[统一定义](../definitions/README.md)和[方案](P2_TASK5_MEASUREMENT_AND_IDENTIFICATION_PROPOSAL.md)，不是新增确认性结论。

## 1. 使用流程与停止依据

按PAPER-SKILL（D:/shen/test/PAPER-SKILL）的路由/证据契约使用现有笔记、精确DOI、原文和版本对照；另按pdf、zotero-clean工作流进行PDF视觉核对和查重。verify_papers.py辅助程序在该技能安装中缺失，helper gate为WARN/UNVERIFIED；没有伪报工具PASS或独立reviewer verdict。独立原文/DOI/hash核验有据可查，不与helper可用性混淆。

Zhang用户提供正式PDF解除Task4获取阻塞；全文18页、关键公式/表视觉核对；只读已有SSRN与Task3/4审计。针对Edie原文一次限定检索只见二手/不明授权入口后停止，不绕认证/付费。Hall官方章已足以支持操作化Proposal及局限，原始Edie仍缺。统计只增principal stratification原始文献与有限样本界原文；其他区间删失、干扰、同时带复用P1/P2既有审计。不为了数量扩大检索。

## 2. 实际来源和Zotero读回

| 来源 / DOI | item key | 原文及阅读状态 | 附件 / 主题 / 本轮动作 | 对AAD的实际价值 |
|---|---|---|---|---|
| Zhang2026 /10.1016/j.trb.2026.103522 | Q65YUJ89 | FULL_TEXT_READ_PUBLISHED，18页 | 新原件9F39AWXN；双语V72AJRHW；既有05_非局部交通流模型集合WCC9X92Q；复用parent | 变化点/事件图候选与版本差异；不能代W1–W9或随机因果识别 |
| SSRN5903681 | 同parent的旧独立附件 | Task3全文精读，Task5定向版本回核 | CLA3GKSX原字节不变；未创建/合并/移动parent | 对照旧公式/标注/结果；不冒充正式版 |
| Frangakis–Rubin2002 /10.1111/j.0006-341X.2002.00021.x | TVEZQ3UT | FULL_TEXT_READ_HTML，PMC作者手稿完整article；PDF端点实际HTML | note NEVZT5FQ；无PDF；AAD根+既有06_类超距与因果理论QPEI5PQP | Qpre对ZC前、对ZS后；principal层定义不赋予数据识别 |
| Hoeffding1963 /10.1080/01621459.1963.10500830 | ASAGL6D9 | PARTIAL_READ，扫描原文印刷pp13–15、28 | 原件42JXM756；note3DCQPWE5；AAD根+QPEI5PQP；无OCR双语 | 独立有界均值/SRS及有限族union保守上界 |
| Hall官方FHWA Chapter2 / FHWA-TFT-CH2 | 26RQQ7EE | PARTIAL_READ，§2.1–2.2补核 | 既有XBQFKNWX，不重复导入 | 时空支持、部分穿越、不同space/time均速 |
| Fay–Shaw2010 JSS（10.18637/jss.v036.i02）、Hudgens–Halloran、Aronow–Samii | QUH3LUP3 / TIWGTN2S；后两者H8GFNS8U、T6SFNY5I | 历史已读，不冒称本轮新增全文阅读 | 原条目保留 | 观察机制、干扰与实际assignment边界 |

本轮新增parent恰为2；AAD子树unique top-level从89到91、集合节点仍11。名称以安全source audit的实际collection_names为准，本表主题含义不新建分类。新增前全库281 top-level按DOI/题名查重；没有重复导入、删除或合并。用户称SSRN已有独立parent与本地事实不一致：实见同parent独立附件；保留事实和版本身份，不伪造另一key。

正式Zhang原件SHA256 1672d0c1bb4207da2f542096bacb4d5e8641993b5768c208d62cec6b2e3627f1，旧预印本047b49c784c49214721aae6021029a3bb3011f9287c23b025adf26fdb41ac253。机器翻译只作辅助，不成为原文证据。

新增正式元数据按精确DOI Crossref核验；easyScholar返回的期刊指标已写Extra，缺项为Unknown，不伪造CCF/索引状态。Crossref刊名简称返回全名，未手造标准短名；可靠短名仍待补核。Principal无PDF与Hoeffding扫描无OCR分别限制双语附件；未将HTML当PDF上传。不在Git建PDF库，不按题名反查Crossref，不运行全库清理/翻译。

## 3. 方法取舍

| 问题 | 可复用成熟方法 | 为什么不直接照搬 | 本轮结论等级 |
|---|---|---|---|
| macro状态 | Edie型车距/车时、完整snapshot辅助 | 原始轨迹覆盖/边界/同域条件必须成立；不能把窗末当最早物理起点 | Proposal，有Hall依据；无AAD参数验证 |
| micro候选 | Zhang CUSUM+候选PELT/物理图 | 无向BFS、经验速度约束、标注大波不证明源特异leader链 | Fact方法审计；提取工具Proposal |
| qualification | W1–W9既有体系 | graph score/时空接近不能补身份和竞争解释 | Agreed框架；质量数值Unknown |
| 两臂/四格 | 潜在结果、principal strata、全期望分解 | 潜在资格缺失与非Q无随机支持无法由符号解决 | Inference识别缺口；共同opportunity为Proposal |
| arrival CDF | 允许集合识别界+有条件Hoeffding上带 | 比NPMLE更保守，但不强假设信息性缺失为随机；n需独立设计 | 新数学Proposal，不是已估F0 |
| 区间删失效率 | 正确inspection下Turnbull | 可恢复状态及隐藏历史不等普通failure inspection | 条件适用；不机械KM |
| 风险全网格带 | 有界包络浓缩；设计相容cluster max-t候选 | 风险范围未证时不可强套；Fisher sharp null不等ATE带 | Proposal；需独立覆盖验证 |

## 4. 创新性增量与证据边界

正式Zhang比预印本更完整，已覆盖变化点、物理图、波前重建、消融/敏感性；不能再把这些本身当AAD独立创新。其无信息随机干预、完整消息验证/采用生命周期、区域riskITT与随机source-present no-message F0联合识别。该缺口在本次最近邻审计范围内仍存在，不能据此宣称全球首次。Task4 Jerath已连接信息—动作—macro状态，Saberi/Duan已覆盖宏观传播/预测；本轮不重复写成AAD新发现。

AAD候选贡献仍为同源可审计生命周期/采用动作、区域风险因果效应、同资格独立物理参考与联合不确定性；目前Hypothesis/设计潜力，未由768合成面板或B60验证。核心缺口：A0、独立Qualified0、F0/TR-TP Unknown、检测能力/域映射、资格与四格支持、论文主分析过时。NC定位风险没有因正式文献获取而自动消失。

## 5. 可追溯交付

[Zhang版本审计](P2_TASK5_ZHANG_PUBLISHED_VERSION_AUDIT.md)、[方法笔记](P2_TASK5_STATISTICAL_METHOD_NOTES.md)、原paper_notes dated更新；P0 PAPER_REGISTER/RELATED_WORK_MATRIX/NOVELTY/NC报告仅追加本轮增量。安全清单doc/literature-notes/P2_TASK5_SOURCE_AUDIT_20261102.json与AAD_ZOTERO_INDEX_20261102_TASK5.csv记录metadata/key/hash/read status，不含凭据、论文原件或.tex正文。
