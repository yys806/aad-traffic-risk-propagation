# 正式风险测量定义一致性核查（AAD-0.5-CLOSURE §六）

日期：2026-10-21。核查对象：正式研究决策记录、当前风险测量实现、版本化配置、验证测试、最新版论文正文。
任务要求：核实指数版风险映射是否已被正式批准为主定义；若已批准，统一实现、配置引用、测试与论文表述；历史线性版本可作为明确标记的历史基线。

## 1. 逐项核查

| 项 | 已批准定义（来源+日期） | 实现事实 | 配置事实 | 测试事实 | 论文事实 | 判定 |
|---|---|---|---|---|---|---|
| 连续风险映射 | `rho = exp(-TTC/tau)`，不以 P2 阈值截断（`AI_CONTEXT/06_DECISIONS.md` 2026-10-11 `Agreed Research Design`） | `code/src/riskprop/formal_risk_measurement.py:46-54` `rho_from_ttc` 返回 `exp(-value/tau)`，非有限/非正输入返回 `None` | `code/configs/stage_0_2_formal_risk_measurement_p2_v1.json` `"rho": {"formula": "exp(-TTC/tau)", ...}` | `code/tests/test_formal_risk_measurement.py::test_rho_and_status_bounds` 断言 `exp(-2.0/tau)`；本轮新增 `test_rho_is_the_approved_exponential_mapping_without_threshold_truncation` 断言单调性、无截断、且**不复现**线性映射 | `paper/主论文/main.tex` 原为阈值线性 `1 - TTC/θ`（仅当 `0<TTC<θ`）→ **已改为指数映射** | 记录/实现/配置/测试 **Consistent**；论文原为 **Conflict**，本轮已同步 |
| 时间尺度 τ | `tau = 15.364279197080283 s`（四来源可靠闭合 TTC 的来源内时间加权中位数的排序中间两源平均） | 默认参数 `P2_FORMAL_CONFIG.tau_s = 15.364279197080283` | 同值（`rho.tau_s`） | 由 `P2_FORMAL_CONFIG.tau_s` 驱动，无硬编码重复 | 已写入正文 | **Consistent** |
| 事件定义 | P2 = 可靠 `TTC<2.0 s`、连续观测首末跨度 `≥0.2 s`、确认时刻取实际观测帧 | `extract_formal_source_events`、`observed_confirmation_time` | `source_event: {ttc_threshold_s: 2.0, minimum_duration_s: 0.2, max_gap_s: 0.11}` | `test_online_confirmation_uses_observed_frame` 等 | 论文 TTC 与阈值定义未改 | **Consistent** |
| 未知/缺失贡献 | 不补零；未知归属或测量贡献取 `[0,1]` 上下界 | `contribution_bounds` 对 `missing`/`in_region=None` 返回 `(0.0, 1.0)` | `unknown_contribution_bounds: [0.0, 1.0]` | `test_rho_and_status_bounds` | 论文新增"未知贡献不补零，进入区间算术的 [0,1] 上下界" | **Consistent** |
| 聚合 | 固定目标车辆/边界/窗口、**车辆等权**（`AI_CONTEXT/06_DECISIONS.md` 2026-10-11） | `equal_vehicle_average` | — | `test_fixed_window_keeps_unknown_denominator_and_equal_vehicle_weight` | 论文原为 `J = Σ_v I_v`（求和）→ **已改为车辆等权平均** | 记录/实现/测试 **Consistent**；论文原为 **Conflict**，本轮已同步 |
| 分母 | 可靠且 P2 可评价跟驰暴露（2026-10-12 裁决） | `compute_exposure` / `formal_risk_measurement` 未改 | — | 既有测试 | 论文未定义 NGSIM 分母口径（属 Stage 0.2 范围，不冲突） | **Consistent**（无冲突项） |
| 线性版本归档 | 历史基线可保留但必须明确标记 | `code/src/riskprop/legacy/`、`code/scripts/legacy/` 中**无**可执行的线性风险映射（全仓库 grep 无命中） | — | — | 论文正文已把线性版本明确标记为"正式记录确认之前的历史基线/历史对照" | **Historical-only** |

## 2. 对既有冲突记录的核验

`AI_CONTEXT/07_KNOWN_ISSUES.md` 的「论文版本冲突 — Awaiting Researcher Decision」写道：*Documented Intent = 06_DECISIONS 指数 rho；Actual Implementation = formal v2 符合批准设计；旧 `main.tex:378-405` 仍为线性/观测分母/求和*。

核验结果：

- 「指数 rho 已被批准」——**成立**（2026-10-11 `Agreed Research Design` 与 2026-10-12 分母裁决两条记录）。
- 「formal v2 符合批准设计」——**成立**（实现/配置/测试三处一致，见 §1）。
- 「论文为线性」——**成立**，且不止措辞差异：是**映射形式**（阈值线性 vs 指数、截断 vs 不截断）与**聚合算子**（求和 vs 车辆等权）两处**实质性**冲突。
- 「观测分母」——该条在论文中未被定义，属 Stage 0.2 的分母口径，**不构成**论文级冲突；原记录把三项并列略显笼统，已在本轮一并澄清。

因此原冲突是**论文未同步**，而不是决策记录与实现之间的未决冲突。按任务书 §六.3，已按已批准定义同步论文，无需新的科研决策。

## 3. 本轮修改

1. `paper/主论文/main.tex`（第 386–406 行区块）：
   - 映射改为 `rho = exp(-TTC/tau)`，`tau = 15.364279197080283 s`，明确"不以事件阈值截断"。
   - 删除 `θ^{TTC}` 阈值分支（连同碰撞分支，因 `TTC→0 ⇒ rho→1` 已连续覆盖）。
   - 区域风险聚合由 `Σ_v I_v` 改为 `(1/|V^T|) Σ_v I_v`（车辆等权）。
   - 新增一段把原阈值线性映射明确标记为**历史基线**，并写明未知贡献进入 `[0,1]` 区间。
2. `code/tests/test_formal_risk_measurement.py`：新增 `test_rho_is_the_approved_exponential_mapping_without_threshold_truncation`。
3. 论文以 XeLaTeX 重新编译：9 页、0 错误；`pdftotext` 复核渲染结果含 `exp` 与 `15.364279197080283`。存在 1 处 overfull hbox（54 pt，第 392 行长段落），属排版问题，未改。

## 4. 结论

- **指数版风险映射已是正式批准的主定义**（不是 Proposal）。
- 实现、配置引用与验证测试**本来就一致**；不一致的只有论文表述，本轮已同步。
- 历史线性版本保留为**明确标记的历史基线**，仓库中无残留可执行实现。
- `AI_CONTEXT/07_KNOWN_ISSUES.md` 中该冲突项状态由 `Awaiting Researcher Decision` 改为 **Resolved（2026-10-21）**，并保留原记录作为历史。
