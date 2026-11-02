# P2 Task7 — 参数确定实验最终报告

Task ID：AAD-P2-TASK7-PARAMETER-DETERMINATION-EXPERIMENT-20261102。日期：2026-11-02。
状态：EXPLORATION_COMPLETE_WITH_LIMITATIONS / INDEPENDENT_V_NOT_EXECUTED。参数认证与严格桥接 **Not established / Unknown**。

## 1. 实际完成与核心判断

连续执行了历史资产核查、独立truth、冻结manifest、三密度576计划单位、参数逐项/关键交互/压力分析、精确验证功效与η双情景计算。575次SUMO完成，1次TraCI连接启动失败保留，未更换seed或补跑。主参数47,808次、参考压力29,952次、所选配置压力24,192次、条件单因素39,168次，均是同576依赖单位上的离线重算，不增加独立n。

三个层的有限状态校准中心恰好相同：W=9 s、constant baseline、θ=1 m/s、h=1 s、q=.05 s；Cohort c=1/固定N界；Macro w=2 s且固定lane0域。它们是 **Calibration candidate**，不是Recommended-for-freeze、Agreed数值或已验证稳定区域。各层输出分别报告，未构造OR/AND检测器。

微观源归属/W8、独立V、最弱信号边界和科学稳定等效margin仍不足。目标A没有获得独立验证的参数推荐；目标B两个η情景均无法建立。任务未产生Formal A、独立Qualified source→cohort、F0或AAD假设证据。

## 2. 历史资产、版本和执行范围

Task6协议AAD-P2-PARAM-20261102-v1.0、统一定义v0.4的27项ID保留。Task3 V2 768面板/42候选/32,256评价、B60/2,520评价只审计；Task9/18/19的Primary60+Supplementary40是同100轨迹，未重跑或计入V。白名单/hash见本次history_asset_audit。未读取locked holdout、OB或上游DRIFT，没有论文/正式config/production模块修改。

独立双lane 6 km直路，lane0为R=[1600,3080] m、固定s14–s17 cohort；lane1为断开跟驰链对照。Krauss、速度上限10 m/s、sigma=.25、tau=.6 s，原始步长.05 s、显式ballistic；仅s0/decoy可被控制，全部目标车辆native，动态target setter=0，碰撞/teleport=0（完整575运行）。Low/Medium/High为不同初始platoon packing，不是持续输入交通总体；实际pre Edie k约16.216/27.027/43.243 veh/km/lane，实际表见actual_density.csv。没有换道、合流或现实迁移资格。

主机16逻辑CPU、约27.7 GiB物理内存；启动可用约10.5 GiB内存、196 GiB磁盘，使用4 workers。原始npz约0.734 GiB，成功单位平均3.864 s。版本、二进制SHA、解释器和dirty来源见provenance；运行Git SHA是基线+明确dirty脚本hash，不能冒称当时工作树完全已提交。

## 3. 真值、设计点和失败

独立truth由完整高频原始状态、固定10 m/s参考、a*=1 m/s、b*=1 s和Macro oracle .1 s域构造；10 m/s是有限模型状态参考，不是无源反事实。a*/b*是有限测试坐标Proposal，**不是由精度证明的最小可传播物理信号**。不使用detector θ/h、拟合baseline或change point生成标签。实际source onset由命令后物理速度/native读回区间确定，不能用计划30 s替代。

先生成全部标签并封存1728条layer-label及原始hash，再运行detector。末端确认工程修复在detector前完成：初版把确认/恢复截在46 s，v2按既定随访延至50 s；原575份v1标签完整保留，48条cohort恢复区间扩展、主状态/起点未改，另补3条失败Unknown记录。没有参数结果驱动的truth修改。

| 层 | Low +/−/? | Medium +/−/? | High +/−/? |
| --- | --- | --- | --- |
| cohort | 0/192/0 | 0/192/0 | 119/72/1 |
| macro | 0/192/0 | 0/192/0 | 48/143/1 |
| micro | 0/192/0 | 48/144/0 | 119/72/1 |

各格分母是192计划单位；阳性包括A0真实状态变化，不能把A0正确状态报警记作FPR。C-N=144、C-P=360（359完成+1失败）、C-A=72。原始N0/N1均为有限状态阴性；不能从中推出任意微小物理变化不存在。

源命令四格为速度下降4/8 m/s、保持4/8 s，另局部2 m/s×1 s；命令不等于目标a*/b*。planned_signal_realization.csv独立核查实际目标强度/持续：Low全部四点未形成指定目标；Medium仅Micro P22达到其目标；High Cohort/Micro四点达到各自最低信号，Macro四点均未达到相应目标等级（P22有a=1有限Macro阳性，但未达计划2a=2）。局部非cohort设计点未形成预列有限阳性。没有扩大源剂量、移动region、降低truth或替换seed。弱于观测支持的范围、边界性能和未实现格均不能认证。

