# AAD Core Scientific Definitions

版本：AAD-SCI-DEF-20261102-P2T4-v0.2（研究者确认A–D；操作细节仍分层登记）。统一入口：README.md。

每项列出13个必需字段。Fact指直接可核验事实，Agreed只指研究者明确接受的方向；本次新操作规则和参数没有自动获批。历史P0/P1/P2报告保留；本文件不反向改写它们。证据ID见本目录账本与P2_TASK3_LITERATURE_AND_METHOD_AUDIT.md。

## 当前约束 — P2 Task4 研究者确认 A–D（2026-11-02）

来源：研究者P2 Task4任务书§四。以下四项为Agreed，覆盖本目录Task3遗留的同事项Awaiting状态；历史Task3报告不变。Agreed的是方向和统计原则，不是新增数值、微宏合并算子或已获得实证。

| 决策 | Agreed当前定义 / 适用范围 | 仍未冻结 | 对旧定义的关系 |
|---|---|---|---|
| A 核心主张 | 信息介导的区域风险效应是否早于预先定义、能独立观测验证的物理传播范围内的物理状态到达；限定空间/时间/交通域，不排除全部可能物理影响 | 观测机制清单、覆盖/不可观测项、具体arrival对象 | 接受Task3 E28范围问题；替代“全部普通物理影响均未到达”的强解释 |
| B 双层测量 | Micro采用既有W1–W9框架；Macro测预定区域速度/流量/密度及必要波前；固定cohort持续signed speed decline保留重要指标，不单独承担排除任务 | W1–W9数值质量门、macro算子/阈值、证据层级与融合规则 | 拓展DEF-PHY-007/008；不机械OR/AND，不抹去Task3指标 |
| C 资格总体 | communication-blind Observer先确认源资格并固定Qpre，再随机ZC；主分析为合格source-present子总体ITT及匹配无消息分布，risk/F0支持一致；四格保留 | 实施机制、概率、干扰域、source-absent比较支持、参数 | Qpre子总体不能自动替代全部ZS=1；禁止按送达/采用/处理后Witness筛选 |
| D 总体时间 | 沿用P1§7：预定H*、risk全网格同时带、no-message arrival上界、联合不确定性/SESOI/错误预算；非个体跨世界提前秒数 | 数值预算、SESOI、网格、持续、具体带估计器 | 接受总体框架；不另建竞争统计体系 |

下文旧条目中的Proposal必须按此表分解：已确认原则现为Agreed；具体可执行规则仍Proposal/Unknown。本轮理论与文献更新在此目录增补，不以Task报告另设最新定义。

## DEF-SRC-001 — 源事件 / Source Event

**Definition ID：** DEF-SRC-001

**中文 / English：** 源事件 / Source Event

**数学表达：** \(S^*\ne Z_S\)

**通俗解释：** 源条件分配不是实际合格事件。Formal P2 A与安全受控扰动B分别登记。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 版本化配置、车辆身份、TTC有效性、事件记录、source_type

**计算 / 判定：** A沿用Formal P2；B保存planned/actual/execution_failure/delay。

**相关假设：** A不降阈值，B不升级为A。

**文献 / 定义依据：** P2 Task1；SUMO资料L11/L12仅为实现背景。

**实验 / 实现依据：** H1/H2：SUMO合格A源事件0；NGSIM事件不等于SUMO事件。

**局限性：** 无事件不能编码为物理未到达。

**当前状态：** Fact（当前实现）；Agreed（A/B分离）

**与现有定义关系：** 沿用P1/P2；不改变Formal P2。

## DEF-SRC-002 — 物理源起点 / Physical Source Onset

**Definition ID：** DEF-SRC-002

**中文 / English：** 物理源起点 / Physical Source Onset

**数学表达：** \(t_{S,onset}\in(L_S,U_S]\)

**通俗解释：** 物理条件首次crossing，而非首次观测或确认。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 可靠末次阴性、首次阳性、检测条件、时钟界

**计算 / 判定：** 满足可观测性时形成区间；缺少前阴性记左删失/Unknown。

**相关假设：** 源条件事先确定；采样不能排除未见短暂crossing时仅定义可观测持续段onset。

**文献 / 定义依据：** L8/L14；P2 Task1/2。

**实验 / 实现依据：** V2验证合成注入区间；B命令与(30,30.1]实际首减速观测分开，不是A标签。

**局限性：** 不能从confirmation反推精确onset。

**当前状态：** Proposal / Awaiting Researcher Decision

**与现有定义关系：** 推荐物理链t_E使用onset；信息链仍从confirmation开始。

## DEF-SRC-003 — 源确认 / Source Confirmation

**Definition ID：** DEF-SRC-003

**中文 / English：** 源确认 / Source Confirmation

**数学表达：** \(t_{S,confirm}\ge t_{S,onset}\)

**通俗解释：** 取得Formal P2事件资格的实际观测时刻。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 既有event_confirm_s、连续身份、观测跨度

**计算 / 判定：** 复用当前first_observed_timestamp_meeting_span语义。

**相关假设：** 不改变TTC阈值、持续时间或最大间隔。

**文献 / 定义依据：** P2 Task1；当前formal_risk_measurement.py。

**实验 / 实现依据：** 代码事实：TTC2.0s、持续0.2s、maxgap0.11s，非arrival参数。

**局限性：** 首次阳性不等于确认；语义核验不等于所有执行器完成接线。

**当前状态：** Fact / Verified implementation semantics

**与现有定义关系：** 不得倒写为物理起点。

## DEF-INF-001 — 消息生成资格 / Message Generation Eligibility

**Definition ID：** DEF-INF-001

**中文 / English：** 消息生成资格 / Message Generation Eligibility

**数学表达：** \(T_{G,eligible}\ge t_{S,confirm}\)

**通俗解释：** 确认后最早允许进入生成流程，actual generation另记。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 确认、资格、生成、发送、交付、验证、采用、动作日志

**计算 / 判定：** 分别保留时间对象及失败原因，未生成不伪造时间。

**相关假设：** 资格约束能在执行器中落实；本轮未验证端到端实现。

**文献 / 定义依据：** P1生命周期；P2 Task1。

