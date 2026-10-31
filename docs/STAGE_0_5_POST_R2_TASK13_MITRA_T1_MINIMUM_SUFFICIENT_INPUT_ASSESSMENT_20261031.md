# AAD-S0.5-POST-R2-TASK13：MiTra T1 最低充分真实性评估与 Task9 输入准备

日期：2026-10-31。基线：`2038e5acafb7593ebe69fd25336e0816e7cafb23`。状态：`COMPLETED_WITH_INPUT_REVIEW_CANDIDATES_AND_BLOCKERS`。

本任务只评估 Task12 已筛选的三个 MiTra T1_DAll 候选，判断其是否足以进入 Task9 输入审查。没有启动 SUMO/TraCI、Task9 正式实验、MP4 下载、tau 映射、Formal P2/D1/B 修改或 Stage 0.5 Gate 变更。

## 1. Fact：数据、日志和视频检查

Task12 的 `T1_DAll.ftlgx` 保持 SHA256 绑定，内部包含 6 个 `.tlgx` 成员。DataFromSky Viewer 在已检查的本机路径中未找到；官方 Viewer 下载入口已记录，但本任务没有安装 Viewer 或下载视频。[MiTra Readme](https://opara.zih.tu-dresden.de/bitstreams/48e0a468-c779-4f37-80aa-68bbeb1a8fd2/download)

没有获取 MP4，因此没有完成车辆 ID 到具体视频、遮挡、ID switch 或像素级车辆几何核验。视频阻塞被作为独立限制记录，不把它反向解释成轨迹必然不可信。

## 2. Observation：三个候选的最低充分性检查

三个候选均满足：

- reciprocal `Leader_ID`/`Follower_ID` 关系为 1.0；
- 同车道关系为 1.0；
- 采样间隔约 0.033367 s，未发现超过 0.05 s 的长间隔；
- 持续时间均超过 45 s；
- 局部航向投影下前车顺序没有反转；
- 所有参考点敏感性区间内的 provisional 初始间距均为正；
- 速度和纵向加速度字段均为有限值。

代表性结果：

| 候选 | 时间范围 (s) | 持续 (s) | 初始 gap 中心假设 (m) | 参考点敏感性下界 (m) | 初始速度 follower/leader (km/h) | Task9 输入等级 |
|---|---:|---:|---:|---:|---:|---|
| 962-958-1 | 282.516–328.429 | 45.913 | 10.253 | 10.253 | 50.762 / 55.297 | `READY_FOR_TASK9_INPUT_REVIEW` |
| 926-924-1 | 268.502–315.082 | 46.580 | 4.859 | 4.859 | 60.458 / 63.440 | `READY_FOR_TASK9_INPUT_REVIEW` |
| 857-851-1 | 248.082–296.630 | 48.549 | 11.028 | 10.612 | 36.067 / 27.494 | `CONDITIONAL_WITH_SENSITIVITY` |

这里的 Level 1 只表示“可以提交研究者做 Task9 输入审查”，不表示正式输入已批准，也不表示独立物理真值已经建立。

## 3. Inference：参考点和间距近似是否改变实验解释

采用一个透明的共同归一化参考点敏感性模型：令两个车辆使用相同的车身参考比例 `alpha`，分别检查 rear (`alpha=0`)、center (`alpha=0.5`) 和 front (`alpha=1`) 三种情况。相应的间距区间为：

\[
g_{\mathrm{low}}=\min(s_l-s_f-L_f,\;s_l-s_f-L_l),\qquad
g_{\mathrm{high}}=\max(s_l-s_f-L_f,\;s_l-s_f-L_l).
\]

结果显示：

- `962-958-1` 和 `926-924-1` 的车辆长度相同，参考点敏感性不改变间距值；
- `857-851-1` 的初始间距区间约为 10.612–11.445 m，区间宽度约 0.83 m；
- 三个候选在整个共同参考点区间内均没有非正初始间距，也没有车辆顺序反转。

因此，在“近似 Task9 输入”这一有限目的下，参考点不确定性没有改变候选的前后关系或初始间距正负判断。它仍然不能被写成精确物理净距，也不能替代视频和独立标定。

三个候选的速度、加速度和闭合速度分布已写入 `candidate_evaluation.csv`。例如，`926-924-1` 的纵向加速度范围约为 follower `-4.33–1.28 m/s²`、leader `-4.45–1.08 m/s²`；`962-958-1` 的对应范围约为 follower `-1.30–1.38 m/s²`、leader `-0.91–1.05 m/s²`。本报告不引入新的“合理加速度阈值”。

## 4. Task9 输入兼容性

三个候选都能提供：

- 前车位置和速度序列；
- 后车初始速度；
- 车辆长度和车道字段；
- 统一的 30 Hz 时间轴；
- 超过 45 s 的连续观测窗口。

对每个候选都进行了 30 Hz 到 0.05 s 的线性速度重采样回插诊断。最高排名候选的误差为中位数约 `0.000274 m/s`、95 分位约 `0.002431 m/s`、最大约 `0.011640 m/s`；三个候选的逐段结果保存在 `input_coverage.csv`。这只是可复现的数值可行性诊断，不是正式插值规则。

Task9 的两臂仍必须使用同一前车输入、同一时间锚、同一后车初始状态和同一物理初始间距。当前任务没有生成正式输入文件，也没有进行时间平移或事后筛选修复。

MiTra `Vehicle_type` 与 B00 五档异质 tau 的映射仍为 `Unknown`。这不影响当前候选数据的最低充分性判断，但会影响正式 Task9 输入配置，必须由研究者单独决定，不能在本任务中自行分配。

## 5. Proposal：下一步最小路径

建议将以下两个候选提交研究者进行 Task9 输入审查：

1. **962-958-1**：优先。间距下界约 9.86 m，速度和加速度变化较平稳，持续 45.9 s。
2. **926-924-1**：次选。间距下界约 4.86 m，连续 46.6 s，但闭合速度上尾更高，应在审查时保留这一观察。

`857-851-1` 作为条件备用候选；它持续时间最长，但速度和间距变化更宽，参考点敏感性也更明显。

研究者若接受“最低充分真实性”路线，下一步只需审查上述候选的输入语义、参考点区间处理和车辆类型映射，不需要重新遍历全部 4,335 个候选段，也不需要下载完整视频归档。正式 Task9 运行仍须另行批准。

## 6. Unknown 与科研边界

- 没有视频，因此身份切换、遮挡和实际视觉前后关系仍 Unknown；
- `.ftlgx` 已获取但未解码，候选 ID 到 MP4 仍 Unknown；
- x/y 的车辆参考点和正式道路 `s` 仍 Unknown；
- provisional gap 不是独立物理净距真值；
- MiTra 不能因此提供 NGSIM 40 条 source→target 候选的直接物理路径见证；
- 近似 Task9 输入可用不等于物理传播路径、到达时间或 AAD 核心假设得到证明。

最终状态保持：Stage 0.5 `blocked`；scientific equivalence `false`；Task9 formal runs `0`；Round3、Stage 0.6、Protocol Lock、Stage I 未启动。

机器证据：`evidence/results/RES-STAGE-0.5-POST-R2-TASK13-MITRA-T1-MINIMUM-SUFFICIENT-INPUT-ASSESSMENT-20261031/`。新增脚本：`code/scripts/audit_stage_0_5_task13_mitra_minimum_sufficient.py`。
