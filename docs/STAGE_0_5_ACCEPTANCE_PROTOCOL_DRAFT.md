# Stage 0.5 验收标准审计与协议草案

> Issue #1后续（2026-10-24）：当前交接入口为 [冻结候选v1](STAGE_0_5_ACCEPTANCE_FREEZE_CANDIDATE_V1.md)和[证据审计/非覆盖式更正](STAGE_0_5_WP1_EVIDENCE_AUDIT.md)。C4两个校准源的混用支持域已由证据解决，其他C项部分解决但科学选择/生产修复待决；本文各项“未复算/全部待决”保留为原审计时点。候选仍未批准，Gate不变。

日期：2026-10-24（Asia/Shanghai）。审计基线：`e73c6de9029e4ceb2c1b792f9b9c401b1773c23c`，开始时 `main...origin/main`、工作区干净。

**状态：Proposed / Awaiting Researcher Decision。本文不是冻结协议，不批准实验，不改变任何 Gate、风险定义或已有决定。** 本任务仅阅读当前源码、配置、已登记报告和机器摘要；未重新读取真实轨迹、未运行科学实验、未访问 locked holdout。第三窗口只核查已发布的验证摘要，不重新物化其数据。

## 1. 当前状态与协议目标

当前登记的 Stage 0.5 Gate 为 `pending_simulation_sample`，`scientific_claim_eligible=false`、`reality_coverage_accepted=false`、`protocol_lock_allowed=false`、`stage_1_1_allowed=false`。状态支持与到达时序任务是条件性诊断，不是现实验收。依据：[注册表](PROJECT_REGISTRY.json) 的 `current` / `stage_0_5` / 两项结果记录，以及 [状态支持计划](../evidence/results/RES-STAGE-0.5-STATE-SUPPORT-V1/experiment_plan.json)、[到达时序计划](../evidence/results/RES-STAGE-0.5-ARRIVAL-TIMING-V1/experiment_plan.json) 的 `mode`。

历史报告将剩余机制缺口概括为“交互相容未成立”。本次审计还发现**正式分母与诊断分母不同、真实与仿真分块不同、时距字段名与公式不一致、报告与机器参考值不一致、计划与实际覆盖判据不同**，详见 §3。它们尚未裁决，不能把历史“状态支持已成立”或诊断 P2 数值直接转换成正式验收结论。本任务保留历史报告和机器结果，不重新判 Gate，也不替研究者选择修复后的科学口径。

协议目标是建立有限适用域内的现实相容性标准，使宏观状态、微观交互、风险测量和所需传播动态逐项可审核。**现实相容不等于事故预测准确、AAD 因果效应成立或真实道路总体被重建。** 仿真中消息—采用—动作—风险的因果链仍属于后续研究，不以交通低速波代替。

本文标签：`Verified` = 已核对文件/实现事实；`Agreed` = 已有研究者批准决定；`Active` = 当前阶段/问题；`Proposed` = 本文建议；`Historical` = 原任务范围内记录；`Unknown / Unverified` = 未知或未核验。机器文件中的 `Observation/Derived` 原标签只表示其自身证据层级，不自动表示科学验收。

## 2. 正式决定、参考范围与可复用事实

### 2.1 决策继承表

正式决定源为 [AI_CONTEXT/06_DECISIONS.md](../AI_CONTEXT/06_DECISIONS.md) 对应日期条目；以下同时给出实现或封存证据，避免只靠上下文认定。

| 决定 / 状态 | 已批准内容 | 实现与证据 | 未批准部分 |
|---|---|---|---|
| 2026-10-11、10-12 风险定义与有限验收 / Agreed | P2：可靠 TTC < 2 s，首末观测跨度 ≥ 0.2 s；确认取实际观测帧。事件率分母为可靠且 P2 可评价跟驰时间，两端状态为 valid 或 not_applicable；无效不补零 | [formal_risk_measurement.py](../code/src/riskprop/formal_risk_measurement.py)：`FormalRiskConfig`、`extract_formal_source_events`、`observed_confirmation_time`；[版本配置](../code/configs/stage_0_2_formal_risk_measurement_p2_v1.json)；[R4 科学 Gate](../evidence/results/RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4/scientific_gate_report.json) | 独立物理真值、事故风险、SUMO 现实覆盖未获此决定支持 |
| 同上，连续风险 / Agreed | `rho=exp(-TTC/tau)`，tau=15.364279197080283 s；固定车辆/区域/窗口、车辆等权、缺失贡献上下界、四格 DID | 同模块 `rho_from_ttc`、`contribution_bounds`、`integrate_fixed_window`、`equal_vehicle_average`、`did_interval`；配置 `rho` | 区域、车辆资格、窗口、消息去重字段仍为 null；公式批准不等于完整主实验已冻结；风险 tau 不等于跟驰模型 tau |
| 2026-10-18 场景职责 / Agreed | US-101 为高速跟驰风险主要参考；Lankershim 为独立城市辅助，不是 US-101 主 Gate 必要条件；pNEUMA 只做单文件城市运动学与车型参考 | [真实参考 R2 audit](../evidence/results/RES-STAGE-0.5-REAL-REF-R2/audit.json)、[重建报告](STAGE_0_5_TASK_0_5_1_REAL_REFERENCE_REBUILD.md) | 不混成 iid 总体；pNEUMA 不承担前车/TTC/DRAC/P2；其 25 Hz 连续性规则不迁移给 NGSIM |
| 2026-10-18 五层与统计原则 / Agreed | 基础运动学、跟驰交互、风险可观测性、正式 P2/暴露、状态与样本支持分别必要，不加权补偿；ED 仅辅助 | [覆盖设计](STAGE_0_5_TASK_0_5_2_COVERAGE_PROTOCOL_DESIGN.md)、[校准准入配置](../evidence/results/RES-STAGE-0.5-CALIBRATION-READINESS-V1/candidate_protocol.json) | `minimum_stratum_coverage=0.90` / `real_real_quantile=0.95` 非科学门槛；ED 上界 Not Identifiable |
| D1，2026-10-20 / Agreed | 局部事件按开始位置/开始时间；完整上下文提取后裁切；两端在域且整边在窗的原可评价 100 ms 边作分母；确认时刻仍为最早消息时刻 | [stage_0_5_final_closure.py](../code/src/riskprop/stage_0_5_final_closure.py)：`real_region_mask`、`checked`、`links`、`local_p2`；[正式局部参考](../evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1/real_local_reference_summary.json) | 确认位置、至确认全在域为辅助；不以归属规则批准现实验收 |
| D2 / Agreed | 局部交通状态目标，不要求全网稳态；窗口/稳定性规则在运行前冻结；记录全网在场、实际进出和 pending | [最终收口计划](../evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1/candidate_experiment_plan.json)、[LF 协议设计](STAGE_0_5_LOCAL_FOLLOWING_PROTOCOL_DESIGN.md) §5–6 | 120 s 暖机、300 s 暖机或任何正式评价窗均不能由已有输出自动批准 |
| D3 / Agreed | 通用高速公路、有限局部覆盖；内部通行率不等于上游需求；需求/供给/路线/车型/网络为条件输入；供给先于行为参数冻结 | [最终收口报告](STAGE_0_5_FINAL_CLOSURE_2026-10-20.md) §1、§3–4；[到达审计摘要](../evidence/results/RES-STAGE-0.5-ARRIVAL-TIMING-V1/phase_a_audit_summary.json) | 不以行为参数补偿供给错配；不据通用网络声称真实结构/物理传播速度已复刻 |
| D4 / Agreed | 95% 报告水平；车辆簇、时间块、seed 不确定性分开；差值区间 + 独立系统误差界 B + 单独科学容差 delta | `stage_0_5_final_closure.py::equivalence`；[delta/h 依据审计](../evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1/delta_h_basis_audit.json) | 未批准 delta、h 或 B 的数值；未批准传播硬门槛或联合区间构造方式 |
| D5 / Agreed（原任务范围） | 原收口最多 5 次，构造最多 3、至少预留 2 次冻结后独立 seed；默认原长度、有资源依据才可至 450 s；第三窗口冻结后使用 | 同模块 `check_run_plan`；[运行账本](../evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1/candidate_run_ledger.json)；[决策包 R1–R5](../evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1/researcher_decision_package.json) | 不是所有后续任务的通用额度；当前草案不消耗剩余次数 |

