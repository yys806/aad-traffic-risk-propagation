# P0 Task 3：验证与交付边界记录

日期：2026-11-01。任务基线：`b2d7e92fa09ecdffbfcbaa3e65a5d6c64ff0b268`，`main`，开始时工作区干净。

## 1. 影响判断

仅修改科研设计文档、引用/能力/功效表和索引/AI_CONTEXT/研究审计注册项。无正式科研源码或 config 变化；无新实验、结果登记、既有结果 audit/manifest/provenance/SHA256SUMS 或证据导出索引变化。正式 `current/experiments/results/history` 注册对象与基线保持相等。AGENTS、上游 DRIFT 和 OB 规划不修改。

最小充分验证：项目文档严格 Git 校验、48 项矩阵/77 项敏感性数据的一致性与算术、来源链接/哈希/本地证据路径、Proposal/阶段边界与 diff。无需全量 pytest、compileall、Task20 fixture、纯 Git 克隆或 evidence exporter；不将软件/文档检查解读为科研方案批准。

## 2. 检查结果

| 检查 | 结果 | 覆盖范围 |
|---|---|---|
| `python code/scripts/validate_project_docs.py --strict-git` | **PASS — PROJECT_DOCS_OK** | 注册/导航/实际路径与 Git 跟踪要求；不是科研 Gate |
| 定向交付物检查 `check_deliverables.py` | **PASS — 14 项** | 48 项矩阵、四级枚举、来源编号/Markdown 与 CSV 一致、77 项功效算术、相对链接、注册对象/变更范围与授权标志 |
| 来源与只读输入 | **PASS** | 9 个官方 HTTP200 快照/hash/技术定位；27 个不应修改的本地输入 hash；OB 规划原路径 hash 不变 |
| 注册表语义比较 | **PASS** | `current/experiments/results/history` 及 Task1/2 审计与基线相同；仅新增 Task3 研究审计/7 个入口 |
| `git diff --cached --check` | **PASS** | 无新增 whitespace 错误；仅 18 个授权文档/机器表/索引文件 |

验证原始输出位于本地 `code/outputs/analysis/p0_task3_20261101/validation_checks.json`，检查脚本同目录。功效演示假设没有使用实验数据，没有将正态近似解释为最终样本量。本次无工程验证失败或无关历史测试修复。Git 提示的既有 LF/CRLF 转换未扩展为换行清理任务。

## 3. 来源和本地工作产物

Git 交付包含最终报告、平台比较 Markdown/CSV、决策清单、来源登记 JSON、功效敏感性 CSV 和本记录。已有实验包只读引用，不重新打包。

本地忽略目录 `code/outputs/analysis/p0_task3_20261101/` 保存 `S1`–`S9` 官方网页/抽取文本、`build_source_register.py`、`build_tables.py` 和本次验证输出；无新交通/人类数据。网页原件不进入 Git/便携证据；可按 source_register 中的响应 SHA 复核，官网更新后的重取内容可能不同。功效表按报告公式可独立复算，不需要实验数据。

有界来源核查保留的异常：DSRI 旧猜测路径 `/simulators/nads-1` 返回 HTTP 404，随后从官网主页链接定位 `/nads-1` 并得到 HTTP 200；首次终端显示 NADS 页面时遇 GBK 编码错误，改 UTF-8 后读取成功。这些是资料获取/显示记录，不是实验或测试失败。未重复开展 Task2 文献调研，未新增 Zotero 条目。

## 4. Context Consistency Check

逐项检查当前状态、研究背景、架构、数据流、模块关系、实验、决策、已知问题及历史。本次影响状态/研究背景/实验设计边界/Proposal 决策依赖/已知问题/变更历史；因此更新 AI_CONTEXT `00/01/05/06/07/08`，同步 `PROJECT_INDEX`、`RESEARCH_STATUS`、`STAGE_INDEX`、`CHANGELOG` 和注册表 `research_audits.p0_task3`/新文档 canonical entries。源码/架构/数据流/模块接口未变，`02/03/04` 无需更新；结果索引/便携证据未变。

研究设计全部 Proposal。Stage 0.5 有限关闭与科学 Gate blocked、Stage 0.6 Pre-Lock blockers、Protocol Lock blocked、Stage I engineering-only、Stage 1.1 not authorized 保持原状。主线规划 hash 与读取时一致。外部资源、最终 n 和研究者科学选择仍 Unknown/待决定。

## 5. Git 与停止点

完成验证后只创建本地 Conventional Commit；远端 Push 不在授权范围内。任务完成后停止，不进入 Task4、后续阶段或实验。
