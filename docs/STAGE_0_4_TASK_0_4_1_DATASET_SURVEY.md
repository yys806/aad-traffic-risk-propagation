# Stage 0.4 任务 0.4.1：通信数据源全面调查与下载前可行性评估

> 任务编号 AAD-0.4.1；调查日期 2026-10-16（**勘误 2026-10-16**：原稿误记 2026-10-16；真实执行日由 git commit 80f92fb=2026-10-16 20:01 +0800 证明）（Asia/Shanghai）。本任务**只调查、不下载**：未获取任何新数据内容，未提交任何访问申请，未改动 Stage 0.4 已封存结果（`RES-STAGE-0.4-COMM-OBS-V3`，`receive_state_continuity_only`，Gate `pending_official_packet_access` 均不变）。
> 结构化数据源清单：`docs/research/stage_0_4_dataset_candidates.json`（含逐数据集 8 项科研需求证据等级、下载优先级与核验日期）。
> 外部状态核验方式：官方门户公开页面、Socrata 元数据 API（视图 JSON 与 count 聚合，无记录内容）、HEAD/重定向检查；本地已取得的官方手册（SHA-256 钉扎）与 4 个配套表（calibration 范围）。

## 1. 当前项目通信证据缺口（基线）

Stage 0.4 已验证：SPMD `RV_RX`（17,481,111 行 / 7,601 设备-行程）支持**接收状态连续性**，且仅此而已。不可观测：packet 级发送—接收关联、通信时延、丢包、控制器采用。AAD 后续（消息生命周期验证、时延/丢包敏感性实验、Stage 0.6 协议检查）需要的最小证据链是：

**发送事件（谁、何时、何种消息）→ 接收事件（谁、何时）→ 可靠配对 → 同步时钟 → 明确分母 → 机会条件 → 采用/响应。**

当前只有"接收侧状态流"一环。下文评估每个候选数据源能补上哪几环。

## 2. 任务 A：SPMD 剩余数据调查（最高优先级）

### 2.1 官方来源重新核实（2026-10-16）

- 官方条目：`Safety Pilot Model Deployment Data`，data.transportation.gov 视图 `deww-aa3r`，DOI **10.21949/1504482**，官方推荐引用已给出；发布方 USDOT ITS JPO；范围 Ann Arbor, MI，2012-10-01 至 2013-04-30。
- **视图状态变化**：该视图约于 2026-01-07 重建（createdAt 1767731083），当前**无附件**（历史上挂两份 DOCX 手册——本地已持有且 SHA-256 钉扎，继续以本地版本为准）。
- **访问状态变化（重要）**：历史记录中 Packet 下载端点返回 HTTP 403；当前 `https://data.transportation.gov/download/deww-aa3r/application%2Fx-zip-compressed` 返回 **302 → 官方文件 API**（blob id `9a19fca6-465a-4247-ad4c-28c67cf7ef8b?filename=SPMD.zip`）。对 blob 端点的 HEAD 请求在 120 s 内未返回响应头——**无法在不获取数据内容的前提下确认最终可达性**。结论：状态为"重定向正常、最终可达性待验证"；此前使用的 Range 请求读取 ZIP64 中央目录的方法需在下一个获授权的下载任务中对新 blob 重新验证。本任务未做任何 Range/内容请求。
- 主包完整大小（历史记录）：117,346,016,961 B，46 个成员。成员级选择下载是已验证的先例（RV_RX + 4 个配套表即由此取得）。

### 2.2 Packet（15.33 GB）——官方字典结论

来源：官方样本手册 RSE Dataset §6.6（本地，SHA 钉扎），字段级证据：

- **一条记录 = 在某个路侧设备（RSE）捕获的一个数据包**；包由车载 OBU 发往 RSE；含 `PacketTimestamp`（GMT，秒）+ `TimestampMicroseconds`（微秒补足）——**单一 RSE 捕获时钟**。
- 字段：PacketId、PCAPFileId（→ 本地 PCAPFile 表可定位 RSE 位置与抓包会话）、PacketNumber/Location、长度、**SourceIPAddress（官方注明 non-constant，即轮换 IP，非稳定发送方身份）**、EtherType、WSMPVersion、**Channel、DataRate（MB/s）、PowerUsed（dBm）**、**PSID（消息类型，0x20=BSM）**。
- **能支持**：RSE 侧捕获事件与时间（单钟）、消息类型区分（PSID）、信道/速率/功率等通信条件、与 PCAPFile 的 RSE 空间锚定。
- **不能支持**：发送时刻（无发送时间戳）、稳定发送方身份（IP 轮换且无 TxRandom/MsgCount）→ **Packet 单独不能算端到端时延**；时延需与 BsmP1 的 Gentime（生成时刻）配对，且依赖跨设备时钟同步证据——两者均未在文档层面证明。
- **丢包**：RSE 捕获集合 ≠ 发送基数；单接收点环境；无接收机会模型时"未捕获"≠丢包。

