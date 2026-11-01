# P0 Task 3：研究者决策清单

日期：2026-11-01。以下全部 **Proposed / Awaiting Researcher Decision**，无新增 Agreed Research Decision。事实、依据和限制见 [最终报告](P0_TASK3_FINAL_REPORT.md)；不要求研究者逐项批准常规文档/接口工程细节。

## 1. 需要研究者决定的科学问题

| ID | 真正需要决定的问题 | 推荐 Proposal | 依赖与未决定的后果 |
|---|---|---|---|
| D1 | 核心主张的首个适用域和优先平台 | 现实证据目标采用封闭测试场多车整场事件随机化；当前 SUMO 只作未来受限机制准备；HIL 可作行为替代 | 现实资源 Unknown。若只选 SUMO，结论必须限定模型内，不声称现实双传播成立 |
| D2 | 最小主处理和四格的关系 | 最小 source-present 设计以 πmsg/π0 的 ITT/policy effect 为主；delivery/adoption/action 为处理后机制；保留规划四格，未来 P5 另定 source×strategy 交互 | 两臂不能识别 τSC；不把 Task20 的 adoption 候选语义改为正式决定 |
| D3 | Source Event：必须 Formal P2 还是允许安全受控扰动机制域 | 优先既有正式定义；安全条件若无法产生 Formal P2，则明确选择受控扰动的有限域或停止现实路线；严禁降阈值/追危险接近 | 安全扰动不自动等于合格风险源；源类型/触发/时间零点需决定 |
| D4 | Target Cohort、固定 R/W 与区域 Primary Outcome | 预列完整实验车队 C；固定道路区域和事件相对窗口；用现有 Formal rho 固定 W 积分/时间均值后车辆等权；有效车时/P2/总积分作辅助 | 车队角色/数量、坐标/边界/窗口和进出规则未定；不能只看消息接收车就称区域总体 |
| D5 | 物理到达的可接受操作定义 | 独立路侧测量的持续速度变化为首选 φ，间距/密度/正式风险作辅助；明确路径证据 | 状态函数、阈值、持续时长、最大间隔、基线与删失规则待定；Tphys 不从距离/假速生成 |
| D6 | “早于物理”的可支持主张层级 | 先做总体层面的早期窗口 ITT 与随机 π0 到达分布；用独立 pilot 预定 H、允许到达比例 η/分位数、时间不确定性与同时推断 | 随机化不识别每个处理事件的 Tphys(0) 或跨世界提前秒数；若必须个体事件主张需额外可辩护设计/假设，目前 Unknown |
| D7 | 网络部署策略和随机化域 | 首版单跳、不转发；整场事件/必要时 session 分配，纳入域内干扰；跨域未知时不声明独立 | 若科研目标要求多跳/渗透率/直接与溢出分解，再选两阶段或 general exposure 设计；需预处理映射、正支持与联合分配概率 |
| D8 | 采用与动作中介是否必须作为首版因果终点；研究对象是人类还是可审计控制器 | 首版用可记录实际决策的控制器，主分析仍 ITT；独立 adoption-enabled/disabled 作为后续机制设计 | 日志完整仍不识别 mediation；人类 acknowledgment/眼动不是心理采用。若核心结论要求中介因果，须另有识别条件 |
| D9 | SESOI、正式精度/功效和 pilot 目标 | 以 Formal rho 单位确定 SESOI；未来独立 pilot 给事件方差/paired SD、ICC、缺失/泄漏、到达分布后算 n；不采用历史 minimum=100 | 当前最终 n/参与者数 Unknown；敏感性表不是计划样本量；选择 α、power、多重窗口/终点和缺失界宽度 |
| D10 | 资源或证据失败时的主线收窄选择 | 缺 witness→保留可测结果 ITT，放弃现实时间优先；缺 adoption→动作/风险 ITT；缺区域→固定个体/子 cohort；只有模型→simulator-only；不足以因果识别→failure-boundary | 不能自动替换科研方向；若研究者不接受收窄，则对应路线 NO-GO。Peng 已覆盖警告改变动作，收窄不保证新颖 |

数值参数未定不在本任务中自动填入；常规 record_id、文件格式、目录和文档排版不再列作科研决策。

## 2. 未决的现实依赖（不是已获得资源）

| 依赖 | 当前状态 | 需要未来拿到的证据 |
|---|---|---|
| 可控封闭场地/实际源—中间—目标路径 | **Unknown** | 场地图、占用/封闭权限、安全操作包络、复位条件 |
| 车辆、消息端点和控制器/CAN 日志权限 | **Unknown** | 可参与 fleet/角色、设备与软件接口、采用/拒绝回执和执行反馈能力 |
| 独立路侧设备/全区域覆盖 | **Unknown** | 空间/时钟标定、遮挡/身份连续性、净 gap 误差和全部车辆覆盖 |
| 独立重复和预算/排期 | **Unknown** | 可承担的事件/session 数、每次运行和复位周期、可靠报价；不得拿车辆数替代簇数 |
| 人类/安全审批、责任与数据治理 | **Unknown** | 机构伦理判断、知情同意/参与者保护、驾驶员/操作资格、急停/中止、隐私与访问条件 |
| HIL 替代平台 | **Unknown** | 座舱/软件许可、警告与全交通日志、多真人若需要的同步接口、参与者和伦理 |
| 直接可用的新随机化现实数据 | **Unknown** | 同源八类记录、处理机制、稳定键/时钟、数据许可；当前已审计来源不能提供 |

这些依赖不因公共设施网页、通用软件能力或本次 Conditional Go 而变为 Verified Access。任务未联系任何实验室、申请资源、采购、招募或开展车测。

## 3. 方案出口与既有边界

**CONDITIONAL GO**：研究者可据 D1–D10 选择继续设计的适用域；最小消息策略实验在结构上可实施，现实证据链取决于上表条件。**当前现实确认和正式实验启动 NO-GO**：资源、源/结果/到达定义、功效参数和既有 Gate 均未闭合。

长期规划 v1.0 Research Proposal 原文件只读，未改动。本清单不修改 Stage 0.5 `CLOSED_WITH_LIMITATIONS`/scientific_gate blocked、Stage 0.6 `PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS`、Protocol Lock `BLOCKED`、Stage I `READY_ENGINEERING_ONLY` 或 Stage 1.1 `NOT_AUTHORIZED`。

本 Task 以本地文档和 Commit 结束，不 Push，不自动进入 Task4/P1/新 pilot/Stage 1.1。研究者后续决定应另行记录为真实的 Agreed Decision；本文件本身不构成同意。
