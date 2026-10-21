# 计划：Stage 0.5 条件性交通状态验证（AAD-0.5-CLOSURE）

日期：2026-10-21。结果 `RES-STAGE-0.5-STATE-SUPPORT-V1`。基线 `origin/main` = `f9b0e14`。

## 背景与前一轮的阻断层

`RES-STAGE-0.5-FINAL-CLOSURE-V1` 与 `RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1` 的判定为
`EvidenceInsufficient_StateSupport`：在观测几何 + 观测边界需求下 SUMO 落在**自由流支**
（`k≈21`、`v≈24`），而真实局部状态在**拥堵支**（`k=43.5/50.5`、`v=10.5/7.9`）；注入真实拥堵初始状态后
180 s 内完全退化；条件下游 3 车道限制则过度拥堵（`k=61.4`）。五层必要条件合取为
`Evidence Insufficient`（阻断层 1/2/5），δ 与 h 未获批。

## 本轮假设

| 编号 | 假设 | 判别对象 | 证伪条件 |
|---|---|---|---|
| H-A | 真实跟驰总体的等效时距约 1.55 s，冻结的 `tau=1.0` 使解析能力比观测最大块流量高约 44% | 时距比例估计 + 观测最大块流量（两条互不相同的证据） | 比例估计与流量上界给出的能力不一致 |
| H-B | 「抬 `tau` 有害」是分层子样本的产物，不是总体结论 | 全体可靠跟驰观测 vs 12 对分层样本 | 总体估计给出 `tau_eff < 1.0` |
| H-C | 给定证据派生的时距与一个声明的下游供给限制，SUMO 能落在真实观测的局部状态域内 | 状态域成员判据（含数据派生跨窗口基线） | 网格内任何格子都出域，或只在一个窗口成立 |
| H-D | 供给的**水平**决定平均状态，**形式**决定相对运动与风险事件生成 | 匹配解析能力下的限速 vs 车道缩减 | 两种形式在匹配能力下给出相同的动态与 P2 率 |
| H-E | 真实观测支持的状态域在时间上可迁移，但具体声明的供给值不可迁移 | 留出窗口 `us101__0820_0835` | 留出窗口出域，或其需求下同一供给仍成立 |

## 预先声明的设计

- **区域**：`[150,350) m × 车道 1–5`（沿用已批准 D1）。
- **供给轴**：下游 `main_2` 自由速度 `{27.78, 15, 12, 10, 8} m/s`，全部行为臂共用同一组值。
- **行为轴**：`B_frozen`（tau=1.0）、`B_mean`（tau=总比例估计）、`B_het`（每车 tau 取自真实每车分布分位）。
- **初始状态**：每个臂注入观测到的真实初始状态（含丢弃与钳制计数）。
- **数值**：内部 0.05 s、记录 0.1 s、420 s、单线程、无 teleport、SUMO 1.26.0。
- **评价窗**：`[300.0, 420.0)` s，写定于 `experiment_plan.json`。
- **判据**：状态域成员（合并域 + 另一窗口域覆盖率 ≥ 跨窗口基线）、机制相容（闭合速度闭合包络覆盖率 ≥ 同一基线 + 低速份额不超真实最大）、工程健全（0 teleport / 0 collision）。三者必要、不加权。
- **停止规则**：工程失败即停批；网格执行后不加格；只有通过两个校准窗口的组合做独立 seed 重复；留出窗口只在 `freeze_manifest.json` 写定后读取；车道缩减假设若在匹配能力下失败则不再尝试其他供给编码。
- **预算**：58 次真实轨迹生成运行（网格 30、独立 seed 20、结构 4、留出 4）。与 2026-10-20 冻结的"剩余 3 次"额度分属不同授权，不重复计算。

## 执行顺序（冻结前置）

1. `real-domain`（只读，无 SUMO）
2. `plan` → `experiment_plan.json` + `PLAN_SHA256`
3. `grid`（30）
4. `verdict`
5. `seeds`（20）
6. `structural` → `structural_plan.json` + `STRUCTURAL_PLAN_SHA256` → 4 次
7. `analysis`（从存盘轨迹重算机制指标，无 SUMO）
8. `freeze` → `freeze_manifest.json`
9. `temporal`（读留出窗口 + 4 次）

## 与任务书要求对应的证据位置

| 要求 | 位置 |
|---|---|
| 假设、比较对象、指标、停止条件、独立验证安排 | 本文件 + `experiment_plan.json` + `structural_plan.json` |
| 速度/密度/低速/相对运动/跟驰/时间动态 | `real_domain.json`、`grid_results.json`、`seed_repeats.json`、`structural_results.json`、`mechanism_analysis.json` |
| 断面流量不能单独证明状态匹配 | `local_state.json`（既有）+ 本轮判据不使用流量作为成员条件 |
| 不确定性分层 | `seed_repeats.json`（独立 seed）、`real_domain.json`（跨窗口基线） |
| 留出窗口独立性 | `freeze_manifest.json` → `temporal_validation.json` |
