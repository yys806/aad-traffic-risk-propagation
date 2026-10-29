# Stage 0.5 第二轮后离线机制诊断与 P2/D1 核验

任务：AAD-S0.5-POST-R2-TASK1-20261029；日期：2026-10-29。
输入版本：d698d9d64c2acb8fa31c3841a08d22d129353cf5 = origin/main。诊断代码与输入逐文件SHA见[机器诊断](../evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/diagnostic.json)及[运行记录](../evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/run_record.json)。

本任务新SUMO进程 **0**、TraCI连接 **0**、新轨迹 **0**、holdout读取 **0**、依赖安装 **0**。正式测量实现、配置、研究空间、cohort、Rule A、科学Gate不变。历史Round2的一次运行不是本任务新启动。

## Observation

### 输入、生产重建与封存交叉验证

仅用已接受的 WEEK_0750_B00_IC1_s20261201_A03 和 AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1。源区固定main_0映射主线1–5、y[0,150)m；目标区主线1–5、y[150,350)m；窗口[120,390)s；处理前C_INPUT_ROUTE=1112 IDs；辅助车道独立。

| 输入 | B00 A03 SHA256 | minGap=1候选 SHA256 |
|---|---|---|
| fcd.xml | 1dc274082f4ea14949979d0c925903bbb5b9668d1124dabb79799b59a55fa304 | 434f1c2500cdf06d069d7eae1c86e064ad76af61f478379943bbefab70b2ac3e |
| measured_state.parquet | 48b20ff458ff1dce4559a762d6965b6747a940d537b1460d74e33d739a3cf63a | 31426640954e6e8ea883f82dce139df130d7f83a8db4300ceb38842d4ee716b8 |

原始运行目录为code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/下对应run_id。网络、路线、配置、身份日志、D1、isolation receipt路径及SHA全列于diagnostic.json的runs.*.inputs。原始封存回执声明的artifact hashes实际重算一致；Parquet实算SHA与Round2最终对照一致。

本环境无pyarrow/fastparquet，不解码Parquet、不安装依赖。直接复用生产assess_capsule的 **parse_fcd → fcd_to_state_frame → measure_state_frame → local_d1_measurement**，不是另一套风险计算器。逐臂断言封存source_all/target_cohort的计数、质量组成、事件起止/身份/成员数、D1 links/暴露、未确认候选、右删失状态，均一致。场景标签参与事件哈希，故不以重算event_id替换封存ID；科学相关成员属性单独核对，原事件/member SHA留在父包。

坐标使用建成网络长度的逆比例映射，**不能以FCD x/y或原生pos直接代替研究y**；main_1_0映射lane6辅助车道。解析全量610725/645369条状态；各4200个完整记录时刻（0至419.9s）；重复车辆时钟0；同车记录>0.11s缺口0；各8401条身份日志链核验通过。

### 正式定义与实际接口逐项对照

依据：[正式配置](../code/configs/stage_0_2_formal_risk_measurement_p2_v1.json)、[正式事件实现](../code/src/riskprop/formal_risk_measurement.py)、[SUMO测量/适配器](../code/src/riskprop/stage_0_5_sumo.py)、[D1](../code/src/riskprop/stage_0_5_d1_measurement.py)、[生产调用](../code/scripts/stage_0_5_acceptance_v3.py)。已有[边界矩阵](../evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/existing_boundary_matrix.json)与[等价性矩阵](../evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/existing_equivalence_matrix.json)按当前源码导出；单项Equivalent/Verified不代表总体科学认可。

