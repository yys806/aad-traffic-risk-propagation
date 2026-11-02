# AAD Parameter and Calibration Register

版本：AAD-SCI-DEF-20261102-P2T6-v0.4。当前有效增量为文末 Task6；前面 v0.1–v0.3 表格保留历史。当前没有经交通数据验证的 Physical Arrival 数值推荐。Unknown 是合法结论；数学域、算法探索网格和交通经验范围分别登记。D1–D7 方向已 Agreed，具体数值和下述推荐仍 Proposal / Awaiting Researcher Decision。

| 参数 | 含义 / 单位 | 推荐值或规则 | 合理范围 / 探索范围 | 确定依据 | 敏感性与依赖 | 状态 |
|---|---|---|---|---|---|---|
| Baseline window W | 源前参考长度，s | 未定；窗末严格早于L_S并排除预兆 | 数学W>0且有足够有效数据；V2仅2/5/10s | V2相邻源前窗口；L10过程baseline；L12域依赖 | 长窗降独立噪声方差但增趋势偏差；相关噪声不按1/n降 | Proposal；真实范围Unknown |
| Baseline model | 常数或处理前趋势预测，m/s | 静态仅在稳定性支持时；必要时处理前拟合趋势并单独验证 | constant/linear或匹配无源参考候选 | V2趋势null误报24/24，说明必须检验趋势 | 去趋势可能吸收缓慢真实传播；严禁处理后拟合 | Awaiting |
| θ_P | 均值下降阈值，m/s | 无唯一推荐值；交通null窗口FPR约束下联合选θ/h | 数学>0；V2/B仅0.25/0.5/1，无A或现实迁移依据 | L8/L10；V2 operating curves | 低阈易触发/高阈漏检；依赖N、baseline、相关性、时域 | Unknown；不得冻结 |
| standardized threshold | 以背景变异缩放，dimensionless | 可比较，当前未测试，不推荐k=3 | 合理k范围未知；σB须估计误差/序列依赖 | NIST CUSUM的k/h与AAD θ/h不是同参 | 多重监测、σ估计、密度依赖使固定k不可通用 | Proposal not evaluated |
| h_P | 最小观测持续跨度，s | 数值未定；使用t_last-t_first，不加一帧 | h>0；V2 0.5/1/2s | v1缺陷撤回；V2测试和持续敏感性 | 大h漏掉短段并增加确认延迟，非自动科学更好 | Awaiting |
| q_P | 最大有效观测间隔，s | 与实际采样/允许缺口联合确定 | q≥有效采样间隔才可连接；V2 1.1/3.1/5.1×dt | V2 block-gap/missing实验 | gap-bridged非真实连续；q大弱化证据 | Awaiting |
| coverage c_P | 有效在区观测人数/N，比例 | 不建议由0.8或0.9经验拍定；完整面板或missing bounds | 0<c≤1；V2 0.8/1.0 | V2缺失/退出压力；固定cohort识别分析 | 大门槛增Unknown，小门槛增选择风险；门槛不修复MNAR | Awaiting |
| Recovery rule | 首段终止与退出持续 | 建议显式低于进入阈值即终止检测段；状态恢复另确认 | 退出持续长度未定，须与首段逻辑区分 | V2显式阴性重置；主文细则C | 影响重入与重复事件，不倒改首次onset | Proposal |
| Hysteresis | 进入/退出不同阈值 | 首版不默认加入；如用需独立校准 | θ_exit<θ_enter，仅为结构约束 | 本轮未测；无文献数值迁移 | 增少抖动也可能延长状态、改变事件数 | Unknown |
| Individual/proportion thresholds | 单车m/s+群体比例 | 仅作辅助，不替代均值并偷偷改量纲 | V2单车0.5m/s、比例0.25/0.5/0.75 | 量纲/对象分析；半cohort响应差异 | 同时引入两个阈值；与affected人数强相关 | Proposal |
| Qualified Witness | W1–W9证据条件 | 逐跳满足全部并审查竞争解释 | 数值gap/响应强度/reaction window待定 | P2、L8及Task10无独立witness | 门槛严格可能低灵敏；拓扑不能补充缺证 | Proposal |
| Identity continuity | 实体ID一致性 | 不明切换断链、role/leader切换分段 | 无通用允许跳跃数 | Task17–19局部完整；全区域未证 | 错合并产生虚假多跳 | Proposal |
| Observation quality | 速度、gap、道路坐标、phase质量 | 有效性逐字段判定，不插值充真 | 数值noise tolerances未定 | 当前正式测量validity；L8 | 去噪改变crossing/延迟；需保留raw+derived版本 | Awaiting |
| Clock offset/drift tolerance | s,s/s | e(t)有同步/phase实证后才赋值 | 无AAD数值范围；同仿真钟也需step相位审计 | RFC5905 §8/11.1；Task18phase | 误差外扩可能消除时间分离 | Unknown |
| Censoring handling | 事件时间估计 | ECDF/KM/Turnbull/界限按观察机制选 | 具体估计器/置信水平未定 | L14全文；P1 §7/8 | informative censoring使常规估计偏误 | Proposal |
| No-message estimate | F0目标域/识别 | 主参考随机source-present no-message；Qpre子总体明示 | 资格、随机概率、H标准化待定 | P1/P2；本轮资格审计 | 资格筛选、竞争源、非独立单位可改变estimand | Agreed资格后通信随机化方向；估计器/数值Proposal或Unknown |
| η,δ,α,H* | 早窗、SESOI、同时覆盖 | 沿用P1原则，不新增数值 | 未定，不由合成代理决定 | P1 Estimand §7 | 事后扫描需同时界；联合错误预算 | Awaiting |