### 2.2 本文采用的真实参考值

局部区域 R：NGSIM 车道 1–5、150 ≤ y < 350 m。时间均为各来源标准化秒，不是名称中“15 分钟”直接换算；两个来源真实采集长 952.8/999 s，并存在 89.5 s 时间重叠，不能作为独立交通日。[A+ 报告](STAGE_0_5_TASK_0_5_4A_SUPPLEMENT_CALIBRATION_GAPS.md) 与 [A+ diagnostics](../evidence/results/RES-STAGE-0.5-CALIBRATION-GAPS-V1/diagnostics.json) 保存来源时钟审计。

| 来源 | 已计算参考窗 | P2 开始事件 N | D1 可评价 E（veh-s） | 3600 N/E（events/可评价 veh-h） | 局部均速（m/s） | 密度（veh/km/lane） |
|---|---|---:|---:|---:|---:|---:|
| us101__0750_0805 | [120,840)，720 s | 147 | 31051.6 | 17.042600 | 10.506118 | 43.543611 |
| us101__0805_0820 | [180,840)，660 s | 216 | 33091.1 | 23.498766 | 7.915276 | 50.505455 |

事件/暴露见上述 `real_local_reference_summary.json` 的 `interior`，速度/密度见同包 `uncertainty` 与 [real_domain.json](../evidence/results/RES-STAGE-0.5-STATE-SUPPORT-V1/real_domain.json) 的 `windows`。它们是已计算参考，**不意味着未来仿真暖机或验证窗口已经批准**。参考 P2 簇区间分别 [13.6041,21.1309]、[19.6213,27.8057]，仅为来源内条件 bootstrap；不包括共同供给、交互依赖或模型偏差，不能当正式联合差值区间或容差。

`real_domain.json` 当前机器记录的速度 sd 为 3.638562/3.985862 m/s，净拉开份额为 0.531176/0.523055，时距比例估计为 1.533904/1.606439 s（312093/331974 个 gap 受限状态；合并 644067、1.566153 s）。这些值与报告部分表格不同，详见 C4；本文不混用不同统计口径。

## 3. 本次发现的冲突与适用性限制

以下冲突仅登记，不更改源码、配置、封存产物或原报告。所有受影响的正式指标冻结须等待裁决；无关的文档审计继续完成。

### C1：诊断 P2 率分母未执行 D1 连续边契约

- **Documented Intent**：D1 要求可靠身份/前车/时钟连续、两端可评价、两端在区域、整条边在评价窗；分母是跟驰时间。
- **Actual Implementation**：`stage_0_5_state_support.py::block_descriptors` 仅对局部点筛 `measurement_status in {valid,not_applicable}`，输出 `len(evaluable)*0.1`。`stage_0_5_sumo.py::compute_sumo_measurements` 将无前车点也设为 `not_applicable`，但 `reliable_following_eligible=false`；诊断分母未检查该资格、相邻边或前车连续性。两个 runner 均直接用此分母计算 `p2_local_rate_per_vehicle_hour`，没有调用 D1 `local_p2/links`。
- **Evidence**：[state_support 模块](../code/src/riskprop/stage_0_5_state_support.py) 的 `block_descriptors`；[SUMO 测量模块](../code/src/riskprop/stage_0_5_sumo.py) 的 `compute_sumo_measurements`、正确边级接口 `compute_exposure`；[状态支持 runner](../code/scripts/run_stage_0_5_state_support.py) `run_cell`；[时序 runner](../code/scripts/run_stage_0_5_boundary_timing.py) `run_arrival`；[seed_repeats.json](../evidence/results/RES-STAGE-0.5-STATE-SUPPORT-V1/seed_repeats.json)、[run_results.json](../evidence/results/RES-STAGE-0.5-ARRIVAL-TIMING-V1/run_results.json) 的 `descriptors.p2_evaluable_exposure_veh_s`。
- **Affected Files**：上述模块/runner/摘要及引用其率的两个报告、注册表、AI_CONTEXT。
- **Conflict**：历史 0.9–1.5、18.2–25.5 等模拟率不是已证同 D1 分母的正式率；方向和影响幅度本次没有重算。事件核心阈值相同不等于整条测量链等价；无前车不能按零风险跟驰计时。事件位置查找的 `except KeyError: continue` 也应在未来审计中单列遗漏计数，不能默认全部成功。
- **Status: Awaiting Researcher Decision**。建议另行授权先做已有输出的边级独立核验；不需要先追加仿真实验。

### C2：状态域空间分块和面积归一化不一致

