# AAD-0.5.0｜SUMO 现实覆盖场景设计与技术可行性审计

> 审计日期：2026-10-18（Asia/Shanghai）
> 审计性质：只读技术审计与候选方案整理。本文不构成 Stage 0.5 Gate、Protocol Lock 或科学参数批准。

## 0. 范围、事实层级与执行边界

本审计从 origin/main 同步后开始。审计时 HEAD=origin/main=6ee987e。工作区已有研究者的 doc/literature-notes/ 删除改动；本任务未读取其私人笔记、未修改这些改动，也未把它们纳入本任务提交。

本任务只读取当前源码、配置、正式封存包、便携证据、AI_CONTEXT 与项目索引，未下载新数据、未访问 locked holdout、未运行 SUMO、未校准驾驶行为或风险参数、未修改 Stage 0.2/0.3/0.4 结果、未创建 Protocol Lock。报告中的“建议”“候选”均为 Proposed / Pending Researcher Decision。

本文采用以下状态词：

- Verified：源码或机器产物可直接核验；
- Agreed：研究者已经批准的范围或语义；
- Active：当前阶段仍在进行；
- Proposed：本审计提出、尚未批准；
- Unknown / Unverified：当前证据不能识别或不能外推。

事实入口与证据包括：

- 项目状态与数据流：AI_CONTEXT/00_PROJECT_STATE.md、AI_CONTEXT/02_ARCHITECTURE.md、AI_CONTEXT/03_DATA_FLOW.md、AI_CONTEXT/05_EXPERIMENTS.md、AI_CONTEXT/06_DECISIONS.md；
- 机器注册表：docs/PROJECT_REGISTRY.json；
- NGSIM 有限科学验收：docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md、code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r4/；
- pNEUMA R2 参考与 R3 关闭：docs/STAGE_0_3_BOUNDARY_REPAIR_R2_2026-10-16.md、docs/STAGE_0_3_SCIENTIFIC_ACCEPTANCE_2026-10-16.md、code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2/；
- 当前 Stage 0.5 实现：code/src/riskprop/simulation_real_coverage.py、code/scripts/prepare_stage_0_5_real_reference.py、code/scripts/run_stage_0_5_coverage.py；
- Stage 0.1 实现及工程证据：code/src/riskprop/stage_0_1_sumo.py、evidence/results/RES-STAGE-0.1-INFRASTRUCTURE-V3/stage_0_1_report.json。

## 1. Stage 0.5 目标与场景职责矩阵

Stage 0.5 的前置问题是：在没有远端风险消息作用时，SUMO 的基础运动、跟驰行为和风险测量是否落在有证据边界的现实参考范围内。它不验证风险消息能否改变远端行为，也不估计 AAD 因果效应。

| 候选现实验证线 | 当前职责事实 | 可用真实数据 | 候选 SUMO 场景 | 本审计建议的正式职责 | 状态 |
|---|---|---|---|---|---|
| NGSIM US-101 高速公路线 | Stage 0.2 已批准四源分别报告；US-101 三个 15 分钟窗口来自无表头 TXT 的 100 ms 观测链 | 3 个 US-101 state Parquet、P2 事件、测量状态和可靠暴露 | 高速公路主线；按窗口/需求密度分层，至少具备真实车道、限速、入口/出口与跟驰需求 | 作为高速公路跟驰风险主线候选；速度、加速度、净间距、闭合速度、TTC 有效资格和 P2 事件/暴露分开比较 | Proposed，依据充分 |
| NGSIM Lankershim 城市道路线 | Stage 0.2 已关闭的独立来源；当前文件是合并 CSV，官方两个源文件与物理身份仍 Unverified | Lankershim state、事件、测量状态和诊断时钟字段 | 城市道路/交叉口或走廊候选；必须重新设计真实拓扑和需求 | 作为独立城市道路跟驰风险辅助线候选；不与 US-101 合并为 iid 分布；若研究者不接受来源限制，可只作边界敏感性参考 | Proposed / Pending |
| pNEUMA Athens-d1 城市混合交通线 | 研究者已批准只承担城市速度、纵向加速度和车型组成；地图匹配、前车推断、TTC、DRAC、P2 和风险事件职责已退役 | 单文件 20181101_d1_0800_0830.csv 的 R2 标准化状态 | 城市混合交通运动学候选；车型映射和道路结构需要另行批准 | 仅作城市运动学补充，按车型/时间加权与车辆等权分别描述；不能用来建立跟驰风险或 real-real 风险阈值 | Agreed 角色，Stage 0.5 纳入方式 Proposed |

因此，两条验证线在技术上可行，但其可比对象不同：US-101/Lankershim 支持 NGSIM 跟驰风险参考，pNEUMA 支持城市混合交通运动学参考。不能把三者拼成一个“现实总体分布”。

## 2. NGSIM 跟驰风险参考审计

### 2.1 正式输入、字段与语义

当前可作为 Stage 0.5 候选输入的四个 Stage 0.2 R4 state 文件位于：

