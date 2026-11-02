# P2 Task3 Literature and Method Audit

日期：2026-11-02。状态：COMPLETED_WITH_LIMITATIONS。采用已读取的D:/shen/test/PAPER-SKILL研究检索、方法精读、实验审计及paper-claim-audit流程；Zotero-clean用于限制文献改动范围。没有新建仓库PDF目录。

## 1. 检索顺序和真实访问记录

先用P0/P1/P2既有审计，再检查Zotero TJU→AAD。早期connector health出现transport error；后续本地API恢复并核验83个既有top-level条目，故“Zotero不可用”不再作为最终阻塞。查询同义词覆盖car following/leader follower、shockwave/kinematic wave、trajectory validation/completeness、CUSUM/sustained change、interval censoring/assessment process、clock offset/drift、SUMO randomness/calibration。只用出版社、原论文、JSS、NIST、IETF和SUMO官方材料作核心依据。

实际工作文本及访问记录保存在local_research/literature-work/p2_task3/（本机工作产物，非正式论文镜像）。原文来自Zotero API返回的确切附件路径，或官方公开端点；未扫描Zotero storage，未修改原文附件。读取状态逐篇列明；摘要/章节阅读不冒充全文。

## 2. 本轮核心精读与方法审计

### L8 — Zhang, Wang, Sun & Shoman，交通波图与change-point

正式条目：Tianya Zhang, Xiunan Wang, Pengyuan Sun, Maged Shoman, Physics-informed graph modeling for traffic shockwave analysis through optimized change-point detection，Zotero Q65YUJ89，DOI 10.1016/j.trb.2026.103522。

**版本和获取：** 本轮实际全文为已有附件CLA3GKSX，36页PDF（正文内部页码至34），SSRN 5903681，标注not peer reviewed，2025-12-10提交版本；不能称为已精读2026期刊最终版。PDF SHA256=047b49c784c49214721aae6021029a3bb3011f9287c23b025adf26fdb41ac253。已分段读取方法、实验、讨论、结论与参考文献全文。最终出版版本未取得，版本差异仍Unknown。

**问题和数学对象：** 从车辆位置/速度轨迹提取减速change points，以图聚类形成时空shockwave front。CUSUM提供候选，受限动态规划/PELT+优化piecewise-linear分段。图节点是减速事件，边用时间、空间、波速、加速度和alignment约束；不是实测leader→follower身份边。方法正文使用undirected graph，而引言/讨论有causal描述，不能将后者当识别保证。

**参数/数据：** 文中例示10Hz、最小segment20点、R²>0.7、反向波速约-10至-30ft/s、恢复速度16ft/s、reaction窗口示例等。其检测匹配还用duration默认10、空间覆盖70%、0.7时间+0.3空间IoU且阈值0.3。这些均属作者设置，不是AAD推荐或物理定律。DP penalty25–200、CUSUM threshold3–15、drift0.5–2敏感性，不能转为AAD θP/hP。

**实验/结果：** NGSIM US101/I80六段15分钟，专家STMap标注100个波事件；表1报告proposed F1=0.849、平均speed error1.421ft/s。该数据与结果是作者报告，本轮未复算。验证的是宏观波前检测匹配，不是独立微观因果路径，也不是AAD消息效应。connected components可能合并多个来源；方向限制偏重反向拥堵波，不覆盖所有扰动。

**AAD复用/不可照搬：** 可复用逐车状态变化、图/时空质量审查、标注匹配与敏感性设计。不可用图连通替代W1–W9；不可复制经验参数、只向上游假设或causal措辞。预印本的分段/平稳假设可能错过缓慢或复杂状态；正文“无需阈值”措辞与实际调参并不消除参数依赖。未据文本抽取中可疑公式排版认定数学勘误。

### L10 — NIST/SEMATECH，CUSUM Control Charts

出处：NIST/SEMATECH e-Handbook §6.3.2.3，https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc323.htm 。官方网页全文已读；无DOI。Zotero Z3MT7GYE。访问2026-11-02，原响应SHA256=2b307ae8b747a4ab0ec8056290dfca94fe50db8e678b25989256e966b7411dce。

