# Stage 0.2 正式风险测量一致性修复（2026-10-11）

## 修复结论

本次仅修复三个确定性工程问题，没有改变 P2、tau、风险公式或历史结果。四个封存 NGSIM state 输入重新提取得到 **4,545** 个 P2 事件，事件成员哈希和实际观测确认时间沿用同一提取结果；新统计区分唯一后车与唯一后车—前车车辆对。

| 源 | 事件数 | 唯一后车轨迹数 | 唯一车辆对数 |
|---|---:|---:|---:|
| Lankershim complete | 2,227 | 1,103 | 1,380 |
| US-101 07:50–08:05 | 543 | 353 | 416 |
| US-101 08:05–08:20 | 732 | 445 | 550 |
| US-101 08:20–08:35 | 1,043 | 611 | 726 |
| **合计** | **4,545** | **2,512** | **3,072** |

## 三项修复

1. `contribution_bounds()` 先判断空间归属：明确区域外记录恒为 `[0,0]`，即使 TTC 缺失或无效；区域未知为 `[0,1]`；区域内再独立判断测量可靠性。由此不再把 TTC 缺失误解为空间归属未知。
2. 验证脚本新增完整作用域车辆对键：`source_file|dataset|site|window_id|source_member|trajectory_id|leader_trajectory_id`，同时输出 `unique_follower_count` 和 `unique_pair_count`。不同前车和不同来源不会合并。
3. `continuity_is_valid()` 使用 NGSIM 的 `diagnostic_clock_anchor_ms`，兼容仅用于构造夹具的旧别名；时钟、作用域、后车、前车任一字段缺失或冲突均 fail-closed。帧差按实际采样步长计算：100 ms 对应 1 帧，200 ms 对应 2 帧；二者不被宣称等价。

## 测试与证据

新增测试覆盖：可靠区域外但 TTC 无效、前车切换、跨来源重号、诊断时钟缺失、跨时钟切换、100/200 ms 步长。针对性测试 6 passed；全量回归和 compileall 另行执行。独立产物位于：

`code/outputs/formal/calibration/stage_0_2_formal_risk_measurement_20261011_r2/`

其中 `p2_event_revalidation.csv` 保留每个事件成员行号哈希和实际 `event_confirm_s`；`p2_source_summary.csv` 与 `audit.json` 保存修正后的统计口径。

## 剩余状态

未发现剩余实现冲突。目标区域、固定目标车辆、评价窗口和消息去重仍是未批准参数，因此本轮不扩展正式区域 burden。历史 r1 产物保留不变，GitHub 自动 CI 仍停用。
