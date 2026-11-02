# P2 Task2 研究者决策记录：物理到达与 No-Message Reference

日期：2026-11-02
状态：`COMPLETED_WITH_LIMITATIONS`；本文件登记本轮 Fact、Inference、Proposal 和 `Awaiting Researcher Decision`，不把 Codex 推荐写成 Agreed。

## 1. 沿用的已确认方向

以下方向来自 P1 Task2 和 P2 Task1，属于当前项目既有事实或已确认研究范围：

- SUMO 是当前优先平台，结论限定为模型内，不能写成现实交通因果证据。
- Formal P2 是 Source Event A 路线；安全受控扰动是独立 B 机制路线。
- 目标 cohort、region、window 原则上在处理前固定。
- 信息传播链和物理传播链分开；Observer 只读，不参与消息、采用或控制。
- 首版只研究总体层面的时间优先性，不识别单个处理事件的跨世界提前秒数。
- 当前主分析保留 source-present 两臂 ITT，最终四格设计仍然需要完成。
- \(Z_S/Z_C\) 是分配变量，\(S^*/C^*\) 是实际状态；消息发送失败属于消息分配臂的实际失败状态。
- Formal rho/P2 保持既有定义；它不是本任务的物理到达主定义。
- 本轮不运行 SUMO/TraCI、Pilot、正式实验，不读取 locked holdout，不生成 Protocol Lock，不启动 Stage 1.1。

## 2. 本轮形成的 Proposal 总表

| 决策事项 | Fact | Inference | Codex Proposal | 推荐理由 | 状态 |
|---|---|---|---|---|---|
| \(t_E\) | onset、confirmation、generation eligibility 是不同时间 | 确认可能晚于真实物理传播 | A 路线物理主分析使用 `source_onset_interval`；信息链使用 `t_S,confirm`；B 路线使用 actual perturbation time | 避免把物理传播的人为确认延迟误写成真实起点 | Awaiting Researcher Decision |
| 物理传播方向 | 车辆方向、道路坐标、物理边、宏观波前可不一致 | 跟驰影响可能向上游，宏观波方向取决于状态 | 字段分开；方向由关系与数据确定，不硬编码上游 | 便于处理自由流、排队、汇入和信号场景 | Awaiting Researcher Decision |
| 主要路径类型 | Task1 已有 Potential/Observed/Qualified 三层 | 拓扑或邻近不能证明响应 | 第一版以同车道纵向 leader/follower 为主要 Qualified 候选，复杂交互单列 | 证据链最短且可审计 | Awaiting Researcher Decision |
| Qualified 准入 | 需要时间、身份、状态、质量、竞争解释 | 同一 leader 标签不足以闭合路径 | 每条边需源变化→目标响应的有序区间，稳定身份/关系和竞争解释审查 | 防止路径自动升级为因果证明 | Awaiting Researcher Decision |
| \(\phi\) 主函数 | 速度、gap、density 可观测 | 区域速度更接近总体状态；风险定义会循环 | 固定 cohort 上等车辆有符号平均速度下降为主；median、分位数、超阈值比例为辅助 | 有方向、可计算、与区域总体和既有聚合相容 | Awaiting Researcher Decision |
| Baseline | Physical baseline 与 no-message 分布用途不同 | no-message 可能已有普通物理传播 | 同运行 pre-onset baseline 主用；no-message 只用于 \(F_0\)/背景敏感性 | 避免把普通传播参考当作无物理状态 | Awaiting Researcher Decision |
| Source qualification 顺序 | \(S^*\) 可能受分配顺序影响 | 若通信先分配，条件化 \(S^*=1\) 可能是 post-treatment | 先确认源事件，再随机化 \(Z_C\)，随后生成/关闭消息 | 使 source-present no-message 总体更可解释 | Awaiting Researcher Decision |
| No-message 主参考 | \(Z_C=0,Z_S=1\) 与 source-absent/失败不同 | 只有 source-present no-message 回答普通物理到达 | 方案 A 独立随机化 no-message 为主；方案 B SUMO 配对为辅助 | 保留总体识别，避免 seed 配对被过度解释 | Awaiting Researcher Decision |
| Censoring | right、interval、Unknown 语义不同 | 缺口不等于未到达 | 按状态分别记录；区间方法处理 interval；KM 仅在删失独立时使用 | 避免中点和普通 KM 造成偏差 | Awaiting Researcher Decision |
| Clock | 采样、offset、漂移和检测误差可扩大区间 | 时间区间重叠无法证明先后 | 保留误差并传递到 \(T_R/T_P\)，重叠返回 Unknown | 保留时间优先性证据边界 | Awaiting Researcher Decision |

