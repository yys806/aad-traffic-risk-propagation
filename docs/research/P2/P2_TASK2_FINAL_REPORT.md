# AAD P2 Task2 最终报告：Physical Arrival Operationalization & No-Message Reference Design

日期：2026-11-02
任务编号：P2-TASK2
状态：`COMPLETED_WITH_LIMITATIONS`

## 1. 任务范围

本任务把 P2 Task1 的一般定义进一步推进为可供后续设计审核的操作化方案，覆盖：

- Physical Source Onset、Source Confirmation 和 Message Generation Eligibility 的时间分离；
- 微观车辆交互路径与宏观交通波前的方向语义；
- 有向物理交互边和 Qualified Physical Propagation Witness 准入；
- 区域物理状态函数 \(\phi\) 的速度候选、baseline、固定 cohort 和动态占用规则；
- no-message physical arrival distribution \(F_0(t\mid H,Z_S=1)\) 的主参考和 SUMO 配对辅助参考；
- arrival onset、confirmation、采样、删失、Unknown 和时钟误差；
- 文献方法对 AAD 的可复用边界。

本轮没有修改生产代码、正式配置、Formal P2、Formal rho/P2、D1/B witness、
Gate、Protocol Lock 或 Stage 1.1，也没有运行 SUMO/TraCI、Pilot、正式实验、
HIL/实车实验、现实交通采集或 locked holdout 读取。

## 2. 核心方法推荐

### 2.1 时间锚点

对 A 路线，物理传播使用

\[
t_{S,onset}\in[L_S,U_S]
\]

作为首选起点，Formal P2 资格使用 \(t_{S,confirm}\)，消息最早可生成时间满足
\(T_{G,eligible}\ge t_{S,confirm}\)。这三个时间分别服务于物理链、资格链和
信息链。确认时间不倒写成物理起点。

对 B 路线，计划扰动和实际扰动分开保存，只有 actual perturbation time 进入
物理时间轴。B 保持独立机制域，不称为 Formal P2。

### 2.2 方向与路径

车辆行驶方向、道路空间坐标方向、候选物理影响方向和宏观波前方向分别记录。
前车减速引起后车响应时，影响方向可能与车辆行驶方向相反；宏观波前方向由
空间—时间状态变化估计，不能预设所有扰动向上游传播。

AAD 第一版建议以同车道纵向 leader/follower 交互作为主要 Qualified Witness
候选。边必须同时具备源状态变化、目标响应、时间顺序、身份/关系连续性、状态
质量、时钟界限和竞争解释审查。换道、汇入、多源和 leader 切换单独记录，不能
在缺乏方向和响应证据时自动升级。Qualified Witness 是证据资格，不是自动因果证明。

### 2.3 区域状态函数

对固定 cohort 的有效观测子集 \(I_t\)，使用

\[
d_i(t)=b_i(t)-v_i^{obs}(t),\qquad
g_v^{mean}(t)=\frac{1}{|I_t|}\sum_{i\in I_t}d_i(t)
\]

作为首选主候选，并写成

\[
\phi(X^*_{\mathcal T}(t),B_{\mathcal T})
=\mathbf 1[g_v^{mean}(t)\ge\theta_P]
\]

加上预先声明的持续时间 \(h_P\)、最大观测间隔 \(q_P\)、coverage 和恢复规则。
中位数、速度偏差分位数、超阈值比例和绝对速度偏差是辅助或敏感性指标；净间距
和局部密度用于路径/区域辅助；Formal rho/P2 不直接定义 \(T_P\)。

该选择是 Proposal，尚未冻结 \(\theta_P,h_P,q_P\)、baseline 窗口、coverage、
恢复规则或区域边界，也没有复用 Formal P2 的 TTC 参数。

### 2.4 Baseline 与 no-message 参考

同一运行 source onset 前的固定窗口是 Physical State Baseline 的主候选；
source-present no-message 运行可以用于背景/阈值敏感性和 \(F_0\)，但不能被
称为无物理扰动 baseline，因为其中可能包含普通物理传播。

主参考方案是：通信盲地确认合格 source event 后，再随机分配 \(Z_C=0/1\)。
\(Z_C=0,Z_S=1\) 提供 no-message physical arrival distribution；消息臂的
delivery/verification/controller 失败仍保留在 \(Z_C=1\) 分配组。若通信策略在
源确认前分配且可能影响 \(S^*\)，不能直接对实际合格源子集作处理后条件化，必须
回到 assignment-level ITT、四格设计、principal-strata 或明确识别假设。

SUMO 同初态/同配置的配对运行只作模型内辅助证据。相同 seed 不足以证明逐事件
反事实配对；必须审计分岔后的随机数调用和外生流。

### 2.5 时间删失和时钟