## 联合校准选择流程（Proposal）

1. 处理前锁定候选指标、交通适用域、单位、区域/cohort/window及真实null与受控标签；B域独立标记，A需合格源事件。
2. 交通数据按独立运行/seed或场景划分校准和验证，不能按帧随机拆分同一轨迹；保护既有locked holdout。
3. 联合扫描W、baseline model、θ、h、q、coverage、恢复；采用窗口/事件级FPR及其上界、valid detection、条件延迟和Unknown率。预先规定可接受FPR/漏报损失，当前研究者未定。
4. 校准中选择满足约束的简洁稳定区域而非最早报警；验证一次，失败如实保留，不把验证再变训练集；按密度/跟驰/换道分层检查可迁移性。
5. 独立标签和质量足够才可推荐交通数值。当前有合成生成器验证及独立B域运动学，B没有目标cohort阳性，所有交通数值继续未定。不能直接借用Formal P2的TTC2s、0.2s持续和0.11s gap。

V1原5s、k=3、h1s、q2dt“起点推荐”已撤回：既未测试standardized阈值，也缺交通null/ground truth。此撤回保留于Task3结果和账本，不影响历史Task1/2。

## B域校准更新（2026-11-02）

B60run沿用42候选，没有根据validation重新调参。cohort峰值mean下降0.01623808–0.02806257m/s，所有候选无报警；该观察不是“合理阈值应该降至0.02”的依据，因为null也处于此范围，且无独立目标arrival阳性。每validation条件n6的0报警95% Wilson上界约0.3903，不能保证低FPR。θ/h/W/q/c的AAD经验合理范围仍Unknown。

B固定cohort覆盖1.0并不意味着所有区域车辆都属于cohort；s1–s4在region内先响应的例子说明coverage与物理机制排除是不同问题。新增参数推荐须先明确claim支持域，不能用更细阈值解决对象错位。B域参数只为本次独立配置，不迁移正式vType、Formal P2/rho或真实交通。


## Task4状态修订（2026-11-02）

无新校准、无任何数值冻结。Qualified Witness继续采用W1–W9的方向为Agreed B，具体质量门仍Proposal。No-message主参考的Qpre后随机化与一致支持为Agreed C；H*/全时间带/联合错误/SESOI原则为Agreed D，具体数值和估计器仍Unknown/Proposal。旧Task3探索网格不因此变成合理推荐范围。

新增待研究者确定的参数对象：macro空间分区/窗口长度、轨迹普查或抽样权重、各机制覆盖/检测强度、独立波前质量、micro/macro冲突处理与检验族预算。其数值推荐及经验合理范围均Unknown；窗口越大可降噪但稀释早期局部变化，越小增多重监测/缺测；稀疏抽样下扩大覆盖阈值不能修复选择。选择需独立标签与预定错误损失，不能为最早风险/最晚到达而优化。


## Task5完整参数确定路线（无新校准 / 数值Unknown）

下表补足每个参数的数据需求、依赖与独立验证；上表V2/B探索网格保留，不改名为经验合理范围。Zhang正式β/距离/波速等为作者NGSIM域参数，不是AAD推荐。

