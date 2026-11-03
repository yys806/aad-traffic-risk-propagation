# P7 Task1 — 真实控制路径清单

本清单只记录当前源码中实际存在的 TraCI 调用、执行管理和 post-step 读回。`命令来源`按“策略、时程、轨迹回放、人工/工程指定、原生模型、环境供给”区分；“可复用”表示能否作为 P7 的工程边界复用，不表示已经具备科学证据资格。

审计结论：`NO_EXISTING_MESSAGE_DRIVEN_TARGET_POLICY_IDENTIFIED`。

## 1. 车辆/环境控制接口矩阵

| 源文件 | 函数 / 行号 | 控制 API | 控制对象 | 命令来源 | 阶段 | 实际读回 | message/decision/command 关联 | 当前性质 | P7 可复用性 |
|---|---|---|---|---|---|---|---|---|---|
| `code/src/riskprop/stage_0_1_sumo.py` | `_run_cell()` L247–L250 | `traci.vehicle.setAcceleration("source_0", -3.0, 0.2)` | source vehicle | source_present 且 `2.0 <= next_time < 3.0` 的固定时程 | Before Step | L258–L285 读取 source 状态 | 无 | 工程时程控制；source 扰动 | 仅可作为 command wrapper 参考；不能作为消息策略 |
| `code/src/riskprop/stage_0_1_sumo.py` | `_run_cell()` L252–L256 | `traci.vehicle.setAcceleration("target_0", -1.5, 0.2)` | target vehicle | `channel_enabled` 且 `adopted_time` 已由 `next_time >= 2.2` 设定 | Before Step | L258–L294 读取目标速度/加速度/位置 | 无；`adopted_time` 与命令同一时程分支 | 工程时程控制，非真实 Adoption | 不可直接复用为正式策略；可作为 API 记录点演示 |
| `code/src/riskprop/stage_0_1_sumo.py` | `_run_cell()` L257 | `traci.simulationStep()` | 仿真全局 | 循环时钟推进 | Step boundary | L258 读取 native time；L260–L285 读取车辆 | 无 | 真实 SUMO step，但没有控制链外键 | 可复用作 post-step 触发点 |
| `code/src/riskprop/stage_0_1_sumo.py` | `_run_cell()` L267–L283 | `getIDList/getLaneID/getRoadID/getPosition/getSpeed/getAcceleration/getLeader` | 所有车辆，重点 target | 观察 | After Step | 是；每个 active vehicle 写 `state_rows` | 无 | native readback | 可复用为 Execution 的原始状态来源 |
| `code/src/riskprop/stage_0_1_sumo.py` | `_run_cell()` L287–L303 | `action_rows` / `risk_rows` | target vehicle | 由时程变量 `target_command/adopted_time` 派生 | After Step | `applied_acceleration_mps2` 有读回；`safety_intervened=False` 写定 | 无 | 旧 action/risk validation 输出 | 只可作为 P4 引用来源；不能直接转成 P3 execution |
| `code/scripts/stage_0_5_execution_v2.py` | `NativeBackend.before_step()` L316–L338 | `connection.lane.setMaxSpeed()` + `lane.getMaxSpeed()` | 车道/环境 | `lane_speed_schedule` | Before Step | 同函数读回 native lane limit | 无 | 环境供给控制，不是车辆 policy | 可复用为 EnvironmentControl adapter；不接目标车策略 |
| `code/scripts/stage_0_5_execution_v2.py` | `NativeBackend.step()` L309–L314 | `connection.simulationStep()` | 仿真全局 | 执行管理器 | Step boundary | `collect_snapshot()` | 无 | SUMO 执行管理 | 可复用为 execution clock boundary |
| `code/scripts/stage_0_5_execution_v2.py` | `run_observation_loop()` L383–L410 | `before_step → step → observer.ingest → journal.append` | 仿真与身份观察 | `synthetic=False` 时 native backend；synthetic 时无过程 | Before/Step/After | `IdentityObserver`、collision/teleport getter | 无 P3 event IDs | 执行/观察循环 | 可封装为 P7 phase scheduler；不能充当策略 |
| `code/scripts/stage_0_5_native_capsule_v4.py` | runtime/capsule verification and launch binding L1–L323 | 不直接调用车辆 setter；校验 SUMO/TraCI/runtime/source binding、capsule context 和 live execution prerequisites | Linux native execution environment | exact proposal/capsule/runtime binding | Launch/Before execution | 返回 context/version/identity binding，不读策略输入 | 无 message/decision/command | 进程/运行环境控制，不是车辆 policy | 可复用为 provenance/runtime manifest boundary |
| `code/src/riskprop/stage_0_5_sumo.py` | `run_stage_0_5_no_message_baseline()` L2739–L2756 | `traci.simulationStep()` | 仿真全局 | no-message baseline | Step boundary | L2755–L2839 vehicle state/leader/gap | `communication_enabled=False` 等配置明确关闭 | 只读 Observer/no-message fixture | 可复用为 readback/measurement path |
| `code/src/riskprop/stage_0_5_sumo.py` | `run_stage_0_5_no_message_baseline()` L2758–L2839 | `getLeader/getSpeed/getAcceleration/getPosition/getLaneID` 等 | 车辆状态 | 观察 | After Step | 是；含 incarnation、leader identity、gap、TTC 输入 | 无 P3 controller chain | 原生状态读回/测量输入 | 可复用为 Execution/P4 source |
| `code/src/riskprop/stage_0_5_fixed_leader_traci.py` | `replay_trace_in_sumo()` L64–L79 | `vehicle.add`, `setSpeedMode(0)`, `setLaneChangeMode(0)`, `setSpeed`, `moveTo` | replay Leader | 历史 Leader 轨迹 | 初始化/Before Step/After Step | L73–L79 读位置、速度、lane、碰撞 | 无 | 轨迹回放 | 可复用为 replay adapter；不可证明消息消费 |
| `code/src/riskprop/stage_0_5_fixed_leader_follower_traci.py` | `run_joint_replay()` L107–L138 | `vehicletype.setLength/setTau/setMinGap`; `vehicle.add`; `setSpeedMode`; `setLaneChangeMode`; `setSpeed` | Leader/Follower | replay 初始化参数、历史初态 | 初始化 | L64–L88 `_state()` | 无 | 工程初始化/模型配置 | 只复用 readback/初始化封装 |
| `code/src/riskprop/stage_0_5_fixed_leader_follower_traci.py` | `run_joint_replay()` L153–L158 | `moveTo`, `setSpeed` | 初始 Leader/Follower | 历史轨迹初态 | After initial step | L159–L170 初始状态误差 | 无 | replay 初始化校准 | 不可作为 policy |
| `code/src/riskprop/stage_0_5_fixed_leader_follower_traci.py` | `run_joint_replay()` L209–L224 | `setSpeed("follower", -1.0)`；Leader `setSpeed` | Follower/Leader | Follower 释放给 SUMO；Leader 历史 speed | Before dynamic / Before Step | `_state()`、`_append_sample()` | 无 | Follower 原生 Krauss + Leader replay | 可复用为原生模型/执行对照；不能作为消息策略 |
| `code/src/riskprop/stage_0_5_fixed_leader_follower_traci.py` | `run_joint_replay()` L225–L231 | `simulationStep(target+offset)`；`moveTo("leader",...)` | 仿真/Leader | 历史 Leader 轨迹 | Step/After Step | L177–L205 读回速度、加速度、gap、碰撞 | 无 | joint replay | 可复用为 post-step capture |
| `code/src/riskprop/stage_0_5_leader_replay.py` | replay loop L339–L357 | `moveTo("leader",...)`; `setSpeed("leader",...)`; `simulationStep()` | Leader | 历史轨迹插值 | Before Step/After Step | L350–L357 读 Leader/Follower 轨迹 | 无 | 固定 Leader replay，Follower 原生 | 仅 replay/readback |
| `code/scripts/interaction_diagnostic_worker.py` | worker loop L65–L84 | `connection.lane.setMaxSpeed()` + `lane.getMaxSpeed()` | `main_2_*` lanes | `supply_pulse` 工程计划 | Before Step | L74–L81 读回 lane limit | 无 | 环境供给诊断 | 仅环境 adapter |
| `code/scripts/run_p2_task3_sumo_b_calibration_only.py` | `run_one()` L74–L86 | `slowDown`, `setSpeed`, `setSpeed(-1)` | source `s0` | CALIBRATION_ONLY controlled-B source pulse | After previous step / future interval | L56–L70 读全部状态 | 无 target policy；audit 明确 `formal_A_eligible=false` | 受限 source calibration | 不可用于 P7 target controller |
| `code/scripts/run_p2_task7_parameter_experiment.py` | worker L132–L147 | `slowDown`, `setSpeed`, `setSpeed(-1)` | configured source vehicle | 参数实验中的 source actuation | After Step / future interval | L111–L130 状态读回 | `native_target_setters=0` | source calibration/parameter experiment | 不可用于 target policy |
| `code/src/riskprop/stage_0_5_b12_worker.py` | worker L67–L112 | 无 vehicle setter；`simulationStep()` 和 getters | 车辆状态 | read-only plan | Step/After Step | `traci_vehicle_control=False` | 无 | 只读 B12 observer | 可复用观察，不可作命令边界 |
| `code/src/riskprop/stage_0_5_cd_worker.py` | worker L67–L110 | 无 vehicle setter；`simulationStep()` 和 getters | 车辆状态 | read-only plan | Step/After Step | `traci_vehicle_control=False` | 无 | 只读 CD observer | 可复用观察，不可作命令边界 |
| `code/src/riskprop/stage_0_5_lf_worker.py` | worker L67–L110 | 无 vehicle setter；`simulationStep()` 和 getters | 车辆状态 | read-only LF plan | Step/After Step | `traci_vehicle_control=False` | 无 | 只读 LF observer | 可复用观察，不可作命令边界 |