| 字段 | 正式定义 | 实际实现 | 已有验证 | 未解决差异、影响 | 建议 |
|---|---|---|---|---|---|
| TTC/方向/单位 | 正净距、正闭合；秒 | compute_sumo_measurements: closing=后车速−前车速；gap>0、closing>0.001m/s、finite、leader可解析；TTC=gap/closing | closing epsilon、非闭合、非正距测试 | 0.001是已有数值容差，非新科学阈值；真实测量误差等价性未认可 | 计算规则可核实 |
| 净间距 | 前车尾至后车前，m | 当前胶囊同native_lane的leader_pos−leader_length−follower_pos，不用映射y求距 | 既有物理坐标测试、全量分布 | 不重建跨edge/lane前车；通用TraCI距离说明不代表本次调用getLeader | 边界保留missing |
| 阈值 | 0<TTC<2s | D1显式检查正值、valid、可靠；native _risk_mask信任ttc_valid，未再检查正值/status | 原边界矩阵、本轮负TTC反例 | 不一致预测量输入可使native生成事件；formal拒绝non-risk member；生产compute禁止有效非正TTC | 接口契约缺口，不是本源零事件的已证原因 |
| 持续时间 | 首末观测跨度≥0.2s | 三接口按跨度，D1带1e-9比较容差 | exactly/below minimum | 成员数×0.1不是跨度；三帧才可能0.2s | 可核实 |
| 确认时刻 | 首个实际观测满足持续门槛 | native取实际成员；formal复用observed_confirmation_time；D1同观测时钟 | 既有因果确认、迟入/warmup测试 | onset、confirmation、message、物理arrival不同 | 物理到达Unknown |
| cadence/max gap | 100ms；maxgap0.11s | native要求0.1±1e-6；D1要求0.1±1e-9且100ms网格；formal检查frame/clock | missing-frame/非标准cadence、全量FCD grid | ≤0.11不等于任意间隔均可；数值容差不完全一致 | 当前grid满足；一般等价性需审查 |
| follower/leader身份 | 连续pair、incarnation、run/source作用域 | D1按run/scenario/follower/incarnation排序；leader ID与incarnation均相同；native检查incarnation及已知ID | identity/leader switch、两臂生命周期 | FCD重建incarnation=vehicle ID别名，非通用重入身份算法 | 当前生命周期核验不外推一般等价 |
| flags、row/frame | 不跨identity_break/observation_gap；clock/原始row可信 | native/D1检查两端；build_sumo_formal_source_frame重编号并将两flag和identity_uncertain置false | 既有身份测试、本轮显式flag反例 | 显式中断可在formal映射丢失，影响事件与暴露 | 记录冲突，待契约裁决；不改正式实现 |
| native lane | 已批准物理路径需真实车道/连接见证 | D1邻接额外要求native_lane相同；native/formal一般不检查 | lane-change反例：1/1/0 | D1保守切断与通用P2不等价；影响事件/暴露；换道不等于不可达 | 分开定义接口，跨连接仍Unknown |
| 空间归属 | 固定主线1–5、半开源/目标范围 | D1全上下文提取后按onset归属；confirmation/全程位置另列 | 区域/left continuation测试、目标局部逐帧 | 全量事件表不是正式源/目标计数；数组可含onset_inside=false | 用onset_events；辅助事件独立 |
| 窗口/原点 | [120,390)s；时钟各有来源原点 | D1 onset半开窗，可用窗后confirmation上下文；formal用absolute ms | warmup/late-entry/window测试 | 仿真absolute秒不等于NGSIM原absolute时刻 | 仅同口径持续/相对时钟可比 |
| missing/无前车 | 未知不补零；真实无前车可not_applicable | core无前车not_applicable且不可靠；state_support把无同lane successor标unresolved_lane_boundary/missing | no-leader/质量测试、本轮完整missing reason统计 | 本次57798/65376个not_applicable为可靠非闭合，不是没有前车 | 边界missing的真实TTC仍Unknown |
| invalid | 非正gap/无效观测不作风险 | core非正距标invalid；D1仅valid/not_applicable入合格边 | 原非正距/布尔契约测试 | 本源invalid=0不表示全部物理风险可见 | 限定结论范围 |
| 暴露/率/零事件 | 可靠且P2可评价的相邻边 | D1两端可靠、质量、区内、clock合格才累加0.1；非闭合仍入分母；rate=3600n/E | 原exposure测试、源E精确复现 | compute_exposure没有D1额外lane/region条件；点数×0.1非D1；E>0不证明missing安全 | 条件观测率，不是总体风险为0 |
| 右删失/事件结束 | 未满0.2未确认；右删失、前车切换、阈值退出区分 | D1有observed_short/right_censored_unconfirmed，但完成事件无exit_reason；native/formal有exit vocabulary | 原right-censored测试、本轮目标272.2s行 | D1单独不能说明所有结束原因；末端之后未知 | 后继观测单列诊断，不补写正式事件 |
| rho | exp(−TTC/15.364279197080283)，无事件阈值截断 | formal rho_from_ttc；不参与P2身份 | 原指数映射测试 | rho一致不证明事件/暴露/路径等价 | 不变 |
| 总体等价性 | 身份/时间/质量/暴露真实参考证据与正式认可 | D1 formal_equivalence_accepted=false；aligned formal_comparability=false | 旧矩阵pending、本轮反例与真实重建 | 工程Pass、定义一致、科学等价是三件事 | 不升级状态 |

