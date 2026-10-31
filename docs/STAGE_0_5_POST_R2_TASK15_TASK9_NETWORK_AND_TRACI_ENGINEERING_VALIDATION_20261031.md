# AAD-S0.5-POST-R2-TASK15：Task9 完整轨迹网络适配、真实 TraCI 回放与实验输入协议预检

日期：2026-10-31。基线：`c8f2ff7693e907cf7bff024d75b85c9f95ae0289`。状态：`COMPLETED_WITH_NETWORK_DECISION_AND_TAU_BLOCKERS`。

本任务没有启动正式 Task9 A/B paired runs。所有 SUMO 回放均为 engineering-only，未计算 Follower 风险响应、Formal P2、D1 或 Task9 科研指标。

## 1. 网络几何和完整空间包络

### Fact

sealed B00 网络的 `main_0 → main_1 → main_2` 主线长度为 659.17 m。三个完整 MiTra leader 轨迹在 Task14 的局部坐标中分别需要约 751.84 m、874.57 m 和 818.02 m，且 follower 初始车身不能只通过延长下游解决。

Task15 构建了独立的 straight-line replay prototype：

- 1,000 m；
- 3 条车道；
- 3.2 m 车道宽度；
- 30 m/s 限速；
- 仅用于工程回放，不声称保持 B00 背景交通等价。

三个候选在该 prototype 中的完整车身包络均通过，未使用坐标循环、轨迹裁剪或隐式延长。sealed B00 网络仍保持未修改。

### Observation

| 候选 | prototype 空间覆盖 | sealed B00 空间覆盖 |
|---|---|---|
| 962-958-1 | PASS | FAIL_HORIZON |
| 926-924-1 | PASS | FAIL_HORIZON |
| 857-851-1 | PASS | FAIL_HORIZON |

prototype 的局部起始偏移为 40 m，用于给 follower 车身保留上游空间。该偏移是工程映射参数，不是地理坐标校准。

## 2. SUMO 1.26.0 与真实 TraCI

本机已发现 SUMO 1.26.0 executable。Python 环境未设置 `SUMO_HOME`，但通过匹配的官方安装目录 `C:\Program Files (x86)\Eclipse\Sumo\tools` 加载了 `traci` 和 `sumolib`，没有升级或修改系统安装。

新增 `stage_0_5_fixed_leader_traci.py`：

- 接收 0.05 s Leader trace；
- 关闭 replay vehicle 的 speed/lane-change 自动约束；
- 按 SUMO 时钟逐步执行；
- 使用 `moveTo` 控制位置，使用 `setSpeed` 控制下一积分区间速度；
- 记录时间、位置、速度 readback；
- 记录 teleport、collision 和 lane 状态。

实测控制语义显示：速度命令对应下一个 0.05 s 积分区间，位置在时钟步进后读取并校正。因此证据明确记录了一个 `0.05 s` 的 speed command phase lag；这不是科学反应时间估计。

## 3. 合成与实际 Leader 回放

### 合成 smoke test

使用非恒速、包含加速和减速的合成 Leader trace：

- 99 个控制步；
- 时间最大误差约 `7.1e-15 s`；
- 位置最大误差 `0 m`；
- 速度最大误差 `0 m/s`；
- teleport `0`；collision `0`。

### 三个实际 Leader trace

三个候选均在独立 prototype 中完成 engineering-only replay：

| 候选 | 控制步数 | 最大时间误差 | 最大位置误差 | 最大速度误差 | Teleport | Collision |
|---|---:|---:|---:|---:|---:|---:|
| 962-958-1 | 918 | 7.1e-15 s | 0 m | 0 m/s | 0 | 0 |
| 926-924-1 | 931 | 7.1e-15 s | 0 m | 0 m/s | 0 | 0 |
| 857-851-1 | 970 | 7.1e-15 s | 0 m | 0 m/s | 0 | 0 |

这证明真实 SUMO/TraCI 可以在独立 straight-line prototype 中逐步执行并回读 Leader trace；不证明原 B00 网络等价，也不证明 Follower 行为或 Task9 科研结论。

## 4. 车辆几何和初始状态

MiTra 与 B00 长度差异会改变近似初始净间距：

- `962-958-1`：若使用 B00 4.4196 m 车辆长度，初始近似 gap 比 MiTra 长度假设增加约 0.5804 m；
- `926-924-1`：同样增加约 0.5804 m；
- `857-851-1`：Car/Medium Vehicle 与 B00 passenger 长度差异带来约 0.9971 m 增量。

两种几何配置均未被正式选择。当前结果只说明车辆长度配置会实质影响初始 gap，必须由研究者在正式输入冻结前决定。

## 5. 重采样和位置—速度一致性

Task14 的线性 0.05 s 输入继续使用。Task15 追加了局部 leader position 的有限差分速度诊断：

- `962-958-1`：速度误差中位数约 0.053 m/s，95 分位约 0.168 m/s；
- `926-924-1`：中位数约 0.051 m/s，95 分位约 0.184 m/s；
- `857-851-1`：中位数约 0.055 m/s，95 分位约 0.180 m/s。

这些是局部映射和重采样诊断，不是原始物理观测误差估计。末端尾差仍为 0.0126/0.0300/0.0486 s，三种处理政策均保留为研究者决定，未进行外推或隐式裁剪。

## 6. A/B 输入公平性

Task15 为每个候选生成了独立加载的 Arm A/B 文件副本。三组副本的 SHA256 完全一致，且：

- leader position/speed 完全一致；
- 时间锚和网格完全一致；
- initial follower/leader speed 完全一致；
- initial approximate gap 完全一致；
- sealed arm audit 仍显示只有五个 passenger `minGap` 2.5→1.0 差异；
- 五档 tau 未改变。

该检查是输入公平性和工程配置验证，不是正式 A/B 运行结果。

## 7. tau 和 vType 决策材料

本任务没有根据 MiTra `Vehicle_type` 自动选择 tau。保留三种方案给研究者：

1. 保留现有 B00 异质 vType 分配，不从 MiTra 类别推断 tau；
2. 按 MiTra Vehicle_type 映射 B00 vType；
3. 将目标 tau 作为额外因素。

方案 1 最能保持现有 Task9 公平性和五档异质结构，但具体目标 Follower vType 仍需研究者确认。方案 2/3 会引入新的行为解释或实验矩阵。

## 8. 最终执行前状态

**Engineering validation：** 独立 prototype 网络、SUMO 1.26.0、真实 TraCI Leader 控制/readback、合成 smoke test 和三个候选 Leader replay 均通过。

**Candidate input readiness：** 三个候选具备可回放的工程输入；sealed B00 网络不能容纳完整轨迹，prototype 不等价于 B00 背景交通。

**Researcher decisions pending：** 网络结构/背景等价性、车辆长度配置、tau/vType 分配和末端尾差政策。

**Formal Task9 authorization：** 未获得；Task9 formal runs 保持 `0`。

Stage 0.5 继续 `blocked`，scientific equivalence 继续 `false`，Round3、Stage 0.6、Protocol Lock、Stage I 未启动。

机器证据：`evidence/results/RES-STAGE-0.5-POST-R2-TASK15-TASK9-NETWORK-TRACI-VALIDATION-20261031/`。