## 2. 关键调用关系

```text
run_stage_0_1 / _run_cell
  ├─ fixed cell/time condition
  ├─ vehicle.setAcceleration(source/target)
  ├─ simulationStep()
  ├─ vehicle getters → state/action/risk rows
  └─ protocol row (legacy lifecycle booleans)

stage_0_5_linux_controller_v4.main
  ├─ NativeBackend.start()
  ├─ run_observation_loop()
  │    ├─ NativeBackend.before_step() → lane.setMaxSpeed/getMaxSpeed
  │    ├─ NativeBackend.step() → simulationStep()
  │    └─ IdentityObserver.ingest/post-step journal
  └─ controller_receipt / identity_summary

run_joint_replay
  ├─ add + model configuration
  ├─ Leader setSpeed/moveTo
  ├─ Follower setSpeed(-1) → native SUMO control
  ├─ simulationStep
  └─ _state/_append_sample readback
```

这些调用关系没有 Message→Policy Input→Decision→Command 的真实生产边界。`controller_receipt.json` 是 Stage 0.5 执行/资源/身份回执，不能被解释为 P3 Controller Decision 或 Adoption receipt。

## 3. 执行时序事实

| 路径 | Before Step | `simulationStep` | After Step | 时序含义 |
|---|---|---|---|---|
| Stage 0.1 | 根据 `next_time` 设置 source/target acceleration | 推进 0.2 s | 读取 native time、车辆状态，再写 action/risk | `target_command` 是计划命令；`applied_acceleration` 是读回值。 |
| Linux Stage 0.5 | lane speed limit 设置并立即 readback | `NativeBackend.step()` | `IdentityObserver.ingest()`、collision/teleport 检查 | 供给控制和观察分开；没有车辆 policy。 |
| fixed replay | Leader speed/position 命令 | 按目标时间推进 | `getSpeed/getPosition/getAcceleration` | 轨迹重放与读回，不是消息策略。 |
| joint replay | Leader speed；Follower 已释放 native | `simulationStep(target+offset)` | Leader `moveTo` 后读取两车状态 | Leader 外部输入，Follower 原生跟驰。 |

