# P7 Task1 — 真实 SUMO 控制路径审计与端到端集成方案

**Task ID:** `AAD-P7-TASK1-20261103`
**工作包:** WP3 — 端到端工程集成与独立验证
**状态:** `COMPLETED_READ_ONLY_AUDIT_WITH_BLOCKER`
**审计日期:** 2026-11-03
**执行边界:** 只读源码、配置、既有报告和既有证据；未启动 SUMO/TraCI，未产生新轨迹，未修改生产控制代码、Formal P2、Formal rho/P2、P4 指标、Gate 或 Protocol Lock。

## 1. 结论先行

当前仓库存在可实际调用的 TraCI 控制接口，但没有识别到一个“接收远端风险消息、在策略输入边界消费消息、产生独立 Controller Decision、再生成目标车辆命令”的真实目标车辆策略。审计结论为：

`NO_EXISTING_MESSAGE_DRIVEN_TARGET_POLICY_IDENTIFIED`

最接近真实车辆控制的路径是 Stage 0.1 的 `_run_cell()`：它在固定时间窗内调用 `traci.vehicle.setAcceleration()`，并在 `traci.simulationStep()` 后读取目标车速度、加速度和位置。该路径的 `adopted_time` 由 `next_time >= 2.2` 直接赋值，目标车的 `-1.5 m/s²` 命令由同一预设时程分支产生；没有接收端回执、策略输入快照、消费回执、decision_id、command_id 或独立安全层。因此它是**工程时程控制**，不是已证实的消息驱动 Adoption。

Stage 0.5 Linux `NativeBackend` 的 `before_step()` 只对车道调用 `lane.setMaxSpeed()` 并用 `lane.getMaxSpeed()` 读回；它是交通环境供给控制，不是目标车辆自动驾驶策略。`run_observation_loop()` 随后调用 `simulationStep()`，再把 SUMO 原生状态送入 `IdentityObserver`，属于执行管理和读回链。`stage_0_5_native_capsule_v4.py` 和 `stage_0_5_linux_isolation.py` 负责 runtime/source/capsule/OS 隔离绑定，也没有策略输入或车辆 policy。Stage 0.5 no-message baseline 以及 B12/CD/LF workers 都明确记录 `no_vehicle_control=True` 或 `traci_vehicle_control=False`，只读车辆状态。

Stage 0.5 fixed-leader/follower 路径可执行 `setSpeed()`、`moveTo()`、速度模式和换道模式设置，但其职责是历史轨迹回放与 SUMO 原生 Follower 跟驰：Leader 被外部轨迹逐步驱动，Follower 在动态区间释放给 SUMO 原生控制器。它不能作为远端风险消息采用证据。

P3 的 `aad.p3.controller-evidence.v1` 已具备 14 类记录、显式外键、多对多消费、时间不确定性和 Unknown 规则，可以作为 P7 唯一新增 sidecar 接口。当前真实生产者尚未调用该接口；Task20 仍是 `fixture_only=true` 的工程 Fixture，不能升级为真实控制器采用证据。

## 2. 当前科研主线和边界

本任务沿用当前主线：来源可追溯且确实被控制器采用的远端风险消息，能否在普通物理影响到达目标区域前，通过改变目标车辆动作而改变区域总体风险。消息生成、发送、送达、验证、输入、消费、决策、命令、安全处理、实际执行、动作观测和区域风险观测必须逐层保留。

当前科研状态保持不变：

- Formal A = 0；Independent Qualified Witness = 0；F0 / Overall TR–TP = Unknown。
- Stage0.5 = `CLOSED_WITH_LIMITATIONS`；Stage0.6 = `PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS`。
- Protocol Lock = `BLOCKED`；Stage I = `READY_ENGINEERING_ONLY`；Stage1.1 = `NOT_AUTHORIZED`。
- 统一定义为 v0.4 / 27 项；P3 策略输入采用边界仍为 `PROPOSED`。

本报告只给出工程事实、证据接口位置和下一项实施范围。它不批准新的控制算法、不冻结 Adoption 定义、不定义 P5 Enabled/Disabled、不改变 P4 动作或风险阈值，也不主张已经存在消息造成的因果效应。

## 3. 审计范围和影响判断

审计覆盖以下源码和既有文档：

