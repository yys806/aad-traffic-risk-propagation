# Stage 0.4 任务 0.4.5：真实 V2X 通信数据最小验证与获取准备

> 任务 AAD-0.4.5（只读核查，2026-10-17）。**零数据下载、零访问申请**；Stage 0.4 Gate（`pending_official_packet_access`）、科研参数与全部封存证据未改动。标注：Fact（实测/文档明确）/Documented（官方文档）/Inference（多证据强推）/Unverified/Unresolved（缺证据）/Proposal（建议）。

## 0. 执行摘要（直接回答六个问题）

1. **SEE-V2X 能不能用？** 能，且是**首选**——见 §2。`latency = rx_timestamp − tx_timestamp`（µs）**在同一台接收设备的日志内成对给出**（该日志同时携带 `tx_timestamp` 与 `rx_timestamp`，且 `tx_seq_num` 提供同消息配对）——**不依赖跨设备时钟对齐**，配对与差值均在接收端单设备内完成。时钟同步架构未文档化（Unverified），但对**差值法**影响仅限两端各自漂移之差（小）。PDR/PER 的 `per_ue_loss_pct` 分母定义**未文档化**（需下载后实证）。获取：**公开 Google Drive 共享，无需申请**。
2. **Bristol ITS-G5 能不能用？** **不能用于时延**。论文**零延迟分析**；`Timestamp`="CAM 创建时刻"，**各设备独立时钟且无论文级同步方法**——跨设备时延不可计算（任务 §二.B 的警告完全应验）。**仍可用于 PDR/RSSI**（PDR 按 RSSI 聚合、成对交互由唯一 SeqNum+MAC 匹配，论文方法明确）——但**不是**时延数据源。
3. **哪个更值得先下载？** **SEE-V2X**。理由：单设备日志内配对时延（证据链完整、不依赖跨设备时钟）、自带 PDR/jitter/信道占用、含 BSM 仿真场景与 GNSS；体量小（**最小样本仅 4.9 MB**）；公开免申请。
4. **最少需要多少空间？** 最小验证 **<0.5 GiB**（SEE-V2X `outdoor_parkinglot.tar.gz` 4.9 MB，解压+处理峰值）；完整可用 **≈10 GiB**（emulating_applications 4.89 GiB + 全部 parameters_sweeping 18.76 GiB 可选）。
5. **下载后首先验证什么？** ①`outdoor_parkinglot` 样本的 rx csv 字段完整性与 `latency` 分布；②`per_ue_loss_pct` 的分母语义（需用 `tx_seq_num` 间隙独立复算 PDR 对比——若一致则分母=发送序列，可校准；若不一致则保留 Unverified）；③`tx_seq_num` 唯一性/循环；④GNSS 轨迹与信道占用字段可用性。
6. **还有什么尚未解决？** ①SEE-V2X `per_ue_loss_pct` 分母语义（下载后实证）；②时钟架构未文档化（差值法低风险，绝对时刻对齐不可宣称）；③Bristol 跨设备时延不可计算（已定论，不再尝试）；④BsmMd 批次（0.4.3）仍待批准。

---

## 1. SEE-V2X（任务 A）——字段、时间语义与时钟证据

### 1.1 数据源与结构（Fact，GitHub README 官方）
- 官方仓库 `UCR-CISL/SEE-V2X`（SenSys'25，DOI 10.1145/3715014.3722077）；项目站 `cisl.ucr.edu/SEE-V2X/`。
- **获取：公开 Google Drive 共享文件夹（无需申请、无需表单）**——本任务以元数据请求（`Range: bytes=0-0`/`Content-Range`）核实了文件存在性与精确大小，未下载数据内容：
  - `emulating_applications.tar.gz` = **5,252,105,816 B（4.89 GiB）**（含 BSM-only / Perception-only / BSM&Perception × Indoor/Outdoor + GNSS）
  - `parameters_sweeping/`（子文件夹，5 个 tar.gz）合计 **20,139,944,998 B（18.76 GiB）**；其中 **`outdoor_parkinglot.tar.gz` 仅 4,883,437 B（4.9 MB）**——最小验证样本
  - 首 4 字节 `1f 8b 08 08` = 标准 gzip（tar.gz）魔数（Fact）。