- code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states/ngsim_lankershim__complete.parquet
- code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states/ngsim_us101__0750_0805.parquet
- code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states/ngsim_us101__0805_0820.parquet
- code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states/ngsim_us101__0820_0835.parquet

四个文件均实际包含 dataset/site/window_id/vehicle_id/time_s/frame_id/speed_mps/acceleration_mps2/net_gap_m/closing_speed_mps/ttc_valid/ttc_s/drac_mps2/measurement_status/missing_reason 以及来源、诊断时钟、前车身份和连续性字段。ngsim_risk_calibration.py::standardize_ngsim_states() 和 real_trajectory.py::add_ngsim_leader_ttc() 保留原始英制字段，同时输出：

- speed_mps、acceleration_mps2：分别为 m/s、m/s²；
- net_gap_m：报告的 Space_Hdwy 减去匹配前车长度后的保险杠间距，单位 m；
- closing_speed_mps：后车速度减前车速度，正值表示闭合；
- ttc_s = net_gap_m / closing_speed_mps：只在前车唯一匹配、净间距为正且正闭合时有效；
- drac_mps2 = closing_speed_mps² / (2 * net_gap_m)：只在同一有效条件下计算；
- measurement_status：valid、not_applicable、invalid、missing 分开保留，缺失原因在 missing_reason，不以零替代；
- time_s、frame_id：Stage 0.2 正式连续性语义为相邻 100 ms 观测；100 ms 与 SUMO 0.2 s 记录不能直接等价。

正式 P2 事件表应使用：

code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/p2_formal_events.parquet

该表有 4,545 条事件，规则字段为 P2_middle，核心语义为可靠 TTC<2.0 s 且首末跨度至少 0.2 s，确认时间取实际观测帧。表内含事件身份、双车轨迹、时间边界、TTC/DRAC 极值、质量和来源字段。write_real_reference_package() 对 ngsim_event_path 只调用 pd.read_parquet()，不校验事件 schema、规则或数量；传入旧 risk_events.parquet（5,381 条候选）或迁移前 4,758 条事件不会被函数阻止。因此 0.5.1 必须由输入 manifest 固定事件文件及 SHA-256，不能仅依赖命令行路径。

### 2.2 四源事实与可比范围

以下数字来自 R4 的 state、measurement_status_by_source.csv 和 p2_event_rates_by_source.csv。事件率仅是已批准范围内“可靠、可评价跟驰观测下的代理频率”，不是事故概率。

| 来源 | state 行数 | valid | missing | invalid | not_applicable | P2 | 可靠跟驰暴露 s | P2 可评价暴露 s | 不可评价 s | P2 rate / vehicle-h |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Lankershim 合并 CSV | 1,607,319 | 483,098 | 380,820 | 75,867 | 667,534 | 2,227 | 121,885.9 | 114,328.5 | 7,557.4 | 70.1242 |
| US-101 07:50–08:05 | 1,180,598 | 464,134 | 59,381 | 1,912 | 655,171 | 543 | 111,613.3 | 111,425.9 | 187.4 | 17.5435 |
| US-101 08:05–08:20 | 1,403,095 | 605,211 | 61,958 | 1,800 | 734,126 | 732 | 133,684.3 | 133,505.6 | 178.7 | 19.7385 |
| US-101 08:20–08:35 | 1,515,240 | 658,935 | 62,583 | 1,968 | 791,754 | 1,043 | 144,859.7 | 144,662.2 | 197.5 | 25.9556 |

US-101 三个窗口是主要高速公路风险参考的最强候选：源码固定 18 列 TXT 读取契约，R4 状态共 4,098,933 行，三窗口的原始/可靠事件与核心状态回归一致。三个窗口仍应保留为来源/时间窗分层，因为需求状态和时段不同；同一站点的相邻窗口不自动提供三个独立交通环境。

Lankershim 可以支持独立城市道路风险参考，但限制必须写入任何 0.5 结果。当前合并 CSV 有 1,506 个原始 Vehicle_ID、两套诊断时钟、2,442 个可核验字段序列；官方两个独立 15 分钟源文件、官方时段标签和物理车辆身份没有被当前包证明。Lankershim 的 missing 与 invalid 比例显著高于 US-101，直接混合会把道路结构、需求、来源合并方式和可观测性差异误判为 SUMO 偏差。推荐将其独立报告，或由研究者明确批准只作辅助/敏感性线；不能切成相邻片段后伪装成多个独立 real groups。

### 2.3 NGSIM 场景比较边界

可以比较的条件是：同一交通环境内使用同一物理单位、同一指标定义、同一可靠观测资格、同一时间分辨率语义，并按来源/窗口/车型或需求层分开报告。速度、加速度和 NGSIM 跟驰字段可以分别进入对应场景的候选覆盖指标；TTC/P2 必须保留 100 ms 观测语义或使用研究者批准的重采样协议。

