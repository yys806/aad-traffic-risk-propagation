# AAD Current State Snapshot

> 核对日期：2026-10-12（Asia/Shanghai）
> 当前事实基线：`RES-STAGE-0.2-FINAL-CLOSURE` 与 `docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；其后按日期排列的任务记录保留历史状态。阶段 Gate 仍未通过。

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

阶段 0.2 工程、异常诊断与描述性证据已收口，独立物理真实性与科学质量验收裁决未完成；阶段 0.3 无专用正式统计产物；阶段 0.5 缺 SUMO 校准样本；科学容差和样本量未冻结。当前便携 readiness 是迁移前旧键快照，只能证明当时 `protocol_lock_allowed=false`。

## 当前下一步

按已登记顺序：研究者审阅阶段 0.2 科学验收准备包并解决两项核心阻断，收口阶段 0.3；冻结阶段 0.4 的有限证据边界；完成阶段 0.5；再完成阶段 0.6 科学参数冻结与协议锁。协议锁通过前不得进入阶段 1.1。

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

## 2026-10-11 任务 2.4

任务 2.4 完成正式候选事件提取等价性与稳健性最终验证。独立实现补齐正式 0.1 s 首末时间跨度条件后，与 `extract_rear_end_events()` 四源逐事件等价：总计 5,381，成员集合、时间边界和极值一致；任务 2.3 的 5,880 与正式基线差异由不可比的最小持续时间/正式连续性语义造成。S1 在完整 state 副本上真实重跑质量条件，raw/reliable/rejected 为 5,381/5,381/0。S2a/b/c/d 探索性屏蔽后事件数为 5,366/5,353/5,263/5,235。连续跟驰暴露按严格相邻帧分段，同时保留首末跨度与覆盖时长。报告：`docs/STAGE_0_2_TASK_2_4_EVENT_EQUIVALENCE_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_4_20261011_r2/`。科学阈值、事件规则、暴露分母和 Stage 0.2 Gate 仍未冻结。

## 2026-10-11 任务 2.5

任务 2.5 完成源端 TTC 阈值与最小持续时间联合敏感性、事件级参数对应、因果确认时刻、非插值采样限制、24 个定向真实案例选择和文献证据矩阵。四源 6×4 事件数（TTC 1.0/1.5/2.0/2.5/3.0/4.0 s；持续 0.1/0.2/0.3/0.5 s）已封存，2.0 s 基线为 5,381。所有候选参数均为 Proposal；未冻结正式规则、Protocol Lock 或 Scientific Gate。报告：`docs/STAGE_0_2_TASK_2_5_THRESHOLD_VALIDATION_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_5_20261011_r1/`。


## 2026-10-11 任务 2.5.1

P1/P2/P3 定向验证已完成：成员级事件重叠图 20,171 条边，事件数 P1=1,900、P2=4,545、P3=8,523、工程参考=5,381；24 个案例全部重新生成记录与 24 页图册，保留 Lankershim 原始行 31,245。在线确认时刻由实际观测验证，P1/P2/P3 中位 onset→confirm 分别为 0.3/0.2/0.1 s。rejected 通过 event_id 与 raw 候选联接；公平 200 ms 采样敏感性仍 Unresolved。文献 2021 surrogate-measure 条目已更正为 Lu et al., Accident Analysis & Prevention 162, 106403, DOI 10.1016/j.aap.2021.106403。所有参数仍 Proposal / Pending Parameters / Not Frozen，科学 Gate、Protocol Lock 和 Stage I 均未启动。报告：`docs/STAGE_0_2_TASK_2_5_1_TARGETED_VALIDATION_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_5_1_20261011_r2/`。


## 2026-10-11 任务 2.5.2

基于 Task 2.5.1 成员级结果完成关键差异案例分析：中心事件按 source、车辆对和 original_row_number 成员精确匹配，附近 ±3 s 事件单独计数；选择 P2-only、P3-only 和三规则确认时刻差异案例共 11 个，生成新 PDF 和逐案例 CSV。P2 仍仅为条件性 Proposal，缺少独立安全真值、公平采样和独立几何真实性，未冻结科学规则。报告：`docs/STAGE_0_2_TASK_2_5_2_KEY_DIFFERENCE_CASES_2026-10-11.md`。


## 2026-10-11 科研决策归档与参数核定

研究者已确认 Stage 0.2 风险设计：P2=可靠 TTC<2.0 s、首末跨度≥0.2 s，P1/P3 为敏感性对照；TTC 触发、DRAC 作严重程度；连续风险使用 rho=exp(-TTC/tau)，固定车辆/区域/窗口、车辆等权、缺失上下界和四格 DID。四源时间加权 TTC 中位数为 11.378882、17.170886、16.312500、14.416058 s，tau=15.364279 s。该设计已记录但 rho burden、固定窗口和 P2 0.2 s 正式实现仍待完成；Scientific Gate、Protocol Lock 和 Stage I 未启动。报告：`docs/STAGE_0_2_DECISION_RATIFICATION_2026-10-11.md`。


## 2026-10-11 连续风险时间尺度验证

在四源任务 1.5 状态上，以可靠相邻 100 ms 闭合边计算 `rho=exp(-TTC/tau)`。tau=15.364279 s 下时间加权平均 rho 为 Lankershim 0.4390、US-101 三窗口 0.3375/0.3529/0.3833；`>=10 s` TTC 暴露占比很高但 rho 较低，风险贡献由暴露时间和条件强度共同决定。tau/2、2tau 敏感性与极端压力结果已封存；正式固定目标区域 burden 仍 Unresolved。报告：`code/outputs/formal/calibration/stage_0_2_rho_timescale_validation_20261011_r1/report.md`。

## 2026-10-11 正式风险测量接口实现

新增 `code/src/riskprop/formal_risk_measurement.py` 与版本化配置 `code/configs/stage_0_2_formal_risk_measurement_p2_v1.json`。P2 使用可靠 TTC<2.0 s、首末跨度≥0.2 s，确认时间取实际观测帧；`rho=exp(-TTC/tau)` 使用 tau=15.364279197080283，仅对可靠有效正闭合 TTC 计算。新增贡献上下界、固定窗口积分、车辆等权平均和 DID 区间算术接口；目标区域、固定车辆资格、评价窗口和消息去重仍为空配置，尚未宣称正式区域 burden 已实现。独立复算得到 P2=4545，与任务 2.5.1 参考一致；产物：`code/outputs/formal/calibration/stage_0_2_formal_risk_measurement_20261011_r1/`。旧提取器 0.1 s 默认和旧线性 TTC 指标保留不变。测试与 Stage 0.2 Gate、Protocol Lock、Stage I 状态分离。

## 2026-10-11 正式风险测量一致性修复

修正区域外贡献判定顺序、车辆对统计和 NGSIM 诊断时钟连续性字段；P2 仍为 4,545 个事件，唯一后车 2,512，唯一车辆对 3,072。新验证产物：`code/outputs/formal/calibration/stage_0_2_formal_risk_measurement_20261011_r2/`；报告：`docs/STAGE_0_2_FORMAL_RISK_MEASUREMENT_CONSISTENCY_REPAIR_2026-10-11.md`。


## 2026-10-12 Stage 0.2 综合收口（当前状态）

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。