- **Documented Intent**：报告称真实 30 s × 100 m 局部块云、同构造相容比较。
- **Actual Implementation**：`block_cloud` 先裁 [150,350)，再用 `floor(y/100)` 分成实际宽 50/100/50 m 的三块，但每块分母都按 100 m × 5 车道；仿真 `block_descriptors` 使用整个 200 m 局部段的 30 s 块。真实包络与仿真块的空间尺度不同。
- **Evidence**：[real_block_cloud_us101__0750_0805.csv](../evidence/results/RES-STAGE-0.5-STATE-SUPPORT-V1/real_block_cloud_us101__0750_0805.csv) 首三个空间块起点 100/200/300 m；首块 states=3094，密度=3094×0.1/(30×0.1×5)=20.626667；这证明使用的是 100 m 分母，尽管进入此块的观测只来自 [150,200)。源码上述两函数与 `local_region_mask` 可直接核对，无需读取原始轨迹。
- **Affected Files**：`stage_0_5_state_support.py`、两个 runner、`real_domain.json`、状态域/覆盖率/时序沿用包络结果。
- **Conflict**：边块归一化与共同空间支持未统一；历史域范围和 0.833/0.636/0.851 覆盖率不能直接升格为科学门槛。整体 200 m 均速/密度不因本发现自动改值；是否影响历史成员判定尚未重算。
- **Status: Awaiting Researcher Decision**。选项：固定两块 [150,250)、[250,350)；或保留全球网格、按实际相交宽度归一化并统一仿真网格。二者改变估计对象，不在本任务选择或修复。

### C3：车头时距标签与实际公式不同

- **Documented Intent**：字段 `time_headway_mean_*_s`、`net_gap_over_speed_s` 表示时距类量。
- **Actual Implementation**：[stage_0_5_leader_replay.py](../code/src/riskprop/stage_0_5_leader_replay.py) `pair_metrics` 实际用 gap/(后车速度−由位置差分的前车速度)，只取正闭合；[stage_0_5_trajectory_reconstruction.py](../code/src/riskprop/stage_0_5_trajectory_reconstruction.py) `interaction_stats` 同样用 gap/closing，而非 gap/后车速度。前者另有 `observed_time_gap_mean_s=mean(gap/max(v,0.1))`，也不同于前保险杠时距。
- **Evidence**：上述函数赋值/输出；`interaction_stats` 分别 `dropna()` gap 与 closing 后按数组位置相除，还需未来核验行对齐，不能因长度相同默认身份相同。
- **Affected Files**：两模块、调用它们的重放/重建报告和输出字段消费者。
- **Conflict**：这些字段更接近 TTC 型派生量，不能据名称视为车头时距已验证，也不能当正式 TTC 替代（其差分速度/epsilon/筛选不同）。
- **Status: Awaiting Researcher Decision**。建议先决定净时距与前保险杠时距的主辅关系、近零速度处置，再另行授权字段及兼容性修复。

### C4：报告参考总体与当前机器包不一致

- **Documented Intent**：[状态支持报告](STAGE_0_5_CONDITIONAL_STATE_SUPPORT.md) §1 声称局部全体 829382 条，两个 tau_eff=1.5393/1.5687；§3 报告闭合均值 −0.197/−0.128、净拉开份额 0.537/0.530。相关上下文/注册表重复了这些数值。
- **Actual Implementation**：当前 `load_real_states` 先按 `CALIBRATION_WINDOWS` 裁时间，`following_relation` 再按 0<gap≤80；当前 `real_domain.json` 是 §2.2 的 644067 条、1.533904/1.606439，闭合均值 −0.171376/−0.109441、份额 0.531176/0.523055。`following_relation` 本身没有额外显式 `leader_matched/measurement_status` 筛选，不能凭报告的“全体可靠”用语证明资格。
- **Evidence**：报告 §1、§3 与 `real_domain.json::{following_relation,windows}`、`stage_0_5_state_support.py::{load_real_states,following_relation,local_summary}`。
- **Affected Files**：状态支持报告、注册表该结果 `core_metrics`、AI_CONTEXT 相应段落与依赖这些参考值的比较。
- **Conflict**：差异可能涉及全采集/内部时间窗及有效闭合分母，但本任务没有重读数据证实原因，不自行解释成已完成勘误。`local_summary` 的负闭合份额以全部局部点为分母（NaN<0 为 false），而重建 `interaction_stats` 先去 NaN；这两种份额不应混用。
- **Status: Awaiting Researcher Decision**。建议按已批准时间/质量语义对账后追加可追踪更正，不覆盖原结果。本文只能引用有明确字段指针的机器值，并保留口径限制。

### C5：冻结计划文字与已执行状态覆盖判据不同

- **Documented Intent**：状态支持 `experiment_plan.json::membership_rules.baseline_definition` 写双向覆盖最小值；`primary_state_support` 写 pooled envelope 覆盖。
- **Actual Implementation**：`run_stage_0_5_state_support.py::_membership`（函数名见源码）对校准条件用“该窗口落在另一窗口包络”的方向性基线（0.833333/0.636364），并比较另一窗口包络覆盖；平均点仍比较 pooled envelope。`state_support_verdict.json::cells` 保存 `reference_baseline_coverage` 与 `block_coverage_reference_envelope`。
- **Evidence**：上述计划、runner 与 [判定产物](../evidence/results/RES-STAGE-0.5-STATE-SUPPORT-V1/state_support_verdict.json)；`real_domain.json::cross_window_baseline_detail`。
- **Affected Files**：冻结计划、runner、判定产物及其后续复用。
- **Conflict**：预声明规则文字与执行不完全一致，不能只凭 PLAN_SHA256 宣称判据完全一致；本次不推断会改变哪些 pass/fail。
- **Status: Awaiting Researcher Decision**。未来版本须逐项对齐判据；历史规则及结果原样保留。

## 4. 验收指标矩阵

分级：**N** 表示已批准五层中的必要责任，并非该行所有统计量都已成为数值硬门槛；**P** 表示建议选作必要指标、待研究者确认；**A** 表示辅助诊断。未列数值容差一律 `Tolerance Not Yet Justified`；精度 h、最低簇/块/seed 数均待决。所有真实参考限 §2 的来源与时间范围；不将跨场景差异当成允许偏差。

### 4.1 宏观状态与交通动态

