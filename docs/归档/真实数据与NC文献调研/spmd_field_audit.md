# SPMD 字段与识别目标审计（进行中）

## 已核验来源

1. USDOT Safety Pilot Model Deployment 官方数据页及其元数据 API。
2. UMTRI/ROSA P 的 *Safety Pilot Model Deployment: WSU Basic Safety Messages* 代码本。
3. Deep Blue 中 *Safety Pilot Model Deployment - Rx Basic Safety Messages Codebook* 的公开检索索引。

## 数据资产状态

- 官方数据条目名称为 `Safety Pilot Model Deployment Data`，完整文件名为 `SPMD.zip`。
- 官方元数据列出两个附件：`Safety_Pilot_Model_Deployment_Sample_Metadata_Documentation.docx` 和 `Safety_Pilot_Model_Deployment_Sample_Data_Handbook.docx`，并提供各自 asset ID。
- 官方页面将数据标为 public，时间范围为 2012-10-01 至 2013-04-30，地理范围为 Ann Arbor, Michigan。
- 两个 DOCX 附件已经通过 USDOT 官方附件接口下载并通过 DOCX 解析。Deep Blue 新旧页面及 bitstream 仍返回 403/Cloudflare 挑战；ROSA P 的 WSU/Rx 代码本可通过官方页面做页级核验，但本地 PDF 直链仍受访问限制。

## 已确认字段

| 层级 | 数据/字段 | 当前证据 | 可支持的分析 |
|---|---|---|---|
| 发送消息 | `GenTime`：BSM 生成时间 | WSU 与 Rx 代码本索引均明确给出 | 构造生成时刻；需要确认不同表的时间基准和精度 |
| 发送设备 | `TxRandom`：随机化发送设备 ID | WSU 与 Rx 代码本索引均明确给出 | 在随机 ID 有效期内识别发送端；不能直接视为永久车辆 ID |
| 消息序号 | `MsgCount`：每条 BSM 递增的消息计数 | WSU 与 Rx 代码本索引均明确给出，范围从 0 开始循环 | 与 `TxRandom`、`GenTime` 组合后可能作为 Tx/Rx 配对键 |
| 车辆状态 | 纬度、经度、高程、速度、航向、纵/横/垂向加速度、yaw rate | WSU 代码本变量索引明确给出 | 描述发送时车辆运动状态、计算空间关系和风险代理 |
| 制动/事件 | J2735 brake status、BSM unusual event flag | WSU 代码本变量索引明确给出 | 构造制动或异常事件候选；需核验事件与 BSM 的时间关联 |
| 设备能力 | VAD 只能发送；ISD、ASD、RSD 可收发 | UMTRI 官方数据说明明确给出 | 定义有接收机会的设备子样本，避免把 VAD 缺失接收当丢包 |

## 仍未核验的关键字段

| 问题 | 必须找到的字段或证据 | 未核验前不能做的主张 |
|---|---|---|
| 接收端是谁 | 接收设备 ID、主机车辆 ID或能关联到接收车辆的稳定键 | 不能建立发送车—接收车配对 |
| 何时接收 | 接收时间戳及其时钟定义 | 不能计算端到端时延 |
| Tx/Rx 是否同一条消息 | `TxRandom + MsgCount + GenTime` 在两表中的实际重复率、循环冲突和脱敏变化 | 不能宣称已完成逐消息交付识别 |
| 是否有接收机会 | 两车位置、设备能力、工作状态、记录覆盖和潜在通信范围 | 未接收记录不能解释为丢包 |
| 是否被控制采用 | 警告触发、控制器状态、驾驶员提示、制动命令或可关联的应用日志 | 不能识别“采用”的因果效应 |
| 是否改变风险 | 接收/采用之后的目标动作与可比反事实 | 不能把相关的减速直接写成消息导致的风险变化 |

## 当前判断

SPMD 对“消息生成—接收可达性—可能的时延”分析具有明确潜力。当前已经取得接收端主车 ID、行程内时间、远车 ID 和远车状态流，但还没有完成逐消息发送—接收配对、接收时间定义和机会条件下丢包识别。因此本周任务“优先核验并接入 SPMD”仍保持未完成。

即使后续成功完成 Tx/Rx 配对，公开资料目前也没有证明存在控制器或驾驶员的逐消息采用字段。若最终没有采用记录，真实数据部分应将主张收缩为：验证通信可达性、时延分布和接收后行为响应代理；“采用后因果效应”仍由仿真或未来 HIL/封闭道路实验识别。

