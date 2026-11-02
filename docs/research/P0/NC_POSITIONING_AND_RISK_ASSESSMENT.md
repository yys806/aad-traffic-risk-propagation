# NC 竞争力与风险评估

## 审稿人式判断

1. **重要性**：交通、网络科学、因果推断和安全工程都能理解“双传播 + 干扰”问题；但当前项目证据还不足以证明超出交通领域的普适机制。
2. **新现象**：信息波、物理波、BLOS 响应和作用区域均已有先行研究；AAD 必须证明它们在一个可审计事件级机制中产生新关系。
3. **实质突破**：目前是 `Unverified/Proposal`。最接近的威胁包括 Jerath 2024 的 ZOI 和 Peng 2026 的 BLOS 因果异质性。
4. **因果识别**：网络干扰使普通个体 A/B 不足。需要 exposure mapping、直接/间接/总体效应和随机/准随机干预。
5. **信息链与物理链**：这是 AAD 的必要条件，但当前 Stage 0.5 仍缺独立物理 time-indexed witness，不能宣称已区分。
6. **控制器采用**：必须记录消息验证、采用和实际动作，不能以送达或模拟开关代替。
7. **动作到区域风险**：需要中介链和区域 estimand；TTC/P2 变化本身不是区域机制证明。
8. **物理基准**：需同事件、同 cohort、同时间轴且独立于干预的物理传播证据。
9. **现实数据**：当前项目有 NGSIM/MiTra 轨迹与工程审计，但现实视频/物理映射仍有阻塞；不能把 SUMO 结果写成现实验证。
10. **可重复性**：工程复现和证据封存较强；科学 Gate、跨场景和外部验证仍未完成。
11. **最强反对意见**：所谓“超距”只是已知 V2X 信息传播、非局部控制或驾驶警告效应的重新命名，且未排除物理扰动、leader 变化和测量链误差。
12. **核心假设失败时**：仍可形成有价值的负结果——证明信息效应在某些状态下被物理传播或采用失败遮蔽，给出失效边界和安全设计约束。

## 条件化结论

AAD 目前具备 NC 级问题的候选重要性和工程审计基础，但不具备 NC 级科学证据闭环。是否具有 NC 竞争力取决于 C1–C4 的不可替代证据；不能由现有局部 SUMO/轨迹结果推出。

## 主要失败风险

- 独立物理到达时间无法观测；
- 消息采用与动作中介不可分离；
- 网络 interference 使效应不可识别；
- 现实轨迹无法建立跨窗口身份/空间基准；
- 代理安全指标在适用域外失效；
- 跨状态/跨道路效应不稳定；
- 仿真与现实的 micro-interaction 不等价。
## P0 Task 2 审计更新

NC 竞争力目前应标为 **候选问题重要，但科学证据未闭环**。Peng 的随机模拟器研究降低了“远端 warning 是否能改变动作”的新颖性空间；Schönhof、Wang 和 Jerath 分别降低了“信息—物理耦合、信息波和作用边界”的新颖性空间。AAD 必须证明的是可审计的事件级机制和网络级因果效应，而不是把这些结果串在一起。

最小不可替代证据是 message strategy ITT/policy effect 加同源 no-message physical reference。Delivery、adoption 和自然 mediation 都是处理后过程，除非有随机鼓励或 interventional design，不能作为首要因果结果。若区域风险效应不可识别，仍可形成 action-level response 或 failure-boundary 论文，但不能保留区域总体因果主张。

NC 评估仍不构成发表保证；阶段状态和 Gate 不因本附录改变。

## P2 Task4 supplement — 2026-11-02

NC positioning remains a candidate scientific question without an empirical identification closure. Main risks are not solved by a lower speed threshold: regional response can precede fixed-cohort alarm; Qpre is pre-ZC but post-ZS; selected complete matched four-cell units may alter the target estimand; within-treated behavioral timing is not population risk-versus-no-message precedence. Jerath, Zhang (formal text still unavailable), Peng, Saberi and Duan constrain novelty. The potentially distinctive joint contract needs falsifiable transferable mechanism results, not only more complete engineering logs. See [Task4 final report](../P2/P2_TASK4_FINAL_REPORT.md) and its linked synthesis. No NC innovation or causal hypothesis is declared proven; Gate/Stage remain unchanged.

## Task5补充审计（2026-11-02；不覆盖历史）

正式Zhang18页现已FULL_TEXT_READ_PUBLISHED（Q65YUJ89/9F39AWXN），预印本CLA3GKSX保留；版本差异见[Task5正式版审计](../P2/P2_TASK5_ZHANG_PUBLISHED_VERSION_AUDIT.md)。旧100 events与正式120 STMaps单位不同；正式F1 .875、speed error2.20ft/s不与旧值混用。正式无向事件图/BFS、物理约束和波前重建不是独立随机因果识别，也不能直接成为W1–W9。变化点/事件图/波前本身不能继续当AAD新颖性。

新增Frangakis–Rubin2002与Hoeffding1963分别支持资格分层识别边界和有条件保守同时界；不是新增交通效应。联合生命周期/采用动作/区域风险ITT/同资格无消息物理基准仍为待验证贡献候选，不是全球首次或NC创新已证。A0、独立Qualified0、F0/TR-TP Unknown保持。微观、宏观、cohort时间族、共同opportunity和具体统计规则均Proposal，见[统一定义v0.3](../definitions/README.md)。本轮0新实验，旧Task3/4结论及当时访问限制保留历史。
