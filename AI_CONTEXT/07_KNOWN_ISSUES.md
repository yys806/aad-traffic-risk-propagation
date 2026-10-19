# AAD Known Issues

## 已确认问题

### KI-01 — 阶段 0.2 尚未收口

v2 便携 audit 能证明 NGSIM 生成有效跟驰测量与风险事件，但异常记录、极端值来源、最终分布和适用边界尚未完成。旧 audit 的 `pending_pneuma_and_blind_reaudit` 是迁移前原始字节；当前代码已改为 `active_audit_closure`，需要新 run 才会产生新证据。

Evidence：`evidence/results/RES-STAGE-0.2-NGSIM-V2/audit.json`、`code/src/riskprop/ngsim_risk_calibration.py`、阶段 0.2 执行记录。

### KI-02 — 阶段 0.3 正式产物已生成，科学参数未冻结

**已解决（2026-10-16）**：研究者经任务 AAD-0.3.3 批准适用范围、连续性参数（0<Δt≤0.043 s）、极端观测处理、描述阈值与 Gate=pass，阶段 0.3 已关闭（`RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3`）。遗留但归属清晰：独立物理真实性永久 `Unverified`；车型→SUMO vType 映射、时间权重抽样与覆盖阈值属 Stage 0.5 独立待决。

### KI-03 — packet 级通信证据不可用（已收束）

官方 Packet 下载端点历史 403；2026-10-16（AAD-0.4.1，日期勘误 2026-10-17）重验为 302→官方文件 API；同日（AAD-0.4.2）Range/ZIP64 在新 blob 重验可用并获取 `RSE_BSM`（`RES-STAGE-0.4-RSE-BSM-V1`）。2026-10-17（AAD-0.4.3）官方文档裁定：RxDevice≡车辆设备 ID、Gentime=生成时间（µs，1609.2）；**车辆侧接收时间在 SPMD 全家族不存在→V2V 端到端时延不可算**（结构性缺失，非下载可解）；RSE_BSM 无绝对时间与信道条件，配对 Ambiguous；其采样设计（≤2 记录方/发送方 ID、双记录对全含 10106）Unverified——接收率统计前必须查明；行为统计按 holdout 规则暂缓（4 候选隔离方案待研究者）。Gentime↔UTC 35 s 官方文档冲突待经验校准；跨设备时钟同步为残余时延类主张（仅生成→RSE 捕获）的共同未验证前置。Packet 尚未下载（Gate `pending_official_packet_access` 不变）。

**2026-10-17（AAD-0.4.8）收束**：Stage 0.4 以研究者批准的有限范围 `pass_limited` 关闭；Packet 未下载、packet_schema_evaluated 仍为 false，保留为历史边界而非当前阻断——研究者已决定不再以获得完整真实 V2V 时延/PDR/距离模型为本阶段目标。

### KI-04 — 阶段 0.5 需要重建

现有结果是职责迁移前的部分真实参考，虽未纳入 pNEUMA TTC，但来源仍指向旧 map-match 产物；SUMO calibration 样本缺失。该结果不能作为最终 coverage Gate。Stage 0.3 R2 canonical pNEUMA 参考携带逐状态质量字段，但当前 write_real_reference_package 直接列契约仍是旧 parse-view，标准化文件不能直连；按状态抽样是否保持时间加权权重属 Stage 0.5 设计决定，未冻结。详见 KI-07 和 AAD-0.5.0 审计。

当前事实（AAD-0.5.1）：V1 保留为历史包；R2 已使用正式输入 manifest 重建并完成 canonical 直连。SUMO 样本仍缺失，抽样和覆盖阈值仍未冻结。

### KI-05 — readiness 是迁移前快照

`RES-PROTOCOL-READINESS-V1` 保留旧实验键和旧 blocker，只能证明当时未就绪。阶段 0 前置项与科学容差完成后，必须用当前 `stage_X_Y` 入口重新生成；当前不允许协议锁或阶段 1.1。

### KI-06 — 当前没有训练模型

仓库没有可核验的训练循环、loss、optimizer、checkpoint 或阶段 1.1 模型。任何对“当前模型结构/训练参数”的进一步描述均为 `Unverified`，直到研究者确认设计并实现。

## 当前冲突状态

2026-09-10 发现的 pNEUMA 职责冲突已由研究者批准退役决定解决。当前没有尚待研究者决定的已知重大科研冲突。

## 冲突记录模板

未来出现重大冲突时必须逐项填写：

- `Documented Intent`
- `Actual Implementation`
- `Evidence`
- `Affected Files`
- `Conflict`
- `Status: Awaiting Researcher Decision`

## 2026-10-10 KI-01 工程问题收尾