**实验 / 实现依据：** 当前无完整源→消息→区域风险实验。

**局限性：** 约束不证明已送达、已采用或产生效应。

**当前状态：** Agreed design constraint; implementation incomplete

**与现有定义关系：** 与物理onset可在确认前传播并存。

## DEF-PHY-001 — 物理传播 / Physical Propagation

**Definition ID：** DEF-PHY-001

**中文 / English：** 物理传播 / Physical Propagation

**数学表达：** \(G_P(t)=(V,E_P(t))\)

**通俗解释：** 车辆运动与交互传递状态；边方向是候选影响方向。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 身份、道路坐标、车道、leader/follower、运动学与时钟

**计算 / 判定：** 车辆行驶、道路坐标、交互影响、宏观波前四种方向分别存储。

**相关假设：** 微观leader→follower可与行驶空间方向相反；宏观波前不固定上游。

**文献 / 定义依据：** P1/P2；L1–L4、L8。

**实验 / 实现依据：** H1–H3仅局部响应/候选连接。

**局限性：** 图边不是随机化因果识别；宏观波前不是车辆路径。

**当前状态：** Agreed direction; operational graph Proposal

**与现有定义关系：** G_P与信息图G_I分开。

## DEF-PHY-002 — 潜在物理Witness / Potential Physical Witness

**Definition ID：** DEF-PHY-002

**中文 / English：** 潜在物理Witness / Potential Physical Witness

**数学表达：** \(\pi\in\Pi_{potential}\)

**通俗解释：** 拓扑/邻近允许一条候选路径。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 道路拓扑、车道连接、空间邻近

**计算 / 判定：** 仅登记潜在边，保留类型和形成依据。

**相关假设：** 拓扑可能性不等于实际交互。

**文献 / 定义依据：** P2 Task1/2；L8对图邻近聚类的局限。

**实验 / 实现依据：** Task10候选不构成Qualified。

**局限性：** 不得跳过Observed直接因拓扑升级。

**当前状态：** Proposal

**与现有定义关系：** 三层第一层。

## DEF-PHY-003 — 观测物理交互 / Observed Physical Interaction

**Definition ID：** DEF-PHY-003

**中文 / English：** 观测物理交互 / Observed Physical Interaction

**数学表达：** \(E_{observed}\subseteq E_{potential}\)

**通俗解释：** 记录证明车辆关系和运动学存在，但响应归属未完成审查。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 实际leader/follower和轨迹记录

**计算 / 判定：** 核对身份、车道、关系时间、source/response区间与质量。

**相关假设：** 无身份连续证据的邻近不可当Observed关系。

**文献 / 定义依据：** P2 Task1/2；L8。

**实验 / 实现依据：** Task17–19支持局部已执行关系，未提供目标区路径。

**局限性：** 观察共变不能独立证明影响。

**当前状态：** Proposal

**与现有定义关系：** 与Qualified准入分开。

## DEF-PHY-004 — 合格物理Witness / Qualified Physical Propagation Witness

**Definition ID：** DEF-PHY-004

**中文 / English：** 合格物理Witness / Qualified Physical Propagation Witness

**数学表达：** \(\pi\in\Pi_{qualified}\subseteq\Pi_{observed}\)

**通俗解释：** 逐跳达到预定证据门槛的模型内传播路径。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 每跳源变化、目标响应、身份、关系、时钟、竞争解释

**计算 / 判定：** 按下文W1–W9全部审查；未知项不自动PASS。

**相关假设：** 严格方向和连续性，外部源可排除或界定；无跨车道默许。

**文献 / 定义依据：** L8仅辅助波前；P2 Task1/2。

**实验 / 实现依据：** H3：合格独立witness=0。

**局限性：** Qualified是证据资格，不是自动因果证明。

**当前状态：** Agreed（Task4 B：采用既有W1–W9框架）；逐条可执行质量门与数值仍Proposal / Awaiting Researcher Decision

**与现有定义关系：** 独立于Formal rho/P2风险结果；macro现在是互补独立测量层，不能替代micro路径准入（Task4 B）。

## DEF-PHY-005 — 物理状态基线 / Physical State Baseline

**Definition ID：** DEF-PHY-005

**中文 / English：** 物理状态基线 / Physical State Baseline

**数学表达：** \(B_{\mathcal T}=\{u^B_{i,t}:i\in\mathcal C_{\mathcal T}\}\)

**通俗解释：** 描述无源扰动的处理前目标状态，供速度变化比较。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** onset下界之前的面板、覆盖、趋势、交通背景H

**计算 / 判定：** 首候选：同运行预定窗口均值；趋势检验与held-out空窗验证后再决定去趋势/匹配无源参考。

**相关假设：** 窗口严格在L_S之前并排除源预兆；不能按处理后曲线选窗口。

**文献 / 定义依据：** L10/L12；P2 Task2。

**实验 / 实现依据：** V2比较W2/5/10s，只限合成生成器。

**局限性：** 静态基线在自然趋势下误报；无消息且有源轨迹不是无扰动基线。

**当前状态：** Proposal

**与现有定义关系：** 与F0和论文risk baseline分开。

## DEF-COHORT-001 — 固定车辆集合 / Fixed Cohort

**Definition ID：** DEF-COHORT-001

**中文 / English：** 固定车辆集合 / Fixed Cohort

**数学表达：** \(\mathcal C_{\mathcal T}=\{i_1,\ldots,i_N\},\quad N\text{ fixed}\)

**通俗解释：** 车辆/角色在策略分配前冻结；退出、缺失不删除成员，新车不补位。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 预选ID/role、进入离开、缺失原因、每时点观察掩码

**计算 / 判定：** 分母N固定；退出区域视区域内状态不可用，不以区域外轨迹冒充区域状态。

**相关假设：** 区域/窗口应由处理前设计提供足够保留支持；不能处理后只筛留存者。

**文献 / 定义依据：** P1 D4；L14观察过程假设用于缺失边界。

**实验 / 实现依据：** V2固定20车；B固定6车在预定region内，60run无cohort出区；现实出入未验证。

**局限性：** coverage高仍可能信息性失访；full-cohort量和observed-subset统计不等价。

