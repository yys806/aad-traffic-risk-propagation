# AAD Known Issues

## Current — 2026-10-28 first-round evidence-consistency repair

Verified: B11 event classification and package hash evidence were corrected. Remaining blockers are scientific source support and environment dependencies for parquet-based regression (`pyarrow`/`fastparquet` absent); no test was allowed to start SUMO or TraCI.

## Historical — 2026-10-28 R0 offline design packet（任务标签；实际准备2026-10-27起）

Verified：A03完整可评价上下文正式P2=0，无现成源事件见证；边界/连接84227点缺失不能补零。归档物理路径helper跨1s时间缺口且有前向道路早拒，不可直接当合格影响到达；本轮未修改科学实现，候选连续身份/链路规则待研究者决定。R1未放行，Stage0.5科学交互Gate仍blocked。 证据：evidence/results/RES-STAGE-0.5-R0-DESIGN-PACKET-20261028/；审查报告：docs/plans/2026-10-28-stage-0-5-r0-design-freeze.md。

## 2026-10-27 Weekly B00 accepted; Stage I remains BLOCKED

Verified: A03 completed420s/8400native steps, independent receipt and all8 measurement checks Pass; B00_EXECUTED_MEASUREMENT_ACCEPTED. This task had3 real B00 starts: A01/A02 resource-coverage failures retained; A03 sealed trajectory independently remeasured with zero new launches after a coordinator import fix.1150declared=1005inserted+145native pending;857arrived/148active; collision/teleport/discard0 with complete required observation.18/18state/D1 support, E=9778.4veh-s, localP2=0. Final isolated software:1386passed/17skipped/7native excluded; audit denied0/SUMO0; compileall/docs/hash Pass. Scientific interaction Gate blocked; numerical budget/protocol candidate are Proposed, StageI BLOCKED. Historical Not Accepted unchanged. Evidence: docs/AAD_WEEK_TO_STAGE_I_2026-10-27.md; evidence/results/RES-AAD-WEEK-20261027-V1/; evidence/results/RES-STAGE-0.6-WEEK-20261027-V1/. Older blocks below retain their historical time points.

Remaining material blockers: absent local source P2 support; scientifically valid minimal source/intervention contract; endpoint/SESOI/scope adoption; real paired dynamic error and pilot variance/split. Legal pending is reported rather than an automatic failure. A03 historical ledger rejection remains; independent postrun certificate is current measurement authority.

## 2026-10-27 B00已真实启动：BLOCKED_BY_VERIFIED_HARD_FAILURE

Verified：ENG-01/02/03修复、无数据全量1361通过/16跳过/7原生排除、compileall、修复后3s原生集成及独立回执Pass；纯Git定向165通过。新candidate-v8及聊天来源授权、实时硬检查完成后已直接执行一次B00（版本/仿真/真实TraCI各1）。最终状态BLOCKED_BY_VERIFIED_HARD_FAILURE：首个simulationStep发生i0007_i0007 slow lane ahead原生Error；冻结输入为15.23m/s、位置233.91m，下游main_2限速10m/s，按既定停止规则终止，420s未完成。仅t=0初始身份快照有效，末态插入/pending/discarded及全程碰撞/teleport均Unknown；三XML截断，18格测量不验收。capsule退出1，SUMO退出码未成功观测；后代已清理且无残留PID。未重复相同失败。具体初态/下游限速/原生Error停止规则冲突需科研决定，不能伪装成工程修复。旧Not Accepted及Gate不变。依据：docs/STAGE_0_5_B00_CLOSURE_2026-10-27.md；evidence/results/RES-STAGE-0.5-B00-NATIVE-V1/。下方为历史时点。

## 2026-10-27 B00科研准入审查V1（高优先级未决）

ENG-01：technical_preflight_v4检查证书true而未检查研究policy accepted_build=false；V4绕过legacy/profile显示锁，后续reserve/running/launch_attempt在controller.verify_live_context晚拒绝之前，形成ready与实际可执行性不一致。属于fail-closed/副作用顺序风险，未证实未授权执行。ENG-02：collect_snapshot碰撞接口异常保存None，run_observation_loop却or 0，finish六类身份完整性不含碰撞；需另任务补缺失拒绝。ENG-03：verify_receipt只核summary封存/根，assess_capsule不作summary与逐车总量对账；原生pending可核算完整但未插入，初态插入/删失科学接受政策须先决定。当前精确候选不改，建议暂缓可执行批准；任何守卫/策略变化均需新绑定。本轮仅报告，不修改代码/科研审批/硬锁或历史事故。Git dirty为生成时点，38源/347文件及既定CRLF检出有双哈希证据；精确JSON字段检查依赖真实人类决策来源。详见主审查报告及authorization_boundary_audit.json；科研待决、动态行为unknown，0新轨迹。下方为历史时点。

