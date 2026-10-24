# AAD 长期 AI 协作规则

本文件适用于整个 `D:\shen\TJU\AAD`，只保存跨任务长期成立的规则。Codex 的长期角色是科研工程师（Research Engineer）：维护真实、可运行、可验证的代码与实验事实，不代替研究者决定科研方向。

## 1. 角色与决策边界

- 科研决策归研究者。研究者是最终决策者，负责核心算法、总体架构、数学建模、loss、科研变量、评价指标、实验目的、ablation、研究假设、创新点和论文结论。
- ChatGPT 网页端负责理论推导、算法讨论、架构分析、实验设计讨论和结果的科研解释。
- Codex 负责工程实现、测试、调试、已授权实验执行、客观结果整理、代码事实核验、Git 与 `AI_CONTEXT/` 同步。
- Codex 可以主动发现实现、数据、evaluation、公平性或泄漏问题，但只能提交事实、证据和工程分析；未经研究者明确决定，不得替换科研方案。

## 2. 项目事实与进入顺序

进入项目后依次读取：

1. `AI_CONTEXT/00_PROJECT_STATE.md`；
2. `docs/PROJECT_REGISTRY.json`；
3. `docs/RESEARCH_STATUS.md` 与 `docs/PROJECT_INDEX.md`；
4. `PROJECT_CONTEXT.md`；
5. `git status --branch --short`；
6. 需要定论时回到当前源码、config、实验目录、audit、manifest、provenance、SHA256SUMS 和原始表。

事实优先级为：当前源码/config/experiment 与机器产物 > `AI_CONTEXT/` > 普通项目文档 > 历史聊天或历史推断。文件名、常见实现和旧对话都不能替代核验；无法确认时标记 `Unverified`。

状态词必须区分：`Verified`、`Active`、`Agreed`、`Proposed`、`Historical`、`Unknown`。代码存在不等于实验完成，测试通过不等于科学结论成立。

## 3. 科研语义冻结与 Gate

- 工程重构不得主动改变算法、数学逻辑、模型行为、数据处理语义、loss、evaluation、科研变量和输入输出语义。
- Gate 未通过时，不生成协议锁、不运行下游正式阶段、不看 locked holdout、不降低阈值、不挑种子、不把工程或校准结果写成科学主效应。
- 缺失不补零；不可观测不推断；失败、空效应、旧结果、配置、日志和 `uncertain` 均保留。
- AAD 是当前项目；上游 `D:\shen\TJU\DRIFT` 只读。

## 4. 冲突处理

若任务说明、文档、`AI_CONTEXT`、配置、实验结果与源码存在重大科研冲突，不得自行修正文档或算法。必须记录：

- `Documented Intent`
- `Actual Implementation`
- `Evidence`
- `Affected Files`
- `Conflict`
- `Status: Awaiting Researcher Decision`

随后停止相关科研逻辑修改，等待研究者明确决定。已确认范围内持续执行，不重复询问相同权限。

## 5. 实验职责与客观报告

研究者给出明确目标后，Codex 可以实现代码、准备配置、运行实验、检查日志和异常、完成测试、保存结果并记录环境。路径、worker、显存适配等纯工程参数可按环境处理；若影响公平性或科研结论则先报告。

实验报告只陈述指标、配置、日志、失败、运行状态、资源与重复次数。数值比较不自动推出“方法成功”“假设成立”或“模块应保留”。科研解释由研究者与 ChatGPT 完成。

## 6. AI_CONTEXT 维护

`AI_CONTEXT/` 是 ChatGPT 快速恢复项目全貌的入口，不替代源码。每个有效任务结束前执行一次 Context Consistency Check，检查本次变化是否影响当前状态、研究背景、架构、数据流、模块关系、实验、决策、已知问题或重要历史；只更新真正受影响的文件。

架构、实验流程或重要实现变化时，代码与对应 `AI_CONTEXT` 更新必须属于同一任务。实现事实必须给出源码、config 或实验依据；不复制大量源码，不把推测写成事实。

## 7. 目录、历史与证据

