# AAD Current State Snapshot

> 核对日期：2026-10-10（Asia/Shanghai）
> 事实基线：任务 1.4 当前工程状态以核验报告和 `RES-STAGE-0.2-TASK-1.4` 为准；阶段 Gate 仍未闭合，瞬时状态须实时查询。

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

## 2026-10-10 任务 1.3 轨迹身份与测量链验证

报告：`docs/STAGE_0_2_TASK_1_3_TRAJECTORY_IDENTITY_VALIDATION_2026-10-10.md`。US-101 三个 TXT 共 4,098,933 行，独立全量测量链产物位于 `code/outputs/formal/calibration/stage_0_2_task_1_3_us101_txt_20261010_r2/`，有效 TTC 1,728,280 行、候选事件 2,604 个。Lankershim 1,607,319 行保留，基于原始 `Frame_ID` 冲突建立 2,654 个确定性诊断片段；228 行身份不确定、1,379 行观测缺口。单帧有效 TTC 483,098 行，其中 482,470 行通过保守连续性筛选。正式科学事件单位和最终阈值仍未冻结，Protocol Lock/Stage I 继续禁止。

## 最近的重要项目变化

- 当前阶段与入口统一为“阶段 X.X”/`stage_X_Y`。
- 研究者于 2026-09-10 明确批准 pNEUMA 前车推断与人工复核退役；相关代码、输出和证据保留在 legacy/history。
- 建立 `AI_CONTEXT/`，并将长期 Research Engineer 协作边界固化到 `AGENTS.md`。

## 当前 Git branch

`main`。实时核验：`git branch --show-current` 与 `git status --branch --short`。

## 对应的最新 commit

任务 1.4 实现版本由文件所属 Git 提交及本轮 provenance 的实现 SHA-256 追溯；历史对照基线为 `da4072909a93c16e96e89fa436fd23127a581b69`。AI_CONTEXT 自身的最新提交用 `git log -1 --format=%H -- AI_CONTEXT` 查询，仓库实时 HEAD 用 `git rev-parse HEAD` 查询。

## 2026-10-10 任务 1.4 当前工程基线

报告：`docs/STAGE_0_2_TASK_1_4_RELIABILITY_CLOSURE_2026-10-10.md`；证据：`RES-STAGE-0.2-TASK-1.4`。Lankershim 两个诊断时钟锚解释 936 个旧异常编号；按字段序列建立 2,442 段，全部 1,607,319 行保留、无同编号同时间冲突，有效 TTC 483,098 行，原始/可靠候选各 2,777、拒绝 0。US-101 4,098,933 行核心测量与任务 1.3 等值，候选事件仍 2,604。任务 1.3 的 482,470 是有效 TTC 排除行级标记后的数量，不是已验证连续事件；旧实现不确定标记只切段，未可靠排除。本轮修复并区分后车/前车、完整序列和记录/段级可靠性。字段 confirmed 不代表官方物理身份；source_period=unknown。建议任务 1 工程验收，等待研究者；Stage 0.2 科学 Gate 仍 Active，不启动任务 2/协议锁/Stage I。

## 2026-10-10 任务 1.5 当前工程基线

报告：`docs/STAGE_0_2_TASK_1_5_LEADER_MATCHING_CLOSURE_2026-10-10.md`；结果：`RES-STAGE-0.2-TASK-1.5`；最终产物为 `code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4`。Lankershim 1,226,499 条报告前车在时间、诊断时钟锚、Frame_ID 和编号约束下均唯一；真实跨时钟匹配 0，跨时钟有效 TTC 0。匹配键修复并增加显式时钟缺失/冲突阻断，四源状态核心与任务 1.4 0 行差异，事件数保持 US-101 2,604、Lankershim 2,777；全量测试 201 passed。任务 1 建议关闭，等待研究者审核；Stage 0.2 科学 Gate 仍 Active。

## 2026-10-10 任务 2 当前基线

报告：`docs/STAGE_0_2_TASK_2_RISK_QUALITY_AUDIT_2026-10-10.md`；结果：`RES-STAGE-0.2-TASK-2`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_risk_quality_audit_20261010_r4`。四个 NGSIM 校准 state 共 5,706,252 行、2,211,378 条有效 TTC；质量状态、有限值分布、极端记录追溯和完整状态序列上的 6×4 事件敏感性网格已完成。TTC/DRAC 为重尾，当前结果仅支持描述性校准和后续人工复核；最终阈值、事件规则、暴露分母和科学 Gate 仍 Active。

## 2026-10-10 任务 2.1 当前基线

报告：`docs/STAGE_0_2_TASK_2_1_EXTREME_REVIEW_2026-10-10.md`；结果：`RES-STAGE-0.2-TASK-2.1`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_1_extreme_review_20261011_r4`。固定种子分层案例 447 个，独立前车唯一匹配 447 个，公式重算浮点误差范围内一致；自动分类 C=399、D=48、A/B=0。物理真实性仍需人工/独立几何复核，科学事件规则和 Gate 仍 Active。

## 2026-10-11 任务 2.2.1 最终修复

连续风险边界现按前一帧边定义，风险段统计保留段首帧；固定 447 案例已在独立 r9 产物重算。多帧连续 298、单帧 3、间歇 0、边界 25、无极端 121；自动 C=349、D=98。48 案例包和 PDF 图册已重生成，人工字段为空，物理真实性仍 Unverified。

## 2026-10-11 任务 2.3

任务 2.3 完成工程质量与探索性稳健性收口：5,706,252 条 state、2,211,378 条有效 TTC、5,381 个正式基线候选事件已核对；独立重提取 S0=5,880，差异保留为 Unverified。447 个案例中心定位 unique=447，几何/物理真实性仍 Unverified。Protocol Lock 与 Stage I 继续禁止。
