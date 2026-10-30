# Stage 0.5 Round2 Task 5：Task 4 证据完整性闭环（2026-10-30）

有限离线审计修复了三个 Task 4 证据问题：跨窗口时间戳重叠与精确记录/事件交集核查、Formal P2 onset unique/unmatched/ambiguous 守恒审计、真实不完整 30 s block 有效时长分母。Task 4 历史证据 SHA 不变，Gate/Stage 0.6/Protocol Lock/Stage I 不变。报告：`docs/STAGE_0_5_ROUND2_TASK5_TASK4_EVIDENCE_INTEGRITY_20261030.md`；证据：`evidence/results/RES-STAGE-0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-20261030/`。

# Stage 0.5 Round2 Task 4：真实源区支持与多尺度对照（2026-10-30）

离线重建两个授权 NGSIM US-101 窗口的 Formal P2 和固定 source/target onset 归属，复用封存 B00/Round2 measured state 做宏观、微观和风险对照。真实 source 有 167/159 个 Formal P2，B00/Round2 source formal-aligned/D1 均为 0；时间原点、cohort 和 simulator equivalence 仍未闭合。任务未启动新 SUMO/TraCI，Stage 0.5 Gate、Stage 0.6、Protocol Lock、Stage I 不变。报告：`docs/STAGE_0_5_ROUND2_TASK4_REAL_SOURCE_SUPPORT_AND_MULTISCALE_CROSSWALK_20261030.md`；证据：`evidence/results/RES-STAGE-0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030/`。

# AAD 阶段索引

## Stage 0.5-R0：候选包审查就绪，R1未执行

任务AAD-S0.5-R0-20261028只做离线设计准备；R0 READY_FOR_RESEARCHER_REVIEW，科学冻结AWAITING_RESEARCHER_DECISION。完整A03轨迹P2审计为0，保留缺失观测边界。三臂候选及60车匝道映射已准备，本轮SUMO0；Stage0.5科学交互Gate、Stage0.6、StageI和历史Not Accepted不变。报告：docs/plans/2026-10-28-stage-0-5-r0-design-freeze.md；证据：evidence/results/RES-STAGE-0.5-R0-DESIGN-PACKET-20261028/。

## 2026-10-27 Weekly B00 accepted; Stage I remains BLOCKED

Verified: A03 completed420s/8400native steps, independent receipt and all8 measurement checks Pass; B00_EXECUTED_MEASUREMENT_ACCEPTED. This task had3 real B00 starts: A01/A02 resource-coverage failures retained; A03 sealed trajectory independently remeasured with zero new launches after a coordinator import fix.1150declared=1005inserted+145native pending;857arrived/148active; collision/teleport/discard0 with complete required observation.18/18state/D1 support, E=9778.4veh-s, localP2=0. Final isolated software:1386passed/17skipped/7native excluded; audit denied0/SUMO0; compileall/docs/hash Pass. Scientific interaction Gate blocked; numerical budget/protocol candidate are Proposed, StageI BLOCKED. Historical Not Accepted unchanged. Evidence: docs/AAD_WEEK_TO_STAGE_I_2026-10-27.md; evidence/results/RES-AAD-WEEK-20261027-V1/; evidence/results/RES-STAGE-0.6-WEEK-20261027-V1/. Older blocks below retain their historical time points.

## 2026-10-27 B00已真实启动：BLOCKED_BY_VERIFIED_HARD_FAILURE

Verified：ENG-01/02/03修复、无数据全量1361通过/16跳过/7原生排除、compileall、修复后3s原生集成及独立回执Pass；纯Git定向165通过。新candidate-v8及聊天来源授权、实时硬检查完成后已直接执行一次B00（版本/仿真/真实TraCI各1）。最终状态BLOCKED_BY_VERIFIED_HARD_FAILURE：首个simulationStep发生i0007_i0007 slow lane ahead原生Error；冻结输入为15.23m/s、位置233.91m，下游main_2限速10m/s，按既定停止规则终止，420s未完成。仅t=0初始身份快照有效，末态插入/pending/discarded及全程碰撞/teleport均Unknown；三XML截断，18格测量不验收。capsule退出1，SUMO退出码未成功观测；后代已清理且无残留PID。未重复相同失败。具体初态/下游限速/原生Error停止规则冲突需科研决定，不能伪装成工程修复。旧Not Accepted及Gate不变。依据：docs/STAGE_0_5_B00_CLOSURE_2026-10-27.md；evidence/results/RES-STAGE-0.5-B00-NATIVE-V1/。下方为历史时点。


## 2026-10-26 V4合成集成工程Pass

唯一原生smoke及独立回执验收Pass；这是工程证据，B00/candidate-v5四false与BLOCKED_ENGINEERING、pending_simulation_sample及Stage1.1不变。依据：`docs/STAGE_0_5_V4_SMOKE_3_CONTINUATION_2026-10-26.md`；下方为历史时点。

## 2026-10-26 smoke 3未启动

PRELAUNCH BLOCKED，任务辅助预检异常后停止，0 SUMO版本/仿真/真实TraCI/科研轨迹；B00仍工程阻断、四false与科研Gate不变。依据：`docs/STAGE_0_5_V4_SMOKE_3_2026-10-26.md`。下方为历史时点。

## 2026-10-26 V4 r5仅准备

新合成smoke提案待精确授权，未运行；Linux v4研究准入候选仍BLOCKED_ENGINEERING，缺当前生产回执。四false、硬锁、pending_simulation_sample及科学Gate/δ/h/B/Stage1.1不变。新六组无害Python探针不构成生产smoke通过。依据：`docs/STAGE_0_5_V4_PREPARATION_2026-10-26.md`。下方为历史时点。

## 2026-10-26 V3工程准入未Ready

新真实证据验收与具体首批输入属于工程准备；0 SUMO/0真实TraCI/0新轨迹。OS隔离未获证明，原生锁True；不改变pending_simulation_sample、科学效应资格、真实覆盖接受或Stage1.1。

依据：`docs/STAGE_0_5_READY_TO_ADMIT_V3_2026-10-26.md`。

## 2026-10-25 Stage 0.5 V2准入工程闭环（最新）

身份/静态保真/硬锁adapter/隔离守卫与六份历史C6复核已完成其离线工程范围；原生隔离与实际初始化Unknown/Not Accepted，科学矩阵仍Proposed，pending_simulation_sample及Stage1.1不变。本轮0次SUMO启动/0新轨迹，V2账本0次。