| ID / 责任 | 定义、单位与统计口径 | 真实参考及实现/证据 | 已有要求与依据 | 缺口 / 待决 | 建议验证方法（Proposed） |
|---|---|---|---|---|---|
| M1 / N 状态支持；P 联合域 | 局部 k=车辆占有时间/(窗长×车道公里)，v 为相同支持上的速度均值；联合 (k,v)，单位 veh/km/lane、m/s；不得仅比较 q | `state_support::{local_summary,block_cloud,block_descriptors,support_envelope}`；§2.2、`real_domain.json` / 块 CSV | 当前域用带宽 7.5、2.5/97.5% 速度包络、跨窗覆盖基线；仅原任务诊断，不是 delta | C2/C5 阻断直接复用；密度范围 14.52–76.10 是当前构造产物，不是科学容差 | 对齐时空单元/边块面积，逐窗逐 seed 联合支持；均值在域不能替代块分布、动态支持 |
| M2 / N 运动学；P 速度分布 | v 的时间/状态加权 CDF、分位数、均值、sd（当前 ddof=1）；低速占比 Pr(v<5 m/s)；车辆等权另表 | `local_summary/block_descriptors`；真实 sd 3.638562/3.985862、低速 0.096892/0.252973；§2.2 | 5 m/s 为描述阈值；无批准的均值、尾部或 sd 容差 | 不能只选最贴近的统计量；不同加权对象不能混比；低速零值可能是无状态支持 | 主统计量及尾部预先选择，来源内车辆簇与时间块分别报告；每个必要量用 §6 区间规则 |
| M3 / A 流量/积压/交通动态；N 输入审计 | 断面实际穿越数/窗长×3600/车道数；q=3.6kv 只作一致性量；全网 N、入/出、pending 和局部进出时间序列 | [重建模块](../code/src/riskprop/stage_0_5_trajectory_reconstruction.py)；[重建报告](STAGE_0_5_TRAJECTORY_RECONSTRUCTION.md)；`run_results.json` 与 LF 周期表 | D2/D3 要求持续记录；未要求全网精确稳态；内部流量不是需求 | 局部五车道区域不是闭合控制体，须计侧向进出；瓶颈位置/供给未识别 | 对账实际而非声明通行；按预定时间块记录漂移和相位；不以守恒残差为零证明稳态 |
| M4 / A 加速度/减速 | a（m/s²）分布、减速持续与极值；明确原始量/差分量、采样尺度和缺口 | `state_support::measure_state_frame` 用速度差分/0.1，首点填 0；`leader_replay::pair_metrics` 的 nrmse_acceleration=null；[方法扩展报告](STAGE_0_5_METHOD_EXPANSION_RESULTS.md) | 既有“未核验噪声、不比较加速度 NRMSE”限制有效；pNEUMA 只是独立城市辅助 | 首点填零、跨缺口差分不能直接作为真实加速度验证；测量误差无界 | 先明确共同测量算子与不合格状态，核验误差再决定是否增加硬门槛；本轮不更改代码 |

### 4.2 微观交互

| ID / 责任 | 定义、单位与统计口径 | 真实参考及实现/证据 | 已有要求与依据 | 缺口 / 待决 | 建议验证方法（Proposed） |
|---|---|---|---|---|---|
| I1 / N 跟驰相容；P 速度—净距联合关系 | g=前车前保险杠位置−前车长度−后车前保险杠位置（m）；TraCI g=getLeader distance+后车 minGap；报告 g 条件于 v 的分布与尾部 | `stage_0_5_sumo` 测量/几何 crosswalk；`state_support::following_relation`；真实当前 0<g≤80 m 子集见 §2.2 | 净距符号/几何契约已确认；80 m、minGap=2.5 是该诊断口径，不是统一验收阈值 | C4；速度分箱、分层权重、共同支持、尾部容差待决；tau_eff 与 minGap 不分别可辨识 | 保留原始与有效支持计数；两窗口分开、同速度/状态层比较；不以单一回归斜率替代联合分布 |
| I2 / P 车头时距；A tau_eff | 净时距 T_g=g/v_f；前保险杠时距 T_h=(g+L_leader)/v_f，均为秒（运动中瞬时换算，不自动等于固定断面通行时距）；tau_eff=(Σg−n·minGap)/Σv 是另一个条件平衡估计 | `leader_replay::pair_metrics`、`trajectory_reconstruction::interaction_stats`、`state_support::following_relation`；[轨迹覆盖与可辨识性报告](STAGE_0_5_TRAJECTORY_COVERAGE_AND_IDENTIFIABILITY.md) | 没有正式时距硬阈值；1.0/1.5/2.5 s 是既有选样分层 | C3 阻断直接采用历史 time_headway 字段；v≈0 时不可用随意截断产生有限值；车辆长度适用性待核验 | 研究者选择主时距及低速排除/单独统计规则；与 TTC、tau_eff 分开；逐身份、逐观测对齐验证 |
| I3 / N 交互；P 闭合速度 | c=v_f−v_l（m/s）；c>0 接近、c<0 拉开；分布/分位数、有效闭合观测中的负值份额、持续段 | `compute_sumo_measurements`、`local_summary`、`interaction_stats`；§2.2、C4 | TTC 有效正闭合 epsilon=1e-3 m/s，继承 NGSIM；不是科学误差界 | 当前负份额点分母与非缺失分母不同；缺失占比须单列；块均值接近 0 不能证明波动一致 | 冻结有效分母/权重，检查分布宽度、符号与连续段；不给缺测赋零；与状态匹配联合而非互相补偿 |
| I4 / A 跟驰响应与汇入诊断 | 重放 gap 相对绝对误差 100Σ abs(g_s−g_r)/Σg_r（%）；NRMSE=RMSE/√mean(x_r²)；偏差/MAE；汇入/换道频率与响应延迟需另定估计量 | `leader_replay::{brockfeld_error,nrmse,pair_metrics}`；[初始化保真报告](STAGE_0_5_INITIALIZATION_FIDELITY.md)、[方法扩展结果](STAGE_0_5_METHOD_EXPANSION_RESULTS.md) | 旧“26/48拒绝”已更正为插入延迟；控制链核验仅限已测适用域 | 12 对分层不是全体总体；外生前车重放不是自由交互；不能把异质参数在自身轨迹上拟合再验证 | 用同批配对与声明 seed 比较，输入/前车重放误差先行；若科学主张依赖汇入，另选必要指标和证据，不擅自扩大研究 |

### 4.3 风险与传播动态

