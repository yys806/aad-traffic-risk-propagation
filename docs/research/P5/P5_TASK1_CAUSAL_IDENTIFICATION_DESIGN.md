# P5 Task1 因果识别方案审计与设计

Task ID：AAD-P5-TASK1-20261104。日期：2026-11-04。

状态：DESIGN_COMPLETE_WITH_OPEN_IDENTIFICATION_DECISIONS。这是设计层交付状态，不是实验准入或因果效应验证。本文沿用[统一定义 v0.4 / 27 IDs](../definitions/README.md)、[P1 estimand](../P1/ESTIMAND_SPECIFICATION.md)及最新 P3/P4/P7 决定，不新增 Definition ID，不更改 H1–H4。局部数学记号用于条件比较，不建立第二套科研定义。

## 1. 结论与证据层级

**Inference：当前资格两臂与最终四格可以并存，但必须分别报告。** 当前可由所述随机设计识别的对象是 source-present、Qpre=1 的通信策略 ITT；这不表示已有可估计的真实数据。最终四格需要共同源前总体、明确的四格干预/分配支持及一致的结果支持。只在 Qpre=1 分配通信不能补齐非资格和 source-absent 的效应。

**Proposal：采用“当前 A + 最终 B 候选 + C 备选”的架构。** A 保留资格两臂；B 在研究者确认的源前 source-opportunity 总体上设计最终四格；C principal stratification 仅在额外假设可辩护时作为敏感性或部分识别路线。B/C 均未批准，不改变最终四格方向。

**Fact：当前具备消息实际消费、决策、命令、执行和目标车辆实际状态的证据链；P4 已实现固定 N 的完整区域风险测量接口。** P7 Task2.1 只有目标车辆轨迹，没有完整区域资格名单、全部成员轨迹和正式 region/window，不能成为完整区域 Y 样本。单次 Enabled v2 及历史基准是工程诊断，不是随机化机制实验。

**Unknown：当前任何真实 H1–H4 效应。** Formal A=0，Independent Qualified=0，F0 与总体 T_R–T_P Unknown。Stage0.5=CLOSED_WITH_LIMITATIONS；Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock=BLOCKED；Stage I=READY_ENGINEERING_ONLY；Stage1.1=NOT_AUTHORIZED。本任务没有交通运行、seed、Pilot、V、holdout 读取或生产代码变更。

Effect、Attribution、Temporal Precedence 分别回答区域政策效应、消息来源与执行可追溯性、总体早窗条件。日志可支持 Attribution；本项目主 ITT 还需有效随机分配设计和合格 Y；匹配的独立物理观测及联合时间推断才可能支持 Temporal Precedence。三者不能互替。

## 2. 事实源、版本与审计冲突

事实优先级遵循 AGENTS：当前源码/config/机器证据优先，再读 Context 与普通文档。以下只读核查没有调用控制器或运行器。

|来源 / 定位|实际核查事实|识别支持与限制|
|---|---|---|
|[P1 estimand §§2–10](../P1/ESTIMAND_SPECIFICATION.md)、[研究者决定](../P1/P1_TASK2_RESEARCHER_DECISIONS_20261101.md)|当前 source-present ITT；最终四格；机制与总体时间分开|设计目标已确认；具体分配和数据支持未成立|
|[统一定义 DEF-POP-001、细则 I/M/N/R/T](../definitions/CORE_SCIENTIFIC_DEFINITIONS.md)|Qpre 相对 ZC 为前、相对 ZS 可为后；三层 F0；Unknown 和检测桥接|本文细化既有边界，不修改其状态|
|[P3 ratification](../P3/CONTROLLER_ADOPTION_RATIFICATION_20261103.md)|Adoption 已于 2026-11-03 正式 Agreed|旧 Proposed 不能覆盖新正式边界|
|[P7 runtime：decide](../../../code/src/riskprop/p7_message_runtime.py)、[RunAssignment](../../../code/src/riskprop/message_driven_longitudinal_controller.py)|先验证，再由 available 与 ENABLED 控制策略输入；消费回执关联 decision；模式必须保持|证明实际开关路径；RunAssignment 校验固定值，不抽签、不记录设计概率|
|[formal_design.py：validate_four_cell_configs](../../../code/src/riskprop/formal_design.py)|验证四格配置及共同字段、源/通信开关|配置兼容检查不是随机化器，也不证明 Q(1) 跨源可见|
|[P4 工程契约](../P4/P4_MEASUREMENT_DATA_CONTRACT_v1.md)、[assignment_result](../../../code/src/riskprop/p4_measurement_bundle.py)|独立 P4 v1；assignment 结果、名单 hash、固定域窗、Y 界、质量与来源；Unknown 仍输出|POINT_IDENTIFIED 是测量贡献状态，不是因果识别；不筛消息失败或无命令车辆|
|[P4 Task2 报告](../P4/P4_TASK2_FINAL_REPORT.md)、[验证](../P4/P4_TASK2_VALIDATION_REPORT.md)|172 项离线测试、15 项独立数学复算是历史已验证事实|本任务不重跑、不将合成验证变成因果样本|
|[P7 Task2.1 报告](../P7/P7_TASK2_1_FINAL_REPORT.md)|352 行目标轨迹；52 次采用、39 命令、326 执行；真实 TraCI 路径已接通|次数非独立 n；无完整区域 Y；合成源资格不能提升为 Formal A|
|[P2 Task7](../P2/P2_TASK7_FINAL_REPORT.md)、[Task8](../P2/P2_TASK8_FINAL_REPORT.md)、[源时钟回溯](../P2/P2_TASK7_SOURCE_TIMESTAMP_BACKFILL_REPORT.md)|B 类有限支持/校准及历史失败保留；独立 V 未执行|不是 Formal A、独立 Qualified 或 F0；不读取原始大表/holdout、不重新运行|

