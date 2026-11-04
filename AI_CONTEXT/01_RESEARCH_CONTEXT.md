## Current — P5 Task1 因果识别设计 (2026-11-04)

Qpre对ZC为前、对ZS可为后；τQ不能代替τSC。Effect、Attribution、Temporal Precedence分别识别。H1可独立于机制报告；No Message与Disabled不自动等价。总体early-window须匹配同资格F0并有真实到达桥接，不识别单例提前秒数。推荐方案未升级Agreed。

Formal A/Independent Qualified仍0，完整真实区域Y、F0及总体T_R–T_P Unknown；Protocol Lock BLOCKED，Stage1.1 NOT_AUTHORIZED，其他Gate不变。统一定义v0.4/27项、Formal参数、P3/P4/P7代码与历史证据不改。无新增交通实验/seed/Pilot/V/holdout读取。

[核心设计](../docs/research/P5/P5_TASK1_CAUSAL_IDENTIFICATION_DESIGN.md) · [决策](../docs/research/P5/P5_TASK1_RESEARCHER_DECISION_REGISTER.md) · [报告](../docs/research/P5/P5_TASK1_FINAL_REPORT.md) · [证据](../evidence/research/P5_TASK1_20261104/README.md)。统一入口仍为[科研定义](../docs/research/definitions/README.md)。下方保留历史任务时点。

## Current — P4 Task2 implementation (2026-11-04)

研究者P4 D01–D08全Agreed（A/A/B/A/A/A/A/A）。D03-B固定完整资格总体、D04-A固定N同窗平均贡献；最终Y算子确定不等于数值冻结。正式region/window/动作阈值/误差、现实覆盖及因果风险仍Unknown。

P7验收保持ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS；Formal A/Qualified仍0，F0/总体T_R–T_P Unknown；Gate/Protocol Lock不变，Stage1.1 NOT_AUTHORIZED。无新增SUMO/seed/Pilot/V/holdout读取。

[报告](../docs/research/P4/P4_TASK2_FINAL_REPORT.md) · [当前P4入口](../docs/research/P4/README_v1.md) · [Agreed决定](../docs/research/P4/P4_RESEARCHER_DECISIONS_20261104.md) · [证据](../evidence/research/P4_TASK2_20261104/README.md)；统一定义仍[v0.4/27项](../docs/research/definitions/README.md)。下方保留历史任务时点状态。

## Current — P4 Task1 measurement audit (2026-11-03)

Command、Execution、实际输入U*与运动状态X*不可等同。消息后运动差异、风险贡献差异、总体区域风险因果效应分别识别；T_U不是T_R。固定cohort不自动覆盖区域全体车辆。P4向P5/P6提供测量支持与界，不实施因果或功效估计。

P7 Task2.1工程验收保持ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS。Formal A/独立Qualified仍0；风险/F0/总体T_R–T_P Unknown；Gate/Protocol Lock不变，Stage1.1 NOT_AUTHORIZED。

[最终报告](../docs/research/P4/P4_TASK1_FINAL_REPORT.md) · [测量规范](../docs/research/P4/P4_ACTION_AND_RISK_MEASUREMENT_SPEC.md) · [待决](../docs/research/P4/P4_RESEARCHER_DECISIONS.md) · [证据](../evidence/research/P4_TASK1_20261103/README.md)。统一定义仍[27项v0.4](../docs/research/definitions/README.md)。下方保留历史任务时点状态。

## Current — P7 Task2.1 (2026-11-03)

ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS。本场景工程动作响应已观测，不代表Adoption因果作用、正式来源资格或区域风险效应。后续P5/P4/P6/P8需独立决策，不自动启动。

唯一Enabled v2复验通过（1次、seed20261103），基准未重跑。最大实际减速度1.0 m/s²，无emergency/碰撞/teleport；52次实际采用、39命令、326执行、352动作。首次命令2.8 s、首个实际差异2.9 s；8.0 s过期恢复20 m/s且后续无消息输入。共同351点比较有效，最大速度差2.649473720 m/s、加速度差2.719870887 m/s²，仅ENGINEERING_DIAGNOSTIC_ONLY。

