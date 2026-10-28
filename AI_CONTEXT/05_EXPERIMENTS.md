## Current — 2026-10-28 Round2 Task1

Verified: the approved minGap candidate was statically bound but not scientifically launched. A current-source synthetic smoke passed in the existing Linux capsule; it used synthetic inputs only and is engineering evidence. Candidate SUMO/TraCI starts are 0, so no candidate trajectory, C6/D1 result or formal P2 exists. The launch is blocked by the existing admission contract's lack of a strict vType-only minGap factor. See `docs/STAGE_0_5_ROUND2_TASK1_EXECUTION.md` and `evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/`.

# AAD Experiments

## Current — 2026-10-28 first-round evidence-consistency repair

Verified: R1 is executed and sealed; the earlier R0 “R1未执行” sentence is historical design-stage wording. The repair recomputed event and formal-measurement summaries from source evidence, corrected B11 auxiliary counts to 16/19 full and 16/17 window, and saved the no-launch regression log and failure inventory.

## Historical — 2026-10-28 R0 offline design packet（任务标签；实际准备2026-10-27起）

R0为离线设计产物，不是新实验轨迹。A03仍为唯一accepted B00；A01/A02资源覆盖失败与更早原生失败保留。源区域分开审计、三臂差异可追踪；R1仍未执行，本轮SUMO0。 证据：evidence/results/RES-STAGE-0.5-R0-DESIGN-PACKET-20261028/；审查报告：docs/plans/2026-10-28-stage-0-5-r0-design-freeze.md。

## 2026-10-27 Weekly B00 accepted; Stage I remains BLOCKED

Verified: A03 completed420s/8400native steps, independent receipt and all8 measurement checks Pass; B00_EXECUTED_MEASUREMENT_ACCEPTED. This task had3 real B00 starts: A01/A02 resource-coverage failures retained; A03 sealed trajectory independently remeasured with zero new launches after a coordinator import fix.1150declared=1005inserted+145native pending;857arrived/148active; collision/teleport/discard0 with complete required observation.18/18state/D1 support, E=9778.4veh-s, localP2=0. Final isolated software:1386passed/17skipped/7native excluded; audit denied0/SUMO0; compileall/docs/hash Pass. Scientific interaction Gate blocked; numerical budget/protocol candidate are Proposed, StageI BLOCKED. Historical Not Accepted unchanged. Evidence: docs/AAD_WEEK_TO_STAGE_I_2026-10-27.md; evidence/results/RES-AAD-WEEK-20261027-V1/; evidence/results/RES-STAGE-0.6-WEEK-20261027-V1/. Older blocks below retain their historical time points.

Three task B00 trajectories used seed20261201 and independent exact bindings; these deterministic repeats are not independent treatment pairs. No StageI confirmatory run or new treatment arm executed.

## 2026-10-27 B00已真实启动：BLOCKED_BY_VERIFIED_HARD_FAILURE

Verified：ENG-01/02/03修复、无数据全量1361通过/16跳过/7原生排除、compileall、修复后3s原生集成及独立回执Pass；纯Git定向165通过。新candidate-v8及聊天来源授权、实时硬检查完成后已直接执行一次B00（版本/仿真/真实TraCI各1）。最终状态BLOCKED_BY_VERIFIED_HARD_FAILURE：首个simulationStep发生i0007_i0007 slow lane ahead原生Error；冻结输入为15.23m/s、位置233.91m，下游main_2限速10m/s，按既定停止规则终止，420s未完成。仅t=0初始身份快照有效，末态插入/pending/discarded及全程碰撞/teleport均Unknown；三XML截断，18格测量不验收。capsule退出1，SUMO退出码未成功观测；后代已清理且无残留PID。未重复相同失败。具体初态/下游限速/原生Error停止规则冲突需科研决定，不能伪装成工程修复。旧Not Accepted及Gate不变。依据：docs/STAGE_0_5_B00_CLOSURE_2026-10-27.md；evidence/results/RES-STAGE-0.5-B00-NATIVE-V1/。下方为历史时点。

## 2026-10-27 B00科研准入审查V1（审查产物，不是实验）

新增研究者决策包，15项问题/9项需明确决定。静态复算1150=117初态+1033非初态，DS38仅38速度10→max，i0007仍15.23；network原字节相同、sumocfg只增TripInfo三项。现有18参考单元与正式C6/D1调用已核验，但新B00实际插入、逐车生命周期、完整支持与科学效应均未观察。A窗残留/另版B窗、初始化/输入保真/测量合同及有限可识别目标仍待研究者。账本仅task_created，无预约；本轮0原生启动/0真实TraCI/0新科研轨迹，不重跑SMOKE、不重测历史轨迹，不改科学政策或Gate。依据：docs/STAGE_0_5_B00_SCIENTIFIC_ADMISSION_REVIEW_V1_2026-10-27.md；docs/audits/stage_0_5_scientific_admission_review_v1/review_matrix.json。下方为历史时点。

## 2026-10-27 B00 candidate-v6 工程准入（Verified / 待研究者审批）

新增不可覆盖 candidate-v6，独立复核347份封存文件、原生产 verify_receipt Pass、12源闭包/8031运行时文件及B00输入/支持/18测量参考/资源策略精确绑定。静态预检仅保留实时检查要求；当前无SUMO的完整Linux技术预检 technical_errors=[]、ready=true、READY_FOR_RESEARCHER_APPROVAL。proposal SHA=b43e2d3af03dd53dd23bee3abd027725f298f58c97a2ae73d868ca9168a229b3。工程证书的accepted仅表示静态输入/资源资格与工程链，不证明B00实际插入、测量支持或科学效应。科研execution_allowed/researcher_confirmed/protocol_frozen及profile accepted_for_new_task仍false，native_launch_locked=true，旧B00 policy accepted_build=false硬锁保留；没有科研授权迁移。candidate-v5/历史失败/SMOKE归档原字节保留，历史Not Accepted、Gate/δ/h/B/Stage1.1不变。本任务SUMO0/真实TraCI0/新B00轨迹0。依据：docs/STAGE_0_5_B00_ADMISSION_V6_2026-10-27.md；docs/audits/stage_0_5_ready_to_admit_v3/candidate-v6/；evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/technical_preflight.json。下方为历史时点。