## 2026-10-27 B00 candidate-v6 工程准入（Verified / 待研究者审批）

新增不可覆盖 candidate-v6，独立复核347份封存文件、原生产 verify_receipt Pass、12源闭包/8031运行时文件及B00输入/支持/18测量参考/资源策略精确绑定。静态预检仅保留实时检查要求；当前无SUMO的完整Linux技术预检 technical_errors=[]、ready=true、READY_FOR_RESEARCHER_APPROVAL。proposal SHA=b43e2d3af03dd53dd23bee3abd027725f298f58c97a2ae73d868ca9168a229b3。工程证书的accepted仅表示静态输入/资源资格与工程链，不证明B00实际插入、测量支持或科学效应。科研execution_allowed/researcher_confirmed/protocol_frozen及profile accepted_for_new_task仍false，native_launch_locked=true，旧B00 policy accepted_build=false硬锁保留；没有科研授权迁移。candidate-v5/历史失败/SMOKE归档原字节保留，历史Not Accepted、Gate/δ/h/B/Stage1.1不变。本任务SUMO0/真实TraCI0/新B00轨迹0。依据：docs/STAGE_0_5_B00_ADMISSION_V6_2026-10-27.md；docs/audits/stage_0_5_ready_to_admit_v3/candidate-v6/；evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/technical_preflight.json。下方为历史时点。

## 2026-10-26 辅助流程修复、合成smoke已Pass（最新）

可选sysctl/已有审计目录/固定输出路径/GBK日志问题已由新辅助工具修复；额外历史host namespace ID相等假设也已纠正为实际新namespace分离。当前完整实时验收及唯一原生smoke均Pass，旧失败证据保留。B00/candidate-v5仍未准入，四false、实际研究初始化/i0007/交互相容/历史Not Accepted及科研Gate未解决、不自动升级。依据：`docs/STAGE_0_5_V4_SMOKE_3_CONTINUATION_2026-10-26.md`；下方为历史时点。

## 2026-10-26 smoke 3预检辅助脚本问题（最新）

任务级helper把`/proc/sys/kernel/unprivileged_userns_clone`当必需文件，当前WSL不暴露该可选路径，触发FileNotFoundError。该错误不证明内核无userns能力；剩余实时隔离/资源检查未完成，PRELAUNCH BLOCKED。按本次任务停止规则未修后重跑、未生成授权envelope或调用launch，原r5不改。后续工程任务需使用实际内核能力判断并保留本次失败，不可自动继续本次smoke。依据：`docs/STAGE_0_5_V4_SMOKE_3_2026-10-26.md`。

## 2026-10-26 V4 r5当前阻断（最新）

精确版本解析和新staging已准备，Linux1.26/TraCI22运行时已静态核验；r5当前生产smoke尚未授权/执行，无已验收生产回执。candidate-v5实际v4预检到达integration_not_accepted，不能报告工程Ready。后续需研究者对新proposal精确SHA一次性授权，且运行时/资源须届时复核；研究B00另需工程通过及科研确认。i0007/实际初始化/交互相容/历史隔离事故仍未解决，四false/硬锁/Gate不变。依据：`docs/STAGE_0_5_V4_PREPARATION_2026-10-26.md`；下方为历史时点。

Historical（本任务已补齐映射，旧快照哈希不变）：通用export_project_evidence重建manifest曾漏三个独立扩展登记（depart-speed/V2 research/V2 admission）；本轮保留生成版本于code/tmp、恢复原manifest字节并verify通过，没有修改历史结果。导出器覆盖问题未在本任务修复，见同报告。

## 2026-10-26 WSL解阻后阻断（最新）

Linux无害capsule已验证，仍缺与Windows SUMO1.26匹配的完整控制器：WSL只有SUMO1.18/TraCI20，系统Python缺numpy/pandas/pyarrow/psutil。未换版本或安装；新候选保持阻断、四false与硬锁。/home/shen/AAD非Git checkout，只作临时探针父目录；历史偏差/i0007未解决。依据：`docs/STAGE_0_5_WSL_ISOLATION_2026-10-26.md`；下方为历史时点。

## 2026-10-26 V3真实阻断