问题是稳定过程均值小偏移的监测。S_hi(i)=max(0,S_hi(i-1)+x_i-μ0-k)，反向S_lo对均值下降累积，超过控制限h报警。需要in-control均值/方差、目标shift、序列监测错误率或ARL设计；过程自相关和baseline估计误差不能忽略。

网页教学例均值325、过程SD1.27、每组4点，δ=1σ、α=0.0027、β=0.01，推出h=4.1959、k=0.3175（原单位）。其α是一个sequential trial口径，不是AAD整段运行FPR；也不等于AAD的持续时间hP。网页说明小shift监测优势，没有提供交通区域阈值。

可复用“先定义null、shift和误报损失，再设计检测器”的原则。第一版保持可审计的简单持续状态；CUSUM/EWMA仅备选，PELT更适合离线分段而不自动适合实时eligibility。没有用3σ经验制造AAD k=3推荐；standardized方案本轮未实测。

### L11 — Eclipse SUMO，Randomness

出处：https://sumo.dlr.de/docs/Simulation/Randomness.html ，官方网页全文已读，页面标注2026-10-08更新；无DOI。Zotero 6RVH4ZCL。响应SHA256=42d6325a9916f9c0ddb82951fc0b00b7e381f8bed4c82541c0cf4e3f0c6c6103。

SUMO采用seed初始化的Mersenne Twister，多实例分别处理载入、流、驾驶动态、设备，同seed初始化；同版本、同参数、同输入通常可重复，官方还列出平台/库和部分模型的差异。Krauss sigma、速度分布、车辆插入/重路由都会用随机性。

可复用版本、输入和seed记录、逐RNG/随机设备审计。由该机制推断：通信引起分支/车辆决策改变后，随机调用顺序与实体对应不自动一致；同seed重复性不是跨策略逐事件反事实配对。此推断不是官方文档直接证明AAD配对无效，也不是必须重跑Task18的理由。官方默认值不改变当前冻结配置。

### L12 — Eclipse SUMO，San Pablo Dam Calibration

出处：https://sumo.dlr.de/docs/Tutorials/Calibration/San_Pablo_Dam.html ，官方网页全文已读，页面标注2024-09-10更新；无DOI。Zotero WYIL4MT4。响应SHA256=3b2dc79e7168cea7c1ab5520e04ddc5544eb94e02caca4c9b5a6bd7b7b9def49。

教程用1997年San Pablo Dam通过时刻资料，模拟travel time并最小化跨车/检测点RMSE；使用出流速度边界、相同车辆类型及COBYLA迭代，教程称约80次迭代十分钟。其minGap2.5m仅特定模型设置；文中validate.py是优化循环的目标评价，不等于独立held-out验证。

可复用域/边界条件、误差目标、参数与运行记录，另由AAD明确校准/验证隔离。不可将travel-time拟合或教程默认参数当arrival测量校准，不为复制教程修改Formal vType/网络。教程提示跨场景需重校准，支持不从B域直接迁移A。

### L14 — Fay & Shaw (2010)，区间删失全文

完整出处：Michael P. Fay & Pamela A. Shaw. Exact and Asymptotic Weighted Logrank Tests for Interval Censored Data: The interval R Package. Journal of Statistical Software 36(2),1–34. DOI 10.18637/jss.v036.i02。官方全文：https://www.jstatsoft.org/article/view/v036i02 ，34页正文、应用、实现和参考文献已分段精读。Zotero QUH3LUP3，导入式原文附件TIWGTN2S；SHA256=fea636822c3d8969233c6ef76938e4ae35cc4db62c1aac6ad7128d1115da57d6。

**定义/假设：** Xi∈(Li,Ri]，Ri=∞为右删失；§2.1非信息性inspection要求评估时刻不依赖事件。文中不处理informative interval censoring。速度会恢复，不能直接复制其不可逆疾病的可靠阴/阳观察过程，AAD必须保留全段日志及持续确认。

**方法：** Turnbull/innermost intervals上的质量NPMLE，区间内survival位置常不唯一；EM收敛需Kuhn–Tucker/gradient检查，不只看迭代停止。WLRT的grouped-continuous likelihood是S(L)-S(R)，比较score、permutation、multiple imputation。交换性要求包括观察机制；不同臂不等inspection不能机械置换。不是AAD时间优先性专用估计器。

