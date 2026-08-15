# Review Findings

## Decisive Experiment Redesign Intake (2026-08-07)
- Real SUMO preflight showed that the original -5.5 m/s2, 1.0 s target pulse was identifiable as an action but not as an outcome: minimum receiver TTC was about 3.26 s and integrated TTC burden was zero.
- A pre-formal calibration with -8.0 m/s2 for 1.4 s yielded positive target risk without collision. Across six excluded calibration seeds, R00=R01=R10 within each seed, R11 was lower in all six, and event trigger/pair invariants held exactly.
- The six-seed calibration mean delta_NL was -0.1268517 and the deterministic paired bootstrap 95% interval was [-0.1290739, -0.1245433]. These are calibration evidence only and are not counted as formal confirmation.
- The frozen equivalence margin is 10% of median calibration R10 burden: epsilon=0.0223763382. Formal support still requires the pre-registered 20-seed interval, sign, collision, topology, and mechanism gates.
- 上轮失败不是通信链失效，而是源事件在接收车风险很低时触发，导致主要结局在10秒窗内缺少可辨识变化；继续扩种会精确估计一个近零效应。
- 决定性实验必须把“源风险事件”和“目标区自身的可干预风险状态”同时纳入触发条件，同时保持目标风险不是由源事件的物理波先制造出来。
- 当前合流路网能排除直接leader/follower，但不能证明物理不可达；严格核验需要新增物理不连通而信息可达的对照拓扑，或使用可审计的双路网/双支路结构。
- 用户已授权严格完成决定性实验，但按brainstorming硬门槛，须先呈现并确认实验设计，之后才能修改代码和运行正式仿真。
- 当前实验构建器复用Flow官方`MergeNetwork`；项目内没有现成的物理不连通双支路路网，严格隔离需要新增专用network/builder，而不是继续修改现有merge坐标。
- `RiskEventCoordinator`仍把源边固定为`inflow_merge`、目标边固定为`bottom/left/:center_1`，目标TTC只支持上界；决定性设计需要把“目标风险可干预”与“源消息有效”拆成明确触发条件。
- 实验worktree保留上轮未提交修改和新增文件；后续只能在该worktree中做最小增量，不能清理或覆盖既有Pilot A/B与真实风险实验。
- Flow官方`MergeNetwork`的匝道路径为`inflow_merge→bottom→center`，主线为`inflow_highway→left→center`；两支路在`center`必然物理汇合，因此现有路网只能证明消息先行或观察期内未到达，不能提供结构性的物理不可达。
- 当前builder深拷贝官方merge配置并替换车辆/流量，新增决定性路网可以沿用这一构建模式，但必须注册为独立scenario，避免污染已有merge基线。
- 官方路网接口由`Network`子类的nodes/edges/types/routes/edge_starts构成，技术上可新增“两条平行且不连接的源/目标走廊”，由信息通道跨走廊连接；这比在现有merge上依赖时间窗更能满足强拓扑隔离。
- 用户于2026-08-07明确接受新增物理完全不连通、仅信息可达的双走廊SUMO路网；决定性设计可以把该路网作为因果识别基准，并保留原合流路网作为现实性迁移验证。
- 双走廊正式实验完成80次有效运行（20个固定配对种子×4单元）。`Delta_NL`均值=-0.1312075，配对bootstrap 95% CI=[-0.1320726,-0.1303981]，固定符号置换p=9.999e-05，20/20种子为负且无碰撞。
- 正式支持门槛全部通过：事件时序不变、采用前目标轨迹一致、控制单元零采用、拓扑审计80/80为零跨走廊路径。结果支持“显式远端消息介导的仿真内类超距风险效应”，不支持物理超光速解释。
- 独立通信核验完成36次：错误来源、错误时间和delivery-only均为零采用；中等/严重受损通信分别采用12/2个步，门控逻辑符合预期。
- 合流迁移预检的初始分析暴露两个实现问题：merge默认`sims_per_step=5`使机制步与state行号错位；受控ID列表还可能短暂包含已离开车辆。迁移runner现已冻结`sims_per_step=1`，快照同时校验活动ID，并将目标候选限制在合流前`left`边。
- 修正后的四格迁移预检完成于`outputs/decisive_merge_preflight_v7`：事件时序和目标车辆在四格中一致，r11于第96步采用消息，无碰撞，采用前目标轨迹一致。但四格`I_TTC`均为0、最小TTC为2.92--3.15 s，`Delta_NL=0`，因此按预注册规则停止10种子扩展；该场景不支持可测迁移效应。
- 受控合流再校准严格只读取`r00/r10`：8步和9步均为0/6正风险，10步两格均6/6出现正`I_TTC`，中位最小TTC为1.9404/1.9400 s，无碰撞且事件/制动前轨迹一致；因此首个通过候选10步被哈希锁定，`epsilon_merge=0.0010993341`。
- 锁定合流正式实验完成20配对种子×4格共80次。均值`Delta_NL=-0.0069459`，bootstrap 95% CI `[-0.0095418,-0.0042398]`，置换`p=0.00049995`，但只有12/20为负，未达到预注册16/20；逐种子采用、采用前一致和采用先于分化门槛也因8个无有效来源事件的种子而失败，正式结论为不支持合流迁移。
- 8个无采用种子均未满足连续3步实际减速度不高于-4.5 m/s²：6个来源车静止、1个几乎静止、1个在离开来源边前仅实现2步制动；其效应均为0。其余12个种子全部形成有效来源消息并采用，且12/12效应为负，但该条件子集只能作机制诊断，不能替代预注册主检验。


## Real-risk Implementation Findings (2026-08-06)
- Flow 的 `BaseEnv` 会在每步调用受控车辆的加速度控制器，因此真实制动脉冲应在 `OursFullController.get_accel` 的返回值层实现，避免被随后控制动作覆盖。
- Flow vehicle kernel 已提供 `get_controlled_ids`、`get_edge`、`get_2d_position`、`get_leader`、`get_follower` 和 `get_realized_accel`，无需猜测或创造仿真接口。
- 现有 Pilot B 的 `DeterministicEtaChannel` 已验证时延、丢包、更新和缓存生命周期；真实风险消息应独立实现并保持相同审计语义，不能复用 ETA 值冒充风险。
- 既有 emission 表包含 `realized_accel`、leader/follower、edge、position 和 relative speed，可用于事后核验制动有效性、直接物理邻接和目标区 TTC。
- 合流仿真步长从既有轨迹可见为 0.2 s；1 s 制动脉冲应按运行时 `sim_step` 换算为 5 步，而不是沿用控制器其他位置的 0.4 s 常数。
- 现有修正 Pilot B 配置 horizon 为 120 步；真实风险事件需先预检触发率，必要时只延长实验时域，不改变需求或控制参数。
- Windows 隔离工作树缺少被 `.gitignore` 排除的三个正式 checkpoint；已从 WSL 正式副本复制同哈希的 `module_a/b/c.pt` 到隔离工作树，仅恢复运行依赖，不修改模型或配置。
- 共完成46次CPU仿真（2次预检、32次四格主实验、8次风险门控、4次独立核验），碰撞总数为0；本轮不需要GPU。
- 32次主实验的16个源事件均达到实际减速度阈值；R11的8个事件均发生消息采用，R10为0。四个渗透率×需求组合的10秒窗 `Delta_NL` 均为0，说明机制成立但结果窗没有形成可测风险差异。
- 风险门控的p60两种子平均 `R11-R10=-0.0004028569`，描述性95%区间为 `[-0.0013990223, 0.0005933085]`；p80为0。方向不足以支持稳定安全收益。
- 错误来源消息交付3次、错误时间消息交付2次，来源/时间核验均为0次通过，接收车0次采用且动作不变；delivery-only可用3次但0次采用；受损通道3次发送中丢2次，只在第361步交付并采用1次。
- 8个主实验配对中源车与接收车均非直接leader/follower；R10接收车轨迹在观察期内未相对R00分化。这是“未观察到物理到达”，不是“路网不存在物理路径”的证明。
- 当前证据支持真实风险消息的显式介导和来源特异动作效应，不支持“类超距信息已稳定改变目标风险”。同设计扩展种子不会修复目标风险不足，应先重构触发场景。

## Real-risk Communication Experiment Intake (2026-08-06)
- Approved design source: `D:\禹尧珅\人工智能知识库\同济科研\交通风险传播\8.5-8.11推进.md`, Section 3.
- The Windows upstream repository is `D:\shen\research\code`; the existing experiment worktree is `C:\Users\Lenovo\.config\superpowers\worktrees\code\nonlocal-pilot-a`; the executable WSL copy is `/home/shen/shen/mixed_autonomy_lab`.
- WSL has 16 CPU threads and about 12 GiB available memory. Flow source exists at `/home/shen/shen/paper_repos/flow`. No GPU is required for rule-based communication, SUMO rollout, TTC analysis, graph reconstruction, or paired statistics.
- Reusable audited settings are target edges `bottom/left/:center_1`, absolute x range 540--612 m, leader-aware TTC threshold 2 s, hard-brake threshold -4.5 m/s2, p60/p80, mainline 2000 veh/h, ramp 100/180 veh/h, and the existing deterministic ideal/impaired channel lifecycle.
- The earlier `source_high` manipulation is a demand context, not a real risk event. The new source factor must be an injected and realized braking/low-TTC event with source-specific message semantics.


## Local Propagation Baseline (2026-07-18)
- The local one-hop/multi-hop baseline uses 2,057 eligible non-boundary episodes after excluding `safe_speed_override_candidate` events.
- Default locality is `0 < delay <= 3 s` and distance `<= 50 m`, with same-vehicle, leader-to-follower, follower-to-leader, and same-region-local relations. Each target keeps at most one strongest local parent, so every run graph is a DAG with in-degree no larger than one.
- The default run produced 2,315 candidate local edges, 1,294 selected direct edges, 763 local chains, 214 multi-hop chains, and maximum depth 24.
- Direct relation composition is 725 leader-to-follower, 494 same-vehicle, 41 same-region-local, and 34 follower-to-leader edges. Cross-vehicle links are 800/1,294, or 61.8%.
- Method-level direct-edge totals are FS 933, DRIFT 196, and PI 165. FS also has much deeper chains: maximum depth 24 for FS, 4 for DRIFT, and 3 for PI.
- Scenario-level direct-edge totals are merge 726, ring 359, and figure-eight 209. Merge contributes the largest cross-vehicle structure and is the main scenario for later propagation claims.
- Target-event context is not mostly clean stable following: 43.0% adjacent-override-only, 38.9% stable-following, 12.9% transition-plus-adjacent-override, and 5.2% interaction-transition-only. Later causal analysis must keep these strata visible.
- Vehicle-wise circular time-shift null results show strong local timing alignment mainly in FS merge: 18/30 FS merge runs have empirical p <= 0.05. DRIFT merge has 5/30 and PI merge has 2/30. Figure-eight has no significant runs in any method; ring FS has 8/25.
- Sensitivity is stable enough for a baseline but not trivial. Tightening to 1 s / 50 m keeps 1,021 direct edges, 79% of the default. Expanding to 5 s / 50 m gives 1,325 edges, 102% of default. Increasing distance beyond 50 m changes edge counts little but can raise maximum depth from 24 to 28.
- Interpretation: local propagation is real and must be controlled first. The current evidence does not justify jumping straight to a nonlocal claim. A later nonlocal test should ask whether any remaining source-target association persists after same-vehicle, leader/follower, same-region, transition, adjacent-override, scenario, penetration, and method effects are conditioned out.
- Output package: `code/outputs/local_propagation_baseline_20260718`, including ten figures and CSV/JSON evidence tables. The work is CPU-only.

## Quantum Physics And Traffic Nonlocality (2026-07-18)
- Search boundary: physical Bell nonlocality and no-signaling; quantum causal models; quantum-like cognition and decision-making; traffic relevance.
- Bell (1964), Brunner et al. (2014), and Hensen et al. (2015) concern correlations from prepared, entangled, and measured quantum systems. They do not provide a physical mechanism for distant traffic-risk propagation.
- Bell nonlocality is not controllable superluminal information transmission. A distant statistical association between vehicles does not qualify, especially when communication, common causes, and ordinary propagation paths are present.
- Quantum causal models by Leifer and Spekkens (2013), Costa and Shrapnel (2016), Allen et al. (2017), and Giarmatzi and Costa (2018) take quantum states, channels, operations, or process matrices as inputs. They cannot be applied directly to the current classical trajectory data.
- Their transferable ideas are limited to distinguishing direct causes from common causes, defining causality through interventions, and checking omitted external memory.
- Quantum-probability work by Busemeyer et al. (2006), Pothos and Busemeyer (2009), and Wang et al. (2014) models contextuality, order effects, and interference-like behavior. It is a mathematical cognitive formalism, not a claim of quantum physics in the brain or traffic system.
- Two 2022 Scientific Reports papers by Song et al. apply quantum-like Bayesian or quantum game models to pedestrian and two-vehicle decisions. They are relevant behavioral-model candidates, but the scenarios and evidence do not establish nonlocal risk propagation.
- In the two-vehicle paper, neural-network test accuracy changes from 65% under trajectory-pair splitting to 97% under shuffled-frame splitting, showing that correlated windows and split design materially affect conclusions.
- Recommended terminology is mechanism-supported nonlocal risk effect or direct risk effect beyond the local neighborhood. Physical quantum literature should set conceptual boundaries; quantum-like cognition should remain an optional behavioral baseline after classical models fail under matched evaluation.
- Core candidate DOIs verified: 10.1103/PhysicsPhysiqueFizika.1.195; 10.1103/RevModPhys.86.419; 10.1038/nature15759; 10.1103/PhysRevA.88.052130; 10.1088/1367-2630/18/6/063032; 10.1103/PhysRevX.7.031021; 10.1038/s41534-018-0062-6; 10.1016/j.jmp.2006.01.003; 10.1098/rspb.2009.0121; 10.1073/pnas.1407756111; 10.1038/s41598-021-04239-y; 10.1038/s41598-022-14737-2.

