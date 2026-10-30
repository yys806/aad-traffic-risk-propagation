# AAD-S0.5-ROUND2-TASK4：真实源区支持与宏观—微观—风险多尺度对照

任务编号：`AAD-S0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030`
日期：2026-10-30
状态：`Verified offline evidence / researcher decision pending`

本任务回答固定源区 `mainline lanes 1–5, y∈[0,150) m` 在真实 US-101 轨迹中是否有按照 Stage 0.2 Formal P2 规则可观测的风险支持，并把真实交通与已封存 B00、Round2 candidate 做描述性多尺度对照。任务没有启动 SUMO/TraCI，没有生成新轨迹，没有读取第三真实窗口或 locked holdout，也没有改变 P2、D1、Rule A、cohort、评价窗口或 Gate。

## 研究范围和输入

真实数据只读取两个 Stage 0.2 canonical Parquet：

| 窗口 | 文件 SHA256 | 全来源 Formal P2 | 全来源 P2 可评价暴露 |
|---|---|---:|---:|
| 0750–0805 | `684a5f0b96dc48116f16d581c278d7039c0554bf1c3cea8d6eda3e605e3e8644` | 543 | 111425.9 s |
| 0805–0820 | `7b0ef830c97a981da018d4e24b029e38aa2630387c728ea87b57926745880a9f` | 732 | 133505.6 s |

仿真只复用两个封存运行：

| 运行 | FCD SHA256 | measured_state SHA256 |
|---|---|---|
| B00 `WEEK_0750_B00_IC1_s20261201_A03` | `1dc274082f4ea14949979d0c925903bbb5b9668d1124dabb79799b59a55fa304` | `48b20ff458ff1dce4559a762d6965b6747a940d537b1460d74e33d739a3cf63a` |
| Round2 `AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1` | `434f1c2500cdf06d069d7eae1c86e064ad76af61f478379943bbefab70b2ac3e` | `31426640954e6e8ea883f82dce139df130d7f83a8db4300ceb38842d4ee716b8` |

复现脚本为 [`analyze_stage_0_5_round2_task4_real_source_support.py`](../code/scripts/analyze_stage_0_5_round2_task4_real_source_support.py)。它只读既有文件，不启动子进程，不调用 SUMO/TraCI，不联网。机器证据包位于 [`RES-STAGE-0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030`](../evidence/results/RES-STAGE-0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030/)。

## 真实 Formal P2 重现和空间归属

脚本先在完整轨迹上下文中用现有 Formal P2 提取器重现全来源结果，再按 event onset 的 follower 位置归属空间。阈值保持 `0<TTC<2 s`、持续时间至少 `0.2 s`、相邻观测间隔不超过 `0.11 s`、采样周期 `0.1 s`；身份、帧、时钟和观测缺口全部 fail-closed。事件离开区域后不改写 onset 归属。

| 窗口 | 全来源事件 | 全来源 P2 可评价暴露 | 源区事件 | 源区可靠跟驰暴露 | 源区 P2 可评价暴露 | 源区不可评价暴露 | 源区描述性率（veh⁻¹h⁻¹） | 目标区事件 | 目标区 P2 可评价暴露 | 目标区描述性率（veh⁻¹h⁻¹） |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0750–0805 | 543 | 111425.9 s | 167 | 30550.3 s | 30519.4 s | 30.9 s | 19.699 | 174 | 39065.8 s | 16.034 |
| 0805–0820 | 732 | 133505.6 s | 159 | 30595.1 s | 30560.7 s | 34.4 s | 18.730 | 252 | 43522.0 s | 20.845 |

全来源复现均通过：事件数为 `543/732`，P2 可评价暴露为 `111425.9/133505.6 s`。空间归属唯一且无重复计数；0750–0805 的 source/target/other-mainline/auxiliary-or-other 事件数为 `167/174/189/13`，0805–0820 为 `159/252/311/10`。源区不可评价暴露占可靠暴露约 `0.10%/0.11%`，不能解释为零风险；未观测部分仍保持 Unknown。

事件严重程度也有真实源区支持。源区事件的 TTC 最小值中位数为 `1.387/1.325 s`，最小值为 `0.00163/0.00344 s`；事件持续时间中位数为 `0.6/0.7 s`，最大为 `2.5/3.2 s`。这些量来自事件成员，不是 D1 same-native-lane 分母。

## 仿真风险结果和测量契约分离

下表来自封存 measured_state 的离线重算。`SUMO_formal_aligned_P2_diagnostic` 使用现有 formal-alignment adapter，`SUMO_D1_diagnostic` 使用既有 D1 局部测量。两者都明确标记 `formal_equivalence_accepted=false`；它们不能与 NGSIM Formal P2 直接合并成一个科学事件体系。

