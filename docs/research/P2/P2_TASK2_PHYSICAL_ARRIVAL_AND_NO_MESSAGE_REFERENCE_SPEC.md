# P2 Task2 物理到达与 No-Message Reference 操作规范

日期：2026-11-02
任务：P2-TASK2
状态：`COMPLETED_WITH_LIMITATIONS`
适用域：AAD 当前 SUMO 模型内定义工作；不构成现实交通因果证据、Protocol Lock 或实验授权。

## 1. 任务边界与结论摘要

本规范在 P2 Task1 的三层 Physical Witness、时变有向物理图和候选
\(T_P\) 定义上继续细化。它不修改 Formal P2、Formal rho/P2、D1/B witness、
现有四格设计、Gate、正式配置、生产代码或历史实验结果。

本轮形成的主要方法 Proposal 如下：

1. A 路线的物理传播以 Physical Source Onset 为首选时间锚点；source
   confirmation 只作为 Formal 资格和消息可用性的时间，保留为独立字段。
2. B 路线使用实际扰动时间，不使用 planned time 充当物理起点，也不改称
   Formal P2。
3. 物理交互边表示候选影响方向，不表示已证明的因果关系。第一版以同车道
   纵向 leader/follower 交互为主要 Qualified Witness 候选；换道、汇入和
   复杂横向交互单独编码。
4. 微观车辆交互路径与宏观交通波前是两个不同数学对象。微观路径优先用于
   AAD 第一版 witness，宏观波前作为辅助一致性证据。
5. \(\phi\) 的首选主指标是固定 cohort 上的等车辆权重、相对基线的有符号
   速度下降持续状态；中位数、速度偏差分位数、超阈值车辆比例、净间距和
   密度作为预先声明的辅助或敏感性指标。
6. Physical State Baseline 与 no-message physical arrival distribution 分开。
   主参考是 source-present 且通信策略关闭的随机化总体
   \(Z_C=0,Z_S=1\)，而不是消息组轨迹，也不是 source-absent 运行。
7. 在可行时，应先由通信盲的 Observer 确认合格源事件，再分配通信策略。
   这样 \(S^*\) 在 \(Z_C\) 之前确定，便于解释 source-present 两臂 ITT 和
   \(F_0\)。如果现有场景只能在运行开始分配 \(Z_C\)，则不得无条件对
   \(S^*=1\) 做处理后筛选。
8. 到达 onset、持续性 confirmation、观测时刻、时钟误差、right censoring、
   interval censoring 和 Unknown 分开记录。时间区间重叠时返回
   `Unknown / temporal precedence not established`，不得用中点强行排序。

以上均为 Proposal 或 Fact 的工程化整理，不自动变为 Agreed Research Decision。

## 2. Source Event 的三个时间锚点

### 2.1 Physical Source Onset

对 A 路线，\(t_{S,onset}\) 表示源事件对应的物理状态首次达到预先定义条件
的真实时间。采样不能定位精确 crossing 时，必须保存

\[
t_{S,onset}\in[L_S,U_S].
\]

若上一条可靠观测在阈值以下、下一条可靠观测在阈值以上，并且中间没有超过
允许的观测缺口，则至少保留该相邻观测区间和时钟/检测误差扩展。首次达到阈值
的观测时间只能是 `source_onset_observation_time`，不能自动写成物理起点。

如果缺口足以容纳多个不同的 crossing 过程，则区间只能作为候选范围；若身份、
质量或时钟也不能闭合，则状态为 `Unknown`，不以一个宽区间掩盖路径不可辨识。

### 2.2 Source Confirmation

\(t_{S,confirm}\) 是 Formal P2 持续性、最大观测间隔、身份和质量条件全部满足，
事件正式取得资格的时间。它可以晚于物理 onset。首条合格观测、候选开始时间和
确认时间须分别保存：

| 字段 | 语义 | 可用于何处 |
|---|---|---|
| `source_onset_interval` | 物理起点的区间 \([L_S,U_S]\) | 物理传播起点和不确定性传播 |
| `source_observation_time` | 首次可审计合格观测时刻 | 观测审计，不是精确 onset |
| `source_confirmation_time` | 持续性真正完成的时刻 | Formal 资格、消息生命周期 |
| `source_confirmation_status` | confirmed / candidate_unconfirmed / censored / unknown | 资格和失败分类 |