## 2026-10-26 V4 smoke 3工程Pass

精确SMOKE_V4_20261026_3实际launch1，SUMO版本1/合成仿真1/真实TraCI1，60步/3s/seed1，调度回读及输出/回执/隔离/资源/清理全验收，无重试。辅助修复180项离线回归通过，旧预检失败保留。仅合成工程验证，B00科研运行0、candidate-v5四false与科研Gate不变。依据：`docs/STAGE_0_5_V4_SMOKE_3_CONTINUATION_2026-10-26.md`；下方为历史时点。

## 2026-10-26 SMOKE_V4_20261026_3未启动

获精确条件授权后，新纯Git135项通过；预检辅助脚本读取WSL未提供的可选sysctl时报错，实时资源/隔离验收未完成，PRELAUNCH BLOCKED。未生成授权envelope，launch/版本进程/仿真/真实TraCI/步数/新科研轨迹均0，无重试。原3s合成定义与B00/candidate-v5四false不改。依据：`docs/STAGE_0_5_V4_SMOKE_3_2026-10-26.md`；下方为历史时点。

## 2026-10-26 V4 r5合成准备，未执行smoke

`SMOKE_V4_20261026_3`：3s/0.05s/seed1/单合成车，新proposal与false envelope已准备；授权不得继承_2。新六组无害Python隔离探针14判据成立；仅准备Linux1.26/TraCI22完整运行时和精确策略。本轮SUMO0、真实TraCI0、新科研轨迹0。candidate-v5原B00 run ID/seed20261201/420s/[120,390)及全部科研定义不变，只重绑Linux环境，仍工程阻断。依据：`docs/STAGE_0_5_V4_PREPARATION_2026-10-26.md`；旧实验保持历史。

## 2026-10-26 V3候选输入，不是实验

0750 B00/S10/R01/SR11分别准备精确routes，均1150辆/117初态/60非初态entering；R两臂只按既有60s块规则改60辆depart，DS38与另外79初态不变。B00首个建议ID为V3_0750_B00_DS38_s20261201，420s/[120,390)，Proposed。i0007仍有旧错误未解决，错误早停不得复用为合格B00。0805未准备新输入。无新SUMO/TraCI/轨迹、无C6重测，V3真实账本0，累计预算无限；旧实验不重复执行。

依据：`evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/`；`docs/plans/2026-10-26-stage-0-5-ready-to-admit-v3.md`。

## 2026-10-25 V2历史C6精确复核（最新）

新增6份旧FCD当前C6重测：两窗口B_het四车道各1、U/E到达时序各2窗口，均seed20261201；独立几何/事件成员/D1复核通过。旧[300,420)结构N33/32→14/10、E5882.8/5433.6；时序N1/2/1/2→0/0/0/0，E均正但支持缺失保留。另列[120,390)非事后选优，不能混读；既有该窗口两基线N0/E9754.8和N0/E10456.7复用。不是新实验/seed重复，不追认全部旧P2。新轨迹0，真实V2账本0，四臂仍Proposed。

依据：`evidence/results/RES-STAGE-0.5-V2-ADMISSION-ENGINEERING-V1/C6_comparison.json`；`docs/STAGE_0_5_V2_ADMISSION_ENGINEERING_2026-10-25.md`。下方“仅两份”描述为历史时点。

## 2026-10-25 V2审计与候选矩阵

旧324=12对×9配置×3seed；另24初始化和24非SUMO原型。58=30grid+20seed+4结构+4历史第三窗（本轮只读聚合），grid/seed有4个相同cell/seed键，非额外独立seed。20=2窗×U/E×5seed。当前新任务0次、无累计上限；每窗B00/S10/R01/SR11的首个seed块共8个候选，不是已批准预算或已执行实验。旧风险事件未整体C6复核，历史噪声仅规划尺度。

依据：`docs/STAGE_0_5_RESEARCH_V2_AUDIT_2026-10-25.md`；`docs/STAGE_0_5_RESEARCH_V2_BUDGET.md`；`docs/plans/2026-10-25-stage-0-5-interaction-research-v2.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-RESEARCH-V2/`。以下内容保留其历史时点。


## 2026-10-25 DS10MAX-V1 离线准备

独立ID1_SUPPLY_0750_DS10MAX_V1与ID3_RAMP_0750_DS10MAX_V1，候选累计第2/3次，未执行；ID2暂缓。既有两校准基线与首次失败FCD仅用于初始化时序审计，不重算P2或重选支持。seed20261201/420s/elapsed[120,390)与原分块保持；预算仍已用1/3。

依据：`docs/STAGE_0_5_DEPART_SPEED_CANDIDATE_2026-10-25.md`；`docs/plans/2026-10-25-stage-0-5-depart-speed-candidate-v1.md`；`evidence/results/RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1/`。以下原内容保留。


## 2026-10-25 政策A执行停止事实

RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1：1次失败/3次上限，ID1原始FCD至179.9s、getter180s；P2部分N=0/E=1933.0veh-s，非完整窗风险率。局部初态t120为1、全网在场初态2、局部106条/10.6veh-s；pending初态身份Unknown。ID2/ID3停止未执行。

