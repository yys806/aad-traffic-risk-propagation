# AAD 阶段索引

> 核对日期：2026-09-10。机器标识统一使用 `stage_X_Y`；旧实验编号仅保留在历史映射和旧证据中。

## 当前顺序

`阶段 0.1 → 阶段 0.2 / 0.3 / 0.4 → 阶段 0.5 → 阶段 0.6 → 协议锁 → 阶段 1.1`。

## stage_0_1 — 正式实验基础设施

工程 Gate 已完成；验证四格、五表、运行隔离、时钟、车辆生命周期、封存和独立复算。只属于工程证据。

## stage_0_2 — NGSIM 跟驰风险审计

当前主任务。审计前车关系、净间距、闭合速度、TTC、DRAC和风险事件，并整理现实参考范围。

## stage_0_3 — pNEUMA 城市运动学校准

只整理速度、纵向加速度和车型分布；不再推断前车，不计算 TTC/DRAC，不进行人工前车复核。

2026-10-12：综合实施与验收准备完成。785 轨迹 / 1,239,475 状态全量审计、时间加权/车辆等权描述性统计、敏感性与 bootstrap、Stage 0.5 真实接口测试均通过，独立复算零差异。报告：`docs/STAGE_0_3_PNEUMA_KINEMATICS_2026-10-12.md`；结果：`RES-STAGE-0.3-PNEUMA-KINEMATICS-R1`；验收准备包：`code/outputs/formal/calibration/stage_0_3_pneuma_kinematics_20261012_r1/`。状态 **Gate Pass Candidate**，科学 Gate 与未冻结参数（连续性容差、描述性阈值、车型映射、适用范围）待研究者审核。

2026-10-16（R2，当前）：AAD-S0.3-T02 边界修复完成。修复排序掩盖原始时间顺序、重复 track_id 字典覆盖与 Stage 0.5 质量字段语义失真三项工程缺陷；时间连续性改为排序前按原始记录顺序评估，时间加权区间由原始顺序邻接定义，轨迹审计以原始行为单位、重复 ID fail-closed，`quality_status` 逐状态推导且 `write_real_reference_package()` 实际使用质量字段。真实统计结果不变（145 项比较：30 项浮点末位、1 项结构性记录差异、无统计变化）；独立复算 discrepancies=0；全量测试 315 passed。报告：`docs/STAGE_0_3_BOUNDARY_REPAIR_R2_2026-10-16.md`；结果：`RES-STAGE-0.3-BOUNDARY-REPAIR-R2`；验收准备包：`code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2/`。状态保持 **Gate Pass Candidate（R2）**，待研究者最终裁决。

2026-10-16（R3，当前）：研究者经任务 AAD-0.3.3 批准五项决定，**Stage 0.3 正式关闭**：正式范围限本文件实际观测车辆的描述性城市运动学参考；连续性规则 `0<Δt≤0.043 s` 升格为已批准科学参数（仅本 25 Hz 文件）；极端观测原始保留+标记+敏感性；描述阈值仅统计描述；`Scientific Gate=pass`、`Completed / Closed`。关闭包基于 R2 证据 fail-closed 复核（checksum、计数、统计不变性、独立复算 discrepancies=0），未重跑全量管线。报告：`docs/STAGE_0_3_SCIENTIFIC_ACCEPTANCE_2026-10-16.md`；结果：`RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3`；包：`code/outputs/formal/calibration/stage_0_3_scientific_acceptance_20261016_r3/`。R1/R2 历史包保留不覆盖；Stage 0.5 的车型映射、时间权重抽样与覆盖阈值独立待决。

## stage_0_4 — SPMD 通信证据边界

已确认 RV_RX 只支持接收状态连续性；packet级时延、丢包和采用仍不可观测。