不能比较的内容包括：把 Lankershim 和 US-101 合并成一个 iid 参考、把 not_applicable 当作零风险、把缺失状态当作安全状态、把 P2 事件率当事故率、把 NGSIM 0.1 s 事件直接与 Stage 0.1 的 0.2 s risk 行等价、把来源时段未知推成官方标签，以及把同一车辆/轨迹的片段当独立来源。

## 3. pNEUMA 城市混合交通运动学审计

### 3.1 正式范围与事实

Stage 0.3 R3 已在有限范围关闭，逐状态输入仍应引用其父证据 R2 文件：

code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2/stage_0_5_reference_states.parquet

R2 文件实际 schema 为：

dataset, site, window_id, vehicle_id, vehicle_type, time_s, speed_mps, acceleration_mps2, quality_status, time_weighting_eligible, source_file_sha256

可核验事实为：785 条轨迹、1,239,475 条状态，时间范围 [38.40, 888.00] s；可靠时间权重状态 1,238,690 条，785 条末帧没有下一时间区间；quality_status 全部为 raw_parsed。已批准连续性为仅针对本 25 Hz 文件的 0 < Δt ≤ 0.043 s，保持原始记录顺序、身份和解析质量的 fail-closed 语义，不插值、不补帧、不跨缺口计权。

R3/R2 统计事实：

- 时间加权速度均值 4.838218 m/s，车辆等权速度均值 6.207738 m/s；
- 时间加权纵向加速度均值 -0.004410 m/s²，sd 0.745368 m/s²；
- 轨迹车型：Car 443、Motorcycle 153、Taxi 137、Medium Vehicle 30、Bus 20、Heavy Vehicle 2；
- Heavy Vehicle 只有 2 条轨迹，不能作车型级总体推断；
- 单文件是 2018-11-01 08:00–08:30 的 Athens-d1 观测，不代表雅典总体、一般城市交通或完整连续 30 分钟总体；
- 物理真实性仍 Unverified，极端运动观测原始保留并只作敏感性诊断。

### 3.2 pNEUMA 的可比较指标和边界

pNEUMA 可以承担速度、纵向加速度、车型组成和分车型运动统计。它不能提供经过批准的前车、净间距、闭合速度、TTC、DRAC、P2 或风险事件；Stage 0.5 不得恢复已退役的地图匹配、前车推断和人工风险 QA。

候选 SUMO 城市场景可以在运动学层面比较速度/加速度分布与车型组成，但必须把“单文件城市运动学参考”作为适用域标签。车型到 SUMO vType 的映射没有当前批准决定；不明确的车型不能用常见默认值代替，必须由研究者选择映射、合并或排除规则。

## 4. Stage 0.5 真实参考接口兼容性

### 4.1 已确认的字段冲突

这是一个需要记录的重大接口冲突：

| 项目 | Documented Intent | Actual Implementation | Evidence | 影响 | 状态 |
|---|---|---|---|---|---|
| pNEUMA 标准化输出接入 | AI_CONTEXT/03_DATA_FLOW.md 与 AI_CONTEXT/00_PROJECT_STATE.md 表述 stage_0_5_reference_states.parquet 可直接进入 writer | pneuma_urban_kinematics.py::build_stage_0_5_reference_states() 输出 vehicle_id、acceleration_mps2；simulation_real_coverage.py::write_real_reference_package() 第 165–177 行固定读取 id、longitudinal_accel_mps2 | R2 Parquet 的 PyArrow schema 与源码列清单 | 直接传正式 R2 Parquet 会因缺列失败；不能把现有兼容测试当成直接兼容证明 | Awaiting Researcher Decision |
| 现有接口测试为何通过 | 文档摘要写成“真实全量接口测试通过” | run_stage_0_3_pneuma_kinematics.py 第 837–849 行从原始 states 另建 raw_view，把 vehicle_id 改成 id、把纵向加速度保留为 longitudinal_accel_mps2，再调用 writer | …r2_stage05_interface_test/reference_package/audit.json 的 pNEUMA path 是临时 pneuma_reference_states.parquet，不是正式 R2 标准化文件 | 测试只证明转换后的旧 parse-view 可读；没有标准化 Parquet→writer 的端到端测试 | Verified |
| pNEUMA 车型是否进入覆盖包 | Stage 0.3 标准化状态含 vehicle_type | writer 只读取 4 个基础列和质量列，生成的 kinematics_reference.parquet 不保留 vehicle_type 或 source hash | simulation_real_coverage.py:164–177、旧/当前包 schema | 当前 Stage 0.5 包不能直接做分车型 coverage 或审计车型映射 | Verified / Design Gap |
| 质量列的契约 | R2 标准化状态同时含 quality_status 与 time_weighting_eligible | writer 只要发现任一质量列就进入分支，随后无条件访问两列；只提供其中一列的部分 schema 会 KeyError | simulation_real_coverage.py:166–204 | 需要在 0.5.1 明确 schema 全量契约和 fail-closed 行为 | Verified / Proposed Fix Pending |