任务 1.4 解释 936 个合并编号异常，修复过度分段及不确定记录误入可靠事件的路径。基线包：`evidence/results/RES-STAGE-0.2-TASK-1.4/`。官方两个来源时段与物理身份未证明，但字段连续性和单帧唯一匹配可独立核验，不再作为工程验收硬阻断。科学异常/极端值审计、最终事件规则与阈值仍未冻结。历史任务 1.3 连续性筛选描述已由任务 1.4 报告更正，历史文件不改写。

## 2026-10-10 KI-01 工程状态更新

跨时钟前车匹配潜在缺口已修复并通过构造测试和全量回归；真实数据无跨时钟匹配。任务 1 工程项建议关闭，官方来源时段/物理身份与科学事件口径仍为 Unverified/待后续审计。


## 2026-10-11 决策归档后仍待处理

正式提取器默认最小跨度仍为 0.1 s，而研究者已批准 P2=0.2 s；指数 rho、固定车辆/窗口、区域贡献上下界和 DID 区间实现尚缺。NGSIM 100 ms 与 SUMO 200 ms 采样语义不可直接等价。

## 2026-10-11 Formal measurement implementation status

P2 formal event extraction and rho/bounded contribution primitives are implemented in an isolated versioned module and independently revalidated to 4,545 reliable events. Historical 0.1 s extractor and linear TTC exposure remain unchanged. Target region, target cohort qualification, evaluation window, message de-duplication, and formal quality gate are still Decision Required/Unresolved; fixed-window burden has not been claimed as completed without those inputs. GitHub automatic project-integrity workflow is disabled; local validation remains required.

## 2026-10-11 一致性修复状态

正式接口的三个确定性问题已修复并回归验证。历史 0.1 s 提取器、旧线性指标和既有产物不变。目标区域/窗口等科学参数仍未决。


## 2026-10-12 Stage 0.2 综合收口（当前状态）

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。

### 论文版本冲突 — Awaiting Researcher Decision

Documented Intent：06_DECISIONS指数rho/固定分母/车辆等权。Actual Implementation：formal v2符合批准设计，旧main.tex:378-405仍为线性/观测分母/求和。Evidence：最新版20261010 PDF与最终包paper_version_conflict.md。Affected Files：paper/主论文/main.tex、paper/历史记录/20261010_YYS.pdf、06_DECISIONS。Conflict：论文版本与当前设计未同步。Status: Awaiting Researcher Decision；研究者指定正式版本，不修改论文、不替换批准算法。

### KI-07 — Stage 0.5 canonical pNEUMA 接口与覆盖协议待决

2026-10-18 场景审计确认：Stage 0.3 R2 canonical pNEUMA Parquet 使用 vehicle_id/acceleration_mps2/vehicle_type/quality_status/time_weighting_eligible；simulation_real_coverage.write_real_reference_package 直接读取 id/longitudinal_accel_mps2，并且只要发现任一质量列就访问两列。Stage 0.3 测试通过是因为脚本另建旧字段 raw_view；没有 canonical Parquet 直连测试。writer 还丢弃 vehicle_type/source_file_sha256，稳定哈希按状态抽样不保持时间权重，real-real groups 不检查独立性。报告：docs/STAGE_0_5_TASK_0_5_0_SCENARIO_DESIGN_AUDIT.md。状态：Awaiting Researcher Decision；0.5.1 前不得把接口称为端到端兼容、不得回接旧 map-match 包、不得冻结抽样和覆盖阈值。

2026-10-18 AAD-0.5.1 更新：canonical 接口、车型/质量/来源保留和正式六输入 manifest 已实现并通过测试，旧字段冲突不再是当前阻断。仍保留的科学问题是：`time_weighting_eligible` 不是时长权重；canonical 表不含逐行可靠区间长度，正式时间加权统计必须引用 Stage 0.3 封存摘要；哈希状态样本只作诊断；real-real 独立性不足；SUMO 车型映射、时间步、校准/验证隔离和覆盖阈值待 0.5.2 决定。

2026-10-18 AAD-0.5.2 更新：协议设计审计确认 `evaluate_simulation_coverage()` 的 pooled scaler、行级 real-real Energy Distance 和集合型 stratum coverage 不能直接提供科学容差。US-101 窗口隔离、五层必要指标、块级不确定性、Lankershim/pNEUMA 辅助职责及 0.5.3 输出契约仍为 Awaiting Researcher Decision；未改函数、阈值或 Gate。

