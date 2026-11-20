# 最近邻与方法对比矩阵

矩阵只比较论文实际做到的内容。`—` 表示论文没有定义或没有证据，不表示不存在。

| 文献 | Scientific question | Information source / lifecycle | Controller adoption / action | Physical propagation / arrival | Risk / regional effect | Causal identification / interference | Real-world evidence | AAD threat |
|---|---|---|---|---|---|---|---|---|
| Schönhof 2006 | 动态车辆网络中消息如何传播 | 车间广播、多跳；分析消息传播速度与渗透率 | —；无控制器采用链 | 信息波与车辆运动耦合，未建立风险到达时间 | 无安全风险指标；网络消息宏观量 | 无因果识别 | 微观仿真 | 直接否定“首次提出信息—物理耦合” |
| Wang 2019 | 多类别 V2V 信息流如何受控传播 | 队列/中继/通信服务率；两层 PDE/积分方程 | 信息队列控制，不是车辆动作采用 | IFPW 速度/密度，未与风险到达对接 | 无风险指标 | 无干预因果估计 | 数值实验 | 直接否定“首次建模信息传播波” |
| Saberi 2020 | 城市拥堵是否呈网络传播 | 路段速度状态；SIR 类 β、μ | 无消息、无控制器链 | 网络拥堵扩散/恢复 | 链路拥堵比例；多城市区域量 | 非因果观察/拟合 | 六城市 Google 速度 + Melbourne 仿真 | 物理网络“传播”已有 NC 级证据 |
| Duan 2023 | 瓶颈增长/恢复的时空规律 | 1-min GPS 路段速度与 jam tree | 无信息干预 | 瓶颈空间/时间增长、恢复和早期信号 | 网络级拥堵规模 | 无信息因果 | 北京、深圳月度数据 | 物理到达/区域传播基准已有强先行 |
| Huang & Du 2022 | 非局部 CAV 信息何时稳定交通流 | 速度由空间邻域密度分布决定 | 非局部控制律，采用被假设 | 稳定性/波耗散，不是事件到达 | 无风险指标 | 理论分析，无因果实验 | 数值示例 | “非局部信息改变流”不能单独主张创新 |
| Jerath 2024 | CV 在何处能影响瓶颈总延误 | V2X 信息位置；事件触发 | 假定 CV 收到信息并执行预定义减速 | 解析 ZOI、event/null horizons | 总车辆延误区域量 | 场景内解析反事实，无随机识别 | LWR 理论/情景计算 | 直接威胁“信息作用边界”新颖性 |
| Peng 2026 | BLOS 警告对驾驶反应的因果异质性 | V2X BLOS warning；处理/响应 | 研究驾驶员是否响应及状态异质性 | 未分离物理传播基准 | 响应质量/及时性 | causal ML/CATE，非网络干扰 | 驾驶数据（出版摘要已核验） | 直接威胁“远端警告改变动作”新颖性 |
| Lyu 2025 | 因果图能否提升实时冲突风险预测 | 轨迹变量与风险标签 | 无消息生命周期/采用 | 冲突时空图预测 | TSC 风险、区域图 | SAM 因果发现 + GAT；非随机干预 | 无人机轨迹 | “因果风险图”已有相邻方法 |
| Hudgens & Halloran 2008 | 干扰下如何定义直接/间接效应 | 组内处理暴露 | 处理由随机设计定义 | — | 个体/组级潜在结果 | 部分干扰、直接/间接/总效应 | 疫苗试验示例 | AAD 必须明确 exposure mapping 与 estimand |
| Aronow & Samii 2017 | 已知网络干扰下如何估计平均效应 | assignment→exposure mapping | 设计式随机化 | — | 直接/间接/总体效应 | IPW、随机化方差、局部依赖 | 社会网络实验 | 网络级因果主张不能只用普通 A/B |
| Lu 2021 / Arun 2021 | 代理安全指标是否预测真实风险 | TTC/PET/DRAC 等 | — | 指标沿轨迹定义 | 代理指标的外推与语境依赖 | 评价/综述，无 AAD 干预 | naturalistic/文献综合 | TTC 变化不能自动等于事故风险变化 |
| Coifman & Li 2024 | 车辆跨相机轨迹是否可信 | 视频轨迹、相机对齐、比例校正 | — | 空间/时间映射误差 | — | 无因果 | NGSIM 视频重校准 | 现实证据的测量链必须独立审计 |

## 结论

最近邻不是一篇论文，而是四条已经相当成熟的支线：信息传播波、非局部控制、物理拥堵传播、BLOS/驾驶响应。AAD 若要成立，必须把它们连接为可审计的事件级因果链，并证明该链在独立物理到达基准和网络干扰下仍成立。仅把四条支线并列、换用“类超距”命名或增加 TTC 聚合均不构成实质突破。
## P0 Task 2 更新

