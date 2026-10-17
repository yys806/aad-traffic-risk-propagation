# Stage 0.4 任务 0.4.7：SEE-V2X BSM 应用场景获取与通信证据验证

> 任务 AAD-0.4.7（2026-10-17）。**唯一新下载**：`emulating_applications.tar.gz`（5,252,105,816 B，SHA-256 `17AB3AC1…0861`，公开 Drive）。仅提取 `bsm_only/*` + `GNSS/*`（峰值 ~10 GiB，未下载参数扫描/Perception）。Stage 0.4 Gate、历史封存证据、参数未改动。作者邮件草稿保留未发。标注：Fact / Verified / Inference / Unverified / Proposal。

## 0. 前置修复（Git 复现测试）

- **问题**：`code/tests/test_see_v2x_reaudit.py` 读取未提交的 `code/outputs/.../reaudit_results.json`，导致纯克隆下 5 项算术测试 skip。
- **修复**：路径改为已提交的 `code/tmp/reaudit_results.json`。本机全量 **6/6 通过**；纯 Git 克隆下 5 项算术测试真实执行通过，1 项需原始数据的测试明确 skip（`test_pairing_identity_unique_in_raw`，`skipif` 已标注）。manifest/代码/结果哈希一致性已核验。

## 1. 数据获取与结构

- `emulating_applications.tar.gz`：5,252,105,816 B，SHA-256 `17AB3AC150F8965CE6BF9F1935AA294C371A6CE811C3F7454549F842D6C00861`，公开 Google Drive（`drive.usercontent.google.com/download?id=1WodOmwYup3xOT8jNsQ0pbcL6Y4Enk-JL`）。
- 提取：`bsm_only/{indoor_timeExtend,outdoor_intersection}/intersection_{1,2}`（每场景 tx_rsu/t1/t2/t3 + 12 个 rx 文件 + sci + mac.pcap）+ `GNSS/{rsu,t1,t2,t3}.csv`。**未提取** `bsm_perception`、`perception_only`（未授权下载范围外）。
- **设备身份（Fact）**：`parameters.csv` + tx 日志：rsu=1、t1=2、t2=3、t3=4。**BSM 类流量（Fact）**：包大小 128 B、优先级 0/7、SPS 模式、预留/间隔 100 ms（=10 Hz），匹配 BSM 心跳特征——**但属 C-V2X 应用仿真流量，不等同实际道路标准 BSM**（保留边界）。

## 2. BSM 消息关联（任务 A）

- 文件：`tx_<dev>.csv`（`seq_num` 连续）+ `rx_<rxdev>_tx_<txdev>_bsm.csv`（含 `tx_seq_num`/`tx_timestamp`/`rx_timestamp`/`latency`/`extra`）。
- **配对（Verified）**：按 `(tx_equipment_id, tx_seq_num)`，4 场景 × 12 有序设备对。室内 2 场景配对率 **0.9978–0.9997**；室外 intersection_1 **0.22–0.90**、intersection_2 **0.22–1.0**。`extra=1` 插值行已排除。
- 所有 tx `seq_num` 唯一、无重复；未配对行 = 真实未接收（发送端有记录、接收端无对应 seq）。

## 3. PDR/PER 与接收机会（任务 B）

沿用 0.4.6.2 三口径（完整运行/接收窗口/字段）。**本批接收机会证据显著增强（GNSS）**：

- **室内（intersection_1/2）**：PDR_full 0.9978–0.9997，GNSS 证设备全程在窗口内 → 接收机会**高置信成立**（描述性投递≈链路 PDR）。
- **室外（intersection_1/2）**：PDR_full 0.22–1.0。GNSS 窗口（t1/t2/t3 各 9,631 s）覆盖全部通信时间戳（配对行 100% 落入）→ **接收设备在线证据 Verified**；未接收=真实未捕获（链路/竞争/距离），非启停边界。**这是 0.4.6 停车场样本未具备的关键改进**。
- **结论**：室外 PDR 分母明确（=该对运行内发送数）、接收机会已证 → **可作为受控 PC5 环境下链路投递率使用**；室内接近 100%（饱和）。

## 4. GNSS 轨迹与通信距离（任务 C）

