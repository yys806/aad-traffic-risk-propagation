# Stage 0.4 任务 0.4.4：真实车联网通信关键证据专项调查

> 任务 AAD-0.4.4（下载前专项调查，2026-10-17）。**零数据下载**；未访问 locked holdout；未提交任何访问申请；Stage 0.4 Gate（`pending_official_packet_access`）、科研参数与全部封存证据未改动。
> 证据等级约定：Verified＝本地实测+可复核；Documented＝官方文档/字典明确；Potential＝结构/字段支持但须下载后实证；Not Observable＝该族数据结构上不存在；Ambiguous＝存在矛盾或未证解释。
> 链路分类：V2V＝车对车；V2I＝车对路侧；云端＝消息经应用服务器；受控试验＝封闭/半封闭环境，非自然交通。

## 1. 调查执行摘要

在 AAD-0.4.3 确立的 SPMD 硬边界之上（车辆侧接收时间在 SPMD 全家族不存在 → V2V 端到端时延不可算），本任务跨 DSRC/ITS-G5、C-V2X、V2I 测量与 CV Pilot 行为评估四个方向共完成 **9 个候选**的字段级核查（官方文档、数据字典、readme、论文与公开代码库，多轮检索+交叉验证）。核心结论：

1. **消息接收时间 + 通信时延（生成→接收）**：找到 **2 个具备"同一消息可靠配对 + 收发双侧时间戳"完整证据链**的候选——**Bristol ITS-G5 FLOURISH 数据集**（ITS-G5/802.11p，Tx/Rx CAM 均记录同一设备日志中的 `Timestamp`+`SeqNum`+`StationID`，接收侧附 RSSI 与接收方位置）与 **SEE-V2X**（C-V2X 侧链，跨层，应用/MAC/SCI，自带时延统计）。两者均为受控试验数据，**不能与自然交通的 V2V 语义混用**，但作为 Stage I 通信损伤模型的延迟/投递率分布基准是合格的。
2. **消息丢失率**：**UCI DSRC** 数据集提供现成"发送方/接收方 ID + PER"样本（适合投递率模型训练/验证）；**Bristol** 通过 SeqNum 间隙法计算 PDR/PER（Documented 于论文）；**SEE-V2X** 报告 PDR。三者均给出明确的**发送基数、接收结果与发送器状态**（接收机会由"发送器已知在线/发送"界定）——满足"不能将接收间断直接解释为丢包"的纪律要求；但**机会条件的真实世界版本**（对方是否在通信范围内）在受控试验中由实验设计保证，与自然场景不同。
3. **消息采用**：**THEA（Tampa）CV Pilot Phase 3 评估**提供了**真实驾驶员对 FCW 告警的响应率**（85% 在 3 秒内减速；接口启用使响应概率提高 9.93%；人工复核样本 6 个事件 2 响应）——这是**行为响应（驾驶员）层面的采用证据**，Documented 于官方评估报告（ROSA P DOT 55818 等）；但**控制器（自动驾驶）层面的采用日志在所有公开实测数据集中仍 Not Observable**（模拟器/封闭试验数据存在，不属于自然实车）。NYC IE EVENT 的"Sent/Heard"仍**不得**解释为采用（告警≠采用，AAD-0.4.1 已确立）。

## 2. 四项证据逐项覆盖矩阵

| 证据项 | 结论 | 最佳候选（按可信度） |
|---|---|---|
| **1. 消息接收时间** | ✅ 已获得可靠候选 | Bristol ITS-G5（RxCAM 记录含接收方日志 Timestamp——注意：记录的是**捕获/处理时刻**而非芯片 RF 时刻，需按文档口径声明）；SEE-V2X（端到端时延实测）；AMCD（云端接收时间，链路语义不同） |
| **2. 通信时延（同一消息）** | ✅ 已获得可靠候选（受控试验条件） | Bristol（同一设备日志内 Tx/Rx 时间戳 + SeqNum 配对 → 生成→接收延迟）；SEE-V2X（直接给端到端时延统计）；AMCD（同消息同行收发时间，云链路） |
| **3. 消息丢失率** | ✅ 已获得可靠候选（受控试验条件） | UCI DSRC（PER 样本）；Bristol（SeqNum 间隙法 PDR/PER）；SEE-V2X（PDR）；SPMD Packet+BsmP1（自然交通、RSE 侧——身份匹配 Unverified，暂缓） |
| **4. 消息采用** | ⚠️ 仅驾驶员行为层面有真实数据；控制器层面 Not Observable | THEA/Tampa Phase 3 评估（驾驶员响应率，真实交通）；NYC IE EVENT（仅告警，≠采用）；控制器采用 → 无公开实车数据，属仿真/封闭试验职责 |