不得为了让物理链和信息链时间相同而把 confirmation 倒写成 onset，也不得因为
onset 早于 confirmation 就把候选事件提前写成 Formal P2。

### 2.3 Message Generation Eligibility

\(T_{G,eligible}\) 是消息生成最早允许发生的时间。沿用 P2 Task1 约束：

\[
T_{G,eligible}\ge t_{S,confirm}.
\]

实际消息生成时间还要另记处理排队、版本检查、过期、发送和失败状态；
\(T_{G,eligible}\) 不是物理到达时间。消息链应使用 confirmation，物理链优先
使用 onset 区间。两条链的时间轴可以共享时钟，但不共享语义。

### 2.4 \(t_E\) 的推荐和敏感性

**推荐 Proposal：** A 路线主分析将物理起点写成 `source_onset_interval`，并以
真实绝对时钟比较区域风险 onset 与目标区物理到达。若必须报告相对传播滞后，
使用区间算术；设目标区 onset 区间为 \([L_A,U_A]\)，则

\[
\Delta_P=t_{A,onset}-t_{S,onset}
\in [L_A-U_S,\;U_A-L_S],
\]

在区间不保证正值时报告顺序 `Unknown`。用 confirmation 作为物理起点只能作为
明确标记的敏感性分析或证据受限 fallback，因为它可能遗漏 confirmation 之前已经
发生的物理传播，并系统性压缩物理传播时长。

对 B 路线保存：

| 字段 | 语义 |
|---|---|
| `planned_perturbation_time` | 计划执行时刻 |
| `actual_perturbation_time` 或区间 | 实际状态改变发生的时刻 |
| `execution_delay` | 计划与实际之间的差异 |
| `execution_status` | executed / delayed / failed / aborted / unknown |

B 路线只用 actual time 作为物理锚点。计划时间可以用于执行审计，不能替代实际
扰动时间，也不能将 B 事件重命名为 Formal P2。

## 3. 物理传播对象与方向语义

### 3.1 四个方向不能互换

AAD 同时保留四种方向：

1. **车辆行驶方向**：车辆速度在车辆自身路线或道路切向坐标上的方向。
2. **道路空间坐标方向**：研究者选择的道路坐标增加方向，例如沿 route 的
   `s` 增加方向；它可能与某一车道的行驶方向相反或在交叉口不连续。
3. **物理影响方向**：候选源状态改变到目标车辆响应的有向关系。
4. **宏观波前方向**：速度、密度或流量状态前沿在空间—时间图中的运动方向，
   由观测到的前沿斜率或状态转移估计。

纵向跟驰中，前车减速后后车响应是常见候选边。若道路 `s` 沿车辆行驶方向
增加，前车在空间上通常位于后车的较大 `s` 一侧，因此“前车影响后车”可能
对应负的空间方向，即向上游；但这只是该几何和关系下的候选语义，不能写成
所有交通扰动都向上游传播。自由流、排队消散、匝道汇入、信号控制和复杂瓶颈
可以产生不同的宏观方向。

宏观波前方向必须从固定空间网格的状态变化估计，例如前沿位置 \(s_f(t)\) 的
变化或多个空间单元的有序 crossing。不能从单个车辆 leader/follower 标签直接
推出宏观波速，也不能用宏观波前的上游移动反推每一条微观边已经具有因果关系。

### 3.2 微观路径与宏观波前

**Micro-level Interaction Path** 以车辆为节点、以候选影响边为有向边，记录
leader/follower 关系、源状态变化、目标响应、净间距、相对速度和身份连续性。
它回答“哪辆车的哪种状态变化之后，哪辆车出现了可审计响应”。

**Macro-level Propagation Front** 以道路空间坐标和时间为轴，记录速度、密度、
占用或其他交通状态的前沿。它回答“一个聚合状态改变在空间上如何移动”。

两者的证据关系是：微观路径可以解释宏观前沿的一部分车辆响应，宏观前沿可以
检查微观路径集合是否呈现一致的空间—时间结构；二者不是同一个图、同一个节点
集合或同一个因果对象。AAD 第一版应以微观路径作为主要 Qualified Witness，宏观
波前只作辅助证据和方向敏感性分析。若只有宏观前沿而无身份连续的微观边，保留
`macro_front_observed_micro_path_unknown`。

### 3.3 时变有向物理图

沿用 P2 Task1：

\[
G_P(t)=(V,E_P(t)).
\]

