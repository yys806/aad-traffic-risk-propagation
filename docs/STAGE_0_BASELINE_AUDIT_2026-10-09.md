# Stage 0 基线核查报告（2026-10-09）

本报告是对 AAD 当前仓库、机器产物和 `dataset/` 文件的只读核查。外部研究设计文件《04数据集与仿真平台.md》仅作为待落实设计对照，不作为已完成事实。I-80、Peachtree 和 SPMD holdout 仅执行文件级元数据与完整文件哈希核验；未解压、未读取科学内容、未运行统计，也未改变划分。

## 1. 数据文件核验

大小使用文件系统字节数；十进制 MB/GB 分别除以 10^6/10^9，二进制 GiB 除以 2^30。哈希均为本机 `Get-FileHash -Algorithm SHA256` 完整文件计算，并与仓库历史下载清单 `docs/归档/真实数据与NC文献调研/download_manifest.md` 一致（该清单是已知校验依据，不是外部重新下载证明）。

| 数据/用途 | 实际路径 | 存在 | 字节 | MB | GiB | SHA-256 |
|---|---|---:|---:|---:|---:|---|
| NGSIM US-101（Stage 0.2 校准） | `dataset/NGSIM/US-101-LosAngeles-CA.zip` | 是 | 327,638,049 | 327.638 | 0.305 | `830442BB08F1F7A20A686B5879B4B82BFB7C47E526D48908DB666FCCC7E811DC` |
| NGSIM Lankershim（Stage 0.2 校准） | `dataset/NGSIM/Lankershim-Boulevard-LosAngeles-CA.zip` | 是 | 184,896,776 | 184.897 | 0.172 | `757C693BA72B7C8BA7561EE1B5107DFA7119CC4862584A4F033AA445246C56C1` |
| NGSIM I-80（锁定留出） | `dataset/NGSIM/I-80-Emeryville-CA.zip` | 是 | 441,781,993 | 441.782 | 0.411 | `B274BB96F20C971E37651E73CA0F86677FDA8009E22885E71322716ECA84FF73` |
| NGSIM Peachtree（锁定留出） | `dataset/NGSIM/Peachtree-Street-Atlanta-GA.zip` | 是 | 50,677,241 | 50.677 | 0.047 | `91B9B1D4ED1D261E8C525DF536ADC466B6844FF49DC6FB08B815C735FE072A2F` |
| pNEUMA d1 08:00–08:30（城市运动学校准） | `dataset/pNEUMA/20181101_d1_0800_0830.csv` | 是 | 73,509,485 | 73.509 | 0.068 | `F9CDE0A3CA5010E2217EA4CBC0BDF26ED87BE1EC0D8C2BE5E2CB93AAC82BA28C` |
| SPMD RV_RX（接收状态；按行程划分） | `dataset/SPMD/selected/RV_RX.csv.zip` | 是 | 783,804,721 | 783.805 | 0.730 | `9E5E7A3842B15ADC08366D1AFE098224C912D3C593A70D4BB4071088749AB56E` |

**总计：1,862,308,265 bytes = 1,862.308 MB = 1.862 GB = 1.734 GiB。**

## 2. Stage 0.1–0.6 状态对照

| 阶段 | 当前状态 | 已核验的实现/证据 | 缺口与边界 |
|---|---|---|---|
| 0.1 基础设施 | **Verified（工程 בלבד）** | `code/src/riskprop/stage_0_1_sumo.py`；`run/analyze/compare_stage_0_1_*`；`RES-STAGE-0.1-INFRASTRUCTURE-V3`。四格隔离、时间对齐、车辆生命周期和处理前等价性通过。 | 证据中的拓扑为 disconnected；物理路径未接通，不能作为科学效应结果。 |
| 0.2 NGSIM | **Active，未收口** | `run_stage_0_2_ngsim.py` → `ngsim_risk_calibration.py` → `real_trajectory.py`；当前读取 US-101 三窗口及 Lankershim。现有包报告可测 TTC/DRAC 与候选事件，holdout 未解锁。 | 异常/极端值追溯、状态比例、最终分位数/事件频率、候选规则敏感性和适用边界尚未形成当前新审计包。候选 TTC=2.0 s 是工程审计参数，不是冻结科学阈值。 |
| 0.3 pNEUMA | **Not started（新职责）** | `read_pneuma_wide()` 能解析“4 个元数据 + 6 字段状态块”；`test_real_trajectory.py` 覆盖结构读取。 | 无专用统计入口、质量审计、分车型/逐车分布表、正式 config/audit；不得使用旧 map-match/人工复核产物。停车阈值、异常处理和 SUMO 映射仍需研究者确定。 |
| 0.4 SPMD | **Verified（有限边界）** | `communication_observability.py`；`profile_stage_0_4_rv_rx.py`；`RES-STAGE-0.4-COMM-OBS-V3`。按 `DeviceID+Trip+RV_ID` 检查接收状态连续性，校准组按 SHA-256 行程分层。 | RV_RX 不是逐包发送/接收记录；断点不等于丢包，无已验证采用字段。Packet 访问记录为当前环境官方入口 403，packet schema、时延、丢包和采用均不可观测。 |
| 0.5 仿真—现实覆盖 | **Active，待 SUMO 样本** | `simulation_real_coverage.py` 提供稳定哈希抽样、真实—真实 Energy Distance 基准和分层覆盖 gate；`prepare/run_stage_0_5_*` 为入口。 | `RES-STAGE-0.5-REAL-REF-V1` 是迁移前部分参考，来源含旧 pNEUMA map-match；没有新职责下的 SUMO 校准样本，不能宣称 coverage 通过。覆盖阈值和容差不能由 Codex 自行确定。 |
| 0.6 数值验证/协议锁 | **Technical checks Verified；Gate blocked** | `prelock_metrics.py`、`prelock_validation.py`、`protocol_lock.py`；解析真值、物理路径真值和步长检查已有证据。 | 科学容差、`delta_eq`/`delta_R`/`delta_plan`、样本量及分析规则未冻结；旧 readiness 是迁移前 blocker 快照。协议锁未创建，Stage I 禁止启动。 |