| 参数 / 数学意义 / 单位 | 文献和当前证据 | 当前可识别范围 / 数值建议 | 关键依赖与改变后果 | 需要的数据、校准和独立验证 |
|---|---|---|---|---|
| W与baseline窗末，s | CORE G；NIST过程基线；V2趋势null失败 | 只有W>0及窗末≤L_S的结构约束；交通范围Unknown | W与交通非平稳/自相关、N、source误差共同决定偏差和方差；长窗不必更好 | source前足量稳定/趋势null、密度分层；独立run比较预测误差/漂移及窗口级FPR |
| baseline model，m/s或q/k/u各自单位 | constant/trend为Proposal；Task3未验证去趋势 | 不能选择唯一模型 | 处理后拟合可吸收真实传播；macro必须同域同窗，不同车构成不能冒充同cohort | 仅pre-onset训练；另一个交通时间块验证；不读现有locked holdout |
| θ_P及macro θ，m/s或各状态量单位 | V2仅算法验证；B cohort无阳性；Zhang不是同量 | AAD数值/经验范围Unknown；θ>0仅定义域 | 与W/h/N/噪声/密度及SESOI无直接换算；提高θ延迟并漏小传播 | 独立交通null + 盲标签阳性及强度序列，按预先FPR/漏报损失选稳定区域；验证不再调参 |
| h_P及macro持续，s | 观测跨度t_last−t_first；原V1撤回；V2验证 | h>0，数值Unknown | 与q、采样、look-ahead、window相关；h增大会延迟确认但不能把确认改onset | 短null波动与真实持续段标签；报告FPR、valid detection、条件delay、Unknown；run层留出 |
| q_P及micro缺口门，s | 原始采样/身份质量契约 | 实际观测可连接的结构约束；数值Unknown | q太大把未见连续性当真，q太小增Unknown；不能插值补真 | 已知真实轨迹的采样/缺失压力资料；本任务不新增实验；未来独立缺失模式验证 |
| cohort coverage，固定N比例 | Task3完整cohort仍不涵盖区域其他车 | 阈值Unknown，0<c≤1仅数学域 | 增阈增加Unknown；不修复退出结构性无定义或MNAR | 在区成员与身份/传感缺失分开标注；用可辩护范围构造缺失界；不动态补位 |
| macro覆盖与抽样概率p_i，比例 | Hall稀疏probe不直接给q/k；CORE K | 全普查或可识别抽样机制优先；数值Unknown | 车时、车距、空间时间覆盖不同；HT ratio非有限样本无偏 | 全域真值对照的传感/轨迹抽样方案；已知p>0及选择机制，分层独立验证 |
| recovery / hysteresis，状态或s | CORE C；Zhang恢复速度16ft/s不迁移 | 首段显式阴性重置推荐；退出持续/双阈Unknown | 影响重复段与持续长度；不能倒改首onset | 稳态/恢复与stop-go标签；检验抖动、漏短段、重入，单独验证 |
| clock tolerance，offset s/drift s/s/phase s | CORE G；旧Task18 phase仅局部实现证据 | 没有实测界不填0 | 影响源与响应顺序、risk对齐和最终分离；共享误差只能有证据抵消 | 同步/phase日志、重启/漂移记录；独立校准时段验证包络覆盖；统计包络纳αclock |
| W1–W9身份/关系/源响应质量门，各字段单位 | Task1/2；Zhang正式仅候选提取；独立Qualified0 | 逐项门方向保留，数值reaction/gap/noise范围Unknown | 更严可损灵敏；图边密度不等于资格/因果正确率；多跳累积缺口 | 盲标真实leader、变化段、竞争源与错配；逐跳/完整路径precision-recall及起点包络覆盖，run/domain独立验证 |
| macro R_l、L_l、w_M、网格Δt，m/s | Hall同域/部分穿越；Task3 B反例支持全区测量需求 | 几何/测量结构可定义，AAD数值Unknown | w_M与θ/h共同改变对象和延迟；L太大稀释局部波，lane合并掩盖异质 | 已有全区轨迹完整性审计；未来预定几何覆盖、分lane盲标签、不同window敏感性；不择最晚arrival |
| η，允许物理到达比例，probability | P1/Task4 Agreed总体框架 | 科学容忍度待研究者，非数据调优 | η越小要求越多n0/更少Unknown；不等于每事件无物理影响 | 研究者指定有限机制主张；用CORE O零到达可行性约束规划，不由B阴性倒推η |
| δ，风险SESOI，risk | P1已有对象 | 科学意义未决；不得借速度阈值或合成生成值 | 决定科学重要性与功效，非p<.05替代 | 基于Formal风险量纲、背景负担及安全意义；独立精度规划 |
| α及各子预算，probability | P1全网格同时控制；Hoeffding原始定理支持保守族界 | 数值/分配Unknown | endpoint×区域×网格×H越多界越宽；共享no-message仍需joint覆盖不需独立 | 先预定检验族与科学错误损失；后对实际分配/缺失机制做覆盖验证，不能逐点CI冒充同时 |
| H*与风险持续/网格，s | P1 H4方向Agreed | 数值Unknown；必须分析前选 | 与确认延迟、源onset区间、macro窗及有效support相容；事后扫描增加选择 | 独立设计/校准资料规划可观测早窗；不能因主数据结果调整H*或删早物理例 |
| 风险范围[A_R,B_R]，risk | Formal结果契约待核实 | 不凭直觉封顶DRAC；无界则本Hoeffding风险路线不可用 | 修改clipping会改正式科研量，禁止本任务实施 | 回读最终选择的Formal区域结局证明范围；否则另审计设计相容的cluster simultaneous方法 |
| independent n / randomization，count | P0/P1簇与干扰；Task3 run不是正式ITT样本 | 正式有效n=0，不给Pilot样本数 | 车辆/帧不增加独立n；非Q/无源支持缺口不靠加seed修复 | 研究者确认分析对象后设计run/block抽样，合法数据不接回locked holdout；覆盖/精度与成本规划 |

路线图：先定scope/endpoint与科学错误损失 → 资格和全区数据可观测性 → 仅复用合法历史/公开校准资料审计 → 未来经另行授权获得足够null与盲阳性 → 按run/场景划分calibration与一次独立validation → 联合选W/θ/h/q/coverage/window的稳定解域 → 验证失败保留并重新研究，不将验证集继续调参后称独立 → 研究者审核后才可能冻结。当前步骤未运行任何新数据生成，不能声称后续校准已经完成。



## Task6 当前科学验收标准（SAC；v0.4）

来源：研究者 Task6 D5/D6；P1 ESTIMAND_SPECIFICATION §7；Task3 原始计数；CORE 当前操作细则。以下数值均是**损失/资源权衡的 Proposal，不是交通实证下限或 Agreed**。一并提交 [T6-R1–R6](../P2/P2_TASK6_RESEARCHER_DECISIONS.md) 决定。

