# AAD 项目信息结构变更记录

只记录影响项目导航、科研状态、实验/结果追踪、协作规则或复现入口的重要变化。代码细节仍以 Git diff 和实验记录为准；本文件不替代实验日志。

## 2026-10-18 — Stage 0.5.1 正式真实参考重建

- 新增 `RES-STAGE-0.5-REAL-REF-R2`、输入 manifest、canonical pNEUMA 直连 writer、显式 legacy 适配和重建入口。
- 新增真实参考重建报告与便携证据；US-101、Lankershim、pNEUMA 职责保持分离，Stage 0.5 Gate 未升级。

## 2026-10-18 — Stage 0.5.2 覆盖协议候选

- 新增分场景指标、校准/验证隔离、Energy Distance 角色、候选容差语义和 Stage 0.5.3 最低契约报告。
- 仅更新设计索引与状态；未修改评价代码、科学阈值、Gate 或 SUMO 场景。

## 2026-10-18 — Stage 0.5.3 SUMO 工程基线

- 新增独立 no-message SUMO 工程骨架、候选配置、统一状态契约、SUMO-native 与 Stage 0.2 formal-alignment P2 adapter、校准/验证 fail-closed 守卫和 34 项工程测试。
- US-101 `generic_highway_candidate` 完成 baseline 与 measurement probe 两个工程 fixture；核验并订正 TraCI `getLeader` 净间距语义，统一 `closing_speed_mps = follower − leader`，分离 internal/recorded 时间步。
- Lankershim/pNEUMA 保持候选入口且 pNEUMA 六类原始车型 `unmapped`；结果仅 engineering-only，P2 等价性 pending，Gate 不变。
- 注册表订正：移除已被科学再审计取代的旧结果 id `RES-STAGE-0.4-SEE-V2X-BSM-V1`（权威记录 `RES-STAGE-0.4-SEE-V2X-BSM-REAUDIT-V1`），已封存历史 gate 报告保留原 id。

## 2026-10-18 — Stage 0.5.4-A 校准准入与测量等价性审计

- 新增 `stage_0_5_calibration_readiness.py` 与两个入口脚本：测量等价性审计、校准窗口（仅前两个）统计、需求可识别性、候选分层、轨迹簇不确定性、时间步敏感性与成本基准、候选协议与准入清单。
- P2 测量契约 16 项维度逐条判定（10 Equivalent/Verified、6 Engineering Consistent Only、0 阻断），16 个确定性边界用例全部符合预期；独立复现封存的可评价暴露与事件率。
- 修复 6 项适配层缺陷：`global_time_ms` 绝对时钟、`leader_frame_id` 前车自身帧号、`exit_reason` 保留、闭合 epsilon 继承已批准默认值、可靠跟驰层与正式边缘审计对齐、DRAC 复用已批准闭式；未修改 Stage 0.2 阈值/持续时间/分母。
- 新增行级作用域 fail-closed 读取（`require_row_scoped_read`）：正式事件表只物化 543+732 行，验证窗口 0 行。
- 结果 `RES-STAGE-0.5-CALIBRATION-READINESS-V1` 为工程审计；准入清单 `ready_to_start_stage_0_5_4b=false`，Gate 不变。

## 2026-09-10 — 建立 AI 上下文与长期协作层

- 新增九文件 `AI_CONTEXT/`，覆盖当前状态、科研背景、架构、数据流、模块、实验、已确认决策、已知问题和重要变化。
- 重写根 `AGENTS.md`，固化 Research Engineer 职责、科研语义冻结、冲突停止、客观实验报告、上下文一致性、验证和自动提交推送规则。
- 文档校验器与测试增加 AI_CONTEXT 文件、主题和 Git 跟踪契约；修正新阶段 0.2/0.6 产物中的旧 Gate 状态词。

## 2026-09-10 — 阶段编号与目录统一

- 当前计划、代码入口、测试和机器 Gate 统一为“阶段 X.X”/`stage_X_Y`。
- 研究者明确批准 pNEUMA 前车推断与人工复核退役；旧实现、输出和证据转入历史区并保留映射，pNEUMA 当前只承担城市运动学校准。
- 根目录 `记录/` 迁入 `docs/归档/项目记录/`；原始数据迁入本机 `dataset/`，迁移后为 35 个文件、2,047,518,107 字节。
- 当前机器注册表、阶段索引、结果索引、研究状态与阶段执行记录同步重建。

## 2026-09-08 — 长期协作收口与纯 Git 证据闭环