**参数/实验：** 文中乳腺cosmesis两组46/48人示例，比较不同软件与30模拟数据NPMLE；本文不提供交通θ/h/q。示例p值及算法精度只说明方法实现差异，不能作AAD效应依据。文中引用midpoint imputation在不等censoring模拟中名义0.05可达0.19，说明中点处理可能失真，非通用定量误差界。

**复用/限制：** 保留时间区间、nonidentification区域、观察机制和估计器分支。不能照搬医学假设、普通KM或固定点CI作为全网格带。本轮没有运行R或拟合F0，因为缺适用事件。统计构造仍Proposal，不把精读写成AAD已验证覆盖率。

### L15 — Mills, Martin, Burbank & Kasch (2010)，RFC5905

Network Time Protocol Version 4: Protocol and Algorithms Specification, IETF RFC5905, DOI 10.17487/RFC5905。官方全文文件已取得，**本轮精读§8 on-wire protocol及§11.1 system clock variables，仅章节阅读，未声称全文精读全部附录**。Zotero 3BK7C596；响应SHA256=8b7abd903c60202e2953ee012fefa6916666c3b0c71825c748cdd262024fb268。

四timestamp给offset θ=0.5[(T2-T1)+(T3-T4)]、round-trip delay δ=(T4-T1)-(T3-T2)；precision、jitter、root delay/dispersion各不相同，时钟表示精度不等于实际测量精度。网络不对称/残差影响同步；本轮不测任何外部时钟。可复用offset/drift/残差分开记录并传播区间的原则，不能从NTP标称精度替AAD填写钟差。SUMO逻辑时间与日志wall clock亦须区分。

## 3. 既有来源复用及未精读限制

| ID | 资料 / DOI | 实际状态 | 本轮用途 / 边界 |
|---|---|---|---|
| L1 | Lighthill & Whitham1955，10.1098/rspa.1955.0089 | 沿用Task2书目/理论审计；未新增全文精读 | 宏观状态场与车辆路径不同，不归因新读 |
| L2 | Richards1956，10.1287/opre.4.1.42 | 沿用Task2；未新增全文精读 | 波速方向依状态，不给AAD阈值 |
| L3 | Austroads2015 Guide Part2 Traffic Theory | 前段已核查相关官方章节，非全文精读 | micro/macro分层背景 |
| L4 | Yang, Yang & Du2024，10.1080/15472450.2023.2270415 | 摘要/方法二手线索；出版全文未获取 | 非核心数值依据，不把成熟波算法当witness |
| L5 | Lindsey & Ryan1998，10.1002/(SICI)1097-0258(19980130)17:2<219::AID-SIM735>3.0.CO;2-O | 未取得全文；用L14开放全文补足方法 | 不冒充精读 |
| L6/L7 | Sharma等2019，10.1016/j.trb.2018.12.016；2018，10.1016/j.trc.2018.09.027 | Zotero metadata/公开摘要；未全文精读 | 只作completeness背景，不借其经验参数 |
| L9 | Page1954，10.1093/biomet/41.1-2.100 | 未取得全文；L10官方方法替代 | 不复制原文结论细节 |
| L13 | SUMO simulator官方文档 | 基本能力资料 | 不作现实有效性证明 |
| B1 | Brockfeld等Calibration and validation，Zotero GMF4LZDC，正确DOI10.3141/1876-07 | metadata与既有审计 | 纠正先前错误DOI；未当本轮全文依据 |
| B2 | Partial trajectory method…，10.1016/j.trc.2023.104416，SZL54NKN/FDMRDKC3 | 已取得26页PDF并提取全文，本轮未精读 | 不冒充已完成trajectory质量精读 |
| B3 | Deep spatial-temporal embedding…，10.1111/mice.13160，SQYZHHPM/CZ6DMMXB | 已取得已有HTML全文，本轮未精读 | 保留后续候选，不支撑数值质量界 |

