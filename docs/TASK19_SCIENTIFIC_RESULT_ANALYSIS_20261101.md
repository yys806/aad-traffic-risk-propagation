# AAD-S0.5-TASK19：Task9 正式实验科研结果分析

## 范围与数据

Task19 只读取 Task18 已完成的 100 组 Task9 结果：Primary 60 组、Supplementary 40 组，以及对应的 100 条完整内部轨迹和 0.1 s 测量轨迹。没有启动 SUMO、没有修改配置、没有新增 seed，也没有改变 Formal P2、D1、B witness 或 Stage 0.5 Gate。

每组结果均为 PASS；50 个 A/B 配对均通过实际轨迹审计。运动学闭合误差的最大绝对值约为 `2.84×10^-14 m`。所有 run 的输入、配置、轨迹哈希和来源标记均保留在分析数据集。

Task9 的正式运动学定义来自 `stage_0_5_fixed_leader_pair.py`：

- `C_initial = (v_f(0)-v_l(0))T`
- `C_f = ∫(v_f-v_f(0))dt`
- `C_l = -∫(v_l-v_l(0))dt`
- `C = C_initial + C_f + C_l = ∫(v_f-v_l)dt`
- `C_gap = gap(0)-gap(T)`
- `R = C_gap-C`

这些量存在代数依赖，不能被当作相互独立的效果证据。TTC 只在正闭合速度时计算；本批次每组均存在有限 TTC，但所有描述性最小值滞后均保持 `Unknown`，因为没有唯一可识别的极值。

## 主要观察

### 1. Follower 对固定 Leader 输入产生了稳定、可重复的动态响应

两条候选轨迹的速度曲线都表现为：初始阶段 Follower 速度下降，随后回升并超过初始速度，最后跟随 Leader 输入变化。Primary 中 Follower 描述性响应幅度范围为：

- `962-958-1`：约 4.22–4.59 m/s；
- `926-924-1`：约 4.22–6.20 m/s。

Supplementary 的范围分别约为 4.22–4.75 m/s 和 4.48–6.40 m/s。六组同 seed 复验的轨迹完全一致，五个不同 seed 在每个 candidate/tau/Arm 组合中都产生不同轨迹哈希。说明当前结果不是由执行器锁死或重复帧造成的，但 seed 数量仍然很小。

### 2. tau 的影响依赖候选输入，不能概括为单调“tau 越大响应越慢”

`962-958-1` 的响应幅度随 tau 总体缓慢增加。Primary Arm A 的五档均值约为 4.26、4.29、4.32、4.37、4.53 m/s；Arm B 约为 4.26、4.29、4.32、4.37、4.38 m/s。

`926-924-1` 呈现明显非单调结构：Primary Arm A 约为 4.64、4.52、4.42、4.83、6.18 m/s，Arm B 约为 4.64、4.52、4.42、4.62、5.97 m/s。最低响应出现在中间 tau，最高响应出现在 tau=2.5614676647。Supplementary 保持相同的非单调形状。

tau 增大时，两条候选的最终 gap 增量和描述性 TTC 最小值整体增大；这反映了本实验窗口中 gap 逐步打开、正闭合状态变少，不能直接解释为风险降低或驾驶反应变慢。

### 3. minGap 的 A/B 差异主要在高 tau 条件下显现

初始 gap 和最小 gap 在 A/B 间相同：`962-958-1` 约 10.253 m，`926-924-1` 约 4.859 m；这与配对初始状态审计一致。

Follower 响应幅度的 B−A 配对差异在 tau_index 0–2 基本为 0。高 tau 条件下出现负差异：

- `962-958-1`：Primary tau_index 4 约 −0.144 m/s，Supplementary 约 −0.221 m/s；
- `926-924-1`：tau_index 3 约 −0.215/−0.283 m/s，tau_index 4 约 −0.216/−0.247 m/s。

因此，较小 minGap 的 Arm B 在部分高 tau 条件下表现出较小的描述性响应幅度和较低的峰值减速度，但这一关系受候选 Leader 输入调节，不能外推为普遍 minGap 效应。

运动学分解中，A/B 的 `ΔC_initial=0`、`ΔC_l=0`，`ΔC_f≈+1.5 m`、`ΔC≈ΔC_gap≈+1.5 m`、`ΔR≈0`。这说明 A/B 差异高度受同一运动学闭合关系约束，不能把 `C_f`、`C` 和 `C_gap` 当成三个独立发现。

### 4. 候选差异明显，不能将绝对差异归因于 tau 或 minGap

`926-924-1` 初始 gap 约 4.859 m，通常具有更大的负向 Follower 速度变化、更大的 gap 打开量和更高的加速度绝对峰值；`962-958-1` 初始 gap 约 10.253 m，响应更平缓。两条候选的 Leader 速度输入、持续时间和初始状态均不同，因此候选间绝对响应差异同时包含输入轨迹和初始条件差异。

当前结果支持“候选交通输入调节局部响应”的描述性判断，但不能区分这一差异究竟来自初始 gap、Leader 速度形状还是二者交互。

### 5. Primary 与 Supplementary 方向总体一致，但不是数值复现

Supplementary 与 Primary 的响应幅度差异通常为数百分之一到数十分之一 m/s。两套数据都显示：

- `962-958-1` 的响应幅度随 tau 缓慢增加；
- `926-924-1` 在中间 tau 附近较低、最高 tau 明显回升；
- A/B 差异集中在高 tau 条件。

Primary 与 Supplementary 的差异说明 seed 噪声不是零，但五个 seed 仍不足以支持总体车辆群体推断。

## 统计边界

分析使用候选、tau、Arm 和来源分层的均值、标准差、中位数、范围、配对 B−A 差值和 seed 级结果。没有把 100 组结果当作 100 个独立车辆样本，也没有把同 seed 复验计入样本量。没有使用未经批准的显著性检验或模型拟合。

`follower_response_amplitude_mps`、TTC、最小 gap 和描述性 lag 都是当前协议下的描述性指标。它们不能直接被解释为传递增益、真实驾驶反应时间、Formal P2 或宏观风险效应。

## Observation / Interpretation / Hypothesis / Limitation

**Observation：** Follower 在固定 Leader 输入下出现可重复的速度、加速度、相对速度和 gap 动态；tau、minGap 和候选输入对这些描述性量的影响并不完全相同。

**Interpretation：** 局部响应由 Follower tau、minGap、Leader 输入形状和初始 gap 共同决定。高 tau 条件对候选输入更敏感，A/B 差异也主要在高 tau 下显现。

**Hypothesis：** 在更广泛的 Leader 扰动和初始状态范围内，tau 与 minGap 可能存在交互作用；当前 2 个候选和每组合 5 个 seed 只能提出该假设，不能验证其普遍性。

**Limitation：** MiTra 轨迹不是独立物理真值，gap 受参考点假设约束；直线 prototype 不等价于完整 B00 网络背景；实验没有通信消息链、控制器采用链或宏观区域风险；候选数量和 seed 数量有限。

## 结论边界

Task19 支持以下有限结论：Task9 执行器产生了真实、可重复、可配对的 SUMO 原生 Follower 响应；tau 的影响具有候选依赖，不能简化为单调规律；minGap 的描述性影响主要在高 tau 条件出现；Primary 与 Supplementary 对方向性模式总体一致。

Task19 不支持 AAD 核心远端消息因果假设、完整网络宏观风险等价性或真实交通物理传播规律已经成立。Stage 0.5 Gate、Scientific Equivalence 和后续阶段状态保持不变。