历史状态接续审计：

|Documented Intent / 历史记录|Actual Implementation / 当前状态|Evidence / Affected Files|Conflict / Status|
|---|---|---|---|
|P3 原实现报告中 Adoption=Proposed、真实 producer 未接线|最新 ratification 已 Agreed，P7 已真实接通|上表 P3/P7，历史 [P3 实现说明](../P3/CONTROLLER_EVIDENCE_IMPLEMENTATION.md)|Historical superseded；有日期接续，不改旧报告|
|Task6/E61 最终 Y 算子待决|P4 2026-11-04 D03-B/D04-A 已确认|[P4 决策](../P4/P4_RESEARCHER_DECISIONS_20261104.md)、[账本](../definitions/EVIDENCE_AND_ASSUMPTION_LEDGER.md)|Historical superseded；Task7/E61 是另一条有限校准授权|
|四格配置中 channel_enabled；P7 中 adoption_mode|分别表示通信开关和输入采用开关，不天然相同|formal_design.py 与 RunAssignment/decide|政策对照映射尚缺；Awaiting Researcher Decision（P5-D03），暂停任何把二者等同的识别主张|

没有发现需修改正式算法才能完成本次设计的冲突。上述政策语义缺口以待决记录保留，没有通过修改代码、历史报告或定义消除。

## 3. 测量结果与处理变量

### 3.1 完整资格总体的区域结果（Agreed，P4）

对独立分配单位 e，固定名单 C_e^elig、N_e、region/version、W_e=[t_s,t_e)、L_e=t_e−t_s：

\[
Y_e(a)=\frac{1}{N_e}\sum_{i\in C_e^{elig}}\frac{1}{L_e}\int_{W_e}b_{ie}(t;a)\,dt,\qquad 0\le Y_e\le1.
\]

Formal rho=exp(−TTC/τ) 及既有参数不变；车辆贡献 b 的区域/缺失语义沿用 P4。完整资格总体包括没有消息或命令的合法成员（NATIVE_NO_COMMAND），不是只包含接收车辆。名单固定不代表实际轨迹无缺失；缺车留界，不缩 N；区域总体本身不明则 UNKNOWN_SCOPE，不能发布完整 Y。

P4 名单必须早于它所服务的处理分配。现行资格两臂可在源后、ZC 前冻结；**这不足以证明四格中 roster 对 ZS 也是处理前且共同**。若选择共同源前四格，需在 ZS 前确定跨四格可绑定的需求角色、域和窗；不按源/通信处理后的入区车辆重组名单。

Y_e(t) 或窗口序列须事先固定时间算子和网格，仍用相同资格名单、版本和预定分母。不能把单个风险样本、只保留有观测车辆的均值或宏观速度当作这一 Y。时间化结果和正式 T_R 的具体规则仍待批准。

### 3.2 三类政策对照不能静默合并

|对照|处理内容|可回答的问题|当前边界|
|---|---|---|---|
|通信政策 C=1 vs No Message C=0|生成/发送/交付/采用等整套政策及其失败|通信政策对区域 Y 的总 assignment 效果|需定义 policy 版本与 no-message 参考；最终主对照待明确|
|Enabled vs Disabled（用局部记号 Z_A 表示开关分配）|两组接收验证，仅 Enabled 允许纳入策略|采用开关对实际运动响应/区域 Y 的 reduced form|P7 路径已实现；未实际随机化，不能把历史差异当 ITT|
|实际 A*=1 vs A*=0|处理后是否真的采用|描述性机制状态；在额外条件下才可能 IV 等因果对象|不能直接分组识别；收到无效消息或未改变命令不等于同一采用版本|

No Message 与 Disabled 在既有场景轨迹相同，也不证明全目标域因果等价：网络负载、验证计算、调度时间、反馈与原生控制可能不同。用于 F0 的“无消息/无通信政策”必须与 H1 的相应控制版本一致，或给出明确且可辩护的桥接；不能直接更名。

## 4. Task A：三个估计对象与 Qpre / 四格

### 4.1 对象、总体与识别

下表沿用 P1 的潜在结果，不把实际源实现与源 assignment 混为一谈。

|对象|目标总体 / 处理 / 结果|设计识别的必要条件|当前支持|
|---|---|---|---|
|τ_ITT^(S=1)=E[Y(1,1)−Y(1,0)]|共同声明总体中 source-present 的通信政策平均效果；Y 为固定完整区域结果|在该完整总体内通信正支持/随机化、well-defined policies、干扰处理、一致结果/缺失|只在 Qpre=1 分配时不能识别整个 S=1 总体|
|τ_Q=E[Y(1,1)−Y(1,0) \| Q(1)=1]|source-present 的通信前合格子总体；Q(1) 是在有源条件下的潜在资格|Q 在 ZC 之前、通信盲且无提前暴露；Q 内已知正概率随机 ZC；完整 assignment 记录和合格 Y 界|当前首选设计入口；尚无实际合格随机数据|
|τ_SC=μ11−μ10−μ01+μ00|共同源前总体的 Source × Communication 加性交互；μsc=E[Y(s,c)]|共同总体/支持、四个明确干预、四格正概率及有效源/通信分配、同域同窗结果、干扰处理|最终目标保留；现有资格两臂不够|

Qpre 是相对 ZC 的处理前资格，但可受 ZS、源实现、观测与交通状态影响。因此 Q(1)=1 的观察不是跨源 baseline。H_C（源后、通信前状态）可用于资格两臂的预定分层；四格共同 H0 必须在源分配之前。不能通过调整 H_C 消除源作用后仍称源总效应。

