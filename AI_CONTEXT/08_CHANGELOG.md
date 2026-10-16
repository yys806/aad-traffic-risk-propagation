# AAD AI Context Changelog

这里只记录影响结构、实现、实验流程或 AI_CONTEXT 的重要变化；细节以 Git diff 和原始实验记录为准。

## 2026-09-10 — 重要变化

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

## 2026-10-17 — AAD-0.4.1：Stage 0.4 数据源下载前调查

只读完成：SPMD 访问状态重验（302 重定向，可达性待 Range 重验）、Packet/BsmP1/RSE_BSM 官方字典结论、RSE_BSM 新识别、时延时钟同步前置、外源候选（AMCD/NYC/Tampa/Sandbox）、8×11 证据矩阵与 P0/P1/P2 下载建议（渐进 RSE_BSM+Packet → 条件性 BsmP1；完整包不必要）。交付 `docs/STAGE_0_4_TASK_0_4_1_DATASET_SURVEY.md`、`docs/research/stage_0_4_dataset_candidates.json`；KI-03 与阶段索引更新；Gate 不变。

## 2026-10-18 — AAD-0.4.2：RSE_BSM 条件获取与核验

获取 `RSE_BSM.csv.zip`（成员级 Range，完整性三重校验通过）并完成结构/身份/时间审计：25 字段、无绝对时间、BSMID 行级唯一、RxDevice 属车载命名空间（与 RSE LocID 零重叠，身份 Ambiguous）、配对键重复 ≥26.9M。证据边界（接收时间/时延/丢包 Not Observable、配对 Ambiguous）与 holdout 暂缓已记录；Packet 下一批建议、BsmP1 价值上调、BsmMd/kml 新候选已入清单。结果 `RES-STAGE-0.4-RSE-BSM-V1`；Gate 不变。