每条边的方向是候选影响方向，不是自动成立的因果箭头。建议将关系和几何符号
分别记录，避免把 `leader_to_follower`、`vehicle_travel_direction` 和
`space_coordinate_sign` 混在一个字段中。

物理边的最小审计字段为：

| 字段 | 记录内容 |
|---|---|
| `physical_edge_id` | 稳定边键和版本 |
| `from_vehicle_id` / `to_vehicle_id` | 候选影响源和候选响应目标 |
| `interaction_type` | longitudinal_following / lane_change / merge / queue / other |
| `lane_id`、`leader_follower_relation` | 车道和关系快照/有效区间 |
| `road_position`、`road_coordinate_name` | 位置和坐标定义 |
| `influence_direction` | 候选影响方向及其空间符号 |
| `interaction_time_interval` | 关系成立区间 |
| `source_state_change_interval` | 源状态改变区间 |
| `target_response_interval` | 目标响应区间 |
| `speed`、`acceleration`、`net_gap`、`relative_speed` | 直接或声明规则派生的状态 |
| `identity_continuity` | stable / reconciled / broken / unknown |
| `quality_status` | 轨迹、采样、数值和时钟质量 |
| `clock_uncertainty` | 时钟 ID、offset、漂移和残差界限 |
| `alternative_explanation_status` | reviewed / unresolved / competing_source / unknown |
| `edge_status` | potential / observed / qualified / rejected / unknown |

## 4. Qualified Physical Propagation Witness 准入

### 4.1 证据层级

| 证据 | 最低含义 | 允许的状态 |
|---|---|---|
| 道路拓扑或车道连通 | 存在可能的空间路线 | Potential Path |
| 空间邻近或同时占用 | 车辆可能互相影响 | Potential / candidate observed |
| 实际轨迹、身份和关系记录 | 观察到一条交互边 | Observed Interaction |
| 实际交互 + 后续有方向响应 + 时间/质量/竞争解释审查 | 支持物理传播归因的证据资格 | Qualified Witness |

道路连通、空间相邻、轨迹先后、相同 leader 标签或单次速度相似，任何一项都
不能单独升级为 Qualified。

### 4.2 第一版准入条件

一条边和由其组成的路径只有在以下条件同时满足时才可标记 `qualified`：

1. **源资格**：起点是 Formal P2 A 的已确认事件，或 B 路线的实际执行扰动；
   失败、候选未确认和身份未知的源只能产生 `unknown` 或 `rejected` 路径。
2. **交互类型适用**：第一版优先同车道纵向 leader/follower。换道、汇入、
   交织、信号或边界流导致的状态变化必须使用独立 `interaction_type`，不能
   仅凭邻近关系自动升级。
3. **时间顺序**：每一跳都有源状态变化和目标响应的有序区间。若
   `source_state_change_interval` 与 `target_response_interval` 完全重叠，
   不能确定先后，整条边的物理归因保持 `Unknown`；不能用区间中点排序。
4. **状态响应**：目标在预声明的响应规则下出现方向一致的状态改变，例如相对
   基线的速度下降、加速度改变或净间距响应。单纯同向移动、共同受信号影响或
   同时进入区域不构成响应证据。
5. **身份连续性**：源和目标身份在交互区间内可追踪，重复、丢帧、重识别或
   车辆 ID 合并均有审计记录。不能以最近空间位置自动填补身份。
6. **关系连续性**：leader/follower 关系在边的有效区间内稳定，或存在独立
   验证的关系转移记录。中间出现无解释的关系断裂，路径降为 `Unknown`。
7. **时钟和采样质量**：观测间隔、时钟 offset/漂移、位置/速度质量满足本轮
   预先声明的质量门槛，并足以给出到达区间；参数尚未冻结前只记录候选，不
     把当前观察直接标为正式 qualified。
8. **竞争解释审查**：原有排队、瓶颈、信号、边界流、其他源车辆、控制器动作
   或数据缺口不能独立解释目标响应；无法排除时保留 `unresolved`。
9. **路径闭合**：从源到目标的每一跳均满足上述条件，并满足
   \(t_{r+1}\ge t_r\)。中间节点缺失、时序倒置或质量失败会使整条路径降级。
10. **区域连接**：目标车辆或目标区域状态属于预先固定的 cohort、region 和
    window；不能在看到状态变化后重新选车辆或边界。

Qualified Witness 表示“达到预定证据资格”，不是自动的现实因果证明。它仍需
与 no-message 参考、竞争解释和适用域一起报告。