| ID / 责任 | 定义、单位与统计口径 | 真实参考及实现/证据 | 已有要求与依据 | 缺口 / 待决 | 建议验证方法（Proposed） |
|---|---|---|---|---|---|
| RISK1 / N 正式 P2 与 E；P 率相容 | TTC=g/c，仅可靠 g>0、c>1e-3；P2 TTC<2 s 且跨度≥0.2 s；lambda=3600N/E，N 按 D1 开始归属，E 为两端在域/在窗的可靠可评价边秒数 | `formal_risk_measurement`、`final_closure::local_p2/links`、`sumo::{build_sumo_p2_events,extract_sumo_formal_p2_events,compute_exposure}`；§2.2 | 100 ms 语义、0.11 s 核心 max_gap 与更严格帧/时钟连续性；阈值/归属已批准；delta_lambda/h_lambda 未定 | C1；零暴露→不可估，零事件≠安全；截断/首次观测风险应单列 | 全上下文事件识别后裁切，独立复算 N/E/成员/确认/边界；按轨迹与时间块处理依赖，稀少事件不用默认正态近似；N/E 不拆成三个互相独立精确目标 |
| RISK2 / A 严重度；N 已批准公式 | DRAC=c²/(2g)，m/s²，仅有效闭合；rho=exp(−TTC/15.364279197080283)，无量纲，P2 阈值不截断 rho | `compute_sumo_measurements`、`formal_risk_measurement` 与配置；[定义一致性历史报告](STAGE_0_5_FORMAL_RISK_DEFINITION_CONSISTENCY.md) | TTC 触发、DRAC 描述严重程度；缺失风险贡献保留 [0,1] 界；车辆等权 burden | 固定车辆/区域/窗、去重未冻结；无严重度或 burden 等效容差；当前 Overleaf 内容本任务未核查 | 分开核验测量、积分与聚合；不将条件闭合 rho 均值当全区域 burden，不用 P2 率替代连续风险效果 |
| RISK3 / P 交通时空传播；当前 A | 同位置时间速度≤自身 15% 分位为异常；50 m×10 s、8邻接；最大连通域（格）、持续（s）、跨度（m）；邻位互相关滞后及 u=−50/(lag×10) m/s；位置内时间置换超越率 | `boundary_timing::{space_time_cells,temporal_position_anomaly,wave_structure,cross_correlation_propagation,permutation_null,classify_wave_structure}`；[波摘要](../evidence/results/RES-STAGE-0.5-ARRIVAL-TIMING-V1/phase_b_wave_diagnostic.json) | 原诊断 ≥6 位置对、上游份额≥0.5、超越率≤0.05、非零滞后且速度向上游；1000置换、seed20261231；不是正式 Gate 硬门槛 | 真实原窗与模拟 [0,420) 比较，非共同 [300,420)；速度分辨率由网格决定，−5 m/s 不表示精确真值；gap/边界单元支持仍需审计 | 先选择传播主张必需的方向/尺度/持续性，再冻结共同观测域/时间长度与误差；合成上游/下游/静止/无异常/缺口反例；敏感性 10/15 s×0.10/0.15/0.20。零模型超越0是有限置换结果，不是概率0 |
| RISK4 / P 风险事件传播 | 需要明确“风险从源到目标”的身份/时空链、先后关系、方向、传播滞后/衰减/持续；目前没有已批准 Stage 0.5 数值估计量或阈值 | 研究问题见 `PROJECT_CONTEXT.md` §1；P2 事件/确认接口可提供节点；现有低速波只提供交通状态证据 | 不以速度波=风险传播，更不能等同消息因果效应；Stage 1.1 禁止 | 对应科学主张、可识别性、必要范围与标准全部待研究者确认；不可填虚构数值 | 工作包2先明确可观测链和替代解释，提交候选估计量；若必要机制不可识别则证据不足，不以宏观拟合绕过 |

### 4.4 测量、工程有效性与重复稳定性

| ID / 责任 | 定义、单位与统计口径 | 真实参考及实现/证据 | 已有要求与依据 | 缺口 / 待决 | 建议验证方法（Proposed） |
|---|---|---|---|---|---|
| E1 / N 输入保真 | 身份/车型/路线/车道/初速/数量逐项匹配；声明与实际到达延迟（s）、间隔 CV（无量纲）、never_inserted（辆）、初态丢弃/夹速 | `boundary_timing::{entry_events,paired_arrival_tables,write_arrival_route_file}`、runner `run_arrival`；[fidelity_metrics.csv](../evidence/results/RES-STAGE-0.5-ARRIVAL-TIMING-V1/fidelity_metrics.csv)、[verdict.json](../evidence/results/RES-STAGE-0.5-ARRIVAL-TIMING-V1/verdict.json) | 主线操纵未实现、匝道实现；原始输入同一不证明实际输入同一；不把延迟当拒绝 | 真实入口是首次观测代理；逐车车型缺失；两臂未插入数不同；无正式延迟/CV容差 | 先查可施加性、身份交集与供给排队；失败则不能作该因素因果对照；预先声明允许误差与停止规则 |
| E2 / N 身份时钟/质量 | 来源+轨迹+前车+原始行号；连续 100 ms/帧与时钟一致，缺帧/换前车/身份不确定断链；可靠、可评价、不可评价、闭合暴露分别报 | `formal_risk_measurement::continuity_is_valid`、`final_closure::checked/links`、`sumo::following_link_is_valid`；[测量等价矩阵](../evidence/results/RES-STAGE-0.5-CALIBRATION-READINESS-V1/measurement_equivalence_matrix.json) | 质量契约必要；NGSIM 无报告前车与 SUMO 无前车状态名不完全等同；都不自动计可靠跟驰 | 独立物理真值 Unverified；状态字段存在不证明每个新调用者遵循契约 | 同输入双实现与逐成员/逐边对账；身份/时间失败阻断受影响测量；报告缺失原因与选择偏差，不伪造缺失 |
| E3 / N 数值/工程链 | 积分器、internal/recorded/action步长、数值分支、位移残差（m）、碰撞/teleport、控制调用、守恒/进程/哈希 | [B1.2-P报告](STAGE_0_5_TASK_0_5_4B1_2P_POSITIVE_NEAR_ZERO.md)、[收口报告](STAGE_0_5_FINAL_CLOSURE_2026-10-20.md)；状态支持/时序计划 SUMO1.26、internal0.05/recorded0.1 | 1e-6 m 是已核验分支工程容差；原批次0 collision/teleport；不是现实误差 B 或 delta | 后续原生 FCD 未自动继承每个分支的微审计；100/200ms不等价；积分器混用不能宣称收敛 | 固定版本/哈希/控制链，同记录尺度核验；任何新适用域先验证，不以调大残差阈值消除失败 |
| E4 / N 样本与独立验证 | 每条件：有效车辆簇数、时间块数、可评价E、事件N、截断/缺失数；每seed全量结果及seed间变异；CI半宽 h_obs | 正式参考簇1789/1431、原60s块12/11；`seed_repeats.json`、`temporal_validation.json`；§7 | D4分离依赖来源、D5保留独立资源；样本支持不足不能补零 | 原seed集合含构造seed；跨窗同日/部分重叠；无多日总体支持、无h目标；已有新seed证据不等于正式独立验收 | 冻结后未用于选择的seed单独评价；配对因素用共同seed、独立重复用不相交seed池；预定支持/精度/失败停止规则，不能挑seed或延长到通过 |
| E5 / A ED与覆盖总览 | 场景内多维 Energy Distance、分层支持比例；依赖变量尺度、权重和抽样单位 | [simulation_real_coverage.py](../code/src/riskprop/simulation_real_coverage.py)、[覆盖设计](STAGE_0_5_TASK_0_5_2_COVERAGE_PROTOCOL_DESIGN.md) | ED仅辅助；real-real上界Not Identifiable；0.90/0.95为工程默认 | 无可迁移数值界、无充分独立重复；不得作综合抵消分数 | 固定变量/标准化/分层，报告敏感性；不取当前最佳模拟ED反定阈值 |

