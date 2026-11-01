## Current — P2 Task1 physical operationalization (2026-11-02)

P2 defines Source Event A as the unchanged Formal P2 route and B as an explicitly separate safe controlled perturbation mechanism domain. Physical propagation is a time-respecting path in G_P(t), with Potential Physical Path, Observed Physical Interaction and Qualified Physical Propagation Witness as separate statuses. Physical arrival is \(T_P=\inf\{t\geq t_E:\phi(X^*_{\mathcal T}(t),B_{\mathcal T})=1\text{ with persistence}\}\); the leading candidate is a sustained relative-baseline speed state, while gap/density are auxiliary and Formal rho/P2 is not the direct arrival definition.

SUMO Observer is read-only model evidence and does not create no-message counterfactuals. The ordinary physical reference is a future Z_C=0, Z_S=1 run distribution. All thresholds, persistence, path admission, clock/error tolerances, source scenarios and region boundaries remain Awaiting Researcher Decision. See docs/research/P2/P2_TASK1_FINAL_REPORT.md.

## Current — P1 Task2 decision synchronization and causal refinement (2026-11-01)

The researcher has confirmed the D1–D10 directions in AAD-P1-TASK2. Current scope is SUMO model-internal causal mechanism work with an automatic controller, source-present two-arm regional-risk ITT as the entry analysis and a required final four-cell design. Formal P2 and safe controlled perturbation remain separate source domains; target cohort/region/window are pre-fixed in principle; the SUMO Observer is read-only and is not a real roadside sensor; communication is direct single-hop; the first temporal claim is population-level; Pilot comes before SESOI/power/sample-size planning.

The refined theory separates assignment Z_S/Z_C from actual S*/C* states and true process from observed logs/Observer records. H2 distinguishes adoption rate, encouragement reduced form and IV/LATE; H3 lists action-intervention, IV, longitudinal g-formula and interventional indirect-effect candidates; H4 defines population risk-curve onset and no-message physical-arrival distributions. Operational parameters remain Awaiting Researcher Decision. See docs/research/P1/P1_TASK2_FINAL_REPORT.md.

## Historical — P1 Task1 theory and causal model (2026-11-01)

P1 formalizes AAD with two coupled but distinct networks: physical interaction G_P(t)=(V,E_P(t)) and information propagation G_I(t)=(V,E_I(t)). The joint state uses physical state x, message/lifecycle state m, controller decision/command/actual input and fixed-region Formal rho/P2 risk. Message generation, transmission, delivery, verification, adoption, command, action and regional risk remain separate events with times T_G,T_S,T_D,T_V,T_A,T_C,T_U,T_R; ordinary physical arrival T_P needs an independent time-indexed witness.

The causal framework preserves the planning four-cell interaction tau_SC and the P0 source-present two-arm tau_ITT^(S=1) as different estimands. Under interference, potential outcomes depend on the full assignment vector; adoption/action are post-treatment mechanism variables and are not identified by subgroup comparisons. H1–H4 are falsifiable, but all substantive D1–D10 choices remain Proposed / Awaiting Researcher Decision. See docs/research/P1/P1_TASK1_FINAL_REPORT.md.

# AAD Research Context

## Current — P0 Task 3 design boundary (2026-11-01)

Task3 recommends, as Proposal, whole-event/closed-network randomized message strategy ITT with independent roadside observation and randomized no-message events for controlled real-world evidence. Existing SUMO supports future model-only mechanism preparation; HIL provides real driver behavior in simulated traffic. Access and final sample size are Unknown. Measurement independence, randomized counterfactual reference and model counterfactual are distinct. Population-level early-window comparisons do not identify individual cross-world arrival differences, and policy ITT plus lifecycle logs does not identify adoption/action mediation. The two-arm minimum complements the proposed four-cell design; no approved definition or Gate changed. See `docs/research/P0/P0_TASK3_FINAL_REPORT.md`.

## 研究背景

联网车辆可以接收来自远端的风险信息，但消息生成、发送、交付、验证、采用、动作变化和区域风险变化是不同事件，必须逐层记录和验证。

## 研究问题

来源可追溯且确实被控制器采用的远端风险消息，能否在普通物理影响到达目标区域以前，通过改变目标车辆动作而改变区域总体风险。依据：`PROJECT_CONTEXT.md`、`docs/RESEARCH_STATUS.md`。

## 问题建模

当前工程设计用 `s` 表示源事件是否存在、`c` 表示通信通道是否启用，形成 `s0c0/s0c1/s1c0/s1c1` 四格；状态、源事件、消息生命周期、动作和风险分别进入五类表。物理路径到达时间与信息链路必须分开。四格和五表的当前实现见 `code/src/riskprop/stage_0_1_sumo.py`、`formal_artifacts.py`、`formal_design.py`。

## 现有方法

仓库历史区保留了 DRIFT 风险事件、局部传播、非局部 pilot 与可行性管线。这些形成于当前协议门禁前，只用于追溯，见 `code/src/riskprop/legacy/` 与 `docs/HISTORY_INDEX.md`。

## 当前项目采用的方法

当前采用“先测量和现实边界、再协议锁、最后核心效应”的分阶段流程：NGSIM 负责跟驰风险；pNEUMA 只负责城市运动学；SPMD 负责通信可观测边界；SUMO 负责受控工程运行和后续实验底座；阶段 0.5/0.6 负责适用域与准入。

## 当前科研假设

已记录的待检验方向是：信息链可能早于普通物理传播影响目标区域，并可能引起目标动作与区域风险变化。当前没有完成的阶段 1.1 结果支持或否定该假设；所有现有结果均 `scientific_claim_eligible=false`。

## Research Rationale

“先建立可信风险尺子、消息账本和现实适用域，再估计核心效应”是项目文档记录的研究动机，不是由现有代码运行自动证明的事实。依据：`docs/METHOD_AND_ALGORITHM_GUIDE.md`、`docs/论文实验推进/总计划.md`。

## 核心研究逻辑

1. 阶段 0.1 证明工程记录链可审计。
2. 阶段 0.2—0.4 确定风险、运动学和通信字段的可测边界。
3. 阶段 0.5 检查仿真样本是否处在现实参考范围。
4. 阶段 0.6 验证数值实现并冻结协议。
5. 只有协议锁通过后，才允许设计、实现和运行阶段 1.1。


## Research Proposal / Pending Parameters / Not Frozen（Task 2.5.1 同步备忘）

研究讨论提出：保留论文原有四格区域风险效应；负向风险效应以小于零为基本方向判据；可探索在预先规定的连续子时间窗中要求风险效应持续小于零，用于刻画 `Sustained Negative Risk Effect`。不额外引入风险改善幅度阈值；持续时间和子窗口长度仍待研究者决定。该持续性要求是 Effect、Attribution、Temporal Precedence 的补充证据，不替代核心成立条件。单次估计为负不等于具有统计支持的因果效应。此备忘与源端 TTC/DRAC 事件阈值验证属于不同科研问题，尚未实施，不构成冻结判据，也未写入 `AI_CONTEXT/06_DECISIONS.md`。
