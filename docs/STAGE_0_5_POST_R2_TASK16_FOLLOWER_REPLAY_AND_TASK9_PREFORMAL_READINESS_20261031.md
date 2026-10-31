# AAD-S0.5-POST-R2-TASK16：固定前车—跟驰车辆联合回放与 Task9 前置验收

日期：2026-10-31。基线：Task15 `8446e75960a7e2b1ffff73b5caa0904a5d39af7e`。本报告只记录工程验证和正式实验前置条件，不启动 Task9 正式 A/B 运行。

## 1. 范围与状态

Task16 复用 Task14 的三个 MiTra T1 输入和 Task15 的独立 1,000 m、3 车道 SUMO prototype，新增原生 SUMO follower 的联合回放、初始化时序诊断、60 组工程矩阵、Leader 控制校正量统计和执行链条预检。Minimum Sufficient Authenticity 继续是已 Agreed 的 Task9 输入适用性原则；它不改变 Formal P2、D1、B witness、Scientific Equivalence 或 Stage 0.5 Gate。

所有回放均为 engineering-only。Task9 formal runs = `0`；Stage 0.5 = `blocked`；scientific equivalence = `false`；Round3、Stage 0.6、Protocol Lock 和 Stage I 均未启动。

## 2. 网络和输入适用性

sealed B00 主线 `main_0 → main_1 → main_2` 总长度为 659.17 m，三个完整 Leader 位移约为 751.84 m、874.57 m 和 818.02 m，因此不能容纳完整候选。Task15 的独立 prototype 为 1,000 m、3 条 3.2 m 车道、30 m/s 限速；它容纳三个候选的完整空间包络，并未修改 sealed B00，也没有声称背景交通等价。

该 prototype 适合验证局部 Leader–Follower 控制链和输入映射。它不能单独证明完整 B00 网络背景、匝道交互或人群构成等价。是否将其用于正式受控局部实验仍由研究者决定。

## 3. Leader 控制时序

当前适配器保留 Task15 的控制方式：在每一积分区间前用上一采样点速度 `setSpeed`，执行 `simulationStep`，再用当前目标位置 `moveTo` 校正并读取状态。因而位置回读误差为零是位置校正后的结果，速度回读误差为零是相对于控制命令的结果；速度命令相对于输入当前样本存在 0.05 s 相位。

三候选的 `moveTo` 校正量（见 `control_timing_diagnostics.json`）如下：

| 候选 | 校正 MAE (m) | P50 abs (m) | P95 abs (m) | 最大 abs (m) | 累积 abs (m) |
|---|---:|---:|---:|---:|---:|
| 962-958-1 | 0.00411 | 0.00265 | 0.00806 | 0.76994 | 3.77173 |
| 926-924-1 | 0.00454 | 0.00245 | 0.00939 | 0.88463 | 4.22317 |
| 857-851-1 | 0.00377 | 0.00264 | 0.00863 | 0.37540 | 3.65915 |

离线对照中，位置差分速度与当前观测速度的 P50/P95 误差分别约为 0.053/0.168、0.051/0.184 和 0.055/0.180 m/s；当前样本速度方案只作为相位对照，没有替换正式适配器。以上是控制方式诊断，不是自然 SUMO 轨迹真实性或反应时间估计。

## 4. Leader–Follower 联合回放

新增 `stage_0_5_fixed_leader_follower_traci.py` 和矩阵脚本 `run_stage_0_5_task16_joint_replay.py`。Leader 由外部轨迹控制；Follower 仅由 SUMO 原生跟驰模型运行，未逐步 `moveTo` Follower。每步记录 Leader/Follower 位置、速度、Follower 加速度、净间距、闭合速度、车道、teleport 和 collision。

矩阵为 3 候选 × 2 几何（MiTra 与 B00）× 5 个原有 tau × 2 个 minGap 臂，共 60 次 engineering-only replay。60/60 返回 `PASS_JOINT_ENGINEERING`，总 teleport 行数为 0、collision 行数为 0，所有评估行净间距为正，且正式运行计数为 0。该结果只证明当前 prototype 上控制链可执行，不构成 A/B 风险效应或 Formal P2/D1 结果。