| 运行 | 区域 | Formal-aligned P2 事件 / 可评价暴露 | D1 事件 / 可评价暴露 | D1 率（veh⁻¹h⁻¹） |
|---|---|---:|---:|---:|
| B00 | 源区 | 0 / 8454.4 s | 0 / 8457.4 s | 0 |
| B00 | 目标区 | 0 / 9774.5 s | 0 / 9778.4 s | 0 |
| Round2 | 源区 | 0 / 8896.7 s | 0 / 8900.0 s | 0 |
| Round2 | 目标区 | 1 / 10568.6 s | 1 / 10572.4 s | 0.341 / 0.341 |

Round2 的唯一目标区事件仍为既有 `m00485/r00036`，onset `271.8 s`、结束 `272.1 s`，不被追溯解释为源区事件，也不被道路拓扑解释为物理传播见证。D1 same-native-lane 暴露（如 `8457.4/8900.0 s`）只作为独立诊断列示，未替代 NGSIM Formal P2 分母。

## 宏观状态对照

真实窗口按各自 `time_s` 全范围统计，仿真按封存评价窗 `[120,390) s` 统计；两者还分别输出 30 s 时间块和 100 m 子区块。以下是源区聚合描述，指标来自同一研究坐标和 lanes 1–5 过滤，但时间范围与车辆总体不同。

| 数据 | 速度均值 m/s | 速度 SD | 密度 veh/km/lane | `v<5` 比例 | 净间距中位数 m | 闭合速度均值 m/s |
|---|---:|---:|---:|---:|---:|---:|
| NGSIM 0750–0805 | 9.182 | 3.455 | 43.156 | 14.72% | 13.899 | -0.174 |
| NGSIM 0805–0820 | 7.832 | 3.303 | 41.296 | 21.01% | 12.494 | -0.135 |
| B00 `[120,390)` | 8.307 | 4.252 | 42.585 | 24.09% | 15.450 | -1.358 |
| Round2 `[120,390)` | 8.327 | 4.698 | 44.967 | 31.69% | 13.520 | -1.520 |

目标区也有可见差异：真实 0750–0805 / 0805–0820 的速度均值为 `10.298/8.571 m/s`、低速比例 `11.78%/20.32%`；B00/Round2 目标 cohort 的速度均值为 `10.465/10.333 m/s`、低速比例 `4.32%/6.62%`。这些是描述性状态差异，不能在未完成时间/cohort 对齐时解释为参数造成的因果变化。

## 微观状态和可观测性

真实源区有效 TTC 的最小值为 `0.00163/0.00344 s`，中位数为 `16.557/18.345 s`；B00/Round2 源区有效 TTC 最小值为 `2.1579/2.6732 s`，中位数为 `35.865/26.819 s`。真实源区因此不仅有更多风险事件，风险尾部也明显进入 `TTC<2 s`。

源区状态组成如下：

| 数据 | valid | not_applicable | invalid | missing |
|---|---:|---:|---:|---:|
| NGSIM 0750–0805 | 137160 | 170397 | 310 | 555 |
| NGSIM 0805–0820 | 138523 | 169264 | 346 | 1305 |
| B00 | 27375 | 57798 | 0 | 1061 |
| Round2 | 24273 | 65376 | 0 | 1409 |

真实源区的 acceleration 均值为 `0.023/0.044 m/s²`，B00/Round2 为 `0.626/0.720 m/s²`；closing speed 的仿真均值约 `-1.36/-1.52 m/s`，真实源区约 `-0.17/-0.13 m/s`。这说明封存仿真源区的跟驰交互状态和真实源区分布存在明显描述性差异，但不能单独区分行为模型、测量契约、时间范围或 population scope 的贡献。

全部聚合值、分位数、状态组成和 30 s block 输出见 `real_source_target_state_metrics.csv` 与 `simulation_source_target_metrics.csv`。

## 时间、空间和 cohort 可比性审计

- NGSIM `time_s` 在两个来源窗口内都从 `0.0 s` 起，最大值分别为 `952.8 s` 和 `999.0 s`；`Global_Time` 也分别保留在独立来源时钟中。
- SUMO measured state 使用绝对仿真时钟，研究评价窗为 `[120,390) s`。当前 provenance、初始排班和封存状态不足以证明两个时钟原点逐时相同。
- 因此本任务没有人为时间偏移、没有逐时间块匹配，也没有把真实 30 s block 和仿真 30 s block 当作同一时刻。
- `C_INPUT_ROUTE` 通过既有 `route_inventory` 的 main_0/main_1 规则得到 1112 个预定义 ID；真实窗口分别有 2169/2017 个 trajectory IDs。真实车辆和 SUMO cohort 没有一一对应关系。
- 事件只按各自 full-context onset 归属；没有从目标区事件反推源区传播，也没有按拓扑可达性构造物理路径。

