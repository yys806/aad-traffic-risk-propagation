# Stage 0.2 任务 2.3｜NGSIM 风险测量质量与稳健性综合收口

日期：2026-10-11。输入仅使用任务 1.5 四个 calibration state、任务 2.1 固定 447 案例和任务 2.2.1 r9；未访问 locked holdout。

## 完成内容

### A. 工程正确性

统一风险段提取为 `extract_risk_runs()`：只有当前帧和前一帧都满足风险条件，并且时间、Frame_ID、诊断时钟和身份边界连续时才合并。独立参考实现对 960 组固定随机掩码/边界组合逐段比较，风险帧数、段数和首末索引一致。447 个中心帧全部通过原始行号、Global_Time、Frame_ID、后车轨迹和前车轨迹唯一定位；未使用最近时间替代。

PDF 图册按目标 follower–leader pair 分别绘制，断点两侧数据均保留，仅禁止跨断点连线。

与 r9 对照：447 个案例连续性分类变化 0，风险帧和最长段统计变化 0；中心匹配为 unique=447。

### B. 全量质量诊断

四源合计 5,706,252 条状态、2,211,378 条有效 TTC、5,141,510 条前车匹配状态、8,543 条 follower 轨迹、17,866 个车辆对。全量状态中 invalid=81,547、missing=564,742、not_applicable=2,848,585；非正净间距 81,547 条。TTC<0.5 s 为 2,485 帧，DRAC>10 m/s² 为 1,170 帧；探索性极端标记（含 TTC/DRAC/净间距条件）106,680 帧。按轨迹内位置差分与记录速度的探索性偏差>5 m/s 共 9,869 帧，不能直接解释为数据错误。

447 案例维度标签中：formula_check=pass 447，leader_match_check=pass 447，center_match_status=unique 447，observation_continuity 仅对存在边界的案例 flagged；kinematic_consistency=pass 322、flagged 125；geometry_check 与 physical_truth_status 均保持 unverified。

### C. 风险事件稳健性

机器基线核对为 5,381 个候选事件。按完整 state 重新以 TTC<2 s/0.1 s 连续段重提取的 S0 为 5,880 个，较基线多 499 个；差异按源为 Lankershim +329、US-101 0750 +40、0805 +55、0820 +75。差异已保留，未通过改阈值或删除记录追平；`event_correspondence.csv` 明确标注正式事件 ID 对应关系因实现规则差异为 Unverified，需要研究者决定是否复用正式事件提取器作为后续敏感性入口。

S1（已有身份、匹配、连续性和数学适用条件）在本工程重提取中与 S0 相同。S2 是探索性压力测试：屏蔽 TTC<0.5 s、DRAC>10 m/s² 或净间距<1 m 的标记帧后，从完整序列重新切段，风险帧由 40,989 降至 36,933，事件由 5,880 降至 5,772，车辆对由 3,590 降至 3,543。S2 不是正式排除规则，不能据此删除原始观测。

事件极值与车辆对的精确一一对应仍受 S0 与正式提取器规则差异限制，报告保留为 Unverified；当前能确认的是压力测试对事件数量和风险帧数量有可量化影响。

### D. 决策材料与人工复核包

复用 r9 的 48 个代表性案例，补充逐维度质量标签、精确中心定位和风险段字段；四源各 12 个，保留 Lankershim 行 31,245，人工判断字段保持空白。新增 `scientific_decision_matrix.csv`，列出 TTC 阈值、DRAC 联合条件、持续时间、进出规则、滞回、去重、极端值处理、暴露分母、跨源适用性和 SUMO 校准统计量等待研究者决定事项，所有备选均标为 Proposal/Decision Required。

## 工程准备度

已完成：风险段 oracle、447 案例精确中心核验、全量四源质量分母、探索性 S0/S1/S2 重分段、事件差异保留、48 案例图册与空白模板、config/audit/provenance/manifest/SHA-256。

未完成：正式候选事件提取器与本轮独立重提取的规则等价性尚未证明；几何物理真实性和人工真实性判断仍未完成。

## 科学准备度与未决事项

现有证据支持描述性校准参考：状态质量分母、有效 TTC 比例、风险指标分布、连续段形态和源内覆盖范围。它不支持把极端值自动定义为错误、把候选事件称为真实事故、冻结正式阈值/持续时间/去重规则、确定最终暴露分母或解释跨源差异为道路类型因果效应。

## 产物

独立目录：`code/outputs/formal/calibration/stage_0_2_task_2_3_20261011_r3/`。

包含 `case_diagnostics.csv`、`run_consistency_audit.csv`、`full_quality_summary.csv`、`risk_run_summary.csv`（由案例风险段字段提供）、`event_robustness.csv`、`event_correspondence.csv`、`exposure_candidates.csv`、`representative_cases.csv`、`coverage_matrix.csv`、`representative_casebook.pdf`、`scientific_decision_matrix.csv`、`config.json`、`audit.json`、`provenance.json`、`manifest.json` 和 `SHA256SUMS`。

Protocol Lock、Stage 0.2 Scientific Gate 和 Stage I 均未启动。
