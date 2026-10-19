# AAD 当前科研状态

> 核对日期：2026-10-19。数字和 Gate 以 `PROJECT_REGISTRY.json`、`evidence/` 和本机原始产物为准。

## 当前研究问题

来源可追溯且确实被控制器采用的远端风险消息，能否在普通物理影响到达目标区域以前，通过改变目标车辆动作而改变区域总体风险。

## 已验证

- 阶段 0.1工程基础设施可运行、封存和复算，但不是科学结果。
- 阶段 0.2的迁移前审计证明 NGSIM能够构造跟驰风险测量与连续事件。
- 阶段 0.3 pNEUMA 城市运动学描述性统计、质量审计与 Stage 0.5 参考接口已完成；R2（2026-10-16）修复边界缺陷后统计不变；R3（2026-10-16）经研究者五项批准正式关闭（`pass`，有限范围：单文件描述性城市运动学校准）。
- 阶段 0.4确认 RV_RX只能支持接收状态连续性。
- 阶段 0.6解析与工程数值检查通过。

## 正在进行

- 当前节点：阶段0.5 B1.1-S公开接口停车可观测性交付，非决策步步内停车已精确核验、决策步停车仍Bounded；B1.1精确停车Pending记录不变，队列规则Candidate；旧B1 C阻断、D未运行。
- 主线待决：独立停车可观测性证据与未来B1.2授权；正式0.5.4-B、现实覆盖验收和科学容差未获批准。
- 阶段0.2/0.3已有限范围关闭、0.4已有限验收；阶段0.6科学参数和协议锁仍未完成。

## 当前机器 Gate

| 阶段 | 状态 |
|---|---|
| 阶段 0.1 | `engineering_pass_scientific_fail` |
| 阶段 0.2 | `pass`（有限范围） |
| 阶段 0.3 | `pass`（有限范围） |
| 阶段 0.4 | `pass_limited`（有限范围，Completed / Closed Limited Scope，2026-10-17） |
| 阶段 0.5 | `pending_simulation_sample` |
| 阶段 0.6 | `blocked_by_calibration_and_tolerance_freeze` |
| 协议锁 | 未通过；需按新阶段键重新生成 |
| 阶段 1.1 | 禁止启动 |

## 尚未确认

- NGSIM异常与极端风险值的最终可信范围（Stage 0.2 已在有限范围内关闭，物理真实性仍 Unverified）。
- pNEUMA 车型→SUMO vType 映射与 Stage 0.5 覆盖设计（Stage 0.3 适用范围与连续性容差已于 2026-10-16 批准冻结，仅限单文件）。
- SPMD packet级通信证据。
- SUMO对现实分布的覆盖程度。
- 科学容差、样本量以及核心效应的存在、方向和大小。

## 当前不能声称

- 不能说已经发现远距离、类超距或因果信息效应。
- 不能把工程 Gate、真实数据校准或历史 pilot写成主效应。
- 不能把消息交付等同于采用，也不能把采用等同于动作或风险变化。

## 2026-10-18｜Stage 0.5.1 当前状态

`RES-STAGE-0.5-REAL-REF-R2` 已完成正式真实参考重建。US-101 三窗口、Lankershim 和 pNEUMA 已按批准职责分离；canonical pNEUMA 接口、输入 SHA/schema/质量契约和正式 P2=4,545 已核验。完整时间/车辆等权统计继续引用 Stage 0.3 封存摘要，哈希状态/轨迹簇样本仅作诊断。Stage 0.5 仍缺 SUMO 校准样本，`pending_simulation_sample` 不变；覆盖阈值、车型映射、SUMO 时间步和验证隔离未冻结，Protocol Lock 与 Stage I 未解锁。

0.5.2 协议设计候选已完成：US-101 采用基础运动学、跟驰交互、风险可观测性、正式 P2 和场景支持五层必要条件；Lankershim 独立辅助；pNEUMA 仅城市运动学；Energy Distance 仅作场景内辅助诊断。校准/验证划分、数值容差、辅助场景范围和 0.5.3 工程契约等待研究者批准，未运行 SUMO。