唯一失败C_high_P12_15：FatalTraCIError: Could not connect in 61 tries；0帧、0命令执行，保留空轨迹和audit并作为三个层的Unknown。没有仿真响应失败伪装成阴性。发现后执行器停止，不启动额外单位；已在并发队列内的其余单位已完成。确认归属本任务的孤立SUMO进程已终止，记录保留。

## 4. 三层参数和描述性性能

| 层/对象 | 状态阳性及时检出(C) | 真阴性 FP(C) | state Unknown | 有效检出delay中位上端 |
| --- | --- | --- | --- | --- |
| cohort | 119/119 | 0/456 | 1/576 | 1.05 s |
| macro | 48/48 | 0/527 | 1/576 | 2.10 s |
| micro (native finite state) | 167/167 | 0/408 | 1/576 | 1.05 s |

上表是校准集状态检测点估计，**不是独立V性能，也不是跨密度/条件iid合并CI**。每个同质N0/N1密度格仅n=24，0 FP的单侧95%精确上界为0.117346，远高于1%。Unknown按全部576 attempts计1/576；若Unknown视作额外未检出阳性，所选候选总体及时率最坏分别为Cohort119/120、Macro48/49、Micro167/168，但这仍是异质校准描述，不能套一个总体CP界。每格保守分母/CI见selected_cell_metrics.csv。

Micro的167是any-source native有限速度状态阳性，**不是167个Qualified Witness**。指定源候选链Potential=359、Observed=47、Qualified=0，360单位的指定源资格Unknown；逐跳W1–W9、原始ID/leader、strict W6和竞争解释见micro_witness_levels.csv。W8未被独立证明，不能让拓扑和响应相似性填补。Micro source-claim为全程弃权；0/216已知非指定源机会错误归属不代表有归属灵敏度，Macro/Cohort any-source FAR为N/A。

延迟是相对独立a=1,b=1状态onset区间的available delay；另存first-positive、confirmation、availability和恢复。它不覆盖更早、低于a*或短于b*的真实物理影响。Macro窗口不能通过减w校正成最早物理onset。

## 5. 单因素、交互、稳定性与鲁棒性

按Task6 pre支持生成W=4.5/9/13.5 s，constant/linear；阈值来自独立cal-null最大残差分位及a*/4,a*/2,a*；h=1/2/4 s；q清洁网格退化为.05 s；c=.6/.8/.9/.95/1；recovery0/2 s、hysteresis off/数值floor、Macro w=1/2/4、Δt=.05/.1/.2、Δx=L/4,L/2,L。1e-6仅数值比较floor，不冒称物理传感误差证书。

原25 Cohort/36 Macro/22 Micro候选共47,808评价；所选中心周围追加条件单因素39,168评价，不改变冻结候选或重新选择。pre_baseline_predictions为完全源前块外预测。阈值更低时会早于有限truth状态报警，这不等于“没有物理影响”；在本次事件匹配中单列early/invalid，不能改物理onset追求更高recall。

11类依赖全部有明确产物/限制：W×model、θ×h、h×q、recovery×hysteresis、w×θ、Δx×Δt在interaction_summary（336分层对比）；coverage×missing在coverage_missing_interaction与压力表；density×threshold单独分层、不伪成paired；reaction-window×clock在reaction_window_clock_summary（固定rep0/23代表单位，边不是独立n）；identity×missing在robustness表；H*×η×α×n在精确规划/CDF预算。q退化、reaction真值和完整identity机制不足时结论Unknown，而不是交互为零。

同run交互差分用[-2,2] Hoeffding同时界，n=24/格，区间宽；科学ε_stab和γ_int未冻结，不能用“不显著”认定稳定。144次独立代码路径的Edie裁切/分区crosscheck通过（同一raw不算144个独立实验），q=ku只为恒等式；V=0速度undefined。

压力层包括0/5%/20% MCAR、块/MNAR，原始采样/2倍/4倍，数值floor及.05/.1 m/s噪声、.1/.2 m/s量化、ID断裂。分别保存reference与所选向量，不用剩余车辆均值冒充full-N；降采样但q不变会失去持续证据，缺失/ID会增加Unknown。缺失gate不能修复MNAR，稳定范围尚未建立。

## 6. 独立验证和统计预算

V未执行、V seed消耗0；没有把C或历史V2/B60改名独立V。实际计划族J_V=765，其中459项性能声明、306项稳定性对比，完整清单保留候选和邻域。β_V=.05用于保守同时置信控制；按1−.1/765分配各可检验二项端点的规划功效，以控制该部分联合type-II错误。稳定性margin及Qualified truth仍Unknown，因此完整765项验证族的90%功效**未建立**。所有同轨迹参数/层/mask共享run block，不按车/帧/边计n。