依据：`docs/STAGE_0_5_INTERACTION_DIAGNOSTICS_POLICY_A_EXECUTION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/`。以下旧状态保留为历史时点。

## 2026-10-25 POLICY-A-VALIDATION-SCOPE-01（当前执行阻断）

补充全量回归误在主工作区运行，13项本地历史/原始数据测试变为可执行。998 passed的该次记录不计为有效隔离验证；任务级零验证资源访问不可认证、数据隔离不Accepted，Status: Awaiting Researcher Decision。源码审计详见 `docs/STAGE_0_5_POLICY_A_VALIDATION.md` 与便携 `validation_scope_incident.json`，不重读相关数据。先前独立纯Git回归985 passed保留其有限效力；最终源码在无数据Git克隆另获987 passed / 14 skipped / 7 deselected，定向9项及compileall通过，仍不能逆转隔离偏差。政策A仍Agreed；最终计划Proposed，新轨迹0/3，Gate不变。工程准备不能代替研究者对偏差及运行资格的裁决；未决前不按有效完成任务提交/推送。


## 2026-10-25 政策A与最终计划预检

RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1：政策A共同支持和输入/资源预检。三份独立配置准备完成，ID3仅60辆非初态匝道depart改变。实际插入、输入保真及新运行自身初始化状态尚Unknown；三次全部not_attempted，计划未冻结。

依据：`docs/plans/2026-10-25-stage-0-5-interaction-diagnostics-policy-a-final.md`；`evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1/`。


## 2026-10-25 C6/C7 offline phase

新增RES-STAGE-0.5-C6-C7-OFFLINE-V1，仅离线工程证据。0750 N/E 7/10904.0→0/9754.8；0805 5/11633.0→0/10456.7，资格支持改变，不能推出零风险。初始化共同候选起点180s仅Proposed；A仍可选。

依据：`docs/STAGE_0_5_C6_C7_OFFLINE_DECISION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-C6-C7-OFFLINE-V1/`。


## 2026-10-25 Interaction diagnostics preflight

AAD-0.5-INTERACTION-DIAGNOSTICS-V1: researcher authorized reallocation of3 historical remaining attempts. Actual new trajectories0; all3 draft roles not_attempted. Offline preflight only; no formal result registration. Initialization and physical measurement conflicts prevent freeze/execution. Two historical D1 pairs at[120,390):0750 N7/E10904.0;0805 N5/E11633.0; not physically corrected reference results.

Evidence: `docs/STAGE_0_5_INTERACTION_DIAGNOSTICS_2026-10-25.md`; `docs/audits/stage_0_5_interaction_preflight_v1/preflight.json`; `execution_ledger.json` in the same directory.


> 这里只记录客观状态。完整字段以 `docs/PROJECT_REGISTRY.json` 为准，原始数字以 audit/manifest/表为准。

## 最近一次 Stage 0.5 实验（2026-10-21，AAD-0.5-ARRIVAL-TIMING）

`RES-STAGE-0.5-ARRIVAL-TIMING-V1`。变量：到达时刻（U = 同批事件按流均匀化；E = 真实重建时刻），其余全部冻结（`B_het`、`vlim=10 m/s`、`[150,350)×1–5`、420 s、0.05/0.1 s、`[300,420)`、真实初始状态、网络与行为参数）。规模 20 次（2 窗口 × 2 臂 × 5 配对 seed 20261201–05）。主要指标：状态域成员、速度离散、净拉开份额、闭合速度包络覆盖、局部 P2 率、相对速度异常档位与互相关传播、**实现到达保真度**。客观结果：主线到达结构不可施加（实现 CV 比 1.01/1.08）、匝道可施加（221.9/186.5）；速度离散朝真实上升（5/5 两窗口），净拉开份额反向、P2 两窗口相反、波结构未恢复；20/20 工程干净、状态支持 20/20。状态 `closed_arrival_timing_partially_supported_mainline_not_imposable`。输出 `code/outputs/formal/calibration/stage_0_5_boundary_timing_v1/`。

## 最近一次 Stage 0.5 实验（2026-10-21）

`RES-STAGE-0.5-STATE-SUPPORT-V1`（AAD-0.5-CLOSURE）。条件 / 变量：观测几何网络；初始状态=观测真实初始状态；边界需求=观测穿越需求（8,345/7,227 veh/h）+ 匝道；**声明的下游供给**（`main_2` 自由速度 27.78/15/12/10/8 m/s，或 4 车道缩减）；行为臂 `B_frozen`（tau=1.0）/`B_mean`（tau=1.5662）/`B_het`（每车 tau 取自真实每车分布分位）。评价窗 `[300.0,420.0)` s，内部 0.05 s，记录 0.1 s，SUMO 1.26.0。规模 58 次：网格 30 + 独立 seed 20 + 结构变体 4 + 留出窗口 4。主要指标：局部 30 s 块 (k, v)、速度离散、低速份额、闭合速度均值/净拉开份额、`tau_eff`、局部 P2 率、状态域成员（含数据派生跨窗口基线）。客观结果：状态层在两窗口与留出窗口成立；交互相容不成立（P2 率 0.9–1.5 对 17.0/23.5）。状态：`closed_conditional_state_support_established_interaction_not_established`。输出：`code/outputs/formal/calibration/stage_0_5_state_support_v1/`。

## 当前实验表