因此，0.5.1 必须由研究者批准一个显式 schema 方案：要么让 writer 原生消费标准化字段并保留 vehicle_type、质量和来源指纹，要么保留一个有名字、有 schema 版本和审计记录的 adapter。当前任务不修改实现。

### 4.2 NGSIM 输入和旧包边界

writer 对 NGSIM state 的列读取与 R4 state 文件一致：dataset/site/window_id/vehicle_id/time_s/speed_mps/acceleration_mps2/net_gap_m/closing_speed_mps/measurement_status。它把 measurement_status == valid 且 gap/closing 非空的行放入 following 样本，pNEUMA 不进入 following 或 event。

code/outputs/formal/calibration/stage_0_5_real_reference_v1/ 是 2026-09-07 的迁移前 E17-A 包：pNEUMA 路径指向 e15a_pneuma_mapmatch_v2/map_matched_states.parquet，风险事件为 4,758 条，包内保留旧 map_match_status。该包只能作为历史证据，不能接回当前 Stage 0.5。prepare_stage_0_5_real_reference.py 的 CLI 目前只接收路径、行数上限和 seed，不校验 schema、来源角色、pNEUMA SHA、事件规则或 real-group 独立性；因此输入约束必须在 0.5.1 的 manifest/adapter 层 fail-closed。

## 5. 抽样与统计代表性审计

### 5.1 当前抽样实际做什么

simulation_real_coverage.py::deterministic_state_sample() 第 17–46 行按可用键 dataset/site/window_id/vehicle_id/id/time_s 计算稳定哈希，取最小的最多 5,000 行，再按哈希排序。它解决了可复现和固定上限问题，但没有实现时间权重、车辆等权或轨迹整簇抽样。

当前规则的工程含义是每个 site/window 取固定状态预算。长轨迹拥有更多抽中机会，样本会打断连续跟驰结构；样本行均值在等间隔、无缺口时近似状态/时间加权，却不等于车辆等权。following_reference 也不能用来重算正式 P2 事件率或可靠暴露，事件率和分母必须直接引用完整 R4 事件/暴露表或完整轨迹抽样后的重算结果。pNEUMA 的 0.04 s 状态、NGSIM 的 0.1 s 状态和非均匀缺口也不能在同一个无权状态池中自然等价。R2 接口测试中 pNEUMA 样本为 5,000 行、748/785 条轨迹，且有 2 条 time_weighting_eligible=false 末帧进入样本，说明“质量列被传递”不等于“抽样保持时间权重”。

哈希键不含 trajectory_id、source_member、frame_id 或 pNEUMA raw_index。当前封存四个 NGSIM state 文件的 (vehicle_id,time_s) 没有重复，但未来出现同车同时间重复时，nsmallest 的并列选择依赖输入顺序。可复现也不代表分布无偏。

### 5.2 抽样和泄漏风险

evaluate_simulation_coverage() 第 49–94 行只要求至少两个 real groups，不验证 group 是否按完整来源、车辆或轨迹独立，也不检查同一轨迹是否跨组。相邻轨迹片段、同一车辆重复切片或 Lankershim 内部诊断片段都可能被伪装成多个真实来源，使 real-real 距离偏小并降低阈值。pNEUMA 单文件不能通过切片制造 real-real 独立来源。

正式校准/验证必须先固定分区单位，再抽样或聚合。优先候选为完整 source/window/vehicle/trajectory 分区；跨组不允许共享同一车辆或轨迹。若没有至少两个有证据的独立真实组，real-real 阈值只能作为描述性诊断，不能作为正式验收上界。

### 5.3 可选方案

| 方案 | 统计口径 | 优点 | 代价与风险 | 本审计建议 |
|---|---|---|---|---|
| A：完整状态主统计 + 有界哈希预览 | 用全量可靠时间区间计算时间加权；车辆等权作为并列摘要；哈希样本仅用于受限距离计算 | 最接近 Stage 0.2/0.3 已批准语义，保留连续性和质量 | Energy Distance 计算成本更高；需要明确大表不可移植的处理 | Proposed / 推荐 |
| B：轨迹簇哈希 | 按完整 vehicle/trajectory 选入，保留轨迹内连续片段 | 降低同一轨迹泄漏，保留事件和跟驰结构 | 车辆/时间权重改变，需要 inclusion weight 或重新解释 | 作为风险事件与连续跟驰敏感性对照 |
| C：来源×车型×速度分层状态抽样 | 每层固定预算，抽样后用后分层权重 | 支持车型/速度 strata 覆盖检查 | 打断轨迹，少数车型小样本不稳定；需先批准 strata | 仅作覆盖诊断，不替代主统计 |

推荐组合为 A 主统计、B 连续性/风险敏感性、C 运动学支持度诊断；研究者仍需决定正式报告采用时间加权、车辆等权或组合口径。

## 6. Stage 0.1 SUMO 工程能力与缺口

### 6.1 当前网络和需求事实

