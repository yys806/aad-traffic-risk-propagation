# AAD-S0.5-POST-R2-TASK14：MiTra T1 固定前车实验输入构建与配对工程预检

日期：2026-10-31。基线：`17ea4f0aa8e527502184ed2536c588ffaad27ce9`。状态：`ACTIVE_PREFLIGHT_COMPLETED_WITH_BLOCKERS`。

本任务已登记研究者 Agreed 决策 `AAD-S0.5-DEC-MINIMUM-SUFFICIENT-AUTHENTICITY-20261031`。该决策只适用于 Task9 真实输入适用性判断，不改变 Formal P2、D1、B witness、Scientific Equivalence 或 Stage 0.5 Gate。

## 1. 完成内容

已为 `962-958-1`、`926-924-1`、`857-851-1` 生成独立的原始片段 CSV 和 0.05 s 预处理 CSV，保存在 ignored staging 目录并通过机器清单记录 SHA256。原始 MiTra 数据未修改，完整原始时间范围仍保留在 raw 文件中。

已完成：

- 30 Hz 到 0.05 s 的线性/PCHIP 诊断；
- 局部航向纵向坐标构建；
- 初始速度和近似间距提取；
- 现有 B00/Round2 静态 arm audit；
- 三个候选的 common-leader/common-initial-state 配对预检；
- Vehicle_type 与 B00 tau 的决策材料；
- 独立 trace/readback 工程组件和 in-memory smoke test。

没有启动 SUMO/TraCI 或正式 Task9。

## 2. 时间重采样

三个候选原始采样间隔中位数均约 `0.033367 s`。线性插值与 PCHIP 的误差都很小，且没有速度过冲；为了保持方法简单、可复现，本次选择线性插值作为候选输入构建方法。

最高排名候选 `962-958-1` 的线性回插 leader speed 误差为：中位数约 `0.000076 m/s`、95 分位约 `0.000487 m/s`、最大约 `0.002715 m/s`。其它候选的诊断保存在 `resampling_diagnostics.json`。

固定 0.05 s 网格在原始片段末端留下小尾差：`962` 约 0.0126 s、`926` 约 0.0300 s、`857` 约 0.0486 s。完整原始时间仍在 raw 文件中；该尾差如何处理仍需在正式输入冻结前决定，不能通过隐式外推掩盖。

## 3. 局部坐标与网络容纳性

局部映射使用现有网络的 `main_0 → main_1 → main_2`，按候选车道索引选择对应 lane，起始 leader 局部位置设为 10 m。该映射只表达受控仿真的纵向运动，不是地理坐标恢复。

现有主线 route 长度为 `659.17 m`，而完整候选 leader 运动范围为：

| 候选 | leader 终点局部位置 (m) | 超出网络 (m) | 映射状态 |
|---|---:|---:|---|
| 962-958-1 | 761.84 | 102.67 | `BLOCKED_NETWORK_HORIZON` |
| 926-924-1 | 884.57 | 225.40 | `BLOCKED_NETWORK_HORIZON` |
| 857-851-1 | 828.02 | 168.85 | `BLOCKED_NETWORK_HORIZON` |

因此三个完整片段都不能直接放入当前 SUMO 网络。没有裁剪时间、循环坐标、修改路由或扩大网络。该阻塞会影响完整固定前车回放，属于真正的执行前工程问题。

## 4. 初始状态

| 候选 | follower speed (m/s) | leader speed (m/s) | approximate net gap (m) |
|---|---:|---:|---:|
| 962-958-1 | 14.101 | 15.360 | 10.253 |
| 926-924-1 | 16.794 | 17.622 | 4.859 |
| 857-851-1 | 10.019 | 7.637 | 11.028 |

间距仍是共同参考点假设下的近似值，不能写成独立物理净距真值。

## 5. A/B 配对公平性

现有 `audit_arm_configs` 通过：

- A/B 仅有五个 passenger vType 的 `minGap` 从 2.5→1.0 差异；
- network 和 `run.sumocfg` 字节一致；
- 五档 tau 保持原值：0.7389146577、1.0933428563、1.3877275661、1.8288599276、2.5614676647。

对三个候选，A/B 使用完全相同的 resampled leader position/speed、时间锚、follower 初始速度、leader 初始速度和 approximate gap 时，现有 `validate_common_input` 均通过。该结果是静态和数据级预检，不是 SUMO 执行结果。

## 6. 固定前车回放工程

原有 `stage_0_5_fixed_leader_pair.py` 是配置和配对数学契约，并不实现实际 TraCI 控制。本次新增 `stage_0_5_fixed_leader_replay.py`，提供：

- 0.05 s leader trace 校验；
- 逐步 apply/readback sink 接口；
- 输入与回读误差记录；
- deterministic in-memory smoke test。

当前环境中 `traci` 和 `sumolib` 均不可用，因此没有实现或测试真实 SUMO 控制，也没有把 in-memory 结果写成正式回放证据。当前 replay 状态为 `CONDITIONAL_ENGINEERING_ONLY`。

## 7. Vehicle_type 与 tau 决策材料

三个候选的 MiTra 类型为：

- `962-958-1`：Car / Car；
- `926-924-1`：Car / Car；
- `857-851-1`：Car / Medium Vehicle。

B00 五个 vType 均为 passenger，tau 代表现有异质跟驰设定。当前保留三种方案供研究者决定：

1. 保留既有 B00 异质分布，不从 MiTra Vehicle_type 推断 tau；这是最能保持原实验公平性的方案，建议优先审查。
2. 按 Vehicle_type 确定性映射 vType；会新增车辆类别到驾驶行为的假设。
3. 把 tau 作为独立因素；需要新的实验因子或矩阵，超出本任务授权。

Codex 没有选择 tau 映射，也没有改变 B00。

## 8. 执行前预检结论

三个候选均已具备可复现的局部输入包，common-input 配对检查通过；但正式执行资格全部为 `Blocked_by_network_horizon`，并且 tau 映射仍为 `Awaiting Researcher Decision`。因此当前不能把任何候选计入正式合格片段，也不能启动 6N 矩阵。

下一步需要研究者决定：

- 是否允许为完整候选提供足够长的受控 SUMO 路段/网络；
- 是否采用保留 B00 异质分布的 tau 方案；
- 如何处理固定 0.05 s 网格末端的小尾差。

这些决定完成前，保持 Task9 formal runs `0`。

## 9. 状态边界

**Fact：** 三个输入包已构建，重采样、初始状态、A/B common-input 和静态 arm 配置均有机器证据。

**Observation：** 当前网络不能容纳三个完整 leader 运动范围；实际 TraCI 回放尚未验证。

**Inference：** 输入构建已达到工程预检阶段，但完整固定前车实验仍受网络范围和 tau 决策约束。

**Proposal：** 优先审查 `962-958-1`，其次 `926-924-1`，`857-851-1` 保持备用；不在本任务中裁剪轨迹或改变网络。

Stage 0.5 继续 `blocked`，scientific equivalence 继续 `false`，Round3、Stage 0.6、Protocol Lock 和 Stage I 未启动。

机器证据：`evidence/results/RES-STAGE-0.5-POST-R2-TASK14-MITRA-TASK9-INPUT-PREFLIGHT-20261031/`。
