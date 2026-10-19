# AAD AI Context Changelog

这里只记录影响结构、实现、实验流程或 AI_CONTEXT 的重要变化；细节以 Git diff 和原始实验记录为准。

## 2026-10-18 — AAD-0.5.4-A 校准准入与测量等价性审计

新增 `stage_0_5_calibration_readiness.py`、`run_stage_0_5_calibration_readiness.py`、`run_stage_0_5_timestep_sensitivity.py`、`test_stage_0_5_measurement_equivalence.py`（50 项）。

测量等价性：16 项维度逐条判定（10 Equivalent/Verified、6 Engineering Consistent Only、0 阻断），16 个确定性边界用例全部符合预期，双适配器在事件身份/起点/终点/确认时刻/退出原因一致。修复 6 项适配层缺陷（绝对时钟、前车自身帧号、退出原因保留、闭合 epsilon 继承批准默认值、可靠层定义对齐批准边缘审计、DRAC 复用批准闭式），未修改 Stage 0.2 阈值、持续时间或分母；0.5.3 工程包用修正层重跑，baseline 数值不变，probe 有效 TTC 729→544、可靠闭合暴露 72.5→54.0 s（epsilon 修正），事件仍为 1 且两适配器含 DRAC 完全一致。

校准窗口分析（仅前两个窗口，SHA 校验 + 行级过滤，验证窗口物化 0 行）：独立复现封存分母与事件率；产出运动学/跟驰/可观测性、需求可识别性矩阵、候选分层、轨迹簇不确定性（事件率 CI ±15%，逐行 i.i.d. 窄 12.7 倍）、时间步敏感性与 300 s 成本基准。准入清单 `ready_to_start_stage_0_5_4b=false`。Gate 与所有科学参数状态不变。

## 2026-10-18 — AAD-0.5.3 SUMO 无消息工程基线 — 重要变化

- 建立九文件 `AI_CONTEXT/`，作为 ChatGPT 从 GitHub 快速恢复项目状态的入口。
- 重写长期 `AGENTS.md`，固化 Research Engineer 角色、科研决策边界、冲突停止规则、Context Consistency Check、验证与自动 commit/push 规则。
- 当前代码、入口、测试、索引和证据目录统一为阶段化命名；旧编号材料保留在 archive/history。
- 研究者明确批准 pNEUMA 前车推断与人工复核退役，当前只保留城市运动学校准职责。
- 项目文档校验器开始检查 AI_CONTEXT 文件集合、必需主题和严格 Git 跟踪状态。

## 2026-10-10 任务 1.4

依据真实全量字段证据修复 Lankershim 时钟/帧序列身份口径；记录级冲突传播到诊断段，事件同时检查前后车和完整观测。保留原始候选及拒绝原因；全量重跑与 US-101 回归、便携证据和报告同步。任务 1 建议工程验收，科研规则未冻结。

## 2026-10-10 任务 1.5

前车匹配显式隔离诊断时钟和 Frame_ID；显式时钟缺失或与 `Global_Time - 100*Frame_ID` 冲突时标记不可观测/冲突，不猜测匹配；完全没有诊断字段的历史调用保留兼容路径。新增独立匹配审计，r4 全量回归与 US-101/Lankershim 核心测量和事件数无变化。

## 2026-10-10 任务 2

新增 NGSIM 任务 2 描述性审计入口，复用任务 1.5 state 和事件实现，输出质量状态、有限值分布、极端记录、连续性摘要和 TTC×持续时间敏感性网格；不冻结科学规则或 Stage 0.2 Gate。

## 2026-10-10 任务 2.1

新增固定种子极端/阈值/普通案例复核入口；447 个案例完成独立前车匹配和 TTC/DRAC 重算，生成局部 follower/leader Parquet 和案例图册。自动分类仅作诊断标签，人工物理真实性仍待研究者复核。

- 2026-10-11：任务 2.2.1 连续风险最终修复；统一前向边界语义和完整风险掩码段统计，固定 447 案例与 48 案例包生成 r9 产物。

