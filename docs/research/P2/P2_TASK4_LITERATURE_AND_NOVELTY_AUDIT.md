# P2 Task4 — Literature, Theory and Novelty Audit

日期：2026-11-02。状态：COMPLETED_WITH_LIMITATIONS。研究结论等级与定义以[统一入口](../definitions/README.md)为准；本报告不批准新参数、不改变研究目标。使用PAPER-SKILL的research-lit检索/分版本/逐篇分析与综合方法，并按zotero-clean边界维护已授权条目；没有运行paper-claim-audit的独立跨模型reviewer，不声称获得该技能的正式PASS verdict。

## 1. 实际资料范围、全文与停止依据

先恢复AI_CONTEXT Current、项目注册表/状态/索引及P1理论、DAG、Estimand、H1–H4，复用P0三任务以及P2 Task1–3原报告和证据。P0已全文审计的LWR、信息波、Hudgens–Halloran/Aronow–Samii不重复做一遍概述；本轮补四篇的直接重叠、版本与主张边界。没有查私人OB、locked holdout或新增实验。

| 文献 / 来源 | 正式出处 / DOI | 本轮实际读取 | 可复用 / 不能照搬 | 逐篇记录 |
|---|---|---|---|---|
| Jerath, Gayah & Brennan 2024 | PLOS ONE19(6)e0301188；10.1371/journal.pone.0301188 | 期刊30页正文、方法、图表；外置S1/S2未重新全文读 | 信息→控制→宏观延误及ZOI；不能把delay边界当AAD全部物理可达边界 | [Jerath](paper_notes/JERATH_2024_ZONES_OF_INFLUENCE.md) |
| Saberi等2020 | Nature Communications11,1616；10.1038/s41467-020-15353-2 | 期刊9页正文/Methods/图表；外置Supplementary未重新全文读 | link拥堵比例SIR/网络传播；非消息风险因果 | [Saberi](paper_notes/SABERI_2020_TRAFFIC_CONTAGION.md) |
| Duan等2023 | Nature Communications14,8002；10.1038/s41467-023-43591-7 | 期刊11页正文/Methods/图表；外置Supplementary未重新全文读 | jam tree早期增长预测；不可当物理未到或干预效应 | [Duan](paper_notes/DUAN_2023_EARLY_SIGNAL.md) |
| Zhang等2026正式版 | TRB211,103522；10.1016/j.trb.2026.103522 | DOI/Elsevier元数据及可用摘要；正式全文未取得，PARTIAL_READ | 六作者与四作者SSRN不同；正式算法/实验/结论变化Unknown | [版本审计](paper_notes/ZHANG_2026_VERSION_AND_WITNESS_AUDIT.md) |
| Zhang等SSRN5903681 | 2025-12-10，4作者，not peer reviewed | 复用Task3完整精读，Task4重核题页/摘要/引言与方法记录 | change-point/物理图只能当预印本方法证据；不归属正式版结果 | 同上 |
| Hall，Traffic Stream Characteristics | FHWA Traffic Flow Theory Chapter2，官方chap2.pdf；出版年未核实 | Introduction/测量部分§2.1–2.2，后半模型综述未精读，PARTIAL_READ | 空间/时空支持、部分穿越与平均速度区别；Edie1963原文未得 | [测量说明](paper_notes/HALL_TRAFFIC_STREAM_MEASUREMENT.md) |

优先Zotero现有附件，再以同义词shockwave/kinematic wave/braking cascade/vehicle trajectory/zone of influence/space mean speed/generalized traffic measurement检索公开primary sources。Crossref按DOI核元数据，不按题名反查简称。Zhang ScienceDirect 403、浏览器captcha、TDM仅coredata、OpenAlex指向同一SSRN的链条已核查；未绕过访问限制。正式版全文缺口明确保留，不继续将同一预印本搜到多次当新证据。

调研停止理由：四工作足以限定信息控制、物理网络、早期预测、事件图已有哪些先例；FHWA测量章补宏观量必要缺口。当前主要科学缺口在AAD的源资格/独立物理证据/随机参考数据，不靠增加摘要数解决。本轮不是系统综述或“全球无相同工作”证明。

### 技能执行与书目核验状态

research-lit的verify_papers.py在项目.aris/tools、tools、配置ARIS路径及已安装技能库均未解析到；按降级契约生成本地candidate_papers.json / verified_papers.json，helper verdict=WARN / verify_papers_unavailable，四篇的helper状态均UNVERIFIED。它不是文献不存在或DOI未核验：四篇分别由实际Crossref精确DOI、出版商/官方原文和Zotero附件核验，direct-metadata状态均Verified，全文状态另列。未伪造helper或独立reviewer PASS。research-wiki不存在时不创建；不扫描私人笔记，不按技能默认建立本地PDF库。以上适配服从本任务/AGENTS的更具体边界。