### 4.3 身份切换、leader 切换与多条路径

- **身份切换**：在稳定身份无法与前后记录可靠拼接时，终止旧路径并新建
  `path_segment_id`；不允许把两个 ID 当成同一车辆继续传播。只有通过独立的
  轨迹重识别契约且残差在预定范围内，才可标记 `reconciled`，并保留原始 ID。
- **Leader 切换**：旧 leader→follower 边在切换时结束。新 leader 只能从切换
  时刻建立新边；是否可把源影响跨越切换传播，必须有显式的 transition edge、
  时间顺序和目标响应证据，不能继承旧边的资格。
- **多条候选路径**：保留全部通过局部质量审查的路径及其状态；不得事后只选
  最短、最近或最快的一条。摘要应报告 `candidate_path_count`、
  `qualified_path_count` 和 `attribution_status`。只有在运行前声明的规则下才
  可取最早合格到达。
- **多个独立源**：为每个源保存 source set 和路径集合。若多个源在目标响应前
  的有效区间重叠，且无法区分各源贡献，记录 `competing_source`，不强行归属
  给最近源或最早源。
- **区间重叠**：任何关键先后关系的上界和下界相交时，保留区间和 `Unknown`；
  不把区间中点当作观测事实。

## 5. Physical Arrival 状态函数 \(\phi\)

### 5.1 总体定义

对预先固定的目标 cohort \(\mathcal C_{\mathcal T}\)、目标区域
\(\mathcal T\)、观察窗口和 baseline \(B_{\mathcal T}\)，沿用

\[
T_P=\inf\left\{t\ge t_E:
\phi\!\left(X^*_{\mathcal T}(t),B_{\mathcal T}\right)=1
\ \text{并满足预设持续性}\right\}.
\]

建议在记录层明确区分：

- `arrival_onset_interval`：第一次状态 crossing 的真实时间区间；
- `arrival_confirmation_time`：持续性条件被后续观测确认的时刻；
- `arrival_observation_time`：第一次观测到阈值状态的采样时刻；
- `arrival_status`：arrived / right_censored / interval_censored / unknown。

\(T_P\) 的科学比较优先使用 onset 区间；confirmation 只提供“到达已被证实”的
审计时点。不能把 confirmation 倒写成 onset。

### 5.2 速度状态候选的比较

设 \(I_t\) 是在时刻 \(t\) 同时属于预先固定 cohort、满足区域定义且有有效
状态观测的车辆集合，\(b_i(t)\) 是 baseline 下的参考速度，
\(v_i^{obs}(t)\) 是观察速度，定义

\[
d_i(t)=b_i(t)-v_i^{obs}(t).
\]

候选函数为：

| 候选 | 计算 | 解释 | 建议 |
|---|---|---|---|
| 有符号速度下降 | \(g_v^{mean}(t)=|I_t|^{-1}\sum_{i\in I_t}d_i(t)\) | 区域典型速度低于 baseline，正值代表减速 | **主候选 Proposal**；与区域总体和现有等车辆聚合一致 |
| 中位速度偏差 | \(g_v^{med}(t)=\operatorname{median}_{i\in I_t}d_i(t)\) | 对少数异常车辆更稳健 | 预声明敏感性，不替代主候选 |
| 偏差分位数 | \(g_v^{(p)}(t)=Q_p\{d_i(t)\}\) | 观察区域中较慢或较快尾部 | 只在研究者预先指定 \(p\) 后使用 |
| 超阈值比例 | \(g_v^{prop}(t)=|I_t|^{-1}\sum_i1[d_i(t)\ge\delta_v]\) | 受影响车辆覆盖率 | 辅助；\(\delta_v\) 另需校准 |
| 绝对速度偏差 | \(g_v^{abs}(t)=|\bar v^{obs}(t)-\bar b(t)|\) | 检测双向变化 | 敏感性；丢失“减速/加速”的方向解释 |

**首选 Proposal** 是等车辆权重的有符号平均速度下降，并用中位数和超阈值
比例检查异常值和局部扩散。原因是平均值保留区域总体状态含义，且与现有
Formal 风险的车辆等权聚合较容易对齐；中位数虽更稳健，但可能隐藏受影响车辆
比例的变化；绝对偏差会把加速和减速合并。该选择仍待研究者确认。