0.5.3 工程骨架已建立：US-101 `generic_highway_candidate` no-message baseline 与 measurement probe 在 SUMO 1.26.0 上运行成功，输出统一状态/跟驰/净间距/闭合速度/TTC/暴露字段，并由 SUMO-native 与 Stage 0.2 formal-alignment 两个 adapter 一致确认 1 个工程 P2 事件；校准入口对时间验证窗口 fail-closed 拒绝。Lankershim/pNEUMA 仍为 candidate_entry_only，pNEUMA 六类原始车型 `unmapped`。结果仅 `engineering_only`，SUMO P2 正式等价性 pending，未进入现实覆盖校准，Gate 继续 `pending_simulation_sample`。

0.5.4-A 校准准入审计已完成（工程审计，不是 Gate 结果）：P2 测量契约 16 项维度中 10 项 Equivalent/Verified、6 项 Engineering Consistent Only、0 项阻断，16/16 边界用例一致，并精确复现已批准两窗口的可评价暴露与事件率。已修复 6 项适配层缺陷但未改动任何 Stage 0.2 规则。校准窗口的交通状态、需求可识别性、候选分层、轨迹簇不确定性与时间步敏感性已记录；准入清单 `ready_to_start_stage_0_5_4b=false`（5 项待批准、5 项阻断）。未读取时间验证窗口、未冻结网络/需求/车型/时间/容差、Gate 继续 `pending_simulation_sample`。

## 已确认的继续顺序

1. 收口阶段 0.2和0.3。
2. 冻结阶段 0.4的真实证据边界。
3. 完成阶段 0.5仿真—现实覆盖。
4. 完成阶段 0.6科学参数冻结和协议锁。
5. 只有协议锁通过后才设计、实现和运行阶段 1.1。

## 2026-10-10 任务 1.4 工程收尾

任务 1 基础数据与测量工程条件已核验，建议关闭，等待研究者审核；不自动开展任务 2。两套原始帧时钟解释 Lankershim 936 个合并编号异常，保留 unknown 来源时段。事件可靠性检查涵盖后车/前车身份、完整状态序列和缺帧边界。详见任务 1.4 报告与 `RES-STAGE-0.2-TASK-1.4`。最终风险阈值、科学事件口径、极端值与分布审计仍待完成；Stage 0.2 Gate 保持 Active。

## 2026-10-10 任务 1.5 收尾

跨诊断时钟前车匹配核查完成；真实数据跨时钟匹配 0，修复匹配键并完成四源回归，建议正式关闭任务 1。详见 `docs/STAGE_0_2_TASK_1_5_LEADER_MATCHING_CLOSURE_2026-10-10.md` 与 `RES-STAGE-0.2-TASK-1.5`。科学质量审计仍待后续任务。

## 2026-10-10 任务 2

NGSIM 风险测量质量、分布和候选事件规则敏感性描述性审计完成。5,706,252 条 state、2,211,378 条有效 TTC；TTC/DRAC 重尾，极端值需原始轨迹复核；TTC 阈值和持续时间网格显著改变候选事件数。最终事件规则、暴露分母和 Stage 0.2 科学 Gate 未冻结。详见 `docs/STAGE_0_2_TASK_2_RISK_QUALITY_AUDIT_2026-10-10.md` 与 `RES-STAGE-0.2-TASK-2`。

## 2026-10-10 任务 2.1

极端风险值与候选事件案例复核完成：447 个固定种子分层案例，独立前车匹配和公式重算一致；399 个 C 类极端/阈值敏感、48 个 D 类普通对照，未发现确定性计算冲突。物理真实性和几何一致性仍需人工复核，科学事件规则未冻结。详见 `docs/STAGE_0_2_TASK_2_1_EXTREME_REVIEW_2026-10-10.md`。


## 2026-10-12 Stage 0.2 综合收口（当前状态）

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。

### 2026-10-12 最终验收审计

当前 Gate 保持 `Blocked`。P2=4,545、跟驰暴露512,043.2s、闭合暴露208,026.3s及四源事件率均可独立复算；但边级审计发现封存跟驰分母含 `invalid/non_positive_gap` 端点边。研究者需确认其是否属于正式 P2 事件率分母，确认前不写入 `Completed / Closed`。验收包：`code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r3/`。

## Stage 0.2 最终状态（2026-10-12，覆盖此前的待裁决/Blocked状态）

