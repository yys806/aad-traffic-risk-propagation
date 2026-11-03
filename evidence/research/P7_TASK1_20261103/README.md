# AAD P7 Task1 便携证据包

- **Task ID:** `AAD-P7-TASK1-20261103`
- **日期:** 2026-11-03
- **性质:** 只读工程审计与集成方案；无 SUMO/TraCI 启动、无新 seed、无新轨迹、无 locked holdout 读取。
- **结论:** `NO_EXISTING_MESSAGE_DRIVEN_TARGET_POLICY_IDENTIFIED`
- **P3 schema:** `aad.p3.controller-evidence.v1`
- **Adoption boundary:** `aad.p3.policy-input-adoption.proposed.v0.1 / PROPOSED`

## 文件

| 文件 | 内容 |
|---|---|
| `source_manifest.json` | 审计源码清单、精确 SHA256、字节数、行号范围和职责。 |
| `control_path_matrix.json` | TraCI setter、simulationStep、环境控制、回放、Observer 和实际读回矩阵。 |
| `integration_mapping.json` | 六个 P3 接入点、14 类记录、P4 Action/Risk 映射、时序、ID 和 manifest 方案。 |
| `validation.json` | 本任务的静态验证、JSON 复算、Git/运行边界和状态保留。 |

## 关键可复核事实

审计清单共绑定 28 个源码文件。`code/src/riskprop/stage_0_1_sumo.py:L252-L256` 在 `next_time >= 2.2` 时直接设置 `adopted_time=2.2` 并调用目标车 `setAcceleration(-1.5, 0.2)`；没有真实 receiver、policy input 或 decision。
2. `code/scripts/stage_0_5_execution_v2.py:L316-L338` 的 `NativeBackend.before_step()` 只写/读车道最大速度；它是环境供给控制。
3. `code/src/riskprop/stage_0_5_fixed_leader_follower_traci.py:L209-L224` 在动态区间释放 Follower 给 SUMO 原生控制，只对 Leader 施加 replay speed。
4. `code/src/riskprop/stage_i_mechanism.py:L241-L339` 和 `code/scripts/run_task20_stagei_engineering_fixture.py:L48-L123` 生成的是显式工程 Fixture；Task20 不能证明真实控制器采用消息。
5. `code/src/riskprop/controller_evidence.py:L87-L119` 已提供 14 类 P3 记录；`L302-L629` 提供结构和关联验证，但当前没有真实 SUMO producer 调用。

## 使用边界

本包是源代码和既有接口审计，不是实验结果，不是 Formal P2/rho 证据，不是 Safety Layer 证明，也不是 Adoption 或因果作用证明。P7 Task2 必须先得到真实目标车辆策略和相关科研语义确认，再按 `docs/research/P7/P7_INTEGRATION_BLUEPRINT.md` 一次性接线。