- Stage 0.1：`code/src/riskprop/stage_0_1_sumo.py`。
- Stage I/Task20：`code/src/riskprop/stage_i_mechanism.py`、`code/scripts/run_task20_stagei_engineering_fixture.py`。
- Stage 0.5 执行体系：`stage_0_5_execution_v2.py`、`stage_0_5_linux_controller_v4.py`、`stage_0_5_linux_isolation.py`、`stage_0_5_identity_observation.py`、`stage_0_5_native_capsule_v4.py`。
- Stage 0.5 no-message/Observer：`stage_0_5_sumo.py`、`run_stage_0_5_sumo_baseline.py`、B12/CD/LF workers。
- Stage 0.5 TraCI replay：`stage_0_5_fixed_leader_traci.py`、`stage_0_5_fixed_leader_follower_traci.py`、`stage_0_5_leader_replay.py`、`run_stage_0_5_task16_joint_replay.py`。
- P3/P4/Formal 接口：`controller_evidence.py`、`communication_observability.py`、`formal_design.py`、`formal_artifacts.py`、`formal_runner.py`、`formal_risk_measurement.py`。

本次只新增审计文档、集成蓝图、机器可读矩阵和便携证据；没有共享核心代码改动。因此验证集中在源代码行号、文件 SHA256、JSON 结构、Markdown 链接和项目文档一致性。

## 4. 控制能力分类

| 类别 | 已识别实现 | 事实边界 |
|---|---|---|
| 真实车辆策略决策 | 未识别 | 没有消息输入组装、策略推理、decision 输出和 command 外键；结论为 `NO_EXISTING_MESSAGE_DRIVEN_TARGET_POLICY_IDENTIFIED`。 |
| 预设时间/条件触发 | Stage 0.1 `_run_cell()` 的 source/target `setAcceleration` | 时间窗和 cell 条件直接决定命令；`adopted_time=2.2` 是工程时程，不是消费凭证。 |
| 历史轨迹回放 | fixed Leader replay、joint replay、`stage_0_5_leader_replay.py` | 轨迹或 Leader 输入直接驱动 SUMO；Follower 动态行为来自 SUMO 原生模型。 |
| SUMO 原生交通模型 | Follower 释放后的 Krauss 跟驰、原生状态/碰撞/teleport getter | 可观察、可读回；不等于远端消息策略或独立安全过滤器。 |
| 环境/车道控制 | Linux `NativeBackend.before_step()`、interaction diagnostic worker 的 `lane.setMaxSpeed()` | 控制 lane speed limit 供给，作用对象是环境，不是目标车 policy。 |
| 只读 Observer | Stage 0.5 no-message、B12/CD/LF、`IdentityObserver` | 读取身份、位置、速度、加速度、leader、gap、TTC/风险测量；不下发车辆策略命令。 |
| 工程 Fixture | Task20、formal runner、P3 evidence fixtures | 证明接口可以运行，`fixture_only=true`；不证明真实 SUMO 控制器消费消息。 |

## 5. 真实策略决策边界

静态调用关系没有找到以下任一完整链：

1. 接收端消息输入函数；
2. payload 验证和有效期过滤；
3. 策略输入快照组装；
4. 消费/采用判断；
5. 独立 `decision_id` 和策略版本；
6. 由决策输出生成的 `command_id`；
7. 命令 API 返回/接受状态；
8. 独立安全层前后命令；
9. command→execution→post-step readback 的显式引用。

Stage 0.1 只在 `_run_cell()` 的同一循环中由时间和 cell 条件设置 `generated_time`、`adopted_time` 和 `target_command`（`stage_0_1_sumo.py` L238–L256），之后才调用 `simulationStep()`（L257）。这说明命令源是实验条件/预设时程，而不是由消息 payload 经过策略函数计算。

Task20 的 `build_engineering_fixture()` 直接构造 `generated/sent/delivered/adopted` 时间和事件表（`stage_i_mechanism.py` L241–L339），runner 也明确写入 `fixture_only=true`、`sumo_runs=0`、`scientific_claim_eligible=false`（`run_task20_stagei_engineering_fixture.py` L48–L123）。它不能填补真实策略缺失。

## 6. 六个 P3 接入位置审计

### A. 消息接收和验证

当前 Stage 0.1 的 `protocol.parquet` 有 `message_id`、`delivered_time_s`、`validation_time_s` 等兼容字段，但这些值来自同一时程记录，不是接收端 producer 的 P3 receipts。真实 P7 必须在目标车辆接收/验证函数处分别写 `delivery`、`validation` 和 `input`；发送端只能写 `send`，不能回填送达。

### B. 策略输入和消费

未找到真实策略输入组装函数。P3 现有 `input`/`consumption` 记录要求 `validation_id`、`input_snapshot_ref`、`input_snapshot_hash`、`decision_id`、策略版本和 Proposed adoption boundary。过滤器读取只能记 `CONSIDERED`；只有真实策略输入边界才能候选记录 `POLICY_INPUT_INCLUDED`。

### C. Controller Decision