| 实验编号 | 实验目的 | config / 变量 | baseline | 数据集 | 主要指标 | 状态 | 客观实验结果 | 输出目录 |
|---|---|---|---|---|---|---|---|---|
| `stage_0_1` | 验证四格、五表与封存链 | seed `2026080701`，dt `0.2 s`，源事件/通道两变量 | 四格内部对照 | SUMO | 处理前等价、隔离、时钟、生命周期、物理路径 | `Verified` 工程层 | 工程检查通过；源/目标双走廊物理不连通，不能形成科学效应 | `code/outputs/formal/stage_0_1/` |
| `stage_0_2` | NGSIM 跟驰风险审计 | 候选 TTC 阈值 `2.0 s`；holdout=false | 无模型 baseline | NGSIM US-101、Lankershim calibration | measurement status、有效 TTC、事件数、TTC/DRAC 分布 | `Active` | v2 旧快照共 4,753,044 state rows、1,797,968 valid-TTC rows、4,758 events；异常和最终范围未收口 | `code/outputs/formal/calibration/stage_0_2_ngsim_v2/` |
| `stage_0_3` | 城市运动学与车型分布 | 时间加权主统计；车辆等权稳健；已批准连续性 0<Δt≤0.043 s（仅本文件）；bootstrap 2000×；R2 原始顺序/身份/质量 fail-closed 语义 | 不适用 | pNEUMA d1 | 分布与分位数 | `Completed / Closed`（2026-10-16 `pass` 有限范围） | 785 轨迹 / 1,239,475 状态；速度 TW mean=4.8382 m/s、VW mean=6.2077 m/s；R3 关闭包 fail-closed 复核全过、独立复算零差异；物理真实性 Unverified | `code/outputs/formal/calibration/stage_0_3_scientific_acceptance_20261016_r3/` |
| `stage_0_4` | 界定通信可观测证据 | RV_RX 仅作 receive-state continuity；trip 级分割 | 不适用 | SPMD RV_RX | packet schema、latency/loss/adoption 可观测性 | `Completed / Closed (Limited Scope)`（2026-10-17 Limited Scientific Acceptance，`pass_limited`） | RV_RX 连续性 Verified；RSE_BSM 车辆侧接收内容已核验；SEE-V2X 受控 PC5 候选参考；通信参数未冻结未校准；Packet 未下载（历史边界） | `code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/` |
| `stage_0_5` | 仿真—现实覆盖 | seed `20260907`，稳定哈希，最多每组 5,000 rows；场景职责/权重/阈值未冻结 | 场景内 real-real 距离候选 | NGSIM、pNEUMA、SUMO | Energy Distance、stratum coverage、场景内分层指标 | `Active` | AAD-0.5.0 只读审计完成；迁移前包含 25,000 kinematics、20,000 following、4,758 events，不能回接；无 SUMO 样本，canonical pNEUMA 与 writer 有字段冲突 | `code/outputs/formal/calibration/stage_0_5_real_reference_v1/` |
| `stage_0_6` | 数值验证与协议锁准备 | 科学容差尚未冻结 | 解析真值/物理真值 | 合成真值与前置 Gate | analytic/path truth、方向、时间步、readiness | `Active` / blocked | 技术检查通过；迁移前 readiness 为 `protocol_lock_allowed=false` | `code/outputs/formal/calibration/stage_0_6_prelock_validation_v2/` |
| `stage_1_1` | 核心效应确认 | `not_frozen` | `not_determined` | `not_created` | 尚未确定 | `Agreed` 但 blocked | 未实现、未运行、无结果 | 无 |

## 结果边界

所有当前登记结果均 `scientific_claim_eligible=false`。`evidence/results/` 中的阶段化目录名是便携索引；其中 JSON 内容保持原运行字节，因此仍可能出现旧实验编号或迁移前 Gate 文本，不能把目录重命名误读为重新运行。

## 历史实验

pNEUMA 地图匹配、候选前车和人工 QA 已由研究者批准退役，代码/测试/脚本位于 `legacy/`，完整输出位于 `code/outputs/history/legacy_experiment_ids/`，小型证据位于 `evidence/history/legacy_experiment_ids/`。其他 DRIFT 与传播 Pilot 见 `docs/HISTORY_INDEX.md`。

## 2026-10-10 当前 Stage 0.2 工程诊断包

`RES-STAGE-0.2-TASK-1.4`（任务 1.4 报告）：5,706,252 状态行、2,211,378 有效 TTC 行、5,381 原始与可靠候选事件、拒绝 0。数据为三个 US-101 TXT 与 Lankershim CSV；工程诊断包在 `code/outputs/formal/calibration/stage_0_2_task_1_4_20261010/`，不是科学风险频率或 Gate 通过。旧 v2 及任务 1.3 不覆盖。

## 2026-10-10 任务 2.2 运动学与持续性诊断

任务 2.2 对任务 2.1 的 447 个案例按同后车—前车轨迹和实际连续帧检查风险持续性、位置/速度/加速度差分与几何证据边界。多帧连续 298、单帧尖峰 3、边界/缺帧 25；自动标签 C=349、D=98。前车长度的独立几何字段不足，几何真实性保持 Unverified。固定 48 个案例审核包和模板位于 code/outputs/formal/calibration/stage_0_2_task_2_2_kinematic_review_20261010_r6/；人工审核未完成。

## 2026-10-10 任务 2.2.1

修复任务 2.2 连续段解析并生成独立验收包。r6 与新结果 1 个案例由多帧连续变为间歇；新统计为 297/3/1/25/121，自动 C=349、D=98。代表案例四源各 12 个，显式配额覆盖普通、阈值、TTC、DRAC、间距类别；人工审核未完成。


## 2026-10-11 决策归档与参数核定

四来源时间加权 TTC 中位数为 11.378882、17.170886、16.312500、14.416058 s，批准尺度规则给出 tau=15.364279 s。P2 事件参考为 4,545。连续 rho、固定窗口贡献上下界和 P2 0.2 s 尚未进入正式 pipeline。


