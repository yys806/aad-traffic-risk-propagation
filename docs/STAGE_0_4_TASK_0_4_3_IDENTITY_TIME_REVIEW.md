# Stage 0.4 任务 0.4.3：SPMD 设备身份、时间语义与下一批数据必要性核查

> 任务 AAD-0.4.3（只读核查，2026-10-17 执行；勘误见 §6）。零新数据下载；Stage 0.4 Gate 保持 `pending_official_packet_access`；V3 与 RSE_BSM V1 封存结果未改动。
> 本次新增官方文档证据（本地保存 + SHA-256 见 `dataset/SPMD/mcity_documentation/README.md`）：
> ① 官方 **WSU BSM Codebook**（ROSA P DOT 66785，2022-01，PDF 1,024,016 B）；
> ② **UMTRI/mCity Connected Vehicle Dataset 官方文档镜像**（BSM/Rx-BSM/RSE/Events/SPaT/MAP 六份 markdown，GitHub caocscar/ConnectedVehicleDocs）。
> 标注约定：**Fact**＝实测或官方文档明确；**Inference**＝由多项证据强推；**Hypothesis**＝未证解释；**Proposal**＝建议。

## 1. RxDevice 物理身份（任务 A）

### 已确认（Fact）

1. **官方语义**（mcity 官方文档，Rx-BSM 数据集）：`RxDevice = "receiving Device Id; equivalent to VehicleID"`——接收设备 ID，**等同于车辆 ID**。同一文档体系的事件表注明 "For VADs this is the same as TxDevice"（VAD 无接收能力，自记录时 Rx=Tx）。
2. **命名空间**（AAD-0.4.2 实测，本次复核）：RSE_BSM 的 2,008 个 `RxDevice` **全部**包含于 BsmP1Summary 的 2,204 个设备 ID；与 DataWsuSummary 91/96、TripFact 23/64 重叠；与 PCAPFile 的 25 个 RSE LocID **零重叠**。
3. **官方样例互证**：SPMD 样本手册 DAS1 Summary 表（Table 18）的 DeviceID 样例值含 `17101`，min/max = `10106`/`17103`——正是 RSE_BSM 行数前三的记录设备；手册明确 DeviceID "doubles as a vehicle's ID"。
4. **记录方=接收方角色**（本次实测，全量 124,115,615 行）：前 10 记录设备全部呈多发送方交织结构（连续同 TemporaryId 的平均游程 1.0–1.35，设备 10106 见到 102,719 个不同发送方 ID）——是**接收日志**而非发送自记（发送自记应为长游程）。
5. **设备 10106 为已登记车辆**：BsmP1Summary 4 月记录其 488 次 BSM 行程、52.0 小时、2,138 km。若成员覆盖约 7 个月，其 38.9M 接收行折合驾驶时约 30 BSM/s——密集装备交通下 V2V 接收的合理量级（若仅覆盖 4 月则需 207 BSM/s，不合理——成员时间跨度待定，见 §2.6）。
6. **结构异常（Fact，含义 Unverified）**：每个 TemporaryId 至多被 **2** 个设备记录（52,751 个单记录、102,469 个双记录、0 个 ≥3）；**全部** 102,469 个双记录对都包含 10106。

### 结论与缺口

- **结论（Inference，多源证据）**：`RSE_BSM.RxDevice` 是**车载设备（车辆）ID**，该成员是**车辆侧接收 BSM 日志**；成员名 "RSE_BSM" 与手册将其放在 RSE Dataset 章节均与实际内容不符（手册 RSE BSM 表本身也漏列了实际首列 RxDevice）。**不得仅凭命名断言其为路侧数据。**
- **缺口（Unverified→Hypothesis）**：①"每个发送方 ID 至多 2 个记录方、且双记录对全部含 10106"与"2,008 辆车全量接收日志"不符——最可能是**样本/策划式导出**（SPMD.zip 本身是 Sample Data 环境）或特殊采集架构（10106 为高吞吐采集点 + 每发送方配一个次要记录方）；采样设计无文档，**任何后续接收率/丢包统计必须先弄清该设计，否则有选择偏差**。②成员时间跨度（7 个月 vs 1 个月）无法从表内确定（无绝对时间）。③设备物理清单与双设备对映关系需 **BsmMd**（文档明确含未脱敏发送天线 ID + 接收天线 ID）或部署设备清单裁定。

## 2. 时间字段与关联可行性（任务 B）

### Gentime 语义（已由官方文档解决）

