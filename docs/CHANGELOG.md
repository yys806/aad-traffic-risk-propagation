# AAD 项目信息结构变更记录

只记录影响项目导航、科研状态、实验/结果追踪、协作规则或复现入口的重要变化。代码细节仍以 Git diff 和实验记录为准；本文件不替代实验日志。

## 2026-09-08 — 建立长期科研协作与双向追踪入口

- 新增根 `AGENTS.md`，明确 Human-driven、AI-accelerated、独立判断、证据边界和持续维护义务。
- 新增 `PROJECT_INDEX`、`ARCHITECTURE`、`RESEARCH_STATUS`、`EXPERIMENT_INDEX`、`RESULTS_INDEX`。
- 新增机器可读 `PROJECT_REGISTRY.json`，登记当前实验、结果和关键 Gate 路径。
- 新增 `riskprop.project_docs` 与 `validate_project_docs.py`，检查稳定入口、路径和实验/结果 ID 同步。
- 更新 `PROJECT_CONTEXT.md` 的交接后入口说明，保持后续会话阅读顺序一致。
- 保留旧 README、旧导航、历史实验和当前脏工作树；本批未移动、删除或改写科研算法和原始产物。

## 2026-09-08 — 受控物理整理

- 将根目录导师批注修订的 `findings/progress/task_plan` 归档到 `记录/项目历史/导师批注修订_2026-08-27_2026-08-29/`。
- 将一次失败的 XeLaTeX 日志归档到主论文工作稿构建日志目录。
- 将根 `tmp/` 的637个文件和根 `.pytest_cache` 的5个文件整体迁入被 Git 忽略的 `code/tmp/`；未删除内容，迁移前后树哈希一致。
- 将14个历史 Pilot 模块、10个命令和9个测试迁入各自 `legacy/` 子目录，保留顶层兼容导出与 `riskprop` CLI。
- 新增显式 `riskprop-legacy` 控制台入口，原 `riskprop` 名称仅作为向后兼容入口保留。
- 迁移清单、前后哈希和验证结果见两个 2026-09-08 maintenance manifest。
