# Stage 0.5-R1 三臂诊断实验执行与测量验收

任务 `AAD-S0.5-R1-EXECUTE-20261028` 已按研究者确认的 R0 设计执行。R0 的 B00 A03（`WEEK_0750_B00_IC1_s20261201_A03`）只作接受基线复用，没有重新启动。B10、B01、B11 各启动一次，均完成 420 s / 8400 个原生步，并通过独立工程回执和统一离线测量。

## Verified

- 固定场景 `US-101 0750`、seed `20261201`、内部步长 `0.05 s`、记录步长 `0.1 s`、评价窗 `[120,390)`；源区为 `S_UPSTREAM_MAIN`，目标区为主线车道 1–5、映射纵向 `[150,350)` m，主 cohort 为 R0 精确 `C_INPUT_ROUTE`。
- 三臂均使用 SUMO 1.26.0 / TraCI 22 原生 capsule。每臂 `SUMO exit=0`，FCD 覆盖 4200 个记录时刻，summary/tripinfo/identity journal/资源采样完整；独立 `verify_receipt` 对身份重放、逐步 summary 对账、碰撞/teleport、只读输入、隔离和资源约束均为 Pass。
- B10 的五条 `main_2_0..4` 在 t=180 s 读回 5 m/s、t=240 s 读回 10 m/s；8400 条控制记录的时钟、目标值和 lane readback 全部通过。B01 的 60 辆非初态匝道车辆保留原 ID、车型、路线和 7 个原始块计数 `9/8/9/8/9/9/8`；候选 depart 按冻结映射生成，实际插入另行记录。B11 只组合 B10+B01。
- R1 主 cohort 三臂均为 1112 辆（79 初态、1033 非初态），精确 ID 哈希 `76db89e2ff2d9df997516b59a23bc4d88a85c7a0161dca6a222f2a8bfee277f8`。

## Observation

| arm | 启动/有效 | 完整时长 | 声明/实际插入/末态 pending | 目标 D1 暴露 (veh-s) | 源 P2 | 目标 P2 |
|---|---:|---:|---:|---:|---:|---:|
| B00 A03（复用） | 0 / 1 | 420 s | 1150 / 1005 / 145 | 9778.4 | 0 | 0 |
| B10 | 1 / 1 | 420 s | 1150 / 955 / 195 | 13667.8 | 0 | 0 |
| B01 | 1 / 1 | 420 s | 1150 / 1009 / 141 | 9865.1 | 0 | 0 |
| B11 | 1 / 1 | 420 s | 1150 / 956 / 194 | 13553.6 | 0 | 0 |

三臂 discarded、碰撞和 teleport 均为 0；`active_native` 分别为 B10 168、B01 155、B11 173。60 辆匝道车实际均有插入：B10 平均插入延迟 0 s，B01 2.9708 s，B11 3.0833 s；这些是完整系统响应，未用成功插入百分比替代全体生命周期。

B10 目标区速度均值 6.7594 m/s、低于 5 m/s 的状态份额 0.4586；B01 为 10.2777 m/s、0.0608；B11 为 6.7875 m/s、0.4375。它们记录交通状态差异，但不能单独推出效应或机制成立。

## Interpretation

三臂均没有在完整轨迹中得到满足正式 TTC、连续性、身份和观测质量要求的源区 P2 事件。B10 的速度脉冲确实执行并改变了目标区交通状态；B01 的匝道供给确实按候选 depart 产生实际插入；B11 的组合操纵也确实执行。工程执行、操纵回读、交通状态变化、正式源事件和物理影响路径保持分层记录。

## Blocked

- `source_event_support.json` 的统一审查结果为 `NO_QUALIFIED_SOURCE_EVENT_SUPPORT`：B10、B01、B11 的源 P2 均为 0。按任务书停止规则，不换 seed、不增加强度、不追加 SUMO 运行。
- 没有源事件，因此没有生成事件特定的物理到达时间。`physical_path_audit.json` 将状态保留为 `uncertain_or_unobservable`；缺失路径支持没有被转成不可达。
- Stage 0.5 科学 Gate 继续 `blocked`。Stage 0.6 仍为 `pending_scientific_tolerances_and_dynamic_calibration`，Stage I 仍为 `blocked_until_protocol_lock`；本轮没有生成 Protocol Lock、没有读取 locked holdout。
- 历史 M3 交互不相容证据保持原状；本轮诊断没有消除结构性状态/交互支持限制。

## Proposal

下一步需要研究者基于 `r2_gate_review.json` 决定是否另行设计能产生可观测源事件的诊断任务。该决定不属于本轮自动追加范围。

输入、proposal、policy、envelope、独立回执和测量索引见 `evidence/results/RES-STAGE-0.5-R1-DIAGNOSTICS-20261028/`；完整原始输出和 parquet 状态表保存在 `code/outputs/formal/calibration/stage_0_5_r1_diagnostics_20261028/`，由便携 manifest 和 SHA256SUMS 绑定。
