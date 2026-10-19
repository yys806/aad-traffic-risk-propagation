# AAD 结果索引

> 核对日期：2026-09-10。以下结果均不能支持核心科学效应声明。

## RES-STAGE-0.1-INFRASTRUCTURE-V3

阶段 0.1工程运行：处理前等价、隔离、时钟和生命周期通过；物理连通路径未接通。便携证据位于同名 `evidence/results/` 目录。

## RES-STAGE-0.1-ENV-COMPARE-V3

阶段 0.1双环境结构一致性结果；只证明结构匹配。

## RES-STAGE-0.2-NGSIM-V2

阶段 0.2迁移前审计包：NGSIM可形成有效跟驰测量与风险事件；holdout未解锁，异常审计和最终分布仍需收口。

## RES-STAGE-0.4-COMM-OBS-V3

阶段 0.4通信可观测性结果：RV_RX只能作为接收状态连续性；packet schema、时延、丢包和采用不可声称已观测。

## RES-STAGE-0.5-REAL-REF-V1

阶段 0.5迁移前部分真实参考。pNEUMA风险指标未纳入、SUMO样本未纳入；按当前“pNEUMA只做运动学”的边界需要重新生成。

## RES-STAGE-0.5-REAL-REF-R2

正式真实参考重建（AAD-0.5.1）。六项正式输入通过路径、SHA-256、来源身份、schema 和质量契约校验：NGSIM US-101 三窗口、Lankershim、Stage 0.2 最终 P2 表和 Stage 0.3 canonical pNEUMA。完整状态共 5,706,252 行；P2=4,545（543/732/1,043/2,227）；pNEUMA=785 条轨迹、1,239,475 条状态。US-101 仍为高速公路跟驰风险主线，Lankershim 独立为城市辅助，pNEUMA 仅为城市运动学。完整正式事件率和 pNEUMA 时间/车辆等权统计绑定既有封存结果；稳定哈希/轨迹簇样本仅为诊断。无 SUMO 样本、无覆盖阈值、无 Gate 升级。报告：`docs/STAGE_0_5_TASK_0_5_1_REAL_REFERENCE_REBUILD.md`；包：`code/outputs/formal/calibration/stage_0_5_real_reference_r2/`。

## RES-STAGE-0.5-CALIBRATION-READINESS-V1

Stage 0.5.4-A 校准准入与测量等价性审计（工程审计结果，不是 Scientific Gate 结果）。P2 测量契约按 16 项维度逐条审计：10 项 `Equivalent / Verified`、6 项 `Engineering Consistent Only`、0 项阻断；16 个确定性边界用例（含前车切换、incarnation 变化、晚进入、缺帧、暖机截断、窗口边界、右删失、0.1/0.2 s 节奏、恰好/不足 0.2 s、风险再进入、有效与可靠非闭合交替）两适配器一致。用独立实现重算已批准两窗口统计并逐项复现封存值：可评价暴露 111,425.9 / 133,505.6 s，事件 543 / 732，事件率 17.5435 / 19.7385 veh⁻¹h⁻¹。修复 6 项适配层缺陷（绝对时钟、前车自身帧号、退出原因字段、闭合 epsilon、可靠层定义、DRAC 闭式），未修改 Stage 0.2 任何规则。校准窗口特征与需求可识别性矩阵、候选分层、轨迹簇不确定性（事件率 95% CI 约 ±15%，逐行 i.i.d. 窄 12.7 倍）、时间步敏感性（内部步长减半使事件边界移动 0.2 s）与 300 s 基准成本均已记录。准入清单 `ready_to_start_stage_0_5_4b=false`，5 项待批准、5 项阻断；未读取验证窗口（materialised 0 行）、未冻结任何容差或参数。报告：`docs/STAGE_0_5_TASK_0_5_4A_CALIBRATION_READINESS.md`。

## RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1

