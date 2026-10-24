# Stage 0.5 工作包1证据审计与非覆盖式更正

任务：[GitHub Issue #1](https://github.com/yys806/aad-traffic-risk-propagation/issues/1)。日期：2026-10-24（Asia/Shanghai）。本地和远端 `main` 基线均为 `c94e6cccb89349845b8ad905b7f65376a3c2f9c4`，开始时工作区干净。本文是审计记录；[冻结候选 v1](STAGE_0_5_ACCEPTANCE_FREEZE_CANDIDATE_V1.md) 是交接入口，**Proposed / Awaiting Researcher Decision，未正式冻结**。

## 1. 执行与证据边界

只读取两个已访问校准来源 `us101__0750_0805`、`us101__0805_0820` 的既有 canonical 状态，以及状态支持 grid/seeds/structural、到达时序 runs 中的既有测量表。未列举 temporal 轨迹目录，未重读第三窗口轨迹、locked holdout、密封数据、OB、Overleaf、WSL 或上游 DRIFT。未生成新 SUMO 轨迹，未消耗历史额度，无 ABCD、通信干预、协议锁、Stage 1.1 或下游运行。

复算入口：[audit_stage_0_5_work_package_1.py](../code/scripts/audit_stage_0_5_work_package_1.py)。独立向量实现提取完整上下文 P2，再按开始位置/时间裁切；边分母要求前后身份、前车、100 ms 时钟、可靠/可评价、两端在域且整边在窗。真实 break 字段沿用“当前行描述入边”；不把前一行 break 再抹掉后一条边。模拟缺失身份列单独标记，不能用推断补为正式等价。

```powershell
python code/scripts/audit_stage_0_5_work_package_1.py --output docs/audits/stage_0_5_wp1_v1
python code/scripts/audit_stage_0_5_work_package_1.py --output docs/audits/stage_0_5_wp1_v1 --verify
```

第一条命令拒绝已有输出目录；再次复算须指定新版本。第二条只核验，不覆盖。全量审计读取 2 份真实表、74 份既有模拟表，绑定 104 个输入。产物仅聚合表与来源信息，无原始大表、车辆/事件明细、密封键、日志或图片：

| 产物 | 用途 |
|---|---|
| [provenance.json](audits/stage_0_5_wp1_v1/provenance.json) | 逐输入路径、SHA256、字节数；源码函数行号；命令、基线、未提交状态、解释器/依赖/平台与限制 |
| [C1_exposure_events.csv](audits/stage_0_5_wp1_v1/C1_exposure_events.csv) | 逐任务/来源/运行 N、E、原点分母、边分母、归属/截断及身份资格 |
| [C2_real_candidates.csv](audits/stage_0_5_wp1_v1/C2_real_candidates.csv)、[模拟候选](audits/stage_0_5_wp1_v1/C2_simulation_candidates.csv) | 三种未批准共同分块的敏感性 |
| [C4_reference_reconciliation.json](audits/stage_0_5_wp1_v1/C4_reference_reconciliation.json) | 全采集/内部窗、权重与缺失分母的逐窗对账 |
| [C5_plan_execution.csv](audits/stage_0_5_wp1_v1/C5_plan_execution.csv) | 逐运行并列文字计划与执行规则，不重判历史结果 |
| [SHA256SUMS](audits/stage_0_5_wp1_v1/SHA256SUMS) | 本次新审计文件校验；与正式结果 `evidence/` 分开 |

`Verified Fact` 只表示计算/文件事实；`Inference` 不自动成为科学解释；`Proposal` 不构成批准；未决项明确为 `Awaiting Researcher Decision`。这些审计表不是新科学结果，不登记为 Stage Gate 结果，也不覆盖原封存包。

## 2. C1–C5 证据矩阵

### C1 — P2 暴露分母：Partially resolved

- **Documented Intent**：D1，见 [正式决定](../AI_CONTEXT/06_DECISIONS.md) 2026-10-20：先全上下文提取，再按开始归属；分母为原可评价连续 100 ms 跟驰边，两端在域、整边在窗。
- **Actual Implementation**：`stage_0_5_final_closure.py::checked/links/local_p2`（23/38/62 行）实施该真实边契约。`stage_0_5_state_support.py::block_descriptors`（800–847 行）用局部可评价点数×0.1；`stage_0_5_sumo.py::compute_sumo_measurements`（1070 行）把无前车点记作 not_applicable、但 reliable_following_eligible=false。状态 runner `run_cell`（247 行）与时序 runner `run_arrival` 直接用点分母；未调用 D1 局部边函数。
- **Evidence**：上述源码 SHA/函数行号见 provenance；既有 `seed_repeats.json`、`structural_results.json`、`run_results.json` 与本次 C1 表逐行对账。44 个原有局部 N 全部精确复现，30 个网格原记录没有局部 N，本次才作审计提取；点分母 74/74 复现。独立真实复算与正式收口 N、E、全源事件/暴露一致。
- **Affected Files/Results**：状态支持与时序两个 runner、`block_descriptors`；`RES-STAGE-0.5-STATE-SUPPORT-V1`、`RES-STAGE-0.5-ARRIVAL-TIMING-V1` 的诊断率及其报告、上下文、注册表引用。历史 LF 的 83/86/87 不属于同一归属，未改写。
- **Conflict**：点资格不等于边资格，不能据历史模拟率声称执行了 D1。模拟行在原表中既有的风险状态和身份字段仍有工程适配范围限制。
- **Status: Awaiting Researcher Decision**：分母差异的事实和数值影响已解决；生产入口修复、模拟测量等价的科学接纳仍待单独决定。本任务未改生产测量函数。

| 来源 / 结果 | N | E（veh-s） | 3600N/E | 资格 |
|---|---:|---:|---:|---|
| 0750 内部真实 [120,840) | 147 | 31051.6 | 17.042600 | 正式 D1，复现封存值 |
| 0805 内部真实 [180,840) | 216 | 33091.1 | 23.498766 | 正式 D1，复现封存值 |
| 0750 seeds，10 次 | 0–3 | 5003.1–5709.7 | 0–2.030152 | 边审计率；原点率 0–1.993908 |
| 0805 seeds，10 次 | 0–6 | 4632.8–5108.1 | 0–4.238036 | 边审计率；原点率 0–4.156644 |
| 0750 structural，2 次 | 33 | 6364.5–6401.5 | 18.558150–18.666038 | 原点率 18.177923–18.292120 |
| 0805 structural，2 次 | 32–46 | 5969.5–6336.1 | 19.298099–26.135951 | 原点率 18.758243–25.535852 |
| 0750 timing，10 次 | 1–3 | 5446.4–5636.9 | 0.640786–1.958970 | 原点率 0.629459–1.924036 |
| 0805 timing，10 次 | 1–4 | 4859.9–5691.4 | 0.637202–2.818942 | 原点率 0.626654–2.771096 |

范围表不是 CI，不池化 seed，不把范围端点当配对结果。74 份模拟中30份早期网格缺显式前车 incarnation，其 C1 `identity_evidence` 为 observed_leader_id_only_not_formal_equivalence；表内边率仅是可观察 ID 下的离线诊断，不能标正式等价。其余表也不因列存在而取得物理真实性资格。事件开始与确认分离、右侧确认越窗和未确认尾段保留在 C1 字段，不按裁切边界制造事件；位置直接取完整表事件首行，未使用历史 runner 的静默 KeyError 跳过分支。

本次发现1个未确认右删失尾段（B_het0750、seed20261204），已单列而非补零；已确认事件的确认越评价窗数为0。该记录不增加已确认事件数。

**科学/历史影响**：原“低 12–25 倍”、结构变体率接近以及时序 P2 配对幅度须携带诊断分母标签；本次未重写这些结论，也不据边率的新数值裁定模型成功/失败。正式真实参考的原 N/E 保持有效，历史边界归属数字全部保留。

### C2 — 空间分块：Partially resolved

- **Documented Intent**：真实/仿真在同构造 30 s×100 m 块上比较状态支持。
- **Actual Implementation**：`state_support::block_cloud`（213–244 行）先裁 [150,350)，再 floor(y/100)，产生 [150,200)、[200,300)、[300,350) 的 50/100/50 m 单元，统一除 100 m×5 车道。`block_descriptors` 则为整体 200 m×30 s。密度公式是 `n*0.1 / (30 * 5 * width_km)`。
- **Evidence**：原块 CSV 的首行 n=3094、k=20.626667，正好使用100m分母；实际50m应为41.253333。原全域范围 [14.52,76.10] 是旧归一化的产物。C2 两表保留逐来源/运行的候选影响。
- **Affected Files/Results**：上述函数、两个 runner、真实块云/real_domain、状态支持判定与时序复用域；整体200m均速/密度不因边块归一化自动改值。
- **Conflict**：长度与权重不相同；跨窗覆盖 0.833/0.636、第三窗公开摘要0.851不能直接升级为科学门槛。
- **Status: Awaiting Researcher Decision**：几何/公式与敏感性已核实，正式分块须由研究者选择；未修生产代码、未追认阈值。

| 候选（全为 Proposal） | 真实块数 0750/0805 | 双向覆盖 0750→0805 / 反向 | pooled k 范围 |
|---|---|---|---|
| offset100：[150,250)、[250,350) | 48/44 | 0.875000 / 0.568182 | [30.4267,79.8067] |
| global_intersection：保留全球网格、按50/100/50m | 72/66 | 0.861111 / 0.636364 | [29.0400,78.5733] |
| whole200：真实和模拟均用整个局部段 | 24/22 | 0.875000 / 0.500000 | [32.4633,72.8600] |

候选比较沿用原诊断包络算法（7.5 k带宽、2.5/97.5%），未批准该算法为正式准则；均采用 pooled覆盖≥最小双向基线，仅为统一对照。三候选 seeds均20/20、timing均20/20、structural均4/4；grid为12/30、12/30、11/30。**这些通过数不等于 C5 执行规则下的通过数**：分块与判据各自改变估计对象，不能交叉归因，不能因某选项通过数更高而选择它。

### C3 — 时距字段：Partially resolved

- **Documented Intent**：time_headway、net_gap_over_speed 表示时距。
- **Actual Implementation / Evidence**：`stage_0_5_leader_replay.py::pair_metrics`（417–467 行），先由前车位置作 gradient，closing=v_f−v_l；435–436 行为 g/closing，仅取正闭合，458–459 行却输出 `time_headway_mean_*_s`。456 行另有 `observed_time_gap_mean_s=mean(g/max(v_f,0.1))`。`trajectory_reconstruction::interaction_stats`（598–626 行）609 行也是 g/closing，625 行却写 `net_gap_over_speed_s`。两者均不是标准车头时距，亦不等于有质量/epsilon契约的正式 TTC。
- **Affected Files/Results**：重放/重建模块、其历史字段和报告消费者。Brockfeld gap误差、gap/speed NRMSE公式与这些误标字段分开，不能仅因字段错名否定全部重放指标。
- **Conflict**：字段语义可由公式唯一确定；正式主辅时距和近零速度规则尚未选定。
- **Status: Awaiting Researcher Decision**：误标事实已解决；采用哪个量、命名迁移与兼容性修复仍待授权。未静默改历史字段。

| 量 / 单位 s | 真实公式与资格 | 使用限制 |
|---|---|---|
| 净时距 | g/v_f，需声明 v_f>0 与质量规则 | 近静止不可默认为0或设任意epsilon |
| 保险杠时距（按本任务定义） | (g+L_leader)/v_f | 需要对应前车长度；不以固定平均长度冒充实测 |
| tau_eff | (Σg−n·minGap)/Σv_f；局部0<g≤80、minGap=2.5 | 比例估计，不等于 mean(g/v)，不辨识个体驾驶员参数 |
| 历史 time_headway / net_gap_over_speed | 正闭合 g/(v_f−v_l)；重放v_l为差分量 | 保留原标签作历史字段，引用时附实际公式 |
| observed_time_gap_mean_s | mean(g/max(v_f,0.1)) | 有0.1钳位的历史代理，不能当未钳位净时距 |

例：g=10m、v_f=5m/s、v_l=4m/s、L_l=4m，则净时距2s、保险杠时距2.8s、g/closing=10s；该例只解释公式。C4 复算还核对两个来源的全采集及内部窗：gap/closing分别dropna后的行索引均相同，**本两源没有观察到错位**；原函数对其他缺失模式缺少联合行筛选仍是结构性风险，不能推广为已修复。

消费者追踪：`run_stage_0_5_method_diagnostics.py` 254/260行调用pair_metrics，264行按**另一个** observed_time_gap_mean_s分层；`leader_replay::summarise`聚合该钳位时距及gap/speed误差，不聚合误标的time_headway_mean字段。`run_stage_0_5_method_expansion.py` 241/355/366/504行亦调用pair_metrics。`run_stage_0_5_trajectory_reconstruction.py` 422/449行把interaction_stats写入同名JSON，报告§6展示的是gap/closing分布，没有把net_gap_over_speed_s列成正式时距主结论。因此错误字段有明确消费者边界，不能推断所有报告的“时距”都使用了g/closing。

### C4 — 报告与机器参考：Resolved by evidence（所审计两校准源）

- **Documented Intent**：状态支持报告§1写829382条、tau_eff=1.5393/1.5687；§3均速/密度使用内部参考窗，同时写闭合−0.197/−0.128、净拉开0.537/0.530。
- **Actual Implementation**：`load_real_states`（92–109 行）先裁内部窗；`following_relation`（153–207 行）选0<g≤80；`local_summary`（120–150 行）的负闭合份额以全部局部点为分母，NaN比较为false。报告混用了全采集与内部窗。新对账精确复现两套统计，既有 `real_domain.json` 没有被修改。
- **Evidence**：C4 JSON、输入 canonical SHA（与正式收口 provenance 一致），原 report§1/§3、`real_domain.json::{windows,following_relation}`、冻结 plan 的 tau_values。所有量为逐状态等权（等间隔记录下点描述），不是车辆等权或独立交通日估计。
- **Affected Files/Results**：状态支持报告、其注册表/AI_CONTEXT历史转述及后续引用；本次以本节 erratum和活动入口提醒更正，不追写历史正文/机器产物。
- **Conflict / 关闭理由**：时间支持不一致足以唯一解释主要数值差异，无需科研选择；正式主指标是否采用其他支持域仍归R1/R3，不由本更正批准。
- **Status: Resolved by evidence**。第三窗只核查公开摘要，本节不认证其轨迹统计。拟合函数未显式加身份质量筛选的通用风险保留，不能把当前两源观察推广给未来来源。

| 来源/支持 | 拟合状态 n | tau_eff s | 闭合均值 m/s | 负闭合份额（全部点） |
|---|---:|---:|---:|---:|
| 0750 全采集 | 392478 | 1.539267782 | −0.196814504 | 0.536761486 |
| 0750 [120,840) | 312093 | 1.533904044 | −0.171375962 | 0.531175641 |
| 0805 全采集 | 436904 | 1.568675221 | −0.128307638 | 0.529760131 |
| 0805 [180,840) | 331974 | 1.606439310 | −0.109441310 | 0.523054816 |

392478+436904=829382；312093+331974=644067。全采集负闭合在去缺失分母下另为0.537735969/0.531010545；内部窗没有缺失闭合值，两种分母相同。因此“0.530/0.537”的来源/排列与统计分母必须随引用说明。冻结模型用合并内部窗 tau_eff=1.5661533927，**没有证据表明实际模型用了报告中全采集的逐窗参数**；不修改参数、模型或历史运行。

### C5 — 计划与执行判据：Partially resolved

- **Documented Intent**：冻结 `experiment_plan.json::membership_rules`：均值在 pooled包络；模拟块在同一pooled包络的覆盖≥最小双向真实覆盖；closing覆盖亦用最小双向基线；低速份额不超过最大真实块。
- **Actual Implementation**：状态 runner `_membership`（364–410 行）均值仍用pooled，但块用另一校准窗口包络和该方向基线。closing用pooled closing包络，但也换成方向基线；低速上限不变。时序 runner沿用这套方向性规则。原计划与执行分别保留。
- **Evidence**：原计划 SHA `6e19b530a0050fb5343fc3d35bacd0564b8a8802d419e38a17f4aad77960ec1e`；C5表以封存描述符重新计算两套规则，未重新挑选配置。`state_support_verdict.json::cells` 可对账实际判定。
- **Affected Files/Results**：冻结计划、两个runner、state_support_verdict、structural/seeds与时序复用、报告中状态支持和独立重复资格。
- **Conflict**：不是文字上等价的规则；若按原计划另选种子/构造，当前数据不能代替未执行运行。
- **Status: Awaiting Researcher Decision**：规则差异及反事实分类已量化；历史合规判读与未来规则选择待研究者。反事实不是重写的 verdict。

| 批次 | 按文字计划 primary | 按执行规则 primary | closing：计划/执行覆盖达标 |
|---|---:|---:|---:|
| grid 30 | 11 | 8 | 16/14 |
| seeds 20 | 20 | 20 | 20/20 |
| structural 4 | 4 | 1 | 4/4 |
| timing 20 | 20 | 20 | 19/19 |

primary 差异为3个grid（B_frozen0750/vlim10、B_mean0805/vlim8、B_het0805/vlim8）和3个structural。以上是**保持旧分块时单独比较判据**；C2候选则是另一项敏感性，不能把两表混成一个已批准规则。所有结果仍不构成科学等效。

| 其他预声明项 | 实施/证据 | 影响或限制 |
|---|---|---|
| 完整性：失败/teleport/collision停批 | grid/seeds/structural 54条、timing20条sumo记录可核对 | 历史摘要无该类失败不等于证明所有进程生命周期；未追加运行 |
| 网格执行后不扩格 | 原grid30；结构另有structural_plan、4次 | 分账，不把结构扩充写成原grid补跑 |
| 仅通过primary才重复 | 两行为×两窗共20次，按执行primary有资格 | 按原计划还会有其他候选；未运行的反事实重复Unknown |
| 独立seed角色 | grid=20261201；repeat=20261201…05 | 五个不同seed中一个已用于构造；不是五个未接触验证seed |
| temporal先freeze | manifest含四文件SHA；入口570–576行只查frozen_files | 不重读第三窗轨迹；公开temporal摘要与manifest指针保留 |
| 源码SHA | 模块SHA与manifest一致；当前runner `832634d5…` ≠ manifest `6bf8d25b…` | 已有报告记能力上报修复和列适配，但没有完整冻结源码快照可唯一还原所有差异；严格源码冻结合规Unknown，不能仅凭记载宣称完全一致 |
| 冻结历史说明 | 报告§11记列适配后重写manifest；`step_temporal`未查source_sha256 | 原记录保留；未来需同时核验源/配置/统计及条件输入角色 |

## 3. R4 运行账本：按授权分账，不转移余额

| 授权任务 / 原证据 | 已用、失败、停止与保留 | 本任务可用额度 |
|---|---|---|
| B0：EXPLORATORY-RESPONSE execution_ledger | 19/23 completed；3个工程blocker；调度器未自动停，人工停；4次未运行 | 0 |
| B1：BOUNDARY-BOTTLENECK V1及其旧ledger | 旧A失败后停止；新版A/B/C三次，C阻断、D未运行；合计4次尝试 | 0 |
| B1.1 / B1.1-S | STOPPING-SPILLBACK 4个微fixture（3个warning）；STOPPING-OBSERVABILITY 3个完成 | 0 |
| B1.2 / N / P | BOUNDARY-BOTTLENECK-R2 C接入阻断1、D/主8未运行；NEAR-ZERO N1–N3三次，C/D未启动；POSITIVE-NEAR-ZERO五次完成 | 0 |
| CD-INTEGRATION | v1 D微运行阻断，v2 C完成warning；2次接入用完；定向0/8另池 | 0 |
| LF → FINAL-CLOSURE | LF1/2/3占3/8；FC1/FC2再2次，warning/状态不足；累计5/8，剩3=1构造+至少2独立重复；FR1/FR2未运行；4次空网smoke单记 | 0；原3保留 |
| TRAJECTORY-RECONSTRUCTION | RC1/2/3三次；冻结状态支持失败停止；原RC1r/RC2r未执行（ledger还列RC3r候选，不能凭列名多出许可） | 0 |
| METHOD-DIAGNOSTICS | 计划48；machine budget_used/executed=43、26条失败记录；报告又称48次进程，primary/secondary插入尝试存在 | 0；确切原进程总次数Evidence Insufficient，不把43指标数或48预算当已核实进程数 |
| METHOD-EXPANSION | response_summary：324/324，failures=[]；初始化/新Newell等独立诊断见各plan，不并入324或剩3 | 0 |
| STATE-SUPPORT | 30 grid+20 repeats+4 structural+4 temporal=58，独立授权；五seed含构造seed | 0 |
| ARRIVAL-TIMING | plan budget=20；run_results20；工程摘要无失败，主线可施加性失败另报 | 0 |
| 本Issue | 2真实+74模拟既有表离线读取；新轨迹0、预算消耗0 | 0 |

账本以 `evidence/results/RES-STAGE-0.5-*/` 的对应 execution_ledger、budget_audit、candidate_run_ledger、scene_run_ledger、budget_ledger_audit、response_summary、grid_results、seed_repeats、structural_results、temporal_validation、run_results 为源；均由项目便携清单核验，未覆盖。跨任务数据角色、同seed延长/重放和独立重复不可池化。本表不发放未来许可，也不修补历史不确定账本。

## 4. 结论影响与交接

可以关闭的是：C4所审计两个校准源的报告支持域混用解释、C3错误标签的实际公式、C1真实N/E和既有模拟N/点E复现、C2几何错误与候选影响、C5计划/执行差异的量化。仍待决定的是：正式共同支持、时距主辅/低速规则、模拟边测量接纳与生产修复、计划偏离的合规处理，以及R1–R5。当前“唯一剩余阻断是交互相容”的历史概括不足以表示正式准入状态；测量/支持/计划一致性同样必须先解决。

**Gate=`pending_simulation_sample`；scientific_claim_eligible=false；reality_coverage_accepted=false；protocol_lock_allowed=false；stage_1_1_allowed=false。** 既有Stage0.2/0.3/0.4有限验收、历史失败与所有产物不变。冻结候选不是Protocol Lock，无科学结论获批。

## 5. 验证记录

具体命令、通过/排除/跳过、提交前与提交后纯Git复核记录见 [本任务验证记录](STAGE_0_5_WP1_VALIDATION.md)。初次复算因早期grid缺leader_incarnation列而停止；识别schema差异、显式降级身份资格后重新完成，失败未生成封存目录。首次合成测试6 passed/1 setup error（独立临时父目录不存在），建立父目录后7 passed；没有修改测试期望以绕过失败。