OS级隔离仍Unknown/Blocked，WSL能力探针被审批拒绝且未执行；不存在已验收的原生隔离驱动/证书，硬锁True。因此不可报告Ready。TripInfo与完整时间/身份/干预/资源验收已实现但仅软件验证，实际插入/原生运行仍未知。i0007旧日志不证明discard归属，保留原输入的首个B00可能早停；不能通过丢弃该车或复用不合格基线消除问题。旧提案输入/环境占位不作当前绑定；新包变化会使旧候选SHA失效，历史manifest不重写。

依据：`docs/STAGE_0_5_READY_TO_ADMIT_V3_2026-10-26.md`。

## 2026-10-25 V2剩余准入阻断（最新）

身份/适配器/守卫已实现但仅合成验证；原生OS访问、实际插入/丢弃身份、精确插入速度、实际匝道到达及18单元仍Unknown。Python audit不覆盖所有native访问或恶意并发路径替换；真实symlink测试当前权限下skip，模拟越界已测。i0007警告未解决；0805 main_2为52潜在冲突而非仅44。六份历史重测不构成同初始化基线，也不证明零风险。POLICY-A-VALIDATION-SCOPE-01仍Not Accepted；未证明保真/隔离的adapter测量验收保守false，后续原生分支需单独审查和授权，不能只翻标志。

依据：`docs/STAGE_0_5_V2_ADMISSION_ENGINEERING_2026-10-25.md`；`docs/STAGE_0_5_V2_ADMISSION_VALIDATION.md`。下方保留历史时点。

## 2026-10-25 V2当前阻断

交互相容未解决；历史结构/时序P2未整体经C6重测。0750 DS38实际插入未验证、i0007警告保留；0805 main2共52辆而44辆为10，另8辆7.71–9.92>5。旧worker只保存depart/pending数量，不能完成逐车契约；新预算API无launch，执行适配器待完成。旧隔离事故Not Accepted；纯Git软件审计不能证明原生实验隔离，新完整批次阻断。预算不再是V2阻断。

依据：`docs/STAGE_0_5_RESEARCH_V2_AUDIT_2026-10-25.md`；`docs/STAGE_0_5_RESEARCH_V2_BUDGET.md`；`docs/plans/2026-10-25-stage-0-5-interaction-research-v2.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-RESEARCH-V2/`。以下内容保留其历史时点。


## 2026-10-25 候选初始化局限

0750并非全体初态为10，最小候选只改38/117辆；i0007=15.23与原t0警告保留，不能保证消除全部初态冲突。首现只是100ms代理，未观测身份不能推定pending。旧基线初始化不同；ID1/ID3供给与匝道同时不同，剩2次无法独立识别初始化政策作用。旧监督器仍拒绝失败后续跑；后续适配器若改码必须重绑确认。POLICY-A-VALIDATION-SCOPE-01仍Not Accepted。

依据：`docs/STAGE_0_5_DEPART_SPEED_CANDIDATE_2026-10-25.md`；`docs/plans/2026-10-25-stage-0-5-depart-speed-candidate-v1.md`；`evidence/results/RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1/`。以下原内容保留。


## 2026-10-25 供给脉冲与待插入初态冲突（新阻断）

Documented Intent：原routes不变、180s将main_2降至5m/s。Actual Implementation：i0063_i0063声明depart=0/speed10，直到180仍未出现在FCD；降速后SUMO报出发速度过高并退出。Evidence：新结果failure_review.json、原生日志/SHA。Affected Files：冻结输入/输入政策及三次对照。Conflict：完整输入不能实现，18单元不可用。Status: Awaiting Researcher Decision；停止余2次，不自动改departSpeed/初始化/窗口。原隔离偏差仍Not Accepted。

依据：`docs/STAGE_0_5_INTERACTION_DIAGNOSTICS_POLICY_A_EXECUTION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/`。以下旧状态保留为历史时点。

## 2026-10-25 POLICY-A-VALIDATION-SCOPE-01（当前执行阻断）

补充全量回归误在主工作区运行，13项本地历史/原始数据测试变为可执行。998 passed的该次记录不计为有效隔离验证；任务级零验证资源访问不可认证、数据隔离不Accepted，Status: Awaiting Researcher Decision。源码审计详见 `docs/STAGE_0_5_POLICY_A_VALIDATION.md` 与便携 `validation_scope_incident.json`，不重读相关数据。先前独立纯Git回归985 passed保留其有限效力；最终源码在无数据Git克隆另获987 passed / 14 skipped / 7 deselected，定向9项及compileall通过，仍不能逆转隔离偏差。政策A仍Agreed；最终计划Proposed，新轨迹0/3，Gate不变。工程准备不能代替研究者对偏差及运行资格的裁决；未决前不按有效完成任务提交/推送。