## Event Taxonomy And Full Extraction (2026-07-16)
- The next evidence gate is event semantics, not nonlocal causal discovery.
- Braking rows must produce one physical braking label with a severity field; rows below the extreme cutoff must be isolated as `safe_speed_override_candidate` rather than ordinary braking.
- Full-dataset rates must use vehicle-time exposure. Raw frame counts are retained only for traceability.
- Sensitivity settings are TTC 1.0/1.5/2.0/3.0 s and braking -3.0/-4.5/-6.0 m/s^2.
- Manual review tables must retain source file, run, vehicle, leader, lane, time, speed, acceleration, TTC, THW, and adjacent-frame context where available.
- Final formal extraction covers 270 files: 90 DRIFT, 90 FS, and 90 PI; every scenario/method/penetration cell has five runs.
- The dataset contains 1,609,149 frame rows and 78.51 vehicle-hours of observed exposure.
- Non-overlapping extraction produced 6,933 frame detections and 4,131 episodes. Of these, 2,012 episodes are `safe_speed_override_candidate` and are excluded from ordinary braking.
- After removing override candidates, 2,119 ordinary surrogate-risk episodes remain; 62 lie on vehicle entry/exit boundaries, leaving 2,057 episodes eligible for the local baseline.
- Context flags identify 565 interaction-transition episodes and 1,049 episodes adjacent to an override candidate; these must be reported as sensitivity strata.
- The stratified 60-episode review retained 12 stable episodes, retained 38 with context flags, and excluded 10 override candidates.
- DRIFT's ordinary-braking advantage over FS is stable across -3/-4.5/-6 m/s^2 thresholds (12 wins, 2 ties, 4 losses at every threshold). TTC comparisons are mixed and threshold-dependent, especially versus PI.
- Raw FS/PI emissions are available and included. IDM, Flow-AIL, and Flow-RL have local aggregate results but no local frame-level emissions, so no event-level values were invented.
- The input gate is now `READY_FOR_LOCAL_BASELINE_WITH_EXCLUSIONS`; nonlocal causal discovery remains out of scope until the local baseline is built and checked.

## DRIFT Qualification Audit (2026-07-16)
- The authoritative upstream DRIFT repository is available at `D:\shen\research\code`.
- The cleaned formal package covers ring, figure8, and merge at p0/p20/p40/p60/p80/p100 with five runs per cell; Flow-RL is applicable at p20-p100.
- Existing evidence supports a trade-off claim, not universal dominance: DRIFT is strong on ring efficiency, competitive on figure-eight and merge efficiency, and often improves hard-braking tails.
- The OOD suite does not support overall DRIFT dominance: Flow-AIL has higher return/speed and IDM has lower TTC violations, while DRIFT has the best hard-braking rank and least severe worst acceleration among the three.
- The current downstream pilot has invalid metadata and risk semantics: all lanes are unknown; several no-leader rows have finite TTC near one second; extreme accelerations and long low-TTC episodes require raw-emission verification.
- The downstream pilot therefore cannot currently serve as evidence for DRIFT quality or causal risk propagation.
- Statistical/result auditing is CPU-only. GPU is unnecessary unless the learned DRIFT/Flow-AIL/Flow-RL models must be retrained.
- The final formal coverage audit passed all 54 requested FS/PI/DRIFT cells (3 scenarios x 6 penetrations x 3 methods), with five runs per cell.
- Mean-level comparison produced 380 like-for-like metric comparisons: DRIFT was better in 203, tied in 81, and had a 67.9% win rate after excluding ties.
- The conservative 95% CI audit produced 291 comparisons: 126 confidently better, 25 confidently worse, and 140 overlapping.
- Candidate-fit evidence passed: learned K=5 error 0.094 versus fixed K=5 error 0.595 and single-candidate error 1.228.
- OOD evidence remains mixed: DRIFT has the best HB10 and least severe worst acceleration among Flow-AIL/IDM/DRIFT, but lower return/speed and worse TTC violation rate.
- Located 90 final DRIFT raw emission files in WSL: 30 each for ring, figure8, and merge, totaling 542,644 rows. Required fields and lane metadata are complete.
- Raw safety audit: ring has no TTC/THW violations or extreme deceleration; figure8 has 0.78% TTC violations, 0.64% THW violations, and 40 rows below -15 m/s^2; merge has 0.17%, 0.10%, and 65 rows respectively.
- Fixed the downstream adapter so TTC requires a valid leader and Flow lanes use `edge_id:lane_number`. The stale pilot's 302 false no-leader TTC detections and 100% unknown lanes are eliminated.
- Re-extracted five final DRIFT merge-p20 runs: 258 labeled detections, 191 unique physical rows, and 98 episodes. No finite TTC occurs without a leader, lane metadata is complete, and no low-TTC episode exceeds 0.8 s.
- Fifteen unique merge-p20 frames remain below -15 m/s^2. All 15 match the adjacent-frame speed derivative and none is a terminal vehicle record, so they are real simulator speed jumps rather than a malformed acceleration column.
- DRIFT controller commands are limited near -3 m/s^2, while Flow/SUMO realized acceleration can be much lower under safe-speed overrides. Similar extreme tails occur in multiple baselines, so this is a shared benchmark/closed-loop execution issue rather than proof that DRIFT alone is defective.
- Final gate: DRIFT performance evidence passes; raw schema passes; causal risk-propagation use remains on hold until extreme safe-speed override candidates are separated from ordinary braking events.

## Initial Inventory
- Top-level directories: `code`, `docs`, `literature`, `paper`.
- Top-level documents: `README.md`, `毕业设计与论文课题固化.md`.
- The current folder is not a Git repository.

## Confirmed Facts
- The fixed topic is "Risk Propagation Graph Modeling and Counterfactual Intervention Analysis for Mixed-Autonomy Closed-Loop Traffic Simulation."
- DRIFT/Flow is intended as the closed-loop evolution and validation environment, not the object of further generative-model improvement.
- The planned method has four stages: event extraction, propagation-graph modeling, propagation metrics, and counterfactual re-simulation.
- The documented pilot result is one real Flow merge run at 20% AV penetration: 309 frame-level detections, 16 merged event segments, 37 candidate edges, and 18 filtered direct edges.
- The documented mean direct-edge delay is 1.467 s and mean direct-edge distance is 13.679 m.
- The real emission's lane field is currently invalid, so unverified long-distance same-lane edges were removed and no long-range propagation claim is supported.
- Multi-penetration, multi-seed experiments and fixed-seed counterfactual rollouts are not yet complete.
- Source/amplifier/absorber scores are documented as transparent proxy metrics, not causal conclusions.
- `code/README.md` defines the current package as an emission-CSV analysis pipeline producing detections, episodes, candidate/direct edges, node roles, chain proxies, and run summaries.
- The documented input adapter accepts several optional fields and fills conservative defaults when absent.
- Counterfactual experiment wrappers that call DRIFT rollout code are explicitly listed as a future extension.
- The real rollout was executed on a server-side Flow/SUMO environment; the local machine's Flow environment was not completed according to the feasibility report.
- The repository contains a synthetic Flow-like validation sample as well as one synchronized real Flow merge result.
- The Python package is a small Python 3.10+ project depending only on pandas, matplotlib, and networkx; pytest is the development dependency.
- `run_pipeline` processes one CSV at a time and writes seven tabular outputs.
- `risk_chains.csv` is currently produced by grouping direct edges by source event; the code explicitly labels it a lightweight proxy pending full graph traversal.
- Full propagation-depth traversal is therefore not implemented in the main pipeline.
- Event extraction currently implements six rule labels: hard/severe braking, low/critical TTC, low THW, and near miss. Unsafe merge, cut-in, congestion, and shockwave are absent.
- Threshold rules overlap, so one frame can intentionally produce multiple event labels (for example severe braking also satisfies hard braking).
- Episodes merge rows only within the same run, vehicle, and event type when adjacent detections are no more than 0.4 s apart.
- Candidate relations are limited to later events within 5 s and one of: same vehicle, leader/follower, same 50 m region, or known same-lane distance from 80 m to 120 m.
- Edge scores are heuristic products of time, distance, endpoint risk, and relation weights.
- Direct-edge selection keeps the top candidate per source event and relation type by default; it reduces graph density but does not establish causality.
- The propagation module includes a depth-limited intervention-candidate screening traversal, but this computes priority only and explicitly does not estimate intervention effects.
- Current run-level metrics include event/edge counts, selection rate, delay, distance, mean heuristic score, and long-range ratio; the full metric set described in the topic document is not yet implemented.
- The test suite covers core rule extraction, episode merging, edge construction/selection, unknown-lane filtering, role scores, intervention ranking, pipeline outputs, runner execution, and synthetic data generation.
- Tests are unit/smoke oriented; there is no test against raw real Flow emission adaptation or actual DRIFT/Flow rollout execution.
- `analyse_existing_run.py` rebuilds episode-level outputs from previously saved frame-level events, writes `risk_direct_edges.csv`, intervention candidates, figures, and a Chinese stage readout.
- The main pipeline and the real-result analysis script use slightly different output naming (`risk_edges.csv` versus `risk_direct_edges.csv`) and the latter adds artifacts not represented by `PipelineOutputs`.
- `docs/实验计划.md` is an earlier roadmap referencing an external project at `D:\shen\research\code\mixed_autonomy_lab`; it is not self-contained in this folder.
- The intended pilot success criteria require at least three penetration settings, four propagation metrics, and one counterfactual intervention; those criteria are not yet met.
- The real smoke configuration is only merge, 20% AV, one `fs` method, one run, and a horizon override of 25.
- The current artifacts roughly correspond to the roadmap's event/graph/visualization phase, before penetration comparison and counterfactual execution.
- The actual real-result summary exactly matches the README: 16 episodes, 37 candidates, 18 direct edges, 9 source-group chain proxies, 1.4667 s mean delay, 13.6789 m mean distance, and zero long-range ratio.
- The 16 real episodes comprise 5 low TTC, 5 critical TTC, 2 severe braking, 2 hard braking, and 2 low THW episodes; no near-miss episode appears in this run.
- The 18 direct edges comprise 9 leader/follower, 5 same-region, and 4 same-vehicle edges.
- Every real episode has lane=`unknown`.
- Top intervention candidates include `human_3` low TTC and two overlapping `flow_10.0` braking labels, illustrating that candidate ranks are event-label based and can place multiple labels from the same physical episode/vehicle near the top.
- `paper/latex/main.tex` is a compilable long-term Chinese paper template with the topic, motivation, questions, method, and evaluation design already drafted.
- The paper's experimental results, typical chains, counterfactual results, and conclusion sections remain explicit placeholders.
- The literature corpus is organized into four purpose-driven modules: risk/safety metrics, mixed-autonomy propagation/control, closed-loop testing, and human interaction/trajectory prediction.
- The literature index says preprints are not retained and Sci-Hub is disabled; formal sources are intended.
- Verification on 2026-07-12: all 10 pytest tests passed in 2.54 s.
- Re-running `analyse_existing_run.py` from the saved 309 frame-level events reproduced 16 episodes, 37 candidates, 18 direct edges, and all documented summary values.
- This reproduction begins from saved risk detections, not from raw Flow emission or a newly executed closed-loop rollout.
- The LaTeX paper was independently compiled in a temporary directory with XeLaTeX, BibTeX, XeLaTeX, XeLaTeX; it produced a 4-page PDF with no final undefined-reference or compile error warnings.
- Consistency scan confirms the major unfinished items are explicitly visible rather than hidden: counterfactual rollout, full metrics, paper result placeholders, and missing literature metadata.
- Many literature-table entries still mark DOI as pending, matching the README's warning that bibliography metadata needs formal verification.
- The result folder is named `pilot_20260714` although the workspace inspection date is 2026-07-12; treat the folder name as a label, not reliable chronology.
- `.gitignore` covers Python caches and LaTeX build/validation directories but there is no Git repository at this root.
- `run_feasibility_week.py` still writes a stale status string saying real Flow rollout is pending environment setup, while newer documents and artifacts show the server smoke succeeded.
- Formal experiment grouping is inconsistent across documents: the top README/paper use 0/20/50/80/100%, while the feasibility report/older plan use 0/20/40/60/80/100%.
- The literature folder contains 22 PDFs and exactly 22 CSV table rows; the paper bibliography currently contains 9 entries.

