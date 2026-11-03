# P7 Task2 研究者决策登记

Task ID: `AAD-P7-TASK2-20261103`；日期：2026-11-03。状态：`Agreed`。依据：研究者本任务书 §2、§12 的明确授权；不从烟测结果推导科研决策。

| ID | 已确认方向 | 尚未冻结 |
|---|---|---|
| D1 | SUMO 原生 Krauss 跟驰 + 消息驱动纵向策略 | 正式策略函数及数值 |
| D2 | 消息提供风险信息，控制器结合本地状态自主计算目标速度参考 | 正式风险映射及调整幅度 |
| D3 | 有效消息实际纳入具体策略决策输入、有消费回执及 decision_id 即 Adoption | 正式消息资格总体、TTL、可信边界 |
| D4 | Enabled/Disabled 均接收验证，仅 Enabled 允许消息进入策略 | 正式机制实验细则 |
| D5 | 按运行或交通交互组分配，组内模式稳定；本任务先运行级固定 | 随机化概率、随机化器、干扰域 |
| D6 | 第一版不增独立 Safety Layer | 后续是否引入及其算法 |
| D7 | 以连续实际速度、加速度轨迹为主要动作观测 | 正式阈值、持续时间、比较窗口 |
| D8 | 沿用 Formal rho/P2，不改主要风险指标 | 正式 Region/Cohort/Window 及效应识别 |

Adoption 正式同步见 [P3 ratification amendment](../P3/CONTROLLER_ADOPTION_RATIFICATION_20261103.md)。统一科研定义仍为 [v0.4 / 27 项](../definitions/README.md)，不新增 Definition ID。

授权范围：独立控制器、单跳进程内消息、输入门控、P3/P4 适配、最多三种确定性 SUMO 工程条件、定向测试、证据、文档和 commit/push。全部未确认数值仅 `ENGINEERING_CANDIDATE_NOT_FORMAL`。

不授权 Pilot、Independent V、locked holdout、正式配置或论文修改；Formal A=0、独立 Qualified=0、F0/总体 TR–TP=Unknown、Protocol Lock=BLOCKED、Stage1.1=NOT_AUTHORIZED 均不因本任务改变。
