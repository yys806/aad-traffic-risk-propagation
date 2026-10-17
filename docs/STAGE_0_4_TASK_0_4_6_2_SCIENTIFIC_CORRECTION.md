# Stage 0.4 任务 0.4.6.2：SEE-V2X 通信指标科学修正与下一批数据验证准备

> 任务 AAD-0.4.6.2（科学修正 + 复现修复 + 验证准备，2026-10-17）。**零新下载、零申请、零邮件**。仅基于已授权样本与公开文档。Stage 0.4 Gate、参数与历史封存证据未改动。标注：Fact / Verified / Inference / Unverified / Proposal。

## 1. 任务 A：PDR/PER 接收机会与统计口径修正

### 1.1 物理意义（关键修正）

**`parameters.csv` 证明 10 次运行配置各不相同**（非重复实验）：包大小 100/1470/4000/5000/8000 B × 优先级 0 或 7，SPS 模式，预留/间隔 20 ms（全部运行发送速率实测 = **50 Hz**，与 20 ms 间隔一致）。同时存在**时间戳起止证据**（`code/tmp/param_timestamp_summary.json`）：

| run | 包大小/优先级 | 发送数 | 接收数 | tx 时长 s | rx 时长 s | 发送→接收首个时戳差 (µs) |
|---|---|---:|---:|---:|---:|---:|
| 0 | 4000B/P0 | 7,918 | 5,304 | 158.3 | 151.2 | +2,763,334 |
| 2 | 100B/P0 | 5,742 | 5,591 | 114.8 | 111.8 | +3,032,931 |
| 4 | 8000B/P0 | 5,013 | 1,378 | 100.2 | 97.1 | +3,120,906 |
| 7 | 100B/P7 | 4,899 | 4,899 | 98.0 | 98.0 | +12,396 |

接收端时长系统性短于发送端（run2：rx 111.8 s vs tx 114.8 s），且首个接收时戳晚于发送首个时戳约 3 秒。**这些边界段（如 Run 2 的 [0,150]）高度符合"接收设备晚启动/早停止记录"的启停边界特征，而非链路上行丢包**。但：

- **接收设备是否全程在线并处于有效接收状态：Unverified**——无设备上线/下线日志、无 GNSS 活动状态、无 RRC/PHY 状态字段可证明接收机在全部发送期间均处于接收窗口。
- **运行首尾未接收消息属真实链路丢包还是启停边界：Unverified**——现有记录无法区分。

### 1.2 三种口径的物理意义（最终证据表）

| 口径 | 分母 | 物理意义 | 适用条件 |
|---|---|---|---|
| **完整运行 PDR（full-run）** | 运行内全部发送 | **描述性接收比例**（"该运行记录了多少接收"） | 接收设备全程在线时 ≈ 链路 PDR；启停边界存在时**系统性低估** |
| **共同窗口 PDR（common-window）** | 接收覆盖序号区间内发送 | **窗口内投递质量** | 排除启停边界后的链路质量；**系统性高估**（剔除了可能的真实边界丢包） |
| **字段 `per_ue_loss_pct`** | ≈接收窗口 | 论文统计口径 | 同窗口口径 |

**修正 0.4.6.1 的过强表述**：完整运行 PDR 的分母定义明确，但**不等于它是唯一物理可靠的无线链路 PDR**——接收机会（接收机全程在线）未证。Run 2 的 [0,150] 边界极可能是启停而非丢包，**保留完整运行日志投递比例（0.9737）作为描述性指标**，**不解释为正式链路丢包率**（Unverified，待设备在线证据）。

### 1.3 接收机会是否确认？—— **未确认（Unverified）**

需要：设备启停/在线状态日志、GNSS 活动时间、或 RRC/PHY 状态字段。现有日志均无。下一批 GNSS 轨迹若含时间戳对齐，可部分约束接收在线边界（见 §4）。

## 2. 任务 B：时延差异的科学解释修正

### 2.1 真实 PHY/MAC 序列化解释（Inference，高置信）

0.4.6.1 把跨运行 P50 差异（8.8–32 ms）记为"可能时钟偏移"。**修正**：