- 2026-10-11：任务 2.3 生成全量质量、S0/S1/S2 稳健性、暴露候选和科学决策矩阵；正式事件规则差异待研究者裁决。

- 2026-10-11：任务 2.4 完成正式事件提取逐事件等价性验证、S1 真实质量条件重跑、S2 极端观测压力测试和严格连续暴露候选分母；5,381 正式事件与独立结果完全对应，科学规则保持未冻结。

- 2026-10-11：任务 2.5 完成文献证据、6×4 阈值/持续时间联合分析、事件确认时刻、非插值采样敏感性和 24 个真实案例定向复核材料；所有规则保留为 Proposal，未冻结科学参数。


- 2026-10-11：任务 2.5.1 完成 P1/P2/P3 成员级事件对应、24 案例新图册、实际观测确认时刻、rejected 联接修复、极端压力诊断和公平采样状态；P1/P2/P3 仍为 Proposal。


- 2026-10-11：任务 2.5.2 完成中心事件/附近事件区分、P2-only/P3-only/确认时刻差异案例和新图册；P2 未获得唯一科学优先证据。


- 2026-10-11：归档研究者确认的 Stage 0.2 风险事件、连续风险聚合、tau 校准和限定验收设计；新增 tau/P2 独立核定产物，明确实现冲突和未决参数。


- 2026-10-11：完成 rho 时间尺度合理性诊断；报告 tau/2、tau、2tau、TTC 分箱风险贡献和极端压力，不修改 tau 或正式 pipeline。

## 2026-10-11 Formal risk measurement

Added isolated formal measurement interface/config, P2 event revalidation, contribution/status fixture audit, temporal semantics audit, and four unit tests. No production default or historical artifact was overwritten. Automatic GitHub project-integrity workflow was archived and disabled in commit 4deb43d.

## 2026-10-11 正式风险测量一致性修复

完成三个实现修复：区域归属与 TTC 可靠性分离；车辆对键使用完整来源/后车/前车身份；连续性使用 `diagnostic_clock_anchor_ms` 并对缺失字段 fail-closed。P2 独立重算保持 4,545 事件，唯一后车 2,512，唯一车辆对 3,072。报告和 r2 审计产物已封存。


## 2026-10-12 Stage 0.2 综合收口（当前状态）

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。


2026-10-12 验证环境收尾：11个历史本机产物测试显式依赖封存包，在纯Git克隆缺包时skip；本机仍全量执行，不将跳过计为通过。计算原语/独立采样单元测试不跳过。

## 2026-10-12 Stage 0.3 综合实施

新增 `pneuma_urban_kinematics.py`（流式解析审计、时间质量标记、时间加权/车辆等权统计、连续性与极端值敏感性、轨迹簇 bootstrap、Stage 0.5 参考接口、不可覆盖验收包）、入口 `run_stage_0_3_pneuma_kinematics.py`、独立复算 `verify_stage_0_3_independent.py` 和 19 个单元测试。真实全量审计：785 轨迹 / 1,239,475 状态，零缺口/畸形/重复；时间加权速度 mean=4.8382 m/s、加速度 mean=-0.0044 m/s²；独立复算零差异；Stage 0.5 真实接口测试通过。注册表、索引、AI_CONTEXT 同步；科学参数未冻结，Gate Pass Candidate 待研究者。

## 2026-10-16 Stage 0.3 R2 边界修复

AAD-S0.3-T02：`pneuma_urban_kinematics.py` 时间连续性改为排序前按原始记录顺序评估，时间加权区间由原始顺序邻接定义并受统一可靠性掩码约束；`audit_pneuma_source()` 改为行级审计、重复 track_id fail-closed；`build_stage_0_5_reference_states()` 逐状态推导 `quality_status`/`time_weighting_eligible`，`write_real_reference_package()` 实际使用质量字段；新增 9 个构造回归测试，独立复算扩展身份/原始顺序/暴露语义。真实统计不变（145 项比较仅 30 项浮点末位 + 1 项结构性记录），discrepancies=0，全量 315 passed。结果 `RES-STAGE-0.3-BOUNDARY-REPAIR-R2`，包 `stage_0_3_pneuma_boundary_repair_20261016_r2/`；Gate Pass Candidate 待研究者，无 Protocol Lock/Stage I/holdout。