在共同总体/结果/权重下，令 p=P{Q(1)=1}：

\[
\tau_{\rm ITT}^{S=1}=p\tau_Q+(1-p)\tau_{\neg Q},\qquad
\tau_{SC}=p\tau_Q+(1-p)\tau_{\neg Q}-\tau_{\rm ITT}^{S=0}.
\]

这是全期望恒等式（Inference），不是缺失效应识别器。不知道 τ非Q 或 τS0 时，不能用 0 补齐。即使 p=1，τQ 也只有在额外知道 τS0=0 时才等于 τSC；当前没有这种批准或证据。

### 4.2 A / B / C 设计比较

|维度|A：当前 Qpre source-present 两臂|B：源前共同 source-opportunity 四格（Proposal）|C：principal-stratum 四格（Proposal）|
|---|---|---|---|
|科学解释|合格有源机会中的通信策略效应|共同源机会总体中的源×通信交互|在潜在 Q(1)=1 或 (Q(0),Q(1)) 分层内的效果|
|分配|源/资格确认后随机 ZC；分配前无通信|ZS、ZC 按事先协议分配于共同源前机会；允许明确的序贯/动态政策|有效四格分配仍不够，还需潜在资格识别|
|正支持|Q=1 内每一通信臂正概率|共同总体每所需 cell / 动态政策正概率；nonQ 与无源政策有定义|各目标 principal stratum 的潜在处理支持和可识别成员/界|
|主要数据|Q 时间/盲法、assignment 概率、完整 Y、失败、H、独立物理参考|源前机会/名单/H0/clock、所有源分配及失败、四格记录|Q 潜在值的额外代理/模型/假设与可审计敏感性范围|
|与既有决定|直接兼容当前入口；不外推整体|兼容最终四格方向；具体共同总体未批准|不改四格方向，但增加假设；当前不能批准点识别|
|当前实施能力|有测量/工程接口，缺合格源、随机器、完整真实 Y|缺共同机会、源干预/分配、无源策略、四格支持|缺跨源潜在资格信息及假设依据|
|优点 / 代价|识别清楚；总体较窄|解释交互清楚；设计与数据条件更多|尊重潜在资格问题；通常只能得到宽界或模型依赖结论|

B 中 source-opportunity 必须是四格都可定义的源前机会，例如预列道路时段和需求角色，不是事后“实际出现源”的事件池。随机分配源诱发机制不保证实际 Formal P2 源成功；必须分别记录 ZS、实际 S*、Q、失败。全体 source-assignment ITT 应保留源未实现单元；若只保留源实现者，则需新的条件因果论证，不能继续声称原 assignment ITT。

如果未来采用“仅 Q 时发消息”的动态策略，必须在所有源机会、nonQ 和 source-absent 中事先定义策略行为。它可成为另一个明确的政策 estimand，但不能因此宣称现有 τ非Q=0。源确认后 fork 两通信臂可作模型配对；已受源影响状态不能再 fork 成无源臂并称源前共同起点。

### 4.3 principal stratification 的非识别与可选界

随机 ZS 识别潜在结果边际，不显示无源单元的 Q(1)。即使 Q(0)=0，仍不知道其是否在有源时合格。Principal stratum 的定义可以不随实际分配改变，但成员和相应效果未必被数据识别。[M3] 不允许把“定义为处理前属性”误读成“已观察到”。

确定性反例：两类潜在人群各半，Q(1)=0/1；所有有源 Y10=Y11=1/2；无源 Y00=1/2。世界 A 中 Y01=Q(1)，世界 B 中 Y01=1−Q(1)。四格可观测结果边际和有源 Q 分布完全相同，τQ=0、全体 τSC=0 也相同；但在 Q(1)=1 中无源通信效应分别为 +1/2 与 −1/2，因此该 principal-stratum 四格交互分别为 −1/2 与 +1/2。随机化本身不能选择世界。

有界 Y 可提供不依赖补零的保守界。若 p>0 已识别，m0c=E[Y(0,c)]，则：

\[
\max\{0,(m_{0c}-(1-p))/p\}\le E[Y(0,c)\mid Q(1)=1]\le\min\{1,m_{0c}/p\}.
\]

分开相减给 τC^(S=0,Q1) 的保守界，再从 τQ 相减给条件交互界；不保证最窄。Principal ignorability、跨源 rank/结构模型、代理识别等若要压窄，必须说明并经研究者批准；不能靠随机源或简单加权自动获得。p=0 时该条件 estimand 无定义。本文没有批准任何这些假设。

**明确结论：** 当前 A 可保留为资格子总体主分析；最终四格需要独立补齐 B 的共同源前总体和分配条件，或接受 C 的额外识别/部分识别限制。A 的完成不完成四格，也不妨碍最终四格继续保留。

## 5. Task B：分配单位、重复和网络干扰

### 5.1 单位对应表（具体设计均 Proposal）

|候选|assignment 单位|结果 / 独立推断单位|信息/物理干扰与支持|适用判断|
|---|---|---|---|---|
|车辆随机|车辆或控制器|车辆嵌套 run；不能当独立 iid 车辆|邻车动作/消息改变彼此 Y；需预定 exposure、混合分配正支持和簇推断|当前不推荐作为首版；P7 无相应分配矩阵|
|完整 run|一次完整道路系统运行的稳定政策|每 run 一个固定区域 Y；共同初态配对需保留 block|域内溢出纳入总政策效应；需隔离跨 run 状态/消息/缓存|首版优先推荐；不等于已实现随机化|
|道路时间簇|预定路段×时段政策|簇级 Y，簇间依赖须处理|边界车流、长程消息和排队 carryover 均可越簇|有 buffer/reset 与域覆盖证据时才考虑|
|matched-block|源前场景/需求/随机流形成 block，块内安排政策|配对/块内差及独立 blocks；不是单个 seed 字符串的自动 iid 性|共同随机数降低方差但带来依赖；同步改变随机流调用需审计|兼容 run 方案；P6 另定分配/权重/方差|