## 5. 容差、精度与误差依据

三者必须分开：统计区间描述估计不确定性；B 描述独立证据支持的剩余系统测量误差上界；delta 描述科研上最大可接受模型差异。h 是所需统计精度，不是另外一种容差。不同单位的指标分别决策，比例量需说明百分点/相对差，率比需事先处理零事件，不能混用。

| 依据 | 当前能支持什么 | 不能支持什么 / 处理 |
|---|---|---|
| 全观测与簇/时间块 bootstrap | 特定窗口、抽样假设下的波动；封存 `reference_statistics_plan.json` 与 `*_joint_uncertainty.json` 可查 | 同一路段共同冲击未消失；12/11块及2000重采样的尾部精度有限；不能直接给道路总体CI或delta |
| Stage0.2/0.3质量关闭、100ms/25Hz规则 | 已批准有限测量语义与可复算性 | 不证明物理测量误差 B=0；没有独立真值就写 Unknown，不从工程epsilon推出B |
| internal减半/记录尺度敏感性、1e-6m链 | 离散化和工程误差的局部证据；前者曾使事件边界移动0.2s，见校准准入包 `timestep/` | 不是允许模型偏差，也不能证明任意后续数值分支有效 |
| 两窗口差异/real-real域 | 观察到的条件异质性，帮助选择估计对象、条件层与工作包 | 自然波动不等于等效容差；观测极值不是允许偏差边界 |
| seed重复 | 现有场景的模拟随机变异已被观察，不能沿用旧“尚无seed方差”的现时说法 | 与构造seed重叠、先选配置后重复等限制需披露；不能抵消C1–C5或证明独立泛化 |
| 下游科学影响允许量 | 理应约束delta：多大参考误差会改变研究者关心的传播判读 | 当前未给定最小有意义效应/可容忍混淆；本任务不运行AAD敏感性实验、不代定效应量 |

**推荐（Proposed）**：先建立每项“估计对象—测量误差证据—允许偏差理由—精度与样本后果”决策卡。优先补独立测量依据并解决口径冲突，然后由研究者确定delta/h。若无法识别B，可选择仅接受明确限定的测量代理域；这属于范围决策，须写清不能支持物理真实相容，不能暗设B=0。也可保持证据不足并暂停科学验收。不给缺证据的指标填经验百分比。

## 6. 三类判定规则草案

本节保留D4已批准原则；以下对“不满足/证据不足”的细分和精度操作是 **Proposed**，尚未写入执行代码。现有 `equivalence` 只返回 `criterion_satisfied/discrepancy_or_imprecision`，不能把后者直接当科学不满足。

### 6.1 单指标

先核验指标定义、来源/条件、共同支持、测量有效性、独立验证角色和批准状态。标量设差异 d=theta_sim−theta_real，95%差值区间 I=[L,U]；B为差值测量系统误差界（若两侧各有界而无抵消证据，采用预先批准的保守合成）；扩展区间 J=[L−B,U+B]；允许集合 A=[−delta,+delta]。非对称/单侧范围或变换尺度须另批，不默认为双侧百分比。

| 结论 | 规则（前置有效且已批准时） | 原因标签 |
|---|---|---|
| 满足 | J 完全包含于 A，且所需精度/样本支持达到批准要求，所有必要窗口/条件分别满足 | criterion_satisfied |
| 不满足 | 已批准必要工程/测量契约被证实违反；或在可评价、精度足够、共同支持上 J 与 A 不相交 | measurement_invalid / input_fidelity_failed / model_discrepancy；必须区分原因，不能一概称模型失败 |
| 证据不足 | delta/h/B未批准或不可识别；测量不可观测；支持/独立性不足；区间部分越界或精度不够；口径冲突未裁决 | awaiting_decision / unidentifiable / insufficient_precision / unresolved_contract |

必要定义未批准时，即使点估计差很大也不凭空设置margin后判正式失败。已确认的工程违规可判该契约不满足，但受污染的科学量仍应“不可评价/证据不足”；不能用修复前数值宣布模型差异。建议对精度采用 h_obs=(U−L)/2≤h，并另报B；非对称CI、率比尺度和联合区间的精度定义由研究者确认。

分布/联合域要先定义距离或功能性比较及其独立界；没有批准距离界不能将“落入自然包络”当分布等效。传播类别需要观测分辨率、反例验证、随机零模型和预先批准的类别规则；显著空间结构不是与真实传播等效的证明。

### 6.2 合取、依赖与报告

1. 每个必要条件、来源窗、预声明状态层分别判断。五层全满足才有资格提交研究者验收；存在任一必要不满足则总体不满足；无不满足但有证据不足则总体证据不足。辅助指标不投票、不抵消、不自动成为硬门槛。
2. 宏观拟合不能补偿微观失配，率接近不能补偿错误分母，速度波不能补偿风险传播不可观测。
3. 车辆/轨迹簇、共同时间冲击、seed为不同相关层。分别报告条件区间与敏感性；如构造联合CI需预声明层次重采样/依赖模型，不把逐帧或多个重叠窗口当独立样本。不简单相加方差假设独立。
4. 95%是已批准报告水平，多指标/多窗口的联合覆盖或多重性策略仍待决。不得挑通过的指标或窗口；置信区间重叠、差异不显著、5个seed同符号都不能替代等效检验。
5. 每项结果须有：版本/条件/窗口/单位、N/E与缺失、估计值、I/B/delta/h、来源依赖、判定/原因、主辅角色、证据路径。缺失字段写 Unknown，不能用0或自动pass填充。

