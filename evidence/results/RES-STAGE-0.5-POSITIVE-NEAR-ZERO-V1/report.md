# AAD-0.5.4-B1.2-P：正近零速度清零的独立验证

日期：2026-10-19。结果：`RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1`。性质：`engineering_observability_and_admission_only` / `exploratory_diagnostic_only`，`scientific_claim_eligible=false`。

**实际取得 2 条正近零、非决策步清零边，七项独立准入条件完整，位移精确核验通过。** 结论仅限全新、无停车任务、无状态恢复/控制/特殊设备等覆盖的生命周期。不是一般停车上下文可观测性的证明，也不批准未来数值准入政策。**C/D 接入及 ABCD 主矩阵本轮仍禁止，未执行。**

## 1. 源码与可识别性审计

从 main `89ead7534e628ac151b39d4356c8b4dcb16a6d41` 开始，未修改旧测量实现或旧证据。固定官方 SUMO 1.26.0、源码 commit `fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3`；13 个具名源文件逐一 SHA 核对，包括 B1.2-N 已审计的 11 个文件，以及为原生制动探针设计新增的 `MSCFModel_Krauss.cpp`、`MSLane.cpp`。完整来源/行号见 `source_audit.json`。

依据：[MSVehicle.cpp](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/src/microsim/MSVehicle.cpp#L4644)、[MSCFModel.cpp](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/src/microsim/cfmodels/MSCFModel.cpp#L877)、[Krauss 停车速度](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/src/microsim/cfmodels/MSCFModel_Krauss.cpp#L101)。

完整条件是严格 `abs(u_pre)<NUMERICAL_EPS_SPEED`，并且 `myStopDist>POSITION_EPS` 或存在下一停车任务且当前 route iterator 等于下一停车任务 iterator。`NUMERICAL_EPS_SPEED=0.1*NUMERICAL_EPS*TS`，`NUMERICAL_EPS=.001`、`POSITION_EPS=.1` 职责不同；`TS=.05s` 时速度阈值 `5e-6m/s`。它是内部数值常数导出值，不是科学交通容差。

审计涵盖整个 `myStopDist` 引用集合和 `newStopDist` 别名：构造函数 1014 行为 doubleMax；1143/5829/5869/7409 行重置为 doubleMax；2149 行传给规划函数，2223 行别名默认 doubleMax，仅在 2620 行处理首个停车任务时赋有限值；7830 行置零属于状态恢复，明确排除。头文件私有成员/按值 getter 和两项 friend 类也核对，friend 源码无相关写入。不能只引用清零单行来证明上下文。

本轮采用受限充分证明：全新空网启动；单辆输入无 stop 任务；非循环且运行时逐帧相符的路线；无动态 stop/route 修改；无状态恢复；碰撞/teleport 均无；实际设备查询排除 elecHybrid、driverstate、rerouting、taxi、bluelight、toc、glosa、friction、stationfinder。该生命周期不能进入有限停车距离的赋值路径，因此 `myStopDist` 保持 doubleMax，第一 OR 分支独立为真。公开空 `getStops` 只是完整证明中的一个证据，不单独等价于私有停车距离。

调用顺序：非决策步延续步初公开加速度，得到 `u_pre=v0+a_start*h` → 条件近零清零 → TraCI 速度控制及电混合动力等后处理 → 最终带符号 `u_final` → `updateState/getDeltaPos` 积分 → 公开 `max(u_final,0)` 及相应公开加速度。本轮客户端数回读为 1，只读 worker 无车辆/信号 setter，输入和命令无 load-state/额外控制文件，实际设备状态与单线程 ballistic 配置均回读。

## 2. 冻结计划与确定性输入

独立计划 SHA：`38c469c7daf299ddd98bd1faa66ac03256a38f3db71b39542b979a56a4f1d74d`。在任何新 SUMO 交通运行前，先完成源码、合成/负面测试、来源角色与 SHA、胶囊和预算冻结；5 项共同冻结后依次运行，各一次，无重试或事后输入调整。

两个 100 m 单车道 edge、原生全红信号；每项一辆新车，初始速度 1 m/s。数值探针使用 Krauss、LC2013、sigma=0、decel/apparentDecel/emergencyDecel=20 m/s²，tau=1 s、minGap=2.5 m、accel=2.6 m/s²、maxSpeed=27.78 m/s、speedFactor=1、speedDev=0、sigmaStep=1 s、actionStepLength=.1 s、内步 .05 s、显式 ballistic、单线程、seed=20261019。这些参数仅构造数值分支，不是交通驾驶参数，不修改 C/D 设置。

基于 `Krauss::stopSpeed` 的 .1 s headway 和官方 ballistic 安全停车速度式，在运行前按名义周期末速度 w 构造净距离：`g=.1*(1+w)/2+w²/(2*20)`；再加源码 .001 m 数值项与显式 1 m 停车线偏移，依据生成网络实际 lane 长度确定初始前端位置。此解析式仅用于设计输入，不用于替代实际 `u_pre` 的观测重建，也不使用本轮位移。

| 变体 | 冻结名义 w（m/s） | 运行前职责 | 仿真时长 |
|---|---:|---|---:|
| P1 | 2e-6 | 正近零区间内部 | 2 s |
| P2 | 4.8e-6 | 接近阈值、严格下侧 | 2 s |
| P3 | 5e-6 | 名义边界；只按实际浮点候选分类 | 2 s |
| P4 | 5.2e-6 | 阈值附近上侧对照 | 2 s |
| P5 | 8e-6 | 阈值以上对照 | 2 s |

单 worker 上限 120 s，进程树 3 GiB，单项输出 1 GiB，执行窗口 1800 s，最多 5 项；共享错误/SHA/来源/身份/时钟/配置/控制/数值/资源错误停止余项，Not Observed 只允许继续原声明余项。不存在 C/D、主矩阵或校准入口。

## 3. 目标分支是否实际出现

五项均完成 2 s，无工程阻断；P1/P2 分别有 1 条目标 Exact Pass，P3/P4/P5 的目标状态为 Not Observed，同时观察到其数值对照。`completed_valid` 只表示该 worker 工程执行合规，不把没有目标边的变体写成目标验证通过。

以下均为实际边 0.10→0.15 s，步末读取 lastActionTime=0.05 s；它早于步初 0.10 s，年龄 .05 s，与 .1 s 决策周期一致，因此确为非决策步。

| 实际变体 | v0（m/s） | 步初 a（m/s²） | 观测重建 u_pre（m/s） | 公开终速（m/s） | 结论 |
|---|---:|---:|---:|---:|---|
| P1 | 0.5000009999999547 | -9.999980000000905 | 1.9999999094633125e-6 | 0 | 严格正且低于阈值，Exact Pass |
| P2 | 0.5000024000000003 | -9.999951999999993 | 4.800000000582116e-6 | 0 | 严格正且低于阈值，Exact Pass |
| P3 | 0.5000025000000158 | -9.999949999999684 | 5.00000003156309e-6 | 5.00000003156309e-6 | 实际略高于阈值，不清零 |
| P4 | 0.5000026000000115 | -9.999947999999769 | 5.200000023020124e-6 | 5.200000023020124e-6 | 高于阈值，不清零 |
| P5 | 0.5000039999999822 | -9.999920000000355 | 7.999999964480864e-6 | 7.999999964480864e-6 | 高于阈值，不清零 |

**运行中恰好等于阈值的候选仍为 Not Observed。** P3 的名义等号不能冒充实际等号；严格边界有独立解析测试，运行对照仅支持本表实际数值范围。不从负近零成功推定正近零成功。

## 4. 清零条件和位移是否独立核验

P1/P2 的七项链条分别留证：实际正区间候选、步初对齐的非决策身份、doubleMax 生命周期证明、无覆盖控制、实际公开终速 0、源码最终分支与精确位移、完整源/输入/配置 SHA。`target_edges.json` 包含每条边两端状态、incarnation、步初/步末加速度、lastActionTime、设备排除、生命周期证明、候选/阈值/最终速度、实际/预期位移及七项布尔资格。

上下文资格先由独立输入、源码和生命周期证据决定，终速只在随后核对；未用被核验位移选择清零。已独立确认 `u_final=0`，官方 `getDeltaPos` 进入最终速度非负分支，本边预期位移为 `.5*v0*.05`。对其他负最终候选仍使用步内停车截断公式，决策停车只做必要范围。

| 目标边 | 实际位移 m | 独立预期位移 m | 残差 m |
|---|---:|---:|---:|
| P1 | 0.012500024999994253 | 0.012500024999998869 | -4.616099169574284e-15 |
| P2 | 0.012500059999993596 | 0.012500060000000007 | -6.411537967210279e-15 |

`1e-6 m` 容差原样保留。该容差**本身不足以区分近零两种速度替代**：在本步长下，即使 u_pre 接近阈值，两种预测位移之差也可能仅约 `1.25e-7 m`。因此本轮没有以残差较小来反推分支，必须同时具备上下文充分证明及独立公开终速检查。目标公开终速要求严格等于 0，不能只用既有辅助速度容差代替。

## 5. 数值分类与执行结果

| 统计口径 | 本轮实测 |
|---|---:|
| 相邻观测边 | 195 |
| 一般精确核验 / 通过 | 192 / 192 |
| 其中无需后处理识别 | 190 |
| 其中独立后处理正近零目标 Exact Pass | 2 |
| Bounded Consistency Only | 3 |
| Near-Zero Context Unresolved | 0 |
| Not Evaluable | 0 |
| Engineering Blocker | 0 |

三个 bounded 是决策步停车，残差为 null，不计 Exact。普通精确边不能充作正近零目标；目标分类另有 `Not Target Branch` 描述非目标边。源代码/生命周期受限证明不能外推成一般停车任务可识别，0 个未决观测不代表一般上下文已解决。

各项车辆均实际进入，2 s 末 1 辆仍在道路内等待红灯，驶出 0；全网身份集合和计数守恒残差均 0。没有队列、回溢或交通机制结论。每 .05 s 的完整状态、逐边 JSONL、SUMO 日志/配置/访问审计保存在 `code/outputs/formal/calibration/stage_0_5_positive_near_zero_v1`；Git 仅保存轻量证据、可还原微型输入和源码/原始输出哈希。

## 6. 剩余缺口、调试构建与权限

本轮受限目标不存在运行覆盖、可观测性或数值一致性缺口，`target_branch_verified=true`。一般停车上下文、动态路线/stop 修改、状态恢复、碰撞任务和特殊控制不在该资格内，仍未验证。运行精确阈值等号也未覆盖。

**该受限正分支无需研究者另批调试构建即可独立验证。** 如果未来确需一般私有上下文，才建议另立任务评估 pinned-source 的独立插桩二进制，记录清零前后候选和 stopDist；成本尚未测量，涉及 MSVC/CMake 依赖、可复现构建、编译选项/浮点行为及与官方二进制等价性审计。私有仪器化改变执行文件，不能假定无侵入；本轮没有构建、替换或启动此路径。

| 研究者决策项 | 本轮状态 | 后续职责 |
|---|---|---|
| 受限正近零分支 | 2 条运行级 Exact Pass | 可作为新的独立数值证据审阅 |
| 未来分层准入政策 | 未批准 | 明确来源限定精确、bounded、未知上下文的空间/时间/结论依赖职责 |
| C/D 接入 | 本轮禁止、0 次 | 另行授权与新冻结计划；C 队列/入口、D 换道/路径/出口分别验证 |
| ABCD 主矩阵 | 本轮禁止、0 次 | 完成剩余接入前置后再独立审批 |
| 调试构建 | 本轮不需要、未执行 | 一般上下文若确有必要，另批可行性/预算/侵入性协议 |
| 正式校准/科学容差/局部 P2 | 未就绪 | 仍需稳定可测交通状态、需求和测量归属协议 |

成功不追溯修改 B1.2-N `integration_allowed=false`，不修改旧 B1.2 阻断、`B1_2_MAIN_MATRIX_ALLOWED=false` 或历史主矩阵 0/8。B0 隔离不接受/验证物化 Unknown、B1 C 工程阻断与 D 未运行、B1.1 Pending Numerical Equivalence、B1.1-S 947/948 全部保持不变。

## 7. 数据隔离、验证与最终停止点

只使用具名官方源码、B1.2-N 四项 SHA 绑定便携元数据、合成测试及新微型输入；没有第三验证窗口、holdout、历史全源事件、旧 C 完整状态或真实轨迹读取。沿用 `-S` 受控 Python 胶囊、角色白名单、负面拒绝探针、SHA 和进程监督。正常运行访问审计无意外拒绝，负面探针另留证；Python 审计不是 OS/native 绝对隔离证明。

冻结前 151 项受控定向回归通过，含新增 29 项独立分类/边界/错误/权限/只读控制测试；初始测试在实现前因模块缺失失败，然后实现并回归，全部输入与判据先于 SUMO 运行冻结。最终纯 Git 全量、compileall、严格文档及便携校验结果见 `test_record.json`；数据缺失 skip 不计科学通过。五项已有文献删除不处理，根目录严格检查的相关例外单独记录；全量 pytest 仅在无本地数据的纯 Git 克隆运行。

正式科研状态不变：`stage_0_5.gate=pending_simulation_sample`；`scientific_claim_eligible=false`、`ready_to_start_stage_0_5_4b=false`、`reality_coverage_accepted=false`、`protocol_lock_allowed=false`、`stage_1_1_allowed=false`；科学容差 `Tolerance Not Yet Justified`、ED real-real 上界 `Not Identifiable`、局部正式 P2 `Unresolved`。Context Consistency Check 同步当前任务、实现/数据流、模块、实验、有限授权与剩余问题；历史封存不变。**停在研究者决策节点。**

最终纯 Git 全量实测 **741 passed / 14 skipped / 0 failed**（119.38 s；snapshot `1b46e54483e8602afecf02c28fc323b3e471e985`）。14 项 skip 的文件、行号和原因逐项列于 `test_record.json`：13 项缺本地/密封数据，1 项专用胶囊职责（已由受控前检执行），均不计科学通过。纯克隆严格文档 `--strict-git --require-clean`、compileall、便携 SHA、2 目标/3 对照独立重算及 33 个冻结源码/测试文件 Git 字节绑定通过。根目录严格文档受任务开始前已有文献索引缺失影响，五项删除不暂存；根目录未运行全量 pytest。提交/推送后使用新的远端纯 Git 克隆复核，最终 SHA 与结果另留本地 post_commit_verification.json。