速度变化不是唯一物理状态。建议同时记录但不直接定义主 \(T_P\)：

- `net_gap_change`：需要车辆长度、参考点、leader 连续性和几何校准；
- `local_density_change`：需要固定空间单元、边界进出和占用定义；
- Formal rho/P2：保留为风险一致性或路径辅助，不直接当作物理到达，避免
  物理到达和区域风险终点循环定义。

### 5.3 参数化 \(\phi\) 和恢复规则

写成统一形式：

\[
\phi(X^*_{\mathcal T}(t),B_{\mathcal T})
=\mathbf 1\left[g(X^*_{\mathcal T}(t),B_{\mathcal T})\ge\theta_P\right].
\]

每个候选函数都必须携带：

- \(\theta_P\)：与所选 \(g\) 单位一致的状态阈值；
- \(h_P\)：状态连续满足阈值所需的持续时间；
- \(q_P\)：允许的最大观测间隔；
- baseline definition 和 baseline estimation window；
- cohort coverage rule；
- recovery rule 和是否允许第二次到达。

这些参数不能直接复用 Formal P2 的 TTC<2.0 s、0.2 s 持续时间或 0.11 s
最大间隔。它们回答不同的测量问题，除非研究者另行证明等价。建议采用
“首次持续合格 episode”作为主记录，并预先定义恢复条件（例如低于退出阈值
并持续足够时间）；恢复后的第二个 episode 另记，不根据结果选择最有利 episode。

### 5.4 Fixed cohort、动态占用和进出区域

P1 D4 要求 cohort、region 和 window 在处理前固定。实现上建议：

1. 预先建立固定车辆集合 \(\mathcal C_{\mathcal T}\) 或固定角色集合；
2. 每个时刻只在其有效观测子集 \(I_t\) 上计算，同时保存
   \(coverage_t=|I_t|/|\mathcal C_{\mathcal T}|\)；
3. 车辆离开区域后不以新进入车辆替换，也不把离开后的状态延长为仍在区域；
4. 新进入目标区的车辆可进入独立 `dynamic_occupancy` 辅助表，但不能改变
   主聚合 cohort；
5. coverage 低于预先定义的质量门槛时返回 `state_unobserved` 或区间/界限，
   不能把缺失车辆补成零偏差；
6. 若区域内车辆数变化本身是研究对象，应以固定空间区域的密度/流量辅助指标
   另行报告，不能把动态分母混入固定 cohort 的速度主指标。

这样可以避免处理后车辆迁移、离开或进入导致聚合对象改变。缺失机制若与处理、
安全覆盖或路径质量相关，简单删除车辆不能恢复识别；应保留缺失状态并做界限或
敏感性分析。

## 6. Physical State Baseline 与 No-Message Reference 的分离

### 6.1 Physical State Baseline

`Physical State Baseline` 用来判断目标区域状态是否偏离参考状态。候选来源有：

| Baseline | 作用 | 限制 |
|---|---|---|
| 同一运行的 source-onset 前窗口 | 与该运行的车辆、几何和时钟一致 | 需要预先确定窗口和趋势处理；不能外推不可见状态 |
| 匹配的 source-present no-message 运行 | 检查普通传播和背景趋势 | 可能已包含普通物理影响，不能当“无物理影响”状态 |
| 其他处理前匹配状态 | 检查跨运行可比性 | 需要明确匹配变量、支持域和独立性 |

**推荐 Proposal：** 主 \(B_{\mathcal T}\) 采用同一运行、source onset 之前的预定
窗口和固定 cohort 计算；source-present no-message 运行用于阈值/背景敏感性和
\(F_0\)，不被改名为同一运行的无扰动物理 baseline。若同一运行前窗口不足以
估计稳定趋势，应把 baseline 不确定性并入 \(\phi\) 的区间，而不是用消息组
实际轨迹补齐。

### 6.2 No-message 不是 No-source

四种分配和实际状态必须分开：

| 分配 | 含义 | 是否是主 \(F_0\) 参考 |
|---|---|---|
| `Source Present + Message Enabled` | \(Z_S=1,Z_C=1\) | 否，属于消息策略臂 |
| `Source Present + No Message` | \(Z_S=1,Z_C=0\) | **是** |
| `Source Absent + Message Enabled` | \(Z_S=0,Z_C=1\) | 否，source-absent 对照 |
| `Source Absent + No Message` | \(Z_S=0,Z_C=0\) | 否，背景/交互对照 |