- **Fact**：官方 WSU BSM Codebook（DOT 66785）：`GenTime = "Time of Basic Safety Message Generation"`（BSM **生成**时间）。mcity 文档（BSM/Rx/RSE 三套数据集一致）：`Gentime = number of microseconds since Jan 1, 2004 (UTC+00:00)`，单位**微秒**；且 "Tx columns should be identical to the same message in the BSM dataset"——Gentime 随消息走（**发送端 1609.2 时钟**），在接收日志中同样是该消息的生成时间。
- **Fact（官方文档间冲突，待实测裁决）**：样本手册 §5.1 要求 `秒 = Gentime/1e6 − 35`（1609.2 与 UTC 的 35 秒文档性偏移）；mcity 文档直接称 UTC 微秒、无 35 秒。两者必有一误；可用 TripFact/BsmP1Summary 的行程 Epoch 起止时间做经验校准（Proposal，不需新数据）。
- **Fact（新发现的手册勘误）**：样本手册 §5.4 称 BsmP1 `DSecond = 点火后十分之一秒`，但其自带样例每 0.1 s（Gentime 增量 ~100,000 µs）DSecond 增 100——即 **100 ms/行**。算术证明 `DSecond = 分钟内毫秒`（secMark 语义，与 mcity 文档一致、与 RSE_BSM 的 DSeconds 0–59,999 相符）；手册的 "deciseconds since ignition" 描述是**错误**的。任务 §二.B 要求"不使用缺乏证据的时间换算"——本条给出的是有样例算术与双文档支持的更正。

### 四类时间的可观测性（核心结论）

| 时间类别 | 字段 | 状态 |
|---|---|---|
| 消息生成时间 | BsmP1.`Gentime`（随消息进入所有 Rx 日志） | **Documented**（发送端 1609.2 时钟；±35 s 文档冲突待经验校准） |
| 实际发送（射频）时间 | 无任何表记录 | **Not Observable** |
| RSE 捕获时间 | Packet.`PacketTimestamp`(GMT �)+`TimestampMicroseconds` | **Documented**（未下载验证） |
| 车辆接收时间 | RSE_BSM/BsmP1 无接收时间戳；RV_RX.Time 为 DAS 本地厘秒（非消息接收时间） | **Not Observable（全 SPMD 家族车辆侧）** |

**推论（对 AAD 的关键边界）**：即使获得全部 SPMD 表，**车对车端到端时延在原始日志中不可计算**（无接收时刻）。家族内唯一可计算的时延类量是"**生成 → RSE 捕获**"（Packet 捕获时刻 − 该 BSM 的 Gentime），前提是 Packet 行能匹配到具体 BSM（无文档化键，见 §3）且 1609.2↔GMT 时钟同步可证。跨 WSU 时钟同步质量（GPS 纪律钟）**Unverified**；如 mcity 元数据的 deltaTmax 提示理想 0.100 s，说明处理链按发送时间对齐而非接收时间。

### 跨表关联键（Fact/Unverified 分列）

- **Fact**：`TxDevice = 临时 ID 的静态 2 字节`、`TxRandom = 随机 2 字节`（mcity）；RSE_BSM 的 `TemporaryId` = 4 字节临时 ID——**结构上可与 BsmP1 的 (TxDevice,TxRandom) 对应**（字节序/拼包方式需实测验证）。mcity 主键：BSM = (RxDevice, FileId, TxDevice, Gentime)。
- **Fact**：RSE_BSM 无 FileId/Gentime，成员内最佳键 = (TemporaryId, MsgCount, DSeconds)，月尺度不唯一（0.4.2 实测重复 ≥26.9M）；若与 BsmP1（Gentime）连接成功，可借发送方自记日志恢复每条接收行的生成时间——**但仍无接收时间**。
- **Unverified**：RV_RX.`RV_ID` 与 BSM 临时 ID 的关系；Packet ↔ 具体 BSM 的匹配（仅 PSID/计数/顺序可能，无文档）；RSE_BSM↔BsmP1 连接的实际重复率。
- **BsmMd（Documented，未验证值）**：含未脱敏发送天线 ID、**接收天线 ID**、CertId、Gentime 及 GenTimeRelOffset 等偏移字段（手册中这些偏移字段为"待填"占位，实际值未知）——是身份与时间偏移的双重钥匙。

## 3. Calibration / Holdout 隔离方案（任务 C，候选与风险，不冻结）

现有规则：`DeviceID|Trip` 哈希（RV_RX）。RSE_BSM 无 DeviceID-Trip 列，规则不可直接适用。候选：

