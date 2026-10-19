# AAD-0.5.4-B1.1-S：SUMO 步内停车分支的独立可观测性最小验证

结果：`RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1`。日期：2026-10-19。性质：有限、独立的停车分支可观测性验证；非交通机制矩阵、非校准、非现实覆盖验收。本任务不覆盖 B1.1 结果 `RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1`。

## 0. 结论摘要

已确证：**在自由/探针实例（无 TraCI 车辆控制）中，SUMO ballistic 步内停车的内部带符号候选终速 u 可被公开接口独立精确重建**，且不依赖被检查的位移。

- 决策步（`myActionStep=true`）与步内停车的组合仍**不可精确重建**（`u≤0` 被公开加速度钳制）；该分支被正确标记为 `Bounded Consistency Only`。
- **非决策步**（加速度延续步）满足 `u = v0 + a_pub_start·h`，**对任意符号精确成立**，包括 `u<0` 的真实步内停车。
- 三个微型运行共 948 条相邻边：**947 条精确可核验、全部通过**，最大绝对残差 `1.4210854715202004e-14 m`（远小于 `1e-6 m` 容差）；1 条为决策步停车，正确归为仅范围一致；0 条不可评价；0 条异常。
- **首次在真实 SUMO 中完成步内停车的独立精确位移核验**：0.05 s 例子中 `v0=0.1236955143419339`、延续 `a=−4.5`，重建 `u=−0.1013044856580661`，解析位移 `0.0017000644742637405 m` 与实测相差约 `6.45e-15 m`。

对照 B1.1：当时 2 条真实停车边只能做范围检查，`Pending Numerical Equivalence`。本次将**非决策步停车提升为精确可核验**，但**决策步停车仍保持 `Pending`**，未无条件放行全部停车测量。

## 1. 官方源码与接口的独立观测可行性

沿用 B1.1 固定官方版本 SUMO 1.26.0，commit `fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3`。源码只读审计，未重编译安装二进制。行号与 SHA 见 `official_observability_source_audit.json`、`official_source_manifest.json`。