2026-10-16（AAD-0.4.1，日期勘误 2026-10-17）：完成下载前数据源调查（只读，未下载）。SPMD 官方条目（DOI 10.21949/1504482）2026-01 重建，下载端点由历史 403 变为 302 重定向至官方文件 API（最终可达性待下个授权下载任务验证）。官方字典确认：Packet（15.33 GB）为 RSE 侧捕获（仅捕获时间戳、IP 轮换、无发送时刻）；BsmP1（55.72 GB）具备发送侧字段（TxRandom/MsgCount/Gentime 含官方换算）；RSE_BSM（3.23 GB，此前未被重视）为 RSE 接收 BSM 内容且含 4 个未文档化字段。跨设备时钟同步是全部时延主张的共同未验证前置。其他候选：AMCD BSM（唯一同行 sent/received 时间，云接收）、NYC IE EVENT（告警级，时间空间分箱）、Tampa BSM 样本（RSU 接收）。推荐渐进下载 RSE_BSM+Packet（18.6 GB）→ 视核验结果再定 BsmP1。报告：`docs/STAGE_0_4_TASK_0_4_1_DATASET_SURVEY.md`；清单：`docs/research/stage_0_4_dataset_candidates.json`。Gate 与既有结论不变。

2026-10-16（AAD-0.4.2，日期勘误 2026-10-17；当前）：经研究者批准，成员级 Range 方式获取 `RSE_BSM.csv.zip`（3,228,646,514 B；CRC32/中央目录一致、内层 ZIP 校验通过、SHA-256 已钉扎）。实测 25 字段（官方 24+RxDevice）、124,115,615 行零畸形、BSMID 逐行唯一、无任何绝对时间字段；RxDevice 2,008 值全部落在 BsmP1Summary 设备命名空间、与 RSE LocID 零重叠（“RSE” 命名与实际记录方命名空间不符，Ambiguous）；成员内最佳配对键重复 ≥26.9M——配对/时延/丢包仍 Ambiguous/Not Observable。行为统计按 holdout 规则暂缓。Packet 建议为下一批（RSE 侧绝对时间+信道条件，修正预期：与 RSE_BSM 无文档化连接键）；BsmP1 价值上调（RxDevice+Gentime 时间锚候选）；新识别 BsmMd（17.29 GB）与 RSE_locations.kml（520 B）。结果 `RES-STAGE-0.4-RSE-BSM-V1`；报告 `docs/STAGE_0_4_TASK_0_4_2_RSE_BSM_AUDIT.md`。Gate 保持 `pending_official_packet_access`。

## stage_0_5 — 仿真—现实覆盖

用 NGSIM 跟驰风险与 pNEUMA 城市运动学约束无消息作用的 SUMO 校准样本。当前缺仿真样本。

## stage_0_6 — 数值验证与协议锁定

技术真值检查已有结果；待前置 Gate 和科学容差冻结后生成不可覆盖的协议锁。

## stage_1_1 — 核心效应确认

已同意的后续目标，尚未实现、未运行、无结果；协议锁完成前禁止启动。

## 后续阶段

- 阶段 1.2—1.3：竞争基线与独立复算。
- 阶段 2.1—2.4：生命周期、负对照、通信损伤与消融。
- 阶段 3.1—3.2：连通场景校准与正式跨几何验证。
- 阶段 4.1—4.6：真实留出校核与跨条件泛化。
- 阶段 5.1—5.4：困难场景、控制优化、尾部验证与真实控制栈。
- 阶段 6：全文复算与投稿。

新增阶段或状态变化时，同步修改本索引、`PROJECT_REGISTRY.json`、`RESEARCH_STATUS.md`和对应执行记录。

任务 2.2 自动诊断报告：docs/STAGE_0_2_TASK_2_2_KINEMATIC_REVIEW_2026-10-10.md；完整案例包位于 code/outputs/formal/calibration/stage_0_2_task_2_2_kinematic_review_20261010_r6/。人工判断尚未完成。

任务 2.2.1 连续风险修复与验收：docs/STAGE_0_2_TASK_2_2_1_CONTINUITY_FIX_2026-10-10.md；产物 code/outputs/formal/calibration/stage_0_2_task_2_2_1_20261010_r5/。

- 2026-10-11：任务 2.2.1 连续风险最终修复产物 `stage_0_2_task_2_2_1_20261011_r9`；447 案例分类/阈值统计、48 案例覆盖和空白复核包已重算，工程结果待研究者验收。

- 2026-10-11：新增任务 2.3 NGSIM 风险质量与稳健性综合收口报告及独立产物 `stage_0_2_task_2_3_20261011_r3`。