同 run 的车辆、帧、消息和决策共享交通状态，不能增加独立 n。同 seed 四格运行可能是一个 block 的四个潜在政策实现；重复执行相同 seed 的确定性轨迹不会产生新总体信息。一个 block 不能估总体重复间方差。不同 seed 也不自动保证独立：共同 scenario、缓存、共享 controller/网络状态与上游抽样都需记录。

推荐分开字段：experimental_unit_id、assignment_id、run_id、block_id、event_id、role/member_id、sample_id。P4 的 assignment_result 提供测量侧 assignment 单位，不替代未来设计确定的独立 block/簇。

### 5.2 两种干扰域及效应

信息域 G_I 表示消息/策略可到达的对象和路径；物理域 G_P 表示车辆交互、排队、边界流量及反馈可能传播的范围。二者可不相同，单跳通信不意味着物理干扰也只有一跳。控制后的物理影响也会改变后续消息和资格，须按时间展开记录。

Partial interference 是“簇间没有影响”的设计/科学假设，需要信息网络隔离、车辆边界/排队范围、时间 carryover 以及未监测机制的证据。既有日志没有跨簇消息不等于没有未监测物理影响。若假设不成立，可扩大分配簇或提出预定 exposure mapping；这都是待决定的设计，不能通过多加协变量修复未知泄漏。[M1–M2]

|效应|所比较对象|所需支持|当前可支持的设计方向|
|---|---|---|---|
|Total Policy Effect（本项目运行/簇总政策效应）|整个域分配政策 π1 vs π0 后区域 Y|域级稳定政策、正支持、跨域处理或隔离|当前优先；包含域内 direct 与 spillover 通路，不要求拆开|
|Direct Effect|固定邻域 exposure 下本车分配改变的结果|本车 treatment 与相同邻域 exposure 的混合 cells 均有支持|全 run Enabled/Disabled 没有自动支持|
|Spillover Effect|固定本车分配时邻域 exposure 改变|同本车 assignment 下多个邻域 exposure、有效 mapping|当前未具备|

此处“区域总政策效应”不是 Hudgens–Halloran 所有 individual-level total/overall estimand 的同义词；应在具体设计中声明平均层次、邻域策略分布和权重。不能直接把其 individual direct+indirect 恒等式套到当前完整区域 Y。

若采用 Aronow–Samii 式 exposure mapping，应从设计分配向量与预定义网络/基线特征计算 E_i=f_i(Z,G0)，说明 exposure 概率和映射充分性（相同 exposure 是否足以约束潜在结果）。实际 delivery、adoption、leader/action 是处理后实现；直接用它们分组或调整会引入选择，不能冒充已随机化 exposure。动态网络需额外时间化定义及识别，不是用事后拓扑自动满足条件。

### 5.3 index source、多事件和时间

每个独立单位建议按通信盲、只用允许的处理前资料预定 index-source 机会/顺序规则，并记录无资格、源失败与删失；这还是 Proposal。运行开始先选道路时间机会，再在 source-present 资格确认后随机 ZC，与随机未来事件发生后按最显著风险选择 source 不同。

一个 run 的后续事件数可能受通信影响。按后续事件数量扩充独立 n、只保留发生的事件、按事件等权替代运行等权都会改变对象。可选路线是预定 index 机会、固定运行级复合结果，或明确簇内预列事件和权重；没有机会/事件时如何输出需协议先定义。当前不通过删除失败解决。

从资格确认时刻随机 ZC 的设计若在 confirmation 前已收到策略相关消息，则 Q 不再可靠地是通信前变量。运行级固定模式在 P7 是工程模式，不证明科学设计已经完成；未来可在无提前暴露条件下先确认、再冻结该运行剩余段模式，但不能本次直接改实现。

## 6. Task C：Adoption 的三层研究对象

继承链：D*→V*→A*→Ucmd,*→U*，并由实际运动状态 X* 观测其响应。P4 Δv 主/Δa 辅是实际响应测量；速度不是未经说明就等于控制输入。采用事实由策略输入和消费凭证定义，不由轨迹反推。

|层次|对象|识别 / 数据要求|允许解释|
|---|---|---|---|
|采用率|预定消息×决策机会中有效输入纳入比例，或预定 run 级描述|完整机会分母、有效性/消费/decision ID；未知单列|链路描述；重复使用同一消息不新增独立样本|
|开关 reduced form|E[M_U(Z_A=1)−M_U(Z_A=0)]，M_U 为预先规定的实际响应曲线/量|随机分配开关、共同观测/角色/clock、稳定策略、簇级干扰与缺失|采用允许策略的 assignment 效果；不是 A* 自身效果|
|Adoption IV/LATE|在明确定义的二元采用对象下 complier 平均动作效果|下列全部 IV 条件及处理版本成立|局部机制效果，不是全部车辆/全部采用者效果|

采用率分母不能事后只取导致动作变化的消息或可成功关联的决策。有效消息/决策机会数量本身可能受反馈影响；条件采用率仍只作描述，不把其臂间差当作随机处理效果。尚未批准一个 run 级二元“有过采用”替代多消息、多周期 A*。

### 6.1 IV 条件审计

