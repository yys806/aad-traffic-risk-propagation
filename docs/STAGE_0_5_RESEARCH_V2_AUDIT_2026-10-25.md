# Stage 0.5 现状审计与研究任务重构

日期：2026-10-25（Asia/Shanghai）。Task：`AAD-0.5-INTERACTION-RESEARCH-V2`。
基线：`741468822c734da4c60102eb37e1082680e11984`，本轮开始时远端main与本机一致、工作区干净。
本任务获准现状审计、预算基础设施、隔离软件验证和新计划；**未授权新SUMO轨迹、初始化变更、科学协议冻结或Gate变更**。

## 1. 当前结论与证据范围

Verified：旧三次额度属于`AAD-0.5-INTERACTION-DIAGNOSTICS-V1`，来自历史FINAL-CLOSURE余额的显式重分配。`docs/audits/stage_0_5_interaction_preflight_v1/execution_ledger.json`记录预检时点0/3；真实执行记录见`evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/execution_ledger.json`及本机同名账本：一次`ID1_SUPPLY_0750/failed_stop`，ID2和ID3未执行。预检快照不是实时计数，不能覆盖实际失败。

**Agreed（本轮新授权）**：新研究任务无累计运行次数上限；逐次运行仍需明确研究问题、精确计划确认和工程准入。旧账本3次上限、一次失败、余2的历史含义保持原字节；该余额不再限制V2任务，也不导入V2当作新尝试。

机器审计：`evidence/results/RES-STAGE-0.5-INTERACTION-RESEARCH-V2/audit.json`。重建入口`code/scripts/audit_stage_0_5_research_v2.py::audit`；只读指定便携聚合、C6源码和已绑定的两份原始prepared routes，不打开真实原始轨迹、第三窗FCD或locked holdout。不把历史报告的Interpretation自动升格为本轮结论。

## 2. 已做实验、适用范围和去重

|历史任务|机器证据复核|可复用的事实|不得直接复用的主张|
|---|---|---|---|
|METHOD-EXPANSION|`response_metrics.csv`324行、324个唯一窗口/车辆对/配置/seed键；12对×9配置×3seed；`response_summary.json`无失败|单车对响应、参数方向、局部/长期差异；seed20261101–03|“抬tau必然有害”不能推广到真实总体；该推广已被CONDITIONAL_STATE_SUPPORT §1更正|
|同任务初始化与原型|`init_summary.json`另外24次微型SUMO运行；Newell另外24次非SUMO原型|局部跟驰初始化路线的控制证据|不能推出117/131辆全网初始化保真已经解决，也不能把这些数量并入324|
|STATE-SUPPORT|30 grid +20 seed重复 +4结构 +4历史第三窗=58次；前54次returncode均0；第三窗仅核对已发布聚合中的4项记录|限速供给与车道缩减的平均状态/速度离散差异；运行规模|58不是58个独立seed；grid与seed批有4个相同cell/seed键，输入字节等价未在本轮宣称|
|ARRIVAL-TIMING|`run_results.json`20项、20个窗口/臂/seed唯一键、returncode均0；2窗×U/E×5seed|声明/实现到达结构区别，入口排队受限；匝道时序变化不足以全面恢复交互|不把该设计重命名为新机制，也不把不同窗口当seed重复|
|政策A交互诊断|一次180s失败，FCD至179.9；2/18完整D1共同单元|失败与输入可施加性问题|部分P2=0/E=1933不能当完整270s基线|
|DS10MAX-V1|仅0750两候选XML准备，0次新轨迹，三个授权标志false|38辆精确属性范围及静态合法性|插入成功、时刻/速度保真、所有初始化异常消除均Unknown|

历史“车道缩减P2接近真实”和“限速P2低12–25倍”属于当时测量接口的Observation。C6后仅两份B_het/vlim10/seed20261201历史FCD获得新离线测量；其他grid、结构和时序风险值未整体重算，不能继续作为当前物理风险主张。状态速度离散可作旧窗口下的描述；平均状态匹配也不证明微观交互相容。

去重准则：新问题必须说明相对于上述任务新增了哪个可辨识对比或修复了哪个有效性缺陷。优先复用FCD做当前接口的独立离线测量，再决定是否需要新轨迹。现阶段不重跑跟驰模型目录、限速网格、车道缩减网格或U/E到达实验。

## 3. C6实际实现与结果边界

当前源码：`stage_0_5_scene_reconstruction.py::parse_fcd`保留`native_position_m/native_lane_id`；`stage_0_5_state_support.py::fcd_to_state_frame`按同原生车道前保险杠位置差减前车长度计算物理gap；`measure_state_frame`将不可观测关系降级；`stage_0_5_d1_measurement.py::local_d1_measurement`在原生车道改变时断开边。映射`y_m`只承担区域归属/分块。

本轮审计比对`RES-STAGE-0.5-C6-C7-OFFLINE-V1/provenance.json`绑定的源码SHA，全部匹配；没有再次修改测量算法。风险核心`stage_0_5_sumo.py`的TTC阈值、持续时间和连续风险定义不改。

两份**旧FCD离线重测**，不是新仿真：0750局部N/E从7/10904.0变0/9754.8；0805从5/11633.0变0/10456.7，窗口均[120,390)。前车选择、物理gap和可评价支持同时改变，不能将事件消失解释成风险消失。跨路段/内部连接段关系仍不可评价；与真实前车观测支持完全等价尚未证明。