- 2026-10-11：任务 2.4 正式事件等价性与风险稳健性最终验证；新增 `docs/STAGE_0_2_TASK_2_4_EVENT_EQUIVALENCE_2026-10-11.md` 和独立产物 `stage_0_2_task_2_4_20261011_r2`。

- 2026-10-11：任务 2.5 阈值、持续时间与物理合理性联合验证材料完成，新增报告和独立产物 `stage_0_2_task_2_5_20261011_r1`。


- 任务 2.5.1：P1/P2/P3 成员级事件对应、24 案例新图册和因果确认审计；科学参数保持未冻结。


- 任务 2.5.2：关键差异案例与中心事件归属验证；科学规则保持未冻结。


- Task 2.5 decision ratification：研究者设计已归档，参数核定与实现缺口保留为待完成事项。


- 连续风险时间尺度验证：rho 分布、暴露时间与贡献结构已完成，未修改科学参数。

- 正式风险测量接口与 P2 独立复核：4,545 个事件一致；区域 burden 因未批准目标区域/窗口保持 Unresolved。

- 正式风险测量一致性修复：P2 事件、车辆对和连续性字段完成独立回归。


## 2026-10-12 Stage 0.2 最终验收审计（当前状态）

最终验收包：`code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r3/`；Gate=`Blocked`。P2=4,545、可靠跟驰暴露512,043.2s、闭合暴露208,026.3s及四源事件率均可复算；独立边级审计确认连续性和来源身份条件，但发现分母含 `invalid/non_positive_gap` 端点边（Lankershim 7,557.4s；US-101 三窗口187.4/178.7/197.5s），其P2可评价性未由批准决定定义。研究者需确认这些边是否属于正式事件率分母，确认前不得关闭。200ms两相位不等价、极端屏蔽与独立物理真实性Unverified继续披露；无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。

## 2026-10-12 — Stage 0.2 最终验收已关闭

Stage 0.2 Gate=`pass`，状态=`Completed / Closed`，限四个批准NGSIM来源和100ms描述性纵向跟驰风险代理测量。研究者批准P2可评价跟驰暴露分母；独立边级复算计入5,039,222条边/503,922.2s，8,121.0s不可评价暴露保留为质量统计，不解释为零风险。P2=4,545。四源事件率和逐源分母在`RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4`报告。200ms非等价、物理真实性、缺失选择偏差、极端敏感性、来源外推继续限制科学解释。R3 Blocked为历史记录，未覆盖。详见`docs/STAGE_0_2_SCIENTIFIC_ACCEPTANCE_2026-10-12.md`及最终包。

2026-10-17（AAD-0.4.3，只读核查）：新获官方文档（ROSA P WSU BSM Codebook + mCity 数据集文档）裁定：`RxDevice`≡车辆设备 ID（接收日志）、`Gentime`=BSM 生成时间（µs 自 2004-01-01，1609.2；35 s 文档冲突待校准）、`TxDevice/TxRandom`=临时 ID 静态/随机 2 字节、`DSecond`=分钟内毫秒（手册 §5.4 描述被样例算术否定）。硬边界：**车辆侧接收时间在 SPMD 全家族不存在→V2V 端到端时延不可算**；唯一时延类量=生成→RSE 捕获（需 Packet 且身份匹配未证）。RSE_BSM 采样设计 Unverified（≤2 记录方/发送方 ID，双记录对全含 10106）——接收率统计前必须查明；holdout 4 候选方案待研究者。下一批建议：**BsmMd（17.29 GB）优先**、BsmP1（55.72 GB）次之、Packet 不为凑 Gate 项提前；新渠道候选 mCity Rx-BSM 过滤数据集（~9 GB，Globus）。零下载，Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_3_IDENTITY_TIME_REVIEW.md`。

2026-10-17（AAD-0.4.4，只读专项调查）：跨 DSRC/ITS-G5、C-V2X、V2I、CV Pilot 四方向核查 9 个候选。核心发现：①接收时间+同消息通信时延获得可信真实证据——Bristol ITS-G5 FLOURISH（同设备日志 Tx/Rx CAM 双侧时间戳+SeqNum+RSSI，受控条件，公开 34.3 GiB/含 MAT 子集）与 SEE-V2X（C-V2X 跨层端到端时延，表单）；②丢失率——UCI DSRC（PER 样本）、Bristol（SeqNum 间隙法）、SEE-V2X（PDR）；③采用——仅驾驶员层面真实数据（THEA Phase 3：85% FCW 后 3 s 减速、+9.93% 接口效应），控制器层面公开实车数据 Not Observable（永久缺口）；④自然交通 V2V 端到端时延公开数据不可达（SPMD/mCity 同边界）。四证据场景互异，禁止混用。最小验证批次 A（Bristol importedData，<=25 GiB）已定义验收条件；待研究者批准项 5 项（含验收范围是否接受受控试验参考）。零下载、零申请；Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_4_COMMUNICATION_EVIDENCE_SEARCH.md`。

