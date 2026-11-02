# P2 Task8 — 有限阳性支持与Independent V决策最终报告

Task ID：AAD-P2-TASK8-BOUNDED-POSITIVE-SUPPORT-AND-V-DECISION-20261102。状态：SUPPORT_RECOVERY_COMPLETE_WITH_LIMITATIONS；NOT_EXECUTED_TRUTH_SUPPORT_INSUFFICIENT。

统一定义仍为[Task6 v0.4、27项](../definitions/README.md)。Task7原575完成/1失败、truth v2与359/47/0历史记录不改。所有Task8结果为校准/补充支持，Independent V种子消耗0；不是现实交通验证或AAD核心假设证据。

Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS；Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock BLOCKED；StageI READY_ENGINEERING_ONLY；Stage1.1 NOT_AUTHORIZED。

## Task7不足的原始证据与三层差异

audit/task7_support_audit.csv逐单位复核全部575完成轨迹并核对原1728标签；一启动失败仍Unknown。planned C-P机会每密度120（四等级96+局部24），不是保证阳性；固定Cohort局部点原本要求阴性，A0状态阳性另列，不能把总192当计划真阳性。

- Low P22源速度确实降到2 m/s，最低加速度−4.5 m/s²，不能归为“源未执行”。代表run s1/s2/s3到a=1的时刻32.95/36.25/39.55s、位置3093.17/3091.15/3089.07m，均在Region上界3080m之外；固定域内最大下降约.0325，完整Cohort约.027–.031。表明当前剂量下响应与固定支持错位，不是观测缺失。此为已测试域限制，不证明所有可能源曲线都不行。
- Medium P22固定域内原生响应可达s8，峰值约5.94–6.08m/s；尚未到s14–s17，Cohort下降约.026–.031。Macro峰值仅.275–.279，车时权重下局部响应不足以使全域降1。Micro有阳性不要求其他层有阳性。
- High P22 Cohort下降7.78–7.86，Macro仅1.508–1.521，未达2a目标。task7_macro_dilution_decomposition.csv给出逐车D/V及车时权重，贡献和严格等于同域速度下降；.1s truth窗口与2s detector窗口分别保存，空间稀释与时间平滑不是三个独立证据。
- 原Plocal源2m/s×1s在High目标Micro峰值仅.358–.468，低于a*=1；没有可用b*=1状态，而非探测器漏检。Local pulse4m/s×1s与8m/s×1s是预列新设计，不改变Region/cohort。N0/N1完整原生面板中未出现a1b1状态，不能推出任意微小影响不存在。

实际leader和身份在完整运行中连续、目标setter=0。源端剂量、衰减、传播时间/域位置、全群体覆盖和Macro聚合共同影响支持；不把所有缺失都解释为“再加大强度”。因果归属仍需W8，以上是轨迹事实及有限工程解释。

| 缺失条件 | 补充前轨迹依据 | 本次核查问题 | 预列允许调整 |
|---|---|---|---|
| Low Cohort | 原固定群体下降约.03，前车a1响应越过Region | 固定群体能否在原Window响应 | LONG/MAX源条件 |
| Medium Cohort | 原a1响应到s8，未到s14–17 | 更长/强源是否传到完整群体 | LONG/MAX源条件 |
| Low Micro | 原首批a1响应位置大于3080m | 同域原生响应能否形成 | LONG/MAX源条件 |
| Low/Medium Macro | 局部响应的车时权重不足 | 同域平均能否达到a1b1 | LONG/MAX源条件 |
| High Macro 2a | 原峰值约1.51，小于2 | 更强源能否增大原域累计减速 | LONG/MAX源条件 |
| Local non-Cohort | 原局部2×1脉冲峰值低于a1 | 原域局部变化能否不改变完整Cohort | LOCAL4/LOCAL8源脉冲 |

以上均不改变Region、Cohort、Window、原生模型或a1b1；实际实现与失败见分设计结果表，未实现条件作为本次测试域限制停止。

## 一次有界补充及停止

R1预列100单位：三密度×LONG(8m/s×12s)/MAX(10m/s×12s)各8；N0/N1/A0各4/密度；High LOCAL4/LOCAL8(4/8m/s×1s)各8。速度下界0，不加第三档。仍用原Task7网络/vType、Krauss、禁换道、区域[1600,3080]、cohort s14–17、30–46监测和50s随访。请求1s slowDown不是实际1s完成；SUMO原生速度模式限制实际decel4.5、accel2.6，逐run核实，恢复按原曲线释放，不做target setter。