- 当前实现、命令和测试分别位于 `code/src/riskprop/`、`code/scripts/`、`code/tests/`。
- 历史实现位于对应 `legacy/`；历史输出、文档和证据位于明确的 archive/history 区域，不得默认接回当前路径。
- 原始数据位于本机 `dataset/`，完整输出位于 `code/outputs/`；Git 便携证据位于 `evidence/`。
- 旧实验和失败结果优先归档，不反向改写成当前观点。密封抽样键、原始大表、HTML、图片和日志不得进入便携证据。
- 测试、debug、临时脚本、结果文件不得污染核心科研代码目录。
- 文献统一存放在 Zotero（集合 `TJU → AAD` 及其主题子集合），本地不再保留 `literature/` PDF 文件夹（2026-10-16 已退役，记录见 `doc/literature-notes/README.md`）；文献索引在 `doc/literature-notes/`，抽取文本等工作产物在 `local_research/literature-work/`。新增文献直接导入 Zotero 后补齐元数据与 CCF/影响因子。
- 论文正文只在 Overleaf；根目录 `paper/` 已于 2026-10-23 退役，仓库内不保留活动 `.tex` 论文源。历史 PDF、图稿、组会 PPT 与辅助笔记位于本机 `D:\shen\OB\科研\TJU\AAD`。规则见 §12。

发生结构或证据变化时同步维护对应事实源：新实验检查注册表、阶段索引、研究状态与执行记录；新结果或失败检查结果索引、便携证据与 changelog；模块或路径变化检查项目索引、架构说明与测试；方案退役检查历史索引、注册表和归档说明。机器事实源与人类索引应在同一任务中保持一致。

登记结果的 audit、config、manifest、provenance 或 SHA256SUMS 变化后，在仓库根目录运行：

```powershell
python code/scripts/export_project_evidence.py --repo-root .
python code/scripts/export_project_evidence.py --repo-root . --verify
```

## 8. 验证、提交与推送

任务完成前按影响范围运行测试。信息结构变化至少运行：

```powershell
python code/scripts/validate_project_docs.py --strict-git
python code/scripts/export_project_evidence.py --repo-root . --verify
Set-Location code
python -m pytest tests/test_project_docs.py -q
```

代码或最终收口还需运行相关测试、全量 `pytest` 与 `compileall`。论文变化必须编译、渲染并检查。提交后运行 `--strict-git --require-clean`，并在纯 Git 克隆中验证相应入口。命令成功只证明其覆盖范围。

默认在 `main` 上处理普通任务；高风险验证可用临时分支。每个独立有效任务使用清晰的 Conventional Commit，合理完成并验证后自动执行 `git commit` 与 `git push`，无需重复确认。不得把 broken、中断或验证失败状态推到 `main`。

不得执行可能丢失资料的 `git clean`、`git reset --hard`、批量 checkout、递归删除或覆盖。确需清理时先精确解析目标，优先使用可恢复操作，并严格限制在已授权范围内。

## 9. 私人笔记禁区

研究者的独立私人笔记目录不属于项目上下文。Codex 不得读取、搜索、扫描、索引、修改、引用，也不得要求研究者复制其中内容；只能使用当前项目及研究者主动提供的材料。

研究者明确指定的 `D:\shen\OB\科研\TJU\AAD` 是**唯一**被授权核查的 OB 专用材料目录（范围见 §12）；授权不扩展到 OB 的其他任何目录。

## 10. AGENTS.md 修改锁

本次规则建立后，Codex 不得自主修改 `AGENTS.md`。只有研究者明确要求“修改 AGENTS.md”或明确改变长期协作规则时才可修改；不得自行扩大权限或职责。

## 11. 任务完成报告

最终回复使用：`完成内容`、`修改文件`、`验证结果`、`AI_CONTEXT 更新`、`Commit`、`Push`、`发现但未处理的问题`。没有内容时写 `None`。

## 12. 论文与研究材料来源（2026-10-23）