1. **结构审计专用（当前，保守，Proposal：维持）**：RSE_BSM 只用于 schema/身份/完整性核验，不做行为统计。零泄漏风险；代价是暂无通信描述性统计。
2. **接收设备级哈希（候选 2）**：RxDevice 已证实为车辆设备 ID → 按现有哈希函数对 `RxDevice` 单键划分。风险：粒度从"设备-行程"变为"设备"，与 RV_RX 分区不一致——同一车辆在 RV_RX 中跨两个分区、在 RSE_BSM 中被整设备划入一侧，若未来联合分析存在跨表泄漏面；且发送方车辆不受此划分约束（发送方身份未知时无法归属）。
3. **发送方映射划分（候选 3，需 BsmMd）**：经 BsmMd 的未脱敏发送天线 ID 把 RSE_BSM 行归属到发送车辆，再套现有设备哈希。最一致，但依赖 BsmMd 下载与轮换 ID 映射的实际可行性。
4. **时间窗划分：不可行**（RSE_BSM 无绝对时间）。

**待研究者决定**；在此之前维持方案 1（行为统计继续暂缓）。另注意：mCity/UMTRI Flux 过滤数据集（§5）自带"去标识化"（行程首尾各截 <8%），与我们基于原始表的分区是两个数据宇宙，不可混用。

## 4. 下一批数据必要性评估（任务 D）

| 数据 | 体量 | 能解决什么 | 需要的字段 | 证据状态 | 即使下载仍解决不了 | 优先级（Proposal） |
|---|---:|---|---|---|---|---|
| **BsmMd** | 17.29 GB 压缩 | 身份映射（TxRandom↔未脱敏设备、**接收天线 ID**）；Gentime/偏移语义（GenTimeRelOffset 实际值）；候选 3 划分的前提；§1 三缺口 | 未脱敏 Tx/Rx 天线 ID、CertId、偏移列 | Documented（字典），值未验 | 消息内容/位置；接收时间；RSE_BSM 采样设计（部分） | **1** |
| **BsmP1** | 55.72 GB 压缩（内层 CSV 估算 ~300 GB，须流式） | 每条 BSM 的生成时间与发送基数；RSE_BSM 行的时间锚（经身份连接）；跨 WSU Gentime 一致性/时钟同步经验检查；发送侧车辆状态 | Gentime、TxDevice/TxRandom、MsgCount、位置/运动 | Documented；连接键 Unverified | **接收时间（不存在）→ V2V 时延不可算**；RSE_BSM 采样设计 | **2**（在 BsmMd 或与 BsmMd 同批后） |
| **mCity Rx-BSM 过滤数据集（新渠道）** | ~9 GB（未压缩，Globus） | 136 辆 Rx 车辆、68.5M 条接收 BSM + 交互元数据（firstTime/lastTime 日期时间）；已文档化的 RxDevice/Gentime schema；比 BsmP1 便宜得多的接收侧证据 | 官方 schema（已获得） | Documented | 原始未过滤数据；V2V 接收时刻（仍无）；受过滤/去标识化限制 | **备选 1'**：需 Globus 机构通道（研究者动作）；若通，可能先于 BsmP1 回答"接收+生成时间配对"问题 |
| **Packet** | 15.33 GB 压缩 | RSE 侧唯一绝对时间（GMT+µs）与无线条件（信道/速率/功率）；`packet_schema_evaluated` 证据；生成→捕获时延（若可配对） | PacketTimestamp、PSID、信道/功率、PCAPFileId | Documented | 与车辆侧行的连接（无文档键）；发送方身份（IP 轮换） | **3**（在 1/2 之后；不为凑 Gate 项提前） |
| **AMCD** | ~2.6M 行（小） | 低成本核验同行 sent/received 时间语义与收发配对方法论（云接收） | time_sent/time_received | Documented | SPMD 内部身份链；V2V 语义 | 随时可做的低成本旁证（P1） |
| **RSE_locations.kml** | 520 B | 25 个 RSE LocID 坐标 | — | — | — | 随任意下一批顺带（近零成本） |

**磁盘与处理成本**：BsmMd 17.3 GB + 解压流式处理（<40 GB 峰值）；BsmP1 55.7 GB 落盘 + 流式（每全量遍 ~3–5 小时，Python 单线程；禁全量解压，内层 CSV 估算 ~300 GB 超出当前可用空间约一半，必须流式）；Packet 15.3 GB；均满足 ≥5 GiB 余量（当前 ~180 GiB）。