## Inferences To Validate
- The project appears to be between feasibility validation and systematic experimental execution.
- The code likely implements the observational analysis pipeline, while the intervention/re-rollout layer remains future work.
- The external DRIFT repository and its `run_penetration_study.py` are dependencies of the full intended workflow but are not present in this folder.
- Some roadmap details are stale relative to the top-level README and should be treated as historical planning rather than current instructions.

## Open Questions
- Which penetration grid is authoritative: 0/20/50/80/100% or 0/20/40/60/80/100%?
- Where is the authoritative external DRIFT/Flow repository, and can it be versioned or referenced reproducibly from this project?
- How will valid lane, road segment, leader, AV/HV type, method, penetration, and seed metadata be preserved in raw emissions?
- Should overlapping threshold labels be treated as separate graph nodes, severity levels of one physical episode, or a hierarchical event taxonomy?
- What exact intervention mechanism can be applied inside closed-loop simulation while holding random seed and other conditions fixed?
- What statistical aggregation and uncertainty reporting will be used across seeds and penetrations?

## Venue Research (2026-07-12)

### Official Scope And Format Facts
- IEEE T-ITS covers fundamental and applied ITS research including modeling, simulation, control, planning, and implementation. Regular papers are suggested at 10 IEEE double-column pages; the abstract is 150-250 words and at most six keywords are allowed. It is hybrid: traditional publication is available, while optional OA and overlength charges may apply.
- Transportation Research Part C centers the transportation-system implications of emerging technologies rather than the technology alone, explicitly welcoming quantitative methods, connected/autonomous vehicles, safety, traffic operations, and open/benchmarkable data. It is hybrid; subscription publication has no author publication fee, while optional OA is charged.
- IEEE T-IV focuses on innovative intelligent-vehicle and automated-vehicle concepts and applications. Regular papers are suggested at 10 IEEE pages. Our current system-analysis framing is less vehicle-method-centric than its core scope.
- Accident Analysis & Prevention welcomes accident/safety modeling and countermeasure evaluation, but a simulator-only surrogate-risk paper would need strong calibration or empirical validation to make the accident-prevention contribution convincing.
- Transportation Safety and Environment explicitly targets safety in complex smart human-machine transportation environments and accepts microscopic simulation and mixed CAV/HDV safety analysis. Original articles allow up to 8,000 words, a 250-word structured abstract, up to 50 references, and up to 10 figures/tables. It is fully open access, so the applicable APC/institutional agreement must be checked before submission.
- Journal of Intelligent Transportation Systems is scope-compatible but warns that about 80% of submissions are desk rejected, especially when planning/operations implications are weak.

### Conference Timing Facts
- IEEE ITSC 2026 regular-paper submission closed on 2026-03-01. Its regular format was 6 pages, maximum 8 with extra-page charges.
- TRB Annual Meeting 2027 closes submissions on 2026-08-01. The remaining time and current single-run pilot make this deadline scientifically unrealistic.
- IEEE IV 2027 is scheduled for 2027-06-15 to 2027-06-18, but official submission dates are still TBA.
- ITSC 2027 official dates/CFP are not yet available; no deadline should be guessed.

### Fit Assessment
- Recommended primary writing target: IEEE T-ITS Regular Paper. It best balances traffic-system analysis, AV/HV interaction, graph modeling, simulation, and intervention methodology.
- Recommended realistic backup: Transportation Safety and Environment Original Article. It is the closest exact scope match for mixed-traffic safety simulation and intervention evaluation, but it is fully OA.
- Stretch alternative: Transportation Research Part C, only if the work develops a stronger general transportation mechanism, theoretical validation, transferability, and open benchmarking beyond a heuristic graph pipeline.
- Conditional alternative: IEEE T-IV, only if the paper is reframed around a concrete AV yielding/control/intervention policy rather than risk-propagation analysis itself.
- Conference contingency: IEEE ITSC 2027, if a concise, complete 6-page version becomes strategically preferable. Avoid simultaneous or minimally changed duplicate submission with a journal.

### Venue-Aligned Minimum Evidence For T-ITS
- Valid lane, leader, road-region, AV/HV, penetration, method, and seed metadata.
- A formal event/episode/edge definition with justification and sensitivity analysis.
- Full graph traversal and metrics, not chain proxies only.
- Multiple scenarios, at least five penetration levels, and multiple fixed seeds with uncertainty/statistical testing.
- At least one genuine closed-loop counterfactual intervention, plus safety and efficiency side effects.
- Baselines/ablations for event-only metrics, dense candidate graph, direct-edge selection, and relation types.
- Manual or rule-grounded validation of representative propagation edges and cases.
- Reproducible configuration, code, and shareable derived data where licensing permits.
# Full Risk Event Visual Review (2026-07-18)
- The validated 270-file extraction was rerun after visual integration: 1,609,149 frame rows, 6,933 frame detections, and 4,131 episodes were reproduced exactly.
- SHA-256 hashes for the manifest, frame events, episodes, event-rate summary, both sensitivity tables, manual-review sample, and dataset summary were unchanged after the rerun.
- Twelve static figures now cover data exposure, event composition, penetration trends, scenario-method rates, TTC and braking thresholds, DRIFT improvement, comparison outcomes, manual review, context flags, override candidates, and representative adjacent frames.
- The figures make the scenario dependence explicit. DRIFT is consistently strong against FS on ordinary braking, but TTC results are not uniformly better. Figure-eight produces the clearest TTC weakness, while ring produces a strong apparent DRIFT advantage and merge remains mixed.
- Against FS, DRIFT has a lower ordinary-braking rate in 67% of matched threshold comparisons, ties in 11%, and is higher in 22%. For TTC, the corresponding shares are 49%, 17%, and 35%.
- Against PI, DRIFT has a lower ordinary-braking rate in 39% of comparisons, ties in 35%, and is higher in 26%. For TTC, DRIFT is lower in only 18%, ties in 38%, and is higher in 44%.
- Manual review keeps all 10 override candidates excluded. Thirty-five of the 60 sampled episodes contain a leader transition, 4 contain a lane transition, and 33 are adjacent to an override candidate.
- The representative context plot confirms that some low-TTC samples are immediately followed by extreme simulator speed changes. The local propagation baseline must therefore report stable-following, interaction-transition, and adjacent-override strata separately.
- Aggregating all scenarios can hide opposite effects. Subsequent propagation analysis must keep scenario and penetration strata visible instead of relying on a single pooled performance number.
- All rendering and extraction work remains CPU-only.

## Project Reappraisal (2026-07-21)

### Scope
- Re-read the current repository rather than relying only on the 2026-07-12 review.
- Treat README/manuscript statements as hypotheses to verify against code, outputs, and cited literature.
- Keep three evidence levels separate: implemented and reproduced; planned but not executed; exploratory interpretation.

### Initial Independent Hypothesis
- The strongest defensible contribution may be a simulator-grounded, intervention-validated account of how surrogate-risk episodes redistribute through local mixed-traffic interaction networks, not a generic or physically nonlocal "risk propagation" claim.
- A null result after controlling local mechanisms would still be scientifically useful if framed as a falsification result that bounds when graph propagation language is justified.

### Fresh Inventory
- Root `README.md` was updated on 2026-07-21 and explicitly says the method is not locked; it asks future work to compare several routes rather than preserve existing code by inertia.
- The repository now has five literature modules. A fifth module adds traffic nonlocal models, classical causal discovery, quantum causal-model boundary papers, and quantum-like decision models.
- Extracted text and structured paper digests already exist under `literature/_work/`, so the primary review can be audited against local full text without re-downloading the corpus.
- The newest communication artifact is the 2026-07-15--2026-07-21 progress report; the main manuscript and README must be checked against it because earlier project records are partially stale.

### README Facts And Version Tension
- The 2026-07-21 root README reframes the topic as vehicle-level pre-crash rear-end conflict and asks three nested questions: reliable event measurement, explanation of event relations, and intervention-based causal evidence.
- The current headline dataset is DRIFT-only: 90 runs, 542,644 state rows, 26.52 vehicle-hours, 382 eligible post-cleaning episodes, 196 selected local edges, 33 multi-hop chains, and maximum depth four.
- Only 5/30 merge runs pass the vehicle-wise circular time-shift test at p <= 0.05; figure-eight is 0/30 and ring has no eligible event under current thresholds. This supports a limited temporal-alignment statement, not propagation or causality.
- Negative controls and closed-loop counterfactuals are still unimplemented. DRAC is documented but not computed by the event extractor.
- Root README correctly flags multi-label duplication as a possible source of false multi-hop paths: one physical conflict may appear as low THW, low TTC, and braking nodes.
- `code/README.md` is stale at the research-status level: it still lists full chain traversal as a future extension even though the newer local-baseline module and outputs implement it. The generic pipeline README also describes a different edge-selection contract than the newer one-parent local baseline.

### Manuscript Tensions Identified Before Code Audit
- The main manuscript still presents the 270-file, three-method dataset (2,057 eligible events; 1,294 local edges; 214 multi-hop chains) as the formal study, whereas the newest README presents the 90-run DRIFT-only subset (382 events; 196 edges; 33 multi-hop chains) as the current primary analysis.
- The manuscript says surrogate indicators are merged into inspectable physical events, but its formal node definition still carries an event type and the README admits low THW, low TTC, and braking can create multiple nodes for one conflict. Physical-event unification is not yet demonstrated.
- The manuscript equation and prose include DRAC in event detection, while the current README explicitly says DRAC is not implemented. Until code confirms otherwise, this is an overstatement.
- The proposed "nonlocal residual" is currently defined as nodes with zero incoming local edge. That is a graph-construction residual, not a statistical residual after conditioning; it can contain missed local causes, threshold failures, sensor/topology mismatches, and the first event of every local chain.
- The paper's strongest completed result is presently a validated local baseline and a method/scenario comparison. The nonlocal and counterfactual components remain protocols, not results.

### Output Package Facts
- Two different valid baseline packages coexist: the all-method package has 2,057 eligible episodes and 1,294 selected edges; the later DRIFT-only package has 382 episodes and 196 selected edges. Their seeds and worker counts also differ (20260718/8 versus 20260719/1).
- The DRIFT-only package labels the method `ours (DRIFT)`. That label should not be treated as proof of ownership or superiority and should be normalized before publication if it can bias tables/figures.
- README's DRIFT-only counts match `code/outputs/local_propagation_baseline_drift_20260719/baseline_summary.json` exactly. The manuscript's all-method counts match `code/outputs/local_propagation_baseline_20260718/baseline_summary.json`.

### Event And Local-Graph Implementation Audit
- `extract_risk_events` emits overlapping labels by design: TTC <= 1 s creates both `low_ttc` and `critical_ttc`; a qualifying near miss can also create TTC and braking labels. Only hard versus severe braking was made non-overlapping.
- `coalesce_risk_events` groups by run, vehicle, and event type. It does not merge different indicators into one physical conflict episode. Therefore the manuscript's physical-event language is ahead of the implementation.
- DRAC is absent from `EventThresholds`, emitted columns, and extraction logic. The manuscript's DRAC-based detector statement is not implemented.
- Episode rows retain the first detection's time, position, lane, leader, TTC, and THW, while adding an end time and duration. Local edges use only the episode start time and first-row topology.
- Candidate edges require target start > source start, but do not require source end <= target start. Overlapping episodes can therefore become directed edges even though the data only establish co-occurrence/order of onset.
- Same-vehicle edges always use zero distance and have no spatial constraint. Leader/follower edges use headway recorded at one event; same-region edges use absolute x difference within lane-based 50 m buckets. Merge-road topology is not normalized across edges.
- Every target keeps exactly one highest-scoring predecessor. This forces an in-degree <= 1 forest and makes chain counts/depths properties of the selection heuristic as well as the traffic process; competing parents and converging causal paths are discarded.
- Link score weights (1.0/1.0/0.9/0.65) are manually assigned heuristics, not fitted probabilities or causal effects.
- The circular-time null shifts each vehicle's event timestamps within the observed event-time span while leaving event metadata/topology fixed. It tests excess time alignment under that particular event-preserving null, not a causal null, and currently has no multiple-testing correction across runs/cells.

### New Read-Only Quantification Of Graph Artifacts
- In the DRIFT-only eligible set, 45 same-run/same-vehicle/same-start groups contain multiple event types, covering 122/382 nodes (31.9%). In the all-method set the corresponding figure is 323/2,057 (15.7%).
- In DRIFT-only, 97/196 selected edges (49.5%) have `source_episode_end >= target_episode_start`; 79/100 same-vehicle edges and 18/96 cross-vehicle edges overlap or touch in time. These edges cannot be interpreted as completed-source then downstream-response propagation without a different temporal convention.
- In the all-method graph, 223/1,294 edges (17.2%) overlap/touch; the fraction is much larger in DRIFT because its graph has many tightly co-occurring multi-indicator episodes.
- DRIFT-only has 81 connected chains, of which 30 contain no cross-vehicle edge. All 33 depth>=2 chains contain at least one cross-vehicle edge, but they can still include same-vehicle multi-indicator branches.
- Across the 60 DRIFT run-level null tests, 5 have raw p <= .05 and none survives a single Benjamini-Hochberg correction across all DRIFT runs. Across all 205 tests, none survives a global BH correction. Group-wise correction still needs to be reported separately because the scientific testing family must be prespecified.
- The dominant DRIFT edge context is transition-plus-adjacent-override to the same stratum (65 edges), larger than stable-to-stable (22 edges). Thus the graph is strongly shaped by interaction changes and simulator-adjacent behavior, not only stable following.