1. **Relevance：** 开关必须改变明确定义的实际 A*；不能只看到 Enabled 收到消息就认为第一阶段成立。无有效消息、过期和原生约束可能导致弱/零第一阶段。
2. **Independence：** Z_A 在目标机会/干扰簇内确实随机，已知概率且无提前暴露。P7 固定运行 assignment 不提供随机机制证据。
3. **Exclusion：** Z_A 对动作的所有作用必须经所定义 A*。额外计算、时序、模式、其他消息/控制输入和邻车路径都须审计；日志完整不证明没有额外路径。
4. **Monotonicity：** 对同一单位/定义良好的二元采用，A*(1)≥A*(0)。对预定固定机会且 Disabled 结构上恒为0的采用，单调性可由单侧 gate 支持；若明确预定run级“曾采用”且Disabled恒为0，也有这一二元结构性质。但不能因此把多周期采用历史、强度或实际动作当成同一二元处理：先前动作会改变后续有效性、到达和决策机会，处理版本/共同支持仍需论证。单侧采用也不证明排除限制。
5. **Positivity / consistency：** 同资格/背景下开关概率正；采用处理及其时间、消息内容、controller/安全版本足够明确，没有无法区分的多版本；干扰按设计处理。

仅在上述二元、单一对象和完整假设下，Wald 比值 RF/first-stage 才有标准 complier LATE 解释（[M4]及其作者书第16章）。多维连续动作、重复采用或 time-varying exposure 不能直接代入同一比值并声称二元 LATE。弱工具或违反条件时报告 reduced form / 描述，不输出 Adoption 因果点效应。

P7 D6 不新增独立 Safety Layer 不是排除限制证明；SUMO 原生约束、执行失败和安全覆盖仍需完整保留。若覆盖是 A* 的下游，它可以属于所定义总机制；若开关直接改变覆盖/其他控制，就是额外路径，须结构区分。不能为满足 IV 删除覆盖/失败样本。

**当前结论：** Adopted 日志事实已具备；率可在声明分母后描述；开关随机化 reduced form 尚无正式数据；IV/LATE 是未批准备选。本任务不新增 encouragement。

## 7. Task D：Action–Risk 因果识别

目标链 A*→U*→X_T*→Y_T* 的各箭头需要自己的设计。随机通信可识别通信政策对 Y 的总效果，但通信会影响多辆车、多种控制和网络状态，不自动是单一目标车辆 U* 的有效工具。adopted/not-adopted 分组有处理后选择；普通 Y 对动作/加速度回归不能消除交通状态、危险程度和原生控制的混杂。

|路线|具体 estimand / 条件|时间混杂、干扰、正支持|需要数据 / 当前可行性|
|---|---|---|---|
|随机动作干预 / encouragement|分配动作策略 g vs g' 对完整区域 Y 的效果；实际 U 效果还需实现一致性或不依从识别|动作可定义/安全/实施；随机化覆盖整个物理干扰域；各策略有正支持|全成员状态、执行/原生约束、完整 Y、真实随机日志；目前无授权/数据。仅 assignment 效果不等于固定 realized U 的效果|
|IV|工具引起的特定动作改变对 Y 的局部效果|工具相关、独立、排除/单调及版本明确；连续/多动作需相应结构条件；全网额外通路不能忽略|动作 first stage、区域 Y、外路径审计；当前没有有效工具证据。不能直接把 ZC 当作目标车速度工具|
|纵向 g-formula|预定动作/动态策略历史下 E[Y^g] 的对比|全历史 sequential exchangeability、consistency、sequential positivity；处理影响的时变混杂需按时间建模，不能普通回归调整|全网/簇交通状态、leader/lane、风险、原生控制、消息、执行、质量与删失历史；P7 单车不足，确定性控制器可能无替代动作支持|
|Interventional indirect effect|明确随机 mediator 干预分布 G 下的风险变化，例如在固定政策时改变动作分布|仍需可识别 mediator–outcome、暴露/混杂历史和正支持；全网动作应有物理可行联合分布|完整纵向交通/消息/动作/风险；当前没有相应数据或批准模型；不是默认 natural indirect effect|

g-formula 的技术条件示意：给定动作前的全网历史 H_t（含以前动作影响的 L_t），要求 Y^g ⟂ U_t | H_t，以及 g 要求的动作在该历史下有支持。对有限离散时点，可通过各时点 p(L_t|过去 L/U) 与末端 E[Y|L/U 历史] 的逐次积分/求和评估策略。该公式只是方法条件说明，不是已选模型或已执行估计。位置/间距/leader 既可受过去动作影响又影响后续动作/风险，遗漏或在普通回归中机械控制可能出错。[M5]

Interventional effects 用可定义的随机 mediator 分布替代自然中介的跨世界耦合，但不会免除混杂、测量、网络或支持条件。[M6] 的多 mediator 论文不能直接当作本项目复杂纵向全网识别定理；若采用此路线，必须另行指定时间顺序、联合动作分布、反馈及估计对象，研究者批准后才实施。独立抽取各车速度而破坏跟驰物理约束不是合格的动作干预。

**推荐（Proposal）：** H1 完整区域政策 ITT 为当前主线，机制证据独立分层。H3 若是必要主张，先论证可操纵且安全的动作策略实验对象；若不适合，则明确 IV/g-formula/中介方法的额外假设与不可识别性，允许机制结论保持 Unknown。H1 可独立于 H2/H3 报告，不用“复杂模型”填补缺失数据。

## 8. 测量缺失、界与 assignment-level 接口

在 scope、结果范围、设计分配和目标总体有效时，每 run 的 Y∈[L,U] 按臂分别标准化。对资格两臂：