依据：`docs/STAGE_0_5_V2_ADMISSION_ENGINEERING_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-V2-ADMISSION-ENGINEERING-V1/`。下方保留历史时点。

## 2026-10-25 Stage 0.5 V2研究任务

预算重构与四臂候选为工程准备，0次新轨迹；交互相容未通过，pending_simulation_sample不变。

依据：`docs/STAGE_0_5_RESEARCH_V2_AUDIT_2026-10-25.md`；`docs/STAGE_0_5_RESEARCH_V2_BUDGET.md`；`docs/plans/2026-10-25-stage-0-5-interaction-research-v2.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-RESEARCH-V2/`。以下内容保留其历史时点。


## 2026-10-25 Stage 0.5 离线候选

首次失败后只准备DS10MAX最小输入修订，计划未获精确确认。WP2–WP5仍未整体完成，Stage0.5/Protocol Lock/Stage1.1不变。

依据：`docs/STAGE_0_5_DEPART_SPEED_CANDIDATE_2026-10-25.md`；`docs/plans/2026-10-25-stage-0-5-depart-speed-candidate-v1.md`；`evidence/results/RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1/`。以下原内容保留。


## 2026-10-25 Stage0.5政策A首次失败

诊断设计已批准并任务绑定；ID1在180s失败，1/3，ID2/ID3按停止规则未执行；不代表科学Gate或三次对照完成。

依据：`docs/STAGE_0_5_INTERACTION_DIAGNOSTICS_POLICY_A_EXECUTION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/`。以下旧状态保留为历史时点。

## 2026-10-25 政策A与最终计划预检

Stage0.5新增政策A预检：共同支持及资源快照通过，运行计划仍待确认，未冻结且0次新轨迹。

依据：`docs/plans/2026-10-25-stage-0-5-interaction-diagnostics-policy-a-final.md`；`evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1/`。


## 2026-10-25 C6/C7 offline phase

Stage0.5新增C6/C7离线工程证据，初始化政策待研究者确认；不解锁后续阶段。

依据：`docs/STAGE_0_5_C6_C7_OFFLINE_DECISION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-C6-C7-OFFLINE-V1/`。


> 核对日期：2026-09-10。机器标识统一使用 `stage_X_Y`；旧实验编号仅保留在历史映射和旧证据中。

## 当前顺序

`阶段 0.1 → 阶段 0.2 / 0.3 / 0.4 → 阶段 0.5 → 阶段 0.6 → 协议锁 → 阶段 1.1`。

## stage_0_1 — 正式实验基础设施

工程 Gate 已完成；验证四格、五表、运行隔离、时钟、车辆生命周期、封存和独立复算。只属于工程证据。

## stage_0_2 — NGSIM 跟驰风险审计

当前主任务。审计前车关系、净间距、闭合速度、TTC、DRAC和风险事件，并整理现实参考范围。

## stage_0_3 — pNEUMA 城市运动学校准

只整理速度、纵向加速度和车型分布；不再推断前车，不计算 TTC/DRAC，不进行人工前车复核。

2026-10-12：综合实施与验收准备完成。785 轨迹 / 1,239,475 状态全量审计、时间加权/车辆等权描述性统计、敏感性与 bootstrap、Stage 0.5 真实接口测试均通过，独立复算零差异。报告：`docs/STAGE_0_3_PNEUMA_KINEMATICS_2026-10-12.md`；结果：`RES-STAGE-0.3-PNEUMA-KINEMATICS-R1`；验收准备包：`code/outputs/formal/calibration/stage_0_3_pneuma_kinematics_20261012_r1/`。状态 **Gate Pass Candidate**，科学 Gate 与未冻结参数（连续性容差、描述性阈值、车型映射、适用范围）待研究者审核。

2026-10-16（R2，当前）：AAD-S0.3-T02 边界修复完成。修复排序掩盖原始时间顺序、重复 track_id 字典覆盖与 Stage 0.5 质量字段语义失真三项工程缺陷；时间连续性改为排序前按原始记录顺序评估，时间加权区间由原始顺序邻接定义，轨迹审计以原始行为单位、重复 ID fail-closed，`quality_status` 逐状态推导且 `write_real_reference_package()` 实际使用质量字段。真实统计结果不变（145 项比较：30 项浮点末位、1 项结构性记录差异、无统计变化）；独立复算 discrepancies=0；全量测试 315 passed。报告：`docs/STAGE_0_3_BOUNDARY_REPAIR_R2_2026-10-16.md`；结果：`RES-STAGE-0.3-BOUNDARY-REPAIR-R2`；验收准备包：`code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2/`。状态保持 **Gate Pass Candidate（R2）**，待研究者最终裁决。

2026-10-16（R3，当前）：研究者经任务 AAD-0.3.3 批准五项决定，**Stage 0.3 正式关闭**：正式范围限本文件实际观测车辆的描述性城市运动学参考；连续性规则 `0<Δt≤0.043 s` 升格为已批准科学参数（仅本 25 Hz 文件）；极端观测原始保留+标记+敏感性；描述阈值仅统计描述；`Scientific Gate=pass`、`Completed / Closed`。关闭包基于 R2 证据 fail-closed 复核（checksum、计数、统计不变性、独立复算 discrepancies=0），未重跑全量管线。报告：`docs/STAGE_0_3_SCIENTIFIC_ACCEPTANCE_2026-10-16.md`；结果：`RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3`；包：`code/outputs/formal/calibration/stage_0_3_scientific_acceptance_20261016_r3/`。R1/R2 历史包保留不覆盖；Stage 0.5 的车型映射、时间权重抽样与覆盖阈值独立待决。

## stage_0_4 — SPMD 通信证据边界

已确认 RV_RX 只支持接收状态连续性；packet级时延、丢包和采用仍不可观测。