## 2026-10-16 Stage 0.3 正式关闭与 Zotero 整理

AAD-0.3.3：五项研究者决定归档（06_DECISIONS）；`finalize_stage_0_3_scientific_acceptance.py` 生成 R3 关闭包并fail-closed 复核 R2 证据（17 项全过，统计不变）；Stage 0.3 置 `completed_closed`、Gate `pass`（有限范围）。Zotero 唯一文献库只读审计：56 条元数据完整、无未分类/库内重复；发现 05 过载混杂、NC 期刊维度集合不一致、7 对 AAD↔DRIFT 跨项目重复条目；分类调整对照表与维护规范已写入 `doc/literature-notes/`，实际修改待研究者批准。注册表、索引、AI_CONTEXT 同步。

## 2026-10-17 — AAD-0.3.4：Zotero 分类整理与 Stage 0.3 状态修复

Zotero 六主题调整经批准并官方授权执行（更名 05、新建 06、移动 21 条、NC 标签补 5、空 NC 集合删除）；计数 7/11/7/4/11/16 核验通过，56 item key/附件完整，DRIFT 与 7 对重复条目未动；执行清单 `doc/literature-notes/zotero_reorg_2026-10-17_execution.json`。Stage 0.3 一致性：注册表 scientific_claim_eligible 对齐 R3（true，范围限单文件描述性校准）、0.043 s 文本改已批准、R3 复核计数勘误 17→18（封存包未动）。Zotero 决定归档 06_DECISIONS。

## 2026-10-16 — AAD-0.4.1：Stage 0.4 数据源下载前调查（日期勘误 2026-10-17）

只读完成：SPMD 访问状态重验（302 重定向，可达性待 Range 重验）、Packet/BsmP1/RSE_BSM 官方字典结论、RSE_BSM 新识别、时延时钟同步前置、外源候选（AMCD/NYC/Tampa/Sandbox）、8×11 证据矩阵与 P0/P1/P2 下载建议（渐进 RSE_BSM+Packet → 条件性 BsmP1；完整包不必要）。交付 `docs/STAGE_0_4_TASK_0_4_1_DATASET_SURVEY.md`、`docs/research/stage_0_4_dataset_candidates.json`；KI-03 与阶段索引更新；Gate 不变。

## 2026-10-16 — AAD-0.4.2：RSE_BSM 条件获取与核验（日期勘误 2026-10-17）

获取 `RSE_BSM.csv.zip`（成员级 Range，完整性三重校验通过）并完成结构/身份/时间审计：25 字段、无绝对时间、BSMID 行级唯一、RxDevice 属车载命名空间（与 RSE LocID 零重叠，身份 Ambiguous）、配对键重复 ≥26.9M。证据边界（接收时间/时延/丢包 Not Observable、配对 Ambiguous）与 holdout 暂缓已记录；Packet 下一批建议、BsmP1 价值上调、BsmMd/kml 新候选已入清单。结果 `RES-STAGE-0.4-RSE-BSM-V1`；Gate 不变。

## 2026-10-17 — AAD-0.4.3：身份与时间语义核查

官方文档裁定 RxDevice≡车辆 ID、Gentime=生成时间（µs/1609.2，35 s 冲突待校准）、TxDevice+TxRandom=临时 ID 两半、DSecond=分钟内毫秒；**车辆侧接收时间全家族不存在→V2V 时延不可算**；RSE_BSM 采样设计 Unverified（≤2 记录方，10106 全配对）；holdout 4 候选待研究者；下一批建议 BsmMd→BsmP1，Packet 缓行，mCity Rx-BSM（~9 GB）新渠道候选。0.4.1/0.4.2 日期勘误为 2026-10-16。新官方文档存 `dataset/SPMD/`（SHA 已录）。报告 `docs/STAGE_0_4_TASK_0_4_3_IDENTITY_TIME_REVIEW.md`。

## 2026-10-17 — AAD-0.4.4：通信关键证据专项调查