## 2026-10-11 连续风险时间尺度验证

使用 tau=15.364279 s 计算四源分布、TTC 分箱暴露/贡献、tau/2/2tau、极端压力和 P2 成员重叠。正式目标区域 burden 因固定区域/车辆/窗口缺失保持 Unresolved。


## 2026-10-12 Stage 0.2 综合收口（当前状态）

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。

## 2026-10-18 Stage 0.5 场景设计审计

只读审计报告：docs/STAGE_0_5_TASK_0_5_0_SCENARIO_DESIGN_AUDIT.md。Stage 0.5 仍为 Active / pending_simulation_sample；US-101 为高速风险主线候选，Lankershim 为独立城市风险辅助候选，pNEUMA 仅为单文件城市运动学补充。已确认标准化 pNEUMA schema 与当前 writer 直接列契约不兼容；现有迁移前 real-reference 包和旧 map-match 路径不能作为正式输入。抽样权重、车型映射、时间分辨率、场景化 Energy Distance 和覆盖阈值均未冻结，未运行 SUMO。

2026-10-18 AAD-0.5.1：`RES-STAGE-0.5-REAL-REF-R2` 已重建。canonical pNEUMA 直连 writer 的 11 字段、质量契约、原始车型和 source SHA 测试通过；四个 NGSIM state、正式 P2=4,545 和 Stage 0.3 R2/R3 统计摘要已进入版本化输入 manifest 与便携证据。完整可靠/时间加权/车辆等权语义保持既有批准结果；哈希状态和轨迹簇只作敏感性。real-real 独立性不足，覆盖阈值、车型映射、SUMO 时间步和校准/验证隔离仍待 0.5.2 决定，未运行 SUMO，Gate 未升级。

2026-10-18 AAD-0.5.2：新增候选覆盖协议报告 `docs/STAGE_0_5_TASK_0_5_2_COVERAGE_PROTOCOL_DESIGN.md`。候选主协议为 US-101 五层必要条件（基础运动学、跟驰交互、风险可观测性、P2 暴露/事件率、场景支持），无综合分数补偿；Lankershim 为独立辅助，pNEUMA 为单文件城市运动学补充。Energy Distance 保持辅助诊断，默认 0.90/0.95 未升级为阈值；校准/验证窗口、统计不确定性、辅助范围和 0.5.3 工程契约待研究者批准。

2026-10-18 AAD-0.5.4-A：新增 `RES-STAGE-0.5-CALIBRATION-READINESS-V1`（工程审计，非 Gate 结果）。测量等价性：16 项维度（10 Equivalent/Verified、6 Engineering Consistent Only、0 阻断）+ 16 个确定性边界用例全部符合预期；封存分母与事件率被独立复现（111,425.9 s/543 与 133,505.6 s/732）。校准窗口（仅前两个，SHA 校验 + 行级过滤，验证窗口 0 行）：0750_0805 均速 11.43 m/s、净间距中位 16.87 m、事件率 17.54 veh⁻¹h⁻¹；0805_0820 均速 8.94 m/s、净间距中位 13.96 m、事件率 19.74 veh⁻¹h⁻¹。轨迹簇 CI（2,000 次重采样）：事件率 [15.11,20.50] 与 [17.47,22.36]，均速 ±0.12 m/s；逐行 i.i.d. 窄 12.7 倍。时间步敏感性：内部 0.1/0.05/0.025 s 事件数一致（1），但边界移动 0.2 s/次减半，TTC 最小值 1.794→1.868→1.906 收敛；300 s 基准墙钟 24.2/27.7/33.8 s。准入清单 `ready_to_start_stage_0_5_4b=false`（5 待批准、5 阻断）。

2026-10-18 AAD-0.5.3：新增独立 SUMO 工程骨架 `stage_0_5_sumo.py` 和入口 `run_stage_0_5_sumo_baseline.py`。US-101 `generic_highway_candidate`（3 主线段 × 3 车道 + 入口/出口匝道）以 seed=20260907、internal 0.1 s、recorded 0.1 s 完成两个工程 fixture：①baseline_mixed_demand（90 s）：8,453 state、17 vehicles（全部进入并驶出）、6,118 leader rows、724 valid TTC rows、min TTC 6.971 s、工程 P2=0、P2 可评价跟驰暴露 609.4 s（0.1693 veh-h）；②measurement_probe_queue_stop（40 s）：2,720 state、7 vehicles、1 个工程 P2 事件（onset 3.1 s、确认 3.3 s、持续 2.4 s、TTC min 1.794 s），Stage 0.2 formal-alignment adapter 给出完全一致的事件边界。同 seed 重复运行 SHA-256 一致。Lankershim/pNEUMA 为 candidate_entry_only；所有网络、需求、vType、行为、时间步、暖机/评价窗口和容差仍未科学冻结。结果 `RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1`，仅 engineering_only。

## 2026-10-18 AAD-0.5.4-A+ 定向补充

`RES-STAGE-0.5-CALIBRATION-GAPS-V1`：两个原始校准TXT共2,583,693行与R2状态100%连接，冲突0；来源车辆2169/2017，汽车比例96.173%/97.323%、汽车中位长4.4196m，车型/长度物理真值仍Unverified。源时钟解释952.8/999s、两源重叠89.5s，没有发现标准化时间错误。候选主线1–5、150≤y<350m；首尾按最长观测轨迹时长100.9/123.5s作候选缓冲后，保留12/11个60s片，统一密度阈值42.8767/48.0828veh/km/lane，内部覆盖720/660s；300m主线1648/1449.82veh/h/lane。局部/分层P2完整成员归属未批准，率Unresolved。