| 科学量 | 精确定义 / 单位 | 现有支持与当前值 | Codex 推荐 / 替代 / 科研后果 | 冻结时点与确定方法 |
|---|---|---|---|---|
| SESOI δ | 固定风险结果同单位的最小有意义下降，δ>0 | P1 有定义、无效应价值依据；Unknown | 先用既有 rho 的原单位积分确定 δ；附 δ/L 的窗口归一解释；不从速度阈值或显著结果倒算。替代预先指定风险均值需研究者接受版本 | 正式风险功效计算前；研究者以风险后果/领域意义确定，参数测量校准不以 δ 选阈值 |
| η | 同资格 no-message 在 H* 前真实指定状态到达的允许总体比例 | P1 原则；无 F0；Unknown | 建议审阅 1% 与 5% 两档损失情景，严格档1%为推荐 Proposal；后者允许更多普通物理到达、主张更弱；不是 c_P | 正式早窗预登记前；研究者选择，不由 cohort 无报警确定 |
| H* | 源物理 onset 后预先规定的总体早窗，s | 未有可校准 A onset；Unknown | 依固定区域/机制、可观测期及独立物理时间证据先定，不能用 TR 或验证最优窗反选。推荐 onset 区间对齐，confirmation 轴仅敏感性 | 校准前先定适用时间域和最大延迟预算；正式数值须风险观察方案批准 |
| α | 正式多时点/区域/endpoint 联合错误概率 | P1 原则、无接受数值 | Proposal 0.05；R/P/clock/measure=0.02/0.02/0.005/0.005。更严格档0.01增样本；不是 detector FPR | 正式推断前。校准 β_V 单独登记；若证书用于 α_measure，证书失败预算不得大于该项 |
| Event FPR p_F* | 真 null 单位在固定监测域出现至少一次错误状态报警概率 | B 无目标阳性；仅 B 无源背景可供本域小样本描述；Unknown | 推荐审阅上界1%，资源档5%；两类 null 分别验收，低 FPR 有利排除误报但通常牺牲 sensitivity/延迟 | 校准前；研究者选择损失，精确二项/簇方法验收 |
| Sensitivity s* | 独立真阳性单位获得匹配且有效检出的概率；Unknown 计不成功 | B 不能估；V2仅生成器；Unknown | 面向早窗，推荐及时有效检出下界≥1−η/4；η=1%时为99.75%（损失Proposal非实证）。95%/90%仅宽松测量方案，不能自动证η=1%；须独立a*/b*/标签域，不能保证任意小扰动 | 校准前；逐层独立真值，不使用正在调的 θ/h 定标签 |
| Miss rate m* | 同一真阳性分母内未有效检出的概率；含 Unknown；m*=1−s* | 无真实目标阳性；Unknown | 早窗推荐 m_delay≤η/4；一般测量可比较5%/10%，但此证书不足以支持η=1%。known miss/Unknown另报，不混观测原因 | 与 sensitivity 同时；与有效检出互补时才使用等式 |
| Detection delay d* | 从真 onset 到首次观察/确认/可用的三个延迟；验收主用可用延迟上界 | B 无目标 onset 真值；Unknown | Proposal 检查 P(有效且可用延迟≤d*) 的下界，而非仅检出者平均；候选 d*≤0.1H*，资源档0.2H*，均非交通依据 | 校准前；若采样/持续/算子使预算不可行，报告不可行，不后移物理 onset |
| Unknown rate u* | 全部指定单位中质量/标签/归属等不能判定比例，各原因分列 | 无充分本域校准；Unknown | 早窗推荐上界≤η/4，η=1%时0.25%（Proposal）；一般测量5%/10%只作宽松方案。Unknown和漏检必须连同抽样余量/已可能到达质量一起小于η，不能单独满足门槛就宣称早窗 | 校准前；统一 assignment/预列运行分母，不能靠删样下降 |
| Power 1−β_pow | 指定真值下通过预定检验/验收的概率 | 方差/真实误报/簇结构未知；Unknown | Proposal 0.90，替代0.80；明确 good FPR、good sensitivity、交互最小效应及风险 τ_alt<−δ | 选定验收标准后按实际独立单位计算；不能用“全零所需n”冒充功效 |
| Independent n | 实际独立 run/随机簇/场景块数量，count | V2=768面板；B=60运行，不等于全部跨条件独立；Task9共享候选/seed | 完整 run 为基本单位；复用 seed/共同输入则按最大依赖 block；多密度/多参数评价不是增加n | 运行前登记依赖键，按实际设计取样/随机化推断 |
| Truth scope a*,b*,e_truth | 独立阳性定义的最小物理信号、持续与真值误差，层内单位 | 不能从42候选或B无报警估；Unknown | 先声明可观察的有限物理范围；幅度/持续独立于 detector θ/h。弱于范围的信号单报、不冒称灵敏度已覆盖全部物理 | 正/负标签生成前；与 θ/h 区分，是T6-R2核心科学选择 |
| False attribution f_A* | 已知非指定源/竞争源单位错误归为该源的概率 | 无独立归属金标准；Unknown | 推荐与 event FPR 同档上界；Macro any-source 不做伪 source-specific 判定；不可归属记 Unknown | 校准前；独立 decoy/多源标签，不能用图最短路当真值 |

SAC 的 FPR 是测量损失，α 是推断错误，η 是总体物理到达容忍；三者不互换。d* 不是 onset，θ 不是科学下限，δ 不是 m/s。区间标签的不确定性进入验收界，不用中点。

## Task6 全参数十三字段登记

探索级记号：B_pre 为可用且无预兆的处理前跨度；r_u 为独立审计的速度测量分辨率/误差尺度；d* 为上表待决延迟预算；Δ 为原始名义步长；g_50/g_90 为校准原始缺口分位数；m 为预置缺失比例；L 为已批准测量区域长度。候选生成只使用 calibration 的处理前支持、已登记真值与质量记录；不使用风险效应、验证集或 locked holdout。所有候选先写入 manifest；空域/无足够标签即 Unknown。秒数/米数未定不构成新的设计任务，下一参数实验按这些规则生成具体候选清单。

文献代码：H=Hall/FHWA §2.1–2.2（Task3 L12/Task5 M3，部分章阅读）；Z=Zhang正式版（Task5全文，参数不可迁移）；N=NIST过程测量/精确二项方法；F=Frangakis–Rubin（Task5 M1）；HF=Hoeffding（Task5 M2）；JSS=Task3 L14；P1=P1 Estimand。实验代码 V2、B60、T19 仅限已审计域。**下表每行“交通经验范围”均 Unknown；候选是方法性探索，不是默认推荐值。**