**当前状态：** Agreed direction; handling Proposal

**与现有定义关系：** 与固定空间region共同约束，必要时缩小预设适用域而非事后筛选。

## DEF-REGION-001 — 目标区域 / Target Region

**Definition ID：** DEF-REGION-001

**中文 / English：** 目标区域 / Target Region

**数学表达：** \(\mathcal T\subset\text{road space}\)

**通俗解释：** 预先固定的道路空间及观察窗口，不跟随处理后车辆移动。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 地图/车道/坐标版本、边界、窗口

**计算 / 判定：** 每车每时点标记in_region；动态占用另作辅助。

**相关假设：** 道路坐标与lane映射可信；不按处理后风险选区域。

**文献 / 定义依据：** P1 D4；P2 Task1/2。

**实验 / 实现依据：** B有region/身份/位置完整记录，但无阈值cohort阳性或完整Qualified链；A仍无合格arrival数据。

**局限性：** 跟踪退出车辆会变成cohort随车指标，不能悄然替代区域指标。

**当前状态：** Agreed direction; numeric boundary Unknown

**与现有定义关系：** 与cohort双重限制；不保证所有场景可实施。

## DEF-PHY-006 — 单车基线相对速度下降 / Baseline-relative Speed Decline

**Definition ID：** DEF-PHY-006

**中文 / English：** 单车基线相对速度下降 / Baseline-relative Speed Decline

**数学表达：** \(\Delta u^B_{i,t}=u^B_{i,t}-u^{obs}_{i,t}\)

**通俗解释：** 正值为减速，保留方向；不是pair closing speed。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 每车速度与独立确定的baseline

**计算 / 判定：** 在有效身份、位置和速度下相减；基线误差随结果传播。

**相关假设：** 速度单位m/s；baseline和观测的车辆/坐标定义一致。

**文献 / 定义依据：** L8/L10；本轮测量Proposal。

**实验 / 实现依据：** V2已知shift面板。

**局限性：** 均值下降可与加速抵消；不检测所有物理状态。

**当前状态：** Proposal

**与现有定义关系：** 优先复用论文u速度；Task2 g_v与早期Task3 Δv仅保留历史映射。

## DEF-PHY-007 — 区域速度下降状态 / Regional Speed Decline State

**Definition ID：** DEF-PHY-007

**中文 / English：** 区域速度下降状态 / Regional Speed Decline State

**数学表达：** \(\bar{\Delta u}^{B}_{\mathcal T}(t)=N^{-1}\sum_{i\in\mathcal C_{\mathcal T}}\Delta u^B_{i,t}\)

**通俗解释：** 主目标是固定cohort的等车辆平均下降；median/比例回答不同问题。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 固定成员全体变化或已申明缺失界

**计算 / 判定：** 完整面板直接算；缺失时不得用变化的observed子集分母冒充上述全体量。

**相关假设：** 缺失机制或物理界需可辩护；不自动MCAR。

**文献 / 定义依据：** L10；P1 D4；本轮V2。

**实验 / 实现依据：** V2均值/median/比例42候选配对比较。

**局限性：** 均值对异常敏感、median可忽略少数真实响应；比例还需单车阈值。

**当前状态：** Agreed signed-decline direction; equal-weight operator Proposal

**与现有定义关系：** 下文给observed estimator与部分识别界；不用g以免net gap冲突。

## DEF-PHY-008 — 固定cohort速度状态到达 / Fixed-cohort Speed-state Arrival

**Definition ID：** DEF-PHY-008

**中文 / English：** 固定cohort速度状态到达 / Fixed-cohort Speed-state Arrival（历史通用标题Physical Arrival保留映射）

**数学表达：** \(\phi(t)=\mathbf1[\bar{\Delta u}^{B}_{\mathcal T}(t)\ge\theta_P]\)

**通俗解释：** 固定区域/cohort达到预定强度的持续速度下降，并有独立源路径资格证据。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 状态量、theta/h/q/coverage、路径、恢复规则、时钟

**计算 / 判定：** 区分state onset和source-attributed qualification；持续完成才确认，不把确认当onset。

**相关假设：** 数值规则先固定，路径资格不得按最早报警择优。

**文献 / 定义依据：** P2 Task2；L8/L10仅方法。

**实验 / 实现依据：** V2测量测试；B60run全部无cohort阈值报警，无独立目标arrival真值。

**局限性：** 无路径时只能叫速度状态报警；phi不可用Formal rho/P2循环定义。

**当前状态：** Agreed physical direction; executable/numeric definition Proposal

**与现有定义关系：** v0.1原条目所测固定cohort对象与公式保留；Task4 B明确其不能单独排除区域普通物理传播。不是新增统一micro/macro OR或AND endpoint；广义物理到达须声明观测域与endpoint版本。

## DEF-REF-001 — 无消息参考 / No-Message Reference

**Definition ID：** DEF-REF-001

**中文 / English：** 无消息参考 / No-Message Reference

**数学表达：** \((Z_S,Z_C)=(1,0)\)

**通俗解释：** 源存在条件下分配通信关闭，普通物理传播仍可发生。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 两项assignment、实际资格、全部通信失败、背景H

**计算 / 判定：** source-present两臂ITT；delivery/verification/adoption失败保留Z_C=1。

**相关假设：** 随机化、正概率、版本一致、干扰域明确，资格/选择规则成立。

**文献 / 定义依据：** P1 §7；P0/P2 Task2。

**实验 / 实现依据：** 当前无满足契约的参考运行。

**局限性：** No source和发送失败均不是No-message arm。

**当前状态：** Agreed estimand direction

**与现有定义关系：** 四格不变；模型配对仅辅助。

## DEF-REF-002 — 无消息物理到达分布 / No-Message Arrival Distribution

**Definition ID：** DEF-REF-002

**中文 / English：** 无消息物理到达分布 / No-Message Arrival Distribution

**数学表达：** \(F_0(t\mid H,Z_S=1)=P\{\widetilde T_P\le t\mid Z_C=0,Z_S=1,H\}\)

**通俗解释：** 可观测适用总体中的无消息arrival分布，而非处理事件反事实轨迹。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** assignment、源资格、arrival区间/删失/Unknown、独立单位