### 2.3 BsmP1（55.72 GB）——官方字典结论

来源：官方样本手册 BSM Dataset §5.1/§5.4 + 历史 UMTRI WSU/Rx 代码本证据（`docs/归档/真实数据与NC文献调研/spmd_field_audit.md`）：

- 19 字段：**RxDevice（记录设备）、TxDevice（发送设备）、Gentime（1609.2 安全时戳，毫秒；官方给出换算公式：/1,000,000 − 35 s 偏移，纪元 2004-01-01）**、**TxRandom（轮换匿名发送 ID）、MsgCount（逐条 BSM 递增序号）**、DSecond（点火后分秒，发送端时钟）、位置/运动（纬经高/速度/航向/三轴加速度/yaw）、路径曲率。
- 10 Hz，BSM Part I 主体 + 少量 Part II；数据来自 CAN 总线经车载 WSU 发出。
- **能支持（文档层面）**：发送方身份（TxDevice/TxRandom）、逐消息序号（MsgCount）、**生成时刻（Gentime，含官方换算）**、发送时车辆状态——即**发送侧基数与消息身份的全部候选字段**。
- **关键未验证问题**：RxDevice 语义表明存在"记录设备"，但 BsmP1 行是否包含**从其他车辆收到**的 BSM（多接收方记录）还是仅自车发送日志，官方文档不明确，必须以实际数据核验（UMTRI 另有独立的 Rx BSM 代码本，提示接收侧可能是独立数据集）。这直接决定 BsmP1 能否提供接收侧时间（从而影响时延路径设计）。
- **时延结论**：若同一消息（TxRandom+MsgCount）被多个 RxDevice 记录且 Gentime 为记录时刻，或与 Packet/RSE_BSM 的捕获时刻可配对，则时延在结构上可行——但**跨 WSU、WSU↔RSE 的时钟同步未在任何官方文档中给出**，是全部时延主张的共同前置条件。

### 2.4 被忽视的候选：RSE_BSM（3.23 GB）

- 官方手册 RSE Dataset §6.1：RSE 接收范围内车辆发来的 BSM **内容**记录；字段含 **TemporaryID（4 字节轮换匿名发送 ID）、MsgCount、DSeconds（发送端毫秒-分钟内时钟）** + J2735 Part I 全量运动/制动状态；样本显示 BSMID 为逐行唯一 ID。
- **注意**：手册称 28 字段而表格仅列出/样本仅显示 24——**4 个未文档化字段**（可能含 RSE ID 或接收时间戳）必须在下载后首先核验；文档层面**没有**记录 RSE 接收时间戳。
- 价值：**固定基础设施接收点**的 BSM 内容 + 消息身份字段，体量仅为 Packet 的 1/5、BsmP1 的 1/17；若未文档化字段含接收时间或可与 Packet 经 BSMID/PCAP 关联，将成为最便宜的"接收侧消息级"证据。

### 2.5 已取得配套表的核实价值（本地实测 2026-10-16）

- `TripFact` / `BsmP1Summary` / `DataWsuSummary`：逐 DeviceID-TripID 的 **Epoch 起止时间**、里程、速度（WSU 另有 BrakeCount/WiperActivated）→ 覆盖窗口、设备-行程关联、绝对时间锚。
- `PCAPFile`：PCAPFileId → `Savari-LocID<NNNN>_dsrc1_out_<时间>.pccap` 文件名与抓包时间 → **RSE 位置/会话识别**，是 Packet.PCAPFileId 的连接目标（注意：该表无表头，首行即数据）。
- 均不提供发送/接收事件本身。

### 2.6 RV_RX 既有边界（不变）

接收状态连续性（Verified）；观测断点≠丢包；无 MsgCount/Gentime/采用字段。本任务不改变该结论。