Stage 0.5.3 工程结果。US-101 `generic_highway_candidate`（3 主线段 × 3 车道 + 入口/出口匝道）在 SUMO 1.26.0、seed=20260907、internal 0.1 s、recorded 0.1 s 下完成两个无消息工程 fixture：①baseline_mixed_demand：8,453 state、17 vehicles（全部进入并驶出）、6,118 leader rows、724 valid TTC rows、min TTC 6.971 s、工程 P2=0、P2 可评价跟驰暴露 609.4 s；②measurement_probe_queue_stop：2,720 state、7 vehicles、1 个工程 P2 事件（onset 3.1 s、确认 3.3 s、持续 2.4 s、TTC min 1.794 s），Stage 0.2 formal-alignment adapter 边界完全一致。TraCI `getLeader` 距离语义已核验为「物理保险杠净间距 − 后车 minGap」，同车道残差 0.0 m；校准入口对 `us101__0820_0835` 与辅助来源 fail-closed 拒绝。P2 等价性为 `pending_measurement_equivalence_review`；Lankershim/pNEUMA 仅保留候选入口，pNEUMA 六类原始车型 `unmapped`。本结果 `engineering_only`、`scientific_claim_eligible=false`，不构成现实校准或 Stage 0.5 Gate 通过。报告：`docs/STAGE_0_5_TASK_0_5_3_SUMO_BASELINE_ENGINEERING.md`；本地包：`code/outputs/formal/calibration/stage_0_5_sumo_baseline_engineering_v1_baseline/` 与 `..._probe/`。

## RES-STAGE-0.6-PRELOCK-V2

阶段 0.6数值审计：解析和工程真值检查通过，科学容差仍未冻结。

## RES-PROTOCOL-READINESS-V1

迁移前协议就绪哨兵，结论为未就绪。新阶段键启用后必须重新生成；它不是科学结果。

每个当前结果必须登记便携证据、本机完整产物、配置、数据身份、结论边界和 Gate。旧 pNEUMA 前车复核结果已转入 `evidence/history/legacy_experiment_ids/`。

## RES-STAGE-0.2-TASK-1.4

Verified 工程核查，待研究者验收任务 1。US-101 4,098,933 行测量回归一致；Lankershim 1,607,319 行保留，2,442 个诊断时钟序列，483,098 个有效 TTC 帧，原始/可靠候选事件各 2,777 个、拒绝 0。官方来源时段与物理身份仍 Unverified，Stage 0.2 科学 Gate 仍 Active。报告：`docs/STAGE_0_2_TASK_1_4_RELIABILITY_CLOSURE_2026-10-10.md`；完整包 `code/outputs/formal/calibration/stage_0_2_task_1_4_20261010/`，小型证据在同名结果目录。

## RES-STAGE-0.2-TASK-1.5

跨时钟前车匹配工程核验 Verified。Lankershim 1,226,499 条报告前车均在时钟锚与 Frame_ID 约束下唯一，真实跨时钟匹配 0；四源核心测量和事件结果与任务 1.4 一致。建议关闭任务 1，Stage 0.2 科学 Gate 仍 Active。报告：`docs/STAGE_0_2_TASK_1_5_LEADER_MATCHING_CLOSURE_2026-10-10.md`。

## RES-STAGE-0.2-TASK-2

NGSIM 风险测量质量、真实分布与候选事件规则描述性审计。5,706,252 条 state、2,211,378 条有效 TTC；TTC/DRAC 重尾，极端记录已追溯，6×4 阈值/持续时间网格显示事件数对规则敏感。未冻结科学规则或 Stage 0.2 Gate。报告：`docs/STAGE_0_2_TASK_2_RISK_QUALITY_AUDIT_2026-10-10.md`；完整包保留在 `code/outputs/formal/calibration/stage_0_2_task_2_risk_quality_audit_20261010_r4/`。

## RES-STAGE-0.2-TASK-2.1

极端风险和候选事件案例复核：固定种子抽取 447 个案例，独立前车匹配和 TTC/DRAC 重算全部一致；399 个 C 类极端/阈值敏感案例、48 个 D 类普通对照，未发现确定性 A 类计算冲突。物理真实性与 B 类几何判断仍需人工/独立复核。报告：`docs/STAGE_0_2_TASK_2_1_EXTREME_REVIEW_2026-10-10.md`。

## RES-STAGE-0.2-TASK-2.2

447 个任务 2.1 案例的同车辆对持续性、探索性运动学差分和几何证据边界诊断；自动 C=349、D=98，代表性人工复核包 48 个。人工判断未完成。

## RES-STAGE-0.2-TASK-2.2.1
连续段边界修复：447 案例多帧 297、单帧 3、间歇 1、边界 25、无极端 121；C=349、D=98；48 个案例按显式配额选择。