**计算 / 判定：** 按下文统计分支估计；资格在随机化前的子总体需明确标为F0^Q。

**相关假设：** population与风险curve一致；源资格不受通信选择污染；可识别观察机制。

**文献 / 定义依据：** P1 §7；L14。

**实验 / 实现依据：** F0数值Unknown。

**局限性：** 不能把S*=0当TP=∞；确认后筛选不自动识别全部ZS=1总体。

**当前状态：** Agreed对象及Task4 C的资格后通信随机化方向；具体估计器/实施规则Proposal，数值Unknown

**与现有定义关系：** 与Physical State Baseline、个体跨世界差分开。

## DEF-TIME-001 — 物理到达时间 / Physical Arrival Time

**Definition ID：** DEF-TIME-001

**中文 / English：** 物理到达时间 / Physical Arrival Time

**数学表达：** \(T_P=\inf\{t\ge t_E:\phi(t)=1\text{ and persistence holds}\}\)

**通俗解释：** 事件级潜在/观测arrival是随机时间；总体由F0描述。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** source onset、state onset、确认、观察、路径时序

**计算 / 判定：** 保存arrival_onset_interval、confirmation、observation分别；持续资格赋予该段onset。

**相关假设：** 第一段须在可观测范围；真实连续持续不可由插值保证。

**文献 / 定义依据：** P1/P2；L14。

**实验 / 实现依据：** 当前A事件TP Unknown。

**局限性：** 不能把事件TP直接当总体共同物理下界。

**当前状态：** Proposal operationalization

**与现有定义关系：** 总体比较用P1预定horizon/F0上界，下文定义可选分位数下界。

## DEF-TIME-002 — 区域风险效应起点 / Regional Risk-effect Onset

**Definition ID：** DEF-TIME-002

**中文 / English：** 区域风险效应起点 / Regional Risk-effect Onset

**数学表达：** \(\widehat T_R=\inf\{t\in\mathcal H:U_{sim}(\widehat\tau_R(t))<-\delta\text{ persistently}\}\)

**通俗解释：** 策略使总体区域风险下降的统计起点，不是首个车辆动作。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 预定时间网格、独立随机单位、regional rho/P2结果、SESOI、同时带

**计算 / 判定：** 沿用P1 §7.1.1；估计失败/无满足段返回Unknown。

**相关假设：** 随机化/干扰/缺失识别成立，阈值和时域预先规定。

**文献 / 定义依据：** P1 estimand；本轮不新建风险估计体系。

**实验 / 实现依据：** 没有消息链区域因果数据。

**局限性：** 没有检出不等于效应为零；不能用TU或首次下降代替。

**当前状态：** Agreed population direction; inferential details Proposal

**与现有定义关系：** Formal rho风险端不变；统计起点与真效应起点区分。

## DEF-TIME-003 — 总体时间优先性 / Population-level Temporal Precedence

**Definition ID：** DEF-TIME-003

**中文 / English：** 总体时间优先性 / Population-level Temporal Precedence

**数学表达：** \(T_R^{upper}<T_P^{lower}\)

**通俗解释：** 在无消息总体通常尚未物理到达的预定窗口有风险策略效应。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 同时风险带、F0同时/固定点上界、钟差、统一时间/总体

**计算 / 判定：** 首选P1 H*早窗判据；联合覆盖与区间误差按下文处理。

**相关假设：** 两总体同目标域、相同基线H与权重；不能由边际识别联合跨世界。

**文献 / 定义依据：** P1 §7.2–7.3。

**实验 / 实现依据：** 当前不可检验；无F0和风险曲线。

**局限性：** 不支持每个处理事件提前秒数；重叠/未知返回not established。

**当前状态：** Agreed direction; bound construction Proposal

**与现有定义关系：** 不修改P1；任何η/alpha/H*仍待决定。

## DEF-CENS-001 — 时间删失 / Event-time Censoring

**Definition ID：** DEF-CENS-001

**中文 / English：** 时间删失 / Event-time Censoring

**数学表达：** \(T_P\in(L_A,U_A],\quad T_P>C\text{ if right-censored}\)

**通俗解释：** 区间只定位事件；完整观察未见合格事件才右删失。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** 全段状态/质量、窗口末端、持续确认需求

**计算 / 判定：** 完整观测、区间、右删失、左边界各自编码；末端待确认段不能当未到达。

**相关假设：** 评估时点、删失机制及可观测性满足所选估计器条件。

**文献 / 定义依据：** L14全文；L5历史摘要不冒充精读。

**实验 / 实现依据：** V2缺口只是测量压力，非交通删失验证。

**局限性：** 瞬时可恢复速度不同于疾病不可逆指标；首次合格持续段需全日志。

**当前状态：** Agreed distinction; statistical handling Proposal

**与现有定义关系：** 右删失并非永久不发生；身份/质量不足不机械删失。

## DEF-CENS-002 — 不可判定 / Unknown

**Definition ID：** DEF-CENS-002

**中文 / English：** 不可判定 / Unknown

**数学表达：** \(\text{arrival_status}=\text{Unknown}\)

**通俗解释：** 不能由身份、路径、clock或测量证据确定到达或未到达。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** missing_reason、失败/竞争源、上下界、quality记录

**计算 / 判定：** 保留全部分母；不补零、不删行、不当普通独立右删失。

**相关假设：** 敏感性界可给所有未知最早/最晚到达情景。

**文献 / 定义依据：** P1 §8；L14不涵盖信息性缺失修复。

**实验 / 实现依据：** 当前A与独立witness不足属于Unknown。

**局限性：** Unknown不证明无到达；完全未知可令CDF界无信息。

**当前状态：** Agreed missingness direction

**与现有定义关系：** 与No source、false、censored不同。

## DEF-CLOCK-001 — 时钟不确定性 / Clock Uncertainty

**Definition ID：** DEF-CLOCK-001

**中文 / English：** 时钟不确定性 / Clock Uncertainty

**数学表达：** \(t_{true}\in[t_{log}-\hat b(t)-e(t),t_{log}-\hat b(t)+e(t)]\)

**通俗解释：** 校正offset并保留drift、同步与测量残差。