## 2. 最近邻比较矩阵

Zhang列除书目外均指**实际读到的SSRN方法**；正式实质版本待核。AAD列是目标/当前缺口，不是已完成系统。

| 研究维度 | Jerath2024 | Saberi2020 | Duan2023 | Zhang2026 / 已读SSRN | AAD当前 |
|---|---|---|---|---|---|
| 场景 | 单车道固定高速瓶颈、LWR | 六城市道路网络+Melbourne模拟 | 北京/深圳瓶颈树、30天 | NGSIM US101/I80波检测；journal实质待核 | SUMO模型内；Formal A源0，B另域 |
| 信息传播 | CV警报，瞬时接收假设 | 无独立联网消息策略 | 早期预测供潜在管理，未干预 | 无信息干预方法证据 | 明确gen/send/delivery/verification/adoption目标链，尚未核心实证 |
| 微观物理传播 | CV控制与运动映射，非逐跳身份审计 | 未恢复逐车响应链 | 拓扑/时序关联jam tree | 加减速change-point事件图 | W1–W9路径，独立Qualified=0 |
| 宏观交通传播 | 三角FD/LWR、总delay、ZOI | c/f/r传播与恢复率 | jam tree增长/消散 | 微观事件连通分量→波前 | 双层方向Agreed；macro算子Proposal |
| 车辆动作控制 | 特定CV减速/恢复策略，已实现模型联系 | 非研究重点 | 管理建议，未实施 | 检测已有轨迹，非随机控制 | 自动控制器实际采用/动作需证据 |
| 区域风险效应 | 结果为宏观延误，不是区域安全风险ITT | 拥堵比例，不是安全风险 | 最终拥堵规模预测 | 波检出/波速误差，不是区域风险策略效应 | Formal rho/P2结果候选不变；因果效应Unknown |
| 独立物理基准 | 解析无控制基准；非同源随机消息关闭 | 速度重排空间null | 跨日预测参考 | 专家STMap等检测标签 | 资格source-present随机no-message为主；尚无F0 |
| 因果识别 | 结构模型控制比较；不是独立随机化消息风险RCT | 拟合/空间null | 预测验证 | 物理约束关联；causal措辞不等于独立识别 | run/簇ITT设计与干扰识别；未执行确认性证据 |
| 时间优先性 | model event/null horizon，目标/策略依赖 | 宏观拥堵时间变化 | 早于最终拥堵峰值的预测 | 变化点/波时序 | P1总体H*、风险同时带+F0上界；Unknown |
| 主要局限 | 单lane/瞬时/特定控制与delay目标 | 单日、均匀混合、SIR不可重感染 | 一月两城、速度聚合/回顾树归属 | 轨迹质量/图约束；正式版本全文受阻 | A源/witness/F0缺、支持域/覆盖/参数未定 |

## 3. 已有研究覆盖与剩余差异

**已存在、不得再独占的内容。** 信息比物理更快、远端消息改变车辆动作、信息/运动网络耦合、信息→动作→宏观交通、作用空间边界、宏观拥堵contagion、瓶颈早期信号、车辆change-point图/制动级联均有直接先例。P0已核的Schönhof2006与Wang2019信息波进一步压缩泛概念新颖性。Hudgens–Halloran和Aronow–Samii已提供干扰下效应对象和设计框架，AAD不能称发明网络因果理论。

**信息控制联系已有谁做到？** Jerath明确以消息触发CV减速，解析比较总延误和ZOI；这直接否定泛化“此前从未建立信息—车辆动作—宏观交通状态联系”。P0已读Peng2026的随机BLOS警告动作结果也否定“首次警告因果改变动作”；其驾驶者结果仍不等于区域安全风险效应和独立普通物理到达分布。

**物理/预测与干预有何不同？** Saberi是网络物理拥堵状态拟合，Duan是已开始增长的拥堵预测，Zhang已读方法是轨迹事件检测图。三者不提供本任务所需独立信息策略随机化；但它们已占有传播模型、早期时间结构、微观事件联系，因此不是只说“非信息风险”就可忽略。

**生命周期与F0有哪些空白？** 本轮四工作均没有在已核材料中展示AAD要求的同源generation→delivery→verification→controller adoption→command/actuation→region risk的完整可审计记录和同资格随机source-present no-message到达参考。Jerath采用/动作由模型规定，不是独立测得；空间null、无控制baseline、专家检测标签与随机no-message是不同对象。正式Zhang未得全文，关于其最终版缺少全部机制只能保留未核验，不能下全称否定。

