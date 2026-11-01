# P2 Task1 Source Event 与 Physical Propagation 操作规范

日期：2026-11-02
状态：COMPLETED_WITH_LIMITATIONS
平台范围：SUMO 模型内；不声称现实交通因果证据。

## 1. 任务边界与已确认范围

P2 Task1 把 P1 的物理链

\[
\text{Source Event}\rightarrow\text{Physical Interaction}
\rightarrow\text{Physical Propagation}\rightarrow\text{Target Region}
\rightarrow\text{Physical Arrival}
\]

转成可记录、可审计和可证伪的对象。当前研究者已确认：

- SUMO 是当前优先平台，现实场地和实车不是前置条件；
- Formal P2 是源事件 A 路线的优先定义；
- 安全受控扰动是独立的 B 机制路线，不重新标记为 Formal P2；
- 目标 cohort、region、window 原则上预先固定；
- SUMO Observer 只读、不参与控制，不等同现实路侧传感器；
- 首版只支持总体时间优先性，不主张单个事件的跨世界提前秒数。

本文件不修改 Formal P2、Formal rho、D1/B witness、Gate、Protocol Lock、正式实验配置或历史结果。

## 2. 符号和三层状态

源事件条件的场景/实验分配为 \(Z_S\)，实际源事件状态为 \(S^*\)。通信策略分配为 \(Z_C\)，实际策略执行状态为 \(C^*\)。观测或派生记录使用波浪号，例如 \(\widetilde X\)、\(\widetilde T_P\)。

物理状态和网络为

\[
G_P(t)=(V,E_P(t)),\qquad
X^*_{t+1}=F_P(X^*_t,U^*_t,G_P^*(t),\xi_t;H,S^*,C^*).
\]

每条物理交互边 \(e^P_{ij}\) 必须带有方向、起止时间、车辆身份、交互类型、状态证据、质量和来源版本。

## 3. Source Event A 路线：Formal P2

### 3.1 不变的正式定义

A 路线沿用现有版本化实现和配置：

- 可靠正闭合 TTC；
- TTC 阈值 < 2.0 s；
- 最小持续时间 0.2 s；
- 最大观测间隔 0.11 s；
- \(\rho(TTC)=\exp(-TTC/\tau_s)\)；
- 未知贡献保留 [0,1]；
- 事件确认遵循现有 event_confirm_s 语义。

本任务不改变任何阈值、\(\tau_s\)、合并规则或缺失策略。Formal P2 是风险代理事件，不等于事故或碰撞。

### 3.2 判定阶段

对事件候选 \(k\)，保留以下不同时间和状态：

1. **首次合格观测时间** \(t_{\mathrm{obs},k}\)：第一条满足身份、质量、TTC 和连续性要求的观测；
2. **事件确认时间** \(t_{\mathrm{confirm},k}\)：持续性和观测间隔要求实际满足的时间；
3. **可用消息生成时间** \(T_G\)：仅在 source event 已按研究协议确认后才可生成；不能用首次候选代替确认；
4. **退出/删失状态**：阈值退出、身份切换、连续性断裂、观测结束、质量失效或未知。

现有 formal_risk_measurement.py 已将 event_confirm_s 和 message_earliest_generation_s 分开记录。消息链不应引用尚未确认的候选事件。

### 3.3 最小 A 路线记录

| 字段 | 含义 |
|---|---|
| event_id | 稳定源事件键 |
| run_id、assignment_id | 运行和分配键 |
| source_vehicle_id、leader_vehicle_id | 源/前车身份 |
| t_obs、event_confirm_s | 首次合格观测和实际确认 |
| event_location | 仿真坐标、道路、车道和版本 |
| ttc_threshold_s、minimum_duration_s、max_gap_s | 版本化配置快照 |
| event_quality、measurement_status | 质量和可用性 |
| exit_reason、missing_reason | 失败、删失或未知原因 |
| source_sha256、algorithm_version | 证据和算法追溯 |

### 3.4 A 路线失败处理

- 没有任何合格观测：no_formal_p2，不生成 source message；
- 有候选但未达到持续性：candidate_unconfirmed，保留候选，不称为 Formal P2；
- 观测缺口跨越可能的确认时段：Unknown 或区间，不补零、不向前倒写；
- 身份、时钟或连续性失败：事件资格 Unknown；
- SUMO 当前源 P2 为零：保留零结果，不降低阈值、不重定义 Formal P2。

## 4. Source Event B 路线：安全受控扰动机制域

B 路线可以在 SUMO 中研究“外生受控扰动—消息—控制器—物理状态”的机制，但必须使用独立命名空间和 source_type=controlled_perturbation。

最小记录包括：