四证据核查 9 候选：接收时间+时延=Bristol ITS-G5/SEE-V2X（受控条件，可信可复现）；丢失率=UCI/Bristol/SEE-V2X；采用=仅驾驶员层面（THEA），控制器 Not Observable（永久缺口）；自然交通 V2V 时延不可达。新增候选入清单；批次 A（Bristol MAT 子集）验收条件已定义；5 项待研究者批准。零下载，Gate 不变。报告 `docs/STAGE_0_4_TASK_0_4_4_COMMUNICATION_EVIDENCE_SEARCH.md`。

## 2026-10-17 — AAD-0.4.5：SEE-V2X/Bristol 可用性裁定

SEE-V2X 可用且首选（单设备日志内配对时延，不依赖跨设备钟；公开 Drive；最小 4.9 MB）。Bristol 时延否定（零延迟分析/创建时刻/无同步）→仅 PDR-RSSI；UCI 属性 Unverified；85% FCW 属 WYDOT。第一批=SEE-V2X 最小样本（<0.5 GiB）。零下载，Gate 不变。报告 `docs/STAGE_0_4_TASK_0_4_5_DATA_ACCESS_VALIDATION.md`。

## 2026-10-17 — AAD-0.4.6：SEE-V2X 最小样本实证验证

下载并验证 outdoor_parkinglot（4.9 MB）：同消息关联 Verified（10/10 配对 1.0）、latency 数值 Verified 但物理意义 Unverified（时钟偏移未证，P50=16.787 ms）、PDR/PER Verified（sender-base 复算与字段一致）、信道占用 Documented。正式校准暂不冻结；建议条件性批准 emulating_applications（4.89 GiB）。Gate 不变；结果 `RES-STAGE-0.4-SEE-V2X-MINIMAL-V1`。

## 2026-10-17 — AAD-0.4.6.1：SEE-V2X 科学复核

修正 0.4.6：完整运行 PDR 才是有效口径（Run 2=0.974 非 1.0）；latency 跨运行时钟偏移 8.8–32 ms 使合并分位数不可靠；逐运行形态相对可信。时钟同步 Unverified；校准仍冻结；下一批 4.89 GiB 建议。结果 `RES-STAGE-0.4-SEE-V2X-REAUDIT-V1`。

## 2026-10-17 — AAD-0.4.6.2：SEE-V2X 科学修正

PDR 接收机会 Unverified（启停 vs 丢包不可分，完整运行 PDR 仅描述性）；跨运行时延差异=真实 PHY/MAC 序列化（包大小），非时钟偏移；Git 可复已修复（方法/结果+6 测试）。下一批 4.89 GiB 建议。Gate 不变。报告 `docs/STAGE_0_4_TASK_0_4_6_2_SCIENTIFIC_CORRECTION.md`。

## 2026-10-17 — AAD-0.4.7：SEE-V2X BSM 验证

下载 emulating_applications（4.89 GiB，提取 BSM+GNSS）：BSM 关联 Verified（12 对 × 4 场景）、PDR 接收机会 GNSS 证实、GNSS 对齐 Verified（距离 0–50 m 不足）、时延数值 Verified（亚毫秒时钟 Unverified）。Git 复现测试修复。受控 PC5 候选参数（非正式校准）。Gate 不变。结果 `RES-STAGE-0.4-SEE-V2X-BSM-V1`。

## 2026-10-17 — AAD-0.4.7.1：SEE-V2X BSM 复核

配对率（1.0）vs 接收比例（0.22–1.0）分开；GNSS≠接收机在线（室内无 GNSS、RSU 静态）→ 链路 PDR/接收机会 Unverified；时钟纪元 ×1000 歧义 → 绝对时延 Unverified；距离仅室外 ~0–10 m。GitHub 交付补齐。Gate 不变。报告 `docs/STAGE_0_4_TASK_0_4_7_1_SCIENTIFIC_REAUDIT.md`。

## 2026-10-17 — AAD-0.4.7.2：SEE-V2X GNSS 修复与收束

