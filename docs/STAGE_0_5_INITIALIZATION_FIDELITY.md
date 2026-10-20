# Stage 0.5 初始状态保真度：两条受验证的初始化路线与一处结论更正

日期：2026-10-20。任务 `AAD-0.5-METHOD-EXPANSION`（第三阶段）。结果 `RES-STAGE-0.5-METHOD-EXPANSION-V1`。

---

## 1. 结论更正（Conflict Record，必须先读）

| 项 | 内容 |
|---|---|
| **Documented Intent** | `docs/STAGE_0_5_LEADER_REPLAY_BEHAVIOUR_DIAGNOSTICS.md` §3 称：48 个「对 × 配置」组合中有 26 个（44%）**被 SUMO 的 Krauss 插入安全包络拒绝**，并把它当作「模型无法表示真实状态」的证据 |
| **Actual Implementation** | SUMO 的插入失败**不是永久拒绝**：`MSLane::isInsertionSuccess()` 失败时车辆保持等待，SUMO 在后续步**重试**插入；该对最终会被插入，只是**晚于**声明的出发时刻。旧重放实现只等待 5 步（0.25 s）就中止并把结果记为 `insertion_failed` |
| **Evidence** | 直接探针：同一对（观测净间距 15.170 m、观测速度 12.503 m/s、`tau=1.0`）在默认检查下于 **t = 0.45 s** 被插入，位置/速度与观测一致；加 `--insertion-checks none` 后于 **t = 0.05 s** 插入。`init_routes.csv` 中 12 对的原生延迟为 0.05–0.70 s（中位 ≈0.45 s） |
| **Affected Files** | `code/src/riskprop/stage_0_5_leader_replay.py`（等待逻辑与对齐）、`docs/STAGE_0_5_LEADER_REPLAY_BEHAVIOUR_DIAGNOSTICS.md` §3、`AI_CONTEXT/07_KNOWN_ISSUES.md` |
| **Conflict** | 旧报告的「44% 被拒绝」是**实现缺陷造成的误判**，不是 SUMO 行为；「观测初始状态在模型安全包络之外」这一**更弱的**陈述仍然成立（见 §4） |
| **Status** | 已更正并保留证据；旧报告正文不追溯改写，更正登记在此与 AI_CONTEXT |

**影响**：上一任务的配对结论（`tau=1.6` 恶化 +19.57 pp）建立在被截断的样本上（拥堵窗口的对大多被旧实现的等待窗排除）。本任务用修正后的实现对**修正样本**重做（`docs/STAGE_0_5_METHOD_EXPANSION_RESULTS.md`），结论方向不变且更强。

---

## 2. 初始化链路审计（Observation，基于 SUMO 1.26 源码）

用具名源码核对（`code/outputs/formal/calibration/stage_0_5_final_candidate_v1/official_source/`，SHA 已在最终收口任务登记）：

| 问题 | 事实 | 位置 |
|---|---|---|
| 插入检查在哪里执行 | `MSLane::isInsertionSuccess()`；失败分支为 `InsertionCheck::LEADER_GAP`，判据来自 `safeInsertionSpeed()` 与 `checkFailure()` | `src_microsim_MSLane.cpp` L850 起 |
| 检查是否可关 | 可。`MSBaseVehicle::getInsertionChecks()` 读车辆/车型参数 `insertionChecks`，否则读全局 `--insertion-checks` | `microsim_MSBaseVehicle.cpp` L1198–1205 |
| 位置/速度如何进入 | `departPos`/`departSpeed` → `setTentativeLaneAndPosition()` → 首个决策步 | `src_microsim_MSLane.cpp` L871–873 |
| 哪些 API 会持续覆盖动力学 | `libsumo::Vehicle::setSpeed(v>=0)` 写入**直到 `SUMOTime_MAX`** 的速度时间线；要释放必须 `setSpeed(-1)` | `libsumo_Vehicle.cpp` L1907–1921 |
| 本实现是否残留外部控制 | **否**：重放从不对后车调用 `setSpeed`；只对前车调用（这正是被驱动对象） | `stage_0_5_leader_replay.replay_pair` |
| 随机状态 | 每个 SUMO 进程独立 seed；同一 seed 集跨配置复用，使配置差异不与被 seed 差异混淆 | `response_plan.json` |

**Observation**：**初始化不会改变被研究的过程**——后车在插入后完全由跟驰模型驱动，无速度覆盖、无位置覆盖、无停靠设备。因此局部/长期响应误差可以公平地归因于模型，而不是初始化。

---

## 3. 两条初始化路线与保真度（Observation）

| 路线 | 含义 | 是否原生 | 插入时刻 | 首步变化 | 控制状态 |
|---|---|---|---|---|---|
| `native` | 默认插入检查；被阻塞时**等待并记录延迟**，把观测序列按后车自身经过的时间对齐 | 是（默认） | 观测时刻 + 0.05–0.70 s（中位 ≈0.45 s） | 无（位置与速度即观测值） | 纯模型 |
| `none` | 文档化选项 `--insertion-checks none`（vType 属性 `insertionChecks`）**只跳过插入时刻的安全检查** | 是（官方选项） | 观测时刻（首步 0.05 s） | 无 | 纯模型 |

**控制实验（关键）**：对**原生即可立即插入**的车辆对，两条路线给出**逐字节相同**的轨迹（`init_routes.csv` 中 `identical_trajectory=true`，例如 run 26903 两条路线 Brockfeld 误差均为 5.95%）。这证明 `insertion-checks=none` **只影响插入判定，不影响后续动力学**，可以作为"精确初始状态"的合法通道，而不是伪造。

12 对 × 2 路线 = 24 次微型运行全部完成，无失败。前车跟随偏差 ≤ 0.25 m 容差（实测 0.013–0.112 m）。

---

## 4. 仍然成立的部分结论（Observation）

即使更正了「拒绝」的措辞，下面这件事仍然成立且有独立意义：

**观测到的初始跟驰状态常常落在冻结 Krauss 的插入安全包络之外。** 例：

| 观测净间距 [m] | 观测速度 [m/s] | `tau=1.0` 允许的最大插入速度 [m/s] | `tau=1.6` |
|---:|---:|---:|---:|
| 15.17 | 12.50 | 11.64 | 9.89 |
| 10.65 | 11.36 | 10.31 | 8.90 |
| 3.38 | 4.19 | 3.96 | 2.96 |

即：在这些车速与间距组合下，**冻结模型自己的安全假设不允许"以观测速度、在观测间距处"跟随**。这仍然是行为模型与真实跟驰状态不匹配的量化形式，只是它现在由**延迟量**而不是"拒绝"来表达。

---

## 5. 结论与对后续的影响

- **Observation**：初始化链路已被源码级核对；两条原生路线都通过保真度与控制链核验（`Exact` 级：位置与速度等于观测值，无残留覆盖）。
- **Observation**：默认路线会引入 0.05–0.70 s 的插入延迟；本任务把该延迟**记录下来并对齐观测序列**，不再当作失败。
- **Derived**：`insertion-checks=none` 是可控的、只影响插入的通道，已在控制实验中被证明不改变后续动力学。
- **Interpretation**：插入延迟的分布本身就是「模型安全包络 vs 真实跟驰状态」的差距分布；它是本任务使用 `none` 路线做响应诊断的前提。
- **Proposal**：正式协议若采用本框架，应在冻结计划中声明使用哪条路线，并报告延迟分布；不得在插入被延迟后夹取速度再把结果混入原始状态结果。