Stage 0.2 已在研究者批准的有限科学范围内 `Completed / Closed`，Gate=`pass`。范围为四个批准 NGSIM 来源、100 ms 连续性语义下的纵向跟驰风险代理测量与描述性现实校准。P2=4,545；可靠跟驰暴露512,043.2s；正式P2可评价跟驰暴露503,922.2s；不可评价8,121.0s；可靠闭合暴露208,026.3s。正式率以两端均为valid或not_applicable的可靠连续相邻边计时，单位events / P2-evaluable following vehicle-hour；不可评价边不代表零风险。四源分别报告，不当作iid道路样本。

未验证限制：独立物理真实性/人工几何真值、缺失造成的选择偏差及极端敏感性；200 ms两相位不与100 ms等价。禁止事故概率、危险识别准确率、P2全局最优性、SUMO或AAD因果效应主张。后续阶段职责不因本Gate通过而视为完成。旧R3 Blocked记录保留历史。最终包：`code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r4/`。

2026-10-18 AAD-0.5.4-A+：前两原始校准源车型/长度已100%连接，主线归一化、统一分层、实际时钟和代表性负载成本已明确；仍有边界选择与初始化积压。此为工程证据，未批准科学容差/暖机/预算，Measurement Ready待有限批准，Calibration Ready=false，Reality Coverage Accepted=false；推荐受限探索仅Proposal，本次未执行。Stage0.5 Gate不变。


2026-10-18 AAD-0.5.4-B0（RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1）：受限探索完成19/23次，4次高输入seed20261019响应未运行。统一27.78m/s上限、空初态、ballistic显式、internal.05/recorded.1、action.1、sigmaStep1；三个基准输入1087.364/1449.818/1648veh/h/lane仅实现局部密度10.37–15.75、均速约27.1，局部低速/P2均0。tau2三次末期未服务21/22/71，入口main0约2.5–20.1m有低速插入/加速，局部段无拥堵。B0-EXEC-STOP-01：原调度器未因completed+blocker停止，发现后人工停止，源码停止后修复并测试；最后worker峰值内存Unverified。推荐先批准需求边界/最小结构对照，不继续参数搜索掩盖状态支持缺口。所有结果exploratory_diagnostic_only、scientific_claim_eligible=false；Gate=pending_simulation_sample、Calibration Ready=false、Reality Coverage Accepted=false、正式容差Tolerance Not Yet Justified、Energy Distance上界Not Identifiable；B0实验验证输入0；根全量回归无过滤打开历史Stage0.2全源事件/案例产物，任务级验证访问不能认证（B0-VALIDATION-SCOPE-02）；数据隔离验收不Accepted。无holdout/正式校准/锁/Stage I。依据：docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md、同ID证据和execution_ledger。

## 2026-10-19 AAD-0.5.4-B1

B1（RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1）按阻断提前结束：V1失败A后7次未启动，V2 A有效/B警告/C阻断/D未启动，累计4次尝试；无补跑或新seed。A/B局部均速27.1088/26.5152m/s、密度16.3208/16.8197、低速0；C记录2.4007m/s、93.8653veh/km/lane、低速80.1719%、末期未服务252，但停车位移检查与冻结回溢资格阻断，不能作为有效校准样本。D只有静态/空加载检查，动态未知。

研究者保留B0有限描述证据，B0任务隔离false/验证物化Unknown不变。B1用两校准摘要白名单、SHA/角色守卫、-S最小胶囊、Python路径/子进程审计；冻结前45测试通过、假路径拒绝3/3，矩阵worker拒绝0；不声称OS/native全监控。根工作区不跑全量pytest，全量只在无本地历史数据的Git检出执行，数据skip不算通过。