当前没有独立决策记录。P3 允许“消费消息但 `UNCHANGED`”、一决策多消息、同消息多周期、失败决策和零命令。P7 应在真实策略产生输出的位置写 `decision`，不能用 `adopted_time` 或 `setAcceleration` 参数代替。

### D. Control Command

Stage 0.1 的 `setAcceleration` 和 replay 的 `setSpeed` 是可复用的 TraCI 调用边界，但当前没有 `command_id`、`decision_id`、API 参数快照、ack/status、取消/替代状态。P7 需在真正调用 API 的薄层记录原始命令值、单位、有效区间和返回/异常。命令值不能当作实际加速度。

### E. Safety Processing

未识别独立策略安全过滤器。Stage 0.1 的 `safety_intervened=False` 是写定字段（L287–L294）；SUMO 原生跟驰、速度模式、碰撞 getter 和 `collision.action=warn` 是仿真/模型行为，不能自动命名为独立 Safety Layer。P7 没有独立安全函数时必须记录 `NOT_OBSERVED` 或 `UNKNOWN`，不能写 `CONFIRMED_NONE`。

### F. Actual Execution

Stage 0.1 在 `simulationStep()` 后读取 `getIDList()`、`getPosition()`、`getSpeed()`、`getAcceleration()`、leader/gap（L258–L285）。fixed replay 的 `_state()`/`_append_sample()` 同样在 post-step 读取位置、速度、加速度和车辆存在性。它们提供可复用的读回事实，但当前没有 execution_id、command_id、车辆 incarnation 的 P3 关联。P7 应把命令值、执行状态、post-step 实际 `v/a/x` 和车辆退出/右删失分别保存。

## 7. P3 14 类记录的适用性

P3 的 `SPECS` 在 `controller_evidence.py` L87–L107 固定了 14 类记录。当前接入状态如下：

| P3 kind | 当前实际位置 | P7 处理 |
|---|---|---|
| `source` | Stage 0.1 的 `source_present`/source vehicle 条件；不是 P3 source receipt | 真实 source observer 边界产生；保留 qualification Unknown。 |
| `message` | Stage 0.1 `protocol.parquet` 只有兼容字段 | 在 message generation producer 记录 payload hash/ref、validity 和 source_event_id。 |
| `send` | 未找到发送端 P3 记录 | 在 sender/transport 调用处写每次 attempt。 |
| `delivery` | 未找到接收端回执 | 只在 receiver 观察到时写；发送端不代替。 |
| `validation` | Stage 0.1 `source_valid/target_valid/freshness_valid` 是表字段 | 在目标接收端的 validator 写状态、版本和原因。 |
| `controller` | 未找到 controller instance registry | 初始化时绑定 controller/policy/code/config hash 和车辆 incarnation。 |
| `input` | 未找到真实策略输入函数 | 在策略输入可用边界写 `RECEIVED/QUEUED/AVAILABLE/UNKNOWN`。 |
| `consumption` | 未找到实际消费路径 | 过滤/评估/拒绝/纳入策略分别写；纳入仍是 Proposed boundary。 |
| `decision` | 未找到独立 decision | 在策略输出点写，支持 no-change/failed/no-command。 |
| `command` | TraCI setter 是孤立调用 | 在真实 API wrapper 写 command creation/issue/ack/failure/supersession。 |
| `safety` | 独立安全函数未识别 | 没有机制时写 `NOT_OBSERVED`/`UNKNOWN`，不默认无干预。 |
| `execution` | post-step native readback 局部存在 | 绑定 command、车辆 incarnation、执行状态、实际 v/a/x 和 readback hash。 |
| `action_observation` | Stage 0.1 `action.parquet`/Task20 action event 是旧或 fixture 输出 | 由 P4 action adapter 引用 execution；不在 P7 冻结阈值。 |
| `risk_observation` | Stage 0.1 `risk.parquet` 是 validation-only；Stage 0.5 有 versioned measurement outputs | 由 P4 risk adapter 引用 action observation 和已有 measurement version；不重算 Formal P2/rho。 |

`controller_evidence.py` 的 `producer_role`、hash 格式和外键验证只能验证记录结构和声明关系，不能认证 producer 自己声称的源代码或 payload 哈希。真实性必须由 P7 manifest、原始日志和外部文件字节绑定共同提供。

## 8. P4 动作和区域风险观测

当前可复用的动作事实有两层：

- Stage 0.1 `action.parquet` 字段包括 `command_acceleration_mps2`、`applied_acceleration_mps2`、`safety_intervened`、`action_diverged` 和配对 cell；其中 `action_diverged` 按时程赋值，不能当作消息造成的变化。
- fixed replay/Stage 0.5 读回表包含 `simulation_time_s`、Leader/Follower 位置、速度、加速度、gap、碰撞/teleport 诊断；这些可作为 `observation_ref` 的原始状态来源。