2026-10-16（AAD-0.4.1，日期勘误 2026-10-17）：完成下载前数据源调查（只读，未下载）。SPMD 官方条目（DOI 10.21949/1504482）2026-01 重建，下载端点由历史 403 变为 302 重定向至官方文件 API（最终可达性待下个授权下载任务验证）。官方字典确认：Packet（15.33 GB）为 RSE 侧捕获（仅捕获时间戳、IP 轮换、无发送时刻）；BsmP1（55.72 GB）具备发送侧字段（TxRandom/MsgCount/Gentime 含官方换算）；RSE_BSM（3.23 GB，此前未被重视）为 RSE 接收 BSM 内容且含 4 个未文档化字段。跨设备时钟同步是全部时延主张的共同未验证前置。其他候选：AMCD BSM（唯一同行 sent/received 时间，云接收）、NYC IE EVENT（告警级，时间空间分箱）、Tampa BSM 样本（RSU 接收）。推荐渐进下载 RSE_BSM+Packet（18.6 GB）→ 视核验结果再定 BsmP1。报告：`docs/STAGE_0_4_TASK_0_4_1_DATASET_SURVEY.md`；清单：`docs/research/stage_0_4_dataset_candidates.json`。Gate 与既有结论不变。

2026-10-16（AAD-0.4.2，日期勘误 2026-10-17；当前）：经研究者批准，成员级 Range 方式获取 `RSE_BSM.csv.zip`（3,228,646,514 B；CRC32/中央目录一致、内层 ZIP 校验通过、SHA-256 已钉扎）。实测 25 字段（官方 24+RxDevice）、124,115,615 行零畸形、BSMID 逐行唯一、无任何绝对时间字段；RxDevice 2,008 值全部落在 BsmP1Summary 设备命名空间、与 RSE LocID 零重叠（“RSE” 命名与实际记录方命名空间不符，Ambiguous）；成员内最佳配对键重复 ≥26.9M——配对/时延/丢包仍 Ambiguous/Not Observable。行为统计按 holdout 规则暂缓。Packet 建议为下一批（RSE 侧绝对时间+信道条件，修正预期：与 RSE_BSM 无文档化连接键）；BsmP1 价值上调（RxDevice+Gentime 时间锚候选）；新识别 BsmMd（17.29 GB）与 RSE_locations.kml（520 B）。结果 `RES-STAGE-0.4-RSE-BSM-V1`；报告 `docs/STAGE_0_4_TASK_0_4_2_RSE_BSM_AUDIT.md`。Gate 保持 `pending_official_packet_access`。

## stage_0_5 — 仿真—现实覆盖

用 NGSIM 跟驰风险与 pNEUMA 城市运动学约束无消息作用的 SUMO 校准样本。当前缺仿真样本。

2026-10-18（AAD-0.5.1）：`RES-STAGE-0.5-REAL-REF-R2` 正式真实参考重建完成。canonical pNEUMA 已由 writer 原生消费并保留车型、质量和来源指纹；四个 NGSIM 状态源、正式 4,545 条 P2 事件和 Stage 0.3 时间/车辆等权摘要通过 SHA/schema/来源契约。稳定哈希状态样本和轨迹簇样本只作诊断，real-real 独立性不足，覆盖阈值未冻结。Stage 0.5 仍 `pending_simulation_sample`，未运行 SUMO。

2026-10-18（AAD-0.5.2）：完成分场景现实覆盖指标与校准—验证协议候选设计。建议 US-101 以速度/加速度、净间距/闭合速度、风险可观测性、P2 暴露/事件率五层必要条件评价；Lankershim 独立辅助；pNEUMA 仅城市运动学。当前 Energy Distance 仅具场景内描述性/辅助价值，real-real 科学上界因来源独立性不足仍 `Not Identifiable`。报告：`docs/STAGE_0_5_TASK_0_5_2_COVERAGE_PROTOCOL_DESIGN.md`。未冻结容差、时间步、车型映射、验证划分或 Gate。

2026-10-18（AAD-0.5.3）：新增独立 SUMO 无消息工程骨架。US-101 `generic_highway_candidate`（3 主线段 × 3 车道 + 入口/出口匝道）在 SUMO 1.26.0 上以 seed=20260907、internal 0.1 s、recorded 0.1 s 完成 baseline 与 measurement probe 两个工程 fixture，输出状态、leader/net-gap、统一闭合速度、TTC 状态、暴露和两路工程 P2 适配；核验并订正 TraCI `getLeader` 净间距语义与 `closing_speed = follower − leader`，建立 internal/recorded 时间步分离与校准/验证 fail-closed 守卫。结果仅 `engineering_only`。Lankershim/pNEUMA 保持 candidate_entry_only，P2 正式等价性 pending，Stage 0.5 Gate 未升级。报告：`docs/STAGE_0_5_TASK_0_5_3_SUMO_BASELINE_ENGINEERING.md`。

2026-10-18（AAD-0.5.4-A）：完成 SUMO 正式校准前的科学准入与参数协议审计。P2 测量等价性 16 项维度逐条判定（10 Equivalent/Verified、6 Engineering Consistent Only、0 阻断），16 个确定性边界用例全部符合预期，并独立复现已批准两窗口的可评价暴露、事件数与事件率。修复 6 项适配层缺陷（绝对时钟、前车帧号、退出原因、闭合 epsilon、可靠层定义、DRAC）而不改动 Stage 0.2 规则。产出校准窗口运动学/跟驰/可观测性统计、需求可识别性矩阵、候选交通状态分层、轨迹簇不确定性、时间步敏感性与成本基准、候选校准协议与研究决策矩阵。准入状态 `ready_to_start_stage_0_5_4b=false`；未读取验证窗口、未冻结容差或参数、Gate 不变。报告：`docs/STAGE_0_5_TASK_0_5_4A_CALIBRATION_READINESS.md`。

## stage_0_6 — 数值验证与协议锁定

技术真值检查已有结果；待前置 Gate 和科学容差冻结后生成不可覆盖的协议锁。

## stage_1_1 — 核心效应确认

已同意的后续目标，尚未实现、未运行、无结果；协议锁完成前禁止启动。

## 后续阶段

- 阶段 1.2—1.3：竞争基线与独立复算。
- 阶段 2.1—2.4：生命周期、负对照、通信损伤与消融。
- 阶段 3.1—3.2：连通场景校准与正式跨几何验证。
- 阶段 4.1—4.6：真实留出校核与跨条件泛化。
- 阶段 5.1—5.4：困难场景、控制优化、尾部验证与真实控制栈。
- 阶段 6：全文复算与投稿。

新增阶段或状态变化时，同步修改本索引、`PROJECT_REGISTRY.json`、`RESEARCH_STATUS.md`和对应执行记录。

任务 2.2 自动诊断报告：docs/STAGE_0_2_TASK_2_2_KINEMATIC_REVIEW_2026-10-10.md；完整案例包位于 code/outputs/formal/calibration/stage_0_2_task_2_2_kinematic_review_20261010_r6/。人工判断尚未完成。