## 2026-08-12 选择性下载后的实证核验

### 远程主包目录

USDOT 主包是 ZIP64，精确大小为 117,346,016,961 B。通过官方服务器的字节范围请求读取中央目录后，确认其包含 46 个成员。与本研究最相关的成员包括：

| 成员 | 外层压缩后大小 | 内层文件大小 | 状态 |
|---|---:|---:|---|
| `BsmP1.csv.zip` | 55,723,172,322 B | 55,709,318,024 B | 发送侧高频 BSM 主表，尚未下载 |
| `Packet.csv.zip` | 15,332,614,985 B | 15,400,825,024 B | 包级索引/时间信息，尚未下载 |
| `RV_RX.csv.zip` | 783,882,525 B | 783,804,721 B | 主车记录的远车接收状态，已下载并通过 CRC |
| `RSE_BSM.csv.zip` | 3,229,630,428 B | 3,228,646,514 B | 路侧设备接收 BSM，尚未下载 |
| `PCAPFile.csv.zip` | 654,501 B | 654,994 B | PCAP 文件索引，已下载并通过 CRC |
| `BsmP1Summary.csv.zip` | 13,181,194 B | 13,177,267 B | BSM 行程摘要，已下载并通过 CRC |
| `DataWsuSummary.csv.zip` | 357,129 B | 357,100 B | WSU 主车状态摘要，已下载并通过 CRC |
| `TripFact.csv.zip` | 840,417 B | 840,157 B | 行程索引，已下载并通过 CRC |

### `RV_RX` 表的真实字段与规模

表头为：`DeviceID, Trip, Time, RV_ID, RV_Type, RV_Number, Brake_Status, Elevation, Heading, Latitude, Lateral_Accel, Longitude, Longitudinal_Accel, Range, Range_Rate, Speed, SteerWheelPosition, Yaw_Rate`。

- 2013 年 4 月文件：22,551,426 行，63 个主车 `DeviceID`，7,741 个主车行程，2,563 个 `RV_ID`。
- 2012 年 10 月文件：12,613,844 行，64 个主车 `DeviceID`，7,584 个主车行程，5,093 个 `RV_ID`。
- 合计 35,165,270 行。
- 所有数据行解析为 22 列，而表头只有 18 列；抽样记录的末 4 列为空。后续读取器必须显式处理这个格式异常，不能静默错位。

官方样本手册对同类 DAS 字段说明：`Device` 是 DAS/车辆 ID，`Trip` 是点火周期计数，`Time` 是 DAS 启动后的厘秒；远车 GPS 时间字段被描述为“从主车 WSU 所跟踪远车接收的 epoch GPS 时间”。这里必须区分：`RV_RX.Time` 是厘秒，`GpsTimeWsu` 与 `GenTime` 才以毫秒记录。当前 `RV_RX` 表头本身没有后两者、明确的消息生成/接收时刻、`MsgCount` 或控制采用字段。

全量处理器初版曾误把 `RV_RX.Time` 解释为毫秒。回到本地官方 DOCX 原文核验后，已将代码、CLI、测试和 JSON 全部改为厘秒，并按 100 厘秒（1 s）重新扫描。初版连续性数字已作废；修正后的合计为 2,690,019 个接收状态片段和 2,567,341 个大于 1 s 的观测断点，仍不得解释为消息数或丢包数。

### 修正后的识别边界

- **已得到支持：** SPMD 的确包含接收端主车 ID、行程内时间、远车 ID 和远车运动/相对距离状态，可用于构建接收可达性和远车状态流。
- **尚未证明：** `RV_RX` 单表不能完成逐消息 Tx-Rx 配对，不能独立计算网络时延或机会条件下的丢包率。
- **仍需下载：** 若要做逐消息识别，至少还需核验 `Packet.csv.zip`，并从 `BsmP1.csv.zip` 或可替代发送侧表中取得同一消息的发送记录。两者分别约 15.33 GB 和 55.72 GB。
- **仍不可观察：** 当前任何已核验 SPMD 表都没有控制器采用、控制命令或“消息导致动作改变”的直接字段。即使完成 Tx-Rx 配对，论文主张也只能到消息生成、传输/接收、时延和丢包，采用与因果动作效应仍需仿真、硬件在环或专门实验补足。