一次R1 TraCI启动失败S1_medium_MAX_01，0帧、0执行；失败seed119947188不重跑。45完成后停机，54个从未启动单位先留Unknown；原partial freeze/零帧占位完整存档。核查唯一归属本任务的orphan SUMO无监听socket后终止。根因Unverified，单进程为有限工程缓解；只首次执行原54个未用seed，无换seed/科学条件变化。后续不再修复迭代。该工程续跑不增加第三轮；原停止记录不抹除。

R1全部truth先封存，再按预注册的truth-only规则冻结R2：三密度MAX各24，High LOCAL4再24，三密度N0/N1/A0各8，共168。LOCAL8已使Cohort改变，不能当局部非Cohort阳性；选LOCAL4依据独立状态而非detector。R2全新namespace，以单进程执行，全部结果保留。R1/R2/可能V分别命名空间[20261102,8,101/202/303]；相同run跨层/参数仍同依赖block。

最大扰动后Low Cohort/Macro及Medium Cohort仍无阳性，已停止这些格；不移动Region/cohort、不延长监测域、不降a*/b*，不继续加seed或更强源。源恢复与目标恢复分别记录，50s前未恢复者right-censored，不外推恢复时刻。扰动较极端，不代表现实交通代表性。

## 分层真值与检测结果

| 轮 | 层 | 密度 | 计划分母 | Positive | Negative | Unknown | 2a*/b* |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | cohort | low | 28 | 0 | 28 | 0 | 0 |
| 1 | cohort | medium | 28 | 0 | 27 | 1 | 0 |
| 1 | cohort | high | 44 | 28 | 16 | 0 | 20 |
| 1 | macro | low | 28 | 0 | 28 | 0 | 0 |
| 1 | macro | medium | 28 | 11 | 16 | 1 | 0 |
| 1 | macro | high | 44 | 20 | 24 | 0 | 12 |
| 1 | micro | low | 28 | 12 | 16 | 0 | 12 |
| 1 | micro | medium | 28 | 19 | 8 | 1 | 19 |
| 1 | micro | high | 44 | 36 | 8 | 0 | 28 |
| 2 | cohort | low | 48 | 0 | 48 | 0 | 0 |
| 2 | cohort | medium | 48 | 0 | 48 | 0 | 0 |
| 2 | cohort | high | 72 | 32 | 40 | 0 | 32 |
| 2 | macro | low | 48 | 0 | 48 | 0 | 0 |
| 2 | macro | medium | 48 | 32 | 16 | 0 | 0 |
| 2 | macro | high | 72 | 32 | 40 | 0 | 32 |
| 2 | micro | low | 48 | 32 | 16 | 0 | 32 |
| 2 | micro | medium | 48 | 32 | 16 | 0 | 32 |
| 2 | micro | high | 72 | 56 | 16 | 0 | 32 |

| 轮 | 层 | 密度 | 及时/真阳性 | FP/真阴性 | Unknown/分母 | 已检出delay中位上端s |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | cohort | low | 0/0 | 0/28 | 0/28 | Unknown |
| 1 | cohort | medium | 0/0 | 0/27 | 1/28 | Unknown |
| 1 | cohort | high | 28/28 | 0/16 | 0/44 | 1.10 |
| 1 | macro | low | 0/0 | 0/28 | 0/28 | Unknown |
| 1 | macro | medium | 11/11 | 0/16 | 1/28 | 2.10 |
| 1 | macro | high | 20/20 | 0/24 | 0/44 | 2.10 |
| 1 | micro | low | 12/12 | 0/16 | 0/28 | 1.05 |
| 1 | micro | medium | 19/19 | 0/8 | 1/28 | 1.05 |
| 1 | micro | high | 36/36 | 0/8 | 0/44 | 1.05 |
| 2 | cohort | low | 0/0 | 0/48 | 0/48 | Unknown |
| 2 | cohort | medium | 0/0 | 0/48 | 0/48 | Unknown |
| 2 | cohort | high | 32/32 | 0/40 | 0/72 | 1.05 |
| 2 | macro | low | 0/0 | 0/48 | 0/48 | Unknown |
| 2 | macro | medium | 32/32 | 0/16 | 0/48 | 2.10 |
| 2 | macro | high | 32/32 | 0/40 | 0/72 | 2.10 |
| 2 | micro | low | 32/32 | 0/16 | 0/48 | 1.05 |
| 2 | micro | medium | 32/32 | 0/16 | 0/48 | 1.05 |
| 2 | micro | high | 56/56 | 0/16 | 0/72 | 1.05 |