2026-10-18 AAD-0.5.4-A 更新：已修复 6 项 SUMO 适配层缺陷（`global_time_ms` 曾按 incarnation 计数重置；`leader_frame_id` 曾用后车自己的帧号；`exit_reason` 曾计算后被丢弃；闭合速度资格缺 1e-3 m/s epsilon；可靠跟驰层曾错误排除非正净间距；DRAC 曾恒为 NaN）。仍未解决的**科研**缺口：批准参考文献无车型与车辆长度字段（车队组成/长度不可识别）；上游网络需求、匝道流入与 OD 不可识别；无任何层级的科学容差数值依据；仅两个校准窗口使事件率容差与密度分层容差不可分离；真实几何证据存在但不属于已批准参考文献；`tau–minGap–decel` 存在代偿方向；内部步长改变会使 P2 事件边界移动 0.2 s，故必须冻结而非优化。SUMO 正式 P2 等价性仍为 `pending_measurement_equivalence_review`（0 阻断，待研究者批准范围）。

2026-10-18 AAD-0.5.3 更新：SUMO `generic_highway_candidate` engineering fixture 与 no-message 状态链已可运行；正式网络/需求/vType/行为/时间步/暖机窗口仍未批准。已核验并修复 TraCI `getLeader` 距离语义（必须加回后车 minGap 才是物理净间距），若沿用旧值会系统性高估闭合风险、低估净间距。SUMO P2 适配因缺少 NGSIM source/member/diagnostic-clock 契约而保持 `pending_sumo_adapter_review`，formal-alignment adapter 亦为 `pending_measurement_equivalence_review`；工程 P2 不能进入正式事件率或现实覆盖 Gate。工程 baseline fixture 在高速度下未产生 TTC<2 s 连续状态（min TTC 6.971 s），说明 SUMO 默认安全跟驰在自由流条件下不会自发产生 P2 事件；P2 适配行为需由显式低速度/停驻队列工程 probe 触发，该 probe 是建模刺激、不是真实交通证据。

2026-10-18 AAD-0.5.4-A+：车型/长度字段可得缺口已补，独立物理真值/注记误差仍Unverified；摩托30/10、货车53/44有限。完整轨迹边界选择、原文件时间重叠、跨成员物理身份、局部分层P2归属均不得忽略。generic不验收真实匝道/织入/波传播。中高负载插入积压、.05s自动ballistic对照限制、完整P2成本未测；暖机和科学容差未批准。Status: Awaiting Researcher Decision。证据见补充报告、benchmark_numerical_diagnostics、candidate_protocol、cost_budget_proposal。


## 2026-10-18 B0仍未解决的准入问题

真实中/高密度状态没有被本轮实现；无法用这批自由流数据排除模型结构限制或识别低速minGap。tau2通过入口服务/安全降速改变实际车队，不能视为纯在场跟驰效应。原调度停止缺陷B0-EXEC-STOP-01已在批次后修复，旧偏差及高输入seed不足保留；最后worker峰值内存Unverified。正式warmup、局部P2归属、科学容差和现实覆盖仍未定。依据：docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md、execution_code_change_audit、机制矩阵。


B0-VALIDATION-SCOPE-02：根目录全量pytest启用了历史Stage0.2本地全源事件/案例测试，未按校准角色过滤。任务级验证读取数Unknown/Not Certified，不能声称0；B0冻结实验/比较摘要输入仍仅前两窗口，未用回归数据选参。已停止根本地数据回归，纯Git452 passed/13 skipped；任务隔离验收未Accepted，等待研究者决定是否保留有限探索结果。见validation_activity_audit及B0报告。

本轮发现但未修改：既有Stage0.1 `_sumo_environment()`版本查询无超时，一次`sumo.exe --version`挂起导致纯Git集成测试失败；精确终止后新查询正常，限时完整重跑452 passed/13 skipped。该环境/超时问题不属于B0状态生成，见test_record。

## 2026-10-19 B1未解决问题

B1（RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1）按阻断提前结束：V1失败A后7次未启动，V2 A有效/B警告/C阻断/D未启动，累计4次尝试；无补跑或新seed。A/B局部均速27.1088/26.5152m/s、密度16.3208/16.8197、低速0；C记录2.4007m/s、93.8653veh/km/lane、低速80.1719%、末期未服务252，但停车位移检查与冻结回溢资格阻断，不能作为有效校准样本。D只有静态/空加载检查，动态未知。