### Sensitivity To A Physical-Process Interpretation
- Requiring strict temporal succession (`source_end < target_start`) reduces the DRIFT graph from 196 to 99 edges and depth>=2 components from 33 to 5; maximum depth falls from 4 to 3. This is a much larger effect than the reported 1--5 s edge-window sensitivity.
- Merging same-vehicle episodes whose time intervals overlap/touch yields 251 physical-process clusters from 382 DRIFT nodes. Seventy-three clusters are multi-type and contain 204 original nodes. Mapping the selected graph to these clusters leaves 85 unique edges and 13 depth>=2 components.
- The same overlap-collapse operation creates cycles in the all-method graph even though the original start-time graph is a DAG. This occurs because interleaved, overlapping processes on different vehicles can produce edges in both directions after node unification; start-time order alone is therefore not a reliable causal ordering.
- Using BH correction within each scenario-method family, DRIFT merge retains 0/30 significant runs (minimum q = 0.099), while FS merge retains 15/30 and FS ring 5/25. The strongest current time-alignment evidence is a baseline-specific local-traffic phenomenon, not a DRIFT-specific nonlocal effect.

### Literature-Corpus Quality Notes
- The local corpus has 45 papers across five modules, but structured legacy summaries exist only for the first 22. All 23 papers in the new nonlocal/causal module have blank digest metadata despite having extracted full text.
- Several legacy `insight` fields are project-forward interpretations (for example, asserting how a paper can support source/amplifier/absorber analysis), not claims grounded in the cited paper. They should not be reused as evidence without checking the original text.
- The manuscript bibliography has detailed DOI metadata for 21 entries, but several mixed-traffic and closed-loop citations still use incomplete `and others` records with no DOI.
- The bibliography correctly separates traffic nonlocal continuum models from Bell/quantum models; however, their presence in one subsection risks implying a stronger conceptual relationship than the literature supports.

### Review Personas
- Traffic-safety measurement specialist: asks whether the event ontology corresponds to collision-conflict processes rather than correlated surrogate labels.
- Time-series causal inference specialist: asks what assumptions make a graph edge identifiable and what null/negative controls are valid under autocorrelation and common causes.
- Mixed-autonomy traffic/control specialist: asks whether apparent propagation is vehicle-following dynamics, shockwaves, control coupling, or true information-mediated influence.
- Closed-loop safety-testing specialist: asks which intervention can be replayed under matched seeds and whether safety improvement trades off with efficiency or exposure.
- Skeptical physics/human-factors specialist: asks whether "nonlocal" and quantum language adds a testable model or only an analogy, and whether decision uncertainty is already explained classically.

### Core Literature Re-read: What The Papers Actually Do
- Wang et al. (TR-C 2024, DOI 10.1016/j.trc.2024.104874) define graph nodes as conflict-prone intersection locations and use Trans-GCN to infer future conflict-risk maps. Their "propagation network" is a spatial prediction structure, not a vehicle-event causal graph.
- Lyu et al. (TR-C 2025, DOI 10.1016/j.trc.2025.105219) use 10 hours of drone trajectories from five expressway diversion zones, a 2-D conflict extraction/TSC indicator, SAM causal discovery over traffic covariates, and GAT prediction. The causal graph is among variables used to structure prediction inputs; it does not establish event-to-event transmission or intervention effects.
- Runge et al. (Science Advances 2019, DOI 10.1126/sciadv.aau4996) introduce PCMCI to reduce false positives from common drivers, indirect paths, and autocorrelation in high-dimensional time series. The method assumes the relevant variables/time lags are represented, focuses on lagged dependencies, notes observational-noise failure modes, and explicitly supports FDR control. Applying it to sparse thresholded event nodes would discard much of the continuous time-series information it expects.
- Luo et al. (AAP 2026, DOI 10.1016/j.aap.2025.108360) are the closest prior work: CRM recursively propagates critical deceleration across successive platoon vehicles, is validated with real platoon data and controlled simulations, models reaction-time uncertainty, and finds central AV placement can interrupt cascading risk. A project contribution limited to local multi-hop graph counts would not clearly exceed this baseline.
- The defensible distinction from Luo is not merely "graph instead of formula": it would need non-platoon/branching topology, unified physical conflict episodes, explicit competing mechanisms, and matched closed-loop interventions that estimate downstream effects.

### Nonlocal Traffic, Closed Loop, And Behavior
- Huang and Du (SIAM J. Applied Mathematics 2022, DOI 10.1137/20M1355732) define nonlocality mechanistically: connected vehicles choose speed from a weighted density over an explicit forward spatial horizon. A suitable non-increasing kernel stabilizes uniform flow; poor weighting can preserve waves.
- Sun and Tan (Physica D 2020, DOI 10.1016/j.physd.2020.132663) likewise use stochastic cellular automata and look-ahead distance/density rules, then derive coarse-grained nonlocal macrodynamics. The target is jam/flux behavior, not vehicle-level conflict causality.
- Colombo et al. (JMAA 2026, DOI 10.1016/j.jmaa.2025.130263) formalize coexistence of local HV density and nonlocal AV density; nonlocal means AVs observe traffic over forward/backward spatial kernels. This supplies a testable mixed-population mechanism, not evidence of unexplained distant action.
- Hui and Zhang (TRR 2025, DOI 10.1177/03611981251381306) extend ARZ with a CAV look-ahead density. Longer look-ahead loosens stability conditions but does not monotonically improve convergence; a moderate 100 m horizon can outperform full-ring observation. Penetration matters more than spatial distribution for long-run stability in their setup.
- Fu et al. (T-ITS 2025, DOI 10.1109/TITS.2025.3592741) make closed-loop generation valuable through dynamic re-planning, interpretable behavior diversity, and controllability. Citing it does not itself validate DRIFT trajectories; simulator behavior/exposure must still be validated against the intended safety question.
- Feng et al. (Nature Communications 2026, DOI 10.1038/s41467-026-69761-x) motivate informative sampling of both failures and successes to reduce safety-learning variance. The relevant lesson is exposure-aware scenario informativeness, not simply replacing rare crashes with a larger count of correlated surrogate labels.
- Schumann et al. (Nature Communications 2026, DOI 10.1038/s41467-026-73345-0) model human collision avoidance through active inference and dynamic replanning, reproducing response times, braking/swerving choices, and outcomes across scenarios. It offers a classical, mechanistic behavioral alternative before quantum-like cognition is considered.
- Song et al. (Scientific Reports 2022, DOI 10.1038/s41598-022-14737-2) study bounded-rational two-car game decisions with quantum game theory versus Markov/CPT models. It is a small decision-modeling study, not a theory of physical traffic propagation, and its own conclusion calls for real and more complex scenes.

### Independent Mechanism Hypothesis
- A stronger and more falsifiable use of "nonlocal" is an information-horizon effect: alter the AV observation/communication kernel while holding vehicle state, seed, and controller family fixed, then estimate how downstream physical conflict processes change.
- The predicted response need not be monotonic. The nonlocal traffic literature specifically suggests an optimal or intermediate horizon may outperform both purely local and global information, giving the project a meaningful dose-response hypothesis rather than a binary distant-edge search.

### Risk-Scope Audit
- The newest weekly report defines a risk event as sustained pre-crash closing in following/merging; braking should count only when it participates in that conflict. The code instead emits `hard_braking` solely from acceleration <= -3 m/s^2, without a proximity/closing requirement.
- Of 118 eligible DRIFT hard-braking episodes, only 44 have TTC <= 2 s or THW <= 1 s at the episode start; 74/118 (62.7%) lack either proximity signal. In merge this is 67/90. These are not automatically irrelevant, but they do not meet the written collision-conflict scope without additional trajectory evidence.
- In the all-method graph, 728/852 hard-braking episodes (85.4%) lack TTC <= 2 s and THW <= 1 s at onset; ring contributes 260 hard-braking episodes and 260 lack that proximity evidence. This explains why the all-method manuscript can show deep ring chains while the DRIFT-only collision-conflict README says ring has no eligible risk under current thresholds.
- `near_miss` is not an independent near-miss detector: by construction it requires TTC <= 1.5 s and braking between -15 and -3 m/s^2, so it duplicates low-TTC/braking evidence.
- Before causal graph work, the project needs a physical conflict-process state machine or continuous severity trajectory, with indicator labels stored as attributes rather than separate graph nodes.

### Upstream DRIFT Mechanism Audit
- The authoritative DRIFT repository exists at `D:/shen/research/code`. `horizon_override` changes the Flow environment rollout horizon; it is not an observation-distance parameter.
- The generic learned input in `OursFullController` contains own speed/acceleration/history, current leader-derived THW/TTC, lane-change state, scenario, and penetration. It does not expose a configurable multi-vehicle look-ahead kernel.
- Merge has a separate hard-coded cross-branch mechanism: `_merge_cross_conflict_state` scans all vehicles on the opposite `left`/`bottom` edge within x=510--605 m, computes each ETA to x=590 m, keeps the minimum ETA, and creates `merge_cross_yield` when the ETA gap is within a fixed range.
- The penetration builder sets `merge_eta_yield=True` for the adopted `ours` family. The candidate controller uses this cross-branch signal at high penetration; full penetration can activate the branch even when the flag is false, so a clean 100% ablation requires a stronger explicit switch.
- This is precisely a non-nearest-neighbor information channel with a known source set, range, direction, and decision rule. It is more defensible to test than an unexplained 80/120 m residual correlation.
- Current downstream emissions do not expose the selected remote vehicle, raw ETA values, `merge_cross_yield`, or whether the cross-branch branch altered the chosen acceleration. Without logging these variables, observational residual analysis cannot condition on the controller's most relevant common/direct mechanism.
- A minimal causal experiment should add or reuse a true mechanism toggle and matched logging, then compare the same seeds with cross-branch ETA information enabled versus disabled/limited. At p60/p80 the current boolean may be usable; at p100 the bypass must be audited before claiming a clean ablation.

### Multi-Perspective Dialogue Synthesis

#### Traffic-Safety Measurement Specialist
- Q: Are current nodes physical collision-conflict events? A: Not yet. Wang's graph uses spatial risk cells, Lyu uses 2-D conflict/TSC, and Luo uses recursive critical deceleration; the current code instead retains overlapping threshold labels as nodes.
- Q: Can hard braking be used as a conflict event by itself? A: Only as a trigger/candidate. The written scope requires sustained closing, while 62.7% of DRIFT hard-braking episodes lack low TTC/THW at onset.
- Q: What is the minimum repair? A: Build one physical-process interval per interacting vehicle pair, attach TTC/THW/DRAC/braking as time-varying attributes, and validate onset/end/severity against trajectory geometry and sampled frames.

#### Time-Series Causal Inference Specialist
- Q: Does start-time order identify direction? A: No. Nearly half of DRIFT selected edges overlap/touch in time; Runge et al. explicitly warn about autocorrelation, indirect paths, and common drivers.
- Q: Is one circular-shift test enough? A: No. It is a useful temporal-coincidence null, but it needs a prespecified testing family, FDR/randomization correction, pre-period/placebo tests, and nulls that preserve traffic-state waves and controller exposure.
- Q: What provides the cleanest estimand? A: Paired randomized simulator interventions on a known mechanism, estimating downstream outcome differences by hop/distance/time rather than promoting observational graph edges to causes.

#### Mixed-Autonomy Traffic And Control Specialist
- Q: What could create a true non-nearest-neighbor effect? A: Look-ahead density, V2V topology, delayed multi-predecessor communication, centralized control, or DRIFT's cross-branch ETA-yield rule. All have observable channels.
- Q: Is penetration currently a clean explanatory variable? A: Not fully. It changes vehicle composition and also gates parts of the ETA-yield logic, so mechanism activation and population composition are entangled.
- Q: What hypothesis follows from nonlocal traffic theory? A: Downstream safety may respond non-monotonically to information horizon; moderate range can outperform both nearest-neighbor-only and global observation.

#### Closed-Loop Safety-Testing Specialist
- Q: Is DRIFT sufficient as a test bed? A: It is executable and seedable, but SUMO overrides, hand-coded merge guards, controlled AV priors, and simplified behavior must remain explicit threats to external validity.
- Q: What is the smallest decisive experiment? A: In matched merge seeds at p60/p80, toggle cross-branch ETA-yield information, log the selected remote vehicle/ETA/decision, and compare downstream physical conflict burden plus efficiency.
- Q: What would count as success? A: A repeatable post-treatment effect with no pre-treatment/placebo effect, a plausible delay/distance profile, mediation through the logged decision channel, and bounded speed/outflow cost.

#### Skeptical Physics And Human-Factors Specialist
- Q: Does Bell nonlocality justify distant traffic propagation? A: No. Bell correlations arise under quantum preparations/measurements and obey no-signaling; classical connected vehicles have explicit information and control channels.
- Q: Is quantum-like probability useful? A: Only as a competing behavioral model for bounded-rational choices, tested against classical models such as active inference under vehicle/person-disjoint evaluation. It does not support physical propagation.
- Q: What terminology should the paper use? A: Prefer `cross-branch information-mediated effect`, `non-nearest-neighbor control influence`, or `information-horizon effect`; reserve `nonlocal traffic model` for explicit spatial kernels and remove quantum terminology from the core title/contribution.