| 参数 / 符号 | 数学定义 | 单位 | 对象 | 数学域 | 算法探索范围；交通经验范围 | 现有实验支持 | 文献依据 | 依赖 | 错误/延迟/选择后果 | 校准方法 | 独立验证要求 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C01 baseline W | [t_B−W,t_B)，t_B<L_S | s | Cohort/Macro baseline | 0<W≤B_pre | {B_pre/4,B_pre/2,3B_pre/4}中质量可行者；经验Unknown | V2仅2/5/10s；不迁移 | N、H | C02/采样/趋势 | 长窗趋势偏差，短窗高变异 | pre-source块预测误差+null FPR，固定模型比较 | 新run/新场景同支持 | Proposal；秒数Unknown |
| C02 baseline model | u_i^B(t)=常数或仅pre拟合线性预测 | m/s | Cohort/Macro | 可识别处理前模型 | constant / linear；不支持者拒绝；经验Unknown | V2 trend-null24/24，未验证去趋势 | N、H | W/自相关/构成 | 处理后拟合吸收信号；去趋势可能漏慢变 | 固定W比较pre块外预测和null/positive | 新场景趋势、稳态各验 | Proposal |
| C03 θ_P | full fixed-N signed decline≥θ_P | m/s | Cohort | θ_P>0 | max(r_u,cal-null事件最大残差Q_.90/.95/.99)；另列a*/4,a*/2,a*，有限去重；经验Unknown | V2/B .25/.5/1仅历史网格 | N、P1 | W/model/h/密度/N | 低θ误报，高θ漏弱响应/晚检 | 固定其余，event FPR与timely recall联合曲线 | 预选候选新run，含a*边界阳性 | Unknown数值 / Proposal网格 |
| C04 h_P | positive段末时刻−首时刻≥h_P | s | Cohort | h_P>0 | {max(2Δ,d*/4),max(2Δ,d*/2),d*}且不超真值/随访支持；经验Unknown | V2 .5/1/2s，仅合成 | N、P1 | θ/q/recovery/d* | 长h漏短段、推迟确认 | 单因素再θ×h与h×q | 短段/持续边界阳性；计时无加一帧 | Unknown |
| C05 q_P | 段内最大有效相邻时差 | s | Cohort | q_P≥名义Δ；长缺口断段 | {Δ,g_50,g_90}中≥Δ者；gap-bridged单标；经验Unknown | V2 1.1/3.1/5.1Δ非推荐 | N、JSS | h/missing/identity | 容大缺口增加隐含未见变化；小值Unknown增 | 预置块缺口下复算；不插值当真观测 | 独立缺口形态/相关缺失 | Unknown |
| C06 c_P | c(t)=ΣM_i(t)/N，要求≥c_P | proportion | Cohort | 0<c_P≤1，N固定 | {1,1−m,1−2m}的(0,1]值；经验Unknown | V2 .8/1；B覆盖1 | P1、missing边界 | missing机制/θ/N | gate不能修复MNAR，低覆盖选择偏差 | mask真值对照+全cohort界；不动态补位 | MNAR/退出独立验 | Unknown |
| C07 recovery | 显式阴性终止段，恢复另确认 | rule/s | Cohort | 首次onset不倒写 | 阴性重置；退出持续{0,h_ref}仅复发敏感性；经验Unknown | V2重置测试 | N | h/hysteresis | 改重复事件/状态寿命 | 同raw比较fragmentation与误报 | 恢复/重入真值 | Proposal |
| C08 hysteresis | θ_exit<θ_enter | m/s | Cohort | 0≤θ_exit<θ_enter | off / θ_exit=θ_enter−r_u（可行时）；经验Unknown | 未测，不默认加入 | N方法非交通数值 | recovery/noise/h | 少抖动但延长状态 | 固定进入阈值比较退出与复发 | 新噪声/恢复run | Proposal；值Unknown |
| C09 missing handling | full-N量的可辩护上下界/Unknown | rule | Cohort | 不改变N，不填0 | 完整观测；有限物理界；否则Unknown；经验Unknown | V2 selective dropout；B非缺失域 | P1§8 | c/identity/退出 | observed均值不等full-N；缺失非随机 | 人工mask对照完整真值，按原因分层 | 未见缺失机制单报不可迁移 | Agreed固定N；具体界Proposal |
| U01 W1 relationship | 真实同lane leader→follower边 | ID/relation | Micro | 实际关系有向 | 无标签时不放宽；复杂边另列；经验Unknown | T19局部跟驰 | Z仅候选、P2 W1 | lane/identity | 邻近误当关系→虚假路径 | oracle/原始leader字段逐边核 | 独立真实关系或结构真值 | Agreed框架；操作Proposal |
| U02 W2 identity | source/target实体持续一致 | ID | Micro | 未证re-ID断链 | 0次未解决ID切换；re-ID须独立映射；经验Unknown | T18/19局部连续 | P2 W2 | missing/换道 | 错合并伪多跳；严格断链降敏感 | 预置ID断裂/切换，检错而非放宽 | 独立身份标签 | Agreed框架；Proposal质量门 |
| U03 W3 leader continuity | 关系覆盖源变化与目标响应支持区间 | s | Micro | 不跨未解释leader切换 | 全窗 / 按实际切换分段；经验Unknown | T19局部两车 | P2 W3、Z分段 | reaction/missing | 跨切换拼接归因错误 | leader替换/换道decoy | 独立lane/关系标注 | Proposal |
| U04 W4 source interval | actual source change∈[L_S,U_S] | s | Micro | 非空有效区间 | 原始高频真值区间；不取计划时刻；经验Unknown | B源(30,30.1]描述例 | P2时间、P1 | clock/采样 | 伪精确导致假先后 | truth clock与采样删降对照 | 独立onset/不确定界 | Agreed区分；数值Unknown |
| U05 W5 response | 目标signed速度/加速度变化候选及区间 | m/s,m/s²,s | Micro | 预定响应方向/有限机制 | 固定成熟候选提取；阈值由独立null及a*级标签比较；经验Unknown | B s1–s4候选非Qualified | Z/P2 | filter/θ/reaction | 变化点相似不证明传导 | 相同raw候选检测+盲法逐边审核 | 独立响应标签，记录look-ahead | Proposal |
| U06 W6/reaction | U_source<L_response；允许反应窗r_U | s | Micro | 顺序严格；重叠Unknown | 宽窗由独立真值反应间隔支持；分位范围附尾部漏检；经验Unknown | 尚无完整合格链 | P2 W6 | clock/采样/multisource | 窄窗漏链，宽窗误接其他响应 | 真值时延×clock误差交互 | 新反应速度/密度；不人为加delay | Agreed框架；数值Unknown |
| U07 W7 quality | gap>0、closing字段有效、坐标/速度误差及最大缺口 | m,m/s,s | Micro | 字段物理有效；不补missing | 仪器/仿真phase实证界；不借Formal q=.11s；经验Unknown | T18 native诊断；B几何gap对照 | P2 W7 | identity/clock/smoothing | 错gap/噪声可伪响应 | 原始对照+误差注入，边界保留 | 新采样/噪声/车长支持 | Proposal，误差值Unknown |
| U08 W8 attribution | 审查全部竞争源/共同原因 | categorical | Micro | 指定源 / any-source / Unknown | 保留多源，不按最短路挑；经验Unknown | B仅描述，A无标签 | P1/P2 | coverage/边界控制/通信 | 假归属或不可识别 | 多源/信号/换道decoy盲审 | 独立归属标签，无标签不估FAR | Agreed审查方向；Proposal实现 |
| U09 W9 witness | 同实体同响应段逐跳可连接并终达固定区域 | path/time | Micro | W1–W9关键项全有证据 | Potential/Observed/Qualified分报；经验Unknown | 独立source→cohort Qualified=0 | P2 | U01–08/region | 无链不等无到达；挑最早完整链有选择 | 图fixture只验证连接；独立传播标签验证资格 | 完整路径与阴性覆盖能力 | Agreed框架；Witness数值Unknown |
| M01 region/lane | R_l=[x_a,x_b]道路弧长同向lane | m/lane | Macro | x_b>x_a | 固定主区域；内部长度{L/4,L/2,L}辅助；经验Unknown | B仅单lane轨迹可复算 | H | spatialΔ/source距离 | 改主区域改变estimand | 主域不搜索；子网格比较稀释/波前 | 新域需重新报告适用范围 | Agreed原则；边界Awaiting |
| M02 w_M | A_lj=R_l×(t_j−w_M,t_j] | s | Macro | w_M>0 | {d*/4,d*/2,d*}中≥2Δ者；经验Unknown | 尚未宏观校准 | H | θ_M/h_M/spatial | 平滑降噪也推迟/稀释 | null+oracle positive固定域比较 | 新密度/短局部波 | Unknown |
| M03 spatial resolution | 主域内预列cell长度Δx | m | Macro | 0<Δx≤L；不改变主域 | {L/4,L/2,L}；经验Unknown | B域不能校全道路 | H、Z | Δt/w_M/density | 小cell空域增Unknown，多网格选择偏差 | 固定主域内分辨率比较 | 边界/局部响应独立验 | Proposal |
| M04 temporal resolution | 过去网格相邻Δt | s | Macro | Δt≥原始可支持步长 | 原始Δ及{2Δ,4Δ}降采样；经验Unknown | V2仅cohort采样 | H/P2时间 | Δx/w/phase | 采样延迟/区间扩大 | 同truth降采样，不能当新n | 独立高频truth | Proposal |
| M05 Edie support | D=Σ域内车距,V=Σ车时,A=Lw；q=D/A,k=V/A,u=D/V | veh·m,veh·s,m·s | Macro | A>0，D,V≥0；u仅V>0 | 普查原始裁切；边界不确定用界；经验Unknown | B可做窄域算子检查，非全域灵敏度 | H，Edie原文未得 | interpolation/lane/missing | 整条穿越/异域qk造成偏差 | 真值积分/入离域/换道裁切恒等检查 | 独立轨迹片段及边界误差 | Agreed主要候选，数值Unknown |
| M06 coverage/sampling p_i | 正包含概率及D/V支持覆盖 | proportion | Macro | 0<p_i≤1；未知不外推 | 完整普查主；已知p抽样敏感性；经验Unknown | 现有交通域代表性不足 | H/设计抽样 | density/MNAR/identity | 可见均速不能冒充区域速度，ratio非无偏 | fulltruth固定概率mask+HT总量/比值误差 | 未知抽样机制仅observed traffic | Agreed限制；具体规则Proposal |
| M07 state θ_M | 同域u^B_A−u_A≥θ_M；q/k补充 | m/s（q/k各自单位） | Macro | θ_M>0；V=0不判速度0 | 同C03由macro null残差与独立a*生成；经验Unknown | 未测 | H、N | w/density/baseline | q=ku非三独立证据；密度混杂 | 固定速度主候选，q/k不事后挑 | 独立每lane/密度阳性 | Proposal主变量；数值Unknown |
| M08 persistence h_M | macro正状态段实际跨度 | s | Macro | h_M>0 | 同C04，另记窗口重叠；经验Unknown | 未测 | H/P2 | w/θ/Δt | 重叠窗口不是独立重复 | w×θ、θ×h边界检查 | 独立短波/恢复 | Unknown |
| M09 lane aggregation | lane分别报；可选ΣD/ΣA,ΣV/ΣA,ΣD/ΣV | lane-normalized | Macro | 同向同time支持 | 不合并为主；合并仅辅助有单位说明；经验Unknown | B单lane不能证跨lane | H | lane长度/换道/coverage | 总车道流与lane均值混淆 | 轨迹换道唯一分配/量纲检查 | 独立多lane全量truth | Agreed分lane；合并Proposal |
| M10 source attribution | any-source状态与指定源链分列 | category | Macro | 非唯一归属则Unknown | 不以波前/图自动归属；经验Unknown | B区域/cohort不一致 | H、Z、P1 | Micro/边界/竞争源 | 区域变化误当指定源传导 | 多源decoy与独立源记录 | 无归属标签不报告source FAR点值 | Agreed限制；实现Proposal |
| T01 H* | 预定源后总体早窗 | s | 全层/Risk | 有效观察域内>0 | 科学标准确定，禁止效果导向搜索；经验Unknown | A0/F0未知 | P1 | η/α/n/delay/clock | 变H改变结论对象和多重族 | 独立物理时间依据与可行性计算 | 新域须说明，不通过验证调窗 | Awaiting Researcher Decision |
| T02 η | P(T_P≤H*)容许上限 | probability | 分层F0 | 0<η<1 | 1%/5%损失方案Proposal，并联动m_delay/Unknown/统计余量；经验Unknown | 不可估F0 | P1 | H*/Unknown/n/αP | 放宽使结论变弱；非coverage | 研究者决定+样本量可行性 | 不用结果反调 | Awaiting |
| T03 δ | 风险SESOI | risk | Risk ITT | δ>0且量纲与Y一致 | 原单位科学后果确定；经验Unknown | 缺价值/方差证据 | P1 | window/range/power | 改δ改变科学判断；非θP | 研究者选择，再功效 | 独立正式域风险数据 | Unknown / Awaiting |
| T04 α与分项 | αR+αP+αclock+αmeasure≤α | probability | 联合判定 | 非负、必要项>0 | .05及.02/.02/.005/.005仅Proposal；经验非适用 | 无最终接受 | P1/HF | endpoints/grid/n | 多重性未计失覆盖；确定界不耗概率 | 预列完整family并算union | 检查证书失败预算和迁移 | Awaiting |
| T05 [A_R,B_R] | 已有结果的可证有限范围 | risk | Risk | A_R<B_R有限 | rho贡献/均值[0,1]；定长L_Y积分[0,L_Y]；经验非适用 | formal_risk_measurement.py contribution_bounds/integrate_fixed_window | 当前源码/P1 | cohort权重/window/DID | 不允许截断DRAC；DID范围另推 | 按实际聚合/基线变换推上下界 | 核对最终Y版本，不修改代码 | Verified算子界；最终聚合Awaiting |
| T06 n与随机单位 | 最大依赖run/seed/scenario-block | count | 全层 | 正整数；n0/n1逐臂 | 以验收/功效公式求；探索24/格仅Proposal；经验Unknown | B跨条件复seed；T19共享输入 | HF/F/P1 | 簇/分层/随机概率 | 车帧伪重复、外推到新场景无据 | dependency key审计；分层/簇设计 | 新seed族和独立场景支持 | 规则Agreed；n Unknown |
| T07 sample size / power | 验收成功概率≥1−β_pow | count/probability | 校准/验证/正式 | 随设计，非帧数 | 协议§8 exact/binomial/concentration；经验Unknown | 无方差/好性能真值 | N/HF/P1 | FPR/sensitivity/interaction/α | 全零样本量非power；临界性能通过概率低 | 先指定good值/最小交互再求n | 冻结n一次验证，不逐次偷看 | Proposal，实际n Awaiting |
| T08 clock / phase | 校正offset+drift×跨度+phase误差包络 | s,s/s | 全层 | 含真实误差，有实证支持 | 同钟仍phase审计；无实证不设数值；经验Unknown | T18有执行phase | P2/RFC5905历史来源 | reaction/采样/onset | 共同钟误差不默认独立，区间重叠Unknown | 独立同步/command-readback日志，逐源端点外扩 | 新设备/step配置重新核 | Agreed区分；数值Unknown |
| T09 delay / measurement bound | P(真阳性却无d*内有效检出)≤m_delay | s/probability | 潜在物理CDF | 有独立同域标签/有效置信界 | 由预定a*,b*,d*验证，不减w；经验Unknown | B不能估 | N/P1 | sampling/h/w/Unknown/域迁移 | detector负不等真物理阴；尾部漏检可破坏早窗 | timely valid recall精确/簇下界 | 证书如用于αmeasure须联合覆盖 | Unknown |
| T10 risk grid/persistence | 预定风险网格Δ_R与连续合格段h_R | s | Risk总体T_R | Δ_R>0，h_R>0且在H*内完成 | 依正式观察能力/科学持续标准预定，非效果搜索；经验Unknown | 只有P1框架，无正式曲线 | P1§7、CORE T | H*/clock/J_R/SESOI | 事后缩网格/挑持续段扩大错误并改变时间对象 | 预定全网格包络及可行性，不用校准风险选参 | 正式独立域/同时覆盖 | Unknown / Awaiting T6-R4 |