t1/t2/t3 GNSS 轨迹逐点相同（同一轨迹复制品）→ 设备间距离不可识别；修复窗口外钳制/时间误差/轨迹独立性。通信统计不受影响。**SEE-V2X 收束**：受控 PC5 候选参考，链路 PDR/接收机会/绝对时延/距离—PDR/自然 V2V Unverified。Gate 不变。结果 `RES-STAGE-0.4-SEE-V2X-GNSS-REPAIR-V1`。

## 2026-10-17 — AAD-0.4.8：Stage 0.4 有限科学验收

研究者批准 Limited Scientific Acceptance：Gate=`pass_limited`、Stage=`Completed / Closed (Limited Scope)`。范围=可观测性边界+描述性证据+参数不确定性原则；性能模型/数值校准/距离函数/采用/因果不验收。通信参数未冻结未校准。RV_RX V3 历史保留。readiness 测试锁定 pass_limited 不单独解锁（Stage I/锁仍禁止）。结果 `RES-STAGE-0.4-LIMITED-SCIENTIFIC-ACCEPTANCE-V1`。

## 2026-10-18 — AAD-0.5.0 场景设计与技术可行性审计

完成只读审计报告 docs/STAGE_0_5_TASK_0_5_0_SCENARIO_DESIGN_AUDIT.md。核验 origin/main=6ee987e、Stage 0.2 R4 NGSIM 四源和 P2=4545、Stage 0.3 R3 单文件 pNEUMA 城市运动学、Stage 0.1 最小双走廊工程能力。确认 US-101/Lankershim/pNEUMA 职责分离候选、稳定哈希抽样和 Energy Distance 的独立性/场景混杂风险，并发现 canonical pNEUMA schema 与 writer 旧字段契约冲突；该冲突和车型映射、抽样权重、时间分辨率、覆盖阈值均待研究者批准。未下载数据、未访问 holdout、未运行 SUMO、未改变 Gate 或 06_DECISIONS。

## 2026-10-18 — AAD-0.5.1 正式真实参考重建

实现 canonical pNEUMA 直连、质量契约 fail-closed 校验、显式 legacy 模式和正式 Stage 0.5 R2 输入 manifest。使用已批准的四个 NGSIM state、Stage 0.2 final_r1 P2 表和 Stage 0.3 canonical pNEUMA 重建 `RES-STAGE-0.5-REAL-REF-R2`；SHA/schema/来源验证通过，正式 P2=4,545，pNEUMA=785/1,239,475。完整时间/车辆等权统计引用封存 R3/R2 摘要；稳定哈希和轨迹簇抽样只作诊断；real-real 独立性不足。新增报告、重建脚本、测试和便携证据索引。未运行 SUMO、未校准、未访问 holdout、未冻结阈值，Gate 仍 `pending_simulation_sample`，Protocol Lock/Stage I 继续阻断。

## 2026-10-18 — AAD-0.5.2 分场景覆盖协议候选

新增 `docs/STAGE_0_5_TASK_0_5_2_COVERAGE_PROTOCOL_DESIGN.md`。核对 `evaluate_simulation_coverage()` 的 pooled scaler、real-real Energy Distance 和集合型 stratum coverage 实现，提出 US-101 五层必要指标、固定完整窗口校准/验证候选、Lankershim/pNEUMA 有限职责、块级不确定性和 Stage 0.5.3 最低输出契约。未修改评价函数、未冻结数值容差、未改变 Gate、未运行 SUMO；全部候选留待研究者批准。

## 2026-10-18 — AAD-0.5.3 SUMO 无消息工程基线

新增 `stage_0_5_sumo.py`、无消息运行入口、candidate config 和 34 项工程测试。US-101 `generic_highway_candidate`（3 主线段 × 3 车道 + 入口/出口匝道）在本地 SUMO 1.26.0 完成两个工程 fixture 并封存 `RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1`：baseline（8,453 state / 17 vehicles / 724 valid TTC / 0 工程 P2）与 measurement probe（1 个 P2 事件，onset 3.1 s、确认 3.3 s、TTC min 1.794 s）。