- 将机器注册表升级为 `aad.project-registry.v2`，为每个实验、结果和历史资产补齐目的、版本、路径、配置、参数、指标、Gate、论文位置和正反向链接。
- 新增 `evidence/` 便携证据层与确定性导出器；九项已登记结果的 52 个小型审计文件按字节数和 SHA-256 校验，大表、原始 CSV、HTML、图片、日志及密封抽样键继续留在本地。
- 新增历史索引、重新上手学习路径和方法算法通俗指南；重写根 README、项目交接、项目索引、架构、科研状态、实验索引和结果索引，移除易漂移的瞬时 Git 状态。
- 将文档校验升级为严格模式，检查必需字段、双向链接、稳定章节、路径、证据哈希、Git 跟踪和干净工作树；新增 CI 项目完整性工作流。
- 该次收口没有改变研究问题、算法原理、模型结构、loss、评价指标、实验变量、科学 Gate 或既有结论。

## 2026-09-08 — 建立长期科研协作与双向追踪入口

- 新增根 `AGENTS.md`，明确 Human-driven、AI-accelerated、独立判断、证据边界和持续维护义务。
- 新增项目、架构、研究状态、实验、结果和历史索引，以及机器可读 `PROJECT_REGISTRY.json`。
- 新增 `riskprop.project_docs` 与 `validate_project_docs.py`，检查稳定入口、路径和实验/结果 ID 同步。

## 2026-09-08 — 受控物理整理

- 将导师批注修订记录与一次失败的 XeLaTeX 日志保留式归档。
- 将根 `tmp/` 的 637 个文件和根 `.pytest_cache` 的 5 个文件迁入被 Git 忽略的 `code/tmp/`，迁移前后树哈希一致。
- 将历史 Pilot 模块、命令和测试迁入对应 `legacy/`，保留历史复现入口。

## 2026-10-10 — 任务 1.4 基础测量工程收尾

按诊断帧时钟恢复可验证的字段序列，修复原始行顺序过度分段、前车身份与可靠事件筛选；新增原始/可靠/拒绝候选产物及全量回归入口。登记 `RES-STAGE-0.2-TASK-1.4` 和报告，保留历史产物与未冻结科学口径。

## 2026-10-10 — 任务 1.5 跨时钟前车匹配

前车匹配键显式加入诊断时钟锚和 Frame_ID，新增独立全量核查与回归产物；真实校准结果未变化。


## 2026-10-12 Stage 0.2 综合收口（当前状态）

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。


2026-10-12 验证环境收尾：11个历史本机产物测试显式依赖封存包，在纯Git克隆缺包时skip；本机仍全量执行，不将跳过计为通过。计算原语/独立采样单元测试不跳过。

## 2026-10-16 Stage 0.3 R2 边界修复

任务 AAD-S0.3-T02。修复 `pneuma_urban_kinematics.py` 排序掩盖原始时间顺序、`audit_pneuma_source()` 重复 track_id 字典覆盖、`build_stage_0_5_reference_states()`/`write_real_reference_package()` 质量字段语义失真；新增原始顺序/身份/质量状态专项审计、统一可靠性掩码（时间加权区间由原始记录顺序邻接定义）与 9 个构造回归测试；独立复算扩展覆盖身份、原始顺序与可靠暴露语义。真实统计结果不变（速度 TW mean=4.8382、VW mean=6.2077、加速度 TW mean=-0.0044），R1/R2 145 项比较仅浮点末位与新增质量记录差异；独立复算 discrepancies=0；全量测试 315 passed（数量差异 287/232/315 由收集范围与新增测试解释）。登记 `RES-STAGE-0.3-BOUNDARY-REPAIR-R2`、报告 `docs/STAGE_0_3_BOUNDARY_REPAIR_R2_2026-10-16.md`；Stage 0.3 保持 Gate Pass Candidate，科学参数未冻结，未创建 Protocol Lock，未启动 Stage I/holdout 访问。

## 2026-10-16 Stage 0.3 正式关闭（R3）与 Zotero 文献管理整理

任务 AAD-0.3.3。研究者批准五项决定（单文件适用范围、0<Δt≤0.043 s 正式连续性参数、极端观测保留+敏感性、描述阈值仅描述、Gate=pass）并归档于 `AI_CONTEXT/06_DECISIONS.md`。新增 `finalize_stage_0_3_scientific_acceptance.py` 生成不可覆盖 R3 关闭包 （`RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3`）：对 R2 证据 fail-closed 复核（checksum/计数/统计不变性/独立复算 17 项全过），统计与 R2 完全一致，验收矩阵 11 项 Verified。注册表、索引、AI_CONTEXT 同步，Stage 0.3 置为 `completed_closed`。Zotero（唯一文献库）完成只读审计：56 条元数据完整、无未分类与库内重复，发现 05 子集合过载混杂、NC 期刊维度集合不一致与 7 对 AAD↔DRIFT 跨项目重复条目；提出分类调整对照表与维护规范，实际修改因接口只读全部留待研究者批准。无 Protocol Lock/Stage I/holdout 访问。

## 2026-10-17 — AAD-0.3.4：Zotero 分类正式整理与 Stage 0.3 状态一致性修复