- 场景：参数扫描（室内全配置/时延扩展/优先级 + 室外停车场）+ 应用仿真（BSM、感知、混合）；GNSS 100 Hz（应用仿真场景）。

### 1.2 字段级证据表（Documented，README）

| 字段 | 文件 | 定义（README 原文要点） |
|---|---|---|
| `tx_timestamp` (µs) | `rx_[UE1]_tx_[UE2].csv` | 发送时间戳（**与 `tx_seq_num` 同行，接收端日志内成对**） |
| `rx_timestamp` (µs) | 同上 | `latency = rx_timestamp − tx_timestamp`（**README 明确定义**） |
| `latency` (ms) | 同上 | 端到端时延（上式；**bold 标注为分析便利列**，原始可复算） |
| `per_ue_loss_pct` (%) | 同上 | UE2 的丢包率（**分母/接收机会定义未文档化 → 需实证**） |
| `ipg` (ms) | 同上 | 包间抖动 |
| `tx_equipment_id`/`tx_seq_num`/`tx_priority`/`tx_timestamp` | 同上 | 发送方身份/序号/优先级/时间——**同消息配对键齐全** |
| `channel_busy_percentage` | tx & rx | 信道占用（接收端报告） |
| `avg_throughput(10ms/100ms)`、`avg_packet_loss(10ms/100ms)` | 同上 | 分析便利列（非原始） |
| `extra` | 同上 | 1=脚本插入行，0=原始 |
| `mac.pcap` / `sci.csv` | 各场景 | MAC 层（USRP B210）+ 侧链控制信息（µs 时间戳、MCS、重传等） |

### 1.3 同消息配对与时钟（关键判断）

- **同消息配对：Documented。** `tx_seq_num` + `tx_equipment_id` 在接收端日志内唯一标识一条发送记录；`latency` 由 README 定义为同行 `rx_timestamp − tx_timestamp`。配对**不需要**跨设备对齐（两端时间戳被记录进同一行）。
- **时钟同步：Unverified（架构未文档化）。** 公开材料未说明共用钟/GNSS-PPS/PTP 或实测互偏移。GNSS 100 Hz 轨迹存在，但不能反推主机日志共用同一 epoch。影响分析：对**差值法**（rx−tx 同行），常数偏移相消，残余仅为两端**漂移速率之差**在包间隔内累积（通常可忽略；室内短时试验更低）。因此 **latency 分布形态（抖动、尾部分位）可靠**；**绝对值若存在固定偏移会平移整个分布**——若 AAD 需要亚毫秒绝对时延，需下载后用 SCI 空口时间戳或共触发事件估计互偏移（列为下载后验证项）。不得仅凭 `latency` 字段存在即宣称测量可靠（本任务已按要求核查其差值结构与记录点）。

### 1.4 PDR/PER 可计算性

- 字段 `per_ue_loss_pct` 给出每发送方丢包率，但**分母（发送基数）与接收机会定义未在 README/论文摘要中给出**（如是否为窗口内期望包数、是否剔除设备未发送时段）。**可计算性 = Potential（字段在）＋需实证（分母语义）**。
- 独立复算路径：由 `tx_seq_num` 序列在接收端日志中的间隙数期望包数，与 `per_ue_loss_pct` 对照——一致则可作为校准依据；不一致则保留 Unverified（下载后验证项②）。

### 1.5 技术/环境

C-V2X 侧链 PC5（3GPP LTE Rel.14 Mode 4）；商用 COTS 标准电台；室内参数扫描 + 室外停车场/路口；应用仿真含 BSM 10 Hz 类流量。**受控/半受控条件，非自然密集交通**——对 SUMO 损伤模块是"干净的单跳 PC5 现实先验"，不得与自然 V2V 场景指标混用（延续 0.4.4 边界）。

## 2. Bristol ITS-G5 FLOURISH（任务 B）——时延否定 + PDR/RSSI 保留

### 2.1 关键否定结论（Fact，论文 arXiv:1903.10289 全文核查）