四次300s工程负载完成（SUMO1.26.0，seed20261018，recorded.1s）；.05s低/中/高实际密度41.91/48.06/54.76，墙钟100.27/103.03/116.24s，峰值合计RSS271.9/297.8/327.7MB，末时未插入0/17/23，无碰撞/teleport/守恒残差。初始化积压仍在，60s不是批准暖机；.05s自动ballistic而.1s积分器未显式固定，不能声称数值收敛。完整P2提取成本未含入。Engineering Ready有条件、Measurement Ready待有限批准、Calibration Ready=false、Reality Coverage Accepted=false；所有科学容差Tolerance Not Yet Justified，推荐路径B受限探索仅Proposal，未启动。Gate继续pending_simulation_sample，无验证/holdout/下载/正式校准/锁/Stage I/II。

依据：`docs/STAGE_0_5_TASK_0_5_4A_SUPPLEMENT_CALIBRATION_GAPS.md`及同ID的diagnostics、unified_strata、benchmark、candidate_protocol、audit。完整包`code/outputs/formal/calibration/stage_0_5_calibration_gaps_v1_final/`。Context Consistency Check：不将Proposal写入06_DECISIONS的Approved Research Decision。


## 2026-10-18 B0受限探索

2026-10-18 AAD-0.5.4-B0（RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1）：受限探索完成19/23次，4次高输入seed20261019响应未运行。统一27.78m/s上限、空初态、ballistic显式、internal.05/recorded.1、action.1、sigmaStep1；三个基准输入1087.364/1449.818/1648veh/h/lane仅实现局部密度10.37–15.75、均速约27.1，局部低速/P2均0。tau2三次末期未服务21/22/71，入口main0约2.5–20.1m有低速插入/加速，局部段无拥堵。B0-EXEC-STOP-01：原调度器未因completed+blocker停止，发现后人工停止，源码停止后修复并测试；最后worker峰值内存Unverified。推荐先批准需求边界/最小结构对照，不继续参数搜索掩盖状态支持缺口。所有结果exploratory_diagnostic_only、scientific_claim_eligible=false；Gate=pending_simulation_sample、Calibration Ready=false、Reality Coverage Accepted=false、正式容差Tolerance Not Yet Justified、Energy Distance上界Not Identifiable；B0实验验证输入0；根全量回归无过滤打开历史Stage0.2全源事件/案例产物，任务级验证访问不能认证（B0-VALIDATION-SCOPE-02）；数据隔离验收不Accepted。无holdout/正式校准/锁/Stage I。依据：docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md、同ID证据和execution_ledger。 全部300s固定五个60s片及5s图表保留；19次合计约541.1s、已监控峰值595.18MB、约224MB产物。高输入响应缺第二seed，无统计确认。

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

`RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1`：固定SUMO1.26.0源码审计确认，非决策步延续公开加速度，内部带符号候选终速可由公开TraCI独立重建`u=v0+a_pub_start*h`，对任意符号精确成立（含`u<0`步内停车）；决策步`v1=0`仍被`max(u,0)`钳制，仅范围一致。3个微型运行、948条相邻边：947精确核验且全过，最大残差`1.4210854715202004e-14m`，1条决策步停车仅范围，0不可评价，0异常；未用位移反推、未用调试二进制。

B1.1精确停车Pending记录与B1 C/D、B0不变。Gate=pending_simulation_sample，scientific_claim_eligible=false、ready_to_start_stage_0_5_4b=false、reality_coverage_accepted=false；容差Tolerance Not Yet Justified、ED上界Not Identifiable、锁/StageI禁止。方案A/B准入与B1.2前置条件待研究者决定；B1.2不自动执行。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_1S_STOPPING_OBSERVABILITY.md`及同ID便携证据；协议/源码/输入冻结SHA见experiment_plan、PLAN_SHA256和provenance。


## 2026-10-19 B1.2 分层准入与机制再验证

RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2：B1.2前置阻断；v1冻结零尝试后被源副本完整性检查替代；v2仅压缩C接入fixture部分运行，最后完整帧19.7s，19.75s一条终速不一致阻断。10047精确全过、14 bounded、84不可评价；D fixture/8主项均not_attempted。局部计数32进入/21离开、全网49进入/6驶出/43在场，71跨edge里程交叉核查。未获完整接入资格，无新原尺度机制/真实覆盖/P2运行结论。


## 2026-10-19 B1.2-N

`RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1`：独立B1.2-N工程任务。固定SUMO1.26源码完整谓词和调用顺序已审计；无停车任务的fresh/immutable生命周期可用doubleMax不变量，同edge常规停车仅非决策步可作充分条件。一般myStopDist不能由公开getter等价恢复。新候选`b12n-near-zero-observability-v1`不以位移/终速选择上下文，1e-6m不变。3个30s微型运行：2879边，2876精确全过（其中1负近零后处理），3 bounded，0近零未决/不可评价/工程错误；最大残差1.3988810110276972e-14m。冻结前203项受控合成通过。

正近零非决策步清零运行边未出现（Not Observed），未满足运行前冻结的共同准入条件；integration_allowed=false，C/D计划冻结被拒绝，均Not Attempted，未追加试验/搜索。新主矩阵禁止且0次。旧B1.2阻断/0-8/D未运行和所有历史证据不变。下一步由研究者决定正近零覆盖设计与未来政策，再另批接入/主矩阵；不自动继续。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2N_NEAR_ZERO_AND_INTEGRATION.md`；证据同ID目录。科研Gate/ready/现实覆盖/锁/StageI状态不变，科学阈值未批准。


## 2026-10-19 B1.2-P

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

