# AAD-S0.5-ROUND2-TASK5：Task 4 离线证据完整性审计与闭环

任务编号：`AAD-S0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-CLOSURE-20261030`
基线：`6ca87be8a12301a6acb943250164af83eabf0290`
状态：`Verified offline integrity closure`

本任务只审计并修复 Task 4 的三个工程问题：两个授权 NGSIM 窗口的跨窗口重叠、Formal P2 onset 归属唯一性，以及真实数据不完整 30 s 时间块的统计分母。Task 4 历史报告和证据包未被覆盖。没有启动 SUMO/TraCI，没有生成新轨迹，没有读取第三窗口或 locked holdout，也没有改变 Formal P2、D1、source/target、cohort、评价窗、Rule A 或 Gate。

## Observation：跨窗口重叠

两个窗口的 `Global_Time` 范围为：

| 窗口 | Global_Time 范围 | 行数 | 原始 vehicle ID 数 |
|---|---:|---:|---:|
| 0750–0805 | 1118846979700–1118847932500 | 1180598 | 2169 |
| 0805–0820 | 1118847843000–1118848842000 | 1403095 | 2017 |

时间戳区间重叠 `[1118847843000, 1118847932500]`，持续 `89.5 s`，共有 896 个共同 `Global_Time` 值；重叠区间内两窗口分别有 81680 和 47715 行观测。

进一步使用 `(original_vehicle_id, Global_Time, Frame_ID)` 作为原始观测键：

- 精确记录交集：`0`；
- 两个窗口各自重复键行：`0/0`；
- trajectory ID 精确交集：`0`；
- Formal P2 onset 原始观测键交集：`0`；
- 重复事件数：`0`。

两个窗口共享 1430 个 `original_vehicle_id`，但来源成员、trajectory ID 和时钟段不同。共享 ID 不能证明是同一物理车辆或同一 trajectory 的跨窗口延续，因此身份对应仍为 `Unknown`。时间戳重叠本身不构成记录或事件重复证据，两个窗口不得合并成一个独立事件总量。

审计结果见 `window_overlap_audit.json`。

## Observation：Formal P2 onset 归属

新的 `attribute_event_onsets()` 对每个事件用 `(trajectory_id, event_start_s)` 精确匹配状态记录，并将匹配结果分为 `unique`、`unmatched`、`ambiguous`。`unmatched` 和 `ambiguous` 进入 `unknown`，不会再被放入 `auxiliary_or_other`。

| 数据 | extracted | unique | unmatched | ambiguous | source | target | other_mainline | auxiliary_or_other | unknown |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| NGSIM 0750–0805 | 543 | 543 | 0 | 0 | 167 | 174 | 189 | 13 | 0 |
| NGSIM 0805–0820 | 732 | 732 | 0 | 0 | 159 | 252 | 311 | 10 | 0 |
| SUMO B00 formal-aligned | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| SUMO Round2 formal-aligned | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |

所有行满足：

`source + target + other_mainline + auxiliary_or_other + unknown = extracted_events`

因此 onset 数量守恒和空间归属审计通过。SUMO formal-aligned 与 D1 仍分别标记，Task 5 没有改变其 pending equivalence 状态。

审计结果见 `event_onset_attribution_audit.json`。

## Observation：不完整 30 s 时间块

`block_rows()` 现在保留固定 30 s nominal block，但用实际观测支持计算：

`effective_start = max(nominal_start, actual_observation_start)`
`effective_end = min(nominal_end, actual_observation_end)`
`effective_duration = effective_end - effective_start`

修正后的 NGSIM 末尾块为：

| 窗口 | nominal block | 修正后实际区间 | 有效时长 |
|---|---|---|---:|
| 0750–0805 | [930,960) s | [930,952.9) s | 22.9 s |
| 0805–0820 | [990,1020) s | [990,999.1) s | 9.1 s |

SUMO `[120,390) s` 的完整 30 s blocks 没有变化。与 Task 4 原统计逐块对照显示：state rows、速度、低速比例、间距和闭合速度保持不变；仅一个有观测的 NGSIM `0750_0805 / target_1 / block 31` 发生密度和流量分母修正：

- density：`0.140000 → 0.183406 veh/km/lane`；
- flow：`5.230807 → 6.852585 veh/h/lane`；
- 有效时长：`22.9 s`。

修正统计和差异表见：

- `corrected_real_source_target_state_metrics.csv`
- `corrected_simulation_source_target_metrics.csv`
- `time_block_statistics_diff.csv`

## Interpretation：对 Task 4 原结论的影响

Task 4 的两个全来源 Formal P2 复现值仍保持：

- 0750–0805：543 事件，111425.9 s P2 可评价暴露；
- 0805–0820：732 事件，133505.6 s P2 可评价暴露。

固定 source/target 事件数仍为 source `167/159`、target `174/252`。跨窗口审计没有发现可证明的重复原始记录或重复事件；因此 Task 4 的两个窗口仍应保持独立统计。onset 审计没有 unmatched/ambiguous，原有空间归属完整闭合。时间块修正只影响描述性末尾 block 的密度/流量，不改变风险事件、暴露分母或 Task 4 的科学解释边界。

## Unresolved

1. 两窗口共享 1430 个原始 vehicle ID，但缺乏跨窗口身份协议；不能据此证明物理车辆延续，也不能进行合并统计。
2. 时间戳重叠区间中的真实交通过程是否有更高层次的采集语义联系，当前输入无法确认。
3. SUMO formal-aligned 与 NGSIM Formal P2 的科学等价、物理传播和 Model Discrepancy 仍未确认。

这些未决事项不阻断本任务的工程完整性闭环，也不改变 Stage 0.5 Gate、Stage 0.6、Protocol Lock 或 Stage I 状态。

## 验证

Task 5 机器证据包：`evidence/results/RES-STAGE-0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-20261030/`。`validation_record.json` 状态为 `PASS_OFFLINE_TASK5`：输入 SHA、Task 4 历史 SHA256、事件守恒、source/target 数量保持和有效末尾 block 时长均通过；native launches、TraCI connections、locked holdout reads 均为 0。Task 4 历史证据包 SHA256 未被修改。