- perturbation_assignment_id：扰动分配；
- planned_perturbation_time：计划时间；
- actual_perturbation_time：实际执行时间；
- source_vehicle_id、扰动动作和执行反馈；
- 扰动强度、持续时间和安全边界；
- 扰动执行失败、延迟、覆盖或中止；
- 与 \(S^*\)、\(Z_C\)、\(C^*\) 的关联键。

B 路线不能写成自然风险事件、Formal P2 或现实物理源事件。它支持模型内机制、必要条件、失败边界和测量接口研究；若需要把 B 解释为 A 或现实事件，必须另有研究者决定和证据。

## 5. Physical Propagation 的时变路径定义

定义时变有向物理图

\[
G_P(t)=(V,E_P(t)).
\]

对每条候选边 \(e^P_{ij}\)，记录：

- 起点 \(i\)、终点 \(j\)；
- 交互类型（跟驰、减速响应、换道冲突、邻近状态传递等）；
- 有效时间区间 \([t_{\mathrm{start}},t_{\mathrm{end}}]\)；
- 车辆身份和 leader 连续性；
- 状态证据（速度、加速度、净间距、相对速度或其他已批准状态）；
- 采样间隔、时钟、质量、缺失和来源版本。

### 5.1 三类路径状态

1. **Potential Physical Path**：由道路/车道/相邻关系推导的候选路径，只表示可能性；
2. **Observed Physical Interaction**：至少有轨迹、身份和状态记录支持的实际边；
3. **Qualified Physical Propagation Witness**：满足路径连续性、时间顺序、状态证据、质量和竞争解释审查的路径。

道路连通、空间相邻、同车有序轨迹或同一 leader 标签都不能单独升级为 Qualified Witness。

### 5.2 Time-respecting path

从源车辆 \(v_0\) 到目标车辆 \(v_K\) 的时间可达路径需要存在

\[
(v_{r-1},v_r,e_r,t_r),\quad
t_{r+1}\geq t_r,\quad
e_r\in E_P(t_r),
\]

并且每条边的身份、时间、状态和质量证据都满足规则。路径中断、leader 切换、身份跳变、重大缺口或未解释的外部源会使整条路径降为 Unknown 或不合格。

## 6. Physical Arrival \(T_P\)

### 6.1 一般定义

以源事件时间锚点 \(t_E\) 为起点，定义

\[
T_P=
\inf\left\{
t\geq t_E:
\phi\!\left(X^*_{\mathcal T}(t),B_{\mathcal T}\right)=1
\ \text{并满足预设持续性}
\right\},
\]

其中 \(B_{\mathcal T}\) 是处理前基线或无消息参考，\(\phi\) 是物理状态判定函数。具体 \(\phi\)、阈值、持续时间和路径资格仍由研究者在 P2 后续工作中确定。

### 6.2 候选物理状态函数

| 候选 | 物理含义 | SUMO 可观测性 | 主要限制 | 当前建议 |
|---|---|---|---|---|
| 相对基线的速度变化 | 目标区域整体运动状态偏离 | 高 | 容易受背景流、边界和控制策略影响 | **首选候选**；需独立基线和持续性 |
| 跟驰净间距变化 | 物理交互的局部状态变化 | 高 | 依赖参考点、车辆长度和 leader 连续性 | 路径辅助，不单独代表区域到达 |
| 局部密度变化 | 区域宏观状态变化 | 中 | 少车/短窗口离散、边界流入流出 | 区域辅助 |
| Formal rho/P2 | 风险状态或事件状态 | 高 | 与区域风险终点解释依赖，可能循环 | 只作辅助，不直接替代 \(T_P\) |

建议优先在不依赖 Formal rho/P2 的状态函数上定义 \(T_P\)，再以 Formal 风险作为辅助一致性证据。不能因为某个指标容易得到就把它写成唯一物理真值。

### 6.3 阈值、持续性和恢复

一般形式可写为

\[
\phi(X^*_{\mathcal T}(t),B_{\mathcal T})
=
\mathbf 1\left[
g(X^*_{\mathcal T}(t),B_{\mathcal T})\geq \theta_P
\right].
\]

需要预先规定：

- 基线 \(B_{\mathcal T}\) 的来源；
- 阈值 \(\theta_P\) 和误差容限；
- 连续持续时间 \(h_P\)；
- 最大允许观测间隔 \(q_P\)；
- 恢复后是否允许第二次到达；
- 多个源事件同时存在时的归属；
- 观察结束和状态缺口的处理。

这些参数不能沿用 Formal P2 的 2.0 s/0.2 s/0.11 s，除非研究者另行确认两套定义等价；当前不作此假设。

### 6.4 时间状态和删失

必须区分：