规划good FPR/FAR=.002对.01、good miss/Unknown=.01对.05，均为假设备选，不是已观测真率。精确逐n搜索得到每同质negative格n=4591、positive格n=881。即使所有预列目标均能实现，至少54534运行、14.63 h、69.49 GiB原始数据；还没包括无法实现格、真实稳定margin和失效率额外成本。超过预定V预算2 h/10 GiB，且若阳性支持本身为0，不能仅靠样本量补足。因此不启动无充分支持的V。

零失败最有利n与90%验收功效n分别保存；16组规划经独立lgamma二项CDF复算。首次CDF规划只数45目标格，现已保留初版并修正为225=3层×3密度×5时点×5固定源设计层；实际C-CDF原本即使用225。未将异质固定格池化为iid。此修正发生在任何V之前，阈值和科学标准未改。

## 7. η双情景严格桥接

| η情景 | miss/Unknown各上限 | 及时检出目标 | 证书positive n/同质格 | 乐观运行下界 | 预计墙钟/原始数据 | CDF Hoeffding n/格 |
| --- | --- | --- | --- | --- | --- | --- |
| 0.01 | 0.0025 | 0.9975 | 21199 | 365586 | 98.1 h / 465.8 GiB | 186563 |
| 0.05 | 0.0125 | 0.9875 | 4229 | 111036 | 29.8 h / 141.5 GiB | 7463 |

上述certificate成本按α_measure=.005情景计算，β_V=.05不能替代。每个情景独立V Positive=0、Negative=0；及时检出、miss、Unknown、FPR、FAR的独立证书均Unknown。CDF极有利成本还假设早到质量0、为Unknown和delay各分η/4，K=225、α_P=.02；固定格exact CDF power规划另存，η1%需8238/格、η5%需1639/格。这些不是Formal F0样本量或正式已接受α分配。

calibration_cdf_budget按每格n=24并保留固定权重，列出detected-early、Unknown、ε_sampling、finite-state possible mass和partial floor；它不是F0。完整条件必须是detected-early + Unknown + ε_sampling + m_delay + 适用truth/clock/measurement误差 < η。当前m_delay独立界、任意微小物理onset界、Formal A/Qpre同资格无消息总体及正式H*均缺失，完整式不能求出有效通过结果，不能把缺项补0。

三类判断明确区分：有限域仅有校准状态性能与算子工程支持，未有独立V；严格桥接的统计规划成本可计算；两个η情景的真实物理桥接均Unknown/Not established。η=.01/.05只是损失情景，不冻结正式η，也不证明现实交通或AAD核心假设。

## 8. 科研冲突、限制和待研究者接受范围

Documented Intent：Task6四个target a*/b*最低信号点及局部非cohort点。Actual Implementation：固定原生SUMO源剂量，不直接控制目标；实际region信号部分达不到目标格。Evidence：manifest、planned_signal_realization、原始SHA。Affected Files：本次协议/参数结果/manifest，未改旧Task6和正式配置。Conflict：计划target信号不等实际source命令，部分实验格未实现。Status: Awaiting Researcher Decision（仅未来如何调整未实现格；本任务停止扩展，不擅改主对象/真值/区域）。

当前不推荐正式冻结任何数值。可供研究者审阅的只有模型域、独立标签规则和C候选；如未来需要改变source剂量/区域/机制或科学稳定margin，先由研究者决定。本任务不再自动启动后续实验。

## 9. 工程复现、验证与Context Consistency Check

本次代码只在code/scripts和定向tests；未改code/src、正式configs、AGENTS、Overleaf、历史轨迹/结果。数据链raw→独立truth v2/hash→候选manifest→离线评价→统计规划→报告/证据。原准备v1、truth v1、CDF规划v1及唯一失败完整保留，不伪装首次通过。早期读取UTF-8/命令转义失败均未触发科研运行。

核心复算：python code/scripts/verify_p2_task7_results.py --output-dir code/outputs/calibration/p2_task7_20261102_v2。它独立检查全部raw/truth/audit hash、1728 label hash、失败分母、所选指标、16 exact计划和保护路径。定向pytest、文档strict-git与evidence导出/verify的实际结果记录在evidence verification_record.json；不默认跑全量pytest/compileall。

AI_CONTEXT、定义账本/参数入口、研究状态/索引/注册同步实际新事实；不把Proposal升级Agreed。Stage0.5=CLOSED_WITH_LIMITATIONS；Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock=BLOCKED；StageI=READY_ENGINEERING_ONLY；Stage1.1=NOT_AUTHORIZED。Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown。

本地输出：code/outputs/calibration/p2_task7_20261102_v2/；便携证据：[P2_TASK7_20261102](../../../evidence/research/P2_TASK7_20261102/README.md)。大型raw、图像和日志不进入便携证据。执行基线SHA/dirty/code hashes在provenance；最终commit/push以交付时Git和远端HEAD为准，不写自指SHA。