任务 2.2.1 连续风险修复与验收：docs/STAGE_0_2_TASK_2_2_1_CONTINUITY_FIX_2026-10-10.md；产物 code/outputs/formal/calibration/stage_0_2_task_2_2_1_20261010_r5/。

- 2026-10-11：任务 2.2.1 连续风险最终修复产物 `stage_0_2_task_2_2_1_20261011_r9`；447 案例分类/阈值统计、48 案例覆盖和空白复核包已重算，工程结果待研究者验收。

- 2026-10-11：新增任务 2.3 NGSIM 风险质量与稳健性综合收口报告及独立产物 `stage_0_2_task_2_3_20261011_r3`。

- 2026-10-11：任务 2.4 正式事件等价性与风险稳健性最终验证；新增 `docs/STAGE_0_2_TASK_2_4_EVENT_EQUIVALENCE_2026-10-11.md` 和独立产物 `stage_0_2_task_2_4_20261011_r2`。

- 2026-10-11：任务 2.5 阈值、持续时间与物理合理性联合验证材料完成，新增报告和独立产物 `stage_0_2_task_2_5_20261011_r1`。


- 任务 2.5.1：P1/P2/P3 成员级事件对应、24 案例新图册和因果确认审计；科学参数保持未冻结。


- 任务 2.5.2：关键差异案例与中心事件归属验证；科学规则保持未冻结。


- Task 2.5 decision ratification：研究者设计已归档，参数核定与实现缺口保留为待完成事项。


- 连续风险时间尺度验证：rho 分布、暴露时间与贡献结构已完成，未修改科学参数。

- 正式风险测量接口与 P2 独立复核：4,545 个事件一致；区域 burden 因未批准目标区域/窗口保持 Unresolved。

- 正式风险测量一致性修复：P2 事件、车辆对和连续性字段完成独立回归。


## 2026-10-12 Stage 0.2 最终验收审计（当前状态）

最终验收包：`code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r3/`；Gate=`Blocked`。P2=4,545、可靠跟驰暴露512,043.2s、闭合暴露208,026.3s及四源事件率均可复算；独立边级审计确认连续性和来源身份条件，但发现分母含 `invalid/non_positive_gap` 端点边（Lankershim 7,557.4s；US-101 三窗口187.4/178.7/197.5s），其P2可评价性未由批准决定定义。研究者需确认这些边是否属于正式事件率分母，确认前不得关闭。200ms两相位不等价、极端屏蔽与独立物理真实性Unverified继续披露；无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。

## 2026-10-12 — Stage 0.2 最终验收已关闭

Stage 0.2 Gate=`pass`，状态=`Completed / Closed`，限四个批准NGSIM来源和100ms描述性纵向跟驰风险代理测量。研究者批准P2可评价跟驰暴露分母；独立边级复算计入5,039,222条边/503,922.2s，8,121.0s不可评价暴露保留为质量统计，不解释为零风险。P2=4,545。四源事件率和逐源分母在`RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4`报告。200ms非等价、物理真实性、缺失选择偏差、极端敏感性、来源外推继续限制科学解释。R3 Blocked为历史记录，未覆盖。详见`docs/STAGE_0_2_SCIENTIFIC_ACCEPTANCE_2026-10-12.md`及最终包。

2026-10-17（AAD-0.4.3，只读核查）：新获官方文档（ROSA P WSU BSM Codebook + mCity 数据集文档）裁定：`RxDevice`≡车辆设备 ID（接收日志）、`Gentime`=BSM 生成时间（µs 自 2004-01-01，1609.2；35 s 文档冲突待校准）、`TxDevice/TxRandom`=临时 ID 静态/随机 2 字节、`DSecond`=分钟内毫秒（手册 §5.4 描述被样例算术否定）。硬边界：**车辆侧接收时间在 SPMD 全家族不存在→V2V 端到端时延不可算**；唯一时延类量=生成→RSE 捕获（需 Packet 且身份匹配未证）。RSE_BSM 采样设计 Unverified（≤2 记录方/发送方 ID，双记录对全含 10106）——接收率统计前必须查明；holdout 4 候选方案待研究者。下一批建议：**BsmMd（17.29 GB）优先**、BsmP1（55.72 GB）次之、Packet 不为凑 Gate 项提前；新渠道候选 mCity Rx-BSM 过滤数据集（~9 GB，Globus）。零下载，Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_3_IDENTITY_TIME_REVIEW.md`。

2026-10-17（AAD-0.4.4，只读专项调查）：跨 DSRC/ITS-G5、C-V2X、V2I、CV Pilot 四方向核查 9 个候选。核心发现：①接收时间+同消息通信时延获得可信真实证据——Bristol ITS-G5 FLOURISH（同设备日志 Tx/Rx CAM 双侧时间戳+SeqNum+RSSI，受控条件，公开 34.3 GiB/含 MAT 子集）与 SEE-V2X（C-V2X 跨层端到端时延，表单）；②丢失率——UCI DSRC（PER 样本）、Bristol（SeqNum 间隙法）、SEE-V2X（PDR）；③采用——仅驾驶员层面真实数据（THEA Phase 3：85% FCW 后 3 s 减速、+9.93% 接口效应），控制器层面公开实车数据 Not Observable（永久缺口）；④自然交通 V2V 端到端时延公开数据不可达（SPMD/mCity 同边界）。四证据场景互异，禁止混用。最小验证批次 A（Bristol importedData，<=25 GiB）已定义验收条件；待研究者批准项 5 项（含验收范围是否接受受控试验参考）。零下载、零申请；Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_4_COMMUNICATION_EVIDENCE_SEARCH.md`。