Formal A/Qualified仍0，风险/F0/总体TR–TP Unknown；科研Gate/Lock和Stage1.1授权不变。统一定义仍[27项v0.4](../docs/research/definitions/README.md)。[复验报告](../docs/research/P7/P7_TASK2_1_FINAL_REPORT.md) · [证据](../evidence/research/P7_TASK2_1_20261103/README.md)。下方为历史状态。

## Historical — P7 Task2 original acceptance (2026-11-03)

状态：ENGINEERING_IMPLEMENTED_SUMO_ACCEPTANCE_BLOCKED。

研究者2026-11-03确认D1–D8方向及有效消息实际纳入具体策略决策输入的Adoption边界。消费事实不依赖动作变化；信息链、物理链、动作—风险识别分开。P7使用合成工程源，不提供Formal P2资格或类超距证据。P5资格总体/随机化、P4正式观测范围/阈值、P6统计仍待后续；不按Adoption筛选assignment-level ITT。

Formal A=0；独立Qualified=0；F0/总体TR–TP=Unknown。Stage0.5=CLOSED_WITH_LIMITATIONS；Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock=BLOCKED；Stage I=READY_ENGINEERING_ONLY；Stage1.1=NOT_AUTHORIZED。Formal算法/config、统一定义v0.4/27项和历史Task7/8/16/20证据不改。

[P7 Task2报告](../docs/research/P7/P7_TASK2_FINAL_REPORT.md) · [Agreed D1–D8](../docs/research/P7/P7_RESEARCHER_DECISIONS_20261103.md) · [Adoption修订](../docs/research/P3/CONTROLLER_ADOPTION_RATIFICATION_20261103.md) · [便携证据](../evidence/research/P7_TASK2_20261103/README.md)。统一科研定义入口仍为[27项v0.4](../docs/research/definitions/README.md)。

下方保留各任务发生时的历史事实；不以旧块覆盖本节当前状态。

## Historical — P3 Task2 research boundary (2026-11-03)

P3 Task2已新增独立版本化controller evidence接口与14类记录、显式关联验证器和A–H合成契约验证。schema=aad.p3.controller-evidence.v1；候选策略输入采用边界仍PROPOSED，scientific_claim_eligible=false。真实接收/策略/安全/执行路径尚未接线；P3基础接口可阶段性收口，后续P7直接复用，P5负责采用因果识别。

Received/Considered与POLICY_INPUT_INCLUDED分开；输入纳入事实不代表正式Adopted或Adoption-induced Action Effect。安全覆盖/零命令不抹去消费，缺失不补False。assignment/adoption_mode仅元数据，不冻结P5开关语义，不按采用筛选ITT。

[Task2报告](../docs/research/P3/P3_TASK2_FINAL_REPORT.md) · [接口/P7接入](../docs/research/P3/CONTROLLER_EVIDENCE_IMPLEMENTATION.md) · [证据](../evidence/research/P3_TASK2_20261103/README.md)。统一定义仍[27项v0.4](../docs/research/definitions/README.md)。

## Historical — P3 Task1 research focus (2026-11-03)

P3 Task1完成只读机制审计、三份Proposed v0.1契约和WP0–WP4路线修订。WP0=P0/P1；WP1=P2/P3/P4并行；WP2=P5/P6；WP3=P7/P8；WP4=P9；历史P编号/Task ID不变。P2阶段性收口，保留V/归属/严格桥接缺口，不自动追加实验。

物理链、信息链、动作—风险链分别建立证据。Message Validated、Controller Adopted和Adoption-induced Action Effect是不同层级。消费凭证支持机制可观测性，作用仍需P5适当干预；沿用P1的assignment ITT和最终四格，不按adopted筛选主分析。