\[
\tau_Q\in[E(L\mid Z_C=1,Q)-E(U\mid Z_C=0,Q),\ E(U\mid Z_C=1,Q)-E(L\mid Z_C=0,Q)].
\]

有分层/不等概率分配时使用相同目标 H 权重和已知设计权重，不能直接用不同臂的构成差异代替标准化。四格若成立，其保守测量界为：

\[
[L_{11}-U_{10}-U_{01}+L_{00},\ U_{11}-L_{10}-L_{01}+U_{00}],
\]

其中各 L/U 是同总体下的臂均值界。以上是测量/识别界；P6 需另加随机化抽样、簇/配对、删失和多重推断的不确定性，不能把界宽当标准误。

UNKNOWN_SCOPE 不是已定义结果的普通缺失。不能从仅可见车辆重建完整 N，再用 [0,1] 冒充完整区域测量；保留 assignment、原因和 null Y。只有先证明共同 estimand/总体有效，才能在因果分析层对缺失结果用已批准的 [0,1] 最坏界。若连共同结果支持都未知，应报告对象不可估，而非删去整 run。无消息、Disabled、验证失败、未采用、安全覆盖和源失败均按相应 assignment 规则保留，不作成功者分析。

P5/P6 只读消费 P4 assignment_result：assignment/event/unit、population_scope、expected_N、名单/region/window/hash、Y lower/upper、measurement/outcome status、missing/invalid summary、provenance/derivation/source hashes。另需未来设计侧提供 block/cluster、分配概率、ZS/ZC/Z_A 的实际政策映射、H0/H_C 的生成时序、Q 规则/时间/盲法、index-source 与源实现失败记录。后者当前不是 P4 自动生成的生产字段，不修改 P4/P3 schema。

## 9. Task E：总体时间优先性

### 9.1 三类时间及三层物理 endpoint

|对象|语义|当前限制|
|---|---|---|
|T_U|阈值和持续规则下实际动作响应变化 onset|P4 Δv/Δa 已实现；阈值/持续/误差未定，THRESHOLD_UNSET；首次数值差异不是正式 T_U|
|T_R|目标总体区域风险因果效应曲线的 onset|需随机政策样本、完整 Y(t)/界、预定效果/持续规则及联合推断；第一次风险下降不是因果 onset|
|T_P^micro|指定源经预定物理交互机制到区域终端的合格响应 onset|身份、逐跳关系/时间/源归属/覆盖不足则 Unknown；Qualified 不是完整物理因果证明|
|T_P^macro|预定固定区域交通状态算子变化的 onset|是算子/强度到达，不是任意微小物理影响；可覆盖域内全部交通|
|T_P^cohort|固定车辆群持续状态变化的 onset|只对应指定群体/算子；不能排除其他车辆更早响应|

不跨三层机械取 min/max，不用 T_U 替 T_R，不用 command/execution time 代任何 onset。源 onset、Formal 确认、消息可用、目标首次观察、持续性确认分别存储。若源确认前已发生物理到达，也要保留，不能事后剔除或把 clock 重新起算以制造提前。

### 9.2 共同比较支持与 F0

对每个预定 endpoint ℓ，在同一资格总体下建立：

\[
F_{0,\ell}^{Q}(t\mid H)=P\{T_P^\ell(0)\le t\mid Z_S=1,Q(1)=1,H\}.
\]

资格两臂 τ_R^Q(t) 与这个 F0 配对，不使用全部 source-present 的 F0 或 B 类校准分布替代。若最终转为源前四格总体，则重新明确相应 source-present 参考总体及共同 H0 权重，不能直接搬用资格子总体 F0。

|需一致的项目|必要条件 / 审计|
|---|---|
|独立单位|相同 run/簇/块定义；参考 sample 与风险 sample 的依赖明确；共享控制组不能假装统计独立|
|资格总体|同 Q 规则/版本、源与支持域；不按处理后 Qualified / 成功消息筛选|
|源时间原点|物理源 onset 区间及原钟；confirmation 与 ZC 时间独立；source-absent 只用预定机会 clock，无真实源 onset|
|空间/时间支持|固定 region/version、可比较风险网格与物理跟踪 horizon；macro 全交通与风险资格群不同可合法，但关联范围须说明|
|H 标准化|在共同目标 H 分布下分别标准化风险与 F0；跨源时 H 必须为源前；不得使用处理后风险/采用作权重|
|测量与删失|身份、采样、clock、Unknown、源归属、恢复状态和到达确认能力明确；独立 Observer 不窥通信/效果挑 endpoint|

独立物理观察指其观测/资格不由控制器的消息或结果选择驱动；若参考来自无通信随机臂而与风险对比共享数据，联合推断必须处理其统计依赖。单独历史校准数据不因“独立运行”就具备同总体、同机制的可迁移性。

### 9.3 风险 onset 与 early-window 可检验条件

τ_R^Q(t) 是总体潜在结果均值差，T_R 应由预定的效果方向/大小、持续时间、时间网格和同时推断规则操作化。数据不能精确证明连续时间曲线在未观测点的首次非零；合格段的候选起点和确认时间不同，应报告可支持的区间/上界或 Unknown。无检出不等于零效果或没有 onset。

沿用 P1 的固定 H* 路线：在预定早窗内，风险效果同时上带按持续规则低于 −δ，且同 endpoint 的 F0^Q(H*) 上界低于 η，并控制联合错误。δ、持续时间、η、H*、置信水平/预算、时间化 Y 算子均不由本任务确定；已有 η 情景不变成正式数值。若 T_R 的支持区间与所选物理总体判断不能分离，则报告 temporal precedence not established / Unknown。