2026-10-17（AAD-0.4.5，只读核查）：SEE-V2X 与 Bristol 可用性裁定。SEE-V2X **可用且为首选**：`latency=rx_timestamp−tx_timestamp` 在接收端单设备日志内成对（`tx_seq_num` 同消息配对），不依赖跨设备时钟；公开 Google Drive 免申请（emulating_applications 4.89 GiB；最小样本 outdoor_parkinglot 4.9 MB；参数扫描合计 18.76 GiB）；`per_ue_loss_pct` 分母待实证。Bristol **不可用于时延**（论文零延迟分析、Timestamp=创建时刻、无跨设备同步），仅 PDR/RSSI（频率勘误为 100 Hz）。UCI DSRC 实测属性 Unverified。85% FCW 响应率为 WYDOT（非 Tampa）。第一批建议 SEE-V2X 最小样本（<0.5 GiB）。零下载，Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_5_DATA_ACCESS_VALIDATION.md`。

2026-10-17（AAD-0.4.6，实证验证）：SEE-V2X 最小样本（outdoor_parkinglot.tar.gz，4,883,437 B，公开 Drive）已获取并实证。核心结果：**同消息关联 Verified**（10/10 次运行配对率 1.0，`seq_num` 0..N−1 唯一，发送端 t1/接收端 t3 日志按 (equipment_id, seq_num) 关联）；**latency 数值可计算 Verified**（(rx−tx)/1000 与 latency 列在 30,571 行逐行一致、0 负值，分布 P50=16.787 ms）**但物理意义（真实时延）Unverified**（跨设备时钟偏移未证，绝对值可能含固定偏移）；**PDR/PER Verified**（sender-base 独立复算与 `per_ue_loss_pct` 字段逐 run 一致，分母=发送数、接收机会=运行内，明确可复算）；信道占用 Documented（停车场低负载 P50 5%/max 23%）。`extra=1` 插值行已按规则排除。正式校准**暂不冻结**；建议条件性批准下一批 `emulating_applications`（4.89 GiB，BSM 场景+GNSS 可能提供时钟参照）。作者咨询邮件草稿已备未发。零超范围下载，Gate 不变。结果 `RES-STAGE-0.4-SEE-V2X-MINIMAL-V1`；报告 `docs/STAGE_0_4_TASK_0_4_6_SEE_V2X_MINIMAL_VALIDATION.md`。

2026-10-17（AAD-0.4.6.1，科学复核）：仅复用 0.4.6 样本独立复核。**PDR 口径修正**：0.4.6 的 `independent_pdr` 用接收窗口口径（排除边界未接收段）系统性高估——**Run 2 完整运行 PDR=0.9737（非 100%）**（发送 5,742/接收 5,591，边界 [0,150] 未接收）；正确口径=**完整运行 PDR**（分母=运行内全部发送），字段 `per_ue_loss_pct`≈接收窗口口径（系统性高 0.3–5 pp）。**时延**：数值复算 Verified，但跨运行固定时钟偏移 P50 8.8–32 ms → **合并分位数不可靠**（降级），逐运行形态相对可信但含漂移（run2 前半−后半 −6.8 ms）。时钟同步凭现有数据不可解（缺共用钟/互偏移/`tx_timestamp` 捕获点声明）。正式校准仍不冻结。下一批 4.89 GiB 建议（目的修正：GNSS 时钟参照+轨迹绑定）。零下载零邮件，Gate 不变。结果 `RES-STAGE-0.4-SEE-V2X-REAUDIT-V1`；报告 `docs/STAGE_0_4_TASK_0_4_6_1_SCIENTIFIC_REAUDIT.md`。

2026-10-17（AAD-0.4.6.2，科学修正+复现修复）：基于 0.4.6/0.4.6.1 的进一步修正。**PDR**：`parameters.csv` 证明 10 运行配置互异（包大小×优先级，发送速率实测 50 Hz）；接收端时长系统性短于发送端且首个接收时戳晚 ~3 s——Run 2 边界 [0,150] 高度符合设备启停而非丢包；**接收机会 Unverified**，完整运行 PDR 仅作描述性指标、不作正式链路丢包率。**时延**：跨运行 P50 差异（8.8–32 ms）由**真实 PHY/MAC 序列化**解释（包大小单调相关：100B 8.8–11、5000B 24–26、8000B 21.8–30 ms），**非时钟偏移**；时钟同步仍 Unverified 但不主导跨运行模式。0.4.6.1 的"跨运行差异=时钟偏移/漂移"过强表述已纠正。**Git 可复现已修复**：`code/tmp/reaudit_*` 入 Git、6 个独立测试通过（Run 2 PDR=0.9737 等）、封存 manifest 补充 method+results。下一批 4.89 GiB 建议（BSM 场景+GNSS；时钟可能仍不可解）。零下载零邮件，Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_6_2_SCIENTIFIC_CORRECTION.md`。

2026-10-17（AAD-0.4.7，BSM 实证）：获取 `emulating_applications.tar.gz`（4.89 GiB，SHA-256 17AB3AC1…0861），提取 BSM+GNSS（峰值 ~10 GiB）。核心结果：①BSM 消息关联 **Verified**（4 场景 × 12 有序设备对，配对率室内 0.998–1.0、室外 0.22–1.0，128B/10 Hz，设备 rsu=1/t1=2/t2=3/t3=4）；②PDR 接收机会**已证**——GNSS 窗口（t1/t2/t3 各 9,631 s）覆盖全部通信时间戳（100%），室外 PDR 0.22–0.90 为真实投递、非启停；③GNSS 时间对齐 Verified（同 UTC 纪元，无任意偏移拟合），但 mobile-mobile 距离全在 0–50 m，**距离×PDR 曲线动态范围不足**；④时延数值 Verified，时钟 epoch 一致但**亚毫秒相位同步 Unverified**，绝对值不冻结。前置修复：Git 复现测试路径改读已提交 `code/tmp/reaudit_results.json`，本机 6/6、纯克隆 5 算术测试真实通过 + 1 原始数据测试 skip。价值：受控 PC5 候选参数（非正式校准）。零超范围下载，Gate 不变。结果 `RES-STAGE-0.4-SEE-V2X-BSM-V1`；报告 `docs/STAGE_0_4_TASK_0_4_7_SEE_V2X_BSM_VALIDATION.md`。

