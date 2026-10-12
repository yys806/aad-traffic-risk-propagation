# Stage 0.2 最终科学验收与关闭记录（2026-10-12）

Stage 0.2 Gate=`pass`，阶段状态=`Completed / Closed`。本验收仅支持四个批准 NGSIM 来源在 100 ms 连续性语义下的纵向跟驰风险代理指标测量与描述性现实校准。

正式 P2 事件率分母为可靠且 P2 可评价跟驰暴露。可靠边两端均须为 `valid` 或 `not_applicable`，并满足来源、诊断时钟、车辆对、帧号、时间戳及连续性规则。`invalid/non_positive_gap` 与其他不可评价状态排除事件率分母，但所有状态和质量信息保留，排除不代表零风险。原可靠跟驰暴露仍独立报告，可靠闭合暴露也不与之混用。

四源事件数均与封存 P2=4,545 对齐。原可靠跟驰暴露512,043.2s；正式P2可评价暴露503,922.2s；不可评价暴露8,121.0s；可靠闭合暴露208,026.3s。逐源边级统计、事件率（events / P2-evaluable following vehicle-hour）、新旧分母率差异及测量状态见验收包 `p2_event_rates_by_source.csv`、`p2_event_rates.json`、`exposure_edge_audit.json`。每条相邻边权重0.1秒，无末帧外推或跨缺口累计。

验收支持可靠观测条件下代理事件频率和 rho/tau 描述性校准，不支持事故概率、真实危险识别准确率、P2全局最优性、SUMO迁移、AAD核心因果效应或来源外道路/总体交通外推。独立物理真实性、缺失引起的选择偏差、极端值敏感性、200 ms与100 ms不等价及来源外推仍为明确限制。后续阶段职责不因此完成。没有创建 Protocol Lock、运行 Stage I 或访问 locked holdout。此前 R3 Blocked 包保留为历史审计记录。

最终不可覆盖证据包：`code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r4/`。机器Gate报告为 `scientific_gate_report.json`，验收矩阵为 `scientific_gate_matrix.csv/json`。