六篇指定最近邻已完成全文或合法全文限制审计。Schönhof 的全文明确给出 Poisson 装备车辆网络、同向/反向消息跳转和到达时间分布；Wang 的全文给出队列—LWR 信息波和 NS-3 校准；Jerath 的全文给出 LWR 瓶颈 ZOI、event horizon 和 null horizon；Peng 的全文在 40 名驾驶者、239 条有效试次上给出随机 BLOS warning 的 ORS/RT ATE 和状态异质性；Hudgens–Halloran 与 Aronow–Samii 的全文分别给出 partial interference 与一般 exposure mapping 的设计式框架。

因此矩阵中的“—”不是文献访问不足，而是这些工作确实没有同时提供 AAD 所需的 message lifecycle、controller adoption、独立 no-message physical witness 和区域风险因果结果。Task2 的最小 estimand、数据缺口和证据契约见 P0_TASK2_ESTIMAND_AND_INTERFERENCE_SPEC.md、P0_TASK2_DATA_SOURCE_CAPABILITY_AUDIT.md 和 P0_TASK2_EVIDENCE_CONTRACT.md。

## P2 Task4 supplement — 2026-11-02

Current cross-paper 10-dimension comparison: [Task4 literature and novelty audit](../P2/P2_TASK4_LITERATURE_AND_NOVELTY_AUDIT.md). Jerath information→CV action→macro delay/ZOI is established prior work; Saberi physical contagion and Duan early jam prediction are distinct from information-policy risk identification but remain novelty threats. Zhang official journal metadata has six authors; available four-author SSRN only supports a preprint-method comparison. No claim that journal methods/results were fully read. Hall official chapter supports explicit space-time measurement; Edie original not acquired. Existing rows and P0 judgments above are retained as history. PAPER_REGISTER.csv remains the reading/version registry; Zotero remains the only library.

## Task5补充审计（2026-11-02；不覆盖历史）

正式Zhang18页现已FULL_TEXT_READ_PUBLISHED（Q65YUJ89/9F39AWXN），预印本CLA3GKSX保留；版本差异见[Task5正式版审计](../P2/P2_TASK5_ZHANG_PUBLISHED_VERSION_AUDIT.md)。旧100 events与正式120 STMaps单位不同；正式F1 .875、speed error2.20ft/s不与旧值混用。正式无向事件图/BFS、物理约束和波前重建不是独立随机因果识别，也不能直接成为W1–W9。变化点/事件图/波前本身不能继续当AAD新颖性。

新增Frangakis–Rubin2002与Hoeffding1963分别支持资格分层识别边界和有条件保守同时界；不是新增交通效应。联合生命周期/采用动作/区域风险ITT/同资格无消息物理基准仍为待验证贡献候选，不是全球首次或NC创新已证。A0、独立Qualified0、F0/TR-TP Unknown保持。微观、宏观、cohort时间族、共同opportunity和具体统计规则均Proposal，见[统一定义v0.3](../definitions/README.md)。本轮0新实验，旧Task3/4结论及当时访问限制保留历史。

## 交通经济学支线补充 — 2026-11-20（不覆盖历史，只追加）

> 补入原因：矩阵此前对「延误测度 / 行程时间价值 / 信息价值 / 路径改道 / 个体与系统均衡」零覆盖
> （关键词自查：行程时间 0、信息价值 0、绕行 0、改道 0、ATIS 0、VMS 0、Wardrop 0、均衡 0、延误 1），
> 而 AAD 主结局 `Y` 正是活在这条线上。
> 文献来源：Zotero `TJU → AAD → 10_信息价值与路径改道`（22 条，2026-11-20 入库）。
> 行文口径经 GPT 第六十轮审阅（`cache/aad-p2/gpt60.md`）。

