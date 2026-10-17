# Stage 0.4 任务 0.4.7.1：SEE-V2X BSM 通信证据科学复核与交付修复

> 任务 AAD-0.4.7.1（2026-10-17）。**零新下载、零邮件**。基于已下载的 `emulating_applications.tar.gz` 复核科学解释、修复 GitHub 交付。Gate、历史封存证据未改动。标注：Fact / Verified / Inference / Unverified / Proposal。

## 1. GitHub 交付缺失的根因与修复

**根因**：0.4.7 的 commit `f9181fd` 实际只含 `code/tmp/analyze_bsm.py` + `code/tmp/bsm_analysis_results.json`（`git show --stat` 证实）；报告/注册表/AI_CONTEXT 的变更在工作区**未暂存**（大概率因 `.gitignore` 或提交遗漏），故未推送到 GitHub。

**修复（本任务完成）**：
1. 正式报告 `docs/STAGE_0_4_TASK_0_4_7_SEE_V2X_BSM_VALIDATION.md`（补全）+ 本复核报告 `docs/STAGE_0_4_TASK_0_4_7_1_SCIENTIFIC_REAUDIT.md`；
2. 注册表、STAGE_INDEX、CHANGELOG、AI_CONTEXT 已同步并 commit；
3. 新的可追溯证据包 `RES-STAGE-0.4-SEE-V2X-BSM-REAUDIT-V1`（不覆盖 0.4.7 的 V1）；
4. `test_see_v2x_reaudit.py` 路径修复（读已提交的 `code/tmp/reaudit_results.json`）。

## 2. 消息配对率与接收比例（任务 A，已正确区分）

**配对率（Verified）= 1.000**：全部 48 个有向设备对（4 场景 × 12 对），`extra=1` 已排除，无重复 Rx/Tx、序号回绕或跨场景身份混淆（设备身份已校验，键为 `(tx_equipment_id, tx_seq_num)`）。

**接收比例（日志）≠ 配对率，已分开报告**（全 48 对，机器可读 `code/tmp/bsm_reaudit_0471.json`）：

| 场景 | 配对率 | 接收比例（全运行） |
|---|---:|---|
| indoor_1 / indoor_2 | 1.000 | 0.998–0.9999 |
| outdoor_1 | 1.000 | 0.22–0.90 |
| outdoor_2 | 1.000 | 0.22–1.00 |

**澄清 0.4.7 的概念混淆**：0.4.7 曾把 `paired/tx_total` 称为"配对率"——错误。`paired/tx_total` 是**日志接收比例**；**配对率 = 已记录 Rx 中唯一匹配 Tx 的比例**（= 1.0）。未收到消息 ≠ 无线丢包（仅当接收机会已证才成立）。

## 3. GNSS 能证明什么？接收机会能否确认？（任务 B，重大修正）

**修正 0.4.7 的过度解释**：0.4.7 以"GNSS 覆盖通信时间窗"推定"接收设备全程在线"——**证据不足，已纠正**。

- **GNSS 实际能证明的（Fact）**：t1/t2/t3 的 GNSS 记录存在、单调、`UTC_ns` 无重复、中位采样 10 ms；RSU 为**静态单点**（无轨迹）。
- **GNSS 不能证明的（Unverified）**：①GNSS 持续定位 ≠ 无线接收机有效在线（无 RRC/PHY/无线模块状态证据）；②RSU 完全无移动 GNSS，**不得从三个移动设备的 GNSS 推广到 RSU**。
- **关键发现（Fact）**：`tx_timestamp (µs)` 与 GNSS `UTC_ns` **相差 ×1000 系数**——两者纪元对齐纯靠数值缩放，**无独立时钟证据**。
- **接收机会逐设备对判定（Unverified，全部）**：无无线模块在线证据 → 全部 48 对保持 Unverified。室外 0.22–0.90 **仅作受控场景下的日志接收比例，不宣称已验证的真实无线链路 PDR**。

## 4. 时钟同步与时延可信性（任务 C）

- **纪元/单位（Fact）**：`timestamp (us)` 与 GNSS `UTC_ns` 同 UTC 纪元但差 ×1000 缩放；**同一 UTC 纪元 ≠ 毫秒级同步**。
- **GNSS 无 PPS/PTP/共钟证据** → 设备间时间误差上界**无法给出**（Unverified）。
- **时延分层结论**：
  - 数值复算 `(rx−tx)/1000` = `latency` 列：**Verified**；
  - 真实端到端绝对时延：**Unverified**（时钟偏移未证）；
  - 运行内时延变化/相对排序：**相对可信**（真实条件为主）；
  - 跨运行分布/分位数：**描述性**，不作正式校准。

## 5. 距离—通信统计实际支持到什么程度？（任务 D）

- **GNSS 覆盖范围（Fact）**：GNSS 仅覆盖**室外**场景（室内 tx 时间戳超出 GNSS 窗口）——**室内场景无 GNSS 距离数据**。
- **室外距离**：三个移动设备在 ~57 s 室外窗口内移动 ~3.9 m（纬度），GNSS 抖动与短距离使**准确距离不可靠**；RSU 静态单点。**实际覆盖 = 极短距离（<10 m），动态范围不足以建立距离—PDR 曲线**。
- **不强行拟合**、不外推；报告为 min/P50/P95/max 仅室外 ~0–10 m。

## 6. GitHub 交付与可复现性（任务 E）

- `test_see_v2x_reaudit.py` 已修复读已提交的 `code/tmp/reaudit_results.json`（本机 **6/6 通过**）。
- **纯 Git 克隆**：5 个算术测试真实执行通过，1 个原始数据测试明确 skip（`test_pairing_identity_unique_in_raw`，条件 `skipif` 已标注）。
- 便携证据 `--verify` OK；manifest/SHA-256 一致。
- 新增独立复核包 `RES-STAGE-0.4-SEE-V2X-BSM-REAUDIT-V1`（不覆盖 V1）。

## 7. 结论速览

| 指标 | 结论 |
|---|---|
| 消息关联（48 对） | **Verified**（配对率 1.0） |
| 日志接收比例 | 室内 0.998–1.0 / 室外 0.22–1.0（**描述性**，分母=运行内发送数） |
| **真实链路 PDR / 接收机会** | **Unverified**（无无线在线证据；GNSS≠接收机在线；RSU 无 GNSS） |
| 时钟同步 | **Unverified**（仅同纪元×缩放，无 PPS/PTP/误差上界） |
| 时延绝对值 | **Unverified** |
| GNSS 距离 | 仅室外 ~0–10 m（室内无 GNSS），不足建距离—PDR |
| AAD 候选现实参考 | 受控 PC5 的消息关联方法 + 接收比例范围（描述性） |
| 不能用于校准 | 真实链路 PDR、绝对时延、距离—PDR、自然交通 V2V |

## 8. 尚需研究者决定

1. 是否将受控 PC5 的**日志接收比例**（非链路 PDR）作 SUMO 通信模块候选参数；
2. 授权发送作者邮件（时钟相位同步 / `per_ue_loss_pct` 分母 / 无线模块在线状态证据）；
3. 是否需补充长距离/动态 C-V2X 数据。

**下载/代码/结果**：`dataset/.tmp_downloads/see_v2x_emulating_applications_download.json`、`code/tmp/reaudit_bsm_0471.py`、`code/tmp/bsm_reaudit_0471.json`。
