# AAD-S0.5-TASK20：Stage 0 收口、Stage 0.6 Pre-Lock 与 Stage I 机制准备

日期：2026-11-01（Asia/Shanghai）
任务状态：`COMPLETED`
科研结论资格：`scientific_claim_eligible=false`

本报告只复用已登记的 Stage 0/Task9–19 证据，并完成必要的离线数值复算与合成工程 fixture。没有重跑 Task9/Task18/Task19 的正式矩阵，没有读取 locked holdout，没有新增正式干预臂、seed 集合、风险事件定义或 Gate 规则。

## 1. 最终状态登记

| 字段 | Task20 状态 | 含义 |
|---|---|---|
| `TASK20_STATUS` | `COMPLETED` | 收口报告、Pre-Lock 包、机制 fixture、测试和证据索引已完成 |
| `STAGE_0_5_FINAL_DISPOSITION` | `CLOSED_WITH_LIMITATIONS` | 工程与已获支持的描述性研究职责完成；严格科学 Gate 未通过 |
| `STAGE_0_6_READINESS` | `PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS` | 数值/字段/复现包齐全，科学容差与动态校准仍待决 |
| `PROTOCOL_LOCK_STATUS` | `BLOCKED` | 既有 fail-closed writer 正确拒绝生成锁文件 |
| `STAGE_I_ENGINEERING_READINESS` | `READY_ENGINEERING_ONLY` | 信息链、联合时间轴、四格/生命周期契约可用合成输入验证 |
| `STAGE_1_1_FORMAL_AUTHORIZATION` | `NOT_AUTHORIZED` | 未生成并核验 Protocol Lock，不得启动正式确认实验 |
| Scientific Equivalence | `FALSE / NOT_ACCEPTED` | 现实—仿真微观交互、独立物理路径和网络级支持仍不足 |

`CLOSED_WITH_LIMITATIONS` 是阶段处置，不是 Gate PASS，也不是 AAD 核心假设成立。

## 2. 影响范围与方法边界

本任务修改了一个 Stage I 工程契约模块、一个合成 fixture 入口、一个定向测试文件，以及 Task20 报告/机器证据和项目索引。修改不触及 Formal P2、D1、B witness、通信可观测性定义、`protocol_lock.py` 准入逻辑、正式 config、locked holdout 或历史结果。验证覆盖范围是新模块与其直接依赖的定向测试、既有 Stage 0.6 解析真值/误差预算脚本和协议 readiness；环境缺失的 Parquet 依赖失败保留为历史环境问题。

## 3. Stage 0.5 最终科研评估

### 3.1 分层结论