这个联合结论只允许表述为：在该资格总体和预定物理机制/算子下，物理到达比例受控的窗口存在政策风险效应。F0(H*)<η 不代表每例均无物理到达，不是所有车辆/全部机制最早到达下界。不能把两个总体分布配成单个处理事件的 T_P(0)−T_R(1)；随机化不识别其跨世界联合耦合。

### 9.4 时间误差、删失与 detector-to-physical 桥接

源 onset∈[L_S,U_S]、到达∈[L_A,U_A] 时，相对到达至少保留 [L_A−U_S,U_A−L_S]，并按有依据的 clock 误差外扩；共享误差是否抵消需证据，不能默认独立平方和。风险曲线对齐也受源时间误差，不能只扩物理时间一侧。不能用区间中点强行排序。

精确、左删失、区间删失、可证此前未到达的右删失、Unknown 分开。缺 Witness、观测中断、阳性已恢复或末端未完成持续确认，不能一律记成“未到达/∞”。P2 允许时间集合 S_eℓ 可给保守 CDF：确定不晚于 t 的质量为下界、可能不晚于 t 的质量为上界；Unknown 纳入可能到达质量。直接 Kaplan–Meier 需要合适删失假设，不能用于任意信息性缺失。

尤其要区分 detector confirmation / available time 的分布与真实物理 onset 分布。按统一定义细则 T，只有同域独立延迟/漏检证书成立时，才可用类似：

\[
F_{\rm true}(t)\le F_{\rm det,available}(t+d^\star)+m_{\rm delay}
\]

的保守桥接（含相应不确定性），并观察至 H*+d*。d* / m_delay 不是当前可自行选的参数；没有桥接只能讨论检测器端点，不能宣布真实物理提前。B 类有限校准也不能自动迁移为 Formal A 或现实桥接。当前独立 Qualified=0，真实早窗效应因此仍 Unknown。

多个风险时间点、持续段、物理 endpoints、H* 或 H 分层共同构成检验选择问题。不能事后选下降最早的风险点或到达最晚的物理层。P6 需明确同时带、联合预算/封闭规则、依赖、删失敏感性、SESOI、power/ICC/样本量；本任务只登记依赖，不计算或冻结数值。

## 10. Task F：统一设计架构图

下图是时间展开的设计建议；左侧源前机会四格部分为 Proposal。图示依赖不是已证实的每条因果边，也不替代 P1 正式 DAG。

~~~mermaid
flowchart TD
  H0[源前背景 H0 / 预列机会 / 角色名单 / region-window]
  ZS[源政策分配 ZS：四格共同总体方案待决定]
  S[实际源过程 S* / onset区间 / 实现失败]
  Q[通信盲 Observer：confirmation 与 Qpre]
  ZC[Qpre=1且有源后随机通信 ZC：当前入口]
  MSG[生成与发送 / delivery D* / verification V*]
  ZA[Enabled-Disabled 开关 Z_A：具体随机机制待决定]
  A[Adoption A* / receipt / decision_id]
  CMD[Decision / Command Ucmd*]
  EXE[Execution / 原生约束 / 失败]
  U[实际控制与运动响应 U* / X* / 严格 Δv、Δa]
  NET[域内其他车辆响应 / 下一时点交通状态]
  Y[P4 完整资格名单固定 N / Y及上下界 / assignment输出]
  PHY[普通物理交互 G_P / 三层独立 Observer]
  REF[同资格无消息参考：F0 micro / macro / cohort]
  EFF[H1 assignment ITT / 最终四格另需共同支持]
  MECH[H2-H3 机制路线：额外识别条件]
  TEMP[H4 联合早窗判断 / clock、Unknown、桥接、多重性]
  H0 --> ZS --> S --> Q --> ZC --> MSG --> A --> CMD --> EXE --> U
  H0 --> Y
  H0 --> PHY
  S --> PHY
  PHY -->|仅匹配无消息策略| REF
  S --> Y
  ZA --> A
  U --> NET --> Y
  NET --> PHY
  NET --> FUT[后续消息、决策、事件：属于同一运行的后续时点]
  Y --> EFF --> TEMP
  REF --> TEMP
  A --> MECH
  U --> MECH
  Y --> MECH
~~~

源后 Qpre 对 ZS 是后变量，图中 Q→ZC 明确当前序贯顺序。未来 B 的无源单元没有真实 Qpre；其 C 政策必须在共同机会总体协议中另行定义，不能照图从有源 Q 箭头复制。H1 不须以 H2/H3 显著为入组条件；H4 不由 MECH 节点自动推出。

### 10.1 H1–H4 对照

|假设层（保持 P1 含义）|估计对象 / 证据|关键识别条件|当前状态 / 失败边界|
|---|---|---|---|
|H1 信息干预效果|当前 τQ 的完整区域 Y ITT；全 S=1 ITT、最终 τSC 单列|有效 assignment、Q前置、政策明确、完整结果/界、干扰单位和正支持|设计可表述；无真实随机+完整Y，尚不能估；不能按成功消息筛|
|H2 控制器采用机制|P3 adoption事实；开关→实际响应 reduced form；可选 IV|receipt/decision/执行链；随机开关；IV 另需排除/单调等|实际消费事实 Verified；因果 reduced form / LATE 未识别|
|H3 Action–Risk 机制|动作策略或可识别中介干预对区域 Y|动作干预/有效 IV 或全历史可交换性、支持和网络处理|P4测量已实现；机制效果 Unknown；普通回归不足|
|H4 物理前信息效果|资格风险曲线与同总体各层 F0 的联合早窗判断|H1/时间化测量、独立物理资格、时钟/删失/桥接、联合推断|Formal A/独立 Qualified=0；F0 / T_R–T_P Unknown；检测器到达不替真实到达|