**适用场景声明（不得混用）**：Bristol/SEE-V2X/UCI 的时延与投递率是**受控试验/单一技术条件**下的分布，可用于 Stage I SUMO 通信损伤模块的参数先验与合理性检查；**不能**当作 SPMD 自然交通场景（Ann Arbor V2V）的现实校准值。AMCD 为云端链路。THEA 为驾驶员响应。四者场景互异，AAD 建模时必须分模块引用并注明场景。

## 3. 候选数据源比较表

| # | 数据集 | 技术/链路 | 接收时间 | 时延（同消息） | 丢失率 | 采用 | 公开/获取 | 体量 | 磁盘峰值 | 校准价值 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Bristol ITS-G5 FLOURISH**（U. Bristol，DOI 10.5523/bris.eupowp7h3jl525yxhm3521f57；论文 arXiv:1903.10289） | ITS-G5/802.11p；2 OBU 车 + 4 RSU；V2V+V2I 混合，CAM 10 Hz，双频段（许可 DSRC + ISM） | Documented（RX-REQ-CAM 行含 `Timestamp`、接收方 MAC、RSSI、接收方 GPS；记录方为捕获/处理时刻） | **Documented**：同一设备日志记录全部 Tx 与 Rx CAM，字段含 `Timestamp`、`SeqNum`、`StationID`——同消息配对 + 双侧时间戳齐全（Tx 日志为生成/发出，Rx 为接收/记录）；时钟为各设备本地（跨设备同步质量 Unverified→时延绝对值待校） | **Documented**：SeqNum 间隙法 PDR/PER（论文方法）；发送基数=Tx 日志 | Not Observable | **公开**：University of Bristol data.bris（NC 许可），完整 34.3 GiB zip；含 `importedData`（MAT，预处理小体积） | 34.3 GiB（完整）/ importedData 子集（估计数 GiB，未实测） | ~70 GiB（完整）；子集 ~15–20 GiB | ★★★★（时延/PDR 分布、RSSI-距离、双频段对比；受控条件） |
| 2 | **SEE-V2X**（UCR，SenSys'25，DOI 10.1145/3715014.3722077） | C-V2X 侧链 PC5（LTE Rel.14 Mode 4）；商用 COTS 电台；参数扫描+真实场景 | Documented（跨层含应用层时戳） | **Documented**：论文直接报告端到端时延实测（含分布）；应用层 trace 可自算 | **Documented**：PDR 报告 | Not Observable | 公开（GitHub UCR-CISL/SEE-V2X，"Get Access"表单） | 未知（须表单） | 估计 <20 GiB | ★★★★（C-V2X 时延/PDR；与 DSRC 数据互补） |
| 3 | **UCI DSRC Vehicle Communications**（UCI #415，DOI 10.24432/c5r615） | DSRC/802.11p 模拟+实测混合；20–100 OBU；含干扰机场景 | Not Observable（无逐消息接收时间） | Not Observable（无同消息双侧时间） | **Verified（字段级 Documented）**：文件含发送方/接收方 ID、PER、RSSI、SNR——现成 PER 样本 | Not Observable | **公开**：archive.ics.uci.edu | 下载 32.8 MB | <1 GiB | ★★★（投递率/干扰敏感性；无时间维度） |
| 4 | **AMCD BSM**（data.transportation.gov eezi-v4pm，DOI 10.21949/1504488） | DSRC BSM；OBU→**VCC 云服务器**（非车对车） | Documented：`time_received`（云侧） | Documented：同行 `time_sent`/`time_received`（**发送侧时钟来源 Unverified**）；链路=云，**不可与 V2V 时延混用** | Potential：逐 OBU/test 发送-接收集合可构造 | Not Observable | 公开 Socrata 表（2,593,113 行） | 估计数百 MB（CSV） | <2 GiB | ★★★（收发配对方法论验证；云链路语义） |
| 5 | **THEA/Tampa CV Pilot Phase 3 评估**（ROSA P DOT 55818；TRID 2072171） | DSRC V2V FCW/EEBL 应用；>1,000 车自然交通 | 告警级（非逐消息接收） | Not Observable（告警时刻非消息接收时刻） | Not Observable | **Documented（驾驶员响应）**：85% FCW 后 3 s 内减速；接口启用响应概率 +9.93%；人工样本 6 事件 2 响应 | 公开（报告 PDF；底层 EVENT+BSM 数据在 ITS DataHub Sandbox 表单） | 报告 MB 级；数据体量大 | — | ★★★（采用-行为现实基准；驾驶员≠控制器） |
| 6 | **NYC CV Pilot IE EVENT**（gu5j-r7xj） | DSRC V2V/V2I 应用告警；自然交通 | Not Observable（分箱时间） | Not Observable | Potential（Sent/Heard，语义待字典） | **⚠️ 仅告警触发，≠采用**（AAD-0.4.1 边界） | 公开 Socrata（164,131 行） | 小 | — | ★★（事件/环境参考） |
| 7 | **mCity Rx-BSM 过滤数据集**（UMTRI Flux/Globus；文档 GitHub caocscar/ConnectedVehicleDocs） | DSRC V2V 接收；136 Rx 车辆；2012–2015 | Documented-字段（Rx 日志，但时间字段为发送端 Gentime——**接收时刻同 SPMD，不存在**） | Not Observable（同 SPMD 家族边界） | Potential（bsmCount 交互计数） | Not Observable | **需 Globus 机构通道**（研究者动作） | ~9 GB（未压缩） | ~20 GiB | ★★（接收结构参考；受过滤限制） |
| 8 | **SPMD Packet + BsmP1**（deww-aa3r） | DSRC；自然交通 V2V+RSE | RSE 捕获时间 Documented（Packet）；车辆接收 Not Observable | 生成→RSE 捕获 Potential（身份匹配 Unverified） | Potential（发送基数+BsmP1 身份链，须先 BsmMd） | Not Observable | 已批准成员级通道 | 15.3 + 55.7 GB | ~100+ GiB（流式） | ★★★（自然交通唯一；前置 BsmMd） |
| 9 | **Bristol BME M0 V2X**（GitHub BMEAutomatedDrive/v2xdatasets） | ITS-G5 PKI on/off；4 车高速实测 | Documented（pcap 级） | Potential（pcap 解析） | Potential | Not Observable | 公开 GitHub | 小 | <5 GiB | ★★（补充） |