## 3. 已有成果、缺口与冲突

可继续作为工程或测量证据使用的内容：四格运行隔离/时间/生命周期测试；NGSIM 的前车匹配、净间距、闭合速度、TTC、DRAC 和连续候选事件实现；pNEUMA 宽表解析器的结构测试；SPMD 接收状态连续性及不可观测边界；Stage 0.6 解析真值、物理路径真值和步长收敛技术检查。它们均标记 `scientific_claim_eligible=false`，不能支持核心效应结论。

不能继续作为最终 Gate 的内容：NGSIM 迁移前 audit 的未收口异常/极端值结论；pNEUMA 旧地图匹配和人工 QA 结果；Stage 0.5 旧真实参考包；迁移前实验键（E15/E16/E17/E01）的 readiness 快照。旧结果保留用于历史追溯，不接回当前正式入口。

本次核查发现的主要文档/实现差异是“研究设计要求”与“当前状态”之间的未完成项，而非已批准的算法冲突：设计要求 pNEUMA 专用统计、正式 SUMO 校准样本和 Stage 0.6 科学冻结；当前源码仅提供底层解析/覆盖/技术检查。pNEUMA 前车推断与人工复核已由研究者于 2026-09-10 明确退役，当前设计对照应按“城市运动学 בלבד”解释。

## 4. 后续实施清单（依赖顺序）

1. **Stage 0.2 收口（部分完成）**：在 `ngsim_risk_calibration.py` 现有输出上补充异常原因/极端值审计、分场景分位数、事件频率和规则敏感性；依赖校准文件及不打开 holdout；验收为新 `stage_0_2` audit、config、manifest、provenance、SHA256SUMS。风险阈值和最终事件规则需研究者决策。
2. **Stage 0.3 专用统计（尚未实现）**：基于 `real_trajectory.read_pneuma_wide()` 建立城市运动学质量标记、逐时刻/逐车和车型统计；依赖停车阈值、异常标记和车型样本最低解释规则的研究者决定；验收为标准化表、质量 audit、分布表/图、冻结输入 manifest。
3. **Stage 0.4 边界冻结（部分完成）**：保留 RV_RX 有限证据边界，记录 Packet 获取状态；只有取得并验证可关联的官方 Packet/发送侧表后才扩展 packet 级结论；验收为当前 `pass_limited` 或明确 `pending` 的新 status 包。不得把外部访问失败当作 schema 失败。
4. **Stage 0.5 重建与 SUMO 校准样本（尚未完成）**：先使用新 Stage 0.2/0.3 参考包，再运行无消息作用的 SUMO 基础场景并保存状态样本；依赖场景、车型、参数候选和 coverage 验收标准的研究者决定；验收为新 real reference、SUMO sample、coverage audit 和独立验证记录。
5. **Stage 0.6 科学冻结与 readiness 重算（尚未完成）**：在 0.2/0.4/0.5 证据齐备后，由研究者确定科学容差、效应阈值、样本量、右删失/失败纳入与分析规则；再用当前 `stage_X_Y` 键重算 readiness。验收为四个 Gate 报告一致、readiness `protocol_lock_allowed=false` 仅在缺口存在时保持，且不生成 Protocol Lock。
6. **Stage I 准入（被阻断）**：只有研究者确认完整 Protocol Lock 并完成所有准入条件后，才可设计/实现/运行 Stage I；本次不执行。

## 5. 当前关键阻断与待决策问题

- NGSIM 异常/极端值的质量分类、事件阈值与敏感性比较规则；
- pNEUMA 停车判定、异常保留/标记、车型样本充分性与 SUMO 车型映射；
- Stage 0.5 的场景参数、校准/独立验证拆分、覆盖阈值和容差；
- Stage 0.6 的 `delta_eq`、`delta_R`、`delta_plan`、显著性/功效和 Stage I 样本量；
- 是否能取得可验证的 SPMD Packet/发送侧字段，以及其是否足以改变当前有限证据边界。

上述均属于科研设计或证据获取决策，报告不替研究者取值。当前 Protocol Lock 未创建，Stage I 未启动。

## 6. 核查范围与未处理事项

未读取六个文件的科学内容；未解压锁定留出集；未运行大型实验、pNEUMA/SPMD 统计或 SUMO 正式校准；未修改算法、配置、测试或私人研究笔记。仓库工作区在审计开始前已有论文文件删除和未跟踪文件，本次不处理。