现adopted由fixture设计条件或工程时程赋值，不是控制器消费凭证。Stage0.1已有孤立SUMO setter/native readback，但缺Message–Receipt–Decision–Command–Execution关联、controller/policy版本与实际安全层日志；时间排序/配对动作差异不足以证明采用因果作用。

下一项建议是一次有界凭证/引用接口与最小合成契约验证，再交P7；具体采用边界、controller/policy/安全层与Enabled/Disabled语义仍待研究者接受，不自动启动实验。

[报告](../docs/research/P3/P3_TASK1_FINAL_REPORT.md) · [生命周期](../docs/research/P3/MESSAGE_LIFECYCLE_CONTRACT.md) · [采用契约](../docs/research/P3/CONTROLLER_ADOPTION_CONTRACT.md) · [通信登记](../docs/research/P3/COMMUNICATION_ASSUMPTIONS.md) · [规划迁移](../docs/research/P3/ROADMAP_REVISION_NOTE.md)。统一定义仍[27项v0.4](../docs/research/definitions/README.md)。

Formal A=0；Independent Qualified Witness=0；F0/Overall TR–TP=Unknown；Stage0.5=CLOSED_WITH_LIMITATIONS；Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock=BLOCKED；Stage I=READY_ENGINEERING_ONLY；Stage1.1=NOT_AUTHORIZED。

## Current — P2 Task6 final calibration protocol (2026-11-02)

统一科研定义入口：[docs/research/definitions/README.md](../docs/research/definitions/README.md)，当前v0.4、27定义；下方旧任务块保留历史。

当前科研方向：Micro/Macro/Cohort分别报告，Edie型同域分lane主要候选，Qpre后随机ZC的资格ITT/F0不替四格交互；onset/确认/观察分开。先SAC、逐项、关键交互和独立验证选择稳定参数区域。有限scope，未观察Witness不等无物理影响，采用/动作/风险不合并。

Formal A=0、独立Qualified=0、F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS，Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS，Protocol Lock BLOCKED，StageI READY_ENGINEERING_ONLY，Stage1.1 NOT_AUTHORIZED。

[最终报告](../docs/research/P2/P2_TASK6_FINAL_REPORT.md) · [参数实验协议](../docs/research/P2/P2_TASK6_PARAMETER_DETERMINATION_EXPERIMENT_PROTOCOL.md) · [集中决策](../docs/research/P2/P2_TASK6_RESEARCHER_DECISIONS.md)

## Historical — P2 Task5 measurement and identification operationalization (2026-11-02)

统一科研定义入口：[docs/research/definitions/README.md](../docs/research/definitions/README.md)。本节只作摘要导航；下方旧任务块为历史。

Recommend separate micro/macro/cohort arrival objects with endpoint-specific F0^Q, not an OR/AND scalar. Same lane-space-time D/V/A measurement distinguishes macro operator onset from first raw physical influence. Qpre precedes ZC but may follow ZS; qualified two-arm τQ and full four-cell τSC need different support. Allowed-time sets and design-valid simultaneous bounds retain Unknown/clock/multiplicity; no empirical time separation or numeric thresholds established. Joint lifecycle/risk/reference contribution remains Hypothesis.

[Task5 final report](../docs/research/P2/P2_TASK5_FINAL_REPORT.md) · [proposal](../docs/research/P2/P2_TASK5_MEASUREMENT_AND_IDENTIFICATION_PROPOSAL.md) · [decisions](../docs/research/P2/P2_TASK5_RESEARCHER_DECISIONS.md)。

## Historical — P2 Task4 related work, claim boundaries and definition synchronization (2026-11-02)

统一科研定义入口：[docs/research/definitions/README.md](../docs/research/definitions/README.md)。本节仅摘要导航；下方旧任务区块保留为历史，冲突以统一定义当前版本和可核验证据为准。