## 4. 缺失与待验证清单（诚实缺口）

- **接收时间字段口径**：Bristol 的 Rx `Timestamp` 是**设备记录时刻**（含处理延迟），论文未给 RF 到达时刻与记录时刻的差值分解——若 AAD 需要"纯传播延迟"，需下载后用 Tx/Rx 同一设备日志内同消息的成对记录实测该口径差异（最小验证批次见 §6）。
- **跨设备时钟同步**：Bristol 各 OBU/RSU 独立时钟（readme 与日志格式）；同设备日志内 Tx/Rx 时间戳同钟可直接求差（同一台设备既发又收），跨设备时延需 GPS 对齐（论文方法）。时钟漂移对绝对时延的影响需实证（Unverified）。
- **自然交通 V2V 时延**：所有候选均为受控试验或 RSE 侧；**自然交通下车对车的接收时刻在任何已调查公开数据集中均不存在**（SPMD 家族+mCity 家族同边界）。Stage I 若需"自然场景 V2V 端到端时延"，只能靠仿真假设声明。
- **控制器采用**：无任何公开自然实车数据集含"控制器采用某 V2X 消息并记录决策"的字段；THEA 为驾驶员层面。自动驾驶控制器采用证据仅存在于模拟器/封闭试验（如 CDA 合并试验 FHWA-HRT-25-051 为 L3 自动化+连接消息，属受控环境）。
- **SEE-V2X 体量与获取**：须表单申请，体量未知。