当前源码 stage_0_1_sumo.py 第 149–200 行生成最小双走廊：

- src 与 tgt 两条物理不连通的单车道走廊，坐标 y=0 与 y=50；
- 每条走廊为 100 m + 300 m + 100 m，edge speed=20 m/s；
- 只有一个 passenger vType：accel=2.0、decel=4.5、sigma=0、length=5、minGap=2、maxSpeed=20；
- 每次运行只有 source_0、target_leader、target_0 三辆车，固定 route、depart=0、departPos=20/75/35、departSpeed=10；
- 四格由 source_present/channel_enabled 组成，事件时刻 2.0 s，仿真窗口 0–32 s，步长 0.2 s。

封存工程证据 RES-STAGE-0.1-INFRASTRUCTURE-V3 显示四格前处理等价、运行隔离、时钟和生命周期通过，但 physical_path_audit.status=disconnected_topology、reachable=false，且 scientific_claim_eligible=false。注册表将 Stage 0.1 标为 verified_engineering_only；该封存包的历史 schema/experiment id 与当前 stage_0_1 源码已迁移，不能当作当前代码重新运行结果。

### 6.2 输出能做什么、不能做什么

TraCI 循环第 242–303 行可记录每个活跃车辆的 speed_mps、acceleration_mps2、edge_id、lane_id、位置、leader_id、net_gap_m 和 relative_speed_mps，并封存 state/emission/protocol/action/risk/clock/lifecycle 表。它具备复用价值：逐步采样、seed、provenance、manifest、四格隔离和独立重算链。

当前输出没有 vehicle_type、measurement_status/missing_reason、正式 ttc_valid/P2 字段，也没有真实需求、多密度、长时间稳态窗口。只有 target_0 写 action/risk；risk 表的 ttc_burden_validation 明确是 stage_0_1_validation，attributable=false，不能进入 Stage 0.5 正式 P2。

存在一个必须在 0.5.3/0.5.4 处理的符号差异：SUMO 当前 relative_speed_mps = leader_speed - follower_speed；NGSIM 的 closing_speed_mps = follower_speed - leader_speed = -relative_speed_mps。源码的 Stage 0.1 validation risk 行直接以 rel > 0 计算 gap/rel，这不是批准的 NGSIM closing/TTC 语义。一个历史 s1c1 例子中前车更快、gap 增大而 relative_speed_mps 为正，直接得到有限 validation TTC；这进一步说明 risk 行仅供工程验证。

### 6.3 复用能力和最小缺口

| 能力 | 可复用判断 | 进入现实覆盖前的最小条件 |
|---|---|---|
| TraCI、seed、封存、状态/时钟/lifecycle | Verified 工程能力 | 保留版本哈希、运行日志和不可覆盖输出 |
| 网络拓扑 | 仅双走廊 fixture | 为高速公路与城市道路分别提供真实可解释的车道、连接、限速和路段标签 |
| 需求与密度 | 当前固定 3 车 | 由研究者批准需求/密度 strata、暖机和稳态评价窗口 |
| 车型与行为 | 单一 passenger vType | 先批准真实车型到 vType 的映射，再固定 vType 与行为参数类别 |
| 运动学输出 | 有速度、加速度、前车、间距、相对速 | 全车记录、vType、统一 closing sign、质量/缺失字段及来源标签 |
| TTC/P2 | 当前只有 validation risk | 按批准 P2 规则以 0.1 s 输出或批准的观测聚合语义计算，保留 valid/not_applicable/invalid/missing |
| 场景时长 | 32 s、0.2 s | 长于暖机的重复需求窗口；0.2 s 只能作运动学覆盖，不能自动等价于 NGSIM 0.1 s 风险参考 |

最小候选结构是三个明确隔离的场景配置：US-101-compatible 高速公路、Lankershim-compatible 城市跟驰、pNEUMA-compatible 城市混合运动学。这里的 compatible 仅表示待设计的适用域标签，不表示当前已有网络或校准结果。当前双走廊不得直接改称现实传播网络。

## 7. 现实覆盖方法审计

### 7.1 当前实现事实

evaluate_simulation_coverage() 的流程是：

1. 要求至少两个 real groups；
2. 把所有 real groups 合并，使用 fit_robust_scaler() 以 pooled real 的 median/IQR 标准化；
3. 对所有 real group 两两计算 Energy Distance；
4. 用 real_real_quantile（默认 0.95、method="higher"）作为 sim-real 距离上界；
5. 将 simulation 与 pooled reference 计算一次距离；
6. 将 stratum 仅按类别集合交集计算 len(supported)/len(real_strata)，默认 minimum_stratum_coverage=0.90。

fit_robust_scaler() 第 361–378 行的 IQR 为零时回退到 1；energy_distance() 第 380–409 行使用每组实际行数的均值距离，_mean_pairwise_distance() 包含自身对角线，是 V-statistic 形式。当前函数没有按场景、车型、密度或时间加权，也没有 cluster bootstrap、组独立性检查或校准/验证分离。run_stage_0_5_coverage.py 仅以 path.stem 作为 real group 名称，也没有记录源文件 SHA 或检查重复 group。NGSIM following 字段与 pNEUMA 运动学字段不能放入同一 pooled Energy Distance：pNEUMA 没有已批准的跟驰字段，缺失值也不满足 energy_distance 的有限值契约。