| 层级 | 已有证据 | 能支持的结论 | 仍缺少的证据 | 对后续研究的影响 | 最终建议 |
|---|---|---|---|---|---|
| 数据与测量正确性 | Stage 0.2 R4 四源 NGSIM 正式重提取与事件审计；Task4/5/6/10 保留 identity、clock、gap、closing 和右删失规则；Formal P2 source `167/159`、target `174/252` 可复核 | 受限的纵向跟驰风险测量、暴露分母和事件/对照内部一致性已可靠建立 | 没有独立视频/标定物理真值；PreciseNGSIM 无事件级独立 crosswalk；参考点与真实物理 gap 仍有假设 | 可做描述性和内部机制诊断；不能把轨迹当独立物理真值 | 关闭“测量链是否可执行”问题，保留真实性限制 |
| 仿真与结果执行正确性 | Task17 修复后 formal Task9 60 组：54 PASS、6 collision FAIL；Task18 共 174 组计划执行，Follower 释放、native speed、输入和 A/B pairing 通过；Task19 100 组离线分析、50 个 A/B 配对均通过 | SUMO/TraCI 执行链、失败保留、输入哈希和同 seed 可复现性已闭合 | 正式 Task9 仍是局部固定 Leader 条件；没有网络级消息、区域风险或物理路径实验 | 可以继承执行器、共同输入和审计框架；不能把局部响应升级为网络效应 | 关闭工程执行缺口，不追加重复运行 |
| 交通状态与运动学支持 | NGSIM、pNEUMA 受限运动学参考；既有状态支持与 Stage 0.5 场景诊断；宏观状态可在限定窗口/配置下复现 | 供给、状态和运动学变量的参考范围已可用于受限场景设计 | 交互兼容层失败：状态匹配配置的局部 P2 约 `0.9–1.5/veh-h`，现实参考约 `17.0/23.5/veh-h`；离散度和低速联合结构仍不同 | Stage I 可使用受限 simulator-only estimand；不得宣称现实等价或外推 | 将差异记录为行为/供给/测量竞争解释，不再参数搜索 |
| 微观跟驰交互 | Task9/Task19 显示两候选固定 Leader 下 Follower 响应可重复；tau 依赖候选、minGap 差异主要在高 tau；Task8 的 `C_initial/C_f/C_l/C/C_gap/R` 闭合保留 | 局部条件响应机制可被工程化测量，且不是执行器锁死或重复帧 | MiTra 输入不是独立物理 truth；直线 prototype 不等价 B00 背景；tau、几何和 tail 适用域有限 | 可作为 Stage I 局部动作响应模块；不能作为网络级信息效应样本 | 采用“局部条件响应”标签，禁止升级为普遍驾驶规律 |
| Formal P2 事件与暴露 | NGSIM 正式 source 167/159、target 174/252；B00/Round2 sealed SUMO source 为 0；positive exposure 已有 | 真实参考和仿真结果的差异是可审计事实 | 未知差异来自输入供给、行为模型、测量契约还是三者交互；零源事件不是零风险证明 | Stage I 不能以当前 source trigger 作为现实等价来源 | 保留两套契约和差异，停止用调参“修复” |
| 物理传播路径可观测性 | Task10 找到 40 个同车 source→target 有序候选（16+24）；身份/时间顺序可追溯 | 可描述时序候选和右删失状态 | 合格 B witness `0`；40 条均 `physical_connection_basis=Unknown`；没有独立时间化道路连接/视频见证 | 无法计算可信的普通物理到达时间；信息先于物理的比较必须为 Unknown | 不从道路距离或任意速度推导 arrival time |
| 后续信息机制适用性 | `formal_design.py` 已有四格、生命周期、pre-treatment equivalence；Task20 新模块将其组装为联合时间轴 fixture；Stage 0.4 仅接受 receive-state observability | 工程链可记录生成→发送→送达→验证→采用→动作→风险各阶段 | 真实通信 adoption 不可观测；Stage I 正式 endpoint、cohort、系统误差界和 physical arrival 未冻结 | 可进入 engineering-only 机制联调；正式 Stage 1.1 仍 blocked | 先完成接口联调和字段审计，等待 Protocol Lock |
| 真实世界外推资格 | 无独立物理 truth、无自然交通 V2V adoption/latency/PDR calibration、无 B witness | 无现实世界因果外推资格 | 需要新独立证据和研究者批准的适用域 | 只能报告 simulator/local conditional 结果 | `real_world_extrapolation=NOT_ELIGIBLE` |

### 3.2 Task9 与 Task19 的科研价值边界

Task9 固定 Leader 实验解决了原有的局部执行不确定性：Follower 控制释放路径明确、Leader 输入和初始状态可配对、A/B minGap 只在声明的五档 tau 和两个候选下变化、轨迹闭合残差约 `2.84×10^-14 m`、同 seed 重复一致且不同 seed 有可见差异。Task19 因此可以报告局部响应的候选依赖、tau 非单调结构和高 tau 下的 A/B 描述性差异。

Task9/19 没有解决：真实物理输入的独立认证、SUMO 背景交通等价性、消息生成/送达/验证/采用链、控制器采用后的区域风险变化、网络级 source risk 支持、B 类物理传播见证、普通物理到达时间，以及 AAD 核心因果假设。`C_f`、`C`、`C_gap` 等分解量代数相关，不能当作独立效果样本。

### 3.3 Stage 0.5 最终处置

Stage 0.5 的工程与描述性科研职责已经达到可交接状态；原严格科学 Gate 仍因以下必要条件不满足而 blocked：

1. B00/Round2 没有合格 source P2 事件，不能支持 source-triggered network effect；
2. 现实—仿真微观交互和输入供给影响尚未达到 Scientific Equivalence；
3. 独立物理路径见证为 `0`，普通物理到达时间为 `Unknown`；
4. 关键系统偏差界、科学容差和正式配对方差没有科学批准。