结果 `RES-STAGE-0.5-FINAL-CLOSURE-V1`（`evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1/`）。

真实局部参考（按已批准 D1）：0750–0805 内部窗 [120,840) 起始 147 件、可评价暴露 31,051.6 veh-s、17.0426 events·veh-h⁻¹（车辆簇条件区间 [13.604, 21.131]）；0805–0820 内部窗 [180,840) 起始 216 件、33,091.1 veh-s、23.4988（[19.621, 27.806]）。全采集敏感口径 174/39,065.8/16.0345 与 252/43,522.0/20.8446。全源确认事件 543/732、全源可评价暴露 111,425.9/133,505.6 s 与 A+ 合格切片求和逐位复现；四个口径逐事件差异 0750 全网 3 件、0805 全网 7 件，均有位置与时钟依据。

条件候选用例（`candidate_experiment_plan.json`，SHA 绑定）：通用三车道网络、60 s 周期信号（绿 48.0/42.2 s）、内部断面流量 1648.0/1449.818 veh/h/lane 作为条件排班流入、A+ 车型长度候选、Krauss/LC2013 固定、内部 0.05 s / 记录 0.1 s、评价窗 [180.0, 299.7] 运行前冻结。FC1（0750 条件）与 FC2（0805 条件）各 300 s、seed 20261019：状态 `completed_with_diagnostic_warning`、工程阻断 0、数值精确 381,560/381,560 与 355,458/355,458、范围一致 36/86、不可评价 1,511/1,318、最大残差 2.84e-14 m、守恒与局部平衡残差 0、期末待插入 0。

状态支持判定（冻结规则）：两次运行的速度与密度全部落在预声明 30 s 块包络之外，低速/闭合状态也未按真实参考出现，故 `EvidenceInsufficient_StateSupport`；按失败分支停止，未执行第 3 次构造与保留的 2 次独立 seed 重复。五层合取 = Evidence Insufficient（阻断层 1/2/5）。本地胶囊：`stage_0_5_final_closure_v4`（参考）与 `stage_0_5_final_candidate_v1`（候选）；v1–v3 为被取代的准备尝试，保留但不作结果。

## 2026-10-21 AAD-0.5-TR-RECON 真实交通重建与条件场景诊断

实验编号 `stage_0_5`（结果 `RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1`）。实验目的：解释「断面流量匹配但不匹配拥堵状态」，并构造有观测证据支撑或明确标记为条件性的 SUMO 场景。

- config / 变量：真实侧只读（无变量）；场景侧 3 个运行前冻结变体 RC1（观测几何 + 观测需求、空网、下游开放）、RC2（+ 真实拥堵初始状态）、RC3（+ 声明的条件 3 车道下游供给）。SUMO 1.26.0，内部 0.05 s / 记录 0.1 s、单线程、300 s，评估窗 `[180.0, 299.7]`。
- baseline：2026-10-20 冻结的 FC1/FC2（3 车道、无匝道流量、80% 绿信号、空初态）作为自由流分支对照，未重跑，逐字节复用。
- 数据集：两个已批准校准窗口 canonical 状态（SHA 绑定）+ 数据集内官方 NGSIM 聚合报告。第三窗口与 holdout 零读取。
- 主要指标：局部 `k`/`v`/`q=k·v·3.6`/低速份额/30 s 块包络；守恒残差；边界流量；慢速连通域起点与扩张方向；净间距、闭合速度符号；观测反推的有效 Krauss 时间间隔。
- 状态：`closed_evidence_insufficient_state_support`。
- 客观实验结果：真实两窗口 43.544/10.506 与 50.505/7.915；RC1 23.899/21.053/q=1,811；RC2 23.812/21.203（前 30 s 16.71/34.14，180 s 内退化）；RC3 6.755/61.349/q=1,492。三者均未落入真实目标包络 → `EvidenceInsufficient_StateSupport`，按预声明停止规则停止（构造 3 次、独立重复 0 次、未加第 4 次）。有效 tau 反推 1.527/1.628 s（密度）与 1.552/1.627 s（净间距），冻结值 1.0 s。
- 输出目录：`code/outputs/formal/calibration/stage_0_5_trajectory_reconstruction_v1/`、`code/outputs/formal/calibration/stage_0_5_scene_reconstruction_v1/`；证据 `evidence/results/RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1/`。

## 2026-10-20 AAD-0.5-LIT-CAL 文献依据的行为诊断

实验编号 `stage_0_5`（结果 `RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1`）。实验目的：把每个方法绑定到经原文核验的文献，并在逐对微观层面检验「有效 `tau`≈1.6 s 能否修复断面流量匹配但状态不匹配」的错配。

- config / 变量：A 阶段只读（10 条状态定义 × 2 窗口，零模型 1000 次置换）；B 阶段 2 窗口 × 12 对 × 2 配置（`tau=1.0` 基准 vs `tau=1.6` 候选，其余冻结），内部 0.05 s / 记录 0.1 s / ≤25 s，种子 20261101 与 20261102。
- baseline：既有 RC1/RC2/RC3 与 FC1/FC2 保留不改，本任务不重跑；B 阶段的 baseline 是同一批样本上的 `tau=1.0`。
- 数据集：两个已批准校准窗口 canonical 状态（SHA 绑定）。第三窗口与 holdout 零读取。
- 主要指标：连通域规模/持续/最早位置/方向/反向速度/零模型超越率；Brockfeld Eq. 2 间距误差、`NRMSE(gap)`、`NRMSE(speed)`、间距与速度偏差/MAE、车头时距、闭合速度。
- 状态：`closed_evidence_behaviour_candidate_not_supported`。
- 客观实验结果：A 阶段 16/16 非饱和规则向上游、起始 y=500–650 m，反向速度 2.0–8.3 m/s；0750 绝对 10 m/s 零模型超越率 0.999（不可区分），相对速度定义 0.000–0.142（显著）。B 阶段 24 对选中、23 对重放、43/48 组合有指标、26 次插入拒绝（44%）；配对 Brockfeld 差 +19.57 pp（CI [4.25, 35.51]）、间距偏差 20/20 变差（+5.62 m）、`NRMSE(speed)` +0.00；分层 <1.0 s +56.7 pp、1.0–1.5 s +63.8 pp、1.5–10 s −2.60 pp。
- 输出目录：`code/outputs/formal/calibration/stage_0_5_method_diagnostics_v1/`；证据 `evidence/results/RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1/`。