### 7.2 对正式验收的判断

现有方法适合做工程诊断和候选距离记录，不足以直接宣布 Stage 0.5 科学通过，原因有四类：

1. 场景混杂：3 个 US-101 窗口和 1 个 Lankershim 若直接放在同一 real group 集合中，地点、道路结构、需求和观测质量差异都会进入 real-real 阈值；
2. 独立性不可识别：函数不检查同车/同轨迹跨组，Lankershim 的合并文件不能通过相邻切片制造独立来源，pNEUMA 单文件也没有第二个真实组；
3. 抽样和相关性：5000 行上限与轨迹长度、采样频率、缺口和车型组成有关；Energy Distance 没有轨迹簇权重或样本量敏感性；
4. stratum 覆盖过弱：类别存在即算支持，不看每层样本量、暴露时长、分布或置信范围；simulation 中额外且 real 未见的类别不会被惩罚；0.90/0.95 只是函数默认值，不是已批准科学阈值。

### 7.3 最小化改进候选

不新增评价框架的前提下，建议仅做以下最小收口，均需研究者批准：

- 将 coverage 调用拆成 highway-US101、urban-Lankershim、urban-pNEUMA-kinematics 三个场景域；每个域内明示可用指标；
- 在输入 manifest 中记录 real group 的完整 source/window/vehicle/trajectory 身份，拒绝同一身份跨组；
- 对每个场景分别报告 pooled reference 距离、来源内 real-real 距离、车型/速度 strata 支持和时间/车辆权重；
- 保留当前 Energy Distance 作为描述性距离，同时做轨迹簇/样本量敏感性；不要把 V-statistic 阈值自动解释为科学容差；
- 用独立的校准组和验证组；如果只有一个 pNEUMA 文件或没有独立 Lankershim 组，则标记 incomparable / evidence insufficient，不伪造 real-real 阈值；
- 将 0.90、0.95 作为候选实现参数保留在报告中，直到研究者给出场景内、预注册或外部依据。

## 8. Stage 0.5 后续执行方案（候选）

下表是 0.5.1–0.5.5 的执行计划，不代表这些任务已经完成。

| 任务 | 输入 | 要解决的问题/候选假设 | 工作内容 | 输出 | 成功、失败或阻断 | 需研究者批准 |
|---|---|---|---|---|---|---|
| 0.5.1 真实参考重建 | R4 四个 NGSIM state；R4 p2_formal_events.parquet；R2 pNEUMA 标准化 Parquet 及 SHA | 正式输入能否按新职责、质量和 schema 复现 | 修复或显式登记 pNEUMA adapter；固定 NGSIM/P2/pNEUMA manifest；保留 source/site/window/vehicle/type/quality；比较完整状态、时间加权、车辆等权和轨迹簇候选 | 新 schema、输入清单、质量审计、抽样/权重对照、不可覆盖参考包 | 缺列、旧 map-match、事件规则/数量不符、来源指纹缺失则阻断；不得回接旧 E17-A | schema 方案、抽样/权重主口径、是否纳入 Lankershim |
| 0.5.2 指标与验收协议 | 0.5.1 参考包；场景职责矩阵；候选 real group 分区 | 如何避免环境差异被误解释为 SUMO 偏差 | 预先分 highway/urban-risk/urban-kinematics；确定每场景字段、单位、质量资格、权重、ED/分层摘要和校准/验证隔离；为容差与样本量准备依据 | 候选协议、场景化指标表、独立性审计、候选阈值依据与 incomparable 规则 | 无独立组、无法定义质量资格或只能用默认阈值则证据不足；不写 Gate pass | 场景内统计口径、阈值原则、real-real 是否仅诊断 |
| 0.5.3 SUMO 无消息基线 | 0.5.2 候选协议；真实道路/需求设计；已批准 vType 映射 | SUMO 基础运动和跟驰是否能产生可比较观测 | 设计最小高速/城市网络、需求 strata、车型、暖机/评价窗口、采样步长和全车状态契约；实现 closing sign、TTC/P2 质量字段 | 版本化网络/route/config、无消息状态与事件输出、运行 audit/provenance | 网络物理结构或输出语义不匹配、0.1/0.2 不可解释、需求未覆盖目标 strata 时阻断 | 网络与需求范围、采样时间语义、vType 映射 |
| 0.5.4 SUMO 校准与偏差诊断 | 校准 real groups、无消息 SUMO 样本、0.5.2 指标 | 哪些偏差来自网络/需求，哪些来自行为参数 | 仅在批准类别内调节跟驰模型参数、期望速度/时距、加减速度、反应时间、车型比例或需求；使用校准/验证隔离、固定候选集合、盲化/版本化记录和敏感性 | 参数候选表、校准日志、sim-real/real-real 分层诊断、未解决偏差清单 | 反复查看验证集、按结果挑参数、跨场景借用阈值或改变风险定义则阻断 | 可调参数类别、边界、调参次数/预算、选择规则 |
| 0.5.5 独立验证与科学验收 | 冻结参数/网络、独立验证来源或不重叠车辆/窗口、完整 provenance | 覆盖结论能否在未参与调参的数据上复现 | 运行独立验证；分场景报告通过/失败/不可比较；核对时间步、字段、质量、车型、strata、ED 和事件/暴露；封存版本与 Gate 证据 | 验证包、场景适用域、失败/阻断记录、Gate 候选矩阵 | 验证与校准泄漏、来源不足、指标不可比较或质量失效则不通过/阻断；不得访问 locked holdout | 独立性定义、各场景验收条件、有限范围 Gate 与版本封存规则 |