## Task6 参数依赖矩阵与分阶段确定

J=必须联合检查；C=混杂/支持或选择约束；E=可能改变科学 estimand（必须版本化）；T=只能靠额外独立真值/独立单位确定。单因素是定位敏感性的步骤，不是交互不存在的证据。

| 组合 | 类型 | 必须固定/记录 | 最小针对性设计及输出 |
|---|---|---|---|
| W×baseline model | J/C | 相同pre支持和原始run | 2模型×W低高四角+中心；趋势与稳态分层 |
| θ_P×h_P | J/E | 固定标签、同cohort/region | 2×2+中心；event FPR、timely recall与onset区间 |
| h_P×q_P | J/C | 同mask/Δ与段计时 | 2×2；gap-bridged、Unknown、延迟 |
| coverage×missingness | J/C/T | 固定N，MCAR/MNAR/块缺口独立 | 门槛低高×预置机制；full-N误差界与选择偏差 |
| recovery×hysteresis | J/E | entering规则不变 | off/on×重置/退出持续；重复事件、寿命，不倒改首次onset |
| w_M×θ_M | J/E | lane/空间域/真值不变 | 2×2+中心；稀释、误报、可用延迟 |
| Δx×Δt | J/C/E | 固定总域及真值 | 2×2；空域、时空裁切与波前误差；主域不随结果改 |
| density×threshold | J/C/T | 预设交通密度/需求条件 | 三密度×θ低高；分层性能，不用处理后密度筛组 |
| reaction window×clock uncertainty | J/C/T | W6仍严格区间顺序 | 宽窄×实证低高误差；错序/漏链，不用中点 |
| identity continuity×missingness | J/C/T | 真身份/leader映射 | 有无已审计映射×块/MNAR缺失；虚链与Unknown |
| H*×η×α×n | J/E | 固定总体/网格/家庭 | 解析可行性表，非交通搜索；Unknown使b均值≥η时n再大也不解决 |

