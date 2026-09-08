# AAD 长期科研协作体系收口计划

> 日期：2026-09-08
> 状态：执行中
> 目标：补齐 2026-09-08 首轮重构后的状态漂移、结果证据不可移植、机器登记字段不足、自动验收覆盖不足和用户学习入口缺口，使仓库满足长期人机科研协作要求。

## 范围与非目标

本轮只修改项目治理、索引、证据快照、校验代码、测试和 CI。不得改变研究问题、算法原理、模型结构、loss、评价指标、研究假设、科研结论、实验 Gate 或正式实验逻辑。

大型原始数据、Parquet/CSV 运行表、人工标注密封键和完整本地输出继续保留在本机或既有受控存储，不直接纳入 Git。Git 中只保存能够证明状态和定位原始证据的小型 audit、manifest、provenance、checksum 与汇总快照。

## 任务 1：先定义严格校验行为

涉及：

- `code/tests/test_project_docs.py`
- `code/src/riskprop/project_docs.py`
- `code/scripts/validate_project_docs.py`

先增加失败测试，要求校验器能够发现：登记表必填字段缺失、实验与结果非双向关联、可移植证据未被 Git 跟踪、旧式 transient Git 状态声明，以及结果证据哈希或来源字段缺失。确认测试按预期失败后再修改实现。

验收：聚焦测试先红后绿；默认模式可在工作树中校验结构，`--strict-git` 可在提交/CI/纯 Git 检出中校验可移植性。

## 任务 2：建立可移植证据快照

涉及：

- `code/scripts/export_project_evidence.py`
- `evidence/README.md`
- `evidence/results/`
- `evidence/EVIDENCE_MANIFEST.json`

从当前本机正式输出中只导出登记结果所需的小型 JSON、manifest、provenance、SHA256SUMS 和独立分析汇总。导出清单记录结果 ID、源路径、Git 路径、字节数和 SHA-256；排除 Parquet、原始 CSV、HTML、图片、日志和密封抽样键。

验收：导出可重复；清单与文件哈希一致；所有登记结果至少有一个 Git 可跟踪的证据入口；原始本地输出路径仍作为二级定位信息保留。

## 任务 3：升级双向科研登记

涉及：

- `docs/PROJECT_REGISTRY.json`
- `docs/EXPERIMENT_INDEX.md`
- `docs/RESULTS_INDEX.md`
- `docs/HISTORY_INDEX.md`
- `docs/RESEARCH_STATUS.md`

将登记表升级为 v2。每个当前实验结构化记录实验名称、目的、研究问题、日期、状态、代码与执行版本、配置、参数、数据版本、模型/checkpoint、结果 ID、核心指标、当前结论、Gate 和科学资格；每个结果反向记录实验 ID、证据快照、原始位置、代码/配置/数据来源、指标、结论、Gate、论文位置和可移植性。

历史 Pilot 按稳定 ID 登记尝试目的、代码、输出、当前历史地位、被替代原因和可用边界，支持回答“是否试过”和“为什么不用”。

验收：实验到结果、结果到实验双向一致；当前索引不再把已提交实现描述为 dirty/untracked；运行时历史 provenance 与当前代码位置明确分开。

## 任务 4：补齐用户重新掌握项目的学习入口

涉及：

- `docs/LEARNING_PATH.md`
- `docs/METHOD_AND_ALGORITHM_GUIDE.md`
- `README.md`
- `docs/PROJECT_INDEX.md`

学习路径覆盖研究问题、核心思想、算法原理、方法设计、实验逻辑、结果含义、当前问题和后续方向。算法指南按“解决什么—直觉—为什么—怎么做—数学—代码—实验影响”解释四格识别、消息生命周期、时间展开物理路径、TTC/DRAC 风险测量、现实校准和协议锁；公式解释变量和方向，不新增未经确认的方法。

验收：用户和新 AI 均可从一个入口逐层定位到公式、实现、测试、实验与结果证据。

## 任务 5：重写当前交接并消除漂移

涉及：

- `PROJECT_CONTEXT.md`
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/CHANGELOG.md`

移除“当前 HEAD 写死在同一个提交内”的自引用设计，改用“本文件所在提交 + 运行时 Git 命令”语义；准确记录当前工作树、已提交实现、实验 Gate、阻断和唯一继续点。保留 E00 在旧 dirty 工作树运行的历史 provenance，不把当前提交误写成当时的实验运行版本。

验收：无过时 dirty/untracked 声明；交接所需类别齐全；瞬态 Git 状态由运行时命令核验。

## 任务 6：建立自动闭环并完成纯 Git 验收

涉及：

- `.github/workflows/project-integrity.yml`
- `AGENTS.md`
- `docs/CHANGELOG.md`

CI 在 push/PR 时安装项目、运行严格项目文档校验和相关测试。最终在当前工作树运行全量测试、编译、严格校验、哈希校验和 diff 检查；提交后再从 `git archive HEAD` 生成纯 Git 检出，确认其中不依赖本机 ignored 输出也能通过严格校验。

验收：当前工作树与纯 Git 检出均通过；工作树干净；提交按逻辑分组并同步到既有 `origin/main`。

## 回滚与保护

- 所有既有原始输出保持原位，不覆盖、不删除。
- 新增证据快照是只读副本，来源与哈希写入清单。
- 任何校验失败都停止提交或推送，保留准确错误。
- 科研 Gate 仍由 `protocol_lock_readiness_v1.json` 决定，本轮不得改变其值。