关键工程事实与订正：①TraCI `getLeader` 距离经三组 vType 对与停驻平衡态实测核验为「物理保险杠净间距 − 后车 minGap」，旧实现直接把该值当 `net_gap_m` 会系统性高估闭合风险；现统一为 `net_gap_m = leader_traci_distance_m + follower_min_gap_m`，同车道几何残差最大 0.0 m；②`closing_speed_mps = follower − leader` 与 Stage 0.1 相反，禁止复用其 TTC 解释；③internal 与 recorded 时间步分离并可审计，0.2 s 记录不得重标为 0.1 s 正式证据；④新增 `CalibrationValidationGuard`，校准入口对 `us101__0820_0835` 与辅助来源 fail-closed 拒绝并写入 `access_audit.json`；⑤新增 Stage 0.2 formal-alignment adapter，逐项说明 SUMO 可自供的身份/时间/连续性字段，`drac_mps2` 保持 NaN，等价性 pending。Lankershim/pNEUMA 未建真实路网、六类 pNEUMA 原始车型全部 `unmapped`；未校准、未进行现实覆盖验收、未改变 Gate 或启动 Stage I。

## 2026-10-18 AAD-0.5.4-A+ 定向补充

`RES-STAGE-0.5-CALIBRATION-GAPS-V1`：两个原始校准TXT共2,583,693行与R2状态100%连接，冲突0；来源车辆2169/2017，汽车比例96.173%/97.323%、汽车中位长4.4196m，车型/长度物理真值仍Unverified。源时钟解释952.8/999s、两源重叠89.5s，没有发现标准化时间错误。候选主线1–5、150≤y<350m；首尾按最长观测轨迹时长100.9/123.5s作候选缓冲后，保留12/11个60s片，统一密度阈值42.8767/48.0828veh/km/lane，内部覆盖720/660s；300m主线1648/1449.82veh/h/lane。局部/分层P2完整成员归属未批准，率Unresolved。

四次300s工程负载完成（SUMO1.26.0，seed20261018，recorded.1s）；.05s低/中/高实际密度41.91/48.06/54.76，墙钟100.27/103.03/116.24s，峰值合计RSS271.9/297.8/327.7MB，末时未插入0/17/23，无碰撞/teleport/守恒残差。初始化积压仍在，60s不是批准暖机；.05s自动ballistic而.1s积分器未显式固定，不能声称数值收敛。完整P2提取成本未含入。Engineering Ready有条件、Measurement Ready待有限批准、Calibration Ready=false、Reality Coverage Accepted=false；所有科学容差Tolerance Not Yet Justified，推荐路径B受限探索仅Proposal，未启动。Gate继续pending_simulation_sample，无验证/holdout/下载/正式校准/锁/Stage I/II。

依据：`docs/STAGE_0_5_TASK_0_5_4A_SUPPLEMENT_CALIBRATION_GAPS.md`及同ID的diagnostics、unified_strata、benchmark、candidate_protocol、audit。完整包`code/outputs/formal/calibration/stage_0_5_calibration_gaps_v1_final/`。Context Consistency Check：不将Proposal写入06_DECISIONS的Approved Research Decision。


## 2026-10-18 — AAD-0.5.4-B0

2026-10-18 AAD-0.5.4-B0（RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1）：受限探索完成19/23次，4次高输入seed20261019响应未运行。统一27.78m/s上限、空初态、ballistic显式、internal.05/recorded.1、action.1、sigmaStep1；三个基准输入1087.364/1449.818/1648veh/h/lane仅实现局部密度10.37–15.75、均速约27.1，局部低速/P2均0。tau2三次末期未服务21/22/71，入口main0约2.5–20.1m有低速插入/加速，局部段无拥堵。B0-EXEC-STOP-01：原调度器未因completed+blocker停止，发现后人工停止，源码停止后修复并测试；最后worker峰值内存Unverified。推荐先批准需求边界/最小结构对照，不继续参数搜索掩盖状态支持缺口。所有结果exploratory_diagnostic_only、scientific_claim_eligible=false；Gate=pending_simulation_sample、Calibration Ready=false、Reality Coverage Accepted=false、正式容差Tolerance Not Yet Justified、Energy Distance上界Not Identifiable；B0实验验证输入0；根全量回归无过滤打开历史Stage0.2全源事件/案例产物，任务级验证访问不能认证（B0-VALIDATION-SCOPE-02）；数据隔离验收不Accepted。无holdout/正式校准/锁/Stage I。依据：docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md、同ID证据和execution_ledger。 Context Consistency Check已覆盖当前状态、架构/模块、数据流、实验、决策授权、已知问题与索引；06仅登记用户有限授权，没有批准结果或参数。