[新增三帧反例](../evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/adapter_counterexamples.json)均无原生启动。按native/formal-aligned/D1顺序：clean=1/1/1；native_lane_change=1/1/0；identity_break和observation_gap各0/1/0；人为负TTC且ttc_valid=true时1/抛non-risk event member/0。**接口对任意预测量输入不等价**；不说明封存轨迹含这些不一致输入，不授权改变正式定义。

### 源区风险分布与暴露

源区所有观测均在固定1112-ID cohort内（实际观察到566/598辆）。暴露来自完整上下文合格边。

| 指标 | B00 A03 | minGap=1 |
|---|---:|---:|
| 源区状态 | 86234 | 91058 |
| valid / not_applicable / missing / invalid | 27375 / 57798 / 1061 / 0 | 24273 / 65376 / 1409 / 0 |
| 可靠可评价点 | 85173 | 89649 |
| D1 links / exposure veh-s | 84574 / 8457.4 | 89000 / 8900.0 |
| 有效TTC状态 | 27375 | 24273 |
| 0<TTC<2状态 / 片段 / 源onset | 0 / 0 / 0 | 0 / 0 / 0 |
| [2,3)s诊断状态 / 片段 | 30 / 4 | 29 / 3 |
| TTC min / p01 / p05 / median s | 2.157878 / 6.015302 / 10.184617 / 35.865455 | 2.673198 / 6.044330 / 8.738633 / 26.819394 |
| 净距mean / median / p05 m | 18.142418 / 15.4504 / 5.1604 | 17.056262 / 13.5204 / 3.3704 |
| closing mean / p95 m/s | −1.358493 / 1.33 | −1.519599 / 1.22 |
| speed mean / SD m/s | 8.306833 / 4.252149 | 8.327291 / 4.698094 |
| speed<5m/s份额 | 0.240903 | 0.316853 |
| 缺失点占比 | 1.2304% | 1.5474% |
| 已观察短正式风险段 / 右删失未确认 | 0 / 0 | 0 / 0 |
| 条件源事件率/可评价vehicle-hour | 0 | 0 |

valid是可靠闭合正TTC，不等于所有可评价跟驰。候选gap更小、TTC中位下降、低速和离散增加，但min TTC反而升高；正闭合数量27375→24273。源平均closing均负。不能仅凭gap收紧、平均速度相似推断源风险增强。

完整9×3（30s×50m）源诊断块的计数、质量、风险/近阈值、分布和完整上下文D1见diagnostic.json的source_blocks；[54格扁平索引](../evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/source_time_space_blocks.csv)保留计数/暴露。50m只作非权威诊断；分格D1之和不必等于全源D1，因为跨格边不进入任一分格。

沿用封存Rule A：候选PASS、speed/closing均18/18块；B00 PASS、分别18/18和15/18。原cross-window最低覆盖0.63636不变。本轮不重跑Rule A、不加阈值。**该Rule A是既定目标区支持判据，不是新增的源区所有分布真实等价验收**。

### 全部近阈值片段与未成事件原因

| arm | follower→leader | native lane | onset–end s | 起–止y m | 观测数/跨度s | min TTC s |
|---|---|---|---|---|---|---|
| B00 | m00421→m00395 | main_0_1 | 230.6–231.0 | 85.404–89.776 | 5 / 0.4 | 2.169926 |
| B00 | m00616→m00545 | main_0_1 | 324.2–324.4 | 86.489–89.960 | 3 / 0.2 | 2.822742 |
| B00 | m00636→m00631 | main_0_1 | 334.0–335.2 | 96.101–108.013 | 13 / 1.2 | 2.498345 |
| B00 | m00691→m00615 | main_0_1 | 362.4–363.2 | 99.432–107.991 | 9 / 0.8 | 2.157878 |
| 候选 | m00315→m00310 | main_0_0 | 168.3–168.3 | 146.169–146.169 | 1 / 0 | 2.971538 |
| 候选 | m00466→m00410 | main_0_1 | 235.7–236.6 | 118.689–132.966 | 10 / 0.9 | 2.673198 |
| 候选 | m00626→m00560 | main_0_1 | 311.0–312.7 | 122.996–147.710 | 18 / 1.7 | 2.831874 |

七段每帧valid、pair/lane/time连续，均以下帧退出诊断band结束。**全部TTC≥2，跨度再长也不构成正式P2**。没有观察到任何源正式风险阈值内状态，所以没有被持续性、前车切换或clock gap阻断的已观察正式风险候选。未确认列表为空来自全量核验。逐段质量/身份/失败原因见两臂source_segments.csv。

### 观测、身份与可识别性

