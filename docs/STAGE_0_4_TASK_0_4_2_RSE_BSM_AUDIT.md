# Stage 0.4 任务 0.4.2：RSE_BSM 最小数据获取与独立证据核验

> 任务 AAD-0.4.2；执行日期 2026-10-16（**勘误 2026-10-17**：原稿误记 2026-10-16；真实执行日由 git commit d9ce638=2026-10-16 22:47 +0800、文件落盘 21:03 与封存包 created_utc=2026-10-16T14:43Z 证明）。结果 ID：`RES-STAGE-0.4-RSE-BSM-V1`；机器可读包：`code/outputs/formal/calibration/stage_0_4_rse_bsm_v1/`（含 audit/config/provenance/manifest/SHA256SUMS 与方法脚本）。
> Stage 0.4 Gate 保持 `pending_official_packet_access`；`RES-STAGE-0.4-COMM-OBS-V3` 未改动。原始数据仅存本地 `dataset/SPMD/selected/RSE_BSM.csv.zip`。

## 1. Phase A：下载前检查（全部通过）

**A1 官方来源**：条目 `deww-aa3r`（DOI 10.21949/1504482）官方文件 API 支持 Range（206 + `Accept-Ranges: bytes`，对象总大小 **117,346,016,961 B 与历史记录逐位一致**）。读取 ZIP64 中央目录（元数据传输共 135,996 B）：**46 个成员**；8 个关键成员的历史尺寸全部吻合（BsmP1/Packet 的"压缩/解压"两列在历史记录中互为倒置，本目录 `spmd_zip64_catalog.json` 为权威记录）；`SPMD/RSE_BSM.csv.zip` 存在：压缩 3,229,630,428 B、解压 3,228,646,514 B、CRC32 `41d7512f`、deflate、本地头偏移 101,092,209,068。全程无主包正文下载；单次探测若返回 200 即中止（未发生）。

**A2 磁盘**：D: 盘前 182.98 GiB → 后 179.98 GiB；峰值占用 ≈ 6.5 GiB（压缩临时 + 成员解压写盘）；远高于 ≥5 GiB 安全余量。未删除任何既有文件。

**A3 价值**：官方手册 §6.1 确认该成员为"接收的 BSM 内容记录"，含 TemporaryID/MsgCount 消息身份字段，且存在 24-vs-28 字段疑问与 4 个未文档化字段的假设——下载价值成立。

## 2. Phase B：下载与完整性（成功）

| 项 | 值 |
|---|---|
| 传输方式 | ZIP64 成员级 Range，64 MiB × 49 分块 |
| 实际传输量 | 3,229,631,452 B（成员压缩 3,229,630,428 + 本地头等元数据），另有预检元数据 135,996 B |
| 响应校验 | 每分块 206 + Content-Range 精确匹配 + ETag 绑定 blob id（含 `--gzip` 传输标注变体；首次探测到非预期编码变体时按 fail-closed 中止，修正后重启，无混合写入） |
| 落盘 | `dataset/SPMD/selected/RSE_BSM.csv.zip`（3,228,646,514 B） |
| CRC32（对中央目录） | `41d7512f` **一致** |
| 内层 ZIP testzip | 通过；成员：`RSE BSM head.csv`（373 B）+ `RSE BSM.csv`（压缩 3,228,645,982 / 解压 **16,841,646,195 B**） |
| SHA-256（成员文件） | `9C40C15FAD32C470592A08556B07DDB91C8A08265E1F56683908AD0EDD47D722` |
| 官方哈希 | 无官方 SHA-256 提供；完整性证明 = 中央目录 CRC32 + 内层 ZIP CRC + 解压大小三重一致 |
| 临时文件 | `.deflate` 中间体与进度文件在校验通过后删除（原子重命名前未冒用正式文件名） |

说明：成员 CRC 一致仅证明 **ZIP 成员完整性**，不构成官方 SHA-256 证明——官方未提供整文件哈希，如实记录。

## 3. Phase C：实际字段与科研证据核验

以下全部为流式读取（未解压 16.8 GB 成员到磁盘，无重复大文件副本）；按 C4 holdout 规则只做结构、身份、时间语义与格式完整性检查，**行为统计暂缓**（见 §3.6）。

### 3.1 实际 schema（C1）