## 2026-10-25 政策A与最终计划预检

C7选择已Resolved为任务级A；全面正式初始化/验收未冻结。两侧18/18共同观察单元不证明物理可观测性或状态分布等价。C6跨路段/连接段降级保留。新运行的实际输入/支持/初始化与资源性能仍Unverified，必须逐次核验后才能放行下一次。

依据：`docs/plans/2026-10-25-stage-0-5-interaction-diagnostics-policy-a-final.md`；`evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1/`。


## 2026-10-25 C6/C7 offline phase

C6在新版本同原生车道可观测支持上修复并独立核验；跨路段/连接段物理关系仍不可重建，旧结果未升级。C7不是基线自动作废：A保留[120,390)显式披露残留；B候选[180,390)减少支持并重排脉冲。政策和草案均Awaiting Researcher Decision；原窗P2已见。

依据：`docs/STAGE_0_5_C6_C7_OFFLINE_DECISION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-C6-C7-OFFLINE-V1/`。


## 2026-10-25 Interaction diagnostics preflight

New C6/C7: parse_fcd scales longitudinal coordinates while fcd_to_state_frame subtracts an unscaled leader length from their difference; measured gaps therefore differ from same-native-lane physical position gaps. Existing0750 baseline also fails the proposed120s initialization criterion (1 residual initial vehicle). **Awaiting Researcher Decision** under AGENTS§4. No geometry/risk-core correction, window change or new trajectory performed.

Evidence: `docs/STAGE_0_5_INTERACTION_DIAGNOSTICS_2026-10-25.md`; `docs/audits/stage_0_5_interaction_preflight_v1/preflight.json`; `execution_ledger.json` in the same directory.


## 2026-10-24 Issue #1：C1–C5当前处置（覆盖下方原审计时态）

[证据审计](../docs/STAGE_0_5_WP1_EVIDENCE_AUDIT.md)记录逐项完整冲突与影响；[冻结候选](../docs/STAGE_0_5_ACCEPTANCE_FREEZE_CANDIDATE_V1.md)集中R1–R5，未批准新科研口径：

- C1 **Partially resolved**：真实D1与44个历史模拟局部N、74个点E复现；模拟边E影响已量化，30份grid只有观测前车ID、缺显式incarnation。生产入口仍用点分母，正式测量接纳待决。
- C2 **Partially resolved**：50/100/50m却按100m归一化及模拟200m事实确认；三种统一支持候选有离线敏感性，正式分块待决。
- C3 **Partially resolved**：误标字段实际g/closing确认；两源dropna索引对齐，未见实际错位，通用对齐风险仍在；时距主辅/近零与迁移未批准。
- C4 **Resolved by evidence（两校准源）**：全采集829382拟合点与内部644067拟合点分别精确复现，tau/closing冲突由支持域混用解释；非覆盖式erratum已记录，第三窗轨迹未复核。
- C5 **Partially resolved**：旧分块不变下，文字计划/执行primary为grid11/8、structural4/1，历史判定保留；当前runner SHA不等于freeze源SHA，完整冻结源码快照不可用，历史完整合规Unknown；未来规则与偏离处理待研究者。

额外账本限制：METHOD-DIAGNOSTICS报告称48次进程，而机器budget/executed=43并有26失败及primary/secondary尝试，确切进程总数Evidence Insufficient，不修写历史。R1–R5全部开放，Gate与原剩3次、B0隔离Unknown、第三窗已使用不变。本任务不修生产科研代码、不启动任何新轨迹。

## 2026-10-24 原验收标准审计新增冲突（历史审计时点）

原审计时点的完整 `Documented Intent / Actual Implementation / Evidence / Affected Files / Conflict / Status` 记录见 [Stage 0.5 验收协议草案 §3](../docs/STAGE_0_5_ACCEPTANCE_PROTOCOL_DRAFT.md)。当时全部为 `Status: Awaiting Researcher Decision`；本次处置以顶部Issue #1记录为准，不覆盖历史结果、原决定或Gate：