| 问题 | 结论 | 证据 |
|---|---|---|
| Tx/Rx 由什么设备记录、时间戳对应何事件 | Tx 与 Rx 分别由**发送/接收设备各自记录**；`Timestamp`="**CAM 创建时刻**"（非 RF 到达、非接收时刻） | 论文变量表："Timestamp — Timestamp at the moment of creation of a CAM" |
| `StationID+SeqNum` 是否足以唯一匹配 | 每会话内 SeqNum 唯一 + 发送 MAC → **PDR 配对可行**（论文 `v2vInteractions` 脚本方法）；但**用于时延差需跨设备时间戳** | 论文 §Dataset Value + 方法段 |
| **跨设备时钟同步** | **论文与 README 均未提供同步或校正方法**（全文无 NTP/GPS-sync/offset 描述） | 论文全文检索 0 命中 |
| **能否得到端到端时延** | **不能。** 两台设备独立记录"创建时刻"，无时钟同步 → 跨设备差值无意义；且论文**零延迟分析**（全文无 latency/delay/RTT） | 任务 §二.B 警告应验 |
| 发送频率 10 Hz vs 10 ms | **10 ms（=100 Hz）**。论文明确 "broadcast a CAM every 10 ms"；0.4.4 中"CAM 10 Hz"为 readme/页面表述误差，**以论文为准** | 论文 Experimental Design 段 |
| PDR/PER 发送基数与统计规则 | **Documented**：每收发 CAM 记录 RSSI+位置；PDR 按 RSSI 聚合（MAC 层 PDR，论文明示"calibrate simplified physical layers where MAC PDR is a direct function of RSSI"）；配对用唯一 SeqNum+MAC | 论文摘要 + 方法段 |

**结论：Bristol 可用于 PDR=f(RSSI) 与交互配对统计（受控城市测试床），但不可用于通信时延。** 0.4.4 将其列为"时延候选"**不准确**（勘误见 §4）。

### 2.2 获取与最小子集

- 完整 zip **34.3 GiB**（data.bris.ac.uk，NC 许可）；含 `importedData`（MAT，预处理小体积）。**individual 子数据集下载**（如单日单设备 MAT）可低至 GiB 级以下——但鉴于时延不可用、PDR/RSSI 可由 SEE-V2X 与 UCI 更小成本覆盖，**Bristol 的下载优先级下调**（除非研究者明确需要 PDR=f(RSSI) 的城市测试床曲线）。

## 3. 比较与科研判断（任务 §三）

| 判据 | SEE-V2X | Bristol ITS-G5 |
|---|---|---|
| 计算时延的必要条件（同消息配对+双侧时间+时钟） | **具备（配对在单设备日志内成对，差值法不依赖跨设备钟）**；绝对偏移待实证 | **不具备（跨设备独立钟+无同步+非接收时刻）** |
| 可靠 PDR/PER | 字段在，**分母语义需实证**（可独立复算） | **Documented**（SeqNum+MAC 配对、RSSI 聚合） |
| 已被文档证明 | 字段定义、latency 公式、同日志成对、跨层 trace | PDR 方法、RSSI、配对；**非时延** |
| 需原始数据验证 | `per_ue_loss_pct` 分母、`tx_seq_num` 唯一性、时钟架构 | —（时延已否定） |
| 时钟同步证据不足时仍可分析 | latency **分布形态**/jitter/信道占用/PDR（差值法）；绝对时刻对齐不可宣称 | PDR/RSSI/交互计数 |
| 最小下载 | `outdoor_parkinglot.tar.gz` 4.9 MB | importedData 子集（GiB 级） |
| **适配 AAD 首发校准** | **是（C-V2X PC5 时延/PDR/信道）** | 仅 PDR-RSSI（备选） |

**明确推荐：SEE-V2X 为第一批**；Bristol 仅在为 PDR=f(RSSI) 目的时作为第二备选。

## 4. AAD-0.4.4 勘误（任务 §二.C）