任务 AAD-0.3.4。**Zotero**：经研究者批准与官方本机 API 授权（Zotero 10 `/api/local/authorize` 对话框确认）执行六主题调整——05 原位更名、新建 06、21 条文献按对照表移动、5 篇 NC 论文补标签、空 `NC_统一汇总` 删除；执行后核验 7/11/7/4/11/16、56 item key 与附件无丢失、11/11 NC 标签、7 对 AAD↔DRIFT 重复条目与 DRIFT 侧原样保留；逐条 before/after 见 `doc/literature-notes/zotero_reorg_2026-10-17_execution.json`。59↔56 PDF 差额 `Unverified`。**Stage 0.3 一致性**：注册表 experiment `scientific_claim_eligible` 对齐 R3（true，仅限单文件有限描述性校准范围，与 Stage 0.2 关闭先例一致）；`configuration` 文本改为 0.043 s 已批准（仅本 25 Hz 文件）；R3 复核计数勘误 17→18（封存包机器记录自始为 18，包未改动）。无 Protocol Lock/Stage I/holdout 访问；不重开 Stage 0.3 Gate。

## 2026-10-16 — AAD-0.4.1：Stage 0.4 通信数据源下载前调查（标题日期勘误 2026-10-17）

只读调查（未下载/未申请/未改 Gate）：SPMD 官方条目重验（DOI 10.21949/1504482；端点 403→302 变化，可达性待 Range 重验）；以官方手册字典确认 Packet/BsmP1/RSE_BSM 字段语义与时延/丢包的条件链；识别 RSE_BSM（3.23 GB）为被忽视的最低成本接收侧证据；跨设备时钟同步为时延共同未验证前置。外源候选：AMCD（同行 sent/received）、NYC IE（告警级）、Tampa 样本（RSU 接收）、ITS DataHub Sandbox。交付科研需求-证据矩阵（8 需求 × 11 候选）、P0/P1/P2 下载决策表与 8 项待真实数据确认问题。新增 `docs/STAGE_0_4_TASK_0_4_1_DATASET_SURVEY.md` 与 `docs/research/stage_0_4_dataset_candidates.json`；KI-03 更新。Zotero 无数据集论文，候选 DOI 已列待研究者决定。

## 2026-10-16 — AAD-0.4.2：RSE_BSM 条件获取与独立证据核验（标题日期勘误 2026-10-17）

经研究者批准仅获取 SPMD `RSE_BSM.csv.zip`（成员级 Range，官方新 blob 的 Range/ZIP64 重新验证；CRC32 对中央目录一致、内层 ZIP 通过、SHA-256 钉扎；磁盘余量全程 ≥5 GiB）。实测 25 字段（官方 24+RxDevice；手册 28 字段说法有误）、124,115,615 行零畸形、BSMID 逐行唯一、无绝对时间字段；RxDevice 2,008 全在 BsmP1Summary 设备命名空间且与 RSE LocID 零重叠（记录方身份 Ambiguous，成员命名与官方手册描述不符实际数据）；最佳配对键部分覆盖下重复 ≥26.9M。接收时间/时延/丢包 Not Observable、配对 Ambiguous；行为统计按 holdout 规则暂缓。Packet 建议为下一批（修正预期：与 RSE_BSM 无文档化连接键）；BsmP1 价值上调（RxDevice+Gentime 候选时间锚）；新增 BsmMd/RSE_locations.kml 候选。登记 `RES-STAGE-0.4-RSE-BSM-V1`、报告、注册表/索引/AI_CONTEXT/下载清单/候选 JSON 同步；Gate 保持 `pending_official_packet_access`，未下载 Packet/BsmP1，未改任何封存结果。

## 2026-10-17 — AAD-0.4.3：SPMD 身份与时间语义核查 + 日期勘误

只读核查（零下载；Gate 不变）。新获官方文档（ROSA P WSU BSM Codebook + mCity 数据集文档镜像，存 `dataset/SPMD/` 并记 SHA）：RxDevice≡车辆设备 ID、Gentime=BSM 生成时间（µs 自 2004-01-01，1609.2；与样本手册 35 s 换算存在官方文档冲突待校准）、TxDevice/TxRandom=临时 ID 静态/随机 2 字节、DSecond=分钟内毫秒（手册 §5.4 描述被样例算术否定）。核心边界：**车辆侧接收时间在 SPMD 全家族不存在→V2V 端到端时延不可算**；唯一时延类量为生成→RSE 捕获（需 Packet 且身份匹配未证）。RSE_BSM 采样设计 Unverified（≤2 记录方/发送方 ID、双记录对 102,469/102,469 全含 10106）。Holdout 4 候选方案待研究者。下一批建议：BsmMd（17.29 GB）优先、BsmP1（55.72 GB）次之、Packet 不为凑 Gate 项提前；mCity Rx-BSM 过滤数据集（~9 GB，Globus）为新渠道候选。**日期勘误**：AAD-0.4.1/0.4.2 实际均执行于 2026-10-16（git commit 与封存 created_utc 证明；原存活文档分别误记 2026-10-17/2026-10-18，已非覆盖式更正；封存包零改动）。报告：`docs/STAGE_0_4_TASK_0_4_3_IDENTITY_TIME_REVIEW.md`。