A–D are now Agreed, not all Awaiting: investigate information-mediated regional risk before arrival within a predeclared independently observable physical scope. Micro W1–W9 and macro traffic state are complementary; fixed-cohort signed decline remains important but cannot exclude all regional physical effects. Scope-specific evidence vector and Edie-type operator are proposals, not new binary arrival rules.

Qpre is pre-ZC but can be post-ZS; qualified two-arm τQ and F0^Q cannot replace whole-source four-cell interaction/F0. P1 population time framework is retained. Jerath already covers information→control→macro delay/ZOI; Saberi/Duan/Zhang constrain propagation/early signal/event graph novelty. AAD joint identification remains Hypothesis, NC claim unsupported. See Task4 literature audit and CORE细则H/I.

Stage0.5=CLOSED_WITH_LIMITATIONS；Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock=BLOCKED；StageI=READY_ENGINEERING_ONLY；Stage1.1=NOT_AUTHORIZED。

## Historical — P2 Task1 physical operationalization (2026-11-02)

P2 defines Source Event A as the unchanged Formal P2 route and B as an explicitly separate safe controlled perturbation mechanism domain. Physical propagation is a time-respecting path in G_P(t), with Potential Physical Path, Observed Physical Interaction and Qualified Physical Propagation Witness as separate statuses. Physical arrival is \(T_P=\inf\{t\geq t_E:\phi(X^*_{\mathcal T}(t),B_{\mathcal T})=1\text{ with persistence}\}\); the leading candidate is a sustained relative-baseline speed state, while gap/density are auxiliary and Formal rho/P2 is not the direct arrival definition.

SUMO Observer is read-only model evidence and does not create no-message counterfactuals. The ordinary physical reference is a future Z_C=0, Z_S=1 run distribution. All thresholds, persistence, path admission, clock/error tolerances, source scenarios and region boundaries remain Awaiting Researcher Decision. See docs/research/P2/P2_TASK1_FINAL_REPORT.md.

## Current — P1 Task2 decision synchronization and causal refinement (2026-11-01)

The researcher has confirmed the D1–D10 directions in AAD-P1-TASK2. Current scope is SUMO model-internal causal mechanism work with an automatic controller, source-present two-arm regional-risk ITT as the entry analysis and a required final four-cell design. Formal P2 and safe controlled perturbation remain separate source domains; target cohort/region/window are pre-fixed in principle; the SUMO Observer is read-only and is not a real roadside sensor; communication is direct single-hop; the first temporal claim is population-level; Pilot comes before SESOI/power/sample-size planning.

The refined theory separates assignment Z_S/Z_C from actual S*/C* states and true process from observed logs/Observer records. H2 distinguishes adoption rate, encouragement reduced form and IV/LATE; H3 lists action-intervention, IV, longitudinal g-formula and interventional indirect-effect candidates; H4 defines population risk-curve onset and no-message physical-arrival distributions. Operational parameters remain Awaiting Researcher Decision. See docs/research/P1/P1_TASK2_FINAL_REPORT.md.

## Historical — P1 Task1 theory and causal model (2026-11-01)

P1 formalizes AAD with two coupled but distinct networks: physical interaction G_P(t)=(V,E_P(t)) and information propagation G_I(t)=(V,E_I(t)). The joint state uses physical state x, message/lifecycle state m, controller decision/command/actual input and fixed-region Formal rho/P2 risk. Message generation, transmission, delivery, verification, adoption, command, action and regional risk remain separate events with times T_G,T_S,T_D,T_V,T_A,T_C,T_U,T_R; ordinary physical arrival T_P needs an independent time-indexed witness.

The causal framework preserves the planning four-cell interaction tau_SC and the P0 source-present two-arm tau_ITT^(S=1) as different estimands. Under interference, potential outcomes depend on the full assignment vector; adoption/action are post-treatment mechanism variables and are not identified by subgroup comparisons. H1–H4 are falsifiable, but all substantive D1–D10 choices remain Proposed / Awaiting Researcher Decision. See docs/research/P1/P1_TASK1_FINAL_REPORT.md.