独立可做：单位/裁切恒等式、固定域完整truth下的数值积分/时间跨度检查；在质量界已独立确定时可单独验证clock实现。θ/h/W/model/coverage 等只可条件单因素比较，最终必须联合；身份、归属、真实onset、抽样概率和漏检上界不能仅由正在校准检测器自产生。区域/cohort/资格、truth scope、结果聚合、主时间原点及阈值状态版本的改变可能改变 estimand；采样/网格改变可观察endpoint/时序支持也须版本化。

**Agreed执行原则（D5）：** 科学标准/可行域 → 固定参考逐项比较 → 按此依赖矩阵检查重点交互 → 一次独立验证 → 稳定参数区域。旧版“联合扫描”仅表示必须检查依赖，不再作为跳过逐项步骤或全笛卡尔搜索的当前指令。[最终实验协议](../P2/P2_TASK6_PARAMETER_DETERMINATION_EXPERIMENT_PROTOCOL.md)规定具体顺序、参考生成、重复数、停止和冻结。

### Task6早窗可行性补充（当前推荐，非新识别假设）

在用检测时间桥接真实物理CDF时，必须同时满足：已检出早期质量 + Unknown可能早到质量 + CDF抽样余量 + 未及时有效检出界 m_delay < η（重复计入只会更保守，但不能漏计）。因此95%灵敏度/5%Unknown即使各自达到一般测量验收，也不能用作η=1%的排除证书。面向早窗的推荐预算是m_delay≤η/4、Unknown≤η/4，并为detected mass+统计误差留严格余量；这只是可行性/损失分配Proposal，不声称真实域能达到，也不修改核心假设。η=1%对应99.75% timely sensitivity与0.25%Unknown目标；若独立样本量/真实能力无法支持，报告Unknown/Not established，由研究者决定成本/有限scope，不反调η追结论。