- C1：`stage_0_5_state_support.py::block_descriptors` 的模拟 P2 分母为状态点数×0.1，包含无前车 `not_applicable` 且未验证连续边；两个后续 runner 直接使用，未执行 D1 两端可靠可评价跟驰时间契约。正式率影响未重算。
- C2：真实 `block_cloud` 的局部两侧块实际50m却按100m归一化，仿真 `block_descriptors` 用200m整体块；共同支持与域成员结论适用性待裁决。
- C3：`stage_0_5_leader_replay.py::pair_metrics` 的 `time_headway_mean_*` 与重建 `interaction_stats::net_gap_over_speed_s` 实际用gap/closing，不可按字段名视为已验证车头时距。
- C4：状态支持报告的829382条、tau_eff=1.5393/1.5687及闭合统计，与当前 `real_domain.json` 的644067条、1.533904/1.606439及对应闭合统计不同；时间/质量口径原因未验证，不自行改成已确认勘误。
- C5：状态支持计划文字写最小双向基线/pooled覆盖，执行对校准条件用方向性基线/另一窗口包络覆盖；哈希存在不证明判据一致。

现有五seed集合包含构造seed；第三窗口已被使用。两者是正式验证独立性限制，不应沿用历史“尚无seed证据/从未打开第三窗”的当前时态。未触及代码或实验；本次只记录冲突与建议，不借此修改科研方案。

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

历史记录：2026-09-10发现的pNEUMA职责冲突已由研究者批准退役决定解决；保留该解决事实。原“当前没有尚待研究者决定的已知重大科研冲突”已过时。当前C1/C2/C3/C5仍有Awaiting Researcher Decision的科学选择与实施冲突，C4仅所审计两校准源的支持域混用已由证据解决，详见本文件顶部Issue #1记录。

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

Documented Intent：06_DECISIONS指数rho/固定分母/车辆等权。Actual Implementation：formal v2符合批准设计，旧main.tex:378-405仍为线性/观测分母/求和。Evidence：最新版20261010 PDF与最终包paper_version_conflict.md。Affected Files：paper/主论文/main.tex、paper/历史记录/20261010_YYS.pdf、06_DECISIONS。Conflict：论文版本与当前设计未同步。Status: **Resolved（2026-10-21，AAD-0.5-CLOSURE）**。核查确认三条事实：(1) 指数 `rho=exp(-TTC/tau)` 已由 2026-10-11 `Agreed Research Design` 与 2026-10-12 分母裁决批准为**主定义**；(2) 实现/配置/测试本已一致（`formal_risk_measurement.py`、`stage_0_2_formal_risk_measurement_p2_v1.json`、`test_formal_risk_measurement.py`），`legacy/` 无残留线性实现；(3) 冲突只在论文——原为阈值线性 `1-TTC/θ` 且区域风险为**求和**。已按批准定义同步 `paper/主论文/main.tex`（指数映射 + 车辆等权平均），并把线性版本明确标记为历史基线；新增 `test_rho_is_the_approved_exponential_mapping_without_threshold_truncation` 断言指数形状、单调性、无截断且不复现线性映射；论文以 XeLaTeX 重编译 9 页 0 错误。原记录保留为历史。核查报告：`docs/STAGE_0_5_FORMAL_RISK_DEFINITION_CONSISTENCY.md`。

