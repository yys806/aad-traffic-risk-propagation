# Stage 0.5 第一轮离线审计与科学决策包（2026-10-28）

## Observation

本轮基线为 `HEAD=353e88a`，工作区任务前为干净状态。R0 是离线设计包，登记了 B10/B01/B11 候选、源/目标/cohort 与物理路径规则，未执行新仿真。R1 真实执行了 B10、B01、B11 各 1 次；B00 复用已接受 A03，未重新启动。四臂均完成 420 s/8400 原生步，独立回执和统一测量通过；本轮离线分析没有 SUMO/TraCI 启动。

R1 的正式结果是：B00/B10/B01/B11 源 P2 均 0、目标 P2 均 0；目标 D1 暴露分别为 9778.4、13667.8、9865.1、13553.6 veh-s。B10 五条 `main_2_0..4` 的 10→5→10 m/s 脉冲、B01 60 辆匝道车供给、B11 组合操纵均有回读证据。B10/B01/B11 的声明/插入/末态 pending 为 1150/955/195、1150/1009/141、1150/956/194；B00 为 1150/1005/145。

逐事件重算与 R1 事件数组完全一致：B10 7 段（窗口内 5），B01 1 段（窗口内 0），B11 19 段（窗口内 17），B00 0。窗口内 B10 的 5 段全部在 `main_1_0` 映射 lane 6 辅助/未映射车道；B11 的 16 段在同一辅助车道，另 1 段在 `main_1_1` lane 5、y=384.44 m，位于目标区 `[150,350)` 外。B01 的唯一段在 y=213.63 m，但 onset=114.8 s，早于评价窗。事件总数因此不能写成正式 P2 数。

源区 `S_UPSTREAM_MAIN` 四臂均有可靠跟驰暴露，但有效观测中没有 TTC<2 s 状态；B00/B10/B01/B11 的源区可靠暴露为 8457.4/10278.8/8350.1/10353.9 veh-s。缺失点仍为 1061/548/1194/542，故“有效状态无风险”不等于“未观测部分无风险”。没有源事件，事件特定物理到达时刻为未定义；缺失身份、断链、右删失均只能标记 uncertain/unobservable。只有在未来出现实际源事件并满足身份连续、≤0.11 s 连续、验证过的车道连接和 leader→follower 见证时，才可报告有限到达时刻。`main_0→main_1` 与 `onramp→main_1` 的道路级可达性已验证；`main_2→target` 的正向道路路径不成立，但这不证明上游影响不可达。

软件层面，R1 使用当前 D1/state-support 适配器，事件、窗口、身份和质量规则与封存正式测量一致。此结论是软件一致性；不等于 SUMO/真实交通科学等价性。历史 324 次微观、58 次状态支持、到达时序、边界瓶颈和初始化/重放诊断继续支持：行为参数耦合、初始化与状态支持限制仍存在；它们不能补出本轮缺失的源事件或物理路径。

## Interpretation

当前阻断由两部分组成：固定主线源区没有合格源事件，以及全量风险段空间上偏向辅助车道或目标区外/窗口外。B10/B11 的速度状态变化是可观察诊断，不能单独推出风险传播或因果效应。未观测风险、辅助车道交互是否为机制主因、以及事件特定影响时刻仍不可区分。

五层验收状态：基础运动学和工程执行有完整证据；跟驰交互与风险可观测性在固定源区没有形成合格源事件；正式 P2/D1 已按规则测量但科学支持不足；状态/样本支持仍受缺失、pending 和初始化限制。因此 Stage 0.5 Gate=`blocked`，Stage 0.6=`pending_scientific_tolerances_and_dynamic_calibration`，Stage I=`blocked_until_protocol_lock`；本轮没有生成 Protocol Lock。

## Proposal

候选方案及离线比较见 [candidate_comparison_matrix.json](/D:/shen/TJU/AAD/evidence/results/RES-STAGE-0.5-FIRST-ROUND-OFFLINE-DECISION-20261028/candidate_comparison_matrix.json)。辅助车道可继续排除并作机制诊断、作为不与主线混池的次级空间、或另行作为替代研究范围；现有数据只支持事件分类和拓扑比较，不能支持正式 P2 重算。源区候选为上游主线、下游主线和匝道；它们分别表现为无源事件、方向不匹配或辅助连接及高缺失。cohort 方面，`C_INPUT_ROUTE` 是唯一已跨臂实际应用且处理前可确定的规则；`C_PRE_PULSE_STATE` 会改变估计对象，精确时钟和规模仍未冻结。物理路径应优先采用时间化身份连续/车道连接/跟驰见证规则；道路可达性或确认/消息时刻不能替代影响见证。

## Awaiting Researcher Decision

1. 是否把辅助车道保留为独立次级机制候选空间。
2. 是否继续 `S_UPSTREAM_MAIN`，或批准下游/匝道候选作为另一个明确估计对象。
3. 是否冻结 `C_INPUT_ROUTE`，以及是否需要预先定义 `C_PRE_PULSE_STATE` 的时钟和区域。
4. 是否接受时间化 leader→follower 见证作为物理路径规则，并分别报告 onset 与 confirmation 时钟。
5. 是否设计一个新的、单独准入的诊断任务以产生可观测源事件；本轮不追加 SUMO。

## Blocked / Unresolved

没有可确认的事件特定物理到达时刻；没有源事件就无法比较传播时延。辅助车道事件与主线正式估计对象的关系尚未裁决。缺失/断链/右删失无法区分真实不可达。Stage 0.6 的 δ、h、B 等容差仍未批准，不能赋值或宣告通过。

## Reproducibility and evidence

机器证据包位于 [RES-STAGE-0.5-FIRST-ROUND-OFFLINE-DECISION-20261028](/D:/shen/TJU/AAD/evidence/results/RES-STAGE-0.5-FIRST-ROUND-OFFLINE-DECISION-20261028/)，含逐文件审计清单、候选矩阵、离线复算、运行记录、manifest 与 SHA256SUMS。输入证据的原始 manifest/SHA 未覆盖或改写。生成命令：`python code/scripts/build_stage_0_5_first_round_decision.py`。

## Verification status

Strict project-doc validation, portable evidence verification, the 13-case project-doc test module, and compileall passed. A broader offline regression attempt completed with 1,389 passed, 34 failed, and 4 skipped because this environment lacks optional pyarrow and 	raci; those failures are retained as environment limitations. No test started SUMO or opened TraCI in this task.

The file audit includes the requested R0/R1/audit evidence trees, linked admission and docs/audits records, listed Stage 0.5 reports, and the specified measurement/source modules and formal config.