## 2026-10-20 AAD-0.5-METHOD-EXPANSION 方法扩展与行为诊断

实验编号 `stage_0_5`（结果 `RES-STAGE-0.5-METHOD-EXPANSION-V1`）。目的：查明真实交通—SUMO 错配来自初始化、模型结构、参数还是随机性，并给出可实施的文献方法。

- config / 变量：P2 只读覆盖矩阵（探索性阈值）；P3 两条初始化路线 × 12 对 × 1 seed = 24 次；P4 9 个单因素配置 × 12 对（分层选取）× 3 个共同 seed = **324 次独立 SUMO 进程**；P5 门控未开。
- baseline：`K_tau1.0`（冻结 Stage 0.5 候选 vType）；同 seed 集跨配置以分离参数与随机性。
- 数据集：两个已批准校准窗口 canonical 状态（SHA 绑定）；第三窗口/holdout 零读取。
- 主要指标：Brockfeld Eq. 2、NRMSE(gap)/NRMSE(speed)（加速度留空并附理由）、间距/速度偏差与 MAE、局部窗与长期窗分列、扰动传播幅值比与滞后、seed 内波动、参数相关与信号/噪声比。
- 状态：`closed_level2_partial_plus_level3_unidentifiable`。
- 客观实验结果：`tau` 配对恶化 +18.31/+40.70/+72.51 pp（1.3/1.6/2.0），三 seed 同号；`minGap`→1.0 −7.31、→5.0 +29.75；`sigma=0` −6.34；IDM(T=1.0) −5.52（长期窗 −8.09、局部窗 −0.09）；IDM(T=1.6) +26.50；Newell 原型 50.94/85.42%。`tau` 与 `minGap` 效应 r=−0.944/+0.818；seed 波动中位 2.35 pp，信号/噪声 13.5。
- 输出目录：`code/outputs/formal/calibration/stage_0_5_method_expansion_v1/`；证据 `evidence/results/RES-STAGE-0.5-METHOD-EXPANSION-V1/`。

## 2026-10-28 Stage 0.5-R1 三臂诊断执行（Verified）

任务 `AAD-S0.5-R1-EXECUTE-20261028` 已完成一次 B10、一次 B01、一次 B11 原生 SUMO 运行；B00 A03 `WEEK_0750_B00_IC1_s20261201_A03` 只复用既有接受证据，未重跑。三臂均为 420 s / 8400 步、SUMO 1.26.0 / TraCI 22、独立工程回执 Pass、统一离线测量完成。B10 五条 `main_2` lane 的 180/240 s 限速设置和回读通过；B01 60 辆匝道车辆全体生命周期保留，原始块计数 `9/8/9/8/9/9/8` 保持；B11 为严格组合。

观测：B10/B01/B11 源区正式 P2 均为 0，目标区正式 P2 均为 0；目标可靠 D1 暴露分别为 13667.8、9865.1、13553.6 veh-s。全体声明车辆均为 1150，实际插入 955/1009/956，pending 195/141/194，discarded/collision/teleport 均为 0。R1 `C_INPUT_ROUTE` 精确 cohort=1112（79 初态、1033 非初态），ID 哈希 `76db89e2ff2d9df997516b59a23bc4d88a85c7a0161dca6a222f2a8bfee277f8`。

R2 结论：情况 A，三臂均未获得合格源事件；按停止规则不追加 seed/intensity/search。Stage 0.5 Gate 继续 blocked，Stage 0.6 仍 pending scientific tolerances/dynamic calibration，Stage I 仍 blocked until Protocol Lock。没有生成 Protocol Lock、没有访问 locked holdout。完整证据：`docs/STAGE_0_5_R1_EXECUTION_2026-10-28.md`、`evidence/results/RES-STAGE-0.5-R1-DIAGNOSTICS-20261028/`；原始输出在 `code/outputs/formal/calibration/stage_0_5_r1_diagnostics_20261028/`。

## 2026-10-28 First-round offline decision package
Completed offline-only R0/R1/B00 reconciliation and candidate comparison. No new trajectory, no formal P2 re-execution, no threshold/window/cohort semantic change. Machine evidence includes file audit, candidate matrix, reconciliation, run record, manifest and SHA256SUMS.

## 2026-10-28 Round1 Task3 / Round2 freeze candidate

Completed static Round2 preparation only. Preferred candidate is current B00 A03 heterogeneous Krauss with minGap 2.5→1.0 on all five vTypes; seed20261201, 420s, [120,390), original source/target/cohort and formal P2 unchanged. One primary attempt is proposed; independent seed is conditional and separately authorized. No new trajectory was run.

## 2026-10-28 Round2 Task1 prelaunch
Completed offline macro-rule comparison only. Rule A strict joint state/closing support is recommended (10/30 prior cells pass); Rule B permissive is 11/30; Rule C is insufficient. Candidate native launch awaits researcher confirmation; SUMO/TraCI=0.