- onset interval：首次满足阈值的真实 crossing 所在区间；
- confirmation time：持续性得到确认的时间；
- arrival interval：考虑采样、时钟和检测误差后的区间；
- right_censored：观测截止仍未达到；
- interval_censored：缺口横跨可能到达时段；
- Unknown：身份、路径、时钟或质量不足以判断。

持续性确认时间不能倒写成原始 onset。消息处理组的轨迹不能直接改名为 no-message 物理反事实。

## 7. 物理路径与到达联合资格

一个目标区域的物理到达记录只有在以下条件同时满足时，才可标记为 qualified_physical_arrival：

1. 目标区域状态函数 \(\phi\) 达到预定条件并通过持续性；
2. 存在从源到目标的 time-respecting Qualified Physical Propagation Witness；
3. 路径时间顺序、身份和状态证据连续；
4. 时钟、采样和质量足以给出到达区间；
5. 没有未记录的重大缺口、独立源或外部控制使路径归属不可辨识。

若区域状态满足但路径不合格，结果是 state_observed_path_unknown；若路径合格但状态未达到，结果是 path_observed_arrival_not_confirmed；两者都不能写成确定 \(T_P\)。

## 8. 竞争解释

以下解释必须作为路径归因的审查项保留：

- 原有拥堵、排队或瓶颈；
- 道路几何、信号和边界流变化；
- 其他独立风险源；
- 非源车辆的控制或动作；
- 目标区域本来就存在的状态趋势；
- 观察质量、身份切换和时钟缺口。

本任务不对这些竞争解释做新的因果实验，但它们必须进入 alternative_explanation_status，不能因路径时间顺序满足就自动排除。

## 9. SUMO Read-only Observer 最小证据契约

Observer 必须只读 SUMO 状态，不生成消息、不转发、不参与 Adoption、不修改车辆动作，也不改变仿真演化。它记录模型内真实状态的可复核视图，并保留观测质量。

最小字段：

| 字段组 | 最小字段 |
|---|---|
| 运行/身份 | run_id、pair_id、event_id、assignment_id、source_vehicle_id、vehicle_id、leader_id |
| 区域/窗口 | target_cohort_id、region_id、window_version |
| 时间 | simulation_time、step_index、clock_id、clock_unit |
| 运动状态 | position、speed、acceleration、lane、net_gap、相对速度 |
| 物理边 | physical_edge_id、起止车辆、交互类型、有效区间 |
| 事件/到达 | t_obs、event_confirm_s、arrival_onset_interval、arrival_confirmation_time |
| 质量/缺失 | measurement_status、quality_status、missing_reason、删失类型 |
| 版本/追溯 | observer_version、scenario_version、algorithm_version、source_sha256 |

稳定关联键必须支持

\[
\text{event\_id}\rightarrow\text{assignment/run}
\rightarrow\text{vehicle/track}\rightarrow\text{region/window}.
\]

Observer 不提供 no-message 反事实。普通物理到达分布应来自 \(Z_C=0,Z_S=1\) 的随机或预定无消息运行：

\[
F_0(t\mid H,Z_S=1)
=P\{\widetilde T_P\leq t\mid Z_C=0,Z_S=1,H\}.
\]

该分布与消息处理组轨迹的独立性、删失和适用域必须分开报告。

## 10. 当前推荐与未决事项

### 推荐

1. A 路线保持 Formal P2 原定义，用于资格清晰的风险源事件；
2. B 路线仅作为安全受控扰动机制域；
3. 物理传播使用 time-respecting path 和三层 witness 状态；
4. \(T_P\) 首选相对基线的持续速度状态，净间距/密度作路径或区域辅助，Formal rho/P2 不直接定义到达；
5. SUMO Observer 采用最小字段契约，所有缺失和删失显式保留；
6. 物理到达参考优先使用 \(Z_C=0,Z_S=1\) 的无消息运行分布，不把消息处理轨迹当作反事实。

### Awaiting Researcher Decision

- A/B 的具体 SUMO 场景和源事件实例；
- \(t_E\) 最终科学时间锚点；
- \(\phi\)、\(\theta_P\)、\(h_P\)、\(q_P\) 和恢复规则；
- 物理路径最终准入标准；
- 时钟误差、缺失比例和正式统计准入；
- 目标区域的最终成员和边界。

本任务不自动冻结上述参数。

## 11. P2 Task2 进入条件

P2 Task1 已形成可供 P2 Task2 使用的 A/B 源事件框架、时变物理路径记录、物理到达候选和 Observer 最小契约；因此具备进入 P2 Task2 的文档准备条件。Formal P2 源事件数量、合格物理 witness、最终 \(\phi\) 参数和真实/模型适用域仍未关闭，不能把“可进入下一项定义工作”写成 Gate 通过或实验授权。\n