## 2026-10-17 — AAD-0.4.4：真实车联网通信关键证据专项调查

只读专项调查（零下载、零申请；Gate 不变）。跨 DSRC/ITS-G5、C-V2X、V2I、CV Pilot 四方向核查 9 候选并交叉验证。结论：接收时间+同消息时延获得可信真实证据（Bristol ITS-G5 FLOURISH：同设备日志 Tx/Rx CAM 双侧时间戳+SeqNum+RSSI，公开 34.3 GiB 含 MAT 子集；SEE-V2X：C-V2X 跨层端到端时延，表单）；丢失率多候选（UCI DSRC PER 样本、Bristol SeqNum 间隙法、SEE-V2X PDR）；采用仅驾驶员行为层面有真实数据（THEA Phase 3：85% 3 s 内减速、+9.93% 接口效应），控制器层面为永久缺口。自然交通 V2V 端到端时延公开数据不可达（SPMD/mCity 同边界）。新增 4 个候选入结构化清单；定义最小验证批次 A（Bristol importedData，<=25 GiB，验收条件明确）；列出 5 项待研究者批准决定（含验收范围是否接受受控试验参考）。报告：`docs/STAGE_0_4_TASK_0_4_4_COMMUNICATION_EVIDENCE_SEARCH.md`。

## 2026-10-17 — AAD-0.4.5：真实 V2X 数据最小验证与获取准备

只读核查（零下载、零申请；Gate 不变）。SEE-V2X 字段级裁定：`latency=rx_timestamp−tx_timestamp` 于接收端单设备日志内成对（`tx_seq_num` 配对），**不依赖跨设备时钟**→时延可用（绝对偏移待实证）；公开 Google Drive 免申请，emulating_applications 4.89 GiB、最小样本 outdoor_parkinglot 4.9 MB、参数扫描 18.76 GiB（Range 元数据核实，无内容下载）。Bristol 时延否定（论文零延迟分析/创建时刻时间戳/无同步方法）→仅 PDR/RSSI；频率勘误 100 Hz。UCI DSRC 实测属性 Unverified。85% FCW 响应率归属 WYDOT（Tampa 为 50% 天气告警）。第一批建议 SEE-V2X 最小样本（<0.5 GiB），验收条件 5 项已定义；4 项待研究者批准。0.4.4 相关结论已非覆盖式勘误。报告：`docs/STAGE_0_4_TASK_0_4_5_DATA_ACCESS_VALIDATION.md`。

## 2026-10-17 — AAD-0.4.6：SEE-V2X 最小样本获取与实证验证

获取唯一授权样本 `outdoor_parkinglot.tar.gz`（4,883,437 B，公开 Drive，SHA-256 钉扎）并完成实证：**同消息关联 Verified**（10/10 次运行配对率 1.0，`seq_num` 唯一）；**latency 数值可计算 Verified**（(rx−tx)/1000 与 latency 列在 30,571 行逐行一致、0 负值，P50=16.787 ms），**物理意义 Unverified**（跨设备时钟偏移未证）；**PDR/PER Verified**（sender-base 独立复算与 `per_ue_loss_pct` 逐 run 一致，分母=发送数）；信道占用 Documented（P50 5%/max 23%）。`extra=1` 插值行排除。正式校准暂不冻结；建议条件性批准 `emulating_applications`（4.89 GiB，BSM 场景+GNSS）。作者咨询邮件草稿已备未发。零超范围下载，Gate 不变。结果 `RES-STAGE-0.4-SEE-V2X-MINIMAL-V1`；注册表/索引/AI_CONTEXT 同步；全量 315 passed。

## 2026-10-17 — AAD-0.4.6.1：SEE-V2X 通信指标科学复核

仅复用 0.4.6 样本独立复核（零下载零邮件；Gate 不变）。**修正**：0.4.6 `independent_pdr` 为接收窗口口径系统性高估 PDR——Run 2 完整运行 PDR=0.9737（非 1.0）；正确口径=完整运行 PDR（分母=运行内全部发送），字段 `per_ue_loss_pct`≈窗口口径（高 0.3–5 pp）。**时延**：数值 Verified；跨运行固定时钟偏移 P50 8.8–32 ms → 合并分位数不可靠（降级），逐运行形态相对可信但含漂移。时钟同步不可解（Unverified）。正式校准仍不冻结；下一批 4.89 GiB 建议（GNSS 时钟+轨迹绑定）。结果 `RES-STAGE-0.4-SEE-V2X-REAUDIT-V1`；0.4.6 封存包未改动；注册表/索引/AI_CONTEXT 同步；全量 315 passed。