## 5. Stage 0.4 距正式科学验收仍缺什么（不因此改变 Gate）

1. `packet_schema_evaluated`：仍需 Packet（15.33 GB）实测 schema 与捕获时间覆盖（独立价值已论证，非凑项）。
2. 车辆侧接收语义：RSE_BSM 已确认 Rx 日志但无接收时间、采样设计 Unverified——若验收范围含"接收侧描述性参考"，需 BsmMd+BsmP1 完成身份与时间锚链（0.4.3 建议）。
3. 通信时延/丢包的现实参考：本任务候选均为受控试验条件；若验收标准接受"受控试验条件下的现实参考"则 Bristol/SEE-V2X 可支持，若要求自然交通 V2V 则当前公开数据**不可达**（如实缺口）。
4. 采用：驾驶员层面可由 THEA 评估报告支持；控制器层面不可达。

## 6. 最小验证批次（下载后验收条件，供研究者批准）

**批次 A（推荐第一批，通信时延+PDR 现实基准）**：
- Bristol ITS-G5 `importedData` 子集（4 天 MAT；估计数 GiB；完整 34.3 GiB 可选）。
- 峰值磁盘：≤25 GiB；余量合规（当前 ~180 GiB）。
- 验收条件：①解出 Tx/Rx CAM 配对率（SeqNum+StationID）；②同消息 Tx-Rx 时间差分布（声明记录口径）；③PDR/SeqNum 间隙统计与论文值一致性；④若可行，RSSI-距离关系。声明为受控 ITS-G5 条件。

**批次 B（C-V2X 互补，需表单）**：SEE-V2X。验收：端到端时延分布复现。

**批次 C（SPMD 身份链，延续 0.4.3）**：BsmMd（17.29 GB）+ 顺带 RSE_locations.kml（520 B）。验收：TxRandom↔设备映射率、GenTimeRelOffset 实际值、holdout 候选③可行性。

**批次 D（采用-行为参考，纯文档级，无需下载数据本体）**：THEA Phase 3 评估报告 + NYC IE 字典（附件当前缺失，需向 DataHub 索取或从 Sandbox 全量）。

## 7. 需要研究者批准的决定

1. 是否下载 **Bristol ITS-G5**（批次 A；建议先 importedData 子集）。
2. 是否开通 **Globus** 机构通道评估 mCity Rx-BSM（~9 GB）与 SEE-V2X 表单申请。
3. 是否按 0.4.3 建议下载 **BsmMd**（批次 C）。
4. Stage 0.4 验收范围是否接受"受控试验条件下的通信参考"（Bristol/SEE-V2X）作为现实校准依据，还是坚持自然交通 V2V（当前不可达，须以仿真假设声明）。
5. 采用证据采用驾驶员层面（THEA）还是将控制器采用永久归入仿真假设。

**核心交付结论**：四项证据中，**接收时间与通信时延找到了可信、可获取、可复现的真实证据**（Bristol/SEE-V2X，受控条件）；**丢失率找到多个合格候选**（UCI/Bristol/SEE-V2X）；**采用仅在驾驶员行为层面有真实数据**（THEA），控制器层面为真实缺口。推荐下一批优先验证 **Bristol ITS-G5**（批次 A），理由：体量适中、公开获取、同消息双侧时间戳+SeqNum 的完整证据链、自带 RSSI/位置与 PDR 方法，最能直接支撑 Stage I 通信时延与投递率的仿真参数化；BsmMd 批次 C 并行价值最高（解 SPMD 身份死结）。