## 4. 初始化与输入问题

Verified：C7任务级A已由研究者选定并用于旧最终计划，elapsed[120,390)、供给[180,240)，允许显式披露初态残留；B的[180,390)始终只是候选。旧文档写“A/B待决”的段落是此前时点，不能覆盖后来的决定。**A是评价支持政策；DS10MAX是不同的出发速度政策，前者获批不批准后者。** V2沿用A仍是待确认的计划建议，不宣称稳态。

0750：117辆初态中38辆固定10，且恰好全部从main_2出发；其余79辆位于main_0/main_1。DS10MAX只改这38辆，历史已成功首现的36辆也会受影响。i0063/64历史未见于FCD；180s报错指向i0063，但FCD缺失本身不能补成pending。

0805：131辆中44辆固定10，main_2初态实际52辆；**另外8辆的固定速度7.71–9.92也高于5m/s脉冲上限**。这是静态潜在相容问题，不证明它们在180s仍待插入；本轮没有生成0805候选XML或扩大政策。

i0007的0750声明速度15.23与t0警告保留；旧summary discarded=1，身份归属不能仅靠汇总确定。原生日志中的成功退出也不等于全部初态成功实现。所有新增完整对照前须明确该问题如何处理和验收。

## 5. 冲突与尚未实现的契约

|编号|Documented Intent|Actual Implementation|Evidence / Affected Files|Conflict / Status|
|---|---|---|---|---|
|INIT-SCOPE|修复初态固定10输入|0750仅38/117；0805仅44/131且还有8辆main_2数值>5|DS候选影响报告、绑定routes、本轮`audit.json/local_input_scope`|不能用“全部初态”替换语义；Awaiting Researcher Decision|
|INIT-OBS|逐车记录depart/pending并验收|worker只把ID列表取len，config仅FCD/summary|`interaction_diagnostic_worker.py::execute`；新计划及未来执行适配器|身份级状态不能从数量倒推；Awaiting Researcher Decision；未改旧worker|
|OLD-RISK|历史P2可描述交互缺口|只有两份FCD经C6重测，资格和事件均变化|C6 comparison/independent_verification、历史三类报告|旧风险比较不能作为当前验收；先离线复核，Awaiting Researcher Decision|
|ISOLATION|测试和实验仅访问批准资源|POLICY-A-VALIDATION-SCOPE-01有13项范围外本地数据测试，缺完整追踪|`docs/STAGE_0_5_POLICY_A_VALIDATION.md`及`validation_scope_incident.json`|历史偏差Not Accepted；新完整批次须独立准入，Awaiting Researcher Decision|

这些项目未通过改算法或改历史报告“解决”。旧报告/旧批准字节保留，新入口注明时序。V2方案为Proposed；科学结论、初始化选择和容差仍归研究者。

## 6. 执行链和预算硬编码审计

`run_stage_0_5_policy_a_confirmed.py::launch → supervise_stage_0_5_diagnostic.py::run_authorized_attempt → reserve_attempt → interaction_task_boundary.worker_bootstrap → interaction_diagnostic_worker.execute`。

旧`reserve_attempt`有len(attempts)>=3、同ID拒绝、任何前次非verified拒绝；`run_authorized_attempt`另有len>=3、按数组下标固定顺序和累计wall+600>3600。旧配置/提案/账本也记录3次。`prepare_stage_0_5_depart_speed_candidate.py`仅prepare/verify，没有预算适配器。直接改旧上限或将failed改verified均不合适，会破坏精确绑定和历史语义。

最小工程方案已实现为独立`stage_0_5_research_ledger.py::ResearchLedger`，新配置及hash链JSONL账本。无累计attempt/wall上限；运行准入与状态事件可追加，失败须明确复核，重复配置须说明理由，新ID保留每次尝试。**这是预算/准入基础设施，不是已完成的SUMO执行适配器。** 旧runner只适用旧任务，不能调用它来启动V2。未来执行适配器、身份记录、原生输入隔离证明必须先补齐并重新绑定精确提案。

## 7. 隔离整改与本轮验证边界

历史事故无法由新测试逆转，Not Accepted保留。旧“允许有限继续”不满足本轮要求的完整新批次隔离准入。新批次至少需要：实验仅含逐项SHA批准的输入副本；XML引用及工具依赖清单；测试在无dataset/历史outputs的Git克隆；父/worker子进程白名单；禁用未绑定字节码；实验/分析/测试各自白名单与访问证据；对原生SUMO文件访问的可证明约束，或报告尚不可证明并保持阻断。

本轮`validate_stage_0_5_research_v2.py`拒绝主工作区、包含数据/正式输出的目录，拒绝越界文件访问和SUMO/netconvert启动，明确排除7项轨迹集成测试。该Python父进程审计不是OS/native全监控，不能据此签发完整仿真实验隔离Accepted。新机器提案仍`execution_allowed=false`、`researcher_confirmed=false`、`protocol_frozen=false`。

验证的精确命令、结果、失败/修复过程见`docs/STAGE_0_5_RESEARCH_V2_VALIDATION.md`。本轮新增SUMO轨迹0；新研究实际尝试0；Gate仍pending_simulation_sample，δ/h/B及Stage1.1不变。相对运动、波结构和P2同时相容的问题仍未解决；已解决的是事实入口、历史预算的适用边界和新追加账本的工程实现。