2026-10-17（AAD-0.4.5，只读核查）：SEE-V2X 与 Bristol 可用性裁定。SEE-V2X **可用且为首选**：`latency=rx_timestamp−tx_timestamp` 在接收端单设备日志内成对（`tx_seq_num` 同消息配对），不依赖跨设备时钟；公开 Google Drive 免申请（emulating_applications 4.89 GiB；最小样本 outdoor_parkinglot 4.9 MB；参数扫描合计 18.76 GiB）；`per_ue_loss_pct` 分母待实证。Bristol **不可用于时延**（论文零延迟分析、Timestamp=创建时刻、无跨设备同步），仅 PDR/RSSI（频率勘误为 100 Hz）。UCI DSRC 实测属性 Unverified。85% FCW 响应率为 WYDOT（非 Tampa）。第一批建议 SEE-V2X 最小样本（<0.5 GiB）。零下载，Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_5_DATA_ACCESS_VALIDATION.md`。

2026-10-17（AAD-0.4.6，实证验证）：SEE-V2X 最小样本（outdoor_parkinglot.tar.gz，4,883,437 B，公开 Drive）已获取并实证。核心结果：**同消息关联 Verified**（10/10 次运行配对率 1.0，`seq_num` 0..N−1 唯一，发送端 t1/接收端 t3 日志按 (equipment_id, seq_num) 关联）；**latency 数值可计算 Verified**（(rx−tx)/1000 与 latency 列在 30,571 行逐行一致、0 负值，分布 P50=16.787 ms）**但物理意义（真实时延）Unverified**（跨设备时钟偏移未证，绝对值可能含固定偏移）；**PDR/PER Verified**（sender-base 独立复算与 `per_ue_loss_pct` 字段逐 run 一致，分母=发送数、接收机会=运行内，明确可复算）；信道占用 Documented（停车场低负载 P50 5%/max 23%）。`extra=1` 插值行已按规则排除。正式校准**暂不冻结**；建议条件性批准下一批 `emulating_applications`（4.89 GiB，BSM 场景+GNSS 可能提供时钟参照）。作者咨询邮件草稿已备未发。零超范围下载，Gate 不变。结果 `RES-STAGE-0.4-SEE-V2X-MINIMAL-V1`；报告 `docs/STAGE_0_4_TASK_0_4_6_SEE_V2X_MINIMAL_VALIDATION.md`。

2026-10-17（AAD-0.4.6.1，科学复核）：仅复用 0.4.6 样本独立复核。**PDR 口径修正**：0.4.6 的 `independent_pdr` 用接收窗口口径（排除边界未接收段）系统性高估——**Run 2 完整运行 PDR=0.9737（非 100%）**（发送 5,742/接收 5,591，边界 [0,150] 未接收）；正确口径=**完整运行 PDR**（分母=运行内全部发送），字段 `per_ue_loss_pct`≈接收窗口口径（系统性高 0.3–5 pp）。**时延**：数值复算 Verified，但跨运行固定时钟偏移 P50 8.8–32 ms → **合并分位数不可靠**（降级），逐运行形态相对可信但含漂移（run2 前半−后半 −6.8 ms）。时钟同步凭现有数据不可解（缺共用钟/互偏移/`tx_timestamp` 捕获点声明）。正式校准仍不冻结。下一批 4.89 GiB 建议（目的修正：GNSS 时钟参照+轨迹绑定）。零下载零邮件，Gate 不变。结果 `RES-STAGE-0.4-SEE-V2X-REAUDIT-V1`；报告 `docs/STAGE_0_4_TASK_0_4_6_1_SCIENTIFIC_REAUDIT.md`。

2026-10-17（AAD-0.4.6.2，科学修正+复现修复）：基于 0.4.6/0.4.6.1 的进一步修正。**PDR**：`parameters.csv` 证明 10 运行配置互异（包大小×优先级，发送速率实测 50 Hz）；接收端时长系统性短于发送端且首个接收时戳晚 ~3 s——Run 2 边界 [0,150] 高度符合设备启停而非丢包；**接收机会 Unverified**，完整运行 PDR 仅作描述性指标、不作正式链路丢包率。**时延**：跨运行 P50 差异（8.8–32 ms）由**真实 PHY/MAC 序列化**解释（包大小单调相关：100B 8.8–11、5000B 24–26、8000B 21.8–30 ms），**非时钟偏移**；时钟同步仍 Unverified 但不主导跨运行模式。0.4.6.1 的"跨运行差异=时钟偏移/漂移"过强表述已纠正。**Git 可复现已修复**：`code/tmp/reaudit_*` 入 Git、6 个独立测试通过（Run 2 PDR=0.9737 等）、封存 manifest 补充 method+results。下一批 4.89 GiB 建议（BSM 场景+GNSS；时钟可能仍不可解）。零下载零邮件，Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_6_2_SCIENTIFIC_CORRECTION.md`。