**适用范围：** 当前SUMO模型内研究；现实交通可迁移性未验证

**必要输入：** clock_id、timebase、step相位、offset估计、drift界、同步证据

**计算 / 判定：** e(t)=e0+dmax|t-t0|+ephase（各分量有证据才数值化）；端点按区间算术外扩。

**相关假设：** 同一SUMO clock只在step/调用相位核验后可免外部同步；日志写入时间不代替状态时间。

**文献 / 定义依据：** L15 RFC5905 §8/§11.1（章节阅读）；P2。

**实验 / 实现依据：** Task18有step phase证据，非所有Observer/风险接口已核验。

**局限性：** NTP标称精度不是AAD误差；抽样区间和clock误差不重复计算。

**当前状态：** Proposal; numerical tolerance Unknown

**与现有定义关系：** 源/arrival相减用[L_A-U_S,U_A-L_S]；无钟差界不可时间排序。

## 操作细则A：Witness W1–W9及有向边契约

W1真实同车道纵向leader→follower关系；W2实体ID连续且角色交换可追溯；W3关系覆盖变化与响应窗口；W4源状态变化有独立区间；W5目标响应采用预定速度/加速度判据；W6校正clock后源区间上界严格早于响应下界；W7轨迹、速度、net gap及相对速度有效，缺口不超过预定质量容限；W8审查信号灯、拥堵、前方其他制动、换道/汇入、边界控制、通信动作等竞争解释；W9逐跳连接使用同一实体/响应段，时间严格可连接到固定目标区。

边必存from/to_vehicle_id、interaction_type、lane_id、leader/follower、road_position与coordinate_direction、influence_direction、interaction_time_interval、source_state_change_interval、target_response_interval、speed/acceleration/net_gap/relative_speed、identity_continuity、quality_status、clock_uncertainty、alternative_explanation_status、derivation_version。

ID切换无法可靠映射则断链；leader切换将边分段，不跨切换拼接；换道/汇入单列复杂路径；多路径分别编号并报告全部，不能事后挑最早一条；多个独立源无法归属则source-specific arrival Unknown，可另报any-source状态。区间重叠仅支持“顺序未确定”，不能中点排序。宏观波前的斜率与connected component不能替代上述每跳。严格W6可能损失真实近同步传播，属于明确保守限制，不伪造reaction delay范围。

## 操作细则B：固定区域、全cohort量与缺失

令M_i(t)=1仅当该预选车辆仍在固定区域且运动学、身份有效。固定N的coverage为c(t)=ΣM_i(t)/N。

\[
\widehat{\bar{\Delta u}}_{obs}(t)=\frac{\sum_iM_i(t)\Delta u^B_{i,t}}{\sum_iM_i(t)}
\]

此observed-subset估计量只有在完整观察，或另有可辩护的缺失识别假设时才代表固定N的主量。coverage≥c_P不自动消除处理后选择。区域外速度有记录也不能当作区域内可观测；退出不删除成员、不补位。若双重固定定义在某交通情景无法稳定观测，应在处理前缩小窗口/改变预选域，或明确结果Unknown；不能按实际处理后留存筛样。

车辆退出区域是结构性不可用：该车当时的“区域内速度”本身无定义，不是普通传感器失访。全cohort区域主量只在成员均有在域支持的预定窗口内适用；不能用速度物理界虚构车辆仍留区。若实际退出使对象失去定义，标为不适用/Unknown；任何composite结局或always-in-region principal-stratum替代均需另行研究者决定。下面的缺失界仅适用于仍在区域、目标量确实存在而传感器漏测的车辆。

若每个缺失单车的下降有预先给定物理界[a_i,b_i]，全cohort主量可界定为
\[
[N^{-1}(\sum_{obs}\Delta u_i+\sum_{mis}a_i),\;N^{-1}(\sum_{obs}\Delta u_i+\sum_{mis}b_i)].
\]
仅当整个区间都≥θ_P才可确定跨阈；整个区间低于θ_P才可确定未跨；否则Unknown。界本身必须由允许速度范围与baseline误差支持，本轮未冻结；不可用伪零贡献。中位数/分位数/比例同样受缺失影响，不因稳健二字而免除识别要求。

推荐等车均值作为“总体平均下降强度”首候选，因为单位、线性权重和对象清楚；不是经验上普遍优于median。单车异常能驱动均值，median会忽略少数真实响应；比例可检测受影响覆盖面，但新增单车阈值与比例阈值。V2显示候选对半数响应得出不同结果，因此不能按更早报警挑选。绝对速度偏差混合加速/减速，保留辅助而非主判据；gap、density为辅助，Formal rho/P2留作风险端。

## 操作细则C：onset、持续、确认、恢复与末端

对每个可判定持续段，先保存最后可靠阴性和首个可靠阳性的onset区间。持续规则为实际观测跨度≥h_P，相邻有效样本间隔≤q_P，显式阴性会重置；允许小缺口连接须标gap-bridged，不能宣称真实连续观察。若不作跨缺口状态假设，真正连续h_P仍不可识别。arrival_confirmation是确认该段的时刻，observation_time是状态被采样的时间，日志写入/资格审核时间另存。

主分析只用第一段。recovery首候选为低于同阈值、按独立退出持续要求确认；当前不默认hysteresis，若需θ_exit<θ_enter必须联合校准。恢复不倒改首次arrival。若到截止C时尚存在未完成h_P的阳性段，可能已有尚待确认的onset，不能把其onset右删失到C；延长观察仅为完成既定确认，或保留更早的区间/Unknown。只在“所有≤C的合格onset均能排除”时可记onset>C。

源onset使用区间，arrival-source相对时间为[L_A-U_S,U_A-L_S]，必要时与t≥t_E约束相交；区间不合法则回查质量。不得将不确定源时间、sampling分辨率、日志延迟全部合成一个精确中点。

## 操作细则D：No-message资格与可识别总体

优先设计是在任何通信动作前由communication-blind Observer确认源，再随机分配Z_C。源确认之前物理扰动已可能传播，仍必须记录onset并保留该早期物理段；不能以随机化时刻重置物理到达。若分配前目标已经受物理影响，该事件不支持预物理早窗，不能事后删掉以获得有利结果。