| 文献 | Scientific question | Information source / lifecycle | Controller adoption / action | Physical propagation / arrival | Risk / regional effect | Causal identification / interference | Real-world evidence | AAD threat |
|---|---|---|---|---|---|---|---|---|
| **延误测度与时间价值**：Mohan Rao 2012；Quiroga & Bullock 1999；Carrion & Levinson 2012；Mackie 2001；Hess 2005；Shires 2009 | 如何测量拥堵与控制延误，如何估计出行时间及其可靠性的价值？ | — | — | — | 控制延误、行程时间及其可靠性；时间节省价值及其异质性。测度与货币估值是两件事 | 测度、估值与元分析；不识别消息对区域结局的因果效应 | Quiroga & Bullock：交叉口延误实测；Hess：选择数据估计；Shires：跨国估值元分析 | **结局口径先例**：延误测度、时间估值不是创新；不构成对物理到达前消息效应的直接重合 |
| **ATIS、信息价值与路由均衡**：Acemoglu 2018；Wu et al. 2021；Yang 1998；Levinson 2003；Hall 1996 | 信息结构如何改变路径选择、均衡及出行成本？ | ATIS、异质信号或用户已知的路线集合；不等同于逐条可追溯的远端风险消息 | 出行者依据信息选路；理论上的信息可用性或策略响应不等同于控制器实际采用日志 | 容量约束、时变成本或拥堵反馈不等同于无消息条件下的物理到达基准 | 个体或群体出行成本、均衡表现；Acemoglu 表明扩展部分用户的路线信息可使该群体的均衡成本上升 | 博弈与均衡分析刻画共享拥堵及策略互动；不等同于对区域溢出效应的经验识别 | 理论与模型分析为主；各篇实证输入待核 | **理论实质重合**：信息可改变均衡及出行成本，收益未必为正；尚未显示其识别了物理到达前的区域效应 |
| **路径选择与途中响应建模**：Prato 2009；Ben-Akiva 1991；Polydoropoulou 1996 | 如何建模路径选择及驾驶员对途中信息的响应？ | 驾驶员信息系统、途中信息及 RP/SP 中的信息条件 | 路径选择、继续原路线或改道；行为模型或调查响应不等于控制器采用链 | Ben-Akiva 涉及动态网络；未见以无消息物理到达时点划分效应窗口 | 主要解释个体路径选择与响应异质性；动态网络模型可连接流量与成本 | 行为模型及 RP/SP 估计；不等同于在网络干扰下识别区域总效应 | Prato：综述；Polydoropoulou：RP/SP 数据，陈述偏好不等同于实地改道 | **行为机制先例**：不能把「收到信息后改道」当作创新；区别在采用可核验、到达前时窗及区域结局 |
| **田野信息实验与 VMS 绕行**：Zhang & Levinson 2008；Peeta 2000；Kim 2014 | 在途信息有没有价值，VMS 内容如何影响实际或报告的绕行决策？ | 田野实验提供的出行信息、VMS 发布内容；发布或展示不等于逐车采用 | 驾驶员选路或绕行；应区分实测动作、调查响应和推断采用 | 事件信息可先于驾驶员抵达事件点；这不等于早于物理影响抵达目标区域 | 信息价值、绕行倾向或绕行率；不能由个体绕行直接推出区域总风险变化 | Zhang & Levinson 提供田野实验先例；分配机制、实际采用和网络溢出的处理待核 | Zhang & Levinson：田野实验；Peeta、Kim：VMS 行为研究，调查与实测口径逐篇核对 | **近邻实证先例，优先核查**：现场信息与行为响应已有；关键是是否同时识别到达前区域效应，而非是否用了 VMS |
| **个体选路与系统最优**：Wolpert 2002；Roughgarden 2006、2003；Jahn 2005 | 个体决策何时偏离系统最优，如何在用户约束下改善网络表现？ | Wolpert 涉及路由代理的反馈；其余主要研究成本、约束或路由分配 | 自私选路、代理路由决策或带用户约束的系统分配 | — | 网络总成本、无政府代价、系统最优与用户可接受性 | 共享链路成本刻画车辆间相互影响；不是经验上的干扰效应识别 | 理论分析与计算实验；现场部署证据待核 | **系统效应先例**：个体受益不保证区域受益；不直接覆盖远端消息的到达前效应 |
| **突发拥堵下的多智能体改道**：Wang 2016 | 多智能体的下一路段改道能否缓解突发拥堵？ | 突发拥堵与网络状态输入；消息来源追溯及逐车采用记录待核 | 算法输出下一路段改道决策；仿真执行不等于现场控制器采用 | 涉及拥堵演化；是否单独构建无消息物理到达基准待核 | 拥堵缓解与网络运行表现；与 AAD 的区域定义及 `Y` 口径需对照 | 策略间性能比较可体现车辆相互作用；不自动等于现实网络中的因果识别 | 仿真评估；真实数据输入与现场部署应分开核验 | **近邻系统先例，优先核查**：事件触发改道改善网络表现已有；直接重合与否取决于是否评估到达前的区域总效应 |

### 定位句（GPT 第六十轮定，可直接用于正文与答辩）

> 「信息改变行为」以及「改道反馈可能改变网络表现」都不是 AAD 的新意；
> AAD 要检验的是，在以无该消息时常规物理影响抵达目标区域的时点为界的**到达前窗口**内，
> 来源可追溯的远端风险消息能否经**可核验的控制器采用与车辆动作**，在**车辆相互影响下**
> 改变该区域的**总体风险**。

### `AAD threat` 列的写法原则（三条，后续补行一律照此）

1. **先写它拿走了哪条主张，再写它是否覆盖 AAD 的核心问题。**
   推荐句式：「已表明 **X**；未见估计 **Y**；需核查 **Z**。」
   例：VMS 研究拿走的是「现场信息能触发绕行」，不是自动拿走「到达前区域总效应」。
2. **按科学问题与所估计的效应分级，不按术语或实现分级。**
   同样用延误指标 → **结局口径先例**；已展示信息—动作或动作—网络反馈 → **部分重合**；
   已可信地估计同类到达前窗口内的区域总效应 → **直接威胁**（即使不用 AAD 术语）。
   反过来，均衡互动不等于干扰下的因果识别，现场实验也不自动等于识别了区域溢出。
3. **用同一把尺子约束 AAD 自己。**
   写「未见」或「待核」，不要把摘要没写当成论文没做，也不要把 AAD 的设计目标写成已识别的结果。
   采用日志能证明消息被采用，但仅比较采用者与未采用者不能识别采用的因果效应。
   若主结局 `Y` 是延误口径，就写「超额行程时间」，不要让它被读成碰撞风险。
