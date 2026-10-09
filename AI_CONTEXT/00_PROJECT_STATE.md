# AAD Current State Snapshot

> 核对日期：2026-09-10（Asia/Shanghai）
> 事实基线：阶段化迁移与 Gate 状态同步至提交 `39c425e8ae9e915c0cd7cfea1b2454b8fbdac04d`；瞬时状态仍须实时查询。

## 当前研究阶段

项目处于阶段 0：测量、现实证据边界、仿真适用域与协议锁准备。阶段 1.1 核心效应确认尚未实现、未运行，并被协议锁阻断。依据：`docs/PROJECT_REGISTRY.json`、`docs/RESEARCH_STATUS.md`。

## 当前主要研究目标

验证来源可追溯且被控制器采用的远端风险消息，能否在普通物理影响到达目标区域前改变车辆动作与区域总体风险。当前工程目标是先闭合阶段 0 的测量与准入证据，不生成核心效应结论。

## 当前模型版本

当前没有可核验的可训练模型、训练循环、loss 或 checkpoint。正式代码是确定性测量、SUMO 工程运行、覆盖审计与协议准入工具；阶段 1.1 的模型为 `not_determined`。依据：`code/pyproject.toml`、`code/src/riskprop/`、注册表 `model`/`model_checkpoint` 字段。

## 当前主要实验

- `stage_0_2`：NGSIM 跟驰风险审计，`Active`，当前主任务。
- `stage_0_3`：pNEUMA 城市运动学校准，数据已就位但正式产出未开始。
- `stage_0_4`：SPMD 接收状态连续性边界已验证，packet 级字段仍不可用。
- `stage_0_5`：仿真—现实覆盖，缺按新分工生成的参考包和 SUMO 样本。
- `stage_0_6`：技术真值检查已有证据，科学容差与协议锁未完成。

## 当前最重要的问题

阶段 0.2 异常与极端值尚未收口；阶段 0.3 无专用正式统计产物；阶段 0.5 缺 SUMO 校准样本；科学容差和样本量未冻结。当前便携 readiness 是迁移前旧键快照，只能证明当时 `protocol_lock_allowed=false`。

## 当前下一步

按已登记顺序：收口阶段 0.2 与 0.3；冻结阶段 0.4 的有限证据边界；完成阶段 0.5；再完成阶段 0.6 科学参数冻结与协议锁。协议锁通过前不得进入阶段 1.1。

## 2026-10-09 Stage 0 基线核查

只读审计报告：`docs/STAGE_0_BASELINE_AUDIT_2026-10-09.md`。六个登记数据文件均存在，完整文件 SHA-256 与历史下载清单一致，总大小 1,862,308,265 bytes（1.862 GB）。I-80、Peachtree 与 SPMD holdout 只做文件级核验，未解压或查看内容。当前结论仍为 0.2/0.3/0.5/0.6 未闭合，Protocol Lock 未创建，Stage I 禁止启动。

## 2026-10-09 任务 1 NGSIM 基础核验

报告：`docs/STAGE_0_2_TASK_1_NGSIM_INTEGRITY_2026-10-09.md`。US-101 三窗口各 1,048,575 行，程序 parquet 与 ZIP CSV 一致，但每窗口各有一个 `Total_Frames` 不一致车辆，不能确认与官方完整窗口一致。Lankershim 有 228 个非递增车辆内时间步、936 个多 `Total_Frames` 车辆，身份/分段边界未解决。公式与单位真值夹具通过；任务 1 未验收，需任务 1.1。

## 2026-10-09 任务 1.1 来源与分段核查

报告：`docs/STAGE_0_2_TASK_1_1_NGSIM_SOURCE_SEGMENTATION_2026-10-09.md`。US-101 同 ZIP 内 TXT 已证明比 CSV 完整；任务 1.2 更正无表头首行计数为 1,180,598、1,403,095、1,515,240。官方元数据建议使用 TXT，但不保证数据完整性。Lankershim 官方设计为两个 15 分钟源文件，当前包只有合并 CSV；编号复用主要原因仍为 Inference，未由源文件证实。

## 2026-10-09 任务 1.2 TXT 接入与源恢复

报告：`docs/STAGE_0_2_TASK_1_2_TXT_SOURCE_RECOVERY_2026-10-09.md`。US-101 三个 Stage 0.2 输入已切换到 ZIP 内原始无表头 TXT，读取器固定校验 18 列、来源标识和精确行数；9 项相关测试通过。Lankershim 当前包仍无两个独立官方源文件，正式身份/分段规则未修改，任务 1.3 仍需研究者决定源不可得时的保守方案。

## 最近的重要项目变化

- 当前阶段与入口统一为“阶段 X.X”/`stage_X_Y`。
- 研究者于 2026-09-10 明确批准 pNEUMA 前车推断与人工复核退役；相关代码、输出和证据保留在 legacy/history。
- 建立 `AI_CONTEXT/`，并将长期 Research Engineer 协作边界固化到 `AGENTS.md`。

## 当前 Git branch

`main`。实时核验：`git branch --show-current` 与 `git status --branch --short`。

## 对应的最新 commit

本快照所描述的当前源码基线为 `39c425e8ae9e915c0cd7cfea1b2454b8fbdac04d`。AI_CONTEXT 自身的最新提交用 `git log -1 --format=%H -- AI_CONTEXT` 查询，仓库实时 HEAD 用 `git rev-parse HEAD` 查询。