P7 应保留 `native_timestamp`、`simulation_step`、`phase`、`sequence`、`clock_id`、`time_lower/time_upper` 和 `clock_mapping_version`。调用顺序可以记录为 `sequence`/`CALL_ORDER`，不应通过 epsilon 制造严格物理先后。

## 4. 真实策略边界审计结果

未发现：消息接收 API、payload validator、策略输入快照、policy inference/decision function、command builder、独立 safety filter、command ACK 或 command→execution 外键。因此：

`NO_EXISTING_MESSAGE_DRIVEN_TARGET_POLICY_IDENTIFIED`

Stage 0.1 的 `adopted_time` 只是 cell/time condition 的派生值；Stage 0.5 的 controller 是 SUMO 执行管理器；replay 是外部轨迹回放；no-message/B12/CD/LF 是 Observer。以上四类不能合并命名为自动控制器。

## 5. 状态读回位置

- Stage 0.1：`stage_0_1_sumo.py` L258–L285；车辆 ID、road/lane、position、speed、acceleration、leader/gap。
- Stage 0.5 Linux：`stage_0_5_execution_v2.py` L309–L314 调用 `collect_snapshot()`；`stage_0_5_identity_observation.py` L64–L120 维护 loaded/departed/active/arrived/teleport/Unknown。
- Stage 0.5 no-message：`stage_0_5_sumo.py` L2755–L2839；含 incarnation、leader identity、gap 和测量输入。
- Fixed replay：`stage_0_5_fixed_leader_traci.py` L73–L79；`stage_0_5_fixed_leader_follower_traci.py` L64–L88、L177–L205。

这些位置可提供 P7 的原始 readback，但需新增 execution sidecar 关联，不能从现有表反推 command 或 safety。