### Supplementary Literature Gap Check
- Additional verified control literature includes `Risk of Cascading Collisions in Network of Vehicles With Delayed Communication` (IEEE TAC, DOI 10.1109/TAC.2025.3640000) and `Stability and Safety Analysis of Connected and Automated Vehicle Platoon Considering Dynamic Communication Topology` (T-ITS 2024, DOI 10.1109/TITS.2024.3398111).
- These papers directly connect cascading collision risk to communication topology, delay, uncertainty, and multi-predecessor information. They strengthen the case for an explicit channel intervention and should be evaluated for the core bibliography before adding more generic GNN/quantum citations.
- Broad external searches for traffic-conflict Hawkes/point-process work were low precision and did not reveal a clearly superior, directly applicable event-propagation method. This is a documented literature gap, not evidence that no such work exists.

## Final Independent Synthesis

### Current Defensible Claim
- The project has a reproducible data-quality and descriptive local-association pipeline. It can show how rule-triggered surrogate episodes co-occur along same-vehicle, leader/follower, and same-region relations, and that the pattern is strongly method/scenario dependent.
- It cannot yet claim a physical conflict-event propagation network, a DRIFT-specific temporal effect, an unexplained distant relation, or a causal intervention effect.

## Explicit communication Pilot B corrected findings (2026-08-02)
- The final analysis contains 32 unique valid cells and excludes 8 source-high cells affected by penetration parsing plus 8 communication seed-2 cells affected by cross-run channel state.
- Final channel audit: off applied 0, oracle 4711, comm-ideal 5018, comm-impaired 2809; impaired communication dropped 706/3670 sent messages (19.24%).
- All 32 runs had zero collisions. TTC conflict burden and hard-braking effects are heterogeneous across demand and penetration, so the defensible result is a measurable communication-mediated influence, not a general safety benefit.
- With only two seeds, all Pilot B numerical results remain preliminary method smoke evidence.

### Recommended Research Question
- In mixed-autonomy merge traffic, does DRIFT's cross-branch ETA information channel causally change downstream rear-end conflict processes, and how does that effect vary with penetration, time, distance, and intervening vehicles?

### Recommended Contribution Stack
- Measurement: represent one relational physical conflict process per interacting vehicle pair; TTC, THW, DRAC, braking, collision, and recovery are attributes/states, not independent event nodes.
- Mechanism: decompose nearest-neighbor kinematic transmission from cross-branch ETA-information exposure and shared controller/traffic-state effects.
- Evidence: estimate paired closed-loop intervention effects and safety-efficiency trade-offs; use the graph to visualize and localize effects, not to manufacture causal direction.

### Minimal Decisive Experiment
- Scenario: merge first; use p60 and p80 because the current ETA-yield flag is active and cleanly toggleable there. Use p20/p40 as mechanism-inactive negative controls. Audit/fix the p100 bypass before including full penetration.
- Treatment: same initial condition and seed, cross-branch ETA information enabled versus disabled. Later add a range/delay dose such as local-only, 25/50/100 m, and available/full branch information if the controller interface is generalized.
- Logging: ego and selected remote vehicle IDs, raw ETAs, ETA gap, exposure/activation time, chosen candidate, acceleration before/after the branch, local leader state, and SUMO override status.
- Primary outcome: downstream pair-level cumulative conflict burden in a fixed post-treatment window. Secondary outcomes: conflict probability, minimum TTC, maximum DRAC, braking response, collision, recovery time, speed, outflow, and travel time.
- Analysis: paired seed differences, randomization/permutation inference, confidence intervals, pre-period placebo, wrong-branch/pseudo-source controls, multiplicity correction, and effect curves over time/distance/hop rather than only edge counts.
- Interpretation gate: call it information-mediated only if the effect begins after activation, follows the logged channel, survives local-state controls/placebos, and is reproducible across seeds. A null effect is a valid finding that bounds the controller's remote influence.

### Alternative Routes
- Safer fallback: drop `nonlocal` from the title and study measurement-valid local collision-conflict processes plus closed-loop intervention. This is defensible for a thesis but must distinguish itself from Luo's CRM through merge topology and actual intervention.
- More ambitious: use continuous vehicle-pair risk trajectories and distributed-lag/conditional causal models after the randomized mechanism experiment. Do not start with PCMCI on sparse thresholded episode IDs.
- Not recommended as core: quantum/Bell/quantum-causal framing. Keep at most one short boundary paragraph; use active inference or classical bounded-rational models as the first behavioral comparator.

### Go/No-Go Order
- Gate 1: physical conflict-process labels pass manual/trajectory validation and hard braking outside conflict is separated as a response/background action.
- Gate 2: strict non-overlap and label-collapse sensitivity no longer changes the qualitative result.
- Gate 3: the remote ETA mechanism is logged and independently toggleable at each selected penetration.
- Gate 4: paired intervention shows a stable post-treatment effect with acceptable efficiency cost.
- Only after Gate 4 should the project use `causal`, `information-mediated`, or `non-nearest-neighbor effect` in its main contribution.

## 非局部问题补充调研（2026-07-25）

### 第一轮近年检索
- OpenAlex 对“nonlocal/look-ahead CAV safety”和“information horizon/look-ahead distance”检索的精度有限；大量结果属于一般自动驾驶综述，不能据此支撑非局部定义。
- 命中的直接相关新工作包括 `An anisotropic traffic flow model with look-ahead effect for mixed autonomy traffic`（arXiv:2407.20554，2024）和一篇 2026 年多类别非局部时延模型。两者值得核对原文，但仍属于宏观流量/稳定性建模，尚不能替代车辆冲突的闭环因果证据。
- `Modelling and simulation of (connected) autonomous vehicles longitudinal driving behavior: A state-of-the-art`（IET ITS 2023，DOI 10.1049/itr2.12337）可用于梳理跟驰信息输入类别，但综述本身不是“远端作用存在”的证据。
- 当前结果再次表明，文献检索必须以机制关键词（multi-predecessor、communication topology、delay、look-ahead kernel、channel intervention）收窄，而不能把所有 CAV 安全或预测论文都算作非局部研究。

### 第二轮近年检索
- “multi-predecessor + communication topology + delay + collision risk”直接命中 T-ITS 2024 动态通信拓扑论文（DOI 10.1109/TITS.2024.3398111），与先前 IEEE 原始摘要核验一致：多前车信息、通信失效/时延和动态权重共同改变稳定性与碰撞风险。
- 同一检索还命中 `Characterization of Transient Communication Outages...`（IEEE OJITS 2023，DOI 10.1109/OJITS.2023.3237958）和 `Predictive Model-Based and Control-Aware Communication Strategies for CACC`（IEEE OJITS 2023，DOI 10.1109/OJITS.2023.3259283）。它们可作为“信息边是可失效、可延迟、可设计的控制输入”这一操作性观点的补充来源。
- `Knowledge-guided self-learning control strategy for mixed vehicle platoons with delays`（Nature Communications 2025，DOI 10.1038/s41467-025-62597-x）是新的高相关候选，但需要核对原文后才能判断它是否研究非最近邻拓扑还是仅研究有时延的局部控制。
- “closed-loop intervention + causal + traffic conflict”检索精度很低，没有发现可直接套用到车辆冲突传播的标准范式。该空缺不证明不存在相关工作，但说明本项目更适合把已知控制通道的随机/配对开关作为因果识别基础，而不是等待某个现成的“非局部冲突”算法。

### 原文核对：信息范围与时延控制
- Hui 与 Zhang 的 arXiv v2 原始摘要（2407.20554，2024-12-06 更新）明确把 CAV look-ahead 定义为“在给定前视距离内的非局部平均密度”。更长前视距离放宽线性稳定条件，但数值实验显示它不一定让系统更快收敛；这为“信息剂量效应可能非单调”提供了直接依据。
- 该文的结果变量是均衡与交通波稳定性，并非车辆对冲突；因此可迁移的是信息范围 `h` 与平均/加权规则，不可直接迁移的是安全因果结论。
- Nature Communications 2025 原文把一般混合车队分解为 `CV-HVs-CV` 子车队，并显式处理共享无线系统中的通信时延。其核心问题是混合车队稳定控制和人驾行为不确定性，初步阅读没有显示它把任意远端车辆都作为“超距源”。
- 这进一步支持三图分离：物理车辆串、可通信/可控制的信息连接、以及由干预产生的下游风险结果不能混成一张“传播图”。

### 原文核对：通信通道是可干预对象
- Hasan、Girs 与 Uhlemann（IEEE OJITS 2023，DOI 10.1109/OJITS.2023.3237958）把偶发丢包造成的瞬态连接状态分类，并用状态机按通信质量与危险水平改变控制器/车间距，必要时进入紧急制动。它证明通信质量不是背景协变量，而是会改变控制动作与安全状态的机制变量。
- Razzaghpour 等（IEEE OJITS 2023，DOI 10.1109/OJITS.2023.3259283）提出事件触发、模型驱动且 control-aware 的通信：各车维护远端状态估计，只在性能误差超过阈值时更新。论文报告平均通信率降低 82%，速度偏差小于 1%。
- 对本项目的直接迁移是：信息边可以通过“是否发送、何时发送、发送谁、延迟多久、误差阈值多大”形成实验处理；不能把“在图中距离较远”自动等同于接收了信息。
- 因此候选非局部暴露宜定义为 `I_{A→B}(t; h,w,d,q)`：来源 A、接收/控制对象 B、范围 h、权重 w、延迟 d 和通信质量 q 均应被记录或操纵。

### 路网/合流语境检索
- 路网非局部检索再次显示，数学非局部模型强调“核函数/信息视域如何跨过连接节点”，而不是凭欧氏距离判断。2026-07 新出现的 `A general framework for nonlocal traffic flow models on networks`（arXiv:2607.09227）需要核对其路网耦合定义。
- 合流检索命中 `Collaborative Multi-Lane On-Ramp Merging Strategy ... Using Dynamic Conflict Graph`（JICV 2024，DOI 10.26599/JICV.2023.9210032）。它可能与项目图表面相似，但必须检查其图节点/边是协同调度冲突约束，还是风险事件传播；标题相似不能视作同一问题。
- 合流控制文献普遍通过 V2X、集中/分布式协调或轨迹优化处理跨车辆冲突，这为“显式通道”提供应用场景；但其目标通常是无冲突排序和轨迹规划，不等于估计远端车辆对下游冲突负担的因果效应。

### 原文核对：路网反馈与动态冲突图
- Keimer、Pflug 与 Prohaska（arXiv:2607.09227v1，2026-07-10）把边上的非局部速度函数与 buffer-based junction dynamics 耦合；动态 k 最短路根据道路旅行时间与路口等待时间更新路径，形成交通演化—路径选择反馈。它扩展的是路网状态与路由反馈，不研究车辆级冲突传播。
- 这篇非常新的预印本可作为路网层“非局部 ≠ 欧氏远距”的补充，但由于尚为 arXiv v1、且层级不同，不宜成为项目主要安全论据。
- Shi 等（JICV 2024，DOI 10.26599/JICV.2023.9210032）已确认是开放获取论文，下一步需从 IEEE 原始页核对 dynamic conflict graph 的节点、边与优化目标；当前仅有题录信息，不先猜其接口。

### 原文核对：Dynamic Conflict Graph 与本项目的区别
- IEEE 原始全文表明，Shi 等把物理平面的“车辆组信息”映射到 cyber plane：图节点携带不同车辆组属性，边描述车辆组间纵向和横向冲突关系；通过图分解和启发式树搜索共同决定主线换道车辆集合、各路线通过顺序与轨迹。
- 该图是广域信息支持的集中式协同规划/约束图，目标是合流排序、换道和轨迹优化，并通过 SUMO 比较安全与效率；它不是由已发生冲突事件构造的风险传播图，也没有估计某一远端信息源对后续冲突负担的因果效应。
- 对项目最有价值的对照是：同一 `merge` 场景中，“图”至少有三种完全不同的语义——物理/冲突约束图、信息/控制图、结果/风险过程图。若论文只说“构建动态图”，很容易与已有合流调度图混淆。
- 因此汇报第一部分应先画三图并说明跨图链条：`A 的状态 → 信息边/控制器 → B 的控制动作 → B 与其局部邻居的冲突过程`。只有最后一段在通道干预下改变，才是我们要验证的信息介导非最近邻效应。

### 因果“网络干扰/溢出”视角
- 交通专用的 `causal interference/spillover` 与 `closed-loop conflict intervention` 关键词检索精度很低，没有找到可直接定义车辆级非局部风险效应的通用做法。
- 但一般因果推断中的 interference/spillover 概念与本项目高度贴合：一个单元的处理会改变其他单元的结果，因而传统 SUTVA 的“无单元间干扰”不成立；应显式定义 exposure mapping，而不是只给每辆车一个独立 treatment 标签。
- 在本项目中，处理不是“车辆 A 存在”，而是 A 的状态是否通过跨支路 ETA/V2X/控制器暴露给 B。这个视角比“远距相关”更严格，也能自然定义 direct effect、spillover effect 和局部物理中介。
- 下一步需核对网络干扰的基础文献题录与定义；它们只提供因果估计语言，不能代替交通机制和闭环仿真验证。

