# Stage 0.4 任务 0.4.6：SEE-V2X 最小样本获取与通信指标实证验证

> 任务 AAD-0.4.6（实证验证，2026-10-17）。
> **勘误（2026-10-17，AAD-0.4.6.1）**：①本报告 `independent_pdr` 采用接收窗口口径（把运行边界未接收段排除在分母外），**系统性高估 PDR**（Run 2 实为 0.974 而非 1.0）；正确口径为**完整运行 PDR**（分母=运行内全部发送）。②latency 存在跨运行固定时钟偏移（P50 8.8–32 ms），**合并分位数不可靠**；逐运行形态相对可信。详见 `docs/STAGE_0_4_TASK_0_4_6_1_SCIENTIFIC_REAUDIT.md` 与结果 `RES-STAGE-0.4-SEE-V2X-REAUDIT-V1`（本封存包未改动）。**唯一授权样本**：`SEE-V2X/parameters_sweeping/outdoor_parkinglot.tar.gz`（4,883,437 B，公开 Google Drive，无需申请）。未下载 `emulating_applications`（4.89 GiB）或其他数据。Stage 0.4 Gate（`pending_official_packet_access`）、参数与封存证据未改动；不冻结任何正式通信参数。
> 四层次区分：**字段存在 / 数值可计算 / 物理意义有效 / 可用于现实校准**——本批验证了前三层，**第四层（正式校准）仍须等待时钟/分母语义与更大样本**。

## 1. 获取与完整性（Fact）

| 项 | 值 |
|---|---|
| 来源 | 官方 SEE-V2X Google Drive 共享（id `133L1r_C9y08jPSyzL64_28AVGkpXAzek`）；0.4.5 曾误记父文件夹 ID，已更正 |
| 大小 | **4,883,437 B**（与 `Content-Range: bytes 0-0/4883437` 元数据一致） |
| SHA-256 | `ABFE57ACC0E5F537C2B07AF84BF7998E55C589629F88A39FBA75C90F09133F89` |
| 解压 | `1_tx/0..9` 共 10 次运行；`tx_t1.csv`（发送日志 t1→）、`rx_t3_tx_t1.csv`（接收日志 t3←t1）、`sci.csv`、`mac.pcap`；总解压 ~18 MB，峰值远 <0.5 GiB |
| 场景 | C-V2X 侧链（LTE Rel.14 Mode 4）参数扫描，**室外停车场**，1 发送方(t1)→1 接收方(t3)；室内参数扫描与 BSM 应用仿真场景未下载（未授权） |

## 2. A. 数据结构与同消息关联（核心结果）

- 发送日志 `tx_t1.csv`：字段 `index, tx_equipment_id, seq_num, priority, timestamp, channel_busy_percentage, packet_size`；`seq_num` **0..N−1 连续无重复**（run 3 实测 5,570 个唯一 (equipment_id, seq_num) 对）。
- 接收日志 `rx_t3_tx_t1.csv`：含 `rx_timestamp (us), latency (ms), per_ue_loss_pct (%), ipg (ms), tx_equipment_id, tx_seq_num, tx_timestamp (us), channel_busy_percentage, extra, packet_size`。
- **同消息配对（实测）**：按 `(tx_equipment_id, tx_seq_num)` 关联 tx↔rx 日志，**10/10 次运行配对率 = 1.000**（配对数 = rx 数据行数；rx 侧无发送日志缺失的孤立行——`rx_paired − tx_sent = 0`）。`extra=1` 插入行已按规则排除（占比 ~75%，是论文绘图用的插值行）。
- 判定：**同消息关联 = Verified（本批实证）**，前提是日志按设备命名（`tx_t1` / `rx_t3_tx_t1`）锁定发送-接收设备对；字段名需按实际表头（`timestamp`/`tx_timestamp (us)`/`rx_timestamp (us)`；注意 README 与实际表头存在拼写差异 `tx_prioirty`）。

## 3. B. 通信时延

- **独立复算**：`d_ms = (rx_timestamp(us) − tx_timestamp(us))/1000`，与数据集 `latency (ms)` 列在 **30,571 条配对行上逐行完全一致（abs diff max = 0.0）**——README 公式实证成立。
- **分布（10 次运行合并，ms）**：min 4.955 / P5 6.856 / P25 9.223 / **P50 16.787** / P75 21.177 / P95 34.861 / P99 40.024 / max 60.120；**负时延 0 条**。
- **物理意义（分层判断）**：
  - 数值可计算：Verified（同行差值一致、无负值、量级合理）。
  - 物理意义有效（=真实端到端时延）：**仍 Unverified**。任务警示"同行不自动抵消时钟偏差"完全正确——`tx_timestamp` 与 `rx_timestamp` 来自两台设备各自时钟；rx 日志把发送端的 `tx_timestamp` 与接收端 `rx_timestamp` 同行记录，**该日志由 t3（接收设备）生成**，但 `tx_timestamp` 实为发送端 t1 发出时戳，被接收端捕获/携带。两台设备的时钟差直接进差值：`measured = true_latency + (O_t3 − O_t1)`。README/论文未给出共用钟/GNSS-PPS/PTP 或实测互偏移。本批无独立共钟事件可校（室内参数扫描无 GNSS；BSM 应用仿真场景的 GNSS 未下载）。
  - 结论：**latency 分布形态（中位、分位、抖动）可信**；**绝对值可能含固定时钟偏移**——不得冻结为 AAD 正式时延参数；需更大样本或作者配置确认（见 §6 邮件草稿）。

## 4. C. PDR/PER（分母与接收机会）

- **独立复算（sender-base）**：`PDR = (rx∩tx 接收到的发送数) / tx_total`。逐 run 与字段 `per_ue_loss_pct`（≈100×(1−PDR)）对照：