## 2026-10-17 — AAD-0.4.6.2：SEE-V2X 科学修正与复现修复

基于 0.4.6/0.4.6.1 修正：①PDR 接收机会 Unverified（parameters.csv 证 10 运行配置互异、接收端时长系统性短于发送端，Run 2 边界 [0,150] 高度符合启停而非丢包）→完整运行 PDR 仅作描述性指标；②跨运行时延差异由真实 PHY/MAC 序列化（包大小×优先级，50 Hz）解释，非时钟偏移（0.4.6.1 过强表述已纠正）；③Git 可复已修复（`code/tmp/reaudit_*` 入 Git、6 独立测试通过、封存 manifest 补充）。下一批 4.89 GiB 建议（GNSS 时钟参照+距离×时延/PDR；时钟可能仍不可解）。零下载零邮件，Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_6_2_SCIENTIFIC_CORRECTION.md`；新增 `code/tests/test_see_v2x_reaudit.py`。

## 2026-10-17 — AAD-0.4.7：SEE-V2X BSM 应用场景获取与验证

获取 `emulating_applications.tar.gz`（4.89 GiB，SHA-256 钉扎），提取 BSM+GNSS。BSM 消息关联 Verified（12 对 × 4 场景，配对率 0.22–1.0）；PDR 接收机会经 GNSS 证实（100% 时间戳覆盖）；GNSS 时间对齐 Verified 但距离动态范围不足（0–50 m）；时延数值 Verified、亚毫秒时钟仍 Unverified。前置修复 Git 复现测试路径（纯克隆 5 算术测试通过）。正式参数仍冻结。结果 `RES-STAGE-0.4-SEE-V2X-BSM-V1`；报告 `docs/STAGE_0_4_TASK_0_4_7_SEE_V2X_BSM_VALIDATION.md`；新增 `code/tests/test_see_v2x_reaudit.py` 路径修复。

## 2026-10-17 — AAD-0.4.7.1：SEE-V2X BSM 科学复核与交付修复

修正 0.4.7：①配对率（1.0）与接收比例（0.22–1.0）概念混淆已分开（48 对）；②GNSS≠接收机在线（室内无 GNSS、RSU 静态）→ 真实链路 PDR 与接收机会 Unverified；③tx_timestamp 与 GNSS 差 ×1000 → 时钟纪元歧义、绝对时延 Unverified；④距离仅室外 ~0–10 m。GitHub 交付修复：补齐报告/注册表/AI_CONTEXT、test 路径修复（纯克隆 5 算术测试通过）、新结果 `RES-STAGE-0.4-SEE-V2X-BSM-REAUDIT-V1`。Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_7_1_SCIENTIFIC_REAUDIT.md`。

## 2026-10-17 — AAD-0.4.7.2：SEE-V2X GNSS 修复与收束

修复 GNSS 匹配三缺陷（窗口外钳制/时间误差单位/轨迹独立性）。决定性发现：t1/t2/t3 GNSS 轨迹逐点相同（同一轨迹复制品）→ 设备间距离不可识别（恒 0 非重合）；RSU 静态、室内无 GNSS → 距离—通信不可识别。通信统计不受影响。**SEE-V2X 收束**：受控 PC5 候选参考（配对/接收比例/相对时延），链路 PDR/接收机会/绝对时延/距离—PDR/自然交通 V2V 保持 Unverified。新增 6 GNSS 测试全过。零下载零邮件，Gate 不变。结果 `RES-STAGE-0.4-SEE-V2X-GNSS-REPAIR-V1`；报告 `docs/STAGE_0_4_TASK_0_4_7_2_GNSS_VALIDITY_REPAIR.md`。

## 2026-10-17 — AAD-0.4.8：Stage 0.4 有限科学验收与正式收口

研究者批准 Limited Scientific Acceptance。Stage 0.4 收束：Gate=`pass_limited`、Stage Status=`Completed / Closed (Limited Scope)`；验收仅限可观测性边界+描述性证据+参数不确定性原则；不验收性能模型/数值校准/距离函数/采用/核心因果。通信参数未冻结未校准。RV_RX V3 与 Packet 403 保留为历史。readiness 测试锁定 pass_limited 不单独解锁（stage_1_1/protocol_lock 仍禁止）。新增 `test_stage_0_4_limited_acceptance.py`（5 测试）。零下载零邮件，Gate 契约不变。结果 `RES-STAGE-0.4-LIMITED-SCIENTIFIC-ACCEPTANCE-V1`。

## 2026-10-18 AAD-0.5.4-A+