**是否已发现完整替代？** 在本轮及P0已读集合中未找到同时完成以上全部联合契约的单篇；这只是有范围的检索结论。不能由“未找到”推出世界首次，也不能由工程日志更全就自动推出科学创新。

## 4. 候选创新及证据等级

| 候选 | 已有工作 / 真正增量候选 | 理论条件 | 所需实验结果 | 当前等级 |
|---|---|---|---|---|
| 同源事件的可审计联合证据契约 | 各链条已有；增量可能是将实际采用/动作、区域风险策略效应和独立物理参考可检验地连接 | assignment/actual分离、盲Qpre、支持域、完整失败保留 | 真实合格源、完整message链、独立run/簇区域ITT及匹配F0 | Hypothesis / Proposal，非已证创新 |
| 有限观测机制下总体时间优先性 | 预测early/信息先到已有；增量是联合控制不确定性的风险早窗与独立物理分布 | 预定H*/SESOI/同时带、clock/删失、风险与F0同总体 | 风险带稳定越过−δ且F0上界<η，并报告负结果与适用域 | Agreed研究方向；科学结论Unknown |
| 双层物理竞争解释审计 | macro交通量、micro图已有；增量可能是冲突可审计、覆盖与不可排除机制明确 | 不机械融合；每层独立质量/源归属 | 多种交通域下双层证据与cohort错位实例的预先规则验证 | Agreed双层方向；具体规则Proposal |
| 失效边界与迁移规律 | ZOI/早期预测鲁棒性已有；需新的可解释风险机制规律 | 预定条件、充分独立重复、无选择报告 | adoption失败、物理早到、异质交通下risk/temporal失效边界 | Hypothesis；当前B结果只校准域反例 |

独立判断：如果最终成果只是四格差值加完整日志、几条波图和一个人为速度阈值，方法组合不足以支持强NC创新。必须产生可反驳、可迁移的机制结论：何种条件下信息策略风险效应早于指定物理状态、为何失败、在测量不确定性下仍成立；且证明这不是source资格/风险聚合/时间窗选择的产物。

最接近的五篇：Jerath（信息控制及作用范围）、Zhang（车辆级物理事件图，最终版待核）、Peng2026（P0已读随机BLOS动作效应，DOI10.1016/j.aap.2026.108642）、Saberi（网络物理传播）、Duan（早期信号）。它们分别覆盖不同维度，不能按单一相似度排名就裁定整个方向无创新。Schönhof/Wang仍是必须引用的概念和信息波威胁，详见P0矩阵，不在本轮重复精读。

## 5. 微观—宏观—cohort的理论审计

Jerath已明确microstate到指定macrostate映射取决于研究目标；Saberi用道路拥堵比例，Duan用道路树，Zhang用运动学事件图。三类节点/边/时间尺度不可混同。LWR波速取决于密度/流量状态；leader→follower响应方向与车行方向相反的例子不证明所有交通波都上游传播。时空靠近、图连通、真实响应、源因果归属是递进不同证据。

推荐保留三个独立输出：W1–W9逐跳micro记录；预定lane-space-time的macro量及变化区间；固定cohort signed-decline状态。DEF-PHY-010的证据向量与细则H冲突表为Proposal，方向已Agreed。micro+ / macro−可因局部响应或聚合稀释；micro− / macro+可因未测路径/外源/需求变化；两阳性仍不自动证明因果；两阴性只表示指定测量能力下未检出。cohort全覆盖不等于区域全覆盖。

宏观建议采用Edie型同域量：q_A=Σd_i/|A|，k_A=Σt_i/|A|，u_A=Σd_i/Σt_i，严格裁切部分轨迹。官方Hall章直接支持时空矩形总行程/总时间、部分穿越与点速度平均区别；Edie1963原文未获得，不冒充精读。完整瞬时空间普查的算术均速也可有明确macro意义，不能粗暴说“所有车辆均值都不是macro”。问题是采样支持、权重、时窗和分母未定义；fixed-cohort统计与动态区域状态回答不同问题。

不以cohort迟报警支持更强时间优势，不以降低θ补概念错位。macro空间区划/窗口/检测强度、质量门、source attribution和主要endpoint须研究者决定；本轮不新造OR/AND二值Physical Arrival。

## 6. Qpre、四格、F0与网络干扰的数学审计

正式定义和推导在CORE DEF-POP-001、细则I。Qpre位于ZS之后、ZC之前：对通信策略是pre-treatment，对源分配不是普通baseline。资格后随机ZC可识别τQ=E[Y(1,1)−Y(1,0)|Q(1)=1]，需资格盲法、无anticipation、随机概率/正支持、稳定版本、干扰与缺失条件。