## RES-STAGE-0.2-TASK-2.2.1-FINAL-FIX
连续风险边界与段统计修复，447 案例重新验证，48 案例人工复核包重绘。产物：`code/outputs/formal/calibration/stage_0_2_task_2_2_1_20261011_r9/`；报告：`docs/STAGE_0_2_TASK_2_2_1_FINAL_FIX_2026-10-11.md`。

## RES-STAGE-0.2-TASK-2.3
NGSIM 风险测量质量与稳健性综合收口；完成风险段 oracle、447 案例精确中心定位、四源全量质量分母与 S0/S1/S2 探索性事件重提取。报告：`docs/STAGE_0_2_TASK_2_3_QUALITY_ROBUSTNESS_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_3_20261011_r3/`。

## RES-STAGE-0.2-TASK-2.4

正式事件提取等价性与风险稳健性最终验证。四源独立重提取与正式 5,381 事件逐成员一致；S1 真实质量条件重跑不改变事件数；S2a/b/c/d 事件数为 5,366/5,353/5,263/5,235；连续暴露分段完成。报告：`docs/STAGE_0_2_TASK_2_4_EVENT_EQUIVALENCE_2026-10-11.md`；完整包：`code/outputs/formal/calibration/stage_0_2_task_2_4_20261011_r2/`。科学 Gate、Protocol Lock 和正式风险规则仍未通过/冻结。

## RES-STAGE-0.2-TASK-2.5

源端风险事件阈值、最小持续时间与物理合理性联合验证。复用任务 2 的 6×4 正式网格，新增事件级特征、参数对应、因果确认时刻、采样敏感性、文献矩阵和 24 个案例。报告：`docs/STAGE_0_2_TASK_2_5_THRESHOLD_VALIDATION_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_5_20261011_r1/`。参数仍为 Proposal，科学 Gate 未通过。


## RES-STAGE-0.2-TASK-2.5.1

P1/P2/P3 源端风险事件规则针对性验证：成员级跨参数对应、24 个真实案例新图册、实际观测确认时刻、极端值压力诊断、采样公平性状态和文献元数据更正。P1=1,900、P2=4,545、P3=8,523、工程参考=5,381；参数仍为 Proposal，科学 Gate 未通过。报告：`docs/STAGE_0_2_TASK_2_5_1_TARGETED_VALIDATION_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_5_1_20261011_r2/`。


## RES-STAGE-0.2-TASK-2.5.2

关键差异案例分析：中心事件精确成员归属与附近事件分离，P2-only、P3-only 和三规则确认时刻差异案例，P2 仍为 Proposal。报告：`docs/STAGE_0_2_TASK_2_5_2_KEY_DIFFERENCE_CASES_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_5_2_20261011_r1/`。


## RES-STAGE-0.2-DECISION-RATIFICATION

研究者已确认的 Stage 0.2 风险设计归档及四来源 tau/P2 实证核定：tau=15.364279 s，来源中位数与实现冲突见报告；Scientific Gate 和正式实现仍未完成。报告：`docs/STAGE_0_2_DECISION_RATIFICATION_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_decision_ratification_20261011_r1/`。


## RES-STAGE-0.2-RHO-TIMESCALE

rho 时间尺度合理性诊断：tau=15.364279 s，完成四源分布、TTC 分箱暴露/贡献、tau/2/2tau 和极端压力分析；正式区域 burden 仍 Unresolved。

## RES-STAGE-0.2-FORMAL-RISK-MEASUREMENT

隔离式正式风险测量接口与 P2 独立复核：4,545 个事件与 Task 2.5.1 参考一致；包含 rho、状态贡献上下界、固定窗口原语和 100/200 ms 语义构造审计。目标区域和评价窗口仍未决。报告：`docs/STAGE_0_2_FORMAL_RISK_MEASUREMENT_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_formal_risk_measurement_20261011_r1/`。

## RES-STAGE-0.2-FORMAL-RISK-MEASUREMENT-CONSISTENCY-REPAIR

正式风险测量三个确定性实现问题修复：区域外贡献顺序、完整车辆对统计、NGSIM 诊断时钟连续性。P2=4,545，唯一后车=2,512，唯一车辆对=3,072。报告：`docs/STAGE_0_2_FORMAL_RISK_MEASUREMENT_CONSISTENCY_REPAIR_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_formal_risk_measurement_20261011_r2/`。