新增独立原始校准车型/长度连接、主线分母、统一分层、时间覆盖与目标密度成本证据及入口/行为测试；登记RES-STAGE-0.5-CALIBRATION-GAPS-V1，不覆盖历史报告/封存结果。保留插入积压、启动异常、积分器限制和未证明容差。科研候选Proposal，无验证/holdout内容读取、无正式校准或Gate升级。


## 2026-10-18 — AAD-0.5.4-B0

2026-10-18 AAD-0.5.4-B0（RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1）：受限探索完成19/23次，4次高输入seed20261019响应未运行。统一27.78m/s上限、空初态、ballistic显式、internal.05/recorded.1、action.1、sigmaStep1；三个基准输入1087.364/1449.818/1648veh/h/lane仅实现局部密度10.37–15.75、均速约27.1，局部低速/P2均0。tau2三次末期未服务21/22/71，入口main0约2.5–20.1m有低速插入/加速，局部段无拥堵。B0-EXEC-STOP-01：原调度器未因completed+blocker停止，发现后人工停止，源码停止后修复并测试；最后worker峰值内存Unverified。推荐先批准需求边界/最小结构对照，不继续参数搜索掩盖状态支持缺口。所有结果exploratory_diagnostic_only、scientific_claim_eligible=false；Gate=pending_simulation_sample、Calibration Ready=false、Reality Coverage Accepted=false、正式容差Tolerance Not Yet Justified、Energy Distance上界Not Identifiable；B0实验验证输入0；根全量回归无过滤打开历史Stage0.2全源事件/案例产物，任务级验证访问不能认证（B0-VALIDATION-SCOPE-02）；数据隔离验收不Accepted。无holdout/正式校准/锁/Stage I。依据：docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md、同ID证据和execution_ledger。

## 2026-10-19 AAD-0.5.4-B1

B1（RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1）按阻断提前结束：V1失败A后7次未启动，V2 A有效/B警告/C阻断/D未启动，累计4次尝试；无补跑或新seed。A/B局部均速27.1088/26.5152m/s、密度16.3208/16.8197、低速0；C记录2.4007m/s、93.8653veh/km/lane、低速80.1719%、末期未服务252，但停车位移检查与冻结回溢资格阻断，不能作为有效校准样本。D只有静态/空加载检查，动态未知。

研究者保留B0有限描述证据，B0任务隔离false/验证物化Unknown不变。B1用两校准摘要白名单、SHA/角色守卫、-S最小胶囊、Python路径/子进程审计；冻结前45测试通过、假路径拒绝3/3，矩阵worker拒绝0；不声称OS/native全监控。根工作区不跑全量pytest，全量只在无本地历史数据的Git检出执行，数据skip不算通过。

Gate=pending_simulation_sample、scientific_claim_eligible=false、ready_to_start_stage_0_5_4b=false、reality_coverage_accepted=false；容差Tolerance Not Yet Justified，ED上界Not Identifiable，ProtocolLock/StageI禁止。仅推荐下一项B1.1停车数值/队列回溢观测契约整改，未启动。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md`、`evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1/`中的preflight、execution_stop_observation、numerical_stop_diagnostic、queue_diagnostics、run_manifest和SHA256SUMS。

## 2026-10-19 AAD-0.5.4-B1.1 独立测量契约整改

`RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1`：已核对固定SUMO1.26.0源码；内部负vNext不同于TraCI非负终速和当步平均加速度。4个独立微型fixture、1366条全量相邻边，其中1363精确核对最大残差1.4210854715202004e-14m，2条停车仅必要范围一致，1条edge转换不可评价。保留1e-6m，精确停车仍`Pending Numerical Equivalence`。14个先冻结真值的合成队列案例比较旧网格/新网格/车辆连接；观测与资格、内外排队分开，阈值均Candidate，未批准现实适用性。

B1 C两阻断和D not_attempted永久保留；B0隔离false/验证物化Unknown不变。无旧C状态读取、无新交通矩阵/参数搜索/校准。胶囊路径白名单与SHA、受审计91项测试通过；完整OS/native文件监控未证明。Gate=pending_simulation_sample，scientific_claim_eligible=false、ready_to_start_stage_0_5_4b=false、reality_coverage_accepted=false；容差Tolerance Not Yet Justified、ED上界Not Identifiable、锁/StageI禁止。下一项只建议独立停车分支可观测性最小验证；B1.2需另批，不自动执行。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_1_STOPPING_AND_SPILLBACK_CONTRACT.md`及同ID便携证据；协议/源码/输入冻结SHA见experiment_plan、PLAN_SHA256和provenance。

## 2026-10-19 AAD-0.5.4-B1.1-S 公开接口停车可观测性验证

`RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1`：固定SUMO1.26.0源码审计确认，非决策步延续公开加速度（`vSafe=v0+a_pub_start*h`），内部带符号候选终速可由公开TraCI独立重建`u=v0+a_pub_start*h`，对任意符号精确成立，包括`u<0`的真实步内停车；决策步`v1=0`仍被`max(u,0)`钳制，仅可范围一致检查。决策步判定：步[`t_prev`→`t_now`]为决策步当且仅当`t_now`读到的`lastActionTime`等于`t_prev`。3个微型运行、948条相邻边：947精确核验且全过，最大残差`1.4210854715202004e-14m`，1条决策步停车仅范围，0不可评价，0异常；未用位移反推、未用调试二进制、未修改官方二进制。方案A/B准入比较与B1.2前置条件已登记，待研究者决定。B1.1精确停车`Pending`记录与B1 C/D、B0不变。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_1S_STOPPING_OBSERVABILITY.md`及同ID便携证据；协议/源码/输入冻结SHA见experiment_plan、PLAN_SHA256和provenance。


## 2026-10-19 B1.2 分层准入与机制再验证

B1.2新增分层数值、分域计数、显式internal路径和队列接入；严格is_action布尔/时钟防御。真实压缩fixture近零候选终速不一致触发自动停止，独立封存反例/计划/未执行项；旧B1/B1.1/B1.1-S证据无变化，主矩阵未启动。


## 2026-10-19 B1.2-N（独立工程观测）

`RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1`：独立B1.2-N工程任务。固定SUMO1.26源码完整谓词和调用顺序已审计；无停车任务的fresh/immutable生命周期可用doubleMax不变量，同edge常规停车仅非决策步可作充分条件。一般myStopDist不能由公开getter等价恢复。新候选`b12n-near-zero-observability-v1`不以位移/终速选择上下文，1e-6m不变。3个30s微型运行：2879边，2876精确全过（其中1负近零后处理），3 bounded，0近零未决/不可评价/工程错误；最大残差1.3988810110276972e-14m。冻结前203项受控合成通过。

正近零非决策步清零运行边未出现（Not Observed），未满足运行前冻结的共同准入条件；integration_allowed=false，C/D计划冻结被拒绝，均Not Attempted，未追加试验/搜索。新主矩阵禁止且0次。旧B1.2阻断/0-8/D未运行和所有历史证据不变。下一步由研究者决定正近零覆盖设计与未来政策，再另批接入/主矩阵；不自动继续。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2N_NEAR_ZERO_AND_INTEGRATION.md`；证据同ID目录。科研Gate/ready/现实覆盖/锁/StageI状态不变，科学阈值未批准。

B1.2-N收口验证：纯Git全量698 passed/14 skipped；严格文档/便携/36源文件绑定/compileall通过，skip逐项列证；根目录文献缺失例外保留。


## 2026-10-19 B1.2-P（受限正近零独立验证）

`RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1`：B1.2-P仅数值观测独立任务。固定SUMO1.26/commit fa7df22d，13具名源码完整谓词/赋值路径核对；fresh/no-stop/无恢复/无控制/无特殊设备/非循环路线doubleMax不变量独立成立。5个冻结原生红灯制动探针各2s、无车辆setter/无重试。实际P1/P2在.10→.15s非决策步重建u_pre约1.999999909e-6/4.800000001e-6，公开终速0，最终分支由源码与生命周期先行确定，位移残差-4.6161e-15/-6.4115e-15m。2条目标Exact Pass；195边中192一般精确全过、3 bounded、0未决/不可评价/阻断。P3/P4/P5实际阈值以上保持正终速；P3名义等号但实际略高，运行精确等号Not Observed。1e-6m未放宽，残差不用于反推上下文。