- **全部运行发送速率实测 = 50 Hz**（20 ms 间隔，无漂移）。
- **P50 延迟与包大小单调相关**：100B（run2 P0=8.8、run7 P7=11.0 ms）、1470B（run1 11.1、run6 20.9）、4000B（run0 17.2、run5 24.75）、5000B（run3 25.7、run8 32.0）、8000B（run4 21.8、run9 30.0）。这与 **PHY/MAC 序列化时间 ∝ 包长 + 信道竞争**一致，是真实通信条件变化，**不是时钟偏移**。
- **运行内前后半段差异**（run2 −6.8 ms）是**单运行内真实通信条件随时间的真实变化**（信道竞争/环境），不是时钟漂移。

### 2.2 三类解释的区分与可识别性（任务 §二.2）

| 解释 | 能否用现有数据区分 | 结论 |
|---|---|---|
| 真实通信条件变化（包大小/信道） | **能**（parameters.csv + 速率实测 50 Hz + P50↔包长单调） | **Inference（高置信）**，解释跨运行 P50 差异的主体 |
| 跨设备固定时钟偏移 | **不能**（绝对偏移无共钟参考；但它不影响跨运行差异的排序） | Unverified（存在性未证；但**不主导**跨运行模式） |
| 时钟漂移 | **不能**（同一时钟差在各运行内稳定，漂移需时间分辨；运行内变化可用真实条件解释） | Unverified |

**纠正过强表述**：0.4.6.1 的"跨运行中位数差异证明时钟偏移""前后半段差异证明时钟漂移"**不成立**——前者被包大小序列化更好地解释，后者被真实条件变化更好地解释。时钟偏移/漂移仍是 Unverified 的独立问题，但**不是**跨运行时延差异的主因。

### 2.3 可信层级（修正后）

| 层级 | 结论 |
|---|---|
| 同消息关联 | **Verified**（配对率 1.0，独立测试通过） |
| 时间戳差值复算 | **Verified**（(rx−tx)/1000 = latency 列，abs diff max 0，独立测试通过） |
| 逐运行时延统计 | **Verified（数值层）** |
| 运行内相对变化与 jitter | **相对可信**（真实条件变化为主，漂移未证） |
| 跨运行合并分布 | **描述性可用**（随参数变化的真实分布，非单一校准值）；不得冻结为固定参数 |
| 真实端到端绝对时延 | **Unverified**（绝对偏移未证） |

**正式校准仍不冻结**：绝对时延、固定 PDR 值、合并分位数均不作 AAD 正式通信参数；仅"随包大小变化的时延/PDR 关系"作为描述性先验。

## 3. 任务 C：Git 可复现性修复

### 3.1 问题确认与根因

- **封存包** `stage_0_4_see_v2x_reaudit_v1/` 自始完整（含 `method_reaudit_see_v2x.py`、`reaudit_results.json`）。
- **`evidence/results/RES-STAGE-0.4-SEE-V2X-REAUDIT-V1/`** 缺这两个文件；根因是 0.4.6.1 的 evidence exporter 手写对未包含它们（exporter 仅导出 `.json/.md/.txt/.sha256` 类型，`.py` 被策略拒绝）。
- **修复**：①封存包 manifest 已补充（非覆盖式，见 §3.3）；②exporter 保持类型策略（`.py` 不进入便携证据），复现性改由仓库代码承载——`code/tmp/reaudit_see_v2x.py` 与 `code/tmp/reaudit_results.json` 已纳入 Git（见下）；③新增独立测试 `code/tests/test_see_v2x_reaudit.py` 锁定关键算术关系。

### 3.2 修复项（已全部完成）

1. **`code/tmp/reaudit_see_v2x.py`、`code/tmp/reaudit_results.json`** 纳入 Git 可追溯证据（方法 + 逐运行机器可读结果）。
2. **`code/tests/test_see_v2x_reaudit.py`**（6 个测试，全部通过）：Run 2 完整运行 PDR=0.9737（非 1.0）、分母守恒（tx = rx + 未接收）、完整≤窗口≈字段、latency 数值一致（abs diff max 0）、ms 单位、原始日志配对唯一性。
3. **封存包 manifest** 已补充 method+results（非覆盖式）。
4. **exporter** 保持类型策略（不含 `.py`）。

### 3.3 纯 Git 克隆的验证边界（区分两类）

- **无需原始数据即可验证**：`test_see_v2x_reaudit.py` 前 5 个测试从封存的 `reaudit_results.json` 重算关键算术关系（Run 2 PDR、分母守恒、窗口↔字段差、latency 数值一致性）——纯克隆可复算。
- **需要原始数据才能全量重算**：`test_pairing_identity_unique_in_raw`（遍历 10 个 tx 日志验证 (equipment_id, seq_num) 唯一性）与逐行时延分布——需要 `dataset/.tmp_downloads/parkinglot_extracted/`（本地、不随 Git 分发）。测试已用 `@pytest.mark.skipif` 优雅降级。