### 网络干扰题录初筛
- 一般网络干扰文献常把处理扩展为“自身处理 + 邻域暴露”，并通过实验设计、逆概率加权或 generalized propensity score 估计直接效应与溢出效应；这与项目需要的 exposure mapping 一致。
- OpenAlex 的模糊题名检索没有直接返回 Aronow & Samii 和 Forastiere 等目标原文，不能据结果自行补 DOI；需要再用精确题名/作者接口核对。
- 可作方法背景而非核心交通依据的候选包括 Bowers 等 `Design and Analysis of Experiments in Networks: Reducing Bias from Interference`（JCI 2016，DOI 10.1515/JCI-2015-0021）与 `Designs for estimating the treatment effect in networks with interference`（Annals of Statistics 2020，DOI 10.1214/18-AOS1807）。

### 网络干扰题录核验
- Crossref 精确核验：Aronow & Samii，`Estimating average causal effects under general interference, with application to a social network experiment`，Annals of Applied Statistics 11(4), 2017，DOI 10.1214/16-AOAS1005。
- Crossref 精确核验：Forastiere、Airoldi 与 Mealli，`Identification and Estimation of Treatment and Interference Effects in Observational Studies on Networks`，JASA，2020 在线发表，DOI 10.1080/01621459.2020.1768100。
- 中介语言还可参考 Hu、Li 与 Wager，`Average direct and indirect causal effects under interference`，Biometrika 2022，DOI 10.1093/BIOMET/ASAC008：该文在 potential outcomes 框架下区分跨单元干扰中的平均直接和平均间接效应，并给出二者与政策干预效应的分解关系。
- 对项目的简化采用：不照搬复杂观测估计器，只借用“暴露映射 + 直接/间接效应”语言；因为仿真中可以直接随机开关已知信息通道，识别条件比纯观测网络更干净。

### 原文核对：暴露映射与邻域处理
- Aronow & Samii 原始摘要明确把干扰实验拆成三部分：处理分配的实验设计、从全局处理分配到各单元实际暴露的 mapping、以及回答实质问题的 estimands；框架允许已知形式的任意干扰，并使用随机化/逆概率加权推断。
- Forastiere 等原始摘要明确指出，有干扰时单元结果同时依赖自身处理和其他单元（如网络邻居）的处理；观测研究还必须把邻居处理与个体/邻域协变量纳入扩展无混杂条件。忽略干扰的朴素估计会产生偏差。
- 本项目可把“邻域”重新定义为信息图邻域而非物理邻接：B 的 exposure mapping 由跨支路 ETA 候选集合、被选中远端车辆、ETA 差、通道状态、延迟/权重共同决定。
- 因仿真中可配对随机化通道，主 estimand 可直接写成 `E[Y_B(I=1)-Y_B(I=0)]`；网络干扰文献主要帮助说明为什么不能把 A、B 当成相互独立样本，也为什么必须报告 exposure mapping。

### 本地全文与既有专家对话复核
- 本地非局部交通全文进一步给出一致定义：2024 年 1-to-1 junction buffer 模型明确称“nonlocal”是通量函数依赖核函数与速度/密度的卷积，且核支撑只向前；它研究交互范围趋近 0 或无穷时的模型极限。
- Sun & Tan 的本地全文把 `L` 定义为驾驶员感知前方 `L` 个元胞的 look-ahead range，并表明不同 look-ahead rule 在大 `L` 时产生显著不同的流量—速度结果；说明范围和聚合规则必须共同定义。
- 既有五视角对话已经覆盖测量、时序因果、混合交通控制、闭环安全测试和物理边界。补充文献没有推翻其结论，而是把“暴露映射”和“三图分离”论证得更严谨。
- 综合后的新增判断：本项目真正可做的不是寻找“远处事件边”，而是估计一个已知信息图暴露相对 local-only 基线的 spillover effect，并把物理跟驰链作为中介/竞争机制。

### 本地题录补充核对
- Chiarello、Friedrich 与 Göttlich 的 junction-buffer 论文正式发表于 Networks and Heterogeneous Media 19(1), 405–429, 2024，DOI 10.3934/NHM.2024018；它比 2026 新预印本更适合作为交叉口/路网非局部定义的稳定来源。
- 本地文献库还包含 `Counterfactual safety benefits quantification method for en-route driving behavior interventions`（AAP 2023，DOI 10.1016/J.AAP.2023.107118），可作为“同一对象干预/无干预潜在结果”安全估计的应用参考，需再核对原始摘要。
- 另有跨尺度交通—通信控制候选（AAP，DOI 10.1016/J.AAP.2025.108339）将多跳通信、时延与拥堵/安全控制耦合，可能是非局部机制的近年强对照；需核对它是否已经正式上线及其安全对象。

### AAP 题录与时间核验
- Crossref 确认 10.1016/J.AAP.2023.107118 的正式卷期时间为 2023-09，Elsevier PII 为 S0001457523001653。
- Crossref 确认 10.1016/J.AAP.2025.108339 的正式卷期时间为 2026-03，Elsevier PII 为 S0001457525004270；截至当前日期 2026-07-25 已经是已出版文献，不属于未来占位。
- 两条 Crossref 记录没有摘要，后续需读出版社原始页；在摘要核对前只把它们当候选，不引用本地二手摘要中的数值结论。
- PubMed DOI 精确查询各返回唯一记录：107118 对应 PMID 37235966，108339 对应 PMID 41351937；可据此读取出版社提交的结构化摘要。

### 原始摘要核对：反事实安全与交通—通信耦合
- Zheng 等（AAP 2023，PMID 37235966）指出传统干预效应比较受观测混杂影响，先用结构因果模型推断同一干预样本的“若未干预”情形，再用 EVT 将速度保持变化映射到事故概率，并形成干预评价—优化闭环。其应用对象是安全播报与网约车驾驶行为，不是车辆间风险传播。
- 可迁移部分是潜在结果口径和闭环评价：同一 seed/初始状态下比较通道开关，避免把不同交通状态的自然差异误当作用；不可迁移部分是其 TPB/EVT 具体行为模型。
- Wu 等（AAP 2026，PMID 41351937）明确研究“不稳定长程通信”下交通系统—通信网络的反馈：通信层用 distance-to-delay interval backtracking 优化长程混合通信路由，交通层结合微观 barrier consensus control 与宏观 delay-corrected cruising control，主动消散拥堵波。
- 该文直接支持“非局部控制必须同时说明信息路由、时延和交通响应”，但其主要安全路径是消除拥堵/激波，摘要报告的安全提升来自拥堵消除；它仍未回答跨支路 ETA 信息是否改变单车对冲突过程。
- 这篇是本项目的重要近年竞争参照：如果我们只说“把通信网络和风险结合”不够新；我们必须突出 `merge 跨支路信息暴露 → 控制决策 → 车辆对冲突负担` 的机制级随机干预与中介验证。

## 非局部问题最终收敛（2026-07-25）

### 建议研究问题
- 在混合交通合流中，当远端来源车辆 A 与目标车辆 B 并非直接物理邻接/冲突对时，A 的状态经跨支路 ETA 信息或控制通道暴露给 B，是否通过改变 B 的控制动作，因果地改变 B 与其局部邻车在后续窗口内的车辆对冲突负担？该效应如何随信息范围、权重、时延和通信质量变化？

## 周推进文档证据收敛（2026-07-26）

### 区域定义
- 本地原文核对显示，现有文献没有统一且可直接照搬的风险区域定义。
- Wang et al. (2024) 从 PET 冲突位置识别冲突易发区并映射为节点，同时指出规则网格可能把弱相关空间混入同一单元；其节点依赖已观测冲突，不适合直接作为本项目机制开关实验的固定地理容器。
- Lyu et al. (2025) 明确说明快速路分流区按交通功能与距离划分，每个场地分成三个 section；支持“功能边界 + 距离补充分段”的组合原则，但没有给出可直接迁移到所有路网的统一长度。
- Chiarello et al. (2024)、Huang & Du (2022) 及 Hui & Zhang (2025) 均把非局部作用定义在明确的道路拓扑/前视范围和核函数上，支持把机制范围作为状态或处理变量，而不是让它决定风险区域边界。
- 因此采用本文操作化规则：先固定支路和拓扑强制边界，再以名义长度 `L0` 均分拓扑段；机制激活位置只写入日志。`L0=25/50/75 m` 是本项目敏感性设置，不是文献规定值。

### 创新与本周实验边界
- 创新应写成拟验证贡献，而非既有结论：统一物理冲突事件、三图分离、步数/距离双尺度判定、源特定通道配对干预、安全—效率联合评价。
- 最小 pilot 采用 p60/p80、每个渗透率 5 个种子、on/off 配对，共 20 次仿真；p100 在旁路清理前不作为干净开关证据。
- 当前未实现的 DRAC、跨指标物理事件合并、远端机制完整日志必须在文档中明确标注，不得输出虚构结果。

### 三层操作性定义
- `非最近邻信息暴露`：A 与 B 不是直接 leader/follower 或同一物理冲突对，但 A 的状态被明确纳入 B/控制器的输入。只需通道日志即可确认，不等同于因果效应。
- `信息介导的控制影响`：在相同局部状态下，屏蔽/改变该信息会改变 B 的控制决策或加速度。需要记录候选来源、原始 ETA、ETA 差、触发分支、通道参数和动作前后差异。
- `信息介导的非局部因果效应`：配对/随机开关通道后，B 的后续车辆对冲突过程发生可重复变化，且无处理前效应，不能被普通跟驰链、共同交通状态、SUMO 覆盖或渗透率门控解释。

### 三张图
- 物理交互图 `G_P(t)`：直接 leader/follower、车辆对接近与冲突几何；用于定义局部传播和结果发生在哪些车辆对上。
- 信息/控制图 `G_I(t)`：ETA、V2V/V2I、多前车、集中控制、时延/丢包/权重；用于定义谁实际暴露给谁。
- 结果过程图 `G_Y(t,t+T)`：处理后车辆对冲突负担、冲突概率、最小 TTC、最大 DRAC、制动/碰撞/恢复等；不能与前两图共用同一种“边”语义。

### 暴露映射与估计量
- 对目标 B 定义 `g_B = f(G_I, source_set, selected_source, ETA_gap, h, w, d, q)`，其中 `h` 为信息范围、`w` 为聚合权重/规则、`d` 为时延、`q` 为通信质量；`g_B=0` 是 local-only/通道关闭基线。
- 机制级主效应可写为 `tau_B(g,g0)=E[Y_B(g)-Y_B(g0) | X(t0)]`。仿真中通过相同 seed 与初始状态的配对通道干预识别。
- 若要声称特定 A→B 作用，必须做 source-specific mask；直接关闭整条跨支路通道只能识别“机制/通道总效应”，不能把总效应归因给某一辆 A。

### 证据等级
- E0：距离较远或统计相关——只能生成候选。
- E1：记录到明确信息暴露——可称非最近邻信息暴露。
- E2：干预信息后控制动作改变——可称信息介导控制影响。
- E3：随机/配对干预使处理后冲突结果改变且安慰剂通过——才可称非局部因果效应。
- E4：来源屏蔽、范围/时延剂量、决策中介和局部链控制共同支持——形成强机制证据。

### 不能采用的定义
- 不能用固定 50/80/120 m 阈值单独定义；它不随道路拓扑、车速、候选集合和通信能力变化。
- 不能用风险图上的长边、无局部父节点或 PCMCI 残差直接定义；它们可能来自自相关、间接路径、共同拥堵状态或遗漏控制器输入。
- 不能把相邻车辆逐跳 CRM 级联称为非局部；它是必须优先解释的局部竞争基线。
- 不能把“全局观察/更远信息”默认视为更好；Hui–Zhang、Huang–Du 和 Sun–Tan 都说明范围与权重效应可能非单调或在错误规则下恶化。
- 不能借用 Bell/量子超距语言；交通系统存在显式经典信息和控制通道。

### 第一部分的结论边界
- 文献没有提供一篇与项目完全相同的标准方案；相邻领域分别研究非局部流量核、通信拓扑/时延、逐跳级联风险、合流冲突图和反事实安全干预。
- 因而可辩护的解决方案不是发明一个距离阈值，而是把这些领域拼成一个可证伪链条：`已知信息暴露 → 控制动作中介 → 下游车辆对冲突结果 → 配对干预反事实`。
- 当前 DRIFT 的跨支路 ETA-yield 规则是最合适的第一个机制，因为它已有明确源集合、冲突点、方向和触发条件；当前缺口是没有导出 selected remote vehicle、原始 ETA、触发状态和动作影响。