## RES-STAGE-0.2-FINAL-CLOSURE

## RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R3

最终有限科学验收审计包，当前 `Blocked`。四源 P2=4,545，事件率按可靠跟驰暴露秒数计算并独立复现；边级分母审计发现 `invalid/non_positive_gap` 端点边进入封存分母，影响量和状态转换已完整封存。研究者需裁决其是否属于正式事件率分母，裁决前不关闭 Stage 0.2。证据：`code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r3/`。

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。

## RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4

Stage 0.2正式Gate=`pass`、`Completed / Closed`，仅限四源NGSIM、100ms描述性纵向跟驰风险代理测量。正式P2分母按可靠相邻边双端P2可评价定义独立复算；5,039,222条边、503,922.2s，原可靠跟驰512,043.2s仍独立列示，不可评价8,121.0s无零风险含义。P2=4,545；逐源事件率、原始分子分母和新旧分母率对照见最终包。独立物理真实性、缺失选择偏差、极端敏感性、200ms迁移不等价和来源外推为未验证限制。历史R3 Blocked记录不覆盖。证据：`code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r4/`。

## RES-STAGE-0.4-LIMITED-SCIENTIFIC-ACCEPTANCE-V1

Stage 0.4 有限科学验收与正式收口（AAD-0.4.8，研究者批准）。**Gate=`pass_limited`；Stage Status=`Completed / Closed (Limited Scope)`**。验收仅限：可观测性边界+已验证描述性通信证据+参数不确定性处理原则；不验收真实性能模型/数值校准/距离函数/采用/核心因果效应。已验证：RV_RX 接收状态连续性、RSE_BSM 车辆侧接收内容（无接收时间）、SEE-V2X 配对（48 对 1.0）与描述性接收比例（室内 0.998–1.0/室外 0.22–1.0）、时延数值复算；未验证（不升级）：真实链路 PDR、接收机会、绝对时延、距离—PDR、采用、自然交通 V2V。通信参数未冻结未校准；不足部分为标记不确定的实验/敏感性参数。RV_RX V3 与 Packet HTTP-403 保留为历史事实未改写。Stage 0.5/0.6 阻断保持，Protocol Lock 与 Stage I 未解锁（readiness 测试锁定）。报告：`docs/STAGE_0_4_LIMITED_SCIENTIFIC_ACCEPTANCE_2026-10-17.md`；包：`code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/`。

## RES-STAGE-0.4-SEE-V2X-BSM-REAUDIT-V1

Stage 0.4 任务 0.4.7.1：SEE-V2X BSM 通信证据科学复核（修正 0.4.7）。**配对率（1.0）与接收比例（0.22–1.0）已分开**（48 对全量）；真实链路 PDR 与接收机会 **Unverified**（GNSS≠无线在线，室内无 GNSS、RSU 静态、无无线模块状态证据）；时钟纪元 ×1000 歧义 → 绝对时延 Unverified；距离仅室外 ~0–10 m（室内无 GNSS）。受控 PC5 候选参数仅限描述性。包：`code/outputs/formal/calibration/stage_0_4_see_v2x_bsm_reaudit_v1/`。

## RES-STAGE-0.4-SEE-V2X-GNSS-REPAIR-V1

Stage 0.4 任务 0.4.7.2：SEE-V2X GNSS 时空匹配修复与证据收束。修复窗口外钳制/时间误差单位/轨迹独立性三缺陷。**决定性发现**：t1/t2/t3 GNSS 轨迹逐点完全相同（同一轨迹复制品，非三个独立设备）→ 室外设备间距离恒 0 m 系轨迹复制（非车辆重合）；RSU 静态、室内无 GNSS → **距离—通信关系不可识别**。消息关联（1.0）与接收比例（0.22–1.0）不受影响。SEE-V2X 阶段收束：受控 PC5 候选参考（配对/接收比例/相对时延），链路 PDR/接收机会/绝对时延/距离—PDR/自然交通 V2V 保持 Unverified。包：`code/outputs/formal/calibration/stage_0_4_see_v2x_gnss_repair_v1/`。

## RES-STAGE-0.4-SEE-V2X-REAUDIT-V1