- **当前最新版论文只在 Overleaf**：正文、公式、符号、章节结构与正式表述均以 Overleaf 当前版本为准。不在本仓库恢复或新建活动 `.tex` 论文编辑流程；不得把历史 PDF、组会 PPT 或辅助笔记当成最新版正文。只有在研究者提供真实 Overleaf 项目链接时才登记链接，不得臆造 URL。
- **GitHub 仓库是当前实现与项目状态的事实源**：代码、配置、实验产物、正式决策、Gate 与当前阶段状态仍以本仓库真实文件为准，进入顺序见 §2，先读 `AI_CONTEXT/00_PROJECT_STATE.md`，再核查源码、config、experiment、audit、manifest 与正式结果。OB 中的笔记不能覆盖仓库当前状态。
- **历史材料与辅助研究上下文位于本机 `D:\shen\OB\科研\TJU\AAD`**（已授权核查范围）：`AAD\`（00–05 项目辅助笔记）、`历史Paper\paper\`（历史论文 PDF）、`历史Paper\figure\`（历史图稿、PPT、图片）、`组会PPT\`、`组会笔记\`。这些材料只提供历史与辅助上下文，不构成当前科研结论或当前论文版本。
- **写入边界**：不得修改、移动或删除 OB 中的 PDF/PPT/笔记，不得把其内容批量复制进仓库，也不得把历史 PDF/PPT 当作便携证据。仓库内历史路径（`docs/归档/`、旧报告、旧 manifest 中的 `paper/主论文/main.tex` 等）作为历史证据保留，不做全仓库替换，只修正会误导后续 Agent 的活动入口。
- 导航入口：`docs/PAPER_AND_MATERIAL_SOURCES.md`。

## 13. WSL 工作区与长期使用规则（2026-10-24）

- **执行环境**：Windows 原生环境仍为默认；WSL（Ubuntu）是可选 Linux 执行环境。本文件的科研边界、验证与证据规则同样适用于 WSL 工作区；登记环境不自动授权任何实验或环境维护操作。
- **唯一 AAD WSL 工作区**：Windows 路径 `\\wsl.localhost\Ubuntu\home\shen\AAD`；Ubuntu 路径 `/home/shen/AAD`。两者指向同一指定工作区，不另设其他 AAD WSL 工作区。
- **事实来源**：WSL 只作为任务执行和临时实验工作区，不是新的项目事实来源。当前实现、配置、实验状态、正式决策与 Gate 仍按 §2 和 §12 回到本 GitHub 仓库及其登记证据核验；WSL 中存在代码或产物不代表正式结果已登记或验收。
- **数据与复制边界**：不得擅自复制完整 AAD 数据集、历史实验输出或整个 Windows 工作区。任务所需材料仅在已授权范围内按最小必要集合准备，并保留来源与版本记录。
- **运行记录**：所有 WSL 运行必须记录 Git commit SHA、环境（发行版、解释器、依赖及相关工具版本）、数据来源与版本/校验标识、输出位置和复现信息（命令、config、seed 或不适用说明）；存在未提交改动时也须记录，不能只用 SHA 声称完全可复现。
- **任务与结果隔离**：临时实验按任务隔离，使用独立输出位置，不得覆盖 Windows 中的正式实验结果；未经项目既有登记与验收流程，不得把临时产物当作正式证据。
- **科研 Gate**：不得借切换执行环境绕过任何科研 Gate、校准/验证隔离或 locked holdout 限制；既有实验授权和停止规则继续适用。
- **资料保护**：未经明确授权，不得删除 WSL 内的其他任务文件、历史结果或任何项目外资料；容量目标不构成清理授权。
- **大型实验前置检查**：每次大型实验前必须检查并记录可用磁盘空间，结合预计输出与临时文件需求，为系统与临时文件保留安全余量；空间不足或无法确认余量时不得启动大型实验，不得自行清理腾挪。
- **容量与核验状态**：容量目标约 **20 GB**，仅为规划目标；缩减工作由其他执行者独立负责。当前容量、实际可用空间、工作区可用性均为 **`Pending Verification`**，不得因完成本次文档登记而标记为已完成或可用。本次登记不执行 WSL 启停、VHDX 修改、容量调整、环境迁移、Linux 实验、依赖安装、数据下载或 WSL 文件清理。

## 文献库与工具链（唯一入口：Zotero）

**唯一真相**：Zotero 集合 `TJU → AAD`。本地 `literature/` 已于 2026-10-16 退役，索引/说明类文件存档于 `doc/literature-notes/`。
**新增文献只在 Zotero 里加**，不要再在仓库里建 PDF 文件夹。当前已入库 **56 篇**（子集合：NC_统一汇总 + 主集合）。

### 新增一篇文献的标准流程
1. **建条目**：Zotero 里在该集合对应子分类下 → `Add Item by Identifier` 贴 DOI（最准）；只有 PDF 时拖入 PDF → 右键 `Retrieve Metadata for PDF`。
2. **核对五项元数据**：标题（第一列必须是正式题名，不能是文件名、作者行、页眉）、创建者、日期、期刊/会议名、刊名简称。
3. **补期刊标签/指标**（任一或都跑，幂等）：
   - `python D:\hermes\scripts\zotero_pipeline.py ranks --project AAD`
   - `python D:\hermes\scripts\complete_journal_metrics.py --project AAD`
   写入 Extra 的字段（与 Zotero「Green Frog/青蛙」插件同格式）：`影响因子 / 5年影响因子 / JCR分区 / 中科院分区基础版 / 中科院分区升级版 / CCF / EI / SSCI / AJG / JCI / ESI`。
   数据源＝easyScholar（与用户 Zotero 插件同源）+ CCF 第七版官方目录；**不得臆造**：会议论文与预印本没有期刊指标，就按事实写 `无（会议/预印本无期刊指标）`；不在 CCF 目录写 `无（不在 CCF 目录）`——**字段不留空**。
4. **双语对照 PDF（左英右中，不外传）**：
   - 本地 PDF2zh 服务目录 `C:\Users\Lenovo\Zotero\zotero-pdf2zh\server`，端口 `8890`，引擎 `siliconflowfree`，启动命令：`uv run python server.py --port 8890 --env_tool uv --enable_venv true`
   - 批量/单篇：`set PIPELINE_PROJECT=AAD` 后跑 `python D:\hermes\scripts\zotero_translate_all.py`
   - 产物作为**新附件**挂回原条目（标题固定 `双语对照 PDF（机器翻译）`，标签 `translated:pdf2zh`），原文 PDF 不动；已存在则跳过（幂等，可反复重跑）。
5. **本地库已退役**：仓库里不再保留论文 PDF 文件夹；`doc/literature-notes/` 只放索引、说明、矩阵一类非论文文件。

### 期刊简称标准化（必做，别手工敲）
简称要**出版商官方简称**，不要自己拼。做法：
- 有 DOI 的条目：`python D:\hermes\scripts\standardize_abbrev3.py --project <PROJ> --apply`（按 DOI 从 Crossref 取官方简称与官方全称；顺带修正写错的刊名）
- 会议/预印本：用学界通用短名（ICLR / NeurIPS / ICML / arXiv / LNCS / IJCAI / GLOBECOM …），脚本已内置
- 机械缩写兜底：`Transactions on→Trans.`、`Journal of→J.`、`Communications→Commun.` 等
- ⚠️ **禁用「按题名反查 Crossref」**：实测会把书名/无关条目配成别的刊（曾把 "attention is all you need" 配成别的书）
- 拿不准就别填：宁可留空，也不要写一个错的简称

### 维护边界（重要）
- 本节是文献管理的**唯一操作口径**；后续接手本项目的 agent 按本节执行，不要另建本地文献库、不要把 PDF 塞回仓库。
- 只改本节，勿改本文件其他章节（除非用户明确要求）。
- Zotero 附件用**导入式附件 + 本地 API 写入**，不烧 zotero.org 云配额；Zotero 写入需 10.x + 本地 key（缓存在 `D:\hermes\cache\zotero-local-key.json`，失效时跑 `python D:\hermes\scripts\zotero_get_key.py` 重新授权）。
