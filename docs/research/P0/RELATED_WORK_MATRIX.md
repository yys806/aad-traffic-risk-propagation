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
