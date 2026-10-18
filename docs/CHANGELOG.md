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
