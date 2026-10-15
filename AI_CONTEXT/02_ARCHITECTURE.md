# AAD Architecture

## 模型总体结构

当前不存在已实现的可训练模型架构。正式系统是一个分阶段的确定性科研工程管线：

```text
NGSIM -> 风险测量 -----+
pNEUMA -> 城市运动学 -+-> 仿真—现实覆盖 -> 数值验证/协议准入 -> 阶段 1.1（未实现）
SPMD -> 通信证据边界 -+
SUMO -> 四格与五表 ----+
```

因此当前“模型 forward、训练过程、loss、checkpoint”均为不适用或 `not_determined`，不能按常见深度学习项目补全。

## 主要模块

- 工程实验底座：`stage_0_1_sumo.py`、`formal_runner.py`、`formal_artifacts.py`、`formal_design.py`。
- 数据与测量：`calibration.py`、`real_trajectory.py`、`ngsim_risk_calibration.py`。
- 通信边界：`communication_observability.py`。
- 现实覆盖：`simulation_real_coverage.py`。
- 数值与准入：`prelock_metrics.py`、`prelock_validation.py`、`protocol_lock.py`。
- 项目一致性：`project_docs.py` 与 `code/scripts/export_project_evidence.py`。

## 模块输入输出

- 阶段 0.1 输入 SUMO 配置与固定 seed，输出每格封存目录、五表 Parquet、clock/lifecycle、audit、manifest、provenance 与 SHA256SUMS。
- 阶段 0.2 输入显式列出的 NGSIM calibration 窗口，输出标准化 state Parquet、合并后的 risk events 及封存元数据。
- 阶段 0.3 输入 pNEUMA 原始 CSV，输出解析审计、状态/轨迹统计、速度/加速度分布、敏感性、bootstrap、Stage 0.5 标准化参考与不可覆盖验收包。
- 阶段 0.4 输入 SPMD RV_RX 与访问状态，输出接收连续性 profile 和证据边界 audit。
- 阶段 0.5 输入 NGSIM state/events、pNEUMA 运动学 state 与 SUMO 样本，输出现实参考和 coverage gate。
- 阶段 0.6 输入解析/物理真值与前置 Gate，输出技术 audit、readiness，满足全部条件后才能写协议锁。

## 模块关系

`real_trajectory.py` 为 NGSIM/pNEUMA 读取层；`ngsim_risk_calibration.py` 调用 NGSIM 读取与 `calibration.py` 表契约；`simulation_real_coverage.py` 调用 `calibration.py` 的稳健缩放和 energy distance；`protocol_lock.py` 聚合阶段 0.2/0.4/0.5/0.6 Gate。阶段 0.3 的产物通过阶段 0.5 间接进入准入链。

## 重要配置

- 当前代码依赖：`code/pyproject.toml`。
- 阶段 0.1 环境证据：`code/environment/`。
- 原始数据与 split 清单生成：`calibration.build_default_calibration_manifests()`。
- 运行时冻结 config 位于各 `code/outputs/formal/**/config_frozen.json`，完整输出不进入 Git。
- `code/configs/feasibility_week_smoke.json` 属于历史 Pilot 配置，不是当前正式阶段配置。

## 关键代码位置

- `code/src/riskprop/stage_0_1_sumo.py::run_real_sumo_stage_0_1()`
- `code/src/riskprop/ngsim_risk_calibration.py::write_stage_0_2_ngsim_package()`
- `code/src/riskprop/real_trajectory.py::read_pneuma_wide()`
- `code/src/riskprop/communication_observability.py::build_stage_0_4_status_package()`
- `code/src/riskprop/simulation_real_coverage.py::evaluate_simulation_coverage()`
- `code/src/riskprop/prelock_validation.py::write_stage_0_6_prelock_validation()`
- `code/src/riskprop/protocol_lock.py::protocol_lock_readiness()` / `write_protocol_lock()`

### Formal Stage 0.2 risk measurement (2026-10-11)

`riskprop.formal_risk_measurement` is a versioned, isolated interface for approved P2 events, causal observed-frame confirmation, `rho=exp(-TTC/tau)`, bounded contribution semantics, fixed-window integration, equal-vehicle aggregation, and DID interval arithmetic. It does not alter historical `ngsim_risk_calibration.extract_rear_end_events` defaults or `prelock_metrics.integrated_ttc_exposure`.


## 2026-10-12 正式测量与收口接口

formal_risk_measurement.v2与历史0.1s提取/线性指标隔离；正式固定窗口原语需完整来源/时钟/双车身份与真实连续边，区域可靠性独立。 依据：相应源码及 `docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`。