## 11. 现有证据与未来需求

|环节|当前可用|缺失证据 / 后续归属|
|---|---|---|
|实验机会/assignment|四格配置 validator、P7 固定模式 ID|共同源前总体、随机器/概率/盲法/支持/跨簇隔离；P5 决策后再实现|
|Source/Qpre|P2定义、B类有限校准、三层操作化|Formal A、可信 Qpre producer/独立 Qualified；不靠合成源补齐|
|消息与采用|P3 ratification / 真实输入消费回执、decision链|正式随机开关证据、明确机会分母、工具假设；P5机制选择|
|命令/执行/动作|P7真实 TraCI + 连续目标状态；P4严格pair/role/clock|全区域成员状态；正式Action阈值/持续/误差；不重做测量设计|
|区域风险|P4 v1 / 固定N完整窗上下界、172离线测试和数学复算|真实完整区域资格名单/轨迹、正式域窗；P7单车不能替代|
|网络干扰|run固定策略与物理/消息链证据接口|域边界、carryover、exposure支持和混合分配若要拆 direct/spillover|
|物理参考|三层定义与Unknown规则|同资格 F0、独立验证、源归属、延迟漏检桥接；后续P8等须另行授权|
|统计推断|P1总体联合框架、P4测量界|P6 SESOI、持续/同时带、α/η/H*、ICC/功效/样本量；此处不定数值|

现有方法和工程足以支撑一套条件明确的设计，不足以支持当前因果结果。SUMO 证据仅限模型内；NGSIM 的跟驰参考、pNEUMA 运动学和 SPMD 通信观察不提供本项目完整资格、分配与全区域 Y。不能用这些数据源互相填充未观测链路。

## 12. 推荐处置与完成边界

1. 保留 A：Qpre=1、有源、通信盲资格后随机通信的区域政策 ITT 为当前最合理主对象，清楚标明是子总体。
2. 最终四格保留；优先提交 B 的源前机会总体、公共clock/名单/政策对照和源分配条件给研究者决定。C 作为备选，不用未经批准的假设压成点估计。
3. 具体分配优先完整 run + 可审计 matched-block；不把车辆/帧/事件扩成 iid 样本。干扰域、index-source 和对照版本集中待决。
4. Adoption先分开日志率与开关 reduced form；IV/LATE 和 H3 各路线必须满足自己的条件。H1 可独立报告，允许机制保持 Unknown。
5. H4 分别对应三层 F0，保持共同资格/时间/权重，Unknown与桥接缺口显式传播。没有独立 Witness 不宣称提前。
6. P6 只收到明确对象、单位、界和错误控制需求；不在本任务执行其数值规划。研究者审阅后再决定后续任务，本任务到文档与证据验证为止。

全部推荐项见[决策登记](P5_TASK1_RESEARCHER_DECISION_REGISTER.md)。源前机会总体、正式随机化器、IV假设、中介模型及统计数值未被本文批准。

## 13. 针对性方法来源与实际阅读范围

优先复用 P1/P2 和 AAD Zotero 2026-11-02 历史索引。只读尝试本机 AAD 集合 API 失败，故不声称当前 live 库数量/附件状态已核验。没有修改 Zotero、没有新建本地论文库。原文工作产物仅在忽略的 local_research/literature-work/p5_task1_20261104；便携包只存元数据、hash和阅读范围，不收录PDF。

|ID|原始来源|本次实际核对范围 / 使用|
|---|---|---|
|M1|Hudgens & Halloran (2008), Toward Causal Inference With Interference, DOI 10.1198/016214508000000292；[PMC原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC2600548/)|定向核对分组干扰、partial interference、两阶段分配及效应层次；Zotero历史key H8GFNS8U；不声称新实验适用条件已证实|
|M2|Aronow & Samii (2017), Estimating average causal effects under general interference, DOI 10.1214/16-AOAS1005；[作者arXiv版本](https://arxiv.org/abs/1305.6156)|出版社页返回阻拦页；实际使用arXiv v4原文的design/exposure/estimand及概率条件段落；历史key T6SFNY5I；版本不是2017排版页|
|M3|Frangakis & Rubin (2002), Principal Stratification in Causal Inference, DOI 10.1111/j.0006-341X.2002.00021.x；[PMC原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4137767/)|复用P2 Task5全文HTML审计并定向核对principal strata与不可见潜在成员；历史key TVEZQ3UT|
|M4|Imbens & Angrist (1994), Identification and Estimation of Local Average Treatment Effects, DOI 10.2307/2951620；[NBER作者工作稿入口](https://www.nber.org/papers/t0118)|核对摘要及发表版本指向；扫描PDF未获得可检索正文，不声称精读。NBER工作稿元数据年份与1994期刊发表不同，分开记录；完整条件另参M5第16章|
|M5|Hernán & Robins, Causal Inference: What If；[作者官网](https://miguelhernan.org/whatifbook)|官网实际链接19aug26版；定向阅读第16章IV与第19–21章时变处理、sequential exchangeability/positivity和g-formula相关页；不称全书精读|
|M6|Vansteelandt & Daniel (2017), Interventional effects for mediation analysis with multiple mediators, DOI 10.1097/EDE.0000000000000596；[PMC原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC5289540/)|定向核对随机mediator分布、与natural effects区别及识别条件；不把论文直接升级为AAD纵向全网识别证书|

详细检索成功/失败、原文版本与实际页段见[method_sources.json](../../../evidence/research/P5_TASK1_20261104/method_sources.json)。独立反例与界的复算不调用项目生产函数，见[证据入口](../../../evidence/research/P5_TASK1_20261104/README.md)。
