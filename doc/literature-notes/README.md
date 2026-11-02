# AAD 文献管理说明（Zotero 唯一文献库）

## Current — P2 Task4 literature audit (2026-11-02)

Task4 metadata-only snapshot: [AAD_ZOTERO_INDEX_20261102_TASK4.csv](AAD_ZOTERO_INDEX_20261102_TASK4.csv); verification/provenance: [P2_TASK4_SOURCE_AUDIT_20261102.json](P2_TASK4_SOURCE_AUDIT_20261102.json). Live AAD scope contains 89 unique top-level items and 11 collection nodes including root. Four target papers already existed; no duplicate parents, merge or deletion. Three journal bodies reread, Zhang journal PARTIAL_READ with existing SSRN explicitly labeled; necessary Hall official chapter added and measurement sections read. PDF originals remain in Zotero; source text/Overleaf snapshots stay local and excluded from Git. Full analysis: [Task4 audit](../../docs/research/P2/P2_TASK4_LITERATURE_AND_NOVELTY_AUDIT.md). Older dated inventories remain historical, not current counts.

**唯一文献库 = Zotero，集合 `TJU → AAD`。** 本目录只保留轻量管理文档，不保存 PDF、不维护与 Zotero 竞争的第二数据库。

## 2026-11-01 P0 Task 1 结构复核与收件箱整理

全局工具链续接只读复核后的最新 Zotero 实际结构为 9 个主题集合（首轮 85 条快照保留，当前为 84 条）：
`01_风险事件与安全指标`（15）、`02_混合自动驾驶传播与控制`（14）、`03_闭环仿真与场景测试`（7）、`04_人类行为交互与轨迹预测`（5）、`05_非局部交通流模型`（12）、`06_类超距与因果理论`（19）、`07_微观跟驰校准与轨迹重放`（14）、`08_拥堵状态识别与时空传播`（3）、`09_仿真校准规范与验证`（1）。收件箱 `补充文献-未分类` 保留且当前为 0 条；主题集合去重后共有 84 个唯一 item key。

此前“共 56 条、六集合”的记录保留为历史审计事实，不覆盖、不回写。P0 Task 1 未批量移动、合并或删除条目；新发现论文的正式登记见 `docs/research/P0/PAPER_REGISTER.csv`，该 CSV 不是 Zotero 的替代数据库。

P0 Task 1 通过 Zotero 本机 DOI 导入了 Jerath 2024、Peng 2026、Schönhof 2006、Hudgens–Halloran 2008、Aronow–Samii 2017 和 Wang 2024 冲突图论文元数据，并将可核验条目挂入 AAD 及相关主题集合。Jerath 与 Aronow 自动获得 PDF 附件。Wang 2024 冲突图已有旧 AAD 条目，新增记录只作重复标记，不合并、不删除。2026-11-01 又依据当前 P0/Stage 0.5 项目主线整理了 `补充文献-未分类` 的 7 条记录：2 条补入主题集合，5 条保留已有主题挂载并移出收件箱；条目 key、附件、元数据和标签均保留。逐条计划、执行前后集合和理由见 [zotero_clean_2026-11-01_plan.json](zotero_clean_2026-11-01_plan.json) 与 [zotero_clean_2026-11-01_execution.json](zotero_clean_2026-11-01_execution.json)。

- 2026-10-16 退役本地 `literature/` PDF 文件夹：59 份 PDF 删除前逐个 md5 与 Zotero 存储副本核对一致（记录见 [README_归档说明.md](README_归档说明.md)，为历史文档）。
- 2026-10-16 完成一次只读审计：实际结构、数量、重复与元数据质量见 [zotero_audit_2026-10-16.md](zotero_audit_2026-10-16.md)（含建议的分类调整对照表与跨项目重复条目清单，item key 可追踪）。
- `混合自动驾驶风险传播_文献总表.xlsx`：历史整理总表（含 2026-07-16 检索的影响因子及来源），作为历史资料保留；其影响因子/CCF 当前值未复核，引用时标注 `Unverified`，以 Zotero 条目维护流程刷新为准。

## 新增文献流程（固定规范）

1. **导入**：优先用 DOI / 正式出版页 / Zotero Connector 导入到 Zotero（避免手敲元数据）。
2. **查重**：先按 DOI 检索确认库内是否已有同一论文，避免重复条目（注意与 DRIFT 等其他项目集合的跨项目重复，见审计 §4）。
3. **补全元数据**：核对 DOI、正式题名、作者、年份、期刊、卷期页码/文章号；Retrieve Metadata 修复缺失字段。
4. **归类**：加入 `TJU → AAD` 与一个或多个主题子集合（01–09）；主题可多挂，PDF 不复制。未能立即判断的条目先放入 `补充文献-未分类`，完成判断后再移出。
5. **补充信息**：需要期刊指标时在 Zotero 条目内记录 CCF/影响因子**并注明来源与检索日期**；无法核实的不填、不猜。
6. **标签**：主题集合为主要分类；标签只用于补充（如 `NC`、阅读状态、方法特征），不用标签替代主题分类。
7. **引用**：论文写作引用时使用 Zotero 条目（DOI/正式来源可追溯），不在仓库重建引用库。

## 历史主题集合基线（2026-10-17，经研究者批准执行）

`01_风险事件与安全指标`（7）、`02_混合自动驾驶传播与控制`（11）、`03_闭环仿真与场景测试`（7）、`04_人类行为交互与轨迹预测`（4）、`05_非局部交通流模型`（11）、`06_类超距与因果理论`（16），共 56 条；一层结构。原 `NC_统一汇总` 已退役删除（11 篇 NC 论文改由 `NC` 标签追踪，均挂主题集合）。这是历史基线，不覆盖当前 9 个主题集合和 2026-11-01 索引。调整的批准、执行与逐条 before/after 记录见 `zotero_audit_2026-10-16.md` §7 与 `zotero_reorg_2026-10-17_execution.json`。