## 4. 下一批 4.89 GiB（`emulating_applications.tar.gz`）验证计划

### 4.1 能提供什么（Proposal）

1. **BSM-only 场景**：10 Hz 类 BSM 流量的端到端时延与 PDR——更接近 AAD 目标应用的消息模式。
2. **100 Hz GNSS 轨迹**：把时延/PDR 与真实移动轨迹、发送-接收距离绑定。
3. **距离/运动状态 × PDR/PER**：分箱统计（Proposal）。
4. **时钟**：GNSS 若含授时纪律可校准跨设备偏移；**若仅定位则时钟问题仍不可解**（任务红线）。

### 4.2 最小必要文件与磁盘

- 全档 4.89 GiB；优先 **BSM-only 子目录**（README 结构：`Emulating Applications/BSM Only/{Indoor timeExtend, Outdoor Intersection}`）+ `GNSS/`。峰值 ≈10 GiB。
- 若 Drive 支持按成员下载，优先仅 BSM-only + GNSS（估计 <2 GiB）；否则整档。

### 4.3 验证步骤与成功/失败标准

1. **结构核验**：列出 BSM-only 文件（tx/rx/GNSS）；成功=文件齐全。
2. **时钟证据**：检查 GNSS 字段是否含 PPS/授时纪律或共钟标记；成功=找到独立时钟证据 → 时延从 Unverified 升至可校准；失败=GNSS 仅定位 → 时钟仍 Unverified。
3. **配对**：BSM 场景按 `tx_seq_num` 配对；成功=配对率与 0.4.6 相当。
4. **时延×距离**：分箱统计 latency/PDR vs 距离与运动状态；成功=趋势稳定且与停车场数据可比。
5. **PDR**：完整运行/窗口/字段三口径对齐，按任务 A 的接收机会约束修正边界。

### 4.4 若时钟仍无法确认

- **仍具独立价值**：距离×PDR 关系、时延×包大小/距离关系、BSM 类流量的相对分布。
- **不能用于**：绝对时延参数、固定 PDR 值、自然交通 V2V 校准。

## 5. 作者咨询邮件草稿（未发送，供研究者授权）

```
Subject: SEE-V2X dataset – clock synchronization and PDR denominator questions

Dear SEE-V2X team,

Thank you for releasing the dataset. We validated outdoor_parkinglot and
have three questions before using it for communication calibration:

1. Clock synchronization: are the tx and rx host timestamps (tx_timestamp,
   rx_timestamp) from a common clock (GNSS/PPS, PTP, shared host)? Is the
   inter-device clock offset measured or estimated? We need the residual
   offset to interpret absolute latency.

2. tx_timestamp capture: is tx_timestamp embedded by the transmitter and
   delivered with the packet, or recorded separately and aligned by seq_num?

3. per_ue_loss_pct: what is the exact denominator (window and receive-
   opportunity definition)? Does it exclude device start/stop boundaries?

Any configuration or code pointers appreciated.

Best regards,
[AAD project research engineer]
```

## 6. 尚需研究者批准

1. 下载 `emulating_applications.tar.gz`（建议先 BSM-only + GNSS，或整档 4.89 GiB）。
2. 授权向 SEE-V2X 作者发送 §5 邮件。
3. 确认"完整运行 PDR 仅作描述性指标、不作正式链路丢包率"（接收机会 Unverified 时）。
4. 确认时延仅在"随包大小/距离变化的关系"层面作为描述性先验，绝对值仍冻结。

## 7. 结论速览

| 问题 | 结论 |
|---|---|
| PDR 接收机会是否确认 | **Unverified**（启停边界 vs 丢包不可分；完整运行 PDR 仅描述性） |
| 时延差异主因 | **真实 PHY/MAC 序列化（包大小×优先级）**，非时钟偏移（Inference，高置信） |
| 时钟偏移/漂移 | Unverified（不主导跨运行模式；绝对时延仍冻结） |
| Git 可复现 | **已修复**（方法+结果入 Git，6 独立测试通过，封存 manifest 补充） |
| 下一批 4.89 GiB | **建议**（GNSS 时钟参照 + 距离×时延/PDR；时钟可能仍不可解） |
