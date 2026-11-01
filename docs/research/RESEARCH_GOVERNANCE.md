# AAD 科研文献与创新性审计治理规范

状态：`Active`（P0 Task 1 建立，2026-11-01）

本文件是 AAD 后续文献调研、原文精读、创新性判断和报告编制的长期工程规范。它不替研究者决定研究方向，不修改 Stage 0.5/0.6、Protocol Lock、Stage I 或 Stage 1.1 的科学状态。

## 1. 阶段与 Task 编号

- 采用 `P0`–`P9` 阶段。
- 每个阶段内部使用独立整数 Task：`Task 1`、`Task 2`、`Task 3`……。
- 不再使用 `Task 1.1`、`Task 1.2` 等扩展编号。必要的补充工作在下一个整数 Task 的开始处处理。
- 每个 Task 应有独立目标、输入、输出、证据和验收边界；内部可以包含多个工作方向。
- 报告标题、目录和 Git 提交信息必须保留阶段前缀，例如 `P0 Task 1`。

## 2. 主线规划保护

`D:\shen\OB\科研\TJU\AAD\AAD\Stage1.1前各个阶段.md` 是长期规划基线。

- 后续阶段按该文件推进，不因单次检索或 agent 提议而直接改写。
- 只有充分证据显示原规划存在实质错误时，才在 `RESEARCH_DIRECTION_DECISION_MEMO.md` 提出修改建议。
- 只有研究者明确确认后，才可修改该文件。
- 历史规划、建议和最终决定必须分开保存，避免把 Proposal 写成 Agreed。

## 3. 文献检索规范

1. 先读取项目事实源和 Zotero `TJU → AAD`，再做外部检索；不重复下载已有文献。
2. 近三年（2024–2026）优先，但经典奠基工作和最接近的先行工作优先级更高。
3. 重点来源：出版社正式页面、IEEE Xplore、ACM、ScienceDirect、Springer、Wiley、Nature Portfolio、arXiv、Semantic Scholar、OpenAlex、Crossref。
4. 每轮检索记录日期、数据库、检索式、返回范围、筛选理由和停止理由；Google Scholar/Semantic Scholar 只作为发现和引用追踪入口。
5. 对候选文献执行 backward citation、forward citation 和最近邻追踪。高度相似文献必须进入注册表，即使最终不纳入核心矩阵。
6. 出版信息以 DOI/出版社/正式会议记录为准；不以搜索摘要、文件名或 LLM 总结代替核验。

## 4. 筛选与分层

- `CORE`：直接回答 AAD 科学问题，或可能直接威胁/支撑核心创新主张。
- `SUPPLEMENTARY`：方法、测量、数据、控制或因果识别与 AAD 直接相关，但不是最近邻。
- `BACKGROUND`：用于概念、经典模型或规范背景。
- `EXCLUDED`：记录排除理由，不删除条目。

排除理由只能写成事实性原因，例如主题不匹配、重复、仅营销材料、元数据无法核验或全文不可得；不得以“支持 AAD”作为纳入标准。

## 5. 原文精读与状态词

每篇最终纳入论文必须有独立 Markdown 记录，至少覆盖摘要、引言/相关工作、方法和数学表达、实验设置、结果、讨论、结论、局限与 AAD 关系。

阅读状态严格使用：

- `FULL_TEXT_READ`：已通过 Zotero 索引全文或正式开放全文逐节阅读。
- `PARTIAL_READ`：读取了正式全文的部分章节/页面，但尚未完成全文。
- `METADATA_ONLY`：仅核验题名、作者、年份、DOI、摘要或出版社页面。
- `FULL_TEXT_UNAVAILABLE`：已尝试合法来源，全文仍不可得。

只有 `FULL_TEXT_READ` 才能支持论文方法和结果的强断言；`PARTIAL_READ`、`METADATA_ONLY` 和 `FULL_TEXT_UNAVAILABLE` 不得被写成已完成精读。