当前可复用的风险事实有：

- Stage 0.1 `risk.parquet` 的 `ttc_burden_validation` 明确标记 `inclusion_status=stage_0_1_validation`、`attributable=False`、`not_calibrated_for_science`。
- `stage_0_5_sumo.compute_sumo_measurements()`（L1070–L1145）保留 `measurement_status`、`ttc_valid`、`missing_reason`、`p2_evaluable_eligible` 等状态；Formal P2/rho 版本由 `formal_risk_measurement.py` 管理。

P7 只应把这些输出以文件/hash/measurement version 引用到 `action_observation` 和 `risk_observation`，不重设计风险指标，不把“观察到风险行”改写为风险效应 onset。

## 9. 推荐的 P7 Task2 路线

P7 Task2 可以采用一次整体接线，但必须先满足一个前置条件：研究者指定并批准真实目标车辆策略和消息输入边界。当前尚无可接线的 message-driven target policy，因此不能把 Stage 0.1 的 fixed schedule 直接升级为正式控制器。

满足前置条件后，建议按以下顺序整体实现：

1. 建立薄的 `Evidence Adapter`，唯一复用 `controller_evidence.EvidenceJournal`；不建立第二套日志 schema。
2. 在真实 receiver/validator 写 Delivery、Validation、Input；绑定原始 payload、接收日志和车辆 incarnation。
3. 在策略输入组装和实际策略执行点写 Consumption、Decision；保留 `CONSIDERED`、`REJECTED`、`POLICY_INPUT_INCLUDED`、`UNCHANGED`、`FAILED`。
4. 在 TraCI command wrapper 写 Command；原样记录 API 名称、参数、单位、有效区间和调用异常。
5. 若真实代码存在独立安全层，再写 Safety；否则显式 Unknown/Not Observed。
6. 在 `simulationStep()` 后读回车辆存在性、incarnation、速度、加速度、位置、step 和 phase，写 Execution。
7. 由 P4 adapter 把 execution 引用到既有 Action/Risk 观测，保存 observation/ref/hash/measurement version。
8. 生成原始日志、代码/config/runtime/SUMO/TraCI/input/payload/snapshot/readback/sidecar 的最终 manifest。

建议修改范围见 [P7_INTEGRATION_BLUEPRINT.md](P7_INTEGRATION_BLUEPRINT.md) §8；本 Task1 不实施这些修改。

## 10. 待决事项分层

### 工程上可以自主解决

- sidecar 文件布局、独占创建、record ID 生成和幂等写入。
- `run_id/pair_id/cell_id/block_id/assignment_id` 与 `vehicle_incarnation_id` 的命名和关联。
- Before Step / After Step / post-readback 的 phase、sequence、clock 字段填充。
- 原始日志、输入快照、代码/config/SUMO/TraCI/payload/readback/sidecar 的 manifest 和 SHA256。
- 定向测试、异常测试、Unknown/右删失保存和文档索引。

### 需要研究者确认

- 哪个真实目标车辆自动控制器是本项目研究对象。
- 是否允许/需要新增目标车辆策略；若需要，策略算法和输入语义由研究者决定。
- `POLICY_INPUT_INCLUDED` Proposed Adoption 边界是否正式接受。
- P5 Enabled/Disabled 的机制语义、随机化和资格总体。
- 是否存在并研究独立 Safety Layer；SUMO 原生约束是否只作为执行环境事实。
- P4 Action Change 的正式比较对象、阈值、窗口和区域风险评价标准。

### 当前不阻塞基础工程接线

- Adoption 正式定义未冻结，不妨碍记录原始 Input/Consumption/Decision 事件。
- P5 开关语义未冻结，不妨碍建立通用 `adoption_mode/source/version` 元数据。
- P4 数值阈值未冻结，不妨碍引用已有 action/risk output 和质量状态。
- 独立物理到达真值不足，不妨碍建立控制器事件链；物理先后保持 Unknown。

## 11. 下一步结论

当前具备**证据 sidecar 和 Observer/TraCI 读回的工程准备条件**，不具备把“远端风险消息→策略消费→目标车决策”作为真实生产路径接线的科研对象条件。P7 Task2 应在研究者确认真实策略后一次性完成 adapter、回执、决策、命令、安全（若存在）、执行、post-step readback、P4 引用和 manifest 绑定；在此之前不得把固定时程、replay、lane supply 或 Task20 fixture 重命名为真实消息驱动控制器。

便携机器证据见 [`evidence/research/P7_TASK1_20261103/README.md`](../../../evidence/research/P7_TASK1_20261103/README.md)。