确认前资格Q_pre=1是通信分配前变量，因此可对该已定义子总体做两臂ITT。但若Z_S=1里仍有未合格源运行，子总体分布
\[
F_0^Q(t\mid H)=P\{\widetilde T_P\le t\mid Z_C=0,Z_S=1,Q_{pre}=1,H\}
\]
不自动等于P1全部ZS=1的F0。须明确资格定义、纳入总体和风险curve同步目标域；原F0符号仅在源合格性由设计保证/原适用总体已如此定义时复用。不能悄然增加S*=1条件。若资格在通信之后，直接筛S*=1可能是处理后选择；需要可证的资格不受通信影响、principal-stratum假设/界限或assignment层重新定义，均待研究者决定。

四格含source present/absent×communication enabled/disabled，矩阵不变。delivery/verification/adoption失败是Z_C=1的实际执行结果，不迁入Z_C=0。无源、执行失败、无合格path、未知arrival各自留存。独立随机化运行是主参考；同初态/配置/seed仅辅助：审计RNG实例、车辆/设备随机流、分支调用顺序和保存状态，不能由相同seed识别逐事件反事实。

## 操作细则E：统计估计、联合覆盖与总体时间

完整独立事件的经验CDF适用精确时间；完整区间数据报告CDF识别带或在非信息性inspection假设下用Turnbull型NPMLE。其区间内质量分配一般不唯一，不能把阶梯线伪装精确时间。普通KM只适用于精确事件+独立/条件独立右删失，不能把interval上界、Unknown或恢复性状态中的未见短段一律输入KM。L14的原文方法假设事件状态可被可靠评估；速度可恢复，若整段状态缺失则不能仅凭后面阴性排除曾有持续段。

无额外缺失假设时，可用每事件允许时间集合构造样本CDF界：已确定U_i≤t者贡献下界1；已确定L_i>t者贡献上界0；其余（含Unknown）上界1。独立事件/簇层抽样不确定性另加，不把识别界等同CI。竞争源若只是归属不明，source-specific量Unknown；若预定为互斥first-event cause则用cumulative incidence/竞争风险，不能假装独立删失。

沿用P1 §7的首选：预定H*上F0的有效上置信界<η，同时风险曲线的全网格上带<-δ并满足持续规则。风险侧可在独立随机化单位/簇层构造bootstrap max-t同时带；小样本/离散条件需要相应随机化推断，未在本轮实现。arrival侧：固定单个H*且完整观测可用二项单侧上界；扫描多个时间必须构造全网格同时界或预分配多重检验错误率，不能择点后用pointwise CI。区间数据可对保守CDF上识别界再加全网格抽样界；需要独立单位，不按车辆行数算n。Turnbull型NPMLE不默认套普通bootstrap正态近似，需专门校验覆盖。

总错误预算α分配α_R+α_P+α_clock≤α；Bonferroni联合覆盖不要求两端独立。确定性clock界无需另分概率，若clock界是统计CI需分配α_clock。两侧使用同一预选总体、时间原点、H分布和权重；H分层后须预定标准化权重。不同源总体不能直接比较。

若保留简写T_R^upper<T_P^lower，必须注明TP侧为总体界，例如由单调同时上带U0(t)反演的η分位数下界sup{t:U0(t)<η}（限定已观测时间域、端点规则另定），并非每事件最早可能arrival。TR侧由覆盖真τ_R的同时带和持续规则保守定位效应起点上界；采样网格只支持网格层结论，连续时间需额外平滑/误差界。本轮不新设η/δ/alpha，也不声称此分位数简写已经研究者批准。首选仍用P1预定H*表述。

clock外扩、onset区间或抽样界有重叠则temporal precedence not established / Unknown。边际风险效应与arrivalCDF不能构造同一处理事件TP(0)-TR(1)、个体提前秒数或跨世界联合概率。

## 操作细则F：状态到达与普通物理竞争机制的主张范围

Fact（B域）：60run/42候选全部无固定cohort报警；validation__a5.0__d6.0__seed202711020中，s1–s4分别在31.2/32.2/34.3/36.6s、固定region内确认单车响应候选，cohort s5–s10没有达到候选阈值。源位于区外，候选只有4条顺序边，未构成source→cohort Qualified Witness。来源：本地B输出scope_audit及便携controlled_B_summary/response_locations.csv，参数与身份详见Task3结果；这是描述性示例，非事后推断样本选择。

Inference：DEF-PHY-008识别的是“指定cohort达到指定强度与持续的速度状态”，不是“几何区域任何普通物理影响首次进入”。phi=0、缺Qualified链或低于阈值均不足以排除更早的非cohort、微小速度、gap/density或其他物理机制。不能由T_R早于此T_P自动推出所有普通物理影响被排除。

Agreed（Task4 A–B，2026-11-02）：风险结局与arrival须预先对齐总体、空间和时间支持；核心主张限定在预定义且可独立观测验证的物理传播范围，采用micro/macro双层测量，cohort速度状态不能单独承担物理排除任务。不再主张已排除所有可能物理影响。具体机制清单、macro算子、质量门与证据层级仍Proposal；详见DEF-SCOPE-001及DEF-PHY-009/010。此为研究者接受方向，不证明时间优先性，不改论文或Gate。v0.1此方向的Awaiting已被E32/E33覆盖，历史Task3记录保留。

## 操作细则G：可计算基线与时钟界（Proposal）

每车静态参考的显式首候选为
\[
u^B_{i,t}=\frac{1}{n_{i,B}}\sum_{k:\,t_k\in[t_{B,end}-W,t_{B,end}),\,valid_{ik}=1}u_{i,t_k},
\qquad t_{B,end}\le L_S,
\]
其中参考窗口完全早于源onset下界、无源预兆，且n_i,B、实际时间跨度、最大缺口、identity/in-region支持逐车报告。不得把没有足够基线的成员填均值/补零。等间隔完整数据可用算术均值；不等间隔若要时间平均，应预定时间权重，不能将采样密集段自动超权。本轮V2/B只测试等间隔方案。线性趋势备选u^B_i,t=â_i+b̂_i t只能由处理前窗口拟合，并在独立无源窗口验证；未在本轮实现或声称去趋势有效。W2/5/10s为探索，不是合理交通范围。

