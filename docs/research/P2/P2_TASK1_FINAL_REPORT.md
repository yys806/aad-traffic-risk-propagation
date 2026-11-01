# AAD P2 Task1 最终报告：Source Event 与 Physical Propagation 操作化

日期：2026-11-02
任务：P2-TASK1
状态：COMPLETED_WITH_LIMITATIONS

## 1. 完成内容

本次任务完成了：

- Formal P2 A 路线与安全受控扰动 B 路线的操作化区分；
- Source Event 的首次合格观测、实际确认、消息生成可用性和失败/删失语义；
- 时变物理交互图 \(G_P(t)\) 和 time-respecting path 定义；
- Potential Path、Observed Interaction、Qualified Physical Propagation Witness 三层路径状态；
- \(T_P\) 的一般定义、候选状态函数、阈值/持续性/缺口/删失框架；
- 目标区域物理状态与物理路径联合资格；
- SUMO Read-only Observer 最小证据契约；
- P2 Task2 的研究者决策和进入条件。

本次没有运行 SUMO/TraCI、Pilot、Task9/18/19/20，也没有修改生产代码、正式配置、Formal P2、Formal rho 或 Gate。

## 2. Source Event 操作定义

### A 路线：Formal P2

沿用当前正式定义：可靠正闭合 TTC、TTC<2.0 s、最小持续时间 0.2 s、最大观测间隔 0.11 s、既有 rho 映射和未知上下界。首次合格观测时间、实际确认时间 event_confirm_s、可用消息生成时间和退出原因分开记录。

SUMO 当前源 P2 为零的事实保留；不得为了获得源事件而降低阈值、改变持续时间或制造危险扰动。

### B 路线：安全受控扰动

B 路线单独记录计划扰动、实际扰动、执行失败/延迟、强度和关联键，使用独立 source type。B 只支持模型内机制和失败边界研究，不称为 Formal P2，也不继承现实源事件适用性。

## 3. Physical Propagation

物理传播使用

\[
G_P(t)=(V,E_P(t)).
\]

每条边记录起止车辆、交互类型、有效时间、身份连续性、物理状态、观测质量和版本。路径必须满足时间可达关系

\[
t_{r+1}\geq t_r,\qquad e_r\in E_P(t_r).
\]

道路连通、空间相邻、轨迹先后或同一 leader 标签只能形成 Potential/Observed 状态，不能单独构成 Qualified Witness。身份断裂、leader 切换、重大缺口和未解释外部源会使路径变为 Unknown 或不合格。

## 4. Physical Arrival \(T_P\)

一般定义为

\[
T_P=
\inf\left\{
t\geq t_E:
\phi\!\left(X^*_{\mathcal T}(t),B_{\mathcal T}\right)=1
\ \text{并满足预设持续性}
\right\}.
\]

候选状态函数比较后，推荐先使用相对基线的持续速度变化；跟驰净间距和局部密度作辅助；Formal rho/P2 只作风险一致性证据，不直接定义物理到达，以避免与区域风险终点循环定义。

首次阈值满足、持续性确认、到达区间、右删失、区间删失和 Unknown 分开保存。参数 \(\phi,\theta_P,h_P,q_P\)、基线、恢复规则和多源归属尚未冻结。

物理到达只有同时满足以下条件才合格：

1. 区域状态满足 \(\phi\) 和持续性；
2. 存在 Qualified Physical Propagation Witness；
3. 身份、时间顺序和状态证据连续；
4. 时钟、采样和质量足以给出到达区间；
5. 没有未记录的重大缺口、独立源或外部控制使归因不可辨识。

## 5. SUMO Observer 契约

Observer 只读取 SUMO 状态，不生成或转发消息，不参与 Adoption，不修改动作或仿真演化。最小字段覆盖：

- run/pair/event/assignment/source/vehicle/leader 身份；
- target cohort、region、window；
- simulation time、step、clock；
- position、speed、acceleration、lane、net gap；
- physical edge；
- source onset/confirmation 和 arrival onset/confirmation；
- measurement、quality、missing、censoring；
- observer/scenario/algorithm version 和 SHA256。

Observer 是模型内观测记录，不是现实路侧传感器，也不提供 no-message 反事实。普通物理参考优先来自 \(Z_C=0,Z_S=1\) 的无消息运行分布

\[
F_0(t\mid H,Z_S=1)
=P\{\widetilde T_P\leq t\mid Z_C=0,Z_S=1,H\}.
\]

## 6. 竞争解释与识别边界

路径归因必须保留原有拥堵/排队、道路几何、信号、边界流、其他风险源、其他车辆控制和观测缺口等竞争解释。本任务没有完成这些解释的因果排除，因此 Qualified Witness 是证据资格，不是自动的源事件因果证明。

当前可支持：

- Formal P2 或 B 机制事件的定义；
- SUMO 内物理路径和状态记录；
- 模型内物理到达候选与删失；
- no-message 运行分布的未来设计接口。

当前不能支持：

- 现实物理传播已被验证；
- 单个处理事件的 \(T_P(0)\)；
- 由消息组轨迹直接得到 no-message 反事实；
- 将 Task9/19 局部 Follower 响应写成网络级传播。

## 7. 待研究者决定的事项

仍需决定：A/B 具体 SUMO 场景、\(t_E\)、\(\phi\)、阈值、持续性、最大间隔、路径准入、多源归属、时钟误差、缺失准入和目标区域边界。完整清单见 [P2_TASK1_RESEARCHER_DECISIONS.md](P2_TASK1_RESEARCHER_DECISIONS.md)。

## 8. P2 Task2 进入判断

P2 Task1 已达到进入 P2 Task2 的文档准备条件：A/B 源事件框架、时变路径表示、物理到达候选和 Observer 最小契约已经形成。Formal P2 源事件数量、合格物理 witness、最终物理状态函数和阈值仍未关闭；因此本任务不代表科学 Gate 通过、实验授权或 Protocol Lock。

## 9. 交付文件

- [P2_TASK1_SOURCE_EVENT_AND_PHYSICAL_PROPAGATION_SPEC.md](P2_TASK1_SOURCE_EVENT_AND_PHYSICAL_PROPAGATION_SPEC.md)
- [P2_TASK1_RESEARCHER_DECISIONS.md](P2_TASK1_RESEARCHER_DECISIONS.md)
- 本报告\n