2026-10-17（AAD-0.4.7.1，科学复核+交付修复）：修正 0.4.7 三处过度解释并完成 GitHub 交付。①**概念混淆修正**：配对率（Rx→Tx 匹配）=1.000 vs 接收比例（Rx/Tx）=0.22–1.0，已分开报告（48 对全量机器可读）；②**GNSS≠接收机在线**：GNSS 仅覆盖室外、RSU 静态单点、室内无 GNSS；无无线模块状态证据 → 真实链路 PDR 与接收机会全部 Unverified；③**时钟纪元歧义**：tx_timestamp(µs) 与 GNSS UTC_ns 差 ×1000，纯数值对齐非独立时钟证据 → 绝对时延 Unverified；④**距离**：仅室外 ~0–10 m（室内无 GNSS），不足建距离—PDR。**GitHub 交付修复**：0.4.7 commit 仅含 2 文件（报告等未暂存），已补齐；test 路径修复（纯克隆 5 算术测试通过）；新结果 `RES-STAGE-0.4-SEE-V2X-BSM-REAUDIT-V1`。零下载零邮件，Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_7_1_SCIENTIFIC_REAUDIT.md`。

2026-10-17（AAD-0.4.7.2，GNSS 修复+收束）：修复 0.4.7.1 三处 GNSS 缺陷——窗口外钳制改为拒绝、时间误差对真实邻点（修 µs/ms 单位）、轨迹独立性检查。决定性发现：**t1/t2/t3 GNSS 轨迹逐点完全相同**（962,995/962,995 精确匹配）——为同一物理轨迹复制品，非三个独立设备；室外设备间距离恒 0 m 系轨迹复制（非车辆重合/计算错误）；RSU 静态单点、室内无 GNSS。**距离—通信关系不可识别**，不拟合不外推。通信统计不受影响（配对率 1.0、接收比例 0.22–1.0 不变）。**SEE-V2X 阶段收束**：可用=受控 PC5 候选参考（配对方法/接收比例/相对时延）；Unverified=链路 PDR/接收机会/绝对时延/距离—PDR/自然交通 V2V。剩余问题仅需作者说明或未来独立证据。新增 6 项独立 GNSS 测试（全过）。零下载零邮件，Gate 不变。结果 `RES-STAGE-0.4-SEE-V2X-GNSS-REPAIR-V1`；报告 `docs/STAGE_0_4_TASK_0_4_7_2_GNSS_VALIDITY_REPAIR.md`。

2026-10-17（AAD-0.4.8，有限科学验收）：研究者批准 Limited Scientific Acceptance。Stage 0.4 正式收束：**Gate=`pass_limited`；Stage Status=`Completed / Closed (Limited Scope)`**。验收范围仅限：可观测性边界+已验证描述性证据+参数不确定性处理原则；不验收真实性能模型/数值校准/距离函数/采用/核心因果效应。证据分层：Verified=RV_RX 连续性、RSE_BSM 车辆侧接收内容、SEE-V2X 配对方法/接收比例/时延数值；Unverified=链路 PDR/接收机会/绝对时延/距离—PDR/采用/自然交通外推；候选参考=受控 PC5 配对方法与接收比例范围；否定性结论全部保留。通信参数**未冻结未校准**（不足部分为标记不确定的实验/敏感性参数）。RV_RX V3 `pending_official_packet_access` 与 Packet HTTP-403 保留为历史事实未改写。readiness 测试证明 pass_limited 在其他 gate 未过时仍阻断锁（`protocol_lock_allowed=false`、`stage_1_1_allowed=false`）。零下载零邮件，Gate 契约不变。结果 `RES-STAGE-0.4-LIMITED-SCIENTIFIC-ACCEPTANCE-V1`；报告 `docs/STAGE_0_4_LIMITED_SCIENTIFIC_ACCEPTANCE_2026-10-17.md`。

2026-10-18（AAD-0.5.0）：完成只读场景设计与技术可行性审计。US-101 三窗口为高速公路跟驰风险主线候选；Lankershim 保持独立城市道路辅助候选；pNEUMA 仅承担单文件城市混合交通运动学。确认 Stage 0.3 R2 标准化 Parquet 与当前 writer 的列契约不兼容：标准字段为 vehicle_id/acceleration_mps2，writer 仍读取 id/longitudinal_accel_mps2；现有测试通过的是脚本生成的旧字段适配视图。报告：docs/STAGE_0_5_TASK_0_5_0_SCENARIO_DESIGN_AUDIT.md。状态仍为 Active / pending_simulation_sample；车型映射、抽样权重、时间分辨率和覆盖阈值均未批准。

2026-10-18 AAD-0.5.4-A+定向缺口补充已完成（RES-STAGE-0.5-CALIBRATION-GAPS-V1）。来源车型/长度、主线空间/流量、统一分层、实际时间和负载成本已量化，局部P2归属/时间/科学容差/预算仍待研究者。Engineering Ready有条件，Measurement Ready待批准，Calibration Ready=false、Reality Coverage Accepted=false；Gate=pending_simulation_sample，正式校准/验证/锁/Stage I/II未启动。


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

## 2026-10-19 AAD-0.5.4-B1.1-S 公开接口停车可观测性验证

`RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1`：固定SUMO1.26.0源码审计确认，非决策步延续公开加速度，因此内部带符号候选终速可由公开TraCI独立重建 `u=v0+a_pub_start*h`，对任意符号精确成立，包括`u<0`的真实步内停车；决策步`v1=0`仍被`max(u,0)`钳制，仅可范围一致检查。3个微型运行、948条相邻边：947精确核验且全过，最大残差`1.4210854715202004e-14m`，1条决策步停车仅范围，0不可评价，0异常；未用位移反推、未用调试二进制。方案A/B准入比较与B1.2前置条件已登记，待研究者决定。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_1S_STOPPING_OBSERVABILITY.md`及同ID便携证据；协议/源码/输入冻结SHA见experiment_plan、PLAN_SHA256和provenance。


## 2026-10-19 B1.2 分层准入与机制再验证

Stage0.5新增RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2（B1.2前置工程阻断）。主矩阵0/8，近零清零适用域Awaiting Researcher Decision，Gate仍pending_simulation_sample；无正式校准、Stage0.5.5、Protocol Lock或StageI。


## 2026-10-19 B1.2-N（独立工程观测）

`RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1`：独立B1.2-N工程任务。固定SUMO1.26源码完整谓词和调用顺序已审计；无停车任务的fresh/immutable生命周期可用doubleMax不变量，同edge常规停车仅非决策步可作充分条件。一般myStopDist不能由公开getter等价恢复。新候选`b12n-near-zero-observability-v1`不以位移/终速选择上下文，1e-6m不变。3个30s微型运行：2879边，2876精确全过（其中1负近零后处理），3 bounded，0近零未决/不可评价/工程错误；最大残差1.3988810110276972e-14m。冻结前203项受控合成通过。