Stage 0.4 任务 0.4.6.1：SEE-V2X 最小样本科学复核（独立复算，修正 0.4.6 PDR 口径与时延可信度）。**PDR 修正**：0.4.6 的 `independent_pdr` 为接收窗口口径（排除运行边界未接收段）系统性高估——Run 2 完整运行 PDR=**0.9737**（发送 5,742/接收 5,591），非 0.4.6 所报 1.0；字段 `per_ue_loss_pct`≈接收窗口口径。**正确口径=完整运行 PDR**（分母=运行内全部发送，物理意义可靠）。**时延**：数值复算 Verified，但跨运行固定时钟偏移 P50 8.8–32 ms（run8 32.0 vs run2 8.8）→ **合并分位数不可靠**，逐运行形态相对可信但含漂移。时钟同步凭现有数据不可解（Unverified）。正式校准仍不冻结；下一批 4.89 GiB 建议（GNSS 时钟参照+轨迹绑定）。0.4.6 封存包未改动。报告 `docs/STAGE_0_4_TASK_0_4_6_1_SCIENTIFIC_REAUDIT.md`；包 `code/outputs/formal/calibration/stage_0_4_see_v2x_reaudit_v1/`。Gate 保持 `pending_official_packet_access`。

## RES-STAGE-0.4-SEE-V2X-MINIMAL-V1

Stage 0.4 任务 0.4.6：SEE-V2X 最小样本（`outdoor_parkinglot.tar.gz`，4,883,437 B，SHA-256 ABFE57AC…33F89，公开 Drive）实证验证。10 次室外停车场运行（C-V2X 侧链，1 发送方→1 接收方）。**同消息关联 Verified**：10/10 配对率 1.0，`seq_num` 0..N−1 唯一；**latency 数值可计算 Verified**：(rx−tx)/1000 与 `latency (ms)` 在 30,571 行逐行一致（abs diff max 0），0 负时延，分布 min 4.955/P50 16.787/P95 34.861/max 60.120 ms——**物理意义（真实时延）Unverified**（跨设备时钟偏移未证，分布形态可信、绝对值可能含固定偏移，未冻结为校准参数）；**PDR/PER Verified**：sender-base 独立复算与 `per_ue_loss_pct` 逐 run 一致（分母=发送数、接收机会=运行内）。信道占用 Documented（低负载 P50 5%/max 23%）。`extra=1` 插值行排除。正式校准暂不冻结；建议条件性批准 `emulating_applications`（4.89 GiB，BSM 场景+GNSS）。报告 `docs/STAGE_0_4_TASK_0_4_6_SEE_V2X_MINIMAL_VALIDATION.md`；包 `code/outputs/formal/calibration/stage_0_4_see_v2x_minimal_v1/`。Gate 保持 `pending_official_packet_access`。

## RES-STAGE-0.4-RSE-BSM-V1

Stage 0.4 任务 0.4.2：SPMD `RSE_BSM.csv.zip` 条件获取与独立证据核验（仅本地原始数据）。成员级 Range 下载（49 分块全部 206/Content-Range/ETag 校验），CRC32 对官方 ZIP64 中央目录一致，内层 ZIP 校验通过，SHA-256 `9C40C15F…D722` 钉扎；磁盘 182.98→179.98 GiB。实测：25 字段（官方 24+RxDevice，手册 28 字段说法有误）、124,115,615 行零畸形、表头独立于数据文件；BSMID 逐行唯一（行 ID 而非跨接收方消息身份）、TemporaryId 155,220、MsgCount 0–127 循环、DSeconds 发送端分钟内毫秒；**无绝对时间字段**；RxDevice 2,008 值全部在 BsmP1Summary 设备命名空间、与 PCAPFile RSE LocID 零重叠（记录方物理身份 Ambiguous）；(TempID,MsgCount,DSeconds) 部分精确覆盖下重复 ≥26,919,767。证据边界：接收时间/时延/丢包 Not Observable，配对 Ambiguous；行为统计按 holdout 规则暂缓。Packet 建议为下一批（修正预期），BsmP1 价值上调，新增 BsmMd/RSE_locations.kml 候选。Gate 保持 `pending_official_packet_access`。报告：`docs/STAGE_0_4_TASK_0_4_2_RSE_BSM_AUDIT.md`；包：`code/outputs/formal/calibration/stage_0_4_rse_bsm_v1/`。

## RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3