- **GNSS 字段（Fact）**：`Latitude/Longitude/Altitude/Vel_E/Vel_N/Vel_U/UTC_ns`（100 Hz，UTC 纪元）；t1/t2/t3 各 962,995 行/9,631 s；rsu 静态单点。
- **时间对齐（Verified）**：通信 `tx/rx_timestamp (µs)` 与 GNSS `UTC_ns` 同 UTC 纪元——所有配对行时间戳 100% 落入各自 GNSS 窗口（无任意偏移拟合）。
- **距离分箱**：室外 mobile-mobile 对（如 t2↔t3）全部样本落在 **0–50 m**（试验场近距离），PDR 随距离趋势**因动态范围不足无法分辨**（Unverified 为距离函数）；mobile→rsu（rsu 静态、距离变化）见逐对 PDR 0.55–0.90。室外为短距离场景，**不能外推长距离**。
- **运动状态**：`Vel_E/Vel_N` 可用；本批未深入速度×PDR 分层（距离箱已受限）。

## 5. 通信时延与时钟（任务 D）

- **数值（Verified）**：`(rx_timestamp−tx_timestamp)/1000` = `latency` 列，全对一致；**包大小恒定 128 B**（本批无时延×包大小混杂）。
- **时钟证据（增强但仍 Unverified 于亚毫秒级）**：所有时间戳与 GNSS 同 UTC 纪元（无秒级偏移）；GNSS `UTC_ns` 暗示各接收机授时纪律，但**未见 PPS/相位同步精度声明**，故绝对时延的**亚毫秒级**物理意义仍 Unverified；**毫秒级及以上**的相对时延/排序/抖动**更可信**（Epoch 一致 + GNSS 覆盖）。
- **跨运行差异**：室内 P50 ~10.4/11.0 ms、室外 11.2/11.7 ms、逐对 9.0–14.2 ms——差异在 ms 级，与 0.4.6.2 包大小效应（此处恒定）无关；候选解释含真实信道竞争/距离/优先级与时钟，**现有数据不可逐一区分**（保留多解释）。
- **结论**：绝对时延、分布形态、合并分位数**仍不冻结**为正式参数；相对/排序可用。

## 6. 对 AAD 的科研价值（任务 §五）

| 层级 | 指标 | 结论 |
|---|---|---|
| **可信真实参考（受控 PC5）** | 消息关联、PDR（接收机会已证，室外 0.22–0.90 / 室内 ~1.0）、相对时延排序、GNSS 轨迹绑定 | 可用于 SUMO 通信模块**候选参数/敏感性范围** |
| **描述性统计** | 绝对时延 P50 ~10–12 ms、逐对抖动 | 仅作参考，不冻结 |
| **不能用于正式校准** | 亚毫秒绝对时延、距离×PDR 曲线（动态范围不足）、自然交通 V2V 语义 | 受控条件 ≠ 自然交通；保留边界 |

## 7. 结论速览

- BSM 消息关联：**Verified**（4 场景 12 对，配对率 0.22–1.0）。
- PDR 接收机会：**室外已证（GNSS 覆盖 100%）**；室内高置信——**显著优于 0.4.6 停车场样本**。
- GNSS 距离：**时间对齐 Verified**；距离动态范围不足（全 0–50 m），**不能作距离×PDR 曲线**。
- 时延：数值 Verified；时钟 epoch 一致但**亚毫秒同步仍 Unverified**；绝对值不冻结。
- 正式通信参数：**仍未冻结**；本批提供受控 PC5 候选参数范围。

## 8. 尚需研究者决定

1. 是否将受控 PC5 的 PDR/时延范围作为 SUMO 通信模块**候选参数**（非正式校准）。
2. 是否授权发送作者邮件（时钟相位同步精度 / `per_ue_loss_pct` 分母 / BSM 仿真配置细节）。
3. 是否需补充**长距离/动态** C-V2X 数据以建立距离×PDR 关系（当前样本 0–50 m 不足）。

**下载/分析代码/结果**：`dataset/.tmp_downloads/see_v2x_emulating_applications_download.json`、`code/tmp/analyze_bsm.py`、`code/tmp/bsm_analysis_results.json`。