若本地timestamp满足t_local=t_ref+b(t)，使用同步估计b̂(t)校正为t_ref_hat=t_local-b̂(t)。有实证支持的offset/drift/step-phase界可形成e(t)≤e_offset+d_max|t-t_sync|+e_phase；各项未测量不能默认零。采样crossing区间另存，不能重复把同一采样间隔计两次。校正区间通过对允许b(t)取上下确界传播；简单保守实现可将端点各外扩e。共享时钟误差可能部分抵消，但须证明共同分量，不能擅自按独立误差相减或平方和缩小界。无有效界则时间比较Unknown。此为误差契约，不是已验证的时钟数值。


## DEF-SCOPE-001 — 物理传播观测范围 / Physical Propagation Observation Scope

**Definition ID：** DEF-SCOPE-001

**中文 / English：** 物理传播观测范围 / Physical Propagation Observation Scope

**数学表达：** \(\mathcal O_P=(\mathcal T,\mathcal W,\mathcal M,H,\mathcal Q,\nu)\)

**通俗解释：** 声明在哪里、何时、哪些机制、何种交通背景和质量下能作物理到达判断；范围外保持不可排除。

**适用范围：** 当前模型内；外推现实需额外验证。

**必要输入：** 固定区域/窗口、机制列表、可观测字段、测量版本ν、质量与clock记录。

**计算 / 判定：** 分析前登记观测清单；逐机制标measured / partially measured / unobserved，不以最终阴性倒推覆盖。

**相关假设：** 盲于通信assignment；不按结果改变区域、机制或检测阈值。

**文献 / 定义依据：** Task4 A；Jerath 2024 §3–6的目标/模型依赖边界；Task2宏微区分。

**实验 / 实现依据：** Task3 B region内s1–s4响应而s5–s10cohort未报警（E27），不是新实验。

**局限性：** 有限范围阴性不能推出不存在任何物理影响；噪声下“未检出”还受检测能力限制。

**当前状态：** Agreed范围限定；本记号、具体清单和质量规则Proposal。

**与现有定义关系：** 约束所有TP/F0与结论；不追溯改变Formal P2、rho或Task3原始记录。


## DEF-PHY-009 — 宏观时空交通状态 / Macroscopic Space-time Traffic State

**Definition ID：** DEF-PHY-009

**中文 / English：** 宏观时空交通状态 / Macroscopic Space-time Traffic State

**数学表达：** \(q_A=\sum_i d_i(A)/|A|,\ k_A=\sum_i t_i(A)/|A|,\ u_A=\sum_i d_i(A)/\sum_i t_i(A)\)

**通俗解释：** 在预定lane-space-time域内累计所有有效轨迹的距离和驻留时间。流量、密度、速度须用同一支持域；不等于固定cohort均值。

**适用范围：** 第一候选为同向单车道局部时空域；多lane分别计算或明确lane-normalized合并。

**必要输入：** 道路纵向坐标、lane、真实timestamp、区域内轨迹片段、覆盖及质量；|A|单位m·s（多lane为lane长度时间之和）。

**计算 / 判定：** 入口/出口按域边界裁切；部分穿越车辆保留域内距离/时间，不要求完整穿越。q为veh/s、k为veh/m、u为m/s；多lane合并为每lane归一尺度，不能当总横断面流量。k=0时u未定义，不能填零。

**相关假设：** 轨迹完整普查或有独立可辩护的抽样权重；坐标/片段边界一致。q=ku在同域构造且k>0时是代数恒等，不证明均匀交通假设。

**文献 / 定义依据：** Hall官方FHWA Traffic Flow Theory Chapter2 §2.1–2.2：点/空间/时空测量、部分穿越与平均速度区别；Edie型广义定义原始1963文献本轮未取得，不称原文已读。

**实验 / 实现依据：** Task3 B支持必须覆盖非cohort车辆的必要性；本轮未计算或校准q/k/u。

**局限性：** 稀疏轨迹、区域外传播、identity缺失可能使估计不可靠；不能无权重外推全交通，也不自动归属某个source。

**当前状态：** Agreed宏观测量层；上述具体Edie型算子、空间分区/时间窗/变化阈值Proposal。

**与现有定义关系：** 不替换DEF-PHY-007/008。完整瞬时空间普查的速度算术均值亦可作snapshot macro指标，但不与本时空u_A混称；临时任意观测子集均值须标采样支持。


## DEF-PHY-010 — 双层物理证据记录 / Two-level Physical Evidence Record

**Definition ID：** DEF-PHY-010

**中文 / English：** 双层物理证据记录 / Two-level Physical Evidence Record

**数学表达：** \(\mathcal E_P=(E_{micro},E_{macro},E_{cohort};\mathcal O_P)\)

**通俗解释：** 分别保留路径证据、宏观状态变化和cohort状态，每项有独立质量、时间区间、源归属与Unknown。

**适用范围：** 预定观测范围内的模型研究，尚无合格源总体实证。

**必要输入：** W1–W9逐跳日志；预定义macro测量；固定cohort面板；共同clock/区域与版本。

**计算 / 判定：** 先报告证据向量和冲突表，再讨论可支持主张；不默认OR/AND。任一层缺测不能由另一层强制填PASS或未到达。

**相关假设：** 测量层独立于通信处理轨迹的事后筛选；source attribution与状态变化检测分开。

**文献 / 定义依据：** Jerath micro→macro映射、Saberi宏观比例、Duan jam tree、Zhang预印本事件图；这些不能相互当同一对象。

**实验 / 实现依据：** Task3 B的区域中间车辆响应与cohort阴性反例；Qualified独立路径仍0。

**局限性：** micro+不保证macro强度达到；macro+不保证source-specific微观链；两阴性只表示在既定能力下未检出。

**当前状态：** Agreed双层方向；向量式分层记录及冲突处理为Proposal，未形成新单一Physical Arrival二值定义。

**与现有定义关系：** 补充而非覆写W1–W9与cohortφ。若未来选一个主要到达endpoint，须版本化，并使F0的endpoint/总体/支持域完全对应。


