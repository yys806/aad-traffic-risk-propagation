# AAD Parameter and Calibration Register

版本：AAD-SCI-DEF-20261102-P2T5-v0.3。当前没有经交通数据验证的Physical Arrival数值推荐。Unknown是合法结论；下表明确区分“数学合理域”“合成探索网格”和“AAD经验合理范围”。后者尚不可识别，不能把前两者改名为推荐范围。

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
