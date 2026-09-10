# AAD Confirmed Decisions

本文件只记录研究者明确决定或已存在的稳定项目约束，不把 Codex 分析写成科研决策。

## 2026-09-10 — pNEUMA 当前职责

- 日期：2026-09-10。
- 决策内容：研究者明确决定批准 pNEUMA 前车推断与人工复核退役；pNEUMA 当前只承担城市运动学校准。
- 相关背景：阶段化迁移发现旧人工 QA Gate 与拟定的新职责冲突，Codex 停止并请求决定后获得批准。
- 影响范围：阶段 0.3、阶段 0.5、注册表、代码/脚本/测试 legacy 边界及历史证据。
- 对应代码：`code/src/riskprop/real_trajectory.py::read_pneuma_wide()`；退役实现位于 `code/src/riskprop/legacy/pneuma_mapmatch.py`、`pneuma_qa.py`。

## 2026-09-10 — 长期人机协作机制

- 日期：2026-09-10。
- 决策内容：Codex 作为 Research Engineer；科研决策归研究者，ChatGPT 网页端承担讨论与科研解释；Codex 维护工程、实验事实、Git 和 AI_CONTEXT。
- 相关背景：项目需要由研究者、ChatGPT 与 Codex 长期协作，并能从 GitHub 快速恢复状态。
- 影响范围：`AGENTS.md`、`AI_CONTEXT/`、任务验证、提交和推送流程。
- 对应代码：`code/src/riskprop/project_docs.py` 检查长期上下文文件。

## 已有稳定约束

- AAD 是当前项目，`D:\shen\TJU\DRIFT` 只读。
- 现有阶段 0 结果不构成核心科学效应；协议锁通过前不得进入阶段 1.1。
- 缺失不补零，不可观测不推断，不通过看 holdout、挑种子或降低阈值制造正向结果。
- 历史结果保留式归档；机器事实源与人类索引同步更新。