Stage 0.3 最终科学验收与正式关闭（AAD-0.3.3，2026-10-16）。研究者批准五项决定：①正式范围限 `20181101_d1_0800_0830.csv` 实际观测车辆的描述性城市运动学参考（不宣称 30 分钟连续覆盖、不代表城市总体、不推断时间原点）；②连续性规则 `0<Δt≤0.043 s` 为已批准科学参数（仅本 25 Hz 文件，原始记录顺序、fail-closed）；③极端观测原始保留+标记+敏感性，物理真实性 Unverified；④低速/近静止/近零阈值仅统计描述；⑤`Scientific Gate=pass`、`Completed / Closed`（有限范围）。关闭包对 R2 证据 fail-closed 复核全部通过：checksum 重验、785/1,239,475/[38.40,888.00] s/暴露 49,547.6 s、速度 TW 4.838218/VW 6.207738/加速度 -0.004410 m/s² 不变、独立复算 discrepancies=0；未重跑全量管线。验收矩阵 11 项全部 Verified。报告：`docs/STAGE_0_3_SCIENTIFIC_ACCEPTANCE_2026-10-16.md`；包：`code/outputs/formal/calibration/stage_0_3_scientific_acceptance_20261016_r3/`。

## RES-STAGE-0.3-BOUNDARY-REPAIR-R2

Stage 0.3 R2 边界修复与验收准备（AAD-S0.3-T02）。修复三项工程边界缺陷：时间连续性在排序前按原始记录顺序评估（时间倒退/重复/非正增量/缺口入标记，时间加权区间由原始顺序邻接定义，异常不可经排序重获权重）；轨迹审计以原始行为单位、重复 track_id fail-closed 不合并不改名；`quality_status` 逐状态推导、`time_weighting_eligible` 由解析质量+身份+原始顺序+可靠区间共同决定，`write_real_reference_package()` 读取并使用质量字段。真实数据统计不变：785 行/785 唯一 ID/1,239,475 状态，速度 TW mean=4.8382、VW mean=6.2077，加速度 TW mean=-0.0044 m/s²；R1/R2 145 项比较仅 30 项浮点末位（≤1e-9，已归因为求和对齐效应）与 1 项结构性记录差异；独立复算 discrepancies=0；全量测试 315 passed。状态 **Gate Pass Candidate（R2）**，待研究者裁决。报告：`docs/STAGE_0_3_BOUNDARY_REPAIR_R2_2026-10-16.md`；包：`code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2/`。

## RES-STAGE-0.3-PNEUMA-KINEMATICS-R1

Stage 0.3 综合实施与验收准备。785 条唯一轨迹（Car 443、Motorcycle 153、Taxi 137、Medium Vehicle 30、Bus 20、Heavy Vehicle 2）、1,239,475 条状态、0.04 s 等间隔、零缺口/畸形/重复。时间加权速度 mean=4.8382 m/s（P50=4.5824、P95=12.1176）、车辆等权 mean=6.2077 m/s；纵向加速度 mean=-0.0044、sd=0.7454 m/s²，极端记录保留并做敏感性。轨迹簇 bootstrap 2000 次；独立复算零差异；Stage 0.5 现有接口真实全量测试通过（pNEUMA TTC 未纳入）。状态 **Gate Pass Candidate**，科学 Gate 与未冻结参数待研究者。报告：`docs/STAGE_0_3_PNEUMA_KINEMATICS_2026-10-12.md`；包：`code/outputs/formal/calibration/stage_0_3_pneuma_kinematics_20261012_r1/`。

## RES-STAGE-0.5-CALIBRATION-GAPS-V1

AAD-0.5.4-A+定向补充，verified_engineering_only。两个原始校准成员100%连接、车型/长度注记可用；主线每车道、统一阈值42.8767/48.0828、12/11内部片、源实际时钟和四个固定负载成本已量化。保留未插入/初始化/积分器限制，所有科研候选Proposal，Calibration Ready=false。报告docs/STAGE_0_5_TASK_0_5_4A_SUPPLEMENT_CALIBRATION_GAPS.md；完整包code/outputs/formal/calibration/stage_0_5_calibration_gaps_v1_final/；便携证据同ID。


## RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1