消息臂中 delivery failure、verification failure、controller rejection 或
安全覆盖仍属于 \(Z_C=1\) 的分配组，并在 \(C^*\) 中记录失败类型。不能把它们
重新归入 no-message 组，也不能用 source-absent 运行代替 source-present
no-message 物理分布。

## 7. No-Message Physical Reference Design

### 7.1 参考分布

沿用 P1：

\[
F_0(t\mid H,Z_S=1)
=P\{\widetilde T_P\le t\mid Z_C=0,Z_S=1,H\}.
\]

在操作层还应记录 `source_eligibility_status` 和 `source_confirmation_time`。
当源事件资格在通信随机化前已经确定时，可写成更明确的 source-present 总体：

\[
F_0^{eligible}(t\mid H,Z_S=1,S^*=1)
=P\{\widetilde T_P\le t\mid Z_C=0,Z_S=1,H,S^*=1\},
\]

其中 \(S^*=1\) 是分配前条件，而非通信处理后的筛选变量。

### 7.2 主参考设计 Proposal：先确认源，再随机通信策略

当前优先路线是：

1. 在通信策略未作用前，由通信盲的 Formal P2 qualification/Observer 确认源
   事件资格；
2. 保存 \(t_{S,onset}\) 区间和 \(t_{S,confirm}\)，形成可审计的 \(S^*=1\)；
3. 在确认后、消息生成前随机分配 \(Z_C\)；
4. `Z_C=1` 进入消息生成和生命周期，`Z_C=0` 保持 source-present no-message；
5. 两臂使用同一固定 cohort、region、window、\(\phi\) 和 witness 规则；
6. 对 no-message 臂保留到达、删失、未知和竞争源记录，估计
   \(F_0(t\mid H,Z_S=1,S^*=1)\)。

此顺序使源事件资格不被通信策略的后处理状态污染，最接近 source-present 两臂
ITT 的定义。它要求源确认过程通信盲、随机化日志可追溯、随机化不会反过来改变
已确认源的定义，并且确认后到消息生成之间不存在未记录的物理或通信干预。

### 7.3 如果 \(S^*\) 在 \(Z_C\) 之后确定

若场景只能在运行开始分配 \(Z_C\)，而通信策略可能影响源事件是否达到 Formal
P2，则 \(S^*=1\) 是处理后变量。此时：

- 不能直接比较“消息组中实际合格源事件”与“无消息组中实际合格源事件”；
- 不能把未发生 Formal P2 的运行写成普通物理未到达；
- 需要回到 assignment-level ITT、四格设计、principal-strata 或明确的
  no-effect-on-eligibility 假设；
- 在没有这些假设时，\(F_0\) 只能作为条件描述或界限，不能宣称为 source-present
  因果参考分布。

这不是通过统计调整自动解决的问题。相关设计信息、源资格影响和未确认事件
必须保留在审计中。

### 7.4 识别条件和失败条件

主参考设计需要：

1. \(Z_C\) 在合格 source-present 总体内具有已知、非零的分配概率；
2. no-message 臂没有消息泄漏、旁路提示或控制器残留；
3. 源资格、背景分层 \(H\)、cohort/region/window 在分配前确定；
4. 两臂使用同一 arrival/witness 测量契约和时钟；
5. 目标车辆受到的物理干扰/网络暴露在设计中可描述，或将 estimand 限定为
   已声明的 exposure mapping；
6. 运行簇独立性和跨运行污染有审计；
7. outcome 质量、删失和 Unknown 规则不随结果事后改变。

以下任一情况会使主 \(F_0\) 不可直接估计：源事件确认数量为零、no-message
策略泄漏、source eligibility 被通信策略改变且未解决、物理路径或时钟缺失导致
大量 Unknown、或目标区域只覆盖处理后重新选择的车辆。

## 8. SUMO 配对反事实作为辅助参考

### 8.1 可复用条件

方案 B 可以在模型假设内配对同一处理前状态的消息和无消息路径，要求保存：

- 完全一致且 hash 绑定的初始位置、速度、车辆身份、背景、网络、需求和配置；
- 同一 SUMO/TraCI/controller/communication 版本；
- 分岔前相同的状态存档和外生输入；
- 明确的随机数流、子流、调用顺序和分支后重采样记录；
- 分支后的随机调用是否改变后续随机序列的审计；
- 每一对的初态相等性、分岔点、轨迹质量和失败状态。