## 3. 任务 B：其他联网车辆通信数据集

### 3.1 AMCD Basic Safety Message（eezi-v4pm，DOI 10.21949/1504488）

- 官方描述：AMCD 实测项目全部 BSM；官方明确"为行添加了识别**发送方、通信时间、通信模式**等字段，使数据使用者能够准确追踪消息在系统中的传递"；所有 BSM 由 OBU 生成、最终由 **VCC 云服务器**接收。
- 字段（42→28 列，官方 schema）：`obu_id`、**`time_sent`、`time_received`**、`mode_of_transmission`、J2735 Part I 全量、test_no、location。
- 行数：**2,593,113**（count 聚合，2026-10-16）；公开表格、无需登录。
- 证据等级：**发送、接收、同消息配对、时延在文档层面均为 Documented**（同行的 sent/received 时间）——是唯一"每条消息自带收发时间"的公开数据集。**限制**：接收方是云服务器（非车对车）；`time_sent` 的时钟来源（OBU 自报 vs 云端记录）未文档化，直接影响时延有效性；受控实测而非自然交通。无采用字段。

### 3.2 NYC CV Pilot（Volpe IE 处理 EVENT 数据，gu5j-r7xj，DOI 10.21949/1404205）

- 164,131 条 EVENT（2026-09 更新）；每条 = 装备 ASD 的主机上一次**应用告警** + 告警前后录制窗口内的 CV 消息。字段含 HostVehID/TargetID、SeqNumHV/TV、WarningType/WarningStartTime、**Sent/Heard 计数**、TimeRecBefore/After、TTC、天气（WeatherCond/Precipitation/WindSpeed）、**TimeBin/LocationBin/dummytime（时间空间已分箱粗化）**。
- 证据等级：告警触发事件 Documented；环境条件 Documented；**告警 ≠ 控制器采用**（AAD 边界明确，不得混同）；时延 NotObservable（分箱时间）；逐消息配对 NotObservable（事件级）。
- 月度样本（vxmm-9bi5）为强脱敏版（eventtimebin/dayofweekbin/locationbin），全量未扁平化数据需 ITS DataHub Sandbox 申请。当前视图的"数据字典见附件"描述与实际（附件为空）不符——字典需另行获取。

### 3.3 Tampa（THEA）CV Pilot BSM Sample（nm7w-nvbm）

- 34,464 行样本（2025-08 更新）：**RSU 接收的 BSM 记录**，含 metadata（**RSUID、recordGeneratedAt、logFileName**）+ coreData（msgCnt、临时 ID、secMark、运动/制动）+ Part II。
- 全量原始 BSM 需经 ITS DataHub Sandbox 表单申请（官方声明"任何人可申请"，无资格限制，但为人工步骤，本任务不提交）。
- 证据等级：RSE 侧接收 Documented（RSUID 逐行）；`recordGeneratedAt` 语义（生成侧 vs 摄取侧时间）未文档化 → 下载样本后核验。

### 3.4 Wyoming CV Pilot

- data.transportation.gov 上的公开条目为 **Phase 4 LTE-V2X 受控测试**（约 12 个 test-ID 小表：固定车速 70/80 mph、BSM 计数等）——受控实验参考，非自然驾驶；Phase 3 DSRC 车队数据在 Sandbox 内。均列 P2。

### 3.5 ITS DataHub Sandbox（通道性质）

- CV Pilot 全量原始脱敏数据的官方通道；S3 桶匿名列举已验证返回 AccessDenied（2026-10-16）；申请表单免费无限制，但属研究者手动动作。

## 4. 科研需求—数据证据矩阵（摘要）

等级定义：Documented（官方文档明确）/ Potential（跨表关联可能支持，未验证）/ Verified（本地实际数据已复核）/ NotObservable / Unknown。完整逐格矩阵见 JSON 清单。