- **25 字段** = 官方表格 24 字段 + **`RxDevice`（第 1 列）**。官方手册"28 字段"的说法与实际不符；此前假设的"4 个未文档化字段"实际是 **1 个**（RxDevice），无隐藏时间字段。
- 数据文件 `RSE BSM.csv` **无表头**（表头是独立的 `RSE BSM head.csv`）——读取器必须显式接表头，与 RV_RX 的"表内表头+末 4 列为空"异常不同，本文件 **124,115,615 行全部 25 列、0 畸形行**。

### 3.2 消息身份（C2）

- **BSMID**：124,115,615 个不同值 = 行数，**逐行唯一**（bitset 精确核验）；真实值域 1,008,581,868–3,054,637,934。它是**行记录 ID，不是跨接收方共享的消息身份**（0 个 BSMID 出现在多个 RxDevice 下）。
- **TemporaryId**：155,220 个不同值（轮换匿名发送 ID，月尺度与官方单日样本量级一致）。
- **MsgCount**：0–127 全周期循环（J2735 语义）；155,220 个发送者中 **133,799 个**出现重复 MsgCount 值——发送序号在月尺度必然回绕。
- **(TemporaryId, MsgCount, DSeconds) 三元组**：在覆盖 60,035,108 个不同三元组的精确检验下已见 **≥26,919,767 次重复**（内存上限截断，属下界）——即使三元组也无法在月尺度唯一识别消息。
- 结论：成员内不存在唯一、可靠的跨记录消息身份；任何配对主张必须加时间窗或位置内容辅助——而本成员没有绝对时间（§3.3），故 **配对能力 = Ambiguous**。

### 3.3 时间证据（C3）——核心否定结论

- **本成员没有任何绝对时间戳**：除发送端 `DSeconds`（0–59,999，分钟内毫秒、回绕）外无时间字段；无接收时间、无纪元、无时区、无同步说明。
- 因此 **RSE_BSM 单独不能提供消息传播时延、时序、接收事件时间的任何证据**；本任务未计算任何伪时延。
- 若需为这些接收记录定时间锚，官方字典显示 **BsmP1 的 RxDevice+Gentime 结构** 与本成员记录方命名空间一致（§3.4），是可能的补充路径；Packet 属 RSE/PCAP 侧，命名空间不同（§4）。

### 3.4 接收方身份（新发现，超出任务预期）

- `RxDevice` 2,008 个不同值：**全部**（2,008/2,008）包含于 BsmP1Summary 的 2,204 个设备 ID；与 DataWsuSummary 设备 ID 重叠 91/96、TripFact 23/64；与 **PCAPFile 的 25 个 RSE LocID 命名空间零重叠**。
- 行数分布重尾：`10106` 一个设备占 38,882,054 行（31%）；前 10 设备占 45%。
- **解释（证据等级：Ambiguous）**：RxDevice 属**车载设备 ID 命名空间**（WSU/BsmP1Summary 一致），与成员名 "RSE_BSM" 和官方手册 RSE Dataset §6.1 "RSE 通信范围内接收" 的描述**不符**。物理上这 2,008 个记录方究竟是车载 WSU（即 V2V 接收日志）还是共享编号的路侧设备，须以设备清单（BsmMd/UMTRI 文档）或跨表核验裁定；**不得按成员名断言**。
- 科研含义：若为车载接收日志，该成员是**车辆侧接收消息流**（对 AAD 的目标车辆更相关），但仍缺时间锚。

### 3.5 关联性

- 与 `PCAPFile`：接收方命名空间零重叠，无文档化连接键 → 当前 **不可关联**。
- 与 `TripFact`/`BsmP1Summary`/`DataWsuSummary`：仅设备 ID 命名空间重叠（覆盖/身份背景），无逐行关联键。
- 与 `BsmP1`/`BsmMd`：字典层面 RxDevice/Gentime/TxRandom 结构提示潜在关联，**需实际数据验证（Potential）**。

### 3.6 数据划分与 holdout（C4）

- 现行 calibration/holdout 划分基于 `DeviceID|Trip` 哈希（RV_RX）；RSE_BSM 无 DeviceID-Trip 列，**规则不可直接适用**。
- 本任务未发明新划分规则、未把全部数据当 calibration、未做行为结果或全量分布统计；已执行者为结构/身份/格式核验。
- **后续隔离策略提交研究者决定**：例如按 RxDevice 子集映射、按发送者映射、或整表按"仅结构证据"处理。在此之前 RSE_BSM 不进入任何正式统计。