跨四格的共同H必须源分配前定义；通信前H若已受源影响，可用于限定通信效应背景，但不能冒充全四格共同baseline调整。P1四格τSC=τITT^(S=1)−τITT^(S=0)；同支持/权重下τITT^(S=1)=pτQ+(1−p)τ非Q。非资格臂没有随机支持则τ非Q未知；source-absent没有实际源资格Q(1)，条件四格属于principal-stratum跨源问题，需要额外假设或另一个真正源分配前可定义的共同资格。不能把只观测Qpre=1的source-present两臂差值代四格交互，也不能把F0^Q代全部ZS=1 F0。

四格设计保留与资格两臂分析数学上可兼容，前提是明确不同estimand、各自支持与随机化顺序；不是已证明单一筛选规则同时识别两者。需要研究者裁定无资格部分/无源臂公共资格和clock的实施，不新增臂/矩阵。模拟配对中可预定借(1,0)clock作比较索引；它不是无源实际onset，不能自动搬到独立现实事件的个体反事实。确认前物理传播照常记录。

P0 interference框架兼容此嵌套总体：把run/道路时间簇作为分配与不确定性单位；若消息或物理链跨簇泄漏，partial interference不成立，需预定一般exposure mapping或全网络policy estimand及支持。不能用帧/车辆数量伪增独立n。delivery/verification/adoption/处理后Witness失败保留原ITT；机制日志不足以识别自然中介或adopter effect。

## 7. F0与总体时间判据边界

F0^Q具有明确统计意义：在同资格source-present、ZC=0总体中按指定endpoint、H、区域和观察窗定义arrivalCDF。No-message包含普通物理传播；无源运行、发送失败、B域未检出均不是该分布。当前A源0、Qualified独立witness0，不能估F0，不报告数值或时间优势。

沿用P1：预定H*内风险全网格同时上带按持续规则低于−δ，且F0^Q(H*)有效上界<η；joint error与clock覆盖可按预定预算控制。不把两边pointwise CI拼起来扫描；多endpoint/窗需预定族，具体估计器与数值仍未定。精确完整时间用ECDF；独立/条件独立右删失才可KM；区间删失需inspection假设、Turnbull或保守识别带；Unknown/信息性缺失需界限/敏感性，不能补零/补∞。clock外扩和onset区间相交则not established，不取中点。

TR upper<TP lower是总体判据的简写，不能从两臂边际分布恢复单个处理事件TP(0)−TR(1)或其跨世界联合概率。η不必等于0；即使判据成立，也只能限定“总体通常尚未达到所定义状态的窗口”，不能称所有物理影响都被排除。

## 8. NC定位、重大漏洞与下一步

优势：问题可被明确证伪，双链/资格/独立参考/时钟/Unknown治理有利于可信机制研究；近邻尚未在已核范围内同时提供完整联合风险证据。风险：联合日志可能被视为系统集成而非科学规律；Formal A无事件，物理观察支持不闭合；B校准不迁移A；参数与region/cohort错位；四格处理后筛选；行为时差替代总体风险时间；风险代理有效性、一般干扰及现实外推仍不足。Zhang最终版缺失限制最近邻判断。

这些是足以影响强论文结论的重大识别漏洞，不是调参小问题。没有证据证明AAD核心假设成立，也没有证据足以据此否定整个方向。当前NC主张不具备实证闭环，不能声称创新性已经确立。需要：合格Formal A源且不降门槛、盲Qpre可实施性、独立双层物理观测、同域随机no-message与风险策略数据、预定统计错误/SESOI、可审计消息采用/实际动作、跨场景失效和稳健性；现实结论另需独立有效性依据。本任务不启动这些实验，下一步须研究者审核专项决策清单。

## 9. Zotero、来源与限制

四条既有parent保留：ZAHRLZ56、YA2ACMZV、5DE6L9RS、Q65YUJ89；没有重复创建。逐DOI核题名/作者/date，简称由Crossref short-container-title自动取回，保留已有集合和历史tags，增dated Task4阅读标签/笔记。CLA3GKSX只改附件标题明确SSRN，不改原字节/parent、不merge/delete。新增必要技术章Hall：26RQQ7EE，原文PDF导入本地Zotero；没有期刊IF/CCF可赋，出版年未核实，EI Unknown；本轮未生成该章双语机器译文。

索引仍是P0/PAPER_REGISTER.csv和doc/literature-notes轻量快照，不新建竞争PDF库。所有直接使用的原文附件、SHA、API读回及访问限制见阅读笔记与Task4审计manifest。三篇期刊活动正文精读完成，不等于外置全部supplement均精读；Zhang正式全文不可得是实质限制，不能称四篇期刊全文全部完成。