因此本报告将 Stage 0.5 登记为 `CLOSED_WITH_LIMITATIONS`，同时保留 `scientific_gate=blocked`、`scientific_equivalence=false`。这表示停止 Stage 0.5 的无限校准/参数搜索循环，不表示这些缺口已被填补。

## 4. Stage 0.6 Numerical and Pre-Lock Validation

### 4.1 已复用与本任务复算的数值事实

- `rear_end_analytic_truth`、NGSIM TTC/DRAC、PET、缺失/碰撞/右删失和路径 fixture 均通过；四个解析案例、PET 两例、碰撞案例和四种物理路径状态（断开、有限到达、右删失、缺车）均 PASS。
- 时间步 fixture 使用 `0.10/0.05/0.02/0.01 s`，方向一致；`0.05–0.02 s` 的固定窗口差异为 `0.0029869451697126514`。由于没有研究者批准的 `delta_eq`，状态保持 `pending_delta_eq`。
- Task20 重新运行既有 `run_stage_0_6_error_budget_v1.py` 的 deterministic smooth-closing fixture。四组 higher-99% bounds 为：numerical `0.0`、timestep `0.003126623629764791`、analyzer `3.33e-16`、reconstruction `0.007484070781639929`；既有 `derive_delta_eq(max)` 返回 `0.007484070781639929`。
- 既有 weekly protocol candidate 另以“来源上界求和 + 配对三角界”提出 `delta_eq_per_arm=0.010610694411405053`、`delta_eq_paired=0.021221388822810106`、`delta_eq_four_arm=0.04244277764562021`。这是不同聚合约定下的 Proposed 候选，不是两个已冻结真值；在研究者采用前必须明确聚合规则。
- 已登记的条件量化敏感性（复用 `stage_0_6_error_budget_week_v2`）覆盖 `240,620` 个支持状态，higher-99% absolute rho sensitivity `0.009846098292511804`，最大值 `0.017363312053241375`。它只表示 `±0.01` gap/closing 角点敏感性，不是动态误差界、现实测量偏差界或 treatment contrast 界。

### 4.2 字段状态

| 字段 | 当前状态 | 处理 |
|---|---|---|
| `rho`、TTC、gap、closing、积分和分析器一致性 | `Verified`（声明域内） | 复用并保留 fixture 输出 |
| 时间步 ladder | `Verified fixture / dynamic Unknown` | 记录差异，不设阈值 |
| `epsilon_input` | `Proposed exact matching` | 工程 hash/paired-input 契约可用，科学容差未冻结 |
| `epsilon_state` | `Proposed resolution floor` | `0.01 m / 0.01 m/s / 0.1 s` 不是动力学 divergence tolerance |
| `delta_eq` | `Proposed` | 存在 max 与 joint-sum/paired 两种候选聚合；待研究者确认 |
| `delta_R`、`delta_plan`、`h` | `Proposed` | `0.05/0.10/0.0125` 仅候选值，未获科学批准 |
| 配对方差 | `Unknown` | Task9 五 seed 和重复一致性不构成确认性 treatment variance |
| Stage 1.1 样本量 | `Unknown` | `minimum=100` 是规划下限，不是最终 n；需真实 paired variance、SESOI 和 endpoint |
| 系统偏差 `B` | `Unknown` | fixture 数值误差不能替代 simulator-to-world bias bound |
| 通信可观测性 | `Agreed limited scope` | 仅 receive-state continuity/描述性通信证据；adoption、PDR/latency/distance 未校准 |
| 物理到达时间 | `Unknown` | 没有独立时间化物理路径见证，不从距离/速度推断 |

### 4.3 Protocol Lock Readiness

当前 gate 输入为：`stage_0_2=pass`、`stage_0_4=pass_limited`、`stage_0_5=blocked`、`stage_0_6=pending_scientific_tolerances_and_dynamic_calibration`。既有 `protocol_lock_readiness()` 返回：

```text
protocol_lock_allowed=false
stage_1_1_allowed=false
blockers=["stage_0_5=blocked", "stage_0_6=pending_scientific_tolerances_and_dynamic_calibration"]
```