| 需求 | SPMD 现状(RV_RX) | SPMD+Packet | SPMD+Packet+RSE_BSM | +BsmP1 | AMCD | NYC IE | Tampa 样本 |
|---|---|---|---|---|---|---|---|
| 消息来源 | NotObs | Potential | Documented(TmpID) | Documented(TxRandom) | Documented | Potential | Documented |
| 消息发送 | NotObs | NotObs | Potential(DSeconds) | **Documented(Gentime)** | Documented | NotObs | Potential |
| 消息接收 | Verified(状态流) | Documented(RSE捕获) | Documented(RSE接收) | Potential(RxDevice) | Documented(云) | Potential(事件级) | Documented(RSU) |
| 发送—接收配对 | NotObs | Potential~Unknown | Potential | Potential | **Documented(同行)** | NotObs | Potential |
| 通信时延 | NotObs | Potential* | Potential~Unknown | Potential* | **Documented*** | NotObs | Potential |
| 丢包/投递 | NotObs | Potential | Potential | Potential | Potential | Potential(事件级) | Potential |
| 环境条件 | Documented | Documented(信道/功率) | Documented | Documented(运动) | Documented(受控) | Documented(天气) | Potential |
| 采用/响应 | NotObs | NotObs | NotObs | NotObs | NotObs | Potential(告警≠采用) | NotObs |

\* 时延的共同前置条件：**跨设备时钟同步证据**。SPMD 路径需要 OBU 1609.2 时钟（Gentime，含官方 35 s 偏移换算）与 RSE GMT 捕获时钟的同步性证据；AMCD 路径需要 time_sent 时钟来源。均未文档化 → 全部标 Potential 而非 Verified。

**时延/丢包的原始字段—关联条件—现状答案**（任务 C 要求显式回答）：
- 时延需要：发送时刻字段（BsmP1 Gentime / AMCD time_sent）＋接收时刻字段（Packet 捕获戳 / RSE_BSM 待验证字段 / AMCD time_received）＋同一消息的可靠配对键（TxRandom+MsgCount / AMCD 同行）＋时钟同步证据。当前：字段层面前者 Documented，配对键 Potential，时钟同步 Unknown（SPMD）/ Unknown（AMCD time_sent 来源）。
- 丢包需要：发送基数（BsmP1 全量发送日志）＋接收集合（Packet/RSE_BSM/多 RxDevice）＋接收机会条件（设备能力：VAD 只发不收、ISD/ASD/RSD 可收——UMTRI 文档已给出；通信范围/设备状态）。当前：基数与机会模型均未落地。

**技术混杂因素**（必须在任何分析设计中显式处理）：跨设备时钟不同步（Gentime 35 s 偏移为文档级常数，残余漂移未知）；BSM 10 Hz 广播 ≠ 点对点消息语义；一消息多接收方（广播）；设备日志缺失 ≠ 无线丢包；MsgCount 循环与 TxRandom 轮换的碰撞；重复记录与重传；脱敏后身份跨表不可关联（IP/临时 ID 轮换）；行程边界与设备重启（DSecond 重置）；网络层捕获 ≠ 应用层处理；受控测试 ≠ 自然交通（AMCD/Wyoming P4）。

## 5. 与 AAD 后续实验需求对接（任务 D）

- **D1 Stage 0.4**：Packet 下载后即可完成"packet_schema_evaluated"这一 Gate 预留项；RSE_BSM+Packet 可建立 RSE 侧描述性接收参考；有限科学验收仍以实际可验证的边界为准。
- **D2 Stage 0.5/0.6**：真实时延/投递分布只能作为后续仿真通信参数的**参考候选**；Stage 0.5 现行职责（无消息 SUMO 运动学覆盖）与 Gate 不变；任何固定通信参数若最终无真实数据支持，必须标记为仿真假设，不得声称现实校准。
- **D3 Stage I**：理想 vs 受限通信对照、时延/投递敏感性、消息接收≠采用的区分——AMCD（云接收、多模式发送）与 SPMD（RSE/车侧接收）分别提供不同环节的参考；**Stage 0.4 提供现实通信证据参考，不证明 AAD 因果效应**——采用与因果动作效应在所有已核验数据源中均不可观察，仍属仿真/封闭实验职责。

## 6. 下载优先级与成本（任务 E，决策表）