## Observation / Interpretation / Hypothesis

**Observation（已验证）**

1. 两个真实窗口的全来源 Formal P2 和全来源 P2 可评价暴露精确复现。
2. 固定真实源区存在 `167/159` 个 Formal P2 事件和 `30519.4/30560.7 s` 的 P2 可评价暴露。
3. B00 与 Round2 的封存 source formal-aligned/D1 均为 0；Round2 有一个目标区事件。
4. 真实与仿真在速度、低速比例、净间距、闭合速度、有效 TTC 尾部和状态组成上存在描述性差异。
5. 时间原点未证明一致，cohort 不同，SUMO Formal-aligned 与 D1 仍未接受科学等价。

**Interpretation（现有证据支持的解释）**

在这两个真实窗口的可靠可评价源区支持中，固定源区不是“没有可见 Formal P2”的情况；它有正的事件支持。因而 B00 和 Round2 没有源区事件，表示当前封存仿真尚未复现这些真实源区风险支持。由于时间、population 和测量等价性仍未闭合，当前证据不能把差异归因于单一驾驶参数，也不能直接宣布 Model Discrepancy 或 simulator-vs-NGSIM 科学不等价已成立。

**Hypothesis（仍待研究者决定）**

行为模型差异、仿真—真实 population/time scope 差异以及 SUMO formal adapter 与 NGSIM 测量契约差异都可能贡献观察到的风险缺口。历史 324 次微观实验和现有 Round2 只说明候选 minGap 改变了仿真微观尾部、但没有形成源区 P2；它们没有提供足够证据单独解释真实源区的正事件支持。

## 科研决策矩阵

| 核心问题 | 当前证据 | 状态/边界 |
|---|---|---|
| 真实源区是否有 P2 | 167/159 事件；正的 30519.4/30560.7 s P2 可评价暴露 | `Verified`; 情况 A |
| 真实源区支持是否不足 | 不可评价仅 30.9/34.4 s，仍需保留 Unknown | `Verified support`; 不是无风险证明 |
| 仿真是否产生源区 P2 | B00/Round2 formal-aligned 和 D1 均 0 | `Verified sealed result` |
| 宏观差异 | 速度、低速比例、密度、30 s blocks 有差异 | 描述性；未做逐时对齐 |
| 微观差异 | 真实源区 TTC 尾部进入 `<2 s`，仿真源区最小 TTC 为 2.158/2.673 s | 描述性；契约尚未等价 |
| 风险差异 | 真实源区正事件，仿真源区零；Round2 目标区 1 个事件 | D1/Formal-aligned 分开列示 |
| 时间对齐 | 无可验证的精确 time-origin mapping | `Unverified` |
| cohort 差异 | 真实 2169/2017 trajectory IDs；SUMO `C_INPUT_ROUTE=1112` | `Verified scope difference` |
| 物理传播 | 没有独立时间化路径与交互见证 | `Unknown`; 不由拓扑推断 |

当前最合理的下一步是由研究者决定是否继续使用固定源区估计对象，并先裁决 simulator formal equivalence / physical-path 事项。现有真实证据支持一次针对测量契约、时间范围和 population scope 的研究者审查；它不支持自动选择新的 `minGap/tau/IDM/Krauss` 参数，也不自动启动 Round 3、Stage 0.6、Protocol Lock 或 Stage I。

## 未解决问题及影响边界

1. 时间原点没有证明逐时一致，因此真实与仿真 block 不能作逐时因果对应。
2. 真实车辆与 SUMO cohort 不同，无法构造车辆级对应。
3. SUMO Formal-aligned P2 的工程输出仍是 `pending_measurement_equivalence_review`，不能替代 NGSIM Formal P2。
4. 没有独立物理路径见证，目标区事件不能解释为源区风险传播。
5. 本任务没有新增科学验收阈值，也没有把描述性率升级为 Stage 0.2/Stage 0.5 Gate 标准。

## 工程验收

机器验证 `PASS_OFFLINE_EVIDENCE`：输入 SHA 全部通过；全来源事件数与暴露复现通过；空间归属唯一；`native_launches=0`、`traci_connections=0`、`locked_holdout_reads=0`；证据包 manifest 与 `SHA256SUMS` 独立校验通过。Stage 0.5 Gate、Stage 0.6、Protocol Lock、Stage I 和 Round2 后续任务状态均未改变。