正式risk的预定Δ_R/h_R和聚合窗口随T6-R4一并冻结；它们与物理h_P/q_P不同，选择它们改变时间判定/族，不能在验证曲线上选。协议已给源/钟映射包络与全网格条件，当前数值Unknown。

## Task7 有限域实验结果增量（2026-11-02）

v0.4/27定义保留。研究者Task7接受本次固定N等车signed mean、Macro同域速度主状态和Micro同lane有限机制的执行；不冻结正式参数。30行C01–09/U01–09/M01–10/T08–09结果见[参数结果](../P2/P2_TASK7_PARAMETER_RESULTS.md)，机器表evidence/research/P2_TASK7_20261102/parameter_register_results.csv。

W9/constant/θ1/h1/q.05、Macro w2是C候选，575完成/1失败、J765、V0；没有Recommended-for-freeze。Low/Medium及Macro目标格缺支持，W8/Qualified/最弱信号/ε_stab/γ_int/正式物理delay证书Unknown。T01–07/T10未冻结，正式η/H*/δ/α不改。原Task6十三字段/数学域/探索范围/历史撤回保留。


## Task8 有限支持与验证决策（2026-11-02）

Task8 D1–D5已Agreed：仅源端有界补充，a1/b1有限坐标，2h/10GiB，ε_stab/γ_int不冻结。W9/constant/θ1/h1/q.05和Macro w2仍C候选；Low Cohort/Macro及Medium Cohort缺支持，J78/state63 V0。容差网格与成本见[参数建议](../P2/P2_TASK8_PARAMETER_RECOMMENDATIONS.md)，不修改T01–07/T10正式η/δ/H*/α。