## 9. 研究者必须批准的科学决策清单

### 9.1 场景职责

- 当前事实：Stage 0.2 四源分别报告；US-101 三窗口高速风险参考证据最完整；Lankershim 是独立合并 CSV 且 source_period=unknown；pNEUMA 仅城市运动学，R3 已关闭有限单文件范围。
- 可执行方案：US-101 作为高速主线；Lankershim 独立城市风险辅助线；pNEUMA 作为城市混合运动学补充，三者不合并 iid。
- 主要替代方案：只正式纳入 US-101 风险线，把 Lankershim 与 pNEUMA 降为边界敏感性。
- 优缺点与风险：三线能覆盖更多适用域，但来源异质和接口/车型工作量更大；只用 US-101 更干净，却不能为城市道路或混合交通运动学提供正式覆盖证据。
- 推荐：批准“US-101 主线 + Lankershim 独立辅助 + pNEUMA 运动学补充”的职责分离；是否把 Lankershim 计入正式验收需单独批准。
- 未批准前禁止：合并来源、把 Lankershim 标为高速公路、恢复 pNEUMA 风险职责。

### 9.2 车型映射

- 当前事实：pNEUMA 有六类车型，Heavy Vehicle 只有 2 条轨迹；当前 SUMO 只有 passenger vType；NGSIM state 未形成可直接消费的车型字段。
- 可执行方案：先按研究者批准的粒度建立显式映射表，每个真实类别绑定 vType、长度/动力学字段和未映射处理规则，未知类别保留 unmapped 并从正式车型结论中排除或单列。
- 主要替代方案：只映射 Car/Taxi/Motorcycle，其他类别合并到受限的重型/中型组；或不做车型级验收，仅做总体运动学。
- 优缺点与风险：显式多 vType 保留混合交通解释，但参数更多；合并类别可运行但掩盖重型车差异；不做车型级验收最保守，却削弱 pNEUMA 的主要价值。
- 推荐：先批准映射表和未知处理，再实现；Heavy Vehicle 不作独立科学结论。
- 未批准前禁止：用 SUMO 默认 passenger 代表所有车型、把未映射类别静默改名、把车型比例差异解释成行为偏差。

### 9.3 抽样与统计权重

- 当前事实：稳定哈希逐状态取最多 5,000 行，可复现但没有时间或车辆权重；R2 已携带 time_weighting_eligible，writer 的 bounded sample 仍无权。
- 可执行方案：全量可靠区间作为时间加权主统计，车辆等权作为并列摘要，轨迹簇抽样作为连续性敏感性；哈希样本只作为有界工程距离上限并记录其权重局限。
- 主要替代方案：只做轨迹簇哈希，或只做来源×车型×速度分层状态抽样。
- 优缺点与风险：组合报告最透明但成本高；轨迹簇保留连续性但权重改变；分层状态抽样支持 strata 但打断轨迹并需后分层权重。
- 推荐：采用组合报告候选 A+B+C，待研究者指定主统计口径。
- 未批准前禁止：把哈希可复现写成无偏、把每行等权写成车辆等权、用同一轨迹片段构造 real-real 独立组。

### 9.4 时间分辨率与风险测量可比性

- 当前事实：NGSIM 正式风险参考为 100 ms；Stage 0.1 SUMO 为 0.2 s；Stage 0.1 risk 不是 formal P2，且 relative_speed 与 NGSIM closing_speed 反号。
- 可执行方案：运动学指标单独允许 0.2 s，但正式 TTC/P2 输出采用 0.1 s 或研究者批准的观测聚合协议；统一 closing sign、质量状态和不插值/不补零语义。
- 主要替代方案：全部 SUMO 保持 0.2 s，只做运动学覆盖，风险线标记 incomparable；或在 0.2 s 上另建独立风险参考并不与 NGSIM P2 直接比。
- 优缺点与风险：0.1 s 输出成本较高但语义最清楚；只做运动学可快速推进但不能支持风险覆盖；另建 0.2 s 规则会增加科学分叉。
- 推荐：风险指标优先采用 0.1 s 或明确批准的聚合语义，0.2 s 仅作为运动学候选。
- 未批准前禁止：把 Stage 0.1 validation risk 当 P2、直接使用反号相对速度、宣称 0.1/0.2 等价。