近三年真实相关论文已查到，但核心交通波最终期刊版与轨迹质量原文精读仍有不足；这限制“文献与实验验收全部完成”的表述。固定cohort/region冲突与缺失界为本轮数学推断，不伪称某篇交通论文已经验证AAD方案。没有为了凑数量扩大到无关论文。

## 4. 历史实验复用矩阵（H1–H6）

| ID / 成果 | 已核验事实与来源 | 可以复用 | 不能复用 / 缺失 |
|---|---|---|---|
| H1 Task17–19 | Task19科学分析、Task18执行完整性；100运行、50实际A/B配对、2候选、5tau、5seed；0.05s内部/0.1s测量 | 运行单位、seed波动、step phase、局部响应/轨迹完整性边界 | 无source-region多车波、消息链、目标区risk或独立arrival；不重跑 |
| H2 B00/Round2 | Task20闭幕报告：SUMO Formal P2 source=0 | 当前A可识别性限制、冻结配置 | 无A源事件经验真值；不降阈值制造样本 |
| H3 Task10/20 | 40同轨迹source→target候选，40连接Unknown，qualified独立witness=0 | 路径准入负证据、不能自动归属 | 不是40物理未到达，也不是可用F0 |
| H4 NGSIM | Task20汇总source167/159、target174/252为相应既有运行口径 | 已有风险测量/运动学背景 | 不合并不同口径分母；非随机source-present no-message或SUMO事件 |
| H5 MiTra T1/pNEUMA | Task12–19/Task20：MiTra局部同车道输入与实际replay；pNEUMA限城市运动学 | 采样、局部动态范围、完整性线索 | 无独立多跳arrival标签；pNEUMA不恢复leader/TTC角色 |
| H6 Stage0.6 | Task20/既有数值复核、fixture边界 | 数值误差和现有未决max/sum聚合冲突 | fixture不是动态系统arrival真值或F0 |

主要输出可定位code/outputs/analysis/task19_20261101/analysis_dataset_run_level.csv及analysis_trajectory_features.csv；报告docs/TASK19_SCIENTIFIC_RESULT_ANALYSIS_20261101.md、docs/TASK20_STAGE0_CLOSURE_AND_STAGEI_READINESS_20261101.md。本轮复用已有审计，不读取locked holdout、不复跑Task9/19、不把A/B minGap工程臂当通信臂。

## 5. Zotero写入和未完成项

新增5条：L14 QUH3LUP3→AAD/因果统计；L10 Z3MT7GYE→同主题；L15 3BK7C596→微观校准；L11 6RVH4ZCL→仿真；L12 WYIL4MT4→校准标准。已有条目、原附件和集合成员均保留。新增JSS通过DOI精确查Crossref，清理返回题名HTML并核对作者/年月/期刊；安装的standardize_abbrev3与complete_journal_metrics管线仅通过过滤输入处理此新期刊，未重写83条已有记录。缩写J. Stat. Soft.与easyScholar指标有来源；未返回的CCF/EI/SSCI/AJG明示Unknown，不凭空补值或称已全部补齐。

原文PDF导入Zotero本地API，不使用云附件配额。JSS单篇双语翻译已完成（管线记录488s、成功1/失败0），回挂导入式附件4TMXFKYB，标题“双语对照 PDF（机器翻译）”；英文原附件TIWGTN2S保留。网页/标准无期刊指标，明确不适用。初次导入附件工具因默认DRIFT配置报KeyError，已限定AAD后恢复；五条已建条目未重复创建。

## 6. 调研停止与仍缺的证据

已有核心方法足以指出持续时间、趋势、coverage、删失和时钟不能忽略，足以推荐测量流程；不足以证明AAD交通参数。停止扩检的原因是关键缺口在独立区域标签/源资格/真实交通null与验证域，不是多找一个阈值就可填补。尚缺：A事件、微观多跳独立witness、固定region×cohort可观测支持、充分交通null、B目标阳性与A/B迁移依据、外部/跨接口clock残差。其结果是部分参数Unknown，非假设成立或失败。

本轮补充B测量域已实际完成60 CALIBRATION_ONLY运行（结果另报告），故“缺独立B运行”不再是限制；仍缺目标cohort阳性标签、完整Qualified链及迁移依据。无需继续扩检来制造阈值。
