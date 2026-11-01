# P1 Task2 研究者决策同步记录

日期：2026-11-01
状态：`Agreed`（研究方向与原则）；具体操作参数保持 `Awaiting Researcher Decision`
授权来源：研究者提交的 `AAD P1 Task2` 任务书。该任务书明确确认 D1–D10 的方向，并要求本记录同步。

## 1. 同步规则

本记录把 P0 Task3 的 D1–D10 从“整体 Proposed”拆成两层：研究者已经确认的方向/原则记为 `Agreed`；尚未给出数值、边界、阈值、精度或最终随机化细节的部分继续记为 `Awaiting Researcher Decision`。P0 Task3 原始清单作为历史记录保留，不被改写。

这些决定只约束 P1–P6 的理论和设计范围，不改变 Formal P2、Formal rho、D1/B witness、Scientific Equivalence、任何历史实验结果、Stage 0.5/0.6、Protocol Lock、Stage I 或 Stage 1.1 状态。

## 2. D1–D10 同步表

| ID | 决策状态 | 已确认方向/原则 | 仍未冻结的内容 | 对模型和后续阶段的影响 |
|---|---|---|---|---|
| D1 | `Agreed` 方向；参数 `Awaiting` | 当前优先 SUMO 仿真，先建立完整的信息传播—自动控制器—物理状态—区域风险链；现实封闭场、实车和现实资源不是当前前置条件 | SUMO 场景、适用域边界、未来现实扩展的具体验证方案 | 当前主张限定为模型内因果机制；现实一般性不能由 SUMO 结果推出。P2–P7 可先在 SUMO 证据契约内推进 |
| D2 | `Agreed` 方向；参数 `Awaiting` | 当前采用 source-present 两臂区域风险 ITT；最终研究必须完成 S0C0/S0C1/S1C0/S1C1 四格；两臂不称为四格交互 | 四格何时执行、正式主次终点、随机化概率和统计计划 | 复用 formal_design.py；区分分配字段与实际执行状态；保留 τ_SC 与 τ_ITT^(S=1) |
| D3 | `Agreed` 方向；参数 `Awaiting` | A 路线优先使用既有 Formal P2；B 路线允许安全受控扰动的仿真机制研究，且不重新标记为 Formal P2 | A/B 的场景清单、触发细节、观测窗口和适用域 | P2 必须保留 Formal P2 资格；B 只支持模型内机制/失败边界，不能继承现实源事件主张 |
| D4 | `Agreed` 方向；参数 `Awaiting` | 目标车辆集合、道路区域和观察窗口预先固定；主结果是区域总体风险，优先复用 Formal rho/P2 固定窗和车辆等权聚合 | 车辆成员、空间边界、窗口长度、进出规则和辅助终点 | P4 的 cohort/region/window 不能由处理后风险选择；区域结果不能只按消息接收车辆计算 |
| D5 | `Agreed` 方向；参数 `Awaiting` | 坚持独立物理观测；SUMO 使用不参与消息/控制的只读 Observer；现实扩展使用独立路侧传感器 | φ、阈值、持续时间、路径资格、误差和删失 | Observer 只生成模型观测记录，不等同现实传感器；P2 负责最终物理到达规则 |
| D6 | `Agreed` 方向；参数 `Awaiting` | 首版只主张总体时间优先性：早期区域风险 ITT 与无消息物理到达分布在共同时间框架中比较 | 早期 horizon、允许到达比例、分位数、同时置信水平和持续性 | 不主张单个处理事件的反事实提前秒数；保留 \(T_R^{upper}<T_P^{lower}\) 的总体分离判据 |
| D7 | `Agreed` 方向；参数 `Awaiting` | 首版单跳直接消息，不转发、不引入多跳中继；仍保留物理交互导致的网络干扰和区域 policy effect | 直接链路覆盖、消息超时/失效细节、随机化域和 exposure mapping | 信息网络简化为 direct Source→Target，但不能使用车辆级 SUTVA 规避物理 spillover |
| D8 | `Agreed` 方向；参数 `Awaiting` | 当前研究对象是自动控制器，不纳入人类驾驶者心理采用、问卷或驾驶模拟器参与者 | 控制器版本、采用日志字段、覆盖/接管规则和未来机制鼓励 | 必须分开 Delivery、Verification、Adoption、Decision、Command、Actual Action；主分析仍 assignment ITT |
| D9 | `Agreed` 方向；参数 `Awaiting` | 先完成必要 Pilot，再用 Pilot 估计方差、相关性、缺失和到达分布后规划 SESOI、功效和正式样本量；本次不运行 Pilot | SESOI、α、power、ICC、独立单位、样本量和多重检验 | 历史 minimum=100 不得作为正式样本量；P6 负责统计规划 |
| D10 | `Agreed` 方向；触发参数 `Awaiting` | 允许按证据缺失收窄主张：缺 witness 保留 ITT、缺 adoption 不主张 adoption 中介、缺动作不主张动作机制、区域不足则收窄区域、只有 SUMO 则限定模型内、核心条件失败则研究失败边界 | 触发阈值、缺失比例、停止规则和替代主线的正式准入 | 失败、Unknown、测量失败和空效应分开报告；不自动替换研究方向 |