## 2026-07-26 Pilot A 执行前核对
- 下游 `research-shuqi` 不是 Git 仓库；上游 `D:/shen/research/code` 位于干净的 `main` 分支，实际 Flow/SUMO 运行副本在 WSL `/home/shen/shen/mixed_autonomy_lab`。
- 当前区域编号仍是 `lane + floor(x / region_length_m)`，没有使用 `edge_id + relative_position` 和拓扑强制边界；Pilot A 将以独立模块分析，不改写既有正式事件输出。
- 上游构建器仍把 adopted ours 的 `merge_eta_yield` 写死为 true；运行脚本循环 `env.reset()`，没有显式 run seed。这两个接口必须先测试和改造，才能做可信的 on/off 配对。
- 本轮实施采用隔离 worktree、TDD 和独立输出目录；不重训模型，不修改周推进文档，不把 4 次冒烟结果外推为正式因果结论。
- 下游现有 52 项测试在改动前全部通过；上游没有专用 pytest 套件，因此本轮必须新增小型、无 Flow 重依赖的行为测试，并保留 compileall 与 WSL 真仿真作为两层验证。
- 同名 Windows Git 代码和 WSL 正式运行副本并非同一版本：WSL 控制器少了后续 candidate-bank、风险权重与筛选器扩展。正式 p60/p80 数据由 WSL 版本生成，因此冒烟实验必须在 WSL 版本上做最小移植，不能整文件换成 Windows 新版，否则 on/off 差异会混入控制器版本差异。

## 2026-07-26 Pilot A 结果
- 拓扑区域尺度结果：25/50/75 m 分别为 39/21/18 个暴露区域、5/4/4 个风险区域，46 条合格 episode 在三种尺度下均成功回连原始轨迹。事件映射分数的 Spearman 为 0.796（25–50）、0.893（25–75）、0.935（50–75）；25 m 提供更多空间分辨率，50/75 m 已较粗。
- 3 s、200 m 候选窗下，仅得到 9 条 all-direct、3 条跨车辆 direct 边；95% 距离分别约 27.31 m 和 27.97 m。30 m 可继续作为 D0 初始值，但样本很小，不能在本轮定死。
- 四组均使用配置 seed 20260726、实际 SUMO seed 13269。p60/p80 on 分别有 651/749 次 `applied`；shadow-off 分别有 629/625 次 `would_trigger`，但 `applied=0`。
- 两个渗透率的首次机制应用均定位到 9.6 s，on/off 首次轨迹分化均为 9.8 s；应用前车辆键完全一致，所有比较字段最大差为 0，说明本轮 on/off 配对成立。
- 单 seed 指标方向并不一致：on 比 off 平均速度低约 1.49/1.55 m/s、出流低 90 veh/h；hard-brake 计数由 2 降到 1、最小 TTC 提高，但 TTC 违规率反而更高。只能解释为机制可运行且存在安全—效率权衡，不能宣称净安全收益。
- SUMO 日志中 on/off 分别出现 2/4 次急刹警告和 4/8 次安全速度覆盖提示，验证了必须同时分析 realized acceleration 和 override，而不能只看控制器候选动作。

## 2026-08-02 显式通信推进起点
- 既有 Pilot A 已完成跨支路 ETA 机制开关、固定种子和动作日志，但 ETA 是控制器直接可读的理想远端信息，不等同于真实通信链路。
- 本轮必须把消息生成、发送、网络交付、接收缓存、信息采用、动作改变和目标区风险结果拆开记录。
- 主识别结构保持为源区域扰动 × 通信通道；理想 ETA、显式通信和受损通信作为机制层级与消融条件。
- 上周结果只作为 oracle/ideal-information baseline 和接口可行性证据，不能提前写成通信安全收益。
- `7.29-8.4推进.md` 当前只有 44 个标题，尚无正文，可按已确认任务顺序逐节填充。
- 主论文 `paper/主论文/main.tex` 当前仍以局部传播基线为主，并明确写着非局部干预未执行；本轮需在新实验后更新题目、摘要、研究问题、方法、实验、结果和局限。
- 主论文当前量子理论边界占一个相关工作小节，但与本轮通信机制相比优先级偏高，后续应压缩为术语边界而非核心文献线。
- `references.bib` 中 `wang2024safety`、`wang2024platooning`、`ma2024risk`、`fu2025trafficmcts`、`li2024hybrid`、`gong2024hinf` 等记录缺完整作者或 DOI，投稿前不能按现状保留。
- 论文已具备 IEEEtran/XeLaTeX 工程和本地结果图，可在原结构内做证据驱动修订，无需另建论文包。
- 交接文件确认上游 Windows 仓库为 `D:/shen/research/code`，隔离 worktree 为 `C:/Users/Lenovo/.config/superpowers/worktrees/code/nonlocal-pilot-a`，WSL 真实运行副本为 `/home/shen/shen/mixed_autonomy_lab`。
- Pilot A 隔离分支截至 2026-07-29 尚未提交或合并；WSL 运行副本版本较旧，只能基于其真实内容做最小移植，不能用 Windows 文件整包覆盖。
- 严格实验的既定主结构为源扰动 `S_A` × 信息通道 `E_I` 的 2×2；正式统计建议 p60/p80、每格至少 10 个配对 seed，但本轮应先验证显式通信模块与小规模配对设计。
- 上游真实控制环境和可回灌机制已经存在，因此显式通信应接入控制器闭环，而不是只在下游日志上模拟网络字段。
- 现有 `nonlocal-pilot-a` 是有效 linked worktree，分支为 `experiment/nonlocal-pilot-a`；修改集中在控制器、实验构建器和运行脚本，新增 `mixlab/nonlocal_pilot.py` 与专用测试。
- 现有 worktree 的改动属于上周 Pilot A，必须在其基础上继续，不能回滚或重建；本轮新增功能需要保持与这些未提交改动兼容。
- Pilot A 的最小 helper 目前只有 `legacy/on/shadow_off` 决策、随机种子和 run token；真实网络消息、时延、丢包、缓存和信息年龄尚不存在。
- 控制器已经能记录远端车辆 ID、原始 ETA、候选触发、是否采用、候选动作和过滤后动作，这些字段可作为显式通信中介链的后半段。
- 运行脚本当前把显式 ETA 模式限制为 `num_runs=1`，正式多 seed 需要改变配置组织方式或增加每 seed 独立条件运行器；不应直接把一个多 run 实验复用同一个 controller run token。
- 上游仓库 `AGENTS.md` 要求 T-ITS 交通系统定位、精确术语、闭环安全/效率/稳定性评价和可复现实验；本轮研究论文与 DRIFT 主论文是不同论文包，当前用户指定的是 `research-shuqi/paper/主论文`。
- 显式通信可采用每个受控车独立的确定性消息通道：原始跨支路状态只生成消息，控制器只能使用已交付且未过期的缓存；零时延零丢包作为显式理想通信，非零时延/丢包/低更新率作为受损通信。
- 合流构建器已经暴露 `merge_highway_flow` 与 `merge_ramp_flow`，运行器支持命名 stress profile，可用 ramp flow 的 nominal/high 条件构造可重复源区负荷扰动，而无需本周引入新的事故注入器。
- Windows Python 缺少 `flow`，专用 pytest 在收集阶段失败；这是环境缺依赖，不是测试断言失败。上周的 WSL Flow 环境仍是实际验证目标。
- WSL 入口 `/home/shen/shen/mixed_autonomy_lab` 存在 `.venv`，但没有交接记录简写中的顶层 `tests/`，需要按实际嵌套目录定位代码与测试；系统 `python` 不在 PATH，验证命令必须使用 `.venv/bin/python`。
- 单独使用 WSL `.venv` 仍不能 import `flow`，正式仿真显然依赖额外 Flow 源码路径或启动脚本环境；必须从实际脚本恢复，不能假设 venv 已安装 Flow。
- 实际 Flow 源码路径为 `/home/shen/shen/paper_repos/flow`；使用该路径加 worktree 作为 `PYTHONPATH` 后，Pilot A 的 12 项测试全部通过（9.03 s）。
- 显式通信实现可限定为一个独立确定性 ETA 通道，控制器输入只取已交付缓存；oracle `on` 与 `shadow_off` 保持现有语义，`communication` 通过参数表达理想或受损链路。
- 合流默认流量为主线 2000、匝道 100 veh/h；既有 OOD 配置使用过主线 2400、匝道 180。为隔离源区因子，本轮只把匝道从 100 提到 180，主线维持 2000。
- 主 2×2 定为匝道源负荷 nominal/high × 通信 off/explicit-ideal；oracle direct ETA 和 impaired communication 作为机制校准与消融，不混入主交互效应定义。
- `DeterministicEtaChannel` 已在 worktree 实现：使用稳定哈希丢包、离散时延队列、发送更新周期和最大缓存年龄，不消耗 Python/NumPy 全局随机状态。
- 通道新增 8 项测试先以缺少类的预期原因失败；实现后上游专用套件为 20 passed（7.35 s）。
- 控制器 `communication` 模式已实现：raw remote 状态只用于生成消息；控制决策只读取已交付且未过期的 cache，消息未到或过期时不会回退到当前真实 ETA。
- 机制日志已扩展为 raw/used remote ID 与 ETA、generated/sent/dropped/delivered、source/delivery step、age、cache usable、would-trigger/applied 和前后动作。
- 控制器接入的 5 个新测试先按预期失败，实现后全套为 24 passed（7.08 s）；WSL compileall 与 worktree `git diff --check` 通过。
- 运行器现支持多 seed 显式机制条件，并把 penetration、source profile、condition label 和 seed 集编码进 run token；ideal/impaired 与 nominal/source-high 日志不会碰撞。
- Task 3 的首轮测试为 8 failed/24 passed，修复后为 32 passed；新增 condition-label 回归测试先 1 failed/32 passed，修复后最终 33 passed（9.10 s）。
- 四份 Pilot B 配置均可解析，每份覆盖 p60/p80 × nominal/source-high × 2 seeds，共 8 次；总计划为 32 次 120-step 闭环运行。
- Pilot emission 不直接提供 TTC，字段包括 `headway`、`leader_id`、`leader_rel_speed`、`realized_accel`、`edge_id`、`x/y` 等；下游目标区指标必须复用现有已审计的 TTC 符号约定，不能另猜。
- 现有 Pilot A 汇总器已实现 configured/actual seed、首次应用定位和处理前轨迹一致性，可复用其审计思路，但不支持通信生命周期、source profile 或多 seed factorial effect。
- 现有风险提取的 TTC 符号约定已核实：`closing_speed = -leader_rel_speed`，且必须要求有效 leader、正 headway 和 `closing_speed > 1e-3`；无 leader 的 1000 m headway 伪值必须排除。
- Pilot A p60-on 在 `left, x=510--590 m` 的 1,243 个车辆步中有 618 个有效 TTC，但最小值约 9.97 s、无 TTC<2 s；若只把主线 left 当目标区，短 smoke 的主指标会退化为全零，需要先审计合流冲突区各 edge 的有效风险分布。
- Pilot A 的短 run 中，TTC<2 s 主要出现在 downstream bottom，off 组偶尔出现在 left；目标区因此固定为 `bottom/left/:center_1` 且 `x=540--612 m` 的下游合流冲突区，源区为其上游匝道输入。
- 下游 `communication_pilot.py` 已实现目标区 mask、leader-aware TTC、连续冲突负担、急制动率、通信生命周期、连续 applied episode 与 paired 2×2 交互。
- Task 4 核心统计测试经历缺模块 RED 后为 5 passed（0.95 s）；汇总 CLI 暂待真实多 run 文件命名产生后完成映射。
- WSL 四个目标文件与 worktree 全部不同；已在 `/home/shen/shen/mixed_autonomy_lab/backups/nonlocal_pilot_b_20260802_prepatch` 逐文件备份并通过 SHA256 校验。
- WSL 实际 runner 比 worktree 更旧，当前不支持 `stress_profiles`，且仍限制显式 ETA 条件为单 seed；Pilot B 移植除了通信参数外还必须最小补入已有的 stress-profile 循环，不能直接复制 worktree runner。
- WSL 旧版已完成最小移植并通过真实代码测试：33 passed（7.42 s）及 compileall。
- p60 单 seed preflight 四组均正常退出，配置 seed 2026080201、实际 SUMO seed 77701、碰撞均为 0。
- preflight 中 oracle 与 explicit ideal communication 的 return=57.8555、速度=13.3803 m/s、出流=1350 veh/h 完全一致；impaired communication 为 57.7561、13.3618 m/s、1350 veh/h；off 为 58.8553、12.9746 m/s、1050 veh/h。
- preflight 仍有急刹与 SUMO safe-velocity clipping，验证了继续基于 emission 的 realized acceleration 和 leader-aware TTC 计算风险的必要性。
- preflight 结构审计为每组 1 emission、1 raw result、0 runner error，通信日志要求的 12 个生命周期/动作字段均无缺失。
- comm-ideal 发送并交付 1290 条消息、0 丢包、675 次 applied；oracle 为 674 次 applied。两组 emission 形状、列和逐值完全相同，最大数值差为 0。
- comm-impaired 发送 648、丢包 116、交付 490、applied 187；观测丢包率约 17.9%，与有限样本下的 20% 配置相容。off 为 0 applied。
# 2026-08-03 第二部分文献与 Zotero 审计