路径迁移备注（2026-10-23，不改变上述已关闭状态）：该记录中的 `paper/主论文/main.tex`、`paper/历史记录/20261010_YYS.pdf` 均为**历史路径**。根目录 `paper/` 已于 2026-10-23 退役，本地 `.tex` 不再是当前活动论文源；最新版论文正文以 Overleaf 为准，历史 PDF 在本机 `D:\shen\OB\科研\TJU\AAD\历史Paper\paper\`。导航见 `docs/PAPER_AND_MATERIAL_SOURCES.md`。本条仍为 **Resolved**，不重新打开。

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

## 2026-10-20 LF候选协议整合

P1：历史83是开始到结束而非确认；全源543/732不能作局部率目标；局部平台不等于全网稳态；no-leader真实missing/SUMO not_applicable需按共同语义比较。19边界/新便携反例保护候选分母/时间窗/批准状态；正式局部真实P2仍待同域重算，300s规则确认后无评价支持，δ/h仍未定。历史AGENTS/五项文献删除不动。报告 `docs/STAGE_0_5_LOCAL_FOLLOWING_PROTOCOL_DESIGN.md`；计划 `docs/plans/2026-10-20-lf-protocol-consolidation.md`；证据 `evidence/results/RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1/`。

收口补充：prepare_stage_0_5_lf_protocol_summaries.py封装v1已记录的冻结前A+两摘要补入步骤，3合成准备测试验证；冻结分析未重跑。有限周期精确平衡非统计稳态必要/充分条件，v1辅助标签不能作正式准入，候选协议已澄清。


## 2026-10-20 Stage 0.5 最终收口未解决问题

真实局部 P2 已按 D1 计算完成（147/31,051.6/17.0426 与 216/33,091.1/23.4988），但**仿真侧无可比状态**：条件候选 FC1/FC2 复现了观测内部断面流量（1647.4 对 1646.9、1451.4 对 1439.2 veh/h/lane）却位于基本图自由流分支（20–22 m/s、约 20 veh/km/lane），真实窗口在拥堵分支（8–10.5 m/s、43–50 veh/km/lane）。预声明 30 s 块包络检验两次全部不通过，故第 5 层状态支持缺失、五层合取为 Evidence Insufficient。

闭合方向不是行为参数：D3 禁止用 Krauss 等参数补偿供给失配，需在边界供给/上游需求（下游容量约束或瓶颈）层面作出科研选择。模拟平均闭合速度为正（+2.73/+3.67 m/s）而真实为负（−0.171/−0.109 m/s），交互 regime 符号不同；模拟低速份额 0.0005/0.042 对真实 0.097/0.253。FC1 评价窗内起始事件 0 件（全源确认 84 件）、FC2 22 件、率 56.23 对真实 17.04/23.50；零分子是状态支持产物，不是安全证据。

δ 与 h 无任何独立依据（物理真值永久 Unverified、无系统误差界、无 seed 间方差、无 AAD 效应量要求）；两个同日窗口不构成总体；ED real-real 上界 Not Identifiable。未执行保留的 2 次独立 seed 重复与第三窗口验证；评价窗 [180.0, 299.7] 仅 119.7 s，运行局部暴露 1458.1/1408.4 veh-s 对真实 31,051.6/33,091.1，精度不足。

准备历史保留：v1（pytest basetemp 冲突并过早冻结）、v2（触及 3 GiB 上限、未提限额）、v3（字符串 lane_id 致局部空集，被零暴露守卫拦截）三个被取代版本留在本地且不入便携证据；v1/v2/v3 不是结果。Python 审计仅覆盖受控入口，非 OS/native 安全边界。根工作区五项既有文献索引删除未处理，根 clean 检查受其影响。

## 2026-10-21 AAD-0.5-TR-RECON 未解决问题

1. **真实拥堵的形成事件不在观测覆盖内**：两窗口起点已经拥堵，观测时段净积累仅 ±70 辆（官方输入—输出表 +31/+24/+16/−38/−33）。队列生成过程 `Unidentifiable`；必须在「条件性的需求历史假设」或「扩展到下游真实瓶颈（无证据）」之间作科研选择。
2. **下游供给不可识别**：慢速波自观测段下游端（y=500–650 m）向上游扩张，说明状态由覆盖之外的下游供给带入；瓶颈位置与容量均不可见。
3. **场景状态支持未达成**：RC1 自由流（q=1,811）、RC3 过堵（q=1,492），真实目标位于两者之间（q=1,647）。是否存在既不过疏也不过密的单一供给设置，本批未搜索，且预声明停止规则禁止在同一批内搜索。
4. **行为模型参数 Hypothesis 待研究者决定**：观测密度与观测净间距独立给出有效 Krauss 时间间隔约 1.53–1.63 s（冻结 1.0 s）。该结论需受控平衡态/容量探针与分层、可解释的参数方案，且必须先评估对自由流容量与其它已验证量的影响。**未做任何参数搜索。**
5. **驶入匝道流量存在 34 辆 / 窗口未解释差异**（0750 官方 137 辆 / 955 s 对轨迹首次观测 138 辆 / 720 s）。场景采用官方值并把轨迹值记为敏感性。
6. **官方聚合表为 OCR 转录**（矢量文本缺 ToUnicode），已回读核对并在结构层面与轨迹法交叉支持，但未逐位对齐；登记为 `Unverified until cross-checked`。
7. **本批数值分支微审计未重跑**：`1e-6 m` 位移链与近零分支沿用 2026-10-20 胶囊的已验证结论，本批使用 SUMO 原生 FCD 记录，报告已披露该范围差异。
8. **预算归属待研究者确认**：本批 3 次构造运行是任务书 §3.2 授权下重新规划的诊断预算，不计入 2026-10-20 冻结的「剩余 3 次」额度；两部分额度的收口归属需研究者确认。
9. 2026-10-20 的 δ/h 无独立依据结论**未改变**；2026-10-20 仍未处理（文献索引删除）仍待处理。

## 2026-10-20 AAD-0.5-LIT-CAL 未解决问题

1. **宏观 `tau` 与微观 `tau` 不可互换**：拥堵区密度/净间距反推的 1.53–1.63 s 是平衡等效量；逐对重放显示观测车头时距分布跨越 0.9–9.0 s，单一 `tau` 无法同时匹配。已收窄表述，未解决机制。
2. **44% 的观测初始状态不在冻结 Krauss 的插入安全包络内**（26/48），集中在拥堵窗口。这不是数值噪声，但当前无一致的「如何表示这些状态」的协议。
3. **`tau=1.6` 未改善间距响应且指标冲突**（间距恶化、速度中性）；1.5–10 s 分层速度略改善。是否采用异质 `tau` 或 IDM 对照尚未决定。
4. **参考速度的文献口径不可复现**：Duan 的 `U_e95`（30 天）与 Saberi 的 `v_max`（24 h）在本数据中不存在，只能用窗口参考；真实自由流速度未实测（`Unidentifiable`）。
5. **饱和型状态定义**（绝对 15 m/s、工程值参考的 λ<0.5）在本走廊失去分辨力，不能作为状态定义；FHWA 四条可接受性准则因缺多日样本**无法计算**。
6. **6 篇文献仅元数据核验**（Kesting 2008、Punzo 2012、Krauss 1997、Krauß 1998、Sharma 2019、Kolekar 2020），未据其采用任何公式；若后续需要使用其方法，必须先取得全文。
7. **加速度指标留空**（差分派生量噪声未验证），故不能与 Schrader 的 `NRMSE(s,v,a)` 数值直接比较。
8. **样本量**：每窗口 12 对，配对区间只反映来源内抽样波动，不是科学容差。
9. 日期勘误已显式登记；根工作区 `doc/literature-notes/` 五项既有删除仍未处理。

## 2026-10-20 AAD-0.5-METHOD-EXPANSION 结论更正与未解决问题

**更正（已生效，旧正文不追溯改写）**：`RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1` 报告中的「26/48 组合被 SUMO Krauss 插入安全包络**拒绝**（44%）」是**实现缺陷造成的误判**。SUMO 对失败的插入在后续步重试（`MSLane::isInsertionSuccess()` 失败后车辆保持等待），旧重放只等待 0.25 s 即中止。实测原生延迟 0.05–0.70 s（中位 ≈0.45 s）。证据与更正记录见 `docs/STAGE_0_5_INITIALIZATION_FIDELITY.md`（Conflict Record 表）与 `code/outputs/.../stage_0_5_method_expansion_v1/init_routes.csv`。仍然成立的弱化结论：观测拥堵跟驰状态常落在冻结模型安全包络之外（表现为延迟）。

**未解决**：
1. **异质参数不可检验（Blocked）**：用同一轨迹构造其自身参数再评价该轨迹属循环拟合；按车辆对划分构造/评价集需要 ≥60 对量级的样本，当前 12 对不够。
2. **宏观机制仍未判定**：P5 门控未开（无配置获得配对支持），需求历史/下游容量/滞回仍未检验。
3. **真实自由流速度与真实静止间距不可辨识**：只有方向信息，无绝对量。
4. **Brockfeld 量级差距未解释**：本项目 45–53% 对原文 12–17%；差异来自自然交通（换道、异质驾驶员）与前车由外部轨迹驱动，尚未逐项分解。
5. **`minGap`→1.0 的改善余量仅约 3× seed 噪声**，不能作为参数结论，只能作为方向提示。
6. **Zotero 附件上传失败**（本机 API `HTTP 400 MD5 hash not provided`）：4 份开放 PDF 已下载到本地 `local_research/litpdf/`（不提交 Git），需研究者用客户端挂接；链接已记录在 `STAGE_0_5_ZOTERO_METHOD_EXPANSION_LOG.md`。
7. **11 篇文献仅元数据核验**（Kesting 2008、Punzo 2012、Krauss 1997、Krauß 1998、Sharma 2019、Kolekar 2020、Rhoades 2016、Newell 2002 等），未据其采用任何公式。
8. **加速度指标仍留空**（差分噪声未验证）。
9. `doc/literature-notes/` 五项既有删除仍未处理。

## 2026-10-21 Stage 0.5 剩余阻断：交互相容层

`RES-STAGE-0.5-STATE-SUPPORT-V1` 之后，Stage 0.5 的唯一剩余阻断从「状态支持未达成」改为「**交互相容未达成**」：

- **已达成**：真实总体等效时距（1.539–1.569 s）及其解析能力与观测最大块流量一致；声明供给下的平均局部状态在真实状态域内（两校准窗口、5 独立 seed、留出窗口域迁移）。
- **未达成**：状态匹配配置的局部 P2 率为 0.9–1.5 events/veh-h（真实 17.0/23.5），速度离散低约 35%，净拉开份额 0.395–0.432（真实 0.530–0.537）。
- **已定位的机制**：供给的**水平**控制平均状态，**形式**控制相对运动与风险事件生成。匹配解析能力下的 4 车道缩减把 P2 率带到 18.2–25.5，同时把密度推到 51–55（真实 43.5/50.5），低速份额 0.445–0.505（真实 0.097/0.253）。
- **停止与未做**：预声明判伪规则已触发，未尝试第三种供给编码；未运行任何 AAD 处理；未读 locked holdout。
- **度量局限（已登记）**：`jam_waves` 的继承绝对 10 m/s 阈值在平均速度 9.7 m/s 的配置上无判别力，因此本任务未以低速波份额作为通过或失败的单独依据；需要相对速度定义的波诊断才能补上这一项。
- **工程缺陷（已修）**：`run_cell` 曾把声明能力算在 `vtypes[0]` 的 τ 上，异质臂因此上报 12,580 而非 8,130；代码已改为按份额加权，已存结果的更正值由 `step_analysis` 写入 `mechanism_analysis.json`。判据不依赖该字段。
- **冻结后执行缺陷（已登记）**：`temporal` 首次执行时 `derive_demand()` 因 canonical 表无 `vehicle_id` 列抛 `AttributeError`；修复仅限脚本内列适配，随后重写 freeze manifest（4 个科学产物 SHA 未变，仅两个源码 SHA 变化），留出窗口的数值读取全部发生在 freeze 之后，未用于任何参数或判据调整。

## 2026-10-21 Stage 0.5 交互相容层：边界到达时序已排除为主线解释

`RES-STAGE-0.5-ARRIVAL-TIMING-V1` 之后，交互相容层仍未达成，但候选解释集合缩小：

- **已排除/收窄**：主线边界到达时间结构。它不是"未检验"，而是**不可施加**——入口排队受限使声明的主线到达结构在入网后消失（两臂实现间隔 CV 0.820 vs 0.831、0.788 vs 0.851，声明值 0.25 vs 0.86、0.20 vs 0.91；平均延迟 25–30 s / 4.5–5.6 s）。匝道到达结构可施加且确有影响（速度离散 +0.25/+1.78，均 5/5），但不足以恢复闭合速度体制、波结构或一致的风险事件变化。
- **已修复的度量缺陷**：绝对 10 m/s 慢速份额在平均 9.7 m/s 的配置上不可比；已由相对速度异常诊断替代并验证判别力（真实两窗口 `propagating_structure`、互相关上游份额 1.00、−5.0 m/s、零模型超越 0.000；上一轮周期到达运行为 `uncorroborated_structure`）。
- **仍存在的场景缺陷（已披露，未修复）**：主线 `never_inserted` 达 13%（0750），两臂缺口数不同（0750 137–149；0805 U 30–37 / E 46–54），因此两臂实际进入车辆数不同，交互差异不能完全归因于到达时刻；显式上游存储段属新网络版本，需研究者批准。
- **未检验**：车型不可逐车获得（canonical schema 无逐车长度/类别）；波机制在 SUMO 中"能否复现"仍未被正面证明，只能确认在当前构造下（本轮 20 次 + 上一轮 10 次）没有出现 5/5 的真实式上游波。
- **停止规则执行**：无工程失败、无身份冲突、两臂输入逐项一致、哈希已冻结；新增保真判据在主线触发后按规则停止，未追加第三种供给编码或新参数搜索。


## 2026-10-28 R1 已知问题与边界

R1 工程执行链已通过三臂独立回执，但科学支持仍受源事件缺失限制：B10/B01/B11 正式源 P2 均为 0，不能形成事件特定物理路径或传播到达结论。目标 D1 暴露、速度和生命周期差异只作观测，不作因果效应。原始 capsule/FCD/parquet 不进入便携 evidence，位于 `code/outputs/formal/calibration/stage_0_5_r1_diagnostics_20261028/` 并由便携 manifest 哈希绑定。历史 M3 结构性限制、Stage 0.5 blocked、Stage 0.6/Stage I 状态不变。

## 2026-10-28 First-round offline blockers
Verified: no qualified source P2 in any R1 arm; full event counts are not formal P2. Auxiliary lane events, target-outside event and pre-window event are classified. Missing identity/link/boundary observations remain uncertain, not unreachable; event-specific arrival is undefined without a source witness. Stage 0.5 blocked.