| 官方位置（固定 commit） | 实现事实 |
|---|---|
| [MSVehicle.cpp executeMove，第 4569 行](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/src/microsim/MSVehicle.cpp#L4569) | 决策步：`vSafe=processLinkApproaches(...)`，再 `vNext=finalizeSpeed(...)`；非决策步：`vSafe=getSpeed()+ACCEL2SPEED(myAcceleration)`，`vNext` 不重算 |
| [MSVehicle.cpp updateState，第 4895 行](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/src/microsim/MSVehicle.cpp#L4895) | 第 4908 行 `myAcceleration=SPEED2ACCEL(MAX2(vNext,0)-v0)`；第 4935 行 `mySpeed=MAX2(vNext,0)` |
| [MSVehicle.cpp getDeltaPos，第 3658 行](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/src/microsim/MSVehicle.cpp#L3658) | ballistic：`u≥0` 时 `dx=(v0+u)/2·h`；`u<0` 时停车截断 `dx=-v0²/(2a)` |
| [MSVehicle.cpp checkActionStep，第 2072 行](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/src/microsim/MSVehicle.cpp#L2072) / [MSVehicle.h isActionStep，第 636 行](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/src/microsim/MSVehicle.h#L636) | 决策步时 `myLastActionTime=t`；`isActionStep(t)=(t-myLastActionTime)%actionStepLength==0` |
| [libsumo Vehicle.cpp，第 1039 行](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/src/libsumo/Vehicle.cpp#L1039) | `getLastActionTime` 返回 `STEPS2TIME(myLastActionTime)`；`getAcceleration` 返回 `myAcceleration` |

推论：内部候选终速 `u` **不等同于** TraCI 观测终速（`max(u,0)`）。位移使用的速度变量是内部 `vNext`，而对外的 `a_pub` 是被钳制的平均加速度。

## 2. `getLastActionTime` 语义与决策/非决策步分类

- `getLastActionTime()` 返回车辆**最近一次决策点**的时间（秒）。每次决策步时置为当前步时间；`depart` 时置为 `now+DELTA_T`；`actionStepLength` 变更时重排。
- 由实测轨迹确认**判定准则**：步 `[t_prev → t_now]` 为决策步 **当且仅当在 `t_now` 读到的 `lastActionTime` 等于 `t_prev`**（决策发生在步初）。
  - 例（0.05 s 步，`actionStepLength=0.1`）：7.10→7.15 步，`lastActionTime`(7.15)=7.05≠7.10 → **非决策步**；7.15→7.20 步，`lastActionTime`(7.20)=7.15=步初 → **决策步**。
- `actionStepLength` 与内部步长之比为整数（0.1/0.05=2、0.1/0.1=1），但这**不是**可重建性的充分条件；决定性限制是**对负 `u` 的钳制**。

## 3. 公开接口重建公式与可识别条件

设内部步长 `h`、步初公开速度 `v0`、步初公开加速度 `a_pub_start`（步初读数）、步末公开速度 `v1`、隐藏带符号候选终速 `u`。

**(a) 非决策步（加速度延续）**：源码 `vSafe=v0+a_pub_start·h`，`vNext` 不重算，且该步不触发钳制（`processTraCISpeedControl` 在无车辆控制时惰性）。故

\[
u = v_0 + a_{\mathrm{pub,start}}\,h
\]

**对任意符号精确成立**，包括 `u<0`（真实步内停车）。位移由官方公式独立计算：

\[
u\ge0:\ \Delta x=\tfrac{v_0+u}{2}h;\qquad u<0:\ \Delta x=-\frac{v_0^2}{2a},\quad a=\frac{u-v_0}{h}.
\]

**(b) 决策步**：`vNext` 经 `finalizeSpeed` 等隐藏处理；对外只保存 `a_pub=(max(u,0)-v0)/h` 与 `v1=max(u,0)`。
- `v1>0`：未触发钳制，`u=v1` **精确可观测**。
- `v1=0`：`u≤0` 被钳制，任意 `u≤0` 产生相同公开记录 → **仅可做范围检查** `0≤Δx≤½v0h`。

**(c) 静止→静止**（`v0=v1=0`）：位移恒为 `0`，与隐藏 `u` 无关 → **精确可核验** `Δx=0`。

**(d) 禁止项**：不得由被检位移反解 `u` 再验证该位移（循环论证）。模块中不存在此类 API（负向测试保证）。

分类为：`Exact Observable`、`Exact Reconstructable Under Verified Conditions`、`Bounded Consistency Only`、`Not Evaluable`。矩阵见 `stopping_identifiability_matrix.json`。

## 4. 微型实验与独立验证

沿用 B1/B1.1 受控胶囊、来源白名单、SHA 绑定与冻结计划。三个预声明微型运行，单车道 250 m，一辆合成车，Krauss，显式 ballistic，`threads=1`，seed 20261019，上限 30 s：

| 运行 | 内部步长 s | 场景 | 墙钟 s | 状态 |
|---|---:|---|---:|---|
| motion_005 | 0.05 | 自由运动（加速/巡航/减速） | 6.10 | completed_valid |
| stop_restart_005 | 0.05 | 常规停车 3 s 后重启（跨越 dt/dt2） | 5.53 | completed_valid |
| stop_restart_010 | 0.1 | 常规停车 3 s 后重启（步长=actionStep） | 4.60 | completed_valid |

计划 SHA：`303dec464438eac4c3ad7c0f9a1096e9e692c6bb0101ba654a58f6e48847709c`。版本 `b11s-observability-v2`。完整 SHA 见 `experiment_plan.json`、`provenance.json`。胶囊预检 79 项通过（含 B1/B1.1 合成回归与本次可观测性测试）。

## 5. 停车分支精确/范围/不可评价统计

| 运行 | 相邻边 | 精确核验 | 精确通过 | 仅范围 | 不可评价 | 异常 |
|---|---:|---:|---:|---:|---:|---:|
| motion_005 | 236 | 236 | 236 | 0 | 0 | 0 |
| stop_restart_005 | 483 | 483 | 483 | 0 | 0 | 0 |
| stop_restart_010 | 229 | 228 | 228 | 1 | 0 | 0 |
| **合计** | **948** | **947** | **947** | **1** | **0** | **0** |

- 最大绝对残差 `1.4210854715202004e-14 m`；精确适用比例 `947/948=99.8945%`；**精确通过比例（仅在可核验边上计算）= 100%**（`1.0`）。二者严格区分，不把适用范围写成通过率。
- `stop_restart_005` 的步内停车边：`t=7.10→7.15`，`v0=0.1236955143419339`，延续 `a=−4.5`，重建 `u=−0.1013044856580661<0`，解析 `dx=0.0017000644742637405 m`，实测 `dx=0.0017000644742637405 m`，残差 `6.45e-15 m`。
- `stop_restart_010` 的停车步：`h=0.1=actionStep`，故停车步**必为决策步**，`v0=0.3486955143419754`、实测 `dx=0.0135098401913609 m`，范围 `[0, 0.0174347757170988]` → 正确归为 `Bounded Consistency Only`，未伪称精确。
- 未出现 edge/lane 转换或身份/时钟不连续（本次为单 edge、单车道），故 `Not Evaluable` 为 0；该分类在 B1.1 已有覆盖并在本次单元测试中保留。

## 6. 调试观测可行性

判定为 **`Not Attempted`**：官方无直接输出内部带符号 `vNext` 的参数或日志；一般决策步停车的精确重建需重编译大型工程，成本高且当前资源不适用。本次公开接口已足以覆盖非决策步全分支与决策步正终速，故不启动调试构建。详见 `debug_feasibility_audit.json`。

## 7. 非侵入性核查

未创建、未使用任何修改版 SUMO 构建，未覆盖官方二进制。所有运行仅通过 TraCI 公开读接口观测，`myInfluencer` 为空（自由/探针实例），未使用 `setSpeed`/`setAcceleration` 等控制。因此不存在“调试输出是否改变被研究过程”的对照需求。详见 `non_intrusiveness_audit.json`（状态 `Not Applicable`）。

## 8. 数值误差与异常边

- 全部精确边残差量级 `~1e-14 m`，为 C++ 求值顺序导致的浮点末位差异，非物理或公式误差。
- 异常计数 0；范围越界 0。
- 修正过程中发现并留痕一处**测量契约缺陷**：初版以 `isActionStep(t_now, lastActionTime)` 判决策步、并误用步末 `a_pub`，导致 40 条非决策步停车被误标 bounded。修正为“步初对齐判决策步 + 步初 `a_pub`”后，非决策步停车精确通过。该缺陷批次已归档为 `stage_0_5_stopping_observability_v1_discarded_defective_measurement`、`..._v2_finalize_entry_fix_intermediate`，不进入 Git 便携证据，也不覆盖任何历史结果。

## 9. 方案 A/B 准入比较

| 方案 | 要求 | 优点 | 限制 | 当前可行 |
|---|---|---|---|---|
| A 严格精确准入 | 每条停车边均可独立精确重建 | 证据最强；数值/物理分离彻底 | 决策步停车需调试构建；工程依赖与环境绑定 | 否（需另批调试任务） |
| B 分层准入 | 常规/非决策步精确；决策步停车范围；不连续不可评价；预声明异常阻断 | 显式保留观测不确定性；解锁 B1.2 工程；无循环推断 | 不能宣称全部停车边精确等价；需预批准不可精确比例与停止策略 | 是（需研究者批准） |

推荐：**方案 B 是可辩护的工程路径，前提是研究者预先批准 bounded/not-evaluable 政策**；方案 A 作为独立授权的调试任务保留。Codex 不单方面批准方案 B。见 `numerical_admission_options.json`。

## 10. B1.2 前置条件

- 数值停车：非决策步精确 `true`；决策步停车精确 `false`、范围 `true`；状态 `Pending Researcher Admission Policy`。
- 队列契约：B1.1 候选软件已测，阈值仍需科研批准。
- 数据隔离：受控 Python 胶囊，非完整 OS 监控。
- **B1.2 未授权**，需研究者另批网络/供给/seed/时长/矩阵/预算/停止条件。

## 11. 研究者决策矩阵

| 决策项 | 现状与依据 | 推荐 | 需研究者决定 |
|---|---|---|---|
| 停车数值准入政策 | 非决策步精确、决策步 bounded 已独立验证 | 采用分层准入（方案 B） | 批准/拒绝；是否要求方案 A |
| 决策步停车处理 | `v1=0` 决策步不可重建 | 仅范围检查并明确标注 | 接受范围一致性还是视为阻断 |
| 不可评价状态 | 单 edge 未出现；B1.1 已覆盖 | 按未来场景预声明 warning/blocker | 分级规则 |
| B1.2 是否受精确停车阻塞 | 非决策步已精确覆盖 | 不阻塞；但决策步停车结论敏感性需评估 | 批准 B1.2 或先做调试观测 |
| 队列契约接入 | B1.1 候选已测 | 接入前需接入级验证 | 阈值与接入要求 |
| 额外实验 | 本次 3 运行已达预算 | 不追加 | 是否授权调试构建 |

## 12. 验证、复核与证据职责

- 胶囊预检 79 项通过；可观测性模块单元测试 12 项通过；便携包正负 8 项通过。
- 纯 Git 克隆全量回归与文档/证据检查结果见 `test_record.json` 与最终验证章节；缺本地真实数据的 skip 不计为科学验证通过。
- 便携复核命令（只读 Git 工程证据，不读本机交通数据）：

```powershell
python code/scripts/verify_stage_0_5_observability_evidence.py evidence/results/RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1 --repo-root .
python code/scripts/export_project_evidence.py --repo-root . --verify
python code/scripts/validate_project_docs.py --strict-git --require-clean
```

- 完整微型状态与官方源码保留在本地正式输出目录；Git 仅存小型输入 bundle、协议、矩阵、对照表、测试记录、manifest 与 SHA。
- 历史状态永久保留：B0 任务级隔离 `false`／验证物化 `Unknown`；旧 B1 C `completed_with_engineering_blocker`；旧 B1 D `not_attempted`；B1.1 `Pending Numerical Equivalence` 记录不变。
- 正式状态保持：`stage_0_5.gate=pending_simulation_sample`、`scientific_claim_eligible=false`、`ready_to_start_stage_0_5_4b=false`、`reality_coverage_accepted=false`、`protocol_lock_allowed=false`、`stage_1_1_allowed=false`；容差 `Tolerance Not Yet Justified`；Energy Distance 上界 `Not Identifiable`；局部/分层 P2 `Unresolved`。未修改 Stage 0.2 TTC/P2；未启动 B1.2、正式校准、Stage 0.5.5 或 Stage I/II。