源missing全部为unresolved_lane_boundary（1061/1409点），未补零。所有FCD ID在1150声明中；每个已观察ID首末FCD与实际departure和identity summary一致，日志链有效。B00 857 arrived+148 active+145 pending；候选904+158+88。pending不是已观察安全车。FCD incarnation=vehicle ID的适用范围只限当前生命周期证据，不认可一般重入语义。

源当前点相对前一点的非互斥邻接失败：B00 same-follower/clock=534/534、same-leader=1658、same-native-lane=553；候选565/565、2058、589。**不是534/565个丢帧**：包括同车第一帧/排序分组边界；全量同车真实>0.11s缺口0。区域进入、换前车、换道不等于数据丢失。

可确认“可靠可评价支持内无源阈值命中”；不能确认整个源物理空间没有风险。跨连接leader、边界missing的真实TTC与100ms观测间风险仍Unknown，无新数据填补。

### 目标事件有限审查

候选m00485→r00036是唯一目标cohort事件：onset271.8、confirmation272.0、end272.1s，4帧/0.3s；起点y189.904025m，native main_1_1→lane5，完整段在目标、cohort和窗口中。四帧TTC=1.114656、1.229541、1.409318、1.693723s；gap2.9204→2.3204m，closing2.62→1.37m/s。272.2s仍同pair/lane、TTC2.232727s，故局部证据支持**阈值退出**，非该段右删失；D1原事件不补写exit_reason。

[局部上下文](../evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/Round2_minGap1.0_target_event_context.csv)显示r00036在271.7s位于main_1_0辅助lane6，271.8s进入main_1_1；m00485此前leader为m00480，onset时变为r00036。事件从切换后新pair起算，没有拼入切换前时间。车道/leader变化是Observation；“变道导致事件”仍是缺反事实的Hypothesis。辅助位置仅作局部上下文，辅助事件未混入主线正式数。

该onset距源上界约39.9m，非源事件；没有合格源P2可作传播锚。拓扑、leader切换、272.0s最早消息时刻均不是源事件影响到达见证。**事件特定路径/物理到达Unknown，不是已证明不可达**。

### 证据索引一致性及失败保留

父candidate_result.json、acceptance_matrix.json、decision_matrix.json保留各自启动前状态和原字节。[最终索引](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/final_result_index.json)明确标prelaunch snapshot并指向[execution_final_v1](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/execution_final_v1/)，不以旧NOT_RUN覆盖最终已执行结果。

独立核验发现父manifest的execution_final_v1/validation_record.json哈希过时，父SHA仍有旧child manifest/validation哈希；**子包本身15个payload/16条SHA通过**。旧父控制文件完整保存在本诊断包prior_round2_manifest.json、prior_round2_SHA256SUMS.txt；漂移见prior_round2_manifest_drift.json。只新增导航、重封父清单，未覆盖科学JSON/轨迹/失败；[修复后独立核验](../evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/prior_packages_independent_verification.json)区分父包和未改子包。

早期手写坐标诊断源状态错为92525/97252，已标INVALID_SUPERSEDED、保存脚本/产物SHA和本地路径；最终生产重建精确回到86234/91058。负TTC探针初次抛错、临时目录权限、父manifest过时等见[开发失败记录](../evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/development_failure_record.json)。指定的辅助路线图已按唯一授权文件路径只读核验；其“第二轮无源P2即停止、第三轮条件执行”与本结论一致。仅作辅助上下文，不作为新批准；实际SHA及逐项核对见[路线图核验](../evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/authorized_roadmap_check.json)，未扫描私人目录或复制笔记正文。

### 验证与重现

[诊断脚本](../code/scripts/analyze_stage_0_5_post_r2_offline_diagnostic.py)拒绝子进程和网络；[独立验证器](../code/scripts/verify_stage_0_5_post_r2_offline_diagnostic.py)只读哈希、不导入测量。重现命令（新输出目录）：

~~~powershell
python code/scripts/analyze_stage_0_5_post_r2_offline_diagnostic.py --repo-root . --output code/outputs/diagnostics/post_r2_reproduction
python code/scripts/verify_stage_0_5_post_r2_offline_diagnostic.py --repo-root . --package evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029 --raw-inputs
~~~

完整离线回归 **1415 passed、28 failed、4 skipped、7原生测试排除**。27项traceback明确缺Parquet engine；另1项先报缺manifest，实际子CLI failure ledger确认同一ImportError，回执已保存，非推测归因。traci不是这28项的归因。**全量回归未通过**，没有安装依赖或伪称Pass。首次定向34pass/1临时目录权限error保留；换可写目录后82pass/3项Parquet失败保留。最终新代码纯离线定向、docs、compile、哈希和纯Git验证的真实结果见validation_record.json；历史35失败未充当本轮结果。