停车步内截断使观测终速梯形核验可能不适用，但保留信息不足以证明本次残差成因；不降低阈值。末期入口低速存在但连续50m低速前沿资格未通过，不能事后改写。C供给人工且过强、实际进入差异、D未运行、单seed、正式warmup/容差/P2局部归属均未解决。首次绘图被拒绝的4个可选系统字体路径保留，renderer改为包内字体；矩阵worker无拒绝。研究者保留B0有限描述证据，B0任务隔离false/验证物化Unknown不变。B1用两校准摘要白名单、SHA/角色守卫、-S最小胶囊、Python路径/子进程审计；冻结前45测试通过、假路径拒绝3/3，矩阵worker拒绝0；不声称OS/native全监控。根工作区不跑全量pytest，全量只在无本地历史数据的Git检出执行，数据skip不算通过。 依据：`docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md`、`evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1/`中的preflight、execution_stop_observation、numerical_stop_diagnostic、queue_diagnostics、run_manifest和SHA256SUMS。

## B1.1 剩余观测缺口（2026-10-19）

官方源码证明公开终速+平均加速度不能一般性识别步内停车；正常分支1e-6验证通过，真实停车仅必要范围检查，精确等价Pending。非决策步可观测性重建未独立验证，不能据此前停车位移反解隐藏速度。旧C最大边端点未保留、prefix10不是固定cohort，旧C具体归因仍Unresolved。

队列软件通过独立合成测试，但10m净距/2s持续/.01m精度等仅测试尺度；真实多edge坐标、域分账、lane change/释放间隙和原因证据接入仍待批准/验证。网格同格误连与严格图连接漏检风险保留。B1.2未授权；五项既有文献索引删除未处理，根严格文档检查因此受限，纯Git克隆单独验证。

## B1.1-S 停车可观测性结论与剩余缺口（2026-10-19）

已确证：非决策步的公开加速度被延续，因此`u=v0+a_pub_start*h`对任意符号精确成立，包含真实步内停车`u<0`；此分支现已独立精确核验（0.05停车例残差~6.45e-15m）。决策步`v1=0`（含`h=actionStep`时的停车步）仍被`max(u,0)`钳制，仅可范围一致，不做精确声明。因此“全部停车边精确等价”仍未成立；精确适用比例947/948，精确通过比例（仅适用边）1.0。残留盲区：一般行为决策步停车需调试构建（本次Not Attempted）；单edge微型fixture未塌lane/edge转换与多车道；实际网拓扑与域分账接入仍待验证。方案A/B准入与B1.2前置条件待研究者决定。


## 2026-10-19 B1.2 分层准入与机制再验证

B1.2首个真实fixture揭示加速度延续后近零清零适用域缺口：明确非决策步候选4.658e-6m/s与终速0不一致。固定源码4644行有条件清零；私有stop条件未仪器化。原“所有非决策步任意符号精确”不能覆盖该情形；保持终速一致性阻断，不调整1e-6m。主矩阵false；D实际换道/出口、完整队列入口持续资格未验证；压缩fixture不能代替主C。队列成员重置统计含edge转换，不等于真实换道证据。五项既有文献删除不处理。


## 2026-10-19 B1.2-N

B1.2-N正近零非决策步清零未在3个冻结微型运行中出现，C/D共同准入失败；无自动追加或放宽。一般myStopDist不可直接观测；fresh/no-stop不变量仅受限输入域充分证明。D真实换道/出口及C入口回溢仍未完成。负近零运行例不补足正例；0未决观测不表示一般上下文可识别。


## 2026-10-19 B1.2-P

新B1.2-P补足fresh/no-stop受限正近零运行覆盖；旧B1.2-N结果不改。一般停车上下文、状态恢复、特殊控制仍未验证；P3名义等号不等于实际等号，精确阈值运行边未观察到。未来准入政策、C队列/入口、D真实换道/路径/出口仍待另批；本轮不执行。1e-6m本身不能区分所有近零替代，必须独立上下文与公开速度链条。


## 2026-10-19 C/D接入

新发现及复现见issue_discovery_report.json：P1旧入口路径关联/不完整支持桥接已由独立新版本修复；P2跨edge误记换道/1Hz连续性/本轮main1-only假阻断已修复但历史保留。C入口组件至下游锚定有约14.35m>10m真实间隙，持续回溢EI，不能调阈值凑过。600s同步getter成本有超预算预测风险（未实测），需自主性能核查。局部P2归属/科学容差/评价窗口仍未决。历史protocol-readiness使用legacy标签但锁false正确，P3留存。


## 2026-10-19 LF局部探索

LF新发现：旧通用SUMO source-frame adapter会把外来identity_break/observation_gap清false，合成旧1事件/新0；仅新LF防御接口保留，原生历史无污染证据。先裁局部会丢前车/事件上下文，已防止。实际300s局部事件候选86/87/83不同，正式归属/暴露仍未决；1222个风险点1203在前120s，不能事后选暖机。600s仅预测268/642/1929s情景，未运行/未保证资源内。间隙1.001+8.12+5.23393m，keep-clear因果仍未观测；C回溢EI不影响已授权局部探索。