当前仅完成事实审计：正式验收整体 **证据不足，协议未冻结**；历史任务的未通过/停止记录与现有Gate全部保持。此处不是重新执行已封存科学判定。

## 7. 实验与验证约束审计

| 项目 | Verified / Agreed 历史事实 | 当前约束与尚未冻结内容 |
|---|---|---|
| 校准源 | 前两个US-101来源已反复用于构造、诊断及定义选择；真实参考窗见§2 | 不再称盲验证；不得根据风险结果事后缩窗。多日独立性不存在，89.5s来源重叠需保留 |
| 第三窗口 | 原收口任务未用；后续 `temporal_validation.json` 已记录 `us101__0820_0835` [300,1020)、4次冻结配置仿真，2行为×seed20261211/20261212；既有摘要记录域覆盖0.850746 | 它**已经接触**，不是未接触holdout。该验证限原状态域/配置；其派生需求6135 veh/h主线、540匝道来自该窗，属已声明条件输入，不是完全盲预测。R5仍须决定未来复用角色 |
| 冻结机制 | `freeze_manifest.json`绑定四个科学产物及两个源码SHA；`step_temporal`读取前实际检查 `frozen_files`，源码SHA记录但此入口未逐项检查 `source_sha256` | 文件存在/哈希记录不等于全部执行语义被冻结；需核验源/配置/统计/条件输入角色。历史列适配修复与重写manifest已在已知问题登记，不借此倒推未访问 |
| locked holdout | 当前任务未读；既有状态支持模块 `_assert_not_holdout`拒绝 lankershim/i80/peachtree/spmd 标记 | 这是该任务守卫范围，不重定义来源的永久科学职责；Lankershim过去Stage0.2辅助使用事实仍保留。不能根据路径名把已看来源重新变成盲holdout；具体密封清单不打开 |
| 旧隔离问题 | B0-VALIDATION-SCOPE-02记录根全量回归读过历史全源产物，任务级验证物化Unknown；后续白名单/胶囊是受控Python入口防线 | 不认证过去全程未接触，不宣称OS/native全监控。本次根目录只跑文档定向测试，完整回归在无本地数据/历史输出的纯Git克隆执行 |
| 暖机/评价窗 | FC1/FC2预声明[180,299.7]；后续状态/时序诊断[300,420)，420s运行；波指标却用模拟全[0,420)，真实按各来源参考窗 | 这些是任务内窗口，不是正式R3批准。需决定有限动态剖面或稳定后评价；不能把“最后三分之一”当已验证暖机；不同指标支持不一致须显式声明 |
| 暖机失败与记录 | LF三周期平台候选5/10/20%敏感性均到300s才完成，剩评价0s；局部平台与全网pending增长并存 | 不回填120s暖机；先冻结供给/初态/暖机规则，再确定有效评价长度。所有延长也须在预算与停止规则内 |
| 原运行额度 | LF1/2/3用3/8，收口FC1/FC2再用2，原累计5/8，剩3（至少2用于冻结后独立重复）；触发失败停止后未补跑 | 剩3只是封存台账，不是本任务可动用额度。原 `check_run_plan` 600s墙钟/3GiB内存/2GiB产物等属于该计划限制，不扩展为当前统一预算 |
| 另行授权额度 | 真实重建3、文献重放48、方法扩展324、状态支持58（30网格+20重复+4结构+4时间验证）、到达时序20；依据各报告、计划和执行台账 | 与原剩3分账，不相互转移；这些是已执行历史数而非下一轮许可。R4须明确来源、保留池、失败/重试/冒烟如何记账 |
| seed角色 | 状态支持grid=20261201，repeat=20261201…20261205；时序同5seed在U/E配对且与前任务复用；第三窗=20261211/12 | 5个不同seed不等于5个都未用于选配置；不能重复池化同seed轨迹或同seed延长。未来建议构造与最终验证seed不相交，配对与独立重复角色分别标注 |
| 环境/资源 | 既有SUMO1.26，internal0.05/recorded0.1及plan中二进制SHA；Windows默认；WSL只作为可选执行环境 | 本任务无环境/WSL操作。未来大型实验必须先查磁盘/输出预测和安全余量；WSL可用性Pending Verification，容量目标不授权清理或复制数据 |

后续任何实验都需新的明确任务授权。不得启动ABCD、通信干预、Stage1.1、Protocol Lock或保留资源验证；失败不得换seed/放宽margin/改窗口继续直到通过。

预算证据导航：[LF执行](STAGE_0_5_LOCAL_FOLLOWING_EXPLORATION.md)、[收口账本](../evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1/candidate_run_ledger.json)、[重建计划](plans/2026-10-21-stage-0-5-trajectory-reconstruction.md)、[重放报告](STAGE_0_5_LEADER_REPLAY_BEHAVIOUR_DIAGNOSTICS.md)、[扩展报告](STAGE_0_5_METHOD_EXPANSION_RESULTS.md)、[状态支持报告](STAGE_0_5_CONDITIONAL_STATE_SUPPORT.md) §4/§11、[时序计划](../evidence/results/RES-STAGE-0.5-ARRIVAL-TIMING-V1/experiment_plan.json)。报告中的运行数与新任务预算不可互换；历史日期勘误按各文档保留。

## 8. R1–R5状态与待研究者决定表

原项来源：[收口决策包](../evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1/researcher_decision_package.json)。2026-10-21两项后续决定记录均保留R1–R5开放。本表更新证据可用性，**不覆盖原决策，不表示批准推荐项**。

