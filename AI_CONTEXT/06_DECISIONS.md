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

## 2026-10-10 任务 1.4 边界授权

Agreed：具有明确字段证据的诊断片段可作为候选事件的保守连续性边界，不视为官方物理轨迹；不确定前后车不得进入可靠事件，原始候选和拒绝原因须保留。来源 unknown 不伪造，最终科学事件规则与阈值未决定。实现与全量证据见任务 1.4 报告及 RES-STAGE-0.2-TASK-1.4。


## 2026-10-11 — Stage 0.2 科研设计确认

状态：`Agreed Research Design`；以下设计已由研究者确认，但不等于已实现、已验证或 Scientific Gate 已通过。

- 研究范围：目标区域纵向闭合风险负担，不代表总体交通安全风险或事故概率。
- 源事件：P2 为主要候选（可靠 TTC<2.0 s，连续风险观测首末跨度≥0.2 s）；`t_confirm` 必须是实际观测确认时刻；缺失/身份中断不代表风险解除；短间隔事件不合并，消息去重另行处理；TTC 触发，DRAC 仅用于严重程度和稳健性；P1/P3 保留为敏感性对照。
- 连续风险：可靠有效闭合 TTC 使用 `rho=exp(-TTC/tau)`，不以 P2 阈值截断；保留 valid/not_applicable/invalid/not_measurable 语义；区分瞬时 rho 与贡献 b；未知归属或测量贡献用 [0,1] 上下界；固定目标车辆/边界/窗口、无跨缺帧插值、车辆等权、窗口时间积分和上下界 DID。
- 校准：tau 使用四来源可靠闭合 TTC 的来源内时间加权中位数，最终为排序中间两来源平均；同时报告来源异质性及 tau/2、2tau；极端值保留并做敏感性；NGSIM 现实参考分为基础跟驰、连续风险负担和 P2 事件特征；SUMO 覆盖属于 Stage 0.5。
- 未冻结：消息去重时间窗、正式质量门槛、Stage 0.5 容差、最终实现默认值和 Protocol Lock。