### 8.2 相同 seed 的限制

相同 seed 只能表示初始化命名相同，不能自动证明两条轨迹具有逐事件有效的
反事实配对关系。若消息分支改变随机数调用顺序、车辆生成/换道/控制器分支或
后续采样，则从分岔点起两条路径可能使用不同的随机量。可行时应使用外生随机量
分区、固定随机流或显式调用日志；否则只将结果解释为模型中两条配置的分布比较。

方案 B 不能替代随机化 no-message 总体参考。它只支持：

- 模型机制的结构性检查；
- 同一模型假设下的路径和敏感性比较；
- 共同随机性在有效耦合成立时的精度改进。

它不能提供现实物理因果证据，也不能识别处理事件的同事件跨世界
\(T_P(0)\)。

## 9. 到达时间、删失与时钟不确定性

### 9.1 时间对象

Observer/分析表至少保留：

| 对象 | 含义 |
|---|---|
| `arrival_onset_interval=[L_A,U_A]` | 真实阈值 crossing 的可审计区间 |
| `arrival_confirmation_time` | 持续性确认时刻 |
| `arrival_observation_time` | 首次采样观测时刻 |
| `clock_id`, `clock_offset`, `clock_drift` | 时间来源和校准信息 |
| `detection_uncertainty` | crossing/状态检测误差界限或分布 |
| `right_censoring_time` | 完整观察到截止仍未达到的时刻 |
| `interval_censoring_bounds` | 缺口横跨可能达到区间 |
| `missing_reason`, `unknown_reason` | 身份、路径、时钟或质量失败原因 |

### 9.2 三类状态

- **Right censoring**：从源锚点到观察截止有连续、可评价的质量，但未发现合格
  到达。它表示“尚未观察到”，不表示永不到达。
- **Interval censoring**：前后有效记录或可界定的数据缺口说明 crossing 位于
  一个区间内。缺口必须足够支持区间边界；不能把末端采样点当精确时间。
- **Unknown**：身份、路径、时钟或测量质量不足以判断是否发生/归属于该源。
  Unknown 不是普通右删失，也不能仅通过扩大区间把不可辨识变成 interval-censored。

### 9.3 统计估计边界

| 数据结构 | 可用方法 | 关键假设和边界 |
|---|---|---|
| 完整精确到达、无删失 | 经验 CDF/事件率 | 只适用于确实可定位的完整事件 |
| 右删失 | 生存函数或累计发生分布 | 只有在给定 \(H\)、质量和协变量后删失近似独立时才可用普通 KM |
| 区间删失 | 区间删失 NPMLE/Turnbull 类方法或相应模型 | 直接使用区间；不能取起点、终点或中点替代 |
| 混合区间与右删失 | 同时支持两者的生存估计 | 需明确观察机制和支持域 |
| 信息性缺失/安全中止 | 上下界、加权或敏感性分析 | 需要缺失/删失机制假设；结果应保留识别区间 |
| 多源竞争或路径不可归属 | competing/unknown 分层或界限 | 不得把竞争源简单当普通删失 |

普通 Kaplan–Meier 不能在没有独立删失假设时机械使用。任何 Unknown 被排除的
分析都必须同时给出排除比例、原因和界限/敏感性结果。

### 9.4 时钟误差的传递

对每个时钟保留校准前后的 offset、漂移、采样间隔和残差。若一个观测时刻的
总误差有已知界限 \(\epsilon\)，则 onset 区间应扩展为观测区间加上该误差，而
跨时钟比较还要加入相对 offset/漂移界限。若误差有概率分布，可以在敏感性分析
中传播分布；若只有边界，采用区间算术。

对源 onset 区间和目标 arrival 区间，传播滞后使用

\[
\Delta_P\in[L_A-U_S,\;U_A-L_S].
\]

对总体时间优先性，分别扩大风险 onset 的上界和物理 arrival 的下界：只有在

\[
T_R^{upper}<T_P^{lower}
\]

且同时满足 witness、删失和质量条件时，才可报告时间分离。区间相交时返回
`Unknown` 或 `temporal precedence not established`。不能取 \((L+U)/2\) 后宣称
先后，也不能用计划时间、首次采样或 confirmation 代替带误差的真实 onset。

## 10. 与 P1 总体时间优先性的接口

P1 定义

\[
T_R=\text{消息策略引起的总体区域风险效应 onset},\qquad
T_P=\text{普通物理状态的合格到达时间}.
\]