2026-10-18 AAD-0.5.4-B0（RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1）：受限探索完成19/23次，4次高输入seed20261019响应未运行。统一27.78m/s上限、空初态、ballistic显式、internal.05/recorded.1、action.1、sigmaStep1；三个基准输入1087.364/1449.818/1648veh/h/lane仅实现局部密度10.37–15.75、均速约27.1，局部低速/P2均0。tau2三次末期未服务21/22/71，入口main0约2.5–20.1m有低速插入/加速，局部段无拥堵。B0-EXEC-STOP-01：原调度器未因completed+blocker停止，发现后人工停止，源码停止后修复并测试；最后worker峰值内存Unverified。推荐先批准需求边界/最小结构对照，不继续参数搜索掩盖状态支持缺口。所有结果exploratory_diagnostic_only、scientific_claim_eligible=false；Gate=pending_simulation_sample、Calibration Ready=false、Reality Coverage Accepted=false、正式容差Tolerance Not Yet Justified、Energy Distance上界Not Identifiable；B0实验验证输入0；根全量回归无过滤打开历史Stage0.2全源事件/案例产物，任务级验证访问不能认证（B0-VALIDATION-SCOPE-02）；数据隔离验收不Accepted。无holdout/正式校准/锁/Stage I。依据：docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md、同ID证据和execution_ledger。

## RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1

B1（RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1）按阻断提前结束：V1失败A后7次未启动，V2 A有效/B警告/C阻断/D未启动，累计4次尝试；无补跑或新seed。A/B局部均速27.1088/26.5152m/s、密度16.3208/16.8197、低速0；C记录2.4007m/s、93.8653veh/km/lane、低速80.1719%、末期未服务252，但停车位移检查与冻结回溢资格阻断，不能作为有效校准样本。D只有静态/空加载检查，动态未知。

Gate=pending_simulation_sample、scientific_claim_eligible=false、ready_to_start_stage_0_5_4b=false、reality_coverage_accepted=false；容差Tolerance Not Yet Justified，ED上界Not Identifiable，ProtocolLock/StageI禁止。仅推荐下一项B1.1停车数值/队列回溢观测契约整改，未启动。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md`、`evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1/`中的preflight、execution_stop_observation、numerical_stop_diagnostic、queue_diagnostics、run_manifest和SHA256SUMS。

## RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1

`RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1`：已核对固定SUMO1.26.0源码；内部负vNext不同于TraCI非负终速和当步平均加速度。4个独立微型fixture、1366条全量相邻边，其中1363精确核对最大残差1.4210854715202004e-14m，2条停车仅必要范围一致，1条edge转换不可评价。保留1e-6m，精确停车仍`Pending Numerical Equivalence`。14个先冻结真值的合成队列案例比较旧网格/新网格/车辆连接；观测与资格、内外排队分开，阈值均Candidate，未批准现实适用性。

B1 C两阻断和D not_attempted永久保留；B0隔离false/验证物化Unknown不变。无旧C状态读取、无新交通矩阵/参数搜索/校准。胶囊路径白名单与SHA、受审计91项测试通过；完整OS/native文件监控未证明。Gate=pending_simulation_sample，scientific_claim_eligible=false、ready_to_start_stage_0_5_4b=false、reality_coverage_accepted=false；容差Tolerance Not Yet Justified、ED上界Not Identifiable、锁/StageI禁止。下一项只建议独立停车分支可观测性最小验证；B1.2需另批，不自动执行。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_1_STOPPING_AND_SPILLBACK_CONTRACT.md`及同ID便携证据；协议/源码/输入冻结SHA见experiment_plan、PLAN_SHA256和provenance。

## RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1

`RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1`：固定SUMO1.26.0源码审计确认，非决策步延续公开加速度（`vSafe=v0+a_pub_start*h`），内部带符号候选终速可由公开TraCI独立重建 `u=v0+a_pub_start*h`，对任意符号精确成立，包括`u<0`的真实步内停车；决策步`v1=0`仍被钳制，仅可范围一致检查。决策步判定：步[`t_prev`→`t_now`]为决策步当且仅当`t_now`读到的`lastActionTime`等于`t_prev`。3个微型运行共948条相邻边：947精确核验且全过，最大残差`1.4210854715202004e-14m`，1条决策步停车仅范围，0不可评价，0异常；未用位移反推、未用调试二进制。方案A/B准入比较及B1.2前置条件已登记，待研究者决定。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_1S_STOPPING_OBSERVABILITY.md`及同ID便携证据；协议/源码/输入冻结SHA见experiment_plan、PLAN_SHA256和provenance。


## RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2

B1.2前置接入工程阻断，主矩阵未冻结/未运行；报告`docs/STAGE_0_5_TASK_0_5_4B1_2_BOUNDARY_BOTTLENECK_REVALIDATION.md`，便携证据`evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2/`。近零终速反例、10047精确/14 bounded/84不可评价；历史及科学Gate保持。


## RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1

`RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1`：独立B1.2-N工程任务。固定SUMO1.26源码完整谓词和调用顺序已审计；无停车任务的fresh/immutable生命周期可用doubleMax不变量，同edge常规停车仅非决策步可作充分条件。一般myStopDist不能由公开getter等价恢复。新候选`b12n-near-zero-observability-v1`不以位移/终速选择上下文，1e-6m不变。3个30s微型运行：2879边，2876精确全过（其中1负近零后处理），3 bounded，0近零未决/不可评价/工程错误；最大残差1.3988810110276972e-14m。冻结前203项受控合成通过。

正近零非决策步清零运行边未出现（Not Observed），未满足运行前冻结的共同准入条件；integration_allowed=false，C/D计划冻结被拒绝，均Not Attempted，未追加试验/搜索。新主矩阵禁止且0次。旧B1.2阻断/0-8/D未运行和所有历史证据不变。下一步由研究者决定正近零覆盖设计与未来政策，再另批接入/主矩阵；不自动继续。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2N_NEAR_ZERO_AND_INTEGRATION.md`；证据同ID目录。科研Gate/ready/现实覆盖/锁/StageI状态不变，科学阈值未批准。


## RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1

`RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1`：B1.2-P仅数值观测独立任务。固定SUMO1.26/commit fa7df22d，13具名源码完整谓词/赋值路径核对；fresh/no-stop/无恢复/无控制/无特殊设备/非循环路线doubleMax不变量独立成立。5个冻结原生红灯制动探针各2s、无车辆setter/无重试。实际P1/P2在.10→.15s非决策步重建u_pre约1.999999909e-6/4.800000001e-6，公开终速0，最终分支由源码与生命周期先行确定，位移残差-4.6161e-15/-6.4115e-15m。2条目标Exact Pass；195边中192一般精确全过、3 bounded、0未决/不可评价/阻断。P3/P4/P5实际阈值以上保持正终速；P3名义等号但实际略高，运行精确等号Not Observed。1e-6m未放宽，残差不用于反推上下文。

仅target_branch_verified=true，C_D_allowed=false/main_matrix_allowed=false/future_numerical_policy_approved=false。不需要为该受限分支使用调试构建；一般停车/状态恢复/特殊控制域未验证。B1.2-N正近零Not Observed与integration_allowed=false、旧B1.2阻断/0-8及所有历史原样保留。本轮C/D和主矩阵0次；下一步研究者需决定未来数值准入政策，另批剩余接入；不自动执行。科学Gate及所有ready/现实覆盖/锁/StageI资格不变。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2P_POSITIVE_NEAR_ZERO.md`；证据同ID目录。


## RES-STAGE-0.5-CD-INTEGRATION-V1

`RES-STAGE-0.5-CD-INTEGRATION-V1`：C/D有限接入2次各60s；62707边中62513精确全过、63 bounded、131合法坐标不可评价、0数值阻断。C内部队列/上游扩展/入口邻近与87 pending可观测，但入口与下游锚定组件约14.35m>10m，持续回溢EI。D9辆实际换道和main2出口由原始状态独立验证；v1 main_1-only假阻断保留，v2修复无重试。定向0/8、主矩阵0次；正式Gate和全部历史不变。

报告 `docs/STAGE_0_5_TASK_CD_INTEGRATION_AND_ISSUE_DISCOVERY.md`；证据 `evidence/results/RES-STAGE-0.5-CD-INTEGRATION-V1/`。研究者本轮授权工程分层与新增2次接入（已用完）、定向最多8次（未用）；无ABCD授权。近零仅fresh/no-stop域，1e-6m不变。当前最重要决策是下一局部跟驰探索是否需要完整入口回溢，以及评价时间/需求/科学容差/P2局部归属协议；不为非核心私有量无限追加验证。旧B1/N/P授权与状态作为历史保留。通用路网/局部匹配为当前研究者优先，真实几何完整复现非必要前提，但结构/匝道/波传播结论受限。