- `7.29-8.4推进.md` 第二部分包含 7 篇：Hasan 2023、Razzaghpour 2023、Wang 2024、Wang 2025、Liu/Somarakis/Motee、Huang/Du、Hui/Zhang。
- Zotero 个人库的对应主集合为 `风险图传播/04 非最近邻信息、通信与控制`（RZCANCHR）；动态拓扑和级联碰撞还属于 `02 局部传播、级联与稳定性`，Wang 2025 还属于 `05 混合交通交互、轨迹与仿真`。
- 查重前已有 4 篇：Wang 2024（8JGE2CNE）、Liu 等（K93EDJ9H）、Huang/Du（6386KP2K）、Hui/Zhang（NMQ6PURG）。新入库 3 篇：Hasan（FEQSMN8Q）、Razzaghpour（JR9EFIT6）、Wang 2025（PBSCBRG4）。
- 已附合法全文：Hasan 大学机构库作者版、Liu 等 arXiv 作者版，以及既有本地 Wang 2025、Huang/Du、Hui/Zhang PDF。Razzaghpour 的公开预印本下载源超时；Wang 2024 未发现开放全文，二者保留题录/待补 PDF 状态。
- 公开 PDF 批量工具的失败边界：Hasan、Razzaghpour 的 IEEE 直链返回 HTTP 418；Wang 2024 没有 OA 命中；Liu 等成功命中 arXiv:2312.17147。
- Razzaghpour 2023：全分布式 ETC + MBC；各车用最近一次通信模型运行远端状态估计，仅当控制性能误差超过阈值才更新。相对 10 Hz 周期通信，模型触发平均约 1.8 Hz（通信率降低 82%），速度偏差低于 1%；阈值体现通信负载—控制误差权衡。
- Wang 2025：用运动波/Newell 跟驰知识提取 HV 的时变期望间隔与停车间距以预测轨迹，并把历史控制指令纳入 SAC 状态以补偿随机通信时延；仿真在稳定性、舒适性、能耗与振荡抑制方面优于基线，并在文中合流/分流场景报告零碰撞。
- Hui/Zhang：扩展 ARZ，以有限前视距离内的非局部平均密度表征 CAV 信息；波动分析给出稳定性条件，数值实验表明 100 m 比 15 m 和 1000 m 收敛更快，前视范围并非越大越好；示例中 20% CAV 能减小振荡，40% 收敛更快，10% 未稳定。
- Huang/Du：研究带非局部项的 LWR 标量守恒律；若核函数非增且非常数，解指数收敛到均匀流；常数核代表对远近信息等权，可能使非均匀交通波持续。结论强调近处信息权重更高、并存在合适的非局部作用范围。
- Liu/Somarakis/Motee：用时延随机线性网络描述车队间距，把既有一个或多个碰撞视为条件观测，基于条件高斯统计和 Average Value-at-Risk 给出级联碰撞风险闭式表达；推导时延/拓扑造成的可达风险下界，并比较 path、complete、p-cycle 等图。案例显示增加局部边或长程边都不必然降低级联风险，中等通信范围可更优，单次碰撞风险与级联风险的最优拓扑可能不同。
- Wang 2024（仅正式摘要层证据）：提出 DWOC，多前车跟随时获取前三辆前车动态，并按通信可用性自适应调整信息权重；推导串列稳定条件并用数值实验验证不同延迟下的稳定与安全改善。未获得全文，因此不写摘要未报告的定量幅度。

# 2026-08-03 第5—7篇详细解释证据记录

- 目标论文：Liu/Somarakis/Motee 的延迟通信级联碰撞风险、Huang/Du 的联网车辆非局部LWR稳定性、Hui/Zhang 的混合自主交通ARZ前视效应。
- 解释结构统一为：问题、概念、模型与公式、实验设计、结果、证据边界、对本课题启发。
- 采用四个审视视角：随机风险控制、非局部PDE、混合交通流、因果与实验边界。
## 2026-08-03：第5—7篇论文详细解释（阶段性核验）

- 第5篇准确题名：Liu, Somarakis, Motee, *Risk of Cascading Collisions in Network of Vehicles With Delayed Communication*，arXiv:2312.17147，后发表于 IEEE Transactions on Automatic Control，DOI: 10.1109/TAC.2025.3640000。
- 第5篇核心不是一般的“丢包仿真”，而是把车辆间距的稳态随机分布、通信时延和网络拉普拉斯谱联系起来，并在已经发生一个或多个碰撞的条件下，用条件 AVaR 衡量其他车对继续碰撞的级联风险。
- 第6篇准确题名：Huang & Du, *Stability of a Nonlocal Traffic Flow Model for Connected Vehicles*，SIAM Journal on Applied Mathematics，DOI: 10.1137/20M1355732，arXiv:2007.13915。
- 第6篇采用前向空间卷积的非局部 LWR 模型；稳定性定理依赖周期道路、线性速度—密度关系、严格正且有界的初始密度，以及非负、非增、非常数的前视权重核。常数核可保留波动，递减核可通过非局部 Poincaré 不等式导出指数衰减。
- 第7篇准确题名：Hui & Zhang, *An Anisotropic Traffic Flow Model with Look-Ahead Effect for Mixed Autonomy Traffic*，Transportation Research Record，DOI: 10.1177/03611981251381306，arXiv:2407.20554。
- 第7篇以各向异性的二阶交通流模型刻画 CAV 的有限前视平均密度，并扩展到 CAV/HDV 混合交通；理论与数值结果共同表明：更长的前视距离可放宽线性稳定条件，但不保证扰动收敛更快；CAV 渗透率的影响比其空间编组形式更显著。
- 三篇与本课题的角色不同：第5篇提供“通信—协方差—条件级联风险”的随机控制链条；第6篇提供“有限作用域+方向+核函数”的严格类超距定义；第7篇提供“有限前视+混合主体+稳定性/收敛速度”的宏观机制。三篇均未直接完成交叉口合流场景下基于消息生命周期的反事实因果验证。

### 原文细节补充

- 第5篇将“已发生碰撞”作为条件观测：两车间距的联合稳态高斯分布给出条件均值与条件方差，再将目标车对的条件距离分布代入 AVaR 型安全损失函数。它因此回答的是“观察到某处碰撞后，另一处离碰撞边界还有多远”，而不是只报一个无条件碰撞概率。
- 第5篇的数值研究包括：单一/多个既有碰撞、碰撞规模与空间分布、路径图中加边、完全图中删边、完全图/路径图/p-cycle 对比，以及通信时延与外部扰动导致的可达风险下界。原文明确显示“提高连通性不总是有益”，边的长度和既有故障分布会改变结论。
- 第6篇证明的关键机制是：递减且非常数的前视核让非局部项产生可耗散交通波的扩散效应；常数核对某些周期模式的非局部梯度实部为零，因而正弦/周期波只平移、不衰减。
- 第6篇五组数值实验分别检验钟形初值、线性初值、常数核反例、作用距离和平均密度。线性递减核下理论指数与数值指数接近；作用距离在文中测试的 0.1—0.3 范围内越大收敛越快，但理论表达式并不保证全范围单调，故结论应写为“存在合适范围”，不能写成“越远越好”。
- 第7篇明确把 CAV 的速度松弛目标从局部密度函数改为前方有限距离内的加权平均密度函数，并称这一抽象主要对应 CACC 的前视逻辑；当周期道路上的前视距离等于道路总长时，局部有限观察退化为全路观察。
- 第5篇车辆模型为二阶纵向随机动力学：位置导数为速度，速度由延迟的相对速度/相对位置反馈和各车独立白噪声共同驱动；通信图要求简单、连通、无向、加权，统一时延用于保持可解析性。研究对象是相邻车辆稳态间距，而非瞬时 TTC。
- 第7篇单类模型为非局部 ARZ：质量守恒方程不变，广义速度 `v+h(rho)` 的松弛目标改成 `V(rho_bar)`；`rho_bar` 是 `[x,x+L_D]` 前视区间上的平均密度。`L_D -> 0+` 时退化回原始 ARZ。
- 第7篇波动分析所得稳定条件可概括为 `h'(rho)+|sin(k L_D)|/(k L_D)·V'(rho)>0`。因 `V'<0`，增大 `L_D` 会减弱负项，故理论稳定域变宽；但该条件只判断小扰动是否衰减，并不等价于比较不同前视距离的收敛速度。
- 第7篇数值设定：1000 m 环形道路，时间步长 0.05 s、空间步长 5 m、松弛时间 3 s；初始密度为平衡态上的正弦扰动。比较 `L_D -> 0+、15、100、1000 m`，其中 100 m 收敛最快，15 m 与全路 1000 m 都较慢。
- 第7篇混合模型分别设 HDV/CAV 密度与速度：HDV 松弛到局部总密度对应的平衡速度，CAV 松弛到前视平均总密度对应的平衡速度；两类采用相同压力函数、松弛时间和基本图，以突出前视机制。10%/20%/40% CAV 中，10% 未稳定流动，20% 抑制到较小振荡，40% 更快收敛；均匀与集中分布的长期稳定行为接近，但集中分布初始波动更大。
- 可用于最终答复的公开主来源：第5篇 arXiv 摘要页 `https://arxiv.org/abs/2312.17147`；第6篇 SIAM 正式页 `https://epubs.siam.org/doi/10.1137/20M1355732` 与 arXiv 全文 `https://arxiv.org/html/2007.13915`；第7篇 arXiv 摘要/全文入口 `https://arxiv.org/abs/2407.20554`。第6篇 arXiv 页面还确认正式卷期为 SIAM J. Appl. Math. 82(1):221–243 (2022)。
- 第5篇将碰撞不安全集定义为间距小于 0，并用一族逐渐逼近该不安全集的阈值集合 `C_delta=(-∞, r/(delta+c))` 表示“离碰撞边界有多近”。风险值越大代表条件尾部均值越接近甚至进入碰撞区；它不是原始 AVaR 数值本身，而是由 AVaR 落入哪一级风险集合反解出的安全裕度尺度。
- 第5篇条件分布的核心式：若观测第 i 对间距为 `d*`，则第 j 对条件间距仍为高斯，条件均值 `r+rho_ij*(sigma_j/sigma_i)*(d*-r)`，条件方差 `sigma_j^2*(1-rho_ij^2)`。因此“级联”来自稳态间距的相关结构：既有碰撞改变对另一车对距离分布的判断，而不是论文显式模拟碰撞按时间依次传播。
- 第5篇图设计实验的精确结论：路径图加边时，单次碰撞风险随新增边跨度增长而持续下降，但级联碰撞风险在该案例由中等跨度边最优；完全图删去任意跨度的一条边，风险增量只局限于相关车辆且大小不随边长改变，显示出故障隔离性。

## 2026-08-08 合流源事件资格诊断

- 旧正式合流实验的20个种子中，12个形成了至少3步连续真实制动并生成/采用消息，12/12的配对效应均为负；其余8个没有形成有效源事件，效应均为0。
- 失败的8个种子中，6个源车速度为0，1个约为0.0037 m/s，1个约为6.97 m/s但只在源边完成2步制动后离开。
- 当前协调器按源边上 `x` 最大的车辆优先选择，没有源车最低速度或剩余边长资格条件，因此会把停车车辆或即将离开源边的车辆锁定为源事件主体。
- 新门槛必须在触发时根据速度和道路剩余距离判定，不得根据消息生成或后续效应筛选；全新种子必须与旧诊断种子隔离。
- Flow标准合流网中 `inflow_merge` 与 `bottom` 两条源边长度均为100 m；因此可在协调器中用 `100-x` 表示触发时剩余源边距离，不需要猜测道路几何。
- 机制日志在消息尚未形成时不会填写 payload 中的源边/源位置，因此源事件资格审计必须从触发前 state 行读取 `edge/x/speed`，不能把空 payload 字段误判为道路信息缺失。
- 新资格阶段已完成：2026081191—2026081196 全部满足最低速度与剩余距离条件，全部形成至少5步连续真实制动，全部无碰撞；源车速度范围9.013—11.309 m/s，剩余距离9.253—86.463 m，所需距离7.250—10.007 m。
- 补充锁 `source_qualification_lock.json` 已生成，哈希为 `7E4DC444DA9C44C69D6D997D6491F778FDC62801004B12C84ACB6BA2D1E92E32`；正式种子冻结为2026081101—2026081120，smoke种子为2026081182。
- 修正后的四格正式实验完成80/80次，四格平均积分TTC负担分别为：r00=0.0140147、r01=0.0140147、r10=0.0138990、r11=0.00361564。
- 意向性配对交互效应均值为`Delta_NL=-0.0102834`，bootstrap 95% CI为`[-0.0119463,-0.0082990]`，符号置换`p=9.999e-5`；18/20个种子为负、2/20为0，区间上界低于冻结的`-epsilon_merge=-0.0010993`。
- 20/20种子触发时源车均合格，r10/r11各20/20形成真实源制动；r11逐种子采用，三个控制格零采用，每个种子均满足采用先于目标轨迹分化、采用前目标轨迹一致、事件不变和无碰撞。
- 14项正式支持门槛全部通过，`supports_qualified_merge_transfer=true`。该结论支持合流场景中的非局部信息干预迁移，但合流拓扑仍存在普通物理路径，不能冒充双走廊的物理不连通证据，也不能替代真实数据外部验证。
- 理论整理冻结：类超距作用被限定为“无直接最近邻物理交互时，来源可追溯的有限时延显式消息经目标采用后改变风险，且该变化在物理路径、局部状态和指定通道反事实控制后仍可识别”；不使用超光速、无媒介或量子纠缠作为交通学结论。
- 证据分级固定为：双走廊=物理断开强证据；合流=物理连通拓扑中的机制迁移证据；真实轨迹/V2X=下一周的外部验证证据。三者不再混写。