| 项 / 当前状态 | 已解决或新增证据 | 仍需决定 | 推荐选项（Proposed）与备选影响 |
|---|---|---|---|
| R1 / Awaiting Researcher Decision | D4方法与95%已批准；已有真实簇/块及模拟seed波动，不再说完全没有seed证据 | 每项主指标、delta/h/B依据、联合统计方式、必要/辅助清单；C1–C4影响测量可比性 | **推荐先统一测量并补独立B/科学影响依据，再给数值**。备选：有明确依据时直接审批数值；或明确限于代理测量域/停止科学验收。自然波动与最佳仿真均不是依据 |
| R2 / Awaiting Researcher Decision | 条件状态和入口不可施加性有已登记诊断；主线入队延迟抹平时序，匝道可施加；状态包络另有C2/C5待裁决 | 目标条件、边界供给/上游存储、初态/路线/车型、主张涉及的结构与传播范围 | **推荐先定条件输入和可施加性标准，再选后续机制对照**。备选：授权新网络版本/上游存储或受控汇入研究；维持有限通用走廊；缩小主张或停止。缩小范围是科研决定，不能为通过而自动删指标 |
| R3 / Awaiting Researcher Decision | 已有300/420s诊断，状态/P2与波的时间支持不同；无正式暖机依据 | 动态目标或稳定目标、实际评价/确认上下文、相位、空间分块、最短支持/精度 | **推荐在R2确定后冻结有限动态时间剖面与共同支持**。备选：独立确认暖机后开始评价，可能需更长预算；延后。不得把[300,420)直接追认正式窗 |
| R4 / Awaiting Researcher Decision | 原剩3保留；后续多个任务单独授权已用；seed与构造重叠可核查 | 原3归属、新预算、构造/独立验证分配、资源上限、停止与失败记账 | **推荐保留旧池，测量审计先行；新实验另列预算和不相交验证seed池**。备选：研究者显式重分配原3或不再执行；不得因3次不够而默认扩额 |
| R5 / Awaiting Researcher Decision | 第三窗已有冻结后条件验证和公开摘要；不再未接触；B0隔离历史Unknown保留 | 已用第三窗未来角色、何谓独立验证、是否需要新的未接触资源及访问一次后的失败规则 | **推荐第三窗标“已使用时间迁移参考”，新协议的确认性独立性另作设计**。备选：显式接受已接触条件验证的有限范围；或申请新的独立来源/保留资源（须另批，绝不自动开启locked holdout） |

### 8.1 审批时需要逐项填写的最小卡片

每个选中的必要指标填写：`指标ID / 必要或辅助 / 科学主张与适用域 / 参考版本与资格 / 估计量及权重 / 空间时间支持 / 测量误差证据与B / delta及独立理由 / h与区间方法 / 相关性与多重性 / seed及预算 / 三类判定 / 不可评价与停止规则 / 批准人和日期`。不要求把所有A/P指标升级为N。

传播还须独立决定：只要求方向/连贯性，还是要求速度/尺度/持续与风险事件链；后者需要更强测量分辨率和真实性证据。推荐将交通波作为机制诊断候选，风险事件传播的硬条件随核心主张另批；不凭“5/5恢复波”或置换p≤0.05自动验收整个Stage0.5。

## 9. 后续工作包2的输入条件

工作包2指后续真实风险机制分析/场景实验准备；本文不给它新增执行授权。输入应包括：

1. 研究者对R1–R5及必要指标范围的逐项决定，或明确仍只做只读机制分析、哪些内容暂缓；协议版本/批准记录与数据访问角色。
2. C1–C5冲突的裁决与另行工程任务：D1边分母/资格、共同分块、时距定义、参考数值对账、计划与执行判据一致性。需要重算时另建结果/更正记录，保留旧包。本草案不以“修复”名义自行重算。
3. 两校准窗的来源哈希、事件成员/边级暴露与统计支持；引用正式参考的SHA/计划；第三窗注明已使用，B0历史隔离不确定性随包携带。
4. 已冻结或明确待定的条件输入：网络/供给/到达/初态/车型、可施加性验证、输入保真界与失效处理；不以内部流率替代不可观测需求。
5. 与科学主张对应的可观测机制链和竞争解释，说明速度波、跟驰风险事件、消息传播分别测什么。无法识别的链不由推断补齐。
6. 若获准实验：独立构造/验证池、统一窗口及确认支持、样本精度和预算、磁盘资源预检、版本/环境/数据来源/输出目录、失败停止与不重试规则。未满足则只推进已授权的不依赖项，不消耗验证资源。

交接验收只问这些输入是否齐备，不替研究者决定算法、模型、loss、效应量或结论。五层相容全部有证据且研究者正式批准后，才有资格另行更新Stage0.5状态；Stage0.6 readiness和协议锁仍需独立流程。

## 10. 审计与验证边界

本稿全部仓库链接按当前文件存在性核验；关键公式与函数直接核对；机器摘要值按JSON字段引用，冲突原样登记。没有使用Overleaf/OB材料来代替当前实现，没有访问它们。历史定义一致性报告中的 `paper/主论文/main.tex` 只是历史操作记录；当前论文来源仍按 [论文与材料导航](PAPER_AND_MATERIAL_SOURCES.md)。

本次已完成验证（2026-10-24）：

- 根目录 `python code/scripts/validate_project_docs.py --strict-git`：`PROJECT_DOCS_OK`；`python code/scripts/export_project_evidence.py --repo-root . --verify`：`PORTABLE_EVIDENCE_OK`。没有修改登记结果的audit/config/manifest/provenance/SHA256SUMS，因此未重导出证据。
- `python -m pytest tests/test_project_docs.py -q`（禁用缓存、使用独立basetemp）：13 passed。最初两次在默认临时目录/沙箱写权限处setup失败；权限流程批准后用新任务临时目录通过，未改测试或扩大数据范围。
- 不含dataset/历史outputs的纯Git克隆，叠加本任务8个文档文件：全量 `python -m pytest -q -rs -p no:cacheprovider --basetemp=tmp/acceptance_full_20261024_01` 为 **958 passed、14 skipped、1 warning**（176.63s）。13项skip因本地原始/密封数据不在克隆，1项为另由专用胶囊preflight覆盖的bootstrap契约；不把skip算科学通过。warning来自既有 `test_stage_0_5_final_closure.py` 中pandas不兼容dtype赋值，未修改。
- 同一克隆严格文档与证据校验通过，`python -m compileall -q code/src code/scripts code/tests` 通过。随后仅修正草案表格分隔符并登记验证结果，未改变代码或测试。
- 58个Markdown文件链接存在，表格列数检查通过，两个正式P2率从封存N/E复算相符；三个关键封存包中87个现存文件与各自SHA256SUMS相符；全项目便携清单另经上述verify覆盖。`git diff --check`通过，改动仅8个文档/导航文件。

§10收尾状态勘误（Issue #1）：上列是原任务已保存的验证记录；原“提交后还需执行”仅为当时待办，不能据此声称原最终核验已执行。本Issue的严格检查、受权限约束的回归与纯Git核验另记于 [工作包1验证记录](STAGE_0_5_WP1_VALIDATION.md)，最终提交后的实际clean/clone检查以本Issue交付报告的SHA和结果为准。历史验证记录不追认成当前验证；哈希/测试通过不构成科学验收。