正近零非决策步清零运行边未出现（Not Observed），未满足运行前冻结的共同准入条件；integration_allowed=false，C/D计划冻结被拒绝，均Not Attempted，未追加试验/搜索。新主矩阵禁止且0次。旧B1.2阻断/0-8/D未运行和所有历史证据不变。下一步由研究者决定正近零覆盖设计与未来政策，再另批接入/主矩阵；不自动继续。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2N_NEAR_ZERO_AND_INTEGRATION.md`；证据同ID目录。科研Gate/ready/现实覆盖/锁/StageI状态不变，科学阈值未批准。


## 2026-10-19 B1.2-P（受限正近零独立验证）

`RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1`：B1.2-P仅数值观测独立任务。固定SUMO1.26/commit fa7df22d，13具名源码完整谓词/赋值路径核对；fresh/no-stop/无恢复/无控制/无特殊设备/非循环路线doubleMax不变量独立成立。5个冻结原生红灯制动探针各2s、无车辆setter/无重试。实际P1/P2在.10→.15s非决策步重建u_pre约1.999999909e-6/4.800000001e-6，公开终速0，最终分支由源码与生命周期先行确定，位移残差-4.6161e-15/-6.4115e-15m。2条目标Exact Pass；195边中192一般精确全过、3 bounded、0未决/不可评价/阻断。P3/P4/P5实际阈值以上保持正终速；P3名义等号但实际略高，运行精确等号Not Observed。1e-6m未放宽，残差不用于反推上下文。

仅target_branch_verified=true，C_D_allowed=false/main_matrix_allowed=false/future_numerical_policy_approved=false。不需要为该受限分支使用调试构建；一般停车/状态恢复/特殊控制域未验证。B1.2-N正近零Not Observed与integration_allowed=false、旧B1.2阻断/0-8及所有历史原样保留。本轮C/D和主矩阵0次；下一步研究者需决定未来数值准入政策，另批剩余接入；不自动执行。科学Gate及所有ready/现实覆盖/锁/StageI资格不变。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2P_POSITIVE_NEAR_ZERO.md`；证据同ID目录。


## 2026-10-19 C/D有限接入与自主问题发现

`RES-STAGE-0.5-CD-INTEGRATION-V1`：C/D有限接入2次各60s；62707边中62513精确全过、63 bounded、131合法坐标不可评价、0数值阻断。C内部队列/上游扩展/入口邻近与87 pending可观测，但入口与下游锚定组件约14.35m>10m，持续回溢EI。D9辆实际换道和main2出口由原始状态独立验证；v1 main_1-only假阻断保留，v2修复无重试。定向0/8、主矩阵0次；正式Gate和全部历史不变。

报告 `docs/STAGE_0_5_TASK_CD_INTEGRATION_AND_ISSUE_DISCOVERY.md`；证据 `evidence/results/RES-STAGE-0.5-CD-INTEGRATION-V1/`。研究者本轮授权工程分层与新增2次接入（已用完）、定向最多8次（未用）；无ABCD授权。近零仅fresh/no-stop域，1e-6m不变。当前最重要决策是下一局部跟驰探索是否需要完整入口回溢，以及评价时间/需求/科学容差/P2局部归属协议；不为非核心私有量无限追加验证。旧B1/N/P授权与状态作为历史保留。通用路网/局部匹配为当前研究者优先，真实几何完整复现非必要前提，但结构/匝道/波传播结论受限。


## 2026-10-19 局部跟驰探索（方案A）

`RES-STAGE-0.5-LOCAL-FOLLOWING-EXPLORATION-V1`：方案A局部探索已独立执行3/8次（120s同步、120s批处理、300s延长），剩5；接入额度不复用。175679行/28非标签字段及延长前缀完全相等，worker283.31→68.63s约4.13倍，无缓存/观测降频。固定原尺度C main1[50,250)m局部可测；LF3均速2.964/density81.558/低速77.03%，1222个TTC<2点中1203在前120s。全网核心266工程事件/42404.3veh-s；局部归属起始86/确认87/全程83，正式局部P2/暴露Unresolved、率Not Calculated。14.35m间隙离线分解，C回溢EI不变；正式Gate/历史不变。

报告 `docs/STAGE_0_5_LOCAL_FOLLOWING_EXPLORATION.md`；证据同结果ID目录。研究者已批准局部探索不以完整入口回溢资格为前提；未批准局部P2归属、正式暖机/窗口、科学容差/需求识别/校准目标。需要的3项决定集中在researcher_decision_matrix.json。当前工程闭环不代表科学Gate，通过只在受限fresh/no-stop/只读域成立。LF1/LF2为同seed读取对照，LF3为同seed延长，不当独立重复池化。正式Gate、C回溢EI与历史不变；没有ABCD/正式校准/Lock/I-II。

## 2026-10-20 LF候选协议整合

266个原核心工程事件独立重建、逐成员核对；历史86/87/83重现，开始至确认全在域为86，差异4件。共同候选分母14636.2veh-s，局部正式P2仍Unresolved/Not Calculated。相位周期5/10/20%敏感性均到300s才完成，后评价0s；局部平台而全网/pending增长。五层必要目标、需求可识别性和科学误差/精度候选已整合为D1–D5待决；无新增SUMO，累计3/8剩5。C回溢EI与全部历史、Gate/Lock/I-II状态不变。

报告 `docs/STAGE_0_5_LOCAL_FOLLOWING_PROTOCOL_DESIGN.md`；计划 `docs/plans/2026-10-20-lf-protocol-consolidation.md`；证据 `evidence/results/RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1/`。


## 2026-10-20 Stage 0.5 最终收口（AAD-0.5-FINAL-CLOSURE）

结果 `RES-STAGE-0.5-FINAL-CLOSURE-V1`。按研究者批准的 D1 主口径（风险开始位置与开始时间）重算两个真实校准窗口的正式局部 P2 与可评价暴露：0750–0805 147 件 / 31,051.6 veh-s / 17.0426；0805–0820 216 件 / 33,091.1 veh-s / 23.4988（单位 events / P2-evaluable following vehicle-hour）。全源 543/732 事件与 111,425.9/133,505.6 s 分母逐位复现，先前 Unresolved / Not Calculated 的计算缺口关闭。

条件候选 FC1/FC2 各 300 s 完成且工程无阻断，但预声明 30 s 块状态包络不含各自真实目标：模拟复现内部断面流量却处于自由流分支，真实窗口处于拥堵分支。按冻结规则停止搜索，未执行第 3 次构造与保留的 2 次独立 seed 重复，第三窗口未访问。五层合取 = Evidence Insufficient，δ/h 无独立依据，集中决策包 R1–R5。Gate 保持 `pending_simulation_sample`。