# AAD Research Context

## Historical — P2 Task2 operational method package (2026-11-02)

### 研究背景

AAD 的研究问题仍是比较信息传播链与普通物理传播链在固定目标区域中的总体时间关系。P2 Task2 only operationalizes the physical-arrival and no-message reference definitions; it does not claim the AAD hypothesis is supported.

### 研究问题

The task asks when a physical source state begins, when it becomes formally confirmed, how physical influence paths are admitted, how a regional state function \(\phi\) is computed, and how \(F_0(t\mid H,Z_S=1)\) is identified without confusing no-message with no-source or delivery failure.

### 问题建模

The physical network remains \(G_P(t)=(V,E_P(t))\). Micro vehicle interaction paths and macro speed/density wave fronts are separate objects. `T_R` remains population-level risk-effect onset; `T_P` is a qualified physical-arrival onset with interval, censoring and clock uncertainty.

### 现有方法

Traffic-wave theory supports macro space-time fronts; trajectory methods support candidate state-change detection; interval-censoring methods support interval event times. None of these sources supplies AAD thresholds or causal witness status.

### 当前项目采用的方法

Use source-onset intervals for the physical chain and confirmation for Formal P2/message eligibility. Prefer micro same-lane longitudinal response evidence for Qualified Witness. Use equal-vehicle signed relative-baseline speed decrease as the leading \(\phi\) proposal, with pre-fixed cohort/region/window and explicit coverage. Estimate the no-message reference from source-present `Z_C=0` assignments when source qualification precedes communication randomization; retain SUMO paired paths as model-only auxiliary evidence.

### 当前科研假设

H4 remains a population-level temporal-precedence hypothesis only. The current work cannot identify a treated event's cross-world \(T_P(0)\), and interval overlap, missing witness, unresolved censoring or clock uncertainty returns Unknown.

### Research Rationale

Separating onset from confirmation avoids a systematic physical-time delay. Separating micro paths from macro fronts prevents a traffic-wave detector from being treated as vehicle-level causality. A source-present randomized no-message arm preserves the intended reference population; a model pair cannot replace it.

### 核心研究逻辑

Source qualification → physical onset interval → time-respecting qualified edges → target-region state function → arrival onset/confirmation and censoring. In parallel, source confirmation → message eligibility → message lifecycle. The two clocks share audit fields but keep their meanings.

## Historical — P2 Task3 scientific scope and evidence (2026-11-02)

统一科研定义入口：[docs/research/definitions/README.md](../docs/research/definitions/README.md)。本节只摘要，最新定义、参数与状态以该入口及对应证据为准。

### 研究背景

Task3 unifies source/onset/confirmation, state arrival, no-message reference and paper alignment without treating calibration as confirmation.

### 研究问题与建模

The proposed Δu^B full-cohort mean measures sustained baseline-relative decline, not the first entry of every physical mechanism into a geometric region. B-domain s1–s4 response candidates were inside the region while the pre-fixed s5–s10 cohort did not alarm. This is a material claim-scope limitation awaiting researcher review. Fixed cohort×region support can become structurally undefined on exit; observed-subset averages do not automatically represent fixed N.

### 因果与统计边界

TP is an event random time; F0 is its no-message population reference. TR is a population risk-effect onset. P1 §7 fixed-H* and jointly valid risk/arrival bounds remain the preferred comparison; no treated-event cross-world seconds are identified. Qualification before ZC randomization supports a prequalified subpopulation, not automatically the full ZS=1 population. A sources and independent Qualified paths remain zero, F0/temporal precedence Unknown.

### 文献与论文

PAPER-SKILL/Zotero workflow completed bounded reading and five new sources. Core full texts and chapter-only/background reads are distinguished. Overleaf was not edited; missing immutable snapshot and exact quotes/lines limit the completed alignment audit.

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