### 3.7 证据等级汇总

| 需求 | 等级 | 依据 |
|---|---|---|
| 消息来源 | Documented（月尺度追踪 Ambiguous） | TemporaryId/MsgCount 实测 |
| 消息发送 | Not Observable | 无绝对时间 |
| 消息接收 | Documented-结构（接收时间 Not Observable） | 接收记录行存在、记录方可识别 |
| 发送—接收配对 | Ambiguous | 最佳键三元组重复 ≥26.9M；无跨接收方共享身份 |
| 通信时延 | Not Observable | 无接收时间戳、无同步证据 |
| 丢包/投递 | Not Observable | 无发送基数、无时间窗、无机会模型 |
| 环境条件 | Potential | J2735 运动内容；无信道/RSSI/功率 |
| 采用与响应 | Not Observable | 无字段（且永久不可由本表观察） |

## 4. Packet 下载决策分析（任务 §六）

**判断：建议继续下载 Packet（15.33 GB），但其作用与 0.4.1 调查时的预期不同，须按修正后的预期决策。**

- **修正预期**：0.4.1 曾预期 Packet 可为 RSE_BSM 提供时间锚。实测显示 RSE_BSM 的记录方属车载命名空间、与 Packet/PCAPFile 的 RSE LocID 命名空间零重叠，且二者无文档化连接键——**Packet 大概率不能直接为 RSE_BSM 行定时间**（除非位置序匹配可验证，需下载后核验）。
- **Packet 独立价值（仍然成立）**：它是 25 个 RSE 会话侧的包级证据——绝对 GMT 捕获时间（秒+微秒）、PSID 类型、信道/数据速率/功率、包长——直接支撑 Gate 预留项 `packet_schema_evaluated`，并提供真实包级捕获与无线条件统计；这是 RSE_BSM 完全没有的维度。
- **BsmP1（55.72 GB）价值上调**：官方字典的 RxDevice+Gentime 与本成员记录方命名空间一致；若 BsmP1 确实按接收设备记录带 Gentime 的 BSM，它将同时提供**接收侧绝对时间**与发送/接收结构，可能是比 Packet 更关键的时间锚来源；其接收语义仍是下载后首验项。体量大（180 GB 余量下可行），建议列为 Packet 之后的下一批决策。
- **新识别成员**：`BsmMd.csv.zip`（压缩 17.29 GB，BSM 元数据：TxRandom↔真实设备映射、证书 ID、时间/帧偏移）——潜在的身份链接钥匙；`RSE_locations.kml`（520 B，RSE 坐标）——**建议随任意下一批顺带获取**（近零成本）。
- **经济替代方案**：AMCD（P1，同行收发时间，云接收）可低成本先行验证时延方法论；NYC/Tampa 样本小且免费。但它们是不同项目/技术环境，不能替代 SPMD 内部的关联链。

## 5. 剩余未验证事项

1. 2,008 个 RxDevice 的物理身份（车载 WSU vs 路侧）——需 BsmMd/设备清单。
2. RSE_BSM ↔ BsmP1 的逐行关联可行性（RxDevice+Gentime 假设）。
3. Packet ↔ RSE_BSM 是否存在位置序/计数匹配（下载 Packet 后核验）。
4. Gentime（1609.2，含 35 s 文档偏移）与任何接收侧时钟的同步性——全部时延主张的永久前置。
5. holdout 隔离策略（提交研究者）。
6. 控制器采用——任何候选数据均无此字段，永久属仿真/实验。

## 6. 交付物索引

- 本报告：`docs/STAGE_0_4_TASK_0_4_2_RSE_BSM_AUDIT.md`；机器可读包：`code/outputs/formal/calibration/stage_0_4_rse_bsm_v1/`（audit/config/provenance/manifest/SHA256SUMS + 方法脚本 + ZIP64 目录快照）；便携证据：`evidence/results/RES-STAGE-0.4-RSE-BSM-V1/`。
- 原始成员（仅本地）：`dataset/SPMD/selected/RSE_BSM.csv.zip`。
- 更新：下载清单、数据源候选 JSON、注册表、索引与 AI_CONTEXT。