仅target_branch_verified=true，C_D_allowed=false/main_matrix_allowed=false/future_numerical_policy_approved=false。不需要为该受限分支使用调试构建；一般停车/状态恢复/特殊控制域未验证。B1.2-N正近零Not Observed与integration_allowed=false、旧B1.2阻断/0-8及所有历史原样保留。本轮C/D和主矩阵0次；下一步研究者需决定未来数值准入政策，另批剩余接入；不自动执行。科学Gate及所有ready/现实覆盖/锁/StageI资格不变。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2P_POSITIVE_NEAR_ZERO.md`；证据同ID目录。

B1.2-P收口：纯Git全量741 passed/14 skipped/0 failed；严格文档/compileall/便携重算/33源绑定通过，skip逐项留证；根目录文献缺失例外不处理。


## 2026-10-19 C/D有限接入与自主问题发现

`RES-STAGE-0.5-CD-INTEGRATION-V1`：C/D有限接入2次各60s；62707边中62513精确全过、63 bounded、131合法坐标不可评价、0数值阻断。C内部队列/上游扩展/入口邻近与87 pending可观测，但入口与下游锚定组件约14.35m>10m，持续回溢EI。D9辆实际换道和main2出口由原始状态独立验证；v1 main_1-only假阻断保留，v2修复无重试。定向0/8、主矩阵0次；正式Gate和全部历史不变。

报告 `docs/STAGE_0_5_TASK_CD_INTEGRATION_AND_ISSUE_DISCOVERY.md`；证据 `evidence/results/RES-STAGE-0.5-CD-INTEGRATION-V1/`。研究者本轮授权工程分层与新增2次接入（已用完）、定向最多8次（未用）；无ABCD授权。近零仅fresh/no-stop域，1e-6m不变。当前最重要决策是下一局部跟驰探索是否需要完整入口回溢，以及评价时间/需求/科学容差/P2局部归属协议；不为非核心私有量无限追加验证。旧B1/N/P授权与状态作为历史保留。通用路网/局部匹配为当前研究者优先，真实几何完整复现非必要前提，但结构/匝道/波传播结论受限。


## 2026-10-19 局部跟驰探索（方案A）

`RES-STAGE-0.5-LOCAL-FOLLOWING-EXPLORATION-V1`：方案A局部探索已独立执行3/8次（120s同步、120s批处理、300s延长），剩5；接入额度不复用。175679行/28非标签字段及延长前缀完全相等，worker283.31→68.63s约4.13倍，无缓存/观测降频。固定原尺度C main1[50,250)m局部可测；LF3均速2.964/density81.558/低速77.03%，1222个TTC<2点中1203在前120s。全网核心266工程事件/42404.3veh-s；局部归属起始86/确认87/全程83，正式局部P2/暴露Unresolved、率Not Calculated。14.35m间隙离线分解，C回溢EI不变；正式Gate/历史不变。

报告 `docs/STAGE_0_5_LOCAL_FOLLOWING_EXPLORATION.md`；证据同结果ID目录。研究者已批准局部探索不以完整入口回溢资格为前提；未批准局部P2归属、正式暖机/窗口、科学容差/需求识别/校准目标。需要的3项决定集中在researcher_decision_matrix.json。当前工程闭环不代表科学Gate，通过只在受限fresh/no-stop/只读域成立。LF1/LF2为同seed读取对照，LF3为同seed延长，不当独立重复池化。正式Gate、C回溢EI与历史不变；没有ABCD/正式校准/Lock/I-II。

## 2026-10-20 LF候选协议整合

266个原核心工程事件独立重建、逐成员核对；历史86/87/83重现，开始至确认全在域为86，差异4件。共同候选分母14636.2veh-s，局部正式P2仍Unresolved/Not Calculated。相位周期5/10/20%敏感性均到300s才完成，后评价0s；局部平台而全网/pending增长。五层必要目标、需求可识别性和科学误差/精度候选已整合为D1–D5待决；无新增SUMO，累计3/8剩5。C回溢EI与全部历史、Gate/Lock/I-II状态不变。

报告 `docs/STAGE_0_5_LOCAL_FOLLOWING_PROTOCOL_DESIGN.md`；计划 `docs/plans/2026-10-20-lf-protocol-consolidation.md`；证据 `evidence/results/RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1/`。


## 2026-10-20 — AAD-0.5-FINAL-CLOSURE Stage 0.5 最终收口

- 新增结果 `RES-STAGE-0.5-FINAL-CLOSURE-V1`，便携证据 59 个文件（含事件级、成员支持级与簇级表），登记入 `PROJECT_REGISTRY.json`、`RESULTS_INDEX.md`、`STAGE_INDEX.md` 与 `RESEARCH_STATUS.md`。
- 新增 `code/src/riskprop/stage_0_5_final_closure.py`（已批准 D1 归属、局部 P2/暴露、误差判据与运行计划守卫）与 12 项手算期望值测试。
- 新增真实参考重算入口 `code/scripts/run_stage_0_5_final_closure.py`、条件候选入口 `code/scripts/run_stage_0_5_closure_candidate.py`、有限进程树监督器 `code/scripts/supervise_stage_0_5_closure.py`、统计冻结/分析脚本 `code/scripts/audit_stage_0_5_closure_statistics.py`。
- 新增装配与校验入口 `code/scripts/package_stage_0_5_final_closure.py`、`code/scripts/verify_stage_0_5_final_closure.py` 与证据回归测试 `code/tests/test_stage_0_5_final_closure_evidence.py`；`export_project_evidence.py` 增补本结果的导出映射与聚合文件白名单。
- 研究者批准 D1–D5 记入 `AI_CONTEXT/06_DECISIONS.md`；真实局部 P2 由 Unresolved/Not Calculated 变为已计算，但 Gate 未升级。
- 历史状态与旧包字节未改写：LF 候选协议包仅在政策上被 D1 批准取代，B0/B1/B1.1/B1.1-S/B1.2/B1.2-N/B1.2-P/CD/LF 全部保留。