## 3. Source Event 时间顺序的研究者决策接口

### 3.1 当前推荐

对 Formal P2 A：

\[
t_{S,onset}\in[L_S,U_S],\qquad
t_{S,confirm}\ge t_{S,onset},\qquad
T_{G,eligible}\ge t_{S,confirm}.
\]

实际生成时间、delivery、verification、adoption 和 action 继续使用信息链字段。
物理到达的绝对时序使用 onset 区间；若需要从源到目标的 elapsed propagation，
使用区间算术而不是确认时间单点。

### 3.2 需要研究者冻结的内容

- onset crossing 需要的最小采样质量和允许缺口；
- onset 区间、clock uncertainty 和 detection uncertainty 的合成规则；
- confirmation 之前出现目标状态变化时的报告分类；
- B 路线 actual perturbation 的状态确认字段和失败/延迟边界；
- 是否保留 confirmation-anchored 结果作为正式敏感性分析。

## 4. Physical Propagation 方向和路径准入

### 4.1 推荐的方向表示

同一条边同时保存：

- `vehicle_travel_direction`；
- `road_coordinate_name` 与空间符号；
- `from_vehicle_id → to_vehicle_id` 的候选影响方向；
- `macro_front_direction`（只在宏观辅助层存在）。

如果 `s` 沿车道行驶方向增加，前车减速到后车响应的物理影响可能对应负的
`Δs`；这只是一个几何实例。所有宏观方向都必须由固定空间单元的状态 crossing
或前沿斜率估计，不能默认“交通波总是向上游”。

### 4.2 第一版 Qualified Witness Proposal

边级必须有：

1. source state change interval；
2. target response interval；
3. source/target identity continuity；
4. leader/follower 或其他 interaction type 的有效区间；
5. speed/acceleration/net gap/relative speed 状态证据；
6. clock、sampling、quality 和 missing 审计；
7. alternative explanation review；
8. 与固定 region/cohort/window 的连接。

路径级必须每一跳满足时间可达和质量要求。任何关键区间重叠、身份跳变、leader
切换无显式 transition edge、多源竞争不可区分或复杂交互缺少方向/响应证据，
均保持 `Unknown` 或降为 Observed。

Qualified Witness 是证据门槛，不是自动因果证明。

### 4.3 需要研究者冻结的内容

- 同车道纵向边是否是第一版唯一主路径类型；
- 关系稳定、响应方向和竞争解释的具体准入规则；
- leader 切换和身份重识别的最长可接受缺口；
- 多条路径、多源事件和复杂交互的汇总规则；
- 宏观波前是否只作为描述性辅助，还是进入联合证据表。

## 5. \(\phi\)、Baseline 与 cohort 的研究者决策接口

### 5.1 推荐的主函数

对固定 cohort 的有效观测子集 \(I_t\)，令

\[
d_i(t)=b_i(t)-v_i^{obs}(t),\qquad
g_v^{mean}(t)=\frac{1}{|I_t|}\sum_{i\in I_t}d_i(t).
\]

主候选为

\[
\phi_v(t)=1[g_v^{mean}(t)\ge\theta_P]
\]

并要求预先定义的持续时间、最大观测间隔、coverage 规则和恢复规则。

这是一项 Proposal。中位数、偏差分位数和超阈值比例用于敏感性；绝对偏差只
作为双向状态的辅助，不作为主方向指标。净间距和密度记录为路径/区域辅助，
Formal rho/P2 只作独立风险一致性证据。

### 5.2 Baseline 的推荐层次

1. 主：同一运行、source onset 之前的固定窗口；
2. 敏感性：source-present no-message 的匹配状态；
3. 辅助：其他处理前匹配状态或固定空间背景。