表为各轮校准描述，含A0 any-source阳性；没有异质池化iid CI。0/0为Unknown，不是0%灵敏度；已检出delay只描述有效检出者，不替及时成功率。

## 源时间日志问题与W1–W9

Task7实际实现把v<源前速度与v!=getSpeedWithoutTraCI同时作为source onset。SUMO受4.5约束减速时两读数可完全相同：C_low_P22_00实际30.05s已减速，旧字段到31.75–31.8s才触发。Task8以命令时间下界及独立的源前加速度包络外原生状态签名上界记录区间，未用planned time代实际onset；签名缺失记Unknown，不称真实模型误差证书。

Documented Intent：actual physical source onset；Actual Implementation：上述AND条件延迟日志；Evidence：raw速度/加速度/native逐帧对照；Affected Files：旧executor及source-time/W6元数据；Conflict：可能错误拒绝首跳严格时序；Status: Awaiting Researcher Decision，仅指是否回溯修正Task7。本任务不改旧truth、旧代码和359/47/0历史统计。相同旧raw的独立诊断把Observed从47变为119，不是新样本、不是Qualified，更不能新增独立证据。

Task8 Potential=159、Observed=151、Qualified=0；native state positive=187是另一对象。witness_levels.csv逐跳保留W1实际leader、W2 ID、W3关系段、W4源区间、W5真实响应、W6严格区间先后、W7质量、W8竞争解释与W9同段连接。固定网络可排除信号/换道/合流/target控制/通信；剩余随机原生制动/共同原因和独立指定源归属金标准尚未认证，W8仍Unknown，未放宽。任何source claim全程弃权，0错误归属只是vacuuous，不证明归属灵敏度。

## 参数候选和容差

三层保留Task7中心：W9s、constant、θ1m/s、h1s、q.05s，Cohort coverage1/full-N、Macro w2s；仅重算中心、θ.5邻居、h2邻居，未重搜83配置。中心只可作为有限状态候选；每密度/源设计的有效检出、早报警、miss、Unknown和延迟见cell_metrics.csv。θ下降可能早于固定a1 truth，h增加可能损失短b1事件；不能只比较报警数。

R2固定MAX中，Micro三密度各24/24及时、High Cohort24/24、Medium/High Macro各24/24；Low Cohort/Macro与Medium Cohort没有真阳性分母。High LOCAL4的Micro24/24，而完整Cohort与Macro均24/24真阴性。中心在全部已实现阳性中没有及时漏检，各层逐轮负样本无FP；这是校准描述，不是参数认证。单个同质格24/24的点态单侧95%灵敏度下界也仅约88.3%，达不到95%规划要求，不能凭零失败通过。

θ=.5邻居在R2已实现MAX阳性与LOCAL4 Micro均出现早于固定a1状态onset的报警，及时有效数0/24；这里“早”相对于有限a1坐标，不等于真实微小物理影响不存在。h=2邻居在Medium MAX Macro和High LOCAL4 Micro均0/24及时（不足持续确认），其他已实现MAX格虽24/24但延迟约增加1s。故保留中心作为待验证候选，不推荐上述邻居全域替代；不能把固定中心的良好描述推成稳定区域。

ε_stab=.01/.025/.05/.1/.2和γ_int=.01/.05/.1/.2/.5仅是概率差容差情景，未冻结。配对差分按run，置信半径保留同质格n；Task7交互336格只复用原结果，不新增n。stability_tolerance_sensitivity/interaction_tolerance_sensitivity给出点估计与同时包络是否落入容差，ε/γ越宽越可能掩盖早检/短时漏检，不能凭不显著证明稳定。

附同一零差/零交互good假设下的Hoeffding充分样本成本（非零失败binomial样本量）：稳定差范围[-1,1]用8 log(2K/.05)/ε²，交互[-2,2]用32 log(2K/.05)/γ²；分配type-II边界也覆盖90%规划功效。无科学损失或独立物理误差依据，无法推荐唯一ε/γ，稳定区域Not established。

## 固定候选Independent V决策

**NOT_EXECUTED_TRUTH_SUPPORT_INSUFFICIENT**。V实际Positive=0、Negative=0、seeds=0，不执行部分验证，不把R2或旧Task7重新命名V。

固定配置验证的科学缩域：每层一组中心参数、每密度一档固定MAX源条件，保留全部三层/三密度和N0/N1/A0；不认证完整剂量范围、局部脉冲或稳定邻域。局部脉冲另作补充诊断，不能用该狭域认证替代局部性能。J=78完整登记：state63（N0/N1 FPR18、主阳性及时miss9、四来源场景Unknown36）；归属15（FAR9、source Unknown3、Qualified timely miss3，其中金标准缺失）。延迟上界4s和及时灵敏/漏检共用同一个二项成功谓词，不重复计信息。