| run | tx 行 | rx 数据行 | 独立 PDR | 字段 loss% |
|---|---:|---:|---:|---:|
| 0 | 7,918 | 5,304 | 0.701 | 29.9 |
| 1 | 6,656 | 5,327 | 0.850 | 15.0 |
| 2 | 5,742 | 5,591 | 1.000 | 0.0 |
| 3 | 5,570 | 2,103 | 0.378 | 61.2 |
| 4 | 5,013 | 1,378 | 0.284 | 71.6 |
| 5 | 5,366 | 1,122 | 0.212 | 78.8 |
| 6 | 4,951 | 3,431 | 0.693 | 30.7 |
| 7 | 4,899 | 4,899 | 1.000 | 0.0 |
| 8 | 4,741 | 850 | 0.179 | 82.1 |
| 9 | 4,573 | 566 | 0.124 | 87.6 |

- **分母语义澄清（实证）**：字段 `per_ue_loss_pct` ≈ 100×(1 − rx_received/tx_sent)——即以**发送端发送数为分母**的 PER。run 3 独立 sender-base PDR=0.378，字段换算 0.388（差 ~1 pp，来自 run 内序号窗口与边界处理）；run 2/7 全接收（loss 0%）。**接收机会**：发送端连续 seq 无重启（0..N−1），接收端覆盖完整——故"序号间隙=丢包"成立（日志完整性已验证）。
- 判定：**PDR/PER = Documented + 本批 Verified（sender-base 复算与字段一致）**；分母=发送数、接收机会=该次运行内，明确可复算。`extra=1` 行已全部排除，不影响统计。

## 5. D. 通信环境字段

- `channel_busy_percentage`（接收端报告，3 次运行样本）：min 0% / P50 5% / P95 10% / max 23%——停车场低占空比环境，量级合理，可作 SUMO 场景的背景占用参考。
- `sci.csv`（USRP 空口侧链控制信息，µs 时间戳、MCS、重传等）与 `mac.pcap` 在样本中存在——**本批未深入**（属 MAC/PHY 层，超出本任务四项指标验证范围；可在后续批次按需启用）。
- **不可直接对应 SUMO**：停车场低负载室外 PC5 环境 ≠ 城市密集交通的占用/干扰；字段只能作为"干净单跳 PC5 先验"参考，不能直接映射为 SUMO 通信损伤参数（延续 0.4.4/0.4.5 边界）。

## 6. 官方时钟与分母证据 + 作者咨询邮件草稿

- 公开材料（README、论文摘要、GitHub 脚本 `cv2x_data_handler.py`/`pssch_ue.c`）已说明 latency 公式与字段；**未发现**共用钟/GNSS-PPS/PTP 或 `per_ue_loss_pct` 精确分母的官方文字说明。
- 已准备英文作者咨询邮件草稿（见 §8 附），**未发送**——列出三个问题：时钟同步架构与互偏移；`tx_timestamp` 进入接收日志的捕获点；`per_ue_loss_pct` 精确分母与窗口。

## 7. 是否建议下载下一批 4.89 GiB（`emulating_applications`）？

**建议批准（条件性）**。新增科学证据：①BSM-only 应用场景（10 Hz 类 BSM 流量）+ 100 Hz GNSS 轨迹——可把时延/PDR 与真实移动轨迹、距离绑定；②路口室外场景（更贴近 AAD 目标环境）；③GNSS 可能提供跨设备共钟参照（GPS 纪律钟）以校准时钟偏移（Unverified→可能升至 Verified）。代价 ~5 GiB（远低于余量）。前提：本批核心指标已实证成立，下一批为"场景泛化+时钟校准"。

## 8. 附录：作者咨询邮件草稿（未发送）

```
Subject: SEE-V2X dataset – clock synchronization and PDR denominator questions

Dear SEE-V2X team,

Thank you for releasing the dataset. We are validating it for latency and
PDR analysis and have two technical questions:

1. Clock synchronization: are the tx and rx host timestamps (tx_timestamp,
   rx_timestamp) derived from a common clock (GNSS/PPS, PTP, shared host)?
   Is the inter-device clock offset measured or estimated anywhere? We need
   to know the residual offset to interpret the absolute latency values.

2. latency capture point: the rx log carries tx_timestamp. Is tx_timestamp
   embedded by the transmitter and delivered to the receiver with the packet,
   or is it recorded separately and later aligned by seq_num?

3. per_ue_loss_pct: what is the exact denominator (window and receive-
   opportunity definition)? Does it exclude periods when the sender is not
   transmitting?

Any pointers to the configuration or code would be appreciated.

Best regards,
[AAD project research engineer]
```

## 9. 结论速览（分层）

| 指标 | 结论 |
|---|---|
| 同消息关联 | **Verified**（10/10 run 配对率 1.0，seq_num 唯一） |
| latency 数值可计算 | **Verified**（rx−tx 与 latency 列逐行一致） |
| latency 物理意义（真实时延） | **Unverified**（时钟偏移未证；分布形态可信、绝对值待校） |
| PDR/PER | **Verified**（sender-base 独立复算与字段一致；分母=发送数明确） |
| 信道占用/环境 | **Documented**（可作低负载参考；不可直接映射 SUMO） |
| 正式校准资格 | **暂不可**（须先解时钟/分母+BSM 场景泛化） |

**下载记录**：`dataset/.tmp_downloads/see_v2x_outdoor_parkinglot_download.json`（SHA-256、大小、来源）；验证代码 `code/tmp/validate_see_v2x.py`；结果 `dataset/.tmp_downloads/see_v2x_validation_results.json`。