风险曲线 onset 仍来自预定时间网格、同时置信带、SESOI 和持续性规则；首次
观察到风险下降、首次命令变化、\(T_U\) 或消息生成时间都不能替代 \(T_R\)。
本规范提供的是 \(T_P\) 的状态、路径、删失和时钟契约。首版结论只允许是总体
层面的 early-window effect 或总体时间分离，不能写成单个处理事件的
\(T_P(0)-T_R(1)\) 或“提前多少秒”。

若 no-message \(F_0(H)\) 的上界低于预先批准的允许物理到达比例，且区域风险曲线
在同一时间框架内满足持续性和同时置信带条件，可以表述为：在明确定义的物理状态
通常尚未达到的总体窗口内观察到策略效应。该表述不排除低于 \(\phi\) 检测阈值的
微弱物理作用，也不把总体分布配成同一事件的跨世界路径。

## 11. 当前推荐、事实与待研究者决定

| 事项 | Fact | Inference | Proposal | 状态 |
|---|---|---|---|---|
| A 路线时间 | Formal P2 有观测和确认语义，消息须等确认 | 物理影响可在确认前出现 | 物理主锚点用 onset interval，确认作信息链锚点 | Awaiting Researcher Decision |
| B 路线时间 | 计划与实际执行可能分离 | 计划时间会产生物理时序偏差 | 仅 actual perturbation time 作为物理锚点 | Awaiting Researcher Decision |
| 方向语义 | 车辆、道路坐标、物理边、宏观波前是不同对象 | 跟驰影响可与车辆行驶方向相反 | 微观边方向候选化，宏观方向数据估计 | Awaiting Researcher Decision |
| 第一版路径 | 拓扑、邻近、轨迹、响应证据可分层 | 仅拓扑不足以归因 | 同车道纵向交互优先，复杂交互单列 | Awaiting Researcher Decision |
| \(\phi\) 主候选 | 相对速度、gap、density 可从 Observer 派生 | 区域均速最接近总体状态且不循环 | 等车辆有符号平均速度下降主指标；median/proportion 辅助 | Awaiting Researcher Decision |
| Baseline | no-message 运行可能已含普通物理传播 | baseline 与参考分布回答不同问题 | 同运行 pre-onset baseline 主用，no-message 估 \(F_0\) | Awaiting Researcher Decision |
| \(S^*\) 与 \(Z_C\) | P1 区分 assignment 与 actual state | 处理后筛选会改变总体 | 先确认源，再分配通信策略 | Awaiting Researcher Decision |
| No-message | \(Z_C=0,Z_S=1\) 与 source-absent/失败不同 | 随机化 no-message 可识别总体分布 | 方案 A 为主，SUMO 配对为辅助 | Awaiting Researcher Decision |
| Censoring | onset、confirmation、右/区间删失和 Unknown 可分开 | 中点会制造时间偏差 | 使用适配的 interval/right-censor 方法和界限 | Awaiting Researcher Decision |
| Clock | 时间戳有时钟、offset、漂移和采样误差 | 区间交叠会阻断先后结论 | 保留误差并传递到 \(T_P\)、\(T_R\) 区间 | Awaiting Researcher Decision |

## 12. 已知限制与下一任务入口

- 当前 SUMO Formal P2 源事件仍为零，不能降低阈值来填补参考设计；
- 当前没有合格独立现实物理 witness，SUMO Observer 仍是模型内记录；
- \(\phi\)、\(\theta_P\)、\(h_P\)、\(q_P\)、baseline 窗口、coverage、恢复规则、
  多源归属、区域边界和时钟准入均未冻结；
- no-message 参考需要 source-present 运行和策略泄漏审计，不能由消息组或
  source-absent 运行替代；
- 进入下一任务前，研究者至少需要审核 \(t_E\)、第一版路径准入、\(\phi\) 主指标、
  source qualification 与通信随机化顺序、删失/时钟准入和目标 cohort/region/window。

本规范没有运行 SUMO/TraCI、Pilot、正式实验或统计估计，没有读取 locked holdout，
没有修改生产代码、正式配置、Gate、Protocol Lock 或 Stage 1.1 状态。

方法来源与适用性见 [P2_TASK2_LITERATURE_AND_METHOD_AUDIT.md](P2_TASK2_LITERATURE_AND_METHOD_AUDIT.md)。