2026-10-17（AAD-0.4.7，BSM 实证）：获取 `emulating_applications.tar.gz`（4.89 GiB，SHA-256 17AB3AC1…0861），提取 BSM+GNSS（峰值 ~10 GiB）。核心结果：①BSM 消息关联 **Verified**（4 场景 × 12 有序设备对，配对率室内 0.998–1.0、室外 0.22–1.0，128B/10 Hz，设备 rsu=1/t1=2/t2=3/t3=4）；②PDR 接收机会**已证**——GNSS 窗口（t1/t2/t3 各 9,631 s）覆盖全部通信时间戳（100%），室外 PDR 0.22–0.90 为真实投递、非启停；③GNSS 时间对齐 Verified（同 UTC 纪元，无任意偏移拟合），但 mobile-mobile 距离全在 0–50 m，**距离×PDR 曲线动态范围不足**；④时延数值 Verified，时钟 epoch 一致但**亚毫秒相位同步 Unverified**，绝对值不冻结。前置修复：Git 复现测试路径改读已提交 `code/tmp/reaudit_results.json`，本机 6/6、纯克隆 5 算术测试真实通过 + 1 原始数据测试 skip。价值：受控 PC5 候选参数（非正式校准）。零超范围下载，Gate 不变。结果 `RES-STAGE-0.4-SEE-V2X-BSM-V1`；报告 `docs/STAGE_0_4_TASK_0_4_7_SEE_V2X_BSM_VALIDATION.md`。

2026-10-17（AAD-0.4.7.1，科学复核+交付修复）：修正 0.4.7 三处过度解释并完成 GitHub 交付。①**概念混淆修正**：配对率（Rx→Tx 匹配）=1.000 vs 接收比例（Rx/Tx）=0.22–1.0，已分开报告（48 对全量机器可读）；②**GNSS≠接收机在线**：GNSS 仅覆盖室外、RSU 静态单点、室内无 GNSS；无无线模块状态证据 → 真实链路 PDR 与接收机会全部 Unverified；③**时钟纪元歧义**：tx_timestamp(µs) 与 GNSS UTC_ns 差 ×1000，纯数值对齐非独立时钟证据 → 绝对时延 Unverified；④**距离**：仅室外 ~0–10 m（室内无 GNSS），不足建距离—PDR。**GitHub 交付修复**：0.4.7 commit 仅含 2 文件（报告等未暂存），已补齐；test 路径修复（纯克隆 5 算术测试通过）；新结果 `RES-STAGE-0.4-SEE-V2X-BSM-REAUDIT-V1`。零下载零邮件，Gate 不变。报告：`docs/STAGE_0_4_TASK_0_4_7_1_SCIENTIFIC_REAUDIT.md`。