### 9.5 覆盖标准与校准/验证隔离

- 当前事实：minimum_stratum_coverage=0.90 和 real_real_quantile=0.95 只是函数默认值；当前方法不检查 real group 独立性，也没有验证集隔离。
- 可执行方案：按场景预注册指标和容差依据，校准与独立验证按完整 source/window/vehicle/trajectory 分区；每场景分别报告 Energy Distance、strata 支持、权重摘要和 incomparable。
- 主要替代方案：保留默认 0.90/0.95 作为工程诊断，科学验收只做定性/描述性判断；或依据外部文献/预注册误差预算给出场景内阈值。
- 优缺点与风险：场景内阈值更可解释但需要足够独立来源；仅诊断不够形成正式 Gate；外部阈值若与数据/指标不匹配会造成伪精确。
- 推荐：先完成独立组与指标协议，再由研究者批准阈值；默认值不得写入科学 Gate。
- 未批准前禁止：为了满足函数要求伪造 real groups、把 pooled real-real 上界当普遍容差、用验证样本反复调参。

## 10. 面向研究者的直接回答

1. **两条现实验证线是否可行？** 可行，但职责必须分开。US-101 三窗口最适合作为高速公路跟驰风险主线；Lankershim 应是独立城市道路风险参考/辅助线，是否正式纳入取决于研究者是否接受合并 CSV、unknown 时段和较高不可评价比例；pNEUMA 仅作为城市混合交通速度、纵向加速度和车型组成补充。
2. **真实参考能否直接接入？** NGSIM R4 state 字段与 writer 的 NGSIM读取列兼容，正式 P2 事件应固定为 final closure 的 4,545 条表；pNEUMA R2 标准化文件不能直接传给当前 writer，存在 vehicle_id/acceleration_mps2 对 id/longitudinal_accel_mps2 的接口冲突。现有通过测试实际走临时旧字段视图；旧 Stage 0.5 包还引用退役 map-match 产物。质量列虽已在适配路径传递，但当前 bounded sample 仍无权，车型字段也被丢弃。
3. **当前 SUMO 能复用什么、缺什么？** 可复用 TraCI 步进、seed、四格隔离、state/emission/protocol/action/risk/clock/lifecycle 封存、provenance 和独立审计。缺真实道路拓扑、需求/密度、长时窗口、多车型、多 vType、全车质量字段、统一 closing/TTC/P2 语义和 0.1 s 风险可比输出；双走廊物理断开，不能当未来传播网络。
4. **Energy Distance 与覆盖方法适合正式验收吗？** 目前只适合作为工程/描述性候选。real groups 独立性、场景混杂、轨迹相关性、V-statistic 小样本效应、pooled scaler、集合式 strata coverage 和默认 0.90/0.95 都不足以直接形成正式科学 Gate。
5. **建议优先采用哪些场景、指标和统计口径？** 优先 US-101 场景内按窗口分层比较速度、加速度、净间距、闭合速度、TTC 有效资格和 P2/暴露；Lankershim 独立报告并作城市敏感性；pNEUMA 只比较速度、纵向加速度、车型组成。主统计候选为全量可靠时间加权，车辆等权并列，轨迹簇与分层状态作为敏感性，hash 只作有界工程样本。
6. **研究者现在必须决定什么？** 决定五项：US-101/Lankershim/pNEUMA 的正式职责；真实车型到 SUMO vType 的映射和未知处理；时间加权/车辆等权/分层或组合报告；SUMO 0.1 s 风险测量与 0.2 s 运动学的可比协议；场景内覆盖容差、real-real 参照和校准/独立验证隔离。
7. **推荐的下一项 Codex 任务是什么？** 在研究者批准上述五项后，执行 0.5.1“真实参考重建”：先解决标准化 pNEUMA schema 与 writer 的显式 adapter/原生契约，固定 R4 state、4,545 P2 事件和 R2 pNEUMA 的 manifest/SHA，输出时间加权/车辆等权/轨迹簇候选的只读审计包；不先运行 SUMO 或调参。

## 11. 审计结论与上下文一致性

本报告确认 Stage 0.5 仍为 Active / pending_simulation_sample，没有新的科学 Gate、协议锁或实验完成结论。当前最重要的工程阻断是 pNEUMA 正式标准化 schema 与 writer 的直接接口不兼容；当前最重要的科研阻断是场景职责、车型映射、抽样权重、时间分辨率和覆盖阈值尚未批准。

本报告与当前源码/封存产物一致；候选方案不写入 AI_CONTEXT/06_DECISIONS.md。必要的索引与已知问题更新只记录“审计完成”“接口冲突待决”和下一步 0.5.1，不把规划任务写成实验完成。