| 优先级 | 数据 | 体量 | 访问 | 下载后首先验证 | 建议 |
|---|---|---:|---|---|---|
| **P0-1** | SPMD `RSE_BSM` | 3.23 GB | 同主包 blob（Range 先例待重验） | 未文档化 4 字段（RSE ID/接收时间?）；TemporaryID+MsgCount 结构；与 Packet/PCAP 关联键 | **先下载**：最便宜的接收侧消息级证据，其字段核实结果直接决定 BsmP1 是否值得 55.7 GB |
| **P0-2** | SPMD `Packet` | 15.33 GB | 同上 | 表头=官方字典；时间覆盖；PSID 分布；PCAPFileId 连接；IP 轮换统计 | 与 RSE_BSM 同批或随后；packet_schema_evaluated 的直接依据 |
| **P0-3** | SPMD `BsmP1` | 55.72 GB | 同上 | RxDevice 接收语义；Gentime 换算；多接收方重复率；MsgCount/TxRandom 连续性 | **条件下载**：若 RSE_BSM/Packet 核验显示配对可行或研究者接受单批成本则获取；它是丢包分母（发送基数）的唯一来源 |
| P1 | AMCD BSM | ~2.6M 行（表格导出，估计数百 MB） | 公开 API | time_sent 时钟来源；time_received 单位；逐 OBU 收发完整性 | 唯一同行收发时间数据集，验证时延方法论 |
| P1 | Tampa BSM 样本 | 34,464 行（小） | 公开 API | recordGeneratedAt 语义；RSUID 覆盖 | 免费、极小；RSU 接收参考 |
| P1 | NYC IE EVENT | 164k 行（小） | 公开 API | Sent/Heard 语义（字典缺失）；TimeBin 粒度 | 告警事件+环境上下文参考（非采用证据） |
| P2 | NYC 月度样本 | 小 | 公开 | — | 强脱敏，被 IE 表替代 |
| P2 | Wyoming P4 测试表 | 小 | 公开 | — | 受控 LTE-V2X，暂缓 |
| P2 | 完整 SPMD.zip | 117 GB | 同 blob | — | **不必**：成员级下载为先例，另有 ~42 GB 与通信无关 |
| P1(通道) | ITS DataHub Sandbox 全量申请 | 未知 | 表单（研究者手动） | — | 待 SPMD 成员分析明确缺口后再决定 |

**三种 SPMD 方案比较**：① 仅 Packet（15.3 GB）——能评 packet schema 与 RSE 捕获统计，但无发送基数，时延/丢包仍是 Potential；② Packet+BsmP1（71 GB）——字段层面具备时延/丢包全链，但 55.7 GB 的接收语义风险（BsmP1 或无接收侧内容）前置未消除；③ **推荐渐进**：先 RSE_BSM+Packet（18.6 GB）核验关联键与未文档化字段，再决定 BsmP1。若研究者偏好单批完成、接受 71 GB 成本，② 也成立——配对与时钟同步仍需下载后实证。③ 完整包不必要。

## 7. 尚未解决、必须等真实数据确认的问题

1. 新 blob 的 Range 可达性与 46 成员结构是否与历史一致。
2. RSE_BSM 的 4 个未文档化字段（是否含 RSE ID/接收时间戳）。
3. BsmP1 是否含多 RxDevice 的接收记录（决定接收侧时间来源）。
4. WSU 1609.2 时钟 ↔ RSE GMT 时钟同步性（全部 SPMD 时延主张的共同前置）。
5. Packet 轮换 IP 与 TxRandom/MsgCount 的跨表配对可行性。
6. AMCD time_sent 时钟来源与 time_received 单位。
7. NYC IE Sent/Heard 字段语义（官方字典附件当前缺失）。
8. 即使全部获得：**控制器采用与因果动作效应在任何候选数据源中均不可观察**——该环节永远属于仿真/实验，不能由数据下载解决。

## 8. 文献与项目维护

- Zotero `TJU → AAD`（56 条）关键词扫描（2026-10-16）：无 SPMD/CV Pilot 数据集论文（仅 1 条弱相关：ZTEPXKBA，连接车辆非局部交通流模型）。候选导入（待研究者决定，按现有规则走 Zotero，不建本地 PDF 库）：数据集 DOI（SPMD 10.21949/1504482、AMCD 10.21949/1504488、NYC IE 10.21949/1404205、NYC 消息样本 10.21949/1522485）与各项目评估报告。本任务未导入。
- 本任务不改变任何 Gate、统计或科研参数；Stage 0.4 状态仍为 `pending_official_packet_access`。

## 9. 边界合规声明

未下载任何数据内容（无 Range/断点/样本获取）；未提交任何申请（含 ITS DataHub 表单）；未访问 holdout；未修改论文正文、AGENTS.md、研究者未提交文件（含其本地删除中的 `doc/literature-notes/`）；未启动 Stage 0.5 正式实验、Protocol Lock 或 Stage I。