Gate=pending_simulation_sample、scientific_claim_eligible=false、ready_to_start_stage_0_5_4b=false、reality_coverage_accepted=false；容差Tolerance Not Yet Justified，ED上界Not Identifiable，ProtocolLock/StageI禁止。仅推荐下一项B1.1停车数值/队列回溢观测契约整改，未启动。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md`、`evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1/`中的preflight、execution_stop_observation、numerical_stop_diagnostic、queue_diagnostics、run_manifest和SHA256SUMS。

## 2026-10-19 AAD-0.5.4-B1.1 独立测量契约整改

`RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1`：已核对固定SUMO1.26.0源码；内部负vNext不同于TraCI非负终速和当步平均加速度。4个独立微型fixture、1366条全量相邻边，其中1363精确核对最大残差1.4210854715202004e-14m，2条停车仅必要范围一致，1条edge转换不可评价。保留1e-6m，精确停车仍`Pending Numerical Equivalence`。14个先冻结真值的合成队列案例比较旧网格/新网格/车辆连接；观测与资格、内外排队分开，阈值均Candidate，未批准现实适用性。

B1 C两阻断和D not_attempted永久保留；B0隔离false/验证物化Unknown不变。无旧C状态读取、无新交通矩阵/参数搜索/校准。胶囊路径白名单与SHA、受审计91项测试通过；完整OS/native文件监控未证明。Gate=pending_simulation_sample，scientific_claim_eligible=false、ready_to_start_stage_0_5_4b=false、reality_coverage_accepted=false；容差Tolerance Not Yet Justified、ED上界Not Identifiable、锁/StageI禁止。下一项只建议独立停车分支可观测性最小验证；B1.2需另批，不自动执行。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_1_STOPPING_AND_SPILLBACK_CONTRACT.md`及同ID便携证据；协议/源码/输入冻结SHA见experiment_plan、PLAN_SHA256和provenance。

## RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1

`RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1`：固定SUMO1.26.0源码审计确认，非决策步的公开加速度被延续（`vSafe=v0+a_pub_start*h`），因此内部带符号候选终速可由公开TraCI独立重建 `u=v0+a_pub_start*h`，对任意符号精确成立，包括`u<0`的真实步内停车；决策步`v1=0`仍被`max(u,0)`钳制，仅可做范围一致检查。步[`t_prev`→`t_now`]为决策步当且仅当在`t_now`读到的`lastActionTime`等于`t_prev`。3个独立微型运行共948条相邻边：947精确核验且全部通过，最大绝对残差`1.4210854715202004e-14m`，1条决策步停车仅范围，0不可评价，0异常；未使用位移反推，未使用调试二进制。

决策步停车仍`Bounded Consistency Only`，未无条件放行全部停车测量；未修改B1.1结果`Pending Numerical Equivalence`。方案A（严格精确）需另批调试构建；方案B（分层准入）待研究者批准。B1 C两阻断和D not_attempted永久保留。Gate=pending_simulation_sample，scientific_claim_eligible=false；容差Tolerance Not Yet Justified、ED上界Not Identifiable、锁/StageI禁止。B1.2需另批，不自动执行。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_1S_STOPPING_OBSERVABILITY.md`及同ID便携证据；协议/源码/输入冻结SHA见experiment_plan、PLAN_SHA256和provenance。


## 2026-10-19 B1.2 分层准入与机制再验证

B1.2（RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2）工程接入阻断：10047精确边通过、14范围、84不可评价（含1近零终速不一致）。固定源码后处理与原非决策步最终候选广泛叙述冲突，Awaiting Researcher Decision。仅1个压缩fixture部分运行；D接入和A/B/C/D主矩阵未执行、B1_2_MAIN_MATRIX_ALLOWED=false。Gate/ready/现实覆盖/锁等不变；报告见docs/STAGE_0_5_TASK_0_5_4B1_2_BOUNDARY_BOTTLENECK_REVALIDATION.md。


## 2026-10-19 B1.2-N（独立工程观测）

`RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1`：独立B1.2-N工程任务。固定SUMO1.26源码完整谓词和调用顺序已审计；无停车任务的fresh/immutable生命周期可用doubleMax不变量，同edge常规停车仅非决策步可作充分条件。一般myStopDist不能由公开getter等价恢复。新候选`b12n-near-zero-observability-v1`不以位移/终速选择上下文，1e-6m不变。3个30s微型运行：2879边，2876精确全过（其中1负近零后处理），3 bounded，0近零未决/不可评价/工程错误；最大残差1.3988810110276972e-14m。冻结前203项受控合成通过。

正近零非决策步清零运行边未出现（Not Observed），未满足运行前冻结的共同准入条件；integration_allowed=false，C/D计划冻结被拒绝，均Not Attempted，未追加试验/搜索。新主矩阵禁止且0次。旧B1.2阻断/0-8/D未运行和所有历史证据不变。下一步由研究者决定正近零覆盖设计与未来政策，再另批接入/主矩阵；不自动继续。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2N_NEAR_ZERO_AND_INTEGRATION.md`；证据同ID目录。科研Gate/ready/现实覆盖/锁/StageI状态不变，科学阈值未批准。