数字必须绑定 Figure、Table、Equation 或 page。无法定位时写 `Unverified`。

## 6. Fact / Inference / Hypothesis / Proposal

- **Fact**：由源码、配置、原文、正式元数据或机器证据直接支持。
- **Inference**：基于多个 Fact 的明确推断，必须写出推断链和反例风险。
- **Hypothesis**：尚待实验或进一步数据检验的科学假设。
- **Proposal**：供研究者选择的研究设计、方向或改进建议，不改变现行方案。

报告不得将作者解释自动升级为事实，也不得把模型输出或工程可行性写成因果机制成立。

## 7. 创新性判断规范

任何创新主张都必须回答：最近邻是谁、其已完成什么、AAD 多了哪一条可检验机制、需要什么不可替代证据、失败时如何收窄主张。

以下内容默认视为已有基础，不能单独宣称首次：

- 信息传播速度可超过车辆物理扰动传播；
- V2X/BLOS 警告能改变驾驶行为；
- 非局部信息可用于交通控制；
- 信息流与交通流可以耦合建模；
- TTC、DRAC、PET 等代理指标可用于风险评价；
- 拥堵/瓶颈可在道路网络上时空传播。

候选创新必须进一步证明生命周期、控制器采用、实际动作变化、物理到达时间、区域风险以及干扰条件下的因果链，而不是只增加一个指标或更换名称。

## 8. Zotero 归档规范

- Zotero 集合 `TJU → AAD` 是唯一正式文献库；DRIFT 条目不改动。
- 新条目先 DOI/题名查重，再加入 AAD 和最相关的已有主题集合。
- 不删除原条目、不批量合并重复、不覆盖历史审计记录。
- 合法 PDF 优先出版社 OA、作者 accepted manuscript、arXiv/CORE/PMC/Unpaywall；付费墙和学校认证由研究者本人处理。
- 统一标签建议：`P0/CORE`、`P0/SUPPLEMENTARY`、`P0/BACKGROUND`、`P0/FULL_TEXT_READ`、`P0/PARTIAL_READ`、`P0/FULL_TEXT_UNAVAILABLE`。
- 附件是否存在、是否可检索全文、是否真正阅读，分别登记，不以 `numChildren>0` 代替阅读状态。

## 9. 统一调研输出格式

每个 P0 文献 Task 至少产生：

1. `SEARCH_PROTOCOL.md`：检索式、来源、日期、筛选和饱和判断；
2. `PAPER_REGISTER.csv`：统一元信息、来源、Zotero Key、附件和阅读状态；
3. `paper_notes/`：逐篇精读记录；
4. `RELATED_WORK_MATRIX.md`：最近邻比较；
5. `NOVELTY_GAP_ANALYSIS.md`：创新性威胁与研究空白；
6. `CORE_SCIENTIFIC_CONTRIBUTIONS.md`：条件化的潜在贡献；
7. `NC_POSITIONING_AND_RISK_ASSESSMENT.md`：高水平期刊审查；
8. `RESEARCH_DIRECTION_DECISION_MEMO.md`：交由研究者决定的方向和问题；
9. `P0_TASK{n}_FINAL_REPORT.md`：事实、未决问题、验证和边界。

各文件引用注册表和精读记录，不复制互相冲突的独立文献数据库。

## 10. 变更与科研边界

文献审计可以提出方向调整建议，但不得自行改变核心科学问题、物理/信息传播定义、风险指标、Gate、容差、Protocol Lock、Stage 1.1 或正式实验授权。所有新方向默认 `Proposal`，等待研究者决定。

P0 Task 1 完成时的项目科学边界保持：Stage 0.5 `CLOSED_WITH_LIMITATIONS`、Stage 0.6 `PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS`、Protocol Lock `BLOCKED`、Stage I `READY_ENGINEERING_ONLY`、Stage 1.1 `NOT_AUTHORIZED`。