**禁止事项对照**：不下载 kml（本任务零下载，含 520 B）；未提交任何 Globus/申请。

## 5. 最终回答（完成要求）

**现有证据是否足以支持再下载大型 SPMD 数据？**
- 对 **BsmMd（17.29 GB）**：**是**——身份与时间语义两大核心缺口（RxDevice 双设备结构、Gentime 35 s、发送方映射、holdout 候选 3）都有文档化的解决字段，且 0.4.2/0.4.3 的身份疑点都指向它。
- 对 **BsmP1（55.72 GB）**：**尚不充分**——只有在 BsmMd（或先行的低成本校准）确认身份连接可行、且研究者接受"即使全下也得不到车辆侧接收时间（V2V 时延不可算）"这一硬边界后，为生成时间锚与发送基数而下载才合理。建议在 BsmMd 核验后再决策。
- 对 **Packet（15.33 GB）**：独立价值真实（RSE 侧绝对时间+无线条件）但与 AAD 当前最需要的车辆侧身份/时间链**正交**；**不建议**仅为了 `packet_schema_evaluated` Gate 项而提前下载。
- **更省空间的替代**：**mCity Rx-BSM 过滤数据集（~9 GB，Globus 通道）**可能以 1/6 的体量先行回答"带生成时间的接收 BSM + 配对结构"，但有过滤/去标识化限制且需机构通道——列为需要研究者批准的备选。

**最少还需要核查什么（若暂不下载）**：① Gentime↔UTC 35 秒冲突的经验校准（用已持有的 TripFact/BsmP1Summary epoch 与 BsmP1 样例即可做部分校准——但完整校准需 BsmP1）；② BsmMd 字典字段实际值（必须下载）；③ RSE_BSM 采样设计（官方文档无，可能需向 ITS JPO/UMTRI 咨询或经 BsmMd 间接推断）。

**最推荐的下一步（Proposal）**：批准下载 **BsmMd**（17.29 GB，P0）＋顺带 **RSE_locations.kml**（520 B）；并行研究者决定是否开通 **Globus** 通道评估 mCity Rx-BSM 过滤数据集（~9 GB）。BsmP1 与 Packet 等 BsmMd 核验后再议。

## 6. 已有报告日期一致性勘误（任务 E）

- **事实**：AAD-0.4.1 与 AAD-0.4.2 均实际执行于 **2026-10-16（北京时间）**：commit `80f92fb` 2026-10-16 20:01 +0800（0.4.1）、`d9ce638` 2026-10-16 22:47 +0800（0.4.2）、RSE_BSM 落盘 21:03、封存包 `created_utc=2026-10-16T14:43:19Z`（=22:43 +0800，正确）。
- **错误**：0.4.1 文档标注"2026-10-17"、0.4.2 文档标注"2026-10-18"（相差 1–2 天）；commit message 中的日期同样错误（不可改写，如实记录）。封存包内容正确、未触碰。
- **处置**：本任务对存活文档做**非覆盖式勘误**（在原日期处更正并注明"勘误 2026-10-17"），不修改任何封存包。

## 7. 证据与来源索引

- 官方 WSU BSM Codebook（ROSA P DOT 66785，2022-01）：`dataset/SPMD/Safety_Pilot_Model_Deployment_WSU_BSM_Codebook_ROSA_P_dot66785.pdf`（SHA-256 898A1A7B…BFB3）——GenTime="Time of BSM Generation"、BsmP1 变量表。
- mCity/UMTRI Connected Vehicle Dataset 文档（GitHub 官方镜像，2026-10-17 保存）：`dataset/SPMD/mcity_documentation/`——RxDevice≡VehicleID、Gentime=µs since 2004-01-01、TxDevice/TxRandom=临时 ID 静态/随机 2 字节、DSecond=分钟内毫秒、96% 行程 Rx==Tx、Rx 数据集 136 车辆/68.5M 行、RSE 数据集 29 RSE/3.5B 行、过滤规则与主键。
- SPMD 样本手册（本地，SHA 钉扎）：§5.1/§5.4/§6.1/§6.6——原始字典与两处被实测/算术更正的描述（28 字段说、DSecond 说）。
- 实测（本地 RSE_BSM 流式，方法脚本封存于 `stage_0_4_rse_bsm_v1/`）：≤2 记录方结构、10106 配对全覆盖、多发送方交织、行程/接收量级一致性。
- 封存包：`RES-STAGE-0.4-COMM-OBS-V3`、`RES-STAGE-0.4-RSE-BSM-V1`（均未改动）。