1. **Bristol "Tx/Rx 双侧时间戳齐全、可算时延"——不成立。** 论文零延迟分析、`Timestamp`=创建时刻、无跨设备同步方法。更正：Bristol 为 **PDR/RSSI 候选**，非时延候选。（0.4.4 报告与清单相应更正。）
2. **Bristol 发送频率**：更正为 **100 Hz（每 10 ms）**（论文为准）。
3. **UCI DSRC #415 的实测/仿真属性——Unverified。** UCI 页面未注明；捐赠者研究背景含 DSRC 建模工作，但**无公开证据表明该 PER 样本来自真实实测**。在确认为实测前，**不得作为真实丢包率的校准依据**（降级为"待核实"）。
4. **THEA/Tampa 与 WYDOT 来源混淆——更正。** 官方 CV Pilots 2024 Update 原文："Drivers reduced speed within 3 seconds of receiving a Forward Collision Warning (FCW) for **85% of FCW events**" 归于 **WYDOT** 站点；Tampa/THEA 的结果为 **50%** 的司机在冰雪/天气**告警**后减速（不同应用）。0.4.4 将 85% 记为 Tampa 系**来源混淆**，予以更正；两者均为**驾驶员告警后减速**，**不能认定为消息被因果采用**（任务原则重申）。

## 5. 推荐第一批最小验证方案（任务 §五）

**对象**：SEE-V2X，最小样本 `parameters_sweeping/outdoor_parkinglot.tar.gz`（**4.9 MB**）。**总峰值磁盘 <0.5 GiB**；随后按需取 `emulating_applications.tar.gz`（4.89 GiB，峰值 ≈10 GiB）。

**验证步骤与成功标准**：
1. 解包 `outdoor_parkinglot.tar.gz`，列出场景文件（`tx_*.csv`、`rx_*_*.csv`、`mac.pcap`、`sci.csv`、`parameters.csv`）。成功=文件齐全、csv 可解析。
2. 字段完整性：rx csv 含 `rx_timestamp/latency/tx_seq_num/tx_equipment_id/per_ue_loss_pct/channel_busy_percentage`。成功=字段与 README 一致、单位标注（µs/ms）正确。
3. **同消息配对核验**：按 (`tx_equipment_id`,`tx_seq_num`) 检查 rx 日志重复率（应低）；抽样对照 tx csv 的 `seq_num`。成功=配对唯一性成立。
4. **latency 分布**：计算 `rx_timestamp−tx_timestamp` 与 `latency` 列一致性（应相等）；给出分布（中位/P95/max）。成功=两者一致、无负值异常占比。
5. **PDR 分母实证**：由 `tx_seq_num` 间隙独立复算每发送方 PDR，与 `per_ue_loss_pct` 对照。成功=一致或在文档化容差内 → 分母语义澄清，可作校准；不一致 → 标记 Unverified，仅用作相对指标。
6. （可选）`emulating_applications` 的 BSM-only 场景：GNSS 轨迹 + 信道占用 + BSM 类流量时延/PDR，直接映射 SUMO 通信损伤参数。

**失败替代**：若配对唯一性差或分母不可澄清，则 SEE-V2X 降级为"信道占用/抖动参考"，时延/PDR 转求 NIST C-V2X 互通数据集（TN 2315）或回归受控综述；Bristol 仅作 PDR-RSSI。

## 6. 尚需研究者批准

1. 下载 SEE-V2X 最小样本（4.9 MB）+（建议）`emulating_applications`（4.89 GiB）。
2. 是否将 Bristol 降级为 PDR-RSSI 备选（不再为时延目的下载）。
3. 是否按 0.4.3 继续 BsmMd（SPMD 身份）批次。
4. 是否联系 SEE-V2X 作者索取时钟同步/分母语义的配置说明（加速验证）。

## 7. 对 0.4.4 报告/清单的同步更正（本次提交一并完成）

- `docs/STAGE_0_4_TASK_0_4_4_COMMUNICATION_EVIDENCE_SEARCH.md`：Bristol 时延主张勘误、频率更正；UCI 属性标记 Unverified；THEA/WYDOT 归属更正。
- `docs/research/stage_0_4_dataset_candidates.json`：同步字段与新增 `batch_A_see_v2x` 计划。