B0收口：纯Git源码1c3aee6全量452 passed/13 skipped，GitHub新克隆严格文档/干净工作区/证据/编译通过，B0+文档41 passed。一次旧Stage0.1版本查询挂起与失败轮次保留；根回归访问例外未消除，任务隔离验收不Accepted。

## 2026-10-19 AAD-0.5.4-B1

B1（RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1）按阻断提前结束：V1失败A后7次未启动，V2 A有效/B警告/C阻断/D未启动，累计4次尝试；无补跑或新seed。A/B局部均速27.1088/26.5152m/s、密度16.3208/16.8197、低速0；C记录2.4007m/s、93.8653veh/km/lane、低速80.1719%、末期未服务252，但停车位移检查与冻结回溢资格阻断，不能作为有效校准样本。D只有静态/空加载检查，动态未知。

收口验证：-S胶囊45 passed、3个合成外部路径拒绝；纯Git全量500 passed/14 skipped（13项缺真实/历史本地数据，1项-S专属已在胶囊验证），compileall/严格文档/干净检出/便携校验通过。17个冻结工程输入解码与SHA核验通过，4组科学图完成视觉检查。根严格检查受原有文献索引缺失影响，5项无关删除未暂存。Context Consistency Check完成，没有改变正式Gate、旧B0封存包或已批准测量规则。

研究者保留B0有限描述证据，B0任务隔离false/验证物化Unknown不变。B1用两校准摘要白名单、SHA/角色守卫、-S最小胶囊、Python路径/子进程审计；冻结前45测试通过、假路径拒绝3/3，矩阵worker拒绝0；不声称OS/native全监控。根工作区不跑全量pytest，全量只在无本地历史数据的Git检出执行，数据skip不算通过。

Gate=pending_simulation_sample、scientific_claim_eligible=false、ready_to_start_stage_0_5_4b=false、reality_coverage_accepted=false；容差Tolerance Not Yet Justified，ED上界Not Identifiable，ProtocolLock/StageI禁止。仅推荐下一项B1.1停车数值/队列回溢观测契约整改，未启动。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md`、`evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1/`中的preflight、execution_stop_observation、numerical_stop_diagnostic、queue_diagnostics、run_manifest和SHA256SUMS。

## 2026-10-19 AAD-0.5.4-B1.1 独立测量契约整改

`RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1`：已核对固定SUMO1.26.0源码；内部负vNext不同于TraCI非负终速和当步平均加速度。4个独立微型fixture、1366条全量相邻边，其中1363精确核对最大残差1.4210854715202004e-14m，2条停车仅必要范围一致，1条edge转换不可评价。保留1e-6m，精确停车仍`Pending Numerical Equivalence`。14个先冻结真值的合成队列案例比较旧网格/新网格/车辆连接；观测与资格、内外排队分开，阈值均Candidate，未批准现实适用性。

B1 C两阻断和D not_attempted永久保留；B0隔离false/验证物化Unknown不变。无旧C状态读取、无新交通矩阵/参数搜索/校准。胶囊路径白名单与SHA、受审计91项测试通过；完整OS/native文件监控未证明。Gate=pending_simulation_sample，scientific_claim_eligible=false、ready_to_start_stage_0_5_4b=false、reality_coverage_accepted=false；容差Tolerance Not Yet Justified、ED上界Not Identifiable、锁/StageI禁止。下一项只建议独立停车分支可观测性最小验证；B1.2需另批，不自动执行。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_1_STOPPING_AND_SPILLBACK_CONTRACT.md`及同ID便携证据；协议/源码/输入冻结SHA见experiment_plan、PLAN_SHA256和provenance。