每个事件分开保留 arrival onset interval、confirmation time、observation time、
clock uncertainty、right censoring、interval censoring 和 Unknown。连续观察到
截止仍未到达才是 right censoring；观测缺口横跨 crossing 才是 interval censoring；
身份、路径、时钟或质量不足时是 Unknown。

普通 Kaplan–Meier 只有在条件独立删失假设成立时才可用；区间删失使用适配方法，
信息性缺失、竞争源和安全中止使用界限或敏感性。源 onset 区间与目标 arrival
区间的传播滞后使用区间算术；时间区间相交时不能通过取中点判定先后。

## 3. 有限文献调研结果

本轮实际采用的直接方法依据为：

- Lighthill & Whitham (1955)：宏观 kinematic wave 是空间—时间状态对象；
- Richards (1956)：shockwave 方向和速度依赖宏观交通状态；
- Austroads (2015)：跟驰、排队、车队和运动波属于相关但不同的交通理论层；
- Yang et al. (2024)：部分车辆轨迹可用于宏观波前候选检测，但算法是数据依赖的；
- Lindsey & Ryan (1998)：区间删失不能用起点、终点或中点替代；
- Sharma et al. (2019)：轨迹完整性和状态覆盖影响运动学方法，必须保留质量门槛。

文献支持方法边界，不支持 AAD 的阈值、现实因果结论或 Formal P2 变更。详细来源、
方法假设、可复用部分和停止理由见
[P2_TASK2_LITERATURE_AND_METHOD_AUDIT.md](P2_TASK2_LITERATURE_AND_METHOD_AUDIT.md)。

## 4. 已完成的交付物

1. [P2_TASK2_PHYSICAL_ARRIVAL_AND_NO_MESSAGE_REFERENCE_SPEC.md](P2_TASK2_PHYSICAL_ARRIVAL_AND_NO_MESSAGE_REFERENCE_SPEC.md)：物理到达、路径、\(\phi\)、baseline、no-message、删失和识别条件规范。
2. [P2_TASK2_RESEARCHER_DECISIONS.md](P2_TASK2_RESEARCHER_DECISIONS.md)：Fact、Inference、Proposal 和 Awaiting Researcher Decision 登记。
3. [P2_TASK2_LITERATURE_AND_METHOD_AUDIT.md](P2_TASK2_LITERATURE_AND_METHOD_AUDIT.md)：六个直接来源和调研停止依据。
4. 本报告：任务结果、方法推荐、限制和下一任务条件。

## 5. 仍未解决的问题

- 当前 SUMO Formal P2 源事件仍为零；不能通过降低阈值或改写 Formal P2 填补；
- 没有合格独立现实物理 witness，Observer 仍是模型内只读证据；
- \(t_E\) 的最终采用、\(\phi\) 主函数、阈值、持续时间、最大间隔、coverage 和
  recovery 尚未由研究者冻结；
- 同车道路径、leader 切换、身份重识别、多源和复杂横向交互的正式准入仍待决定；
- 先确认 source 再随机通信的顺序需要场景可行性确认；
- no-message 参考的删失独立性、时钟容差、区域边界和动态占用规则尚未关闭；
- 当前文档没有产生 \(F_0\) 数值、\(T_P\) 样本、时间优先性结果或功效结论。

## 6. 进入下一任务的条件

研究者审核并决定以下项目后，才具备进入后续参数/接口冻结的条件：

1. A/B 时间锚点和 confirmation/generation 关系；
2. 第一版 Qualified Witness 的边级/路径级准入与多源规则；
3. \(\phi\) 主指标、Physical State Baseline、fixed cohort/region/window 和 coverage；
4. source qualification 与 \(Z_C\) 分配的时间顺序；
5. no-message 主参考和 SUMO 配对辅助参考的适用域；
6. censoring、Unknown、clock 和时间优先性判据的正式质量边界。

这些条件是后续研究设计的入口，不是本轮实验授权。下一任务不得自动新增实验臂、
seed、运行矩阵或 Protocol Lock。

## 7. 本轮没有执行的工作

- 没有运行 SUMO、TraCI、Pilot 或正式实验；
- 没有修改生产代码、Formal P2、Formal rho、D1/B witness、正式配置或 Gate；
- 没有读取 locked holdout；
- 没有进行现实交通采集、HIL、实车或外部资源联系；
- 没有生成 Protocol Lock 或启动 Stage 1.1；
- 没有把模型内 witness、Task9/Task19 局部响应或文献方法写成 AAD 科学主效应。

## 8. 任务结论

P2 Task2 达到 `COMPLETED_WITH_LIMITATIONS`：物理起点与确认时间已经分离，微观
路径与宏观波前具有明确的不同语义，Qualified Witness 有可审计的第一版准入，
区域物理状态函数和 no-message 总体参考有可计算的候选定义，删失和时钟误差
进入到达时间判据。所有数值参数和核心研究选择仍保留为
`Awaiting Researcher Decision`，当前没有科学 Gate 通过或实验结果。