## DEF-POP-001 — 通信前资格子总体 / Pre-communication Qualified Population

**Definition ID：** DEF-POP-001

**中文 / English：** 通信前资格子总体 / Pre-communication Qualified Population

**数学表达：** \(\tau_Q(t)=E[Y_{\mathcal T}(1,1;t)-Y_{\mathcal T}(1,0;t)\mid Q(1)=1]\), \(F_0^Q(t\mid H)=P\{\widetilde T_P\le t\mid Z_S=1,Z_C=0,Q_{pre}=1,H\}\)

**通俗解释：** 先盲法确认源和资格，再随机通信；估计这些事件的策略效应及同总体无消息物理到达分布。

**适用范围：** 合格source-present事件。Q(1)表示源条件存在时、通信分配前的潜在资格；不是source-absent的实际可观测资格。

**必要输入：** 资格规则/时刻/Observer盲法、Z_S/Z_C及概率、H、固定区域/窗口、所有失败/缺失。

**计算 / 判定：** 在Qpre=1且ZS=1内随机ZC；按assignment估ITT，不因delivery/verification/adoption/处理后Witness失败剔除。风险/F0使用相同H分布和权重。

**相关假设：** 无预先通信泄漏或anticipation，正概率、well-defined policy、独立run/干扰簇与可识别缺失。

**文献 / 定义依据：** Task4 C、P1 Estimand §2/3/7；P0 Task2已读Hudgens–Halloran 2008与Aronow–Samii 2017的干扰边界。

**实验 / 实现依据：** 当前没有Formal A合格事件或可估F0；仅设计兼容性推导。

**局限性：** Qpre对ZC是pre-treatment，但对ZS可能是处理后变量；不能自动在source-absent臂筛同一Q或外推全部source-present。

**当前状态：** Agreed资格顺序、子总体与匹配要求；Q(1)/τQ记号、具体实现/估计器Proposal；结果Unknown。

**与现有定义关系：** 细化DEF-REF-002，不替代P1四格交互或全部ZS=1 F0；下文细则I给分解。


## 操作细则H：微观 / 宏观不一致的解释（Task4 Proposal）

| micro路径 | macro状态 | 允许解释与后续核查 | 禁止解释 |
|---|---|---|---|
| Qualified | 有合格变化 | 两层相容；核查源、空间/时间支持和其他源 | 两阳性自动证明source因果链 |
| Qualified | 未检出 | 局部/弱响应、聚合稀释或尺度不合；报告macro检测能力 | micro必然错误，或macro阴性证明无物理影响 |
| 缺Qualified | 有合格变化 | 未观测路径、身份缺口、区域外机制、其他源/需求变化；source归属Unknown | 用macro填补微观身份与竞争解释 |
| 未检出 | 未检出 | 仅在已观测机制和检测能力下阴性 | 已排除所有普通物理传播 |
| 任一Unknown | 任意 | 保留Unknown原因、覆盖和时间集合；不删除运行 | Unknown=未到达 |

macro窗口内变化、波前斜率、车辆交互路径、cohort持续状态是四种对象。波前方向由状态和坐标决定，不恒向上游。macro可提供独立物理状态证据；micro提供实际交互联系证据。主张所需联合充分条件仍须按具体机制确定，本轮不发明一个最早OR或最晚AND到达时间。若物理状态在通信前已到达，记录实际到达，不按事后资格剔除以追求提前。

## 操作细则I：四格与Qpre两臂的兼容性（Task4 Inference / Proposal）

P1四格保持 \(\tau_{SC}=\mu_{11}-\mu_{10}-\mu_{01}+\mu_{00}=\tau_{\mathrm{ITT}}^{S=1}-\tau_{\mathrm{ITT}}^{S=0}\)。在同一源条件总体、共同结果定义和H权重下，令 \(p=P\{Q(1)=1\}\)，则由全期望
\[
\tau_{\mathrm{ITT}}^{S=1}=p\tau_Q+(1-p)\tau_{\neg Q},\qquad
\tau_{SC}=p\tau_Q+(1-p)\tau_{\neg Q}-\tau_{\mathrm{ITT}}^{S=0}.
\]
跨四格共同H须定义在源分配之前；通信前、已受源影响的状态可作通信效应的背景，但不能作为跨源普通baseline直接调整。这说明τQ和四格交互可以共存但不是同一量。若非资格事件没有ZC随机化支持，τ非Q不可识别；此代数恒等不赋予数据识别，不能补零。source-absent没有实际源，Qpre=1没有天然共同支持。若要四格限制在Q(1)=1的principal stratum，需要跨源潜在资格识别假设；随机化ZS本身不显示source-absent单元的Q(1)。另一选择是源分配前、四格均可定义的共同资格，但那是不同资格对象，需要研究者决定。保留最终四格设计不等于已经实现所有条件四格estimand。

源确认可先于ZC，但确认前的物理传播必须保留；不可用t_confirm或随机化时刻重新设物理onset。模拟在源确认后fork通信两臂可共享处理前段，仅为辅助模型配对；不能把该已受源影响状态fork成无源臂并称四格共同无源初态。source-absent的策略及公共clock需按预定协议定义；配对模型可借(1,0)的观测clock作公共比较索引，但不是source-absent真实onset，也不能自动解释为独立现实事件的个体反事实时间。

随机化独立单位是完整运行/道路时间簇，不是车辆或帧；若跨簇message或物理链泄漏，须可辩护partial interference或预先定义assignment→exposure mapping及正支持。事后实际adoption或Witness是机制观测，不能作为主要ITT入组条件。

Task4 D沿用P1 H*检验：在本资格总体中，风险全网格同时上带按预定持续规则低于−δ，且同endpoint的UCB[F0^Q(H*)]<η，联合错误受控。若同时选择多个macro/micro endpoint或H*，必须预先规定检验族与预算，不能事后选最晚physical arrival。α分配/具体带仍Proposal；clock界与删失按细则E/G传播。η允许的是总体到达比例，不能把统计结论改写成“每例绝无物理影响”。当前无F0/风险曲线，不能作经验时间分离结论。