## 3. Assignment 与实际状态的同步口径

D2 的四格配置中的 `source_present` 和 `channel_enabled` 表示配置/分配条件。它们不自动等于实际发生的 Formal P2 源事件或实际通信执行。P1 Task2 采用以下分层：

- \(Z_S\)：源事件条件的场景/实验分配；\(S^*\)：实际源事件状态及 Formal P2 资格；
- \(Z_C\)：通信策略的分配；\(C^*\)：实际策略执行状态，包括生成、发送、链路失败、过期和覆盖；
- \(D^*,V^*,A^*,U^{cmd,*},U^*\)：真实送达、验证、采用、命令和实际动作；
- 带波浪号的记录（例如 \(\widetilde D\)、\(\widetilde U\)、\(\widetilde T_P\)）是日志、Observer 或风险计算得到的观测/派生值。

现有 `validate_four_cell_configs` 校验配置契约，`validate_protocol_lifecycle` 校验生命周期记录；它们尚未把所有 assignment、actual execution 和 observation 字段作为同一生产接口冻结。本次只登记该语义差距，不修改正式代码。

## 4. 已确认方向与未冻结参数的边界

### 4.1 已确认，可直接指导 P1–P5

- SUMO 是当前优先平台，现实资源不是前置条件；结论限定模型内。
- 当前主分析是 source-present 两臂 ITT，最终必须保留四格交互。
- Formal P2 与安全受控扰动路线分开。
- 目标 cohort、region、window 预先固定，使用区域总体 Formal rho/P2 风险。
- Observer/路侧观测独立于消息和控制器决策。
- 首版研究总体时间优先性、单跳通信和自动控制器。
- 先 Pilot 后正式功效与样本量；本任务不运行 Pilot。
- 依据证据缺失收窄主张。

### 4.2 仍需后续决定

D1–D10 的数值和操作细节仍包括：场景参数、正式源事件样本、车辆/区域/窗口边界、物理状态函数和阈值、消息时延与过期、随机化概率、IV/鼓励是否实际部署、SESOI、α、power、ICC、样本量和缺失准入。它们不能由本记录自动冻结。

## 5. 项目边界

本记录不授权新的 SUMO/TraCI 运行、Pilot、Task9/18/19 重跑、现实数据采集、HIL/实车测试、locked holdout、Protocol Lock 或 Stage 1.1。Stage 0.5=`CLOSED_WITH_LIMITATIONS` 且 scientific Gate blocked；Stage 0.6=`PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS`；Protocol Lock=`BLOCKED`；Stage I=`READY_ENGINEERING_ONLY`；Stage 1.1=`NOT_AUTHORIZED`。

依据：P0 Task3 研究者决策清单、P1 Task1 理论/依赖登记，以及本次研究者明确提交的 AAD-P1-TASK2 任务书。