源码SHA、环境、逐测试traceback、原失败回执、精确命令与清单在机器包；不复制大轨迹。manifest无自引用；SHA含manifest、不含自身；独立核验覆盖全payload/大小/哈希、原始输入及计数等式。

## Interpretation

| 情况 | 支持 | 反对/限定 | 判定 |
|---|---|---|---|
| A：无接近阈值有效状态 | 正式TTC<2命中为0 | 有30/29个[2,3)近阈值状态，故“完全没接近”不成立 | 狭义无正式命中Verified，绝无近阈值不成立 |
| B：短风险未成事件 | 近阈值段存在，部分跨度>0.2s | 一帧正式风险都没有；短正式段/未确认/右删失0 | 支持近阈值存在，不支持持续性为主要瓶颈 |
| C：关键测量差异 | lane、flags、预测量质量契约反例；科学认可false | 差异不能解释当前源0：可靠TTC本身未<2 | 一般契约/等价性缺口成立，不是本零事件已证原因 |
| D：观测不可识别 | 1.23%/1.55%边界missing、采样间与跨连接未知 | 正D1支持、完整时钟及当前生命周期一致 | 局部Unknown成立，不能说全部无支持 |

在**当前可评价支持**中，更接近“单因素未产生足够强的源风险交互”，而非“已有源风险被0.2s门槛排除”。这只是固定一次运行的有限解释，不是一般机制假设获证。科学等价性仍独立阻断，不因计数重现获得批准。

## Proposal

最小有价值动作：**独立的离线测量输入契约裁决与验证**。用本轮反例明确通用pair-P2与D1同native-lane保守切断的关系、显式flags保真、真实生命周期incarnation、边界leader不可观测及真实参考质量/暴露crosswalk。先裁决预期，若需改实现另行授权；不先开新seed、重做minGap搜索。

复用Round1已验收的324微观、58状态支持、到达时序、初始化、leader replay和瓶颈结论，不重算/重跑历史。局部跟驰误差改善≠网络源P2、宏观支持≠尾部风险真实、拓扑可达≠事件物理到达的边界继续成立。研究者若继续机制设计，应针对源gap与closing联合不足提出新假设，并约束真实源区交互支持；不要重跑同seed失败候选、改阈值或事后挪空间。

引用入口：[Round1最终决策](STAGE_0_5_ROUND1_FINAL_DECISION.md)、[已验收第一轮审计](STAGE_0_5_FIRST_ROUND_OFFLINE_DECISION_20261028.md)、[R1机制审计](STAGE_0_5_OFFLINE_MECHANISM_AUDIT_2026-10-28.md)。[2026-10-21定义一致性报告](STAGE_0_5_FORMAL_RISK_DEFINITION_CONSISTENCY.md)只作为当时的实现/决策历史，不把其中旧paper路径当成当前Overleaf论文或当前测量等价性批准。

## Awaiting Researcher Decision

| 决策 | 最小明确事项 | 本轮状态 |
|---|---|---|
| P2/D1科学等价性 | 通用pair与D1车道规则、flags保真、incarnation及真实参考质量/暴露证据 | false不变，本轮不批准 |
| 下一步源机制 | 是否在测量补缺后另提新假设；保留当前单因素源零结果 | Proposal，无新实验授权 |
| 观测识别性 | 是否及如何补跨连接/边界见证；不可用连通替代影响 | Unknown，未判不可达 |

不重新索要已批准Rule A/研究空间；全部原样复用。没有独立seed、第三轮或Stage I的默示授权。

## Blocked / Unresolved

1. formal_equivalence_accepted=false。最小缺口：输入契约/连续性语义裁决、真实参考身份/质量/暴露适用证据、正式科学认可；不是再比较一次合成事件数。
2. 固定源P2仍0，既定独立确认前提不满足；不自动进入第三轮。
3. 缺失段、跨连接和100ms采样间风险、源到目标事件特定物理路径/到达仍Unknown；现有封存文件不能填补或证明无风险。
4. 全量回归28失败按各自证据保留；本轮不安装依赖、不改无关历史测试。新代码定向与全量结果分别报告。
5. Stage 0.5 Gate、Stage 0.6 δ/h/B、Protocol Lock、Stage I不提升。离线诊断完成不等于科学验收通过。