随后对现有 `write_protocol_lock()` 做了 refusal check，结果为 `Correctly refused`，没有生成候选锁文件。Task20 交付 `PRE-LOCK` 包，不修改任何准入逻辑。

## 5. Stage I 核心机制设计与工程就绪

### 5.1 估计对象和两条链

正式候选 estimand 保持为：在共同初始状态、共同随机性和预先定义的目标 cohort 下，比较“风险消息被控制器采用”与相应对照对目标区域 Formal rho/P2 对象的影响；当前仍是 `Proposed`，不写入 Agreed。

物理链记录：`source risk/state → vehicle motion/interaction → physical propagation → target state/risk`。
信息链记录：`event generated → message generated → sent → delivered → validated → adopted → action change → regional risk observation`。

Task20 原型要求每一阶段都有 `run_id/pair_id/event_id/event_type/time_s/vehicle_id/region/source`，并复用既有生命周期字段与时间顺序校验。消息生成不等于送达，送达不等于验证，验证不等于采用，采用不等于动作改变，动作改变不等于区域风险改变。

### 5.2 四格对照候选

工程 fixture 复用了现有 `s0c0/s0c1/s1c0/s1c1` 契约：source presence × channel enabled。正式实验仍需研究者确认下列对照的科学语义：

1. `s0c0`：无源消息、无通道；
2. `s0c1`：无源消息/安慰剂或关闭 adoption 的通道对照，不能偷偷生成 source message；
3. `s1c0`：有源事件但通道关闭/未采用；
4. `s1c1`：有源事件、消息完成送达并由控制器采用。

工程原型只验证契约和日志闭合，不把它当作正式四格结果。正式候选必须另外冻结：干预变量、采用证据、动作改变判据、区域风险对象、消息影响时间、共同输入/初态/随机性、失败/缺失/右删失规则、安慰剂 payload 和竞争解释。

### 5.3 物理—信息时间比较

联合时间轴在无独立 physical arrival time 时输出 `information_before_physical=Unknown`，并明确“event ordering is not treated as proof”。只有当物理到达时间来自合格 B witness 或其他研究者批准的独立时间化证据时，才比较 adopted/action/risk 时间与 arrival；否则不能用道路距离、任意速度或 SUMO 拓扑单独构造到达时间。

### 5.4 工程 fixture 结果

`code/outputs/analysis/task20_20261101/stage_i_engineering_fixture/` 中的合成 fixture 通过：四格 common-config 检查、四格 lifecycle 单调性、pre-treatment 等价性、动作差异持续判据、联合时间轴排序和 Unknown 物理到达处理。该 fixture 明确 `sumo_runs=0`、`locked_holdout_read=false`、`scientific_claim_eligible=false`。

## 6. Stage 0 → Stage I 交接

### 已完成

- Stage 0.2 Formal P2 测量、暴露和失效语义在批准范围内可复核。
- Stage 0.3 pNEUMA 仅承担城市运动学/车型分布角色；不恢复退役的前车推断职责。
- Stage 0.4 通信可观测边界已限域关闭，adoption 仍不可观测。
- SUMO/TraCI、原生 Follower、A/B 配对、随机种子和机器证据链已具备工程复现能力。
- Task9/19 已形成局部条件响应证据，且严格保留失败、候选差异和适用域。
- Stage 0.6 解析真值、路径 fixture、误差预算和 Pre-Lock 字段审计已执行。
- Stage I 信息链/物理链日志接口和合成联调 fixture 已完成。

### 可由本任务完成

- Task20 分层收口、Stage 0.5 处置、Stage 0.6 readiness 和最小 Stage I 机制原型。
- 输入/源码/配置/环境/证据 SHA 绑定和报告索引。
- 现有协议 lock refusal 的可复现核验。

### 已有工程能力但缺科研验证

- 生产消息链与 SUMO controller 的端到端 adoption 事件；
- 目标区域 Formal rho/P2 的四格联动与区域级聚合；
- 真实/仿真物理 arrival witness；
- 动态配对时间步收敛、endpoint-specific error budget 和 treatment variance；
- 现实—仿真系统偏差 `B` 的识别。