No-message 运行可能包含普通物理传播，因此不能被直接称为“无扰动物理状态”。

### 5.3 Fixed cohort 与动态区域

主聚合只使用处理前固定的车辆/角色集合。车辆离开区域时保留其缺失/离开状态，
不由处理后进入车辆补位；区域动态占用另作辅助表。coverage 下降到未批准阈值
以下时，状态为 `state_unobserved`/区间/Unknown，不补零、不删除分母成员。

### 5.4 需要研究者冻结的内容

- \(g_v^{mean}\) 是否接受为主函数；
- baseline 窗口、趋势处理和车辆等权规则；
- \(\theta_P,h_P,q_P\)、coverage 和 recovery；
- 车辆进出区域、缺失分母和动态占用的正式规则；
- 是否在主报告中同时给 median、quantile、proportion 和 gap/density。

## 6. No-Message Reference 的研究者决策接口

### 6.1 主方案 A

在 source-present 适用总体中，先完成通信盲的源事件确认，再随机分配
`Z_C=0/1`。`Z_C=0` 运行提供

\[
F_0(t\mid H,Z_S=1,S^*=1)
\]

的总体参考。delivery failure、verification failure 和 controller rejection
仍然留在 `Z_C=1` 分配组。

### 6.2 辅助方案 B

SUMO 同初态、同配置、同外生随机流的配对运行只支持模型内辅助解释。必须审计
随机数调用顺序和分支后随机性；相同 seed 不自动形成逐事件反事实配对。

### 6.3 需要研究者冻结的内容

- 现实/模型场景是否能够先确认源再随机通信；
- 若不能，是否接受 assignment-level ITT 或 principal-strata 限制；
- no-message arm 的泄漏审计、positivity 和 exposure mapping；
- 配对反事实是否仅保留为工程诊断；
- source-absent 四格是否只作背景/interaction 对照，不纳入 \(F_0\)。

## 7. Censoring 和 Clock 的研究者决策接口

### 7.1 状态语义

| 状态 | 允许的解释 |
|---|---|
| `right_censored` | 完整观察到截止仍未达到 |
| `interval_censored` | crossing 被可靠限制在一个时间区间 |
| `unknown` | 身份、路径、时钟或质量不足，不能判断 |

### 7.2 统计边界

- 精确完整事件可用经验 CDF；
- 右删失只有在条件独立假设合理时才用普通 KM/生存估计；
- 区间删失使用相应的 interval-censored 方法；
- 信息性缺失、竞争源和安全中止用界限/敏感性，不机械重分类；
- 时间误差进入 onset/arrival 区间；区间重叠时不判定先后。

### 7.3 需要研究者冻结的内容

- 允许的观测缺口和质量门槛；
- clock offset/drift/detection uncertainty 的上界或分布；
- 主分析的删失估计器、界限和敏感性场景；
- `Unknown` 的报告格式和是否设最低可评价比例；
- \(T_R^{upper}<T_P^{lower}\) 的同时置信和持续性配套规则。

## 8. 明确不构成研究者决定的事项

以下内容虽然在本轮给出推荐，但没有被登记为 Agreed：

- 任何 \(\theta_P,h_P,q_P\)、coverage、恢复时间、分位数或时钟数值；
- 任何新的 SUMO 场景、seed、实验臂或运行矩阵；
- 将 B 事件升级为 Formal P2；
- 将宏观波前算法直接作为 AAD 物理因果判据；
- 将 Task9/Task19 局部响应写成网络传播；
- 将当前零 Formal P2 结果解释为物理传播不存在。

## 9. 下一步准入

下一任务只有在研究者审核至少以下事项后才能进入参数/接口冻结：

1. A 路线 `t_E`、B 路线 actual time 语义；
2. 第一版 Qualified Witness 的路径和多源规则；
3. \(\phi\) 主指标及 baseline/cohort/coverage；
4. 源资格与通信随机化顺序；
5. no-message 主参考和 SUMO 配对辅助范围；
6. censoring/Unknown/clock 的质量门槛。

本记录不授权实验、代码、配置或 Gate 变更。