βV=.05，good FPR/FAR=.002对.01、good miss/Unknown=.01对.05，分配单项power=1−.1/J，exact逐n搜索。完整78声明的90%功效仍未建立，因3个Qualified真值端点不可检验。即使假设所有阳性可实现，negative需3197/同质格、positive需633/格，合计至少30672新run；理想4-worker 7.95h、已采用串行31.81h、仅raw约41.49GiB。只做state63仍需28965run、理想7.51h/39.18GiB。不是沿用Task7 J765的成本，也不是零失败最有利n冒充power。

缺失状态支持：[{"layer": "cohort", "density": "low", "reason": "no a1b1 positive under either bounded source design"}, {"layer": "cohort", "density": "medium", "reason": "no a1b1 positive under either bounded source design"}, {"layer": "macro", "density": "low", "reason": "no a1b1 positive under either bounded source design"}]。源归属truth不足、现有候选边界/局部性能、资源和必要独立样本共同阻断；不能由增加seed假定阳性产率1。当前剩余资源详见decision JSON，已完成工作仍计在2h/10GiB总预算内。

| η情景 | 及时检出目标 | 证书Positive n/格 | Negative n/格 | 理想运行下界 | 4-worker理想h/串行h | raw GiB | CDF Hoeffding n/格 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.01 | 0.9975 | 15571 | 15571 | 186852 | 48.4/193.8 | 252.8 | 154374 |
| 0.05 | 0.9875 | 3106 | 3885 | 44283 | 11.5/45.9 | 59.9 | 6175 |

η仅情景，miss/Unknown各η/4，正式αmeasure未冻结，另以.005/J规划，绝不等同βV=.05。CDF K45来自本次更窄的单源条件×3层×3密度×5时点，不是Task7五设计层的K225；仅描述有限状态proxy，非F0。finite_state_cdf_budget.csv按R2同质格分别列detected-early、Unknown和采样余量，n0的格保持Unknown。

完整式detected-early + Unknown + εsampling + mdelay + εtruth/clock/measurement <η。独立V的及时检出/FPR/FAR、真实任意最早物理onset/独立延迟界、Formal A/Qpre/F0、正式H*仍缺失，完整预算不可求值；两个η情景均Not established/Unknown。上述样本成本也建立在极有利假设上，不能代表已达到桥接。

成本复核留痕：首次η=1%估算仅给对照格分配FPR所需n，未同时覆盖更严格Unknown端点；最终表已取二者最大值15571/格，原估算与修订原因保留于initial_statistical_plan/和analysis_revision.json。无truth、detector输出或候选评价改动，不把首次估算伪称正确。

## 复现、验证及Context Consistency Check

268计划单位、267完成、1失败/未执行，804分层标签，2412离线参数评价。完整运行碰撞0、teleport0、target setters 0。目前新增输出0.369GiB；预算计时30.5分钟，硬上限2小时/10GiB。每单位raw/truth/audit、旧源输入、代码/配置、seed/split均有hash和Git baseline/dirty记录。

定向测试覆盖源onset陷阱、b1时间跨度、identity不拼接、seed分离和Unknown失败；复用Task7算子/精确二项定向测试，不跑无关全量pytest/compileall。独立复算核查全部新run/label hash、Task7原hash、中心指标和16份exact计划；文档strict-git、evidence exporter/verify及纯Git字节保真实际结果见[verification_record](../../../evidence/research/P2_TASK8_20261102/verification_record.json)。启动原失败与一次工程续跑完整保留，不伪称首次通过。

统一定义v0.4/27项不变；AI_CONTEXT/状态/索引/注册/参数证据账本按真实结果同步。旧账本E61–64在Task6/Task7重复，历史表不改，本任务用Task命名空间注明歧义且新增E66以后。无生产模块/正式配置、AGENTS、论文、locked holdout或上游DRIFT变动。Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS；Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock BLOCKED；StageI READY_ENGINEERING_ONLY；Stage1.1 NOT_AUTHORIZED。

本地输出code/outputs/calibration/p2_task8_20261102_v1/；[便携证据](../../../evidence/research/P2_TASK8_20261102/README.md)仅元数据/小表/运行摘要/原hash与必要源快照，无raw大表、日志、图片或密封键。最终Commit/Push以Git核对为准，不写循环自指SHA。