### 需要研究者最终确认

- 是否接受有限 simulator/local-conditional estimand 作为 Stage I 先行研究对象；
- `delta_eq` 聚合约定、`delta_R`、`delta_plan`、`h` 和 `epsilon_state` 的正式值；
- Stage I 四格中安慰剂、通道关闭和 adoption 的具体科学语义；
- target cohort、risk window、验证窗口、失败/删失纳入和独立方差校准设计。

### 必须等待新证据

- 独立物理路径与事件级 physical arrival time；
- source-triggered 网络级风险事件或研究者批准的有限适用域替代定义；
- 真实通信 adoption、消息时间和控制器采用证据；
- 足以识别系统偏差和配对方差的新证据。

## 7. 集中决策清单

| 决策项 | 证据 | 可选方案 | 推荐 | 科学影响 |
|---|---|---|---|---|
| Stage 0.5 是否继续无限校准 | Task10/11/12/13/14/15/16/17/18/19 已闭合可执行工作，但 B witness=0、等价性 false | 继续搜索；有限适用域收口；改 Gate | 采用 `CLOSED_WITH_LIMITATIONS`，停止无边界参数搜索 | 保留历史成果，明确现实外推不成立 |
| Stage I 先行 estimand | Task9/19 只有局部固定 Leader 响应；Stage 0.4 adoption 不可观测 | 直接正式因果；simulator-only engineering/conditional mechanism；等待真实证据 | 先做工程联调和受限 mechanism design，不启动 1.1 | 可验证信息链/动作链接口，不产生科学主效应 |
| `delta_eq` 与科学容差 | fixture max 与 joint-sum/paired 候选均已计算，尚未 Agreed | 采用 max；采用 joint-sum；继续 Pending | 保持 Pending，先由研究者选定聚合语义 | 避免把软件误差或候选阈值写成现实 bias 界 |
| physical arrival time | 40 条 source→target 候选全部 B `Unknown` | 距离/速度推断；独立见证；保留 Unknown | 保留 Unknown；无 arrival time 不做“先于物理”结论 | 保护核心因果识别不被时间先后替代 |
| 四格 adoption 语义 | 现有四格/lifecycle 工程契约通过，真实 adoption 未观测 | 以送达代替采用；增加 controller receipt；仅合成 fixture | 必须记录 controller adoption receipt；送达不得替代采用 | 保持信息链因果边界 |

## 8. 机器证据与复现入口

- 报告：`docs/TASK20_STAGE0_CLOSURE_AND_STAGEI_READINESS_20261101.md`
- Task20 输出：`code/outputs/analysis/task20_20261101/`
- Stage I fixture：`code/outputs/analysis/task20_20261101/stage_i_engineering_fixture/`
- Stage 0.6 pre-lock validation：`code/outputs/analysis/task20_20261101/stage_0_6_prelock_validation/`
- Stage 0.6 error budget：`code/outputs/analysis/task20_20261101/error_budget/`
- Protocol readiness/refusal：`code/outputs/analysis/task20_20261101/protocol_lock_readiness.json`、`protocol_lock_writer_check.json`
- 既有 Task19：`docs/TASK19_SCIENTIFIC_RESULT_ANALYSIS_20261101.md` 与 `RES-STAGE-0.5-TASK19-SCIENTIFIC-RESULT-ANALYSIS-20261101`
- 既有 Task18：`docs/TASK18_EXECUTION_AUDIT_20261101.md` 与 `RES-STAGE-0.5-TASK18-EXECUTION-INTEGRITY-20261101`
- 既有 Stage 0.6 周期包：`RES-STAGE-0.6-WEEK-20261027-V1`

复现命令：

```powershell
$env:PYTHONPATH='code/src'
python code/scripts/run_task20_stagei_engineering_fixture.py --output code/outputs/analysis/task20_20261101/stage_i_engineering_fixture
python code/scripts/run_stage_0_6_prelock_validation.py --output code/outputs/analysis/task20_20261101/stage_0_6_prelock_validation
python code/scripts/run_stage_0_6_error_budget_v1.py --output code/outputs/analysis/task20_20261101/error_budget
```

本任务没有生成 Protocol Lock，也没有打开 Stage 1.1。