### 初始化时序发现

直接同时以目标初始位置插入时，962 可以通过；926 和 857 因 SUMO 插入安全间距约束无法保留 Follower（现已 fail-closed 记录为 `DIRECT_INSERTION_FAILED`）。工程矩阵采用 `safe_then_move`：先在足够上游位置安全插入，再执行一次性 `moveTo` 到候选初始位置，之后每个时间步只控制 Leader，Follower 由原生模型推进。初始观测速度在插入前设置并与候选输入一致；初始净间距在一次性放置后保持。该初始化动作不是正式科学输入政策，正式实验前仍需研究者审查。

## 5. 几何、tau 和配对公平性

MiTra Car/Medium Vehicle 长度为 5.0/5.8333 m，sealed B00 passenger 长度为 4.4196 m。由同一参考点位置计算时，B00 几何相对 MiTra 几何使初始近似 gap 增加约 0.5804 m（962、926）或 0.99705 m（857 的 Car/Medium 组合）。两臂在同一选定几何下使用完全相同的初始状态；正式采用哪种几何尚未冻结。

五档 tau 原值全部保留：`0.7389146577, 1.0933428563, 1.3877275661, 1.8288599276, 2.5614676647`。本任务没有从 MiTra `Vehicle_type` 推断 tau。候选方案为保留既有 B00 分配、按类别映射或将 tau 作为独立因素；后两者会改变行为解释或实验矩阵，需研究者决定。

Task14 的独立 A/B 输入文件哈希和初始状态审计继续通过：Leader 文件、时间网格、Leader/Follower 初始速度和近似 gap 相同；静态配置差异仍仅是五个 passenger vType 的 `minGap` 2.5→1.0。Task16 没有运行正式 A/B，也没有计算 `C`、TTC、Formal P2 或 D1 科研结果。

## 6. 重采样尾差

继续使用 Task14 线性 0.05 s 网格。原始与固定网格未表示尾差为 962=`0.012624 s`、926=`0.029958 s`、857=`0.048596 s`。固定网格、保留非网格终点、末端保持/外推三种政策均未冻结；本任务不外推未观测状态，也不擅自缩短正式观察窗口。

## 7. 正式执行链条预检

输入层、prototype 网络加载、SUMO 1.26.0/官方 TraCI 工具绑定、Leader readback、Follower 原生回放和静态 A/B common-input 接口均完成工程验证。结果层接口被保留用于后续正式运行，但本任务没有登记正式运动学、风险或事件结果。每次工程回放均带有输入来源、tau、几何、minGap、初始化模式、teleport/collision 和 `formal_task9=false` 字段。

## 8. 研究者决策清单

以下事项不能由本任务自动冻结：

1. 是否接受独立 straight-line prototype 作为受控局部实验网络；
2. 正式采用 MiTra 几何还是 B00 几何；
3. 正式 Follower 使用哪一个既有 B00 vType/tau（不新增映射或全因子矩阵）；
4. 是否接受 `safe_then_move` 一次性初始化以及当前 Leader `setSpeed`/`moveTo` 控制政策；
5. 固定网格尾差政策；
6. 是否将 962、926 及条件备用 857 提交正式输入审查；
7. 是否单独批准 Task9 三 seed、两臂的正式 6N 矩阵。

Codex 推荐先审查初始化动作、网络背景边界和几何/tau 选择，再决定是否冻结正式输入。推荐不把本次 60 次工程回放写成正式实验效果。

## 9. 最终状态

Task16 状态：`COMPLETED_PREFORMAL_ENGINEERING_READY_PENDING_RESEARCHER_DECISIONS`。三个候选均具备可复现的联合回放工程记录，但正式输入准入、网络科学适用性、车辆几何、目标 vType/tau、Leader 控制方式、尾差政策和正式运行授权仍待研究者决定。Stage 0.5 不因工程通过而解除 blocked。

机器证据：`evidence/results/RES-STAGE-0.5-POST-R2-TASK16-FOLLOWER-REPLAY-AND-PREFORMAL-READINESS-20261031/`。