报告 `docs/STAGE_0_5_FINAL_CLOSURE_2026-10-20.md`；计划 `docs/plans/2026-10-20-stage-0-5-final-closure.md`；证据 `evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1/`。


## 2026-10-21 Stage 0.5 真实交通重建与场景重建（AAD-0.5-TR-RECON）

结果 `RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1`。只读重建两个已批准校准窗口的交通过程：识别出 5 主线车道 + 驶入匝道 + 辅助车道 + 驶出匝道，并证明已批准 D1 局域内部含第六车道（非闭合控制体）；两窗口均在拥堵分支（43.544/50.505 veh/km/lane、10.506/7.915 m/s、q=1,646.9/1,439.2 veh/h/lane）；规模最大的低速波最先出现在观测段下游端 y=500–650 m 并向上游扩张，说明拥堵由覆盖之外的下游供给带入。

运行前冻结的 3 项条件场景诊断：观测几何 + 观测需求 → 自由流（23.90 m/s / 21.05）；注入真实拥堵初始状态 → 180 s 内退化为自由流（23.81 / 21.20）；声明条件 3 车道下游供给 → 过堵（6.76 / 61.35）。三者均未落入真实目标 30 s 块包络 → `EvidenceInsufficient_StateSupport`，按预声明停止规则停止，未搜索参数、未做独立 seed 重复、未加第 4 次构造。

拥堵分支诊断：观测密度与观测净间距两条独立路径一致给出有效 Krauss 时间间隔约 1.53–1.63 s（冻结值 1.0 s），为「同一流量只在自由流支可达」的定量原因，属 Hypothesis。

第三窗口读取 0 行、holdout 0 次；Gate 保持 `pending_simulation_sample`；协议锁 / Stage 1.1 / ABCD 未启动。

报告 `docs/STAGE_0_5_TRAJECTORY_RECONSTRUCTION.md`、`docs/STAGE_0_5_SUMO_SCENE_RECONSTRUCTION.md`；计划 `docs/plans/2026-10-21-stage-0-5-trajectory-reconstruction.md`；证据 `evidence/results/RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1/`。


## 2026-10-20 Stage 0.5 文献依据的行为诊断（AAD-0.5-LIT-CAL）

结果 `RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1`。状态定义阈值敏感性（10 种定义 × 2 窗口）显示低速波方向与起始位置稳健（16/16 非饱和规则向上游、起始 y=500–650 m），但最大连通域规模在 0750 的绝对 10 m/s 定义下不可区分于逐时间片置换零模型（0.999），故规模结论收窄为依赖相对速度定义。前车轨迹重放（每窗口 12 对 × 2 配置 = 48 次微型运行）显示候选 `tau=1.6` 未改善间距响应：配对 Brockfeld 误差 +19.57 pp、间距偏差 20/20 对变大；44% 观测初始状态被 Krauss 插入包络拒绝。按预声明门控**主线 C 未执行**，RC1/RC2/RC3 保留。8 篇文献经 DOI 核验补入 Zotero。Gate 保持 `pending_simulation_sample`。

报告 `docs/STAGE_0_5_TRAFFIC_STATE_DEFINITION_SENSITIVITY.md`、`docs/STAGE_0_5_LEADER_REPLAY_BEHAVIOUR_DIAGNOSTICS.md`、`doc/literature-notes/STAGE_0_5_METHOD_EVIDENCE_MAP.md`；证据同结果 ID 目录。


## 2026-10-20 Stage 0.5 方法扩展（AAD-0.5-METHOD-EXPANSION）

结果 `RES-STAGE-0.5-METHOD-EXPANSION-V1`。覆盖与可辨识性：5,815 段 / 186,529 s，各行为阶段均存在（稳定 40%/52%、低速 9%/25%、贴近 18%/32%），H1 大部分被反驳；`tau` 与 `minGap` 效应高度相关（r=−0.94/+0.82）不可分别辨识。初始化：更正上一任务「插入被拒绝」的误判（实为延迟插入），验证两条原生路线并用控制实验证明 `insertion-checks=none` 不改变后续动力学。响应诊断：324 次独立运行（12 对 × 9 配置 × 3 共同 seed，0 失败）——`tau` 单调有害（+18.3/+40.7/+72.5 pp，三 seed 同号）、`minGap`↓与 `sigma=0` 改善、IDM(T=1.0) 最佳（−5.5 pp，增益在长期窗）、Newell 原型同量级。宏观阶段门控未开，未执行。Gate 保持 `pending_simulation_sample`。

报告 `docs/STAGE_0_5_METHOD_EXPANSION_SUMMARY.md` 等四份；文献 `doc/literature-notes/STAGE_0_5_METHOD_EVIDENCE_MAP.md`（18 条 + 方法状态矩阵）；证据同结果 ID 目录。

## 2026-10-28 Stage 0.5-R1 三臂诊断执行

R1 已按确认设计完成 B10（主线速度脉冲）、B01（匝道供给脉冲）、B11（严格组合）各一次。固定 `US-101 0750`、seed `20261201`、420 s、0.05/0.1 s、`[120,390)`、`S_UPSTREAM_MAIN`、`C_INPUT_ROUTE` 均绑定并通过独立回执。三臂源 P2 均 0，D1 暴露分别 13667.8/9865.1/13553.6 veh-s；按停止规则不追加搜索。Gate blocked，Stage0.6/StageI状态不变。报告和证据见 `docs/STAGE_0_5_R1_EXECUTION_2026-10-28.md` 与 `RES-STAGE-0.5-R1-DIAGNOSTICS-20261028`。

## 2026-10-28 Stage 0.5-R1 封存轨迹离线机制审计

结果 `RES-STAGE-0.5-OFFLINE-MECHANISM-AUDIT-20261028`：只读复核 B00/B10/B01/B11 封存状态表，完成全量事件数组、窗口 onset、源区/目标区正式 P2、事件空间、源区可观测性和 30 s 时间块审计。B10/B01/B11 全量事件段 7/1/19，窗口 onset 5/0/17；正式源/目标 P2 均 0。B10/B11 事件主要位于辅助 lane，B01 事件早于窗口。Stage 0.5 Gate 继续 blocked；无新 SUMO。