## 边界

- 研究者私人笔记不属于项目上下文，不扫描、不迁移。
- 不向 GitHub 导出 PDF、批注、笔记或整库数据。
- 大规模集合重构、批量移动、合并重复条目须先经研究者批准并记录 item key 与原集合关系；低风险调整（单条目补挂、标签规范化、有来源的元数据修正）可在记录后执行。
- 7 对 AAD↔DRIFT 同 DOI 重复条目按研究者 2026-10-16 决定暂不合并，双方 item key 原样保留；后续合并需单独批准。
- 写入授权：如需程序化写入，使用 Zotero 10 本机 API 官方授权流程（`POST /api/local/authorize`，研究者在客户端内确认）；禁止读取或改动 Zotero 数据库文件本身。
- 工具链约束：本项目的整理脚本只使用 Zotero 本机 HTTP API；禁止使用 Computer Use、桌面 UI 自动化或直接数据库访问。通用流程版本保存在仓库 `skills/zotero-clean/`；全局 skill 已安装在 `C:\Users\Lenovo\.codex\skills\zotero-clean\`，可在任意科研项目使用 `$zotero-clean`。每次按目标项目指定库、根集合、收件箱与输出目录；全局 skill 不固定 AAD、用户库 ID 或日期。
- `zotero-clean` 分四层：Level 1 只整理新增未分类条目；Level 2 对全项目做只读查重、冲突和失效候选审计；Level 3 在冻结规则并获批准后重构子分类；Level 4 在逐条批准后处理重复合并、冲突修复与退役/删除。年龄、缺 PDF 或低引用量本身不构成失效依据。
- 首轮历史索引：`AAD_ZOTERO_INDEX_2026-11-01.md` 与 `.csv` 由实时 Zotero 集合生成，逐条列出 item key 与主题集合；执行前后记录见 `zotero_clean_2026-11-01_execution.json`。
- 首轮只读全项目审计见 `zotero_clean_audit_20261101.md` / `.json`：发现 1 个 AAD 内 DOI 重复候选（`5LYN24YV`/`BYCXQ5A3`，已按 P0 决策保留未合并）、1 个无 DOI 的同题名候选，以及 6 个缺期刊字段的复核候选；这些不在本次 Level 1 收件箱任务中自动删除或合并。
- PDF 口径：退役本地 `literature/` 曾有 59 份 PDF；历史六主题基线为 56 条。当前专题索引包含新增方法与 P0 条目，附件数量不从历史 56 条推断，缺失情况以 Zotero 条目逐条核验。

## 全局 skill 与 AAD 工具链（2026-11-01）

当前本机 API 库为 `http://127.0.0.1:23119/api/users/18841865`；AAD 根集合 key 为 `TGJP2TIA`，收件箱 key 为 `BXMY8MBN`。授权 key 仍只从仓库外的 `D:\hermes\cache\zotero-local-key.json` 读取；其他环境通过 `ZOTERO_LOCAL_KEY_PATH` 指定，不写入 Git、索引或日志。API 库通过 `--base`、`ZOTERO_LOCAL_BASE` 或 `ZOTERO_LIBRARY_ID` 指定，无需改变全局用户配置。

在任意工作目录运行已安装脚本即可回读本次归类结果（只读）：

```powershell
$zoteroCleanScript = 'C:/Users/Lenovo/.codex/skills/zotero-clean/scripts/zotero_clean.py'
python $zoteroCleanScript --base http://127.0.0.1:23119/api/users/18841865 --plan D:/shen/TJU/AAD/doc/literature-notes/zotero_clean_2026-11-01_plan.json --verify
```

全局脚本的列表读取已分页；索引/审计遍历项目根集合及全部嵌套集合，保留只挂根集合或收件箱的条目。历史 `AAD_ZOTERO_INDEX_2026-11-01.*` 与本次分类执行记录保留；通用化续接只补计划/执行记录的 `project_name` 描述字段，没有重跑分类写入。辅助审计覆盖精确匹配、缺失字段和状态关键词候选；近似重复、出版商信息、撤稿证据及孤立附件仍须另做只读复核。

最新只读快照为 [AAD_ZOTERO_INDEX_20261101-global.md](AAD_ZOTERO_INDEX_20261101-global.md) / `.csv` 与 [zotero_clean_audit_20261101-global.md](zotero_clean_audit_20261101-global.md) / `.json`：9 个主题集合、84 个唯一条目、收件箱 0 条、精确 DOI 和题名/作者/年份候选均为 0，元数据复核候选仍为 6。首轮快照中的 `BYCXQ5A3` 当前 GET 返回 `deleted=true`，不在实时集合清单中；删除时间与执行者 `Unknown`，本次续接 Zotero 写入次数为 0，不恢复或改变该条目。历史审计的题名/作者/年份匹配可能与 DOI 候选重叠，不能据旧报告标题将其断言为“无 DOI”。逐项核验记录见 [zotero_clean_2026-11-01_continuation.json](zotero_clean_2026-11-01_continuation.json)。

## 2026-10-30 Task6 文献复用入口

Task6 复用 Zotero 既有条目及项目已读全文笔记；未新增 PDF 库或重复条目。逐条区分作者发现、解释、项目借鉴与待验证假设，见 `docs/STAGE_0_5_ROUND2_TASK6_REAL_SIM_MICRO_INTERACTION_ANALYSIS_20261030.md` 及 `evidence/results/RES-STAGE-0.5-ROUND2-TASK6-REAL-SIM-MICRO-INTERACTION-20261030/literature_review.json`。
