# Stage 0.3 最终科学验收与正式关闭（AAD-0.3.3）

> 日期：2026-10-16（Asia/Shanghai）。结果 ID：`RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3`。
> 正式关闭包：`code/outputs/formal/calibration/stage_0_3_scientific_acceptance_20261016_r3/`（不可覆盖，SHA256SUMS 校验通过）。
> 决策归档：`AI_CONTEXT/06_DECISIONS.md` 2026-10-16 条目（任务 AAD-0.3.3，研究者批准）。
> 本文件是导航与解释摘要；数值以包内 audit/config/decisions/scientific_gate_report 与 SHA256SUMS 为准。R1/R2 历史包保留不覆盖。

## 0. 结论

- **Stage 0.3 Scientific Gate = `pass`；Stage Status = `Completed / Closed`**（研究者 2026-10-16 批准，任务 AAD-0.3.3）。
- 关闭范围：单一批准文件 `dataset/pNEUMA/20181101_d1_0800_0830.csv` 实际观测车辆的描述性城市运动学校准（速度、纵向加速度、车型组成）。
- 统计与 R2 完全一致（本包不重跑全量管线，只做 fail-closed 复核）：785 唯一轨迹 / 1,239,475 状态 / 时间戳 [38.40, 888.00] s / 可靠暴露 49,547.6 vehicle-seconds；速度时间加权 mean=4.838218 m/s、车辆等权 mean=6.207738 m/s；纵向加速度 mean=-0.004410 m/s²（sd=0.745368）。
- 独立复算 discrepancies=0；R2 checksum 重验通过。

## 1. 五项研究者决定（已归档并落实）

| # | 决定 | 内容 | 批准依据 |
|---|---|---|---|
| D1 | 正式适用范围 | 仅当前文件实际观测车辆的描述性城市运动学参考；不宣称完整 30 分钟连续观测，不代表雅典或城市总体，不推断时间字段绝对原点 | R2 审计：785 轨迹、1,239,475 状态、[38.40, 888.00] s、暴露 49,547.6 vehicle-seconds、原始顺序/身份/质量审计通过 |
| D2 | 时间连续性规则 | `0 < Δt ≤ 0.043 s` 升格为正式科学参数（仅当前 25 Hz 文件）；保持 R2 原始记录顺序、身份、解析质量与 fail-closed；不插值、不补帧、不跨缺口计权 | R2 原始顺序审计零异常 + 封存的 8 容差敏感性历史 |
| D3 | 极端运动学观测 | 原始保留、异常标记、敏感性对照；不自动删除；`|a|>2`、`|a|>5 m/s²` 仅探索性诊断阈值；物理真实性保持 `Unverified` | R2 极端敏感性已封存 |
| D4 | 描述性分类阈值 | 低速、近静止、近零加速度阈值保留为统计描述，不批准为正式风险分类或质量排除标准 | R2 状态份额表 |
| D5 | Scientific Gate | `pass` / `Completed / Closed`（沿用现有状态编码）；仅限当前单文件有限描述性校准 | 全部验收矩阵项 + 独立复算 |

## 2. 关闭包核验（fail-closed，全部通过）

- R2 包 32 文件 SHA256SUMS 重算一致，无未封存文件。
- 源文件 SHA-256 钉扎一致（`F9CDE0A3…28C`）。
- 计数/范围/资格：785/785/785、1,239,475、[38.40, 888.00] s、eligible 1,238,690。
- 统计不变性：速度 TW mean、VW mean、加速度 TW mean/sd 与 R2 逐值一致（<1e-9）。
- 独立复算 JSON `pass=true, discrepancies=0`。
- 详细检查项清单见包内 `scientific_gate_report.json → verification.r2_reverification_checks`（17 项全部 true）。

## 3. 验收矩阵

包内 `scientific_gate_matrix.csv/json` 共 11 项全部 `Verified`：决定归档、R2 证据完整性、来源不可变、计数与范围、原始顺序/身份/质量审计、连续性规则批准、极端观测处理、描述性阈值、统计不变性、有限适用范围、最终 Gate。

## 4. 科学适用范围（scope_and_claims.md 摘要）

- **允许**：本文件实际观测车辆的速度、纵向加速度、车型组成描述性参考；已批准连续性语义下的可靠暴露与分布统计。
- **禁止外推**：完整 30 分钟连续交通观测、雅典或任何城市总体交通、其他 pNEUMA 文件/数据集/采样率、事故概率、危险识别准确率、AAD 因果效应、SUMO 现实覆盖；不推断时间字段绝对原点。
- **永久限制**：独立物理真实性 `Unverified`；极端观测仅敏感性对照；车辆等权不代表城市车辆总体分布；Heavy Vehicle n=2 不作车型级推断。
- **后续归属**：车型→SUMO vType 映射、时间权重抽样设计与覆盖阈值属 Stage 0.5 独立待决；Protocol Lock 与 Stage I 不因本关闭解锁；locked holdout 不访问。

## 5. 历史链

| 产物 | 结果 ID | 状态 |
|---|---|---|
| R1 综合实施 | `RES-STAGE-0.3-PNEUMA-KINEMATICS-R1` | 历史证据，不覆盖 |
| R2 边界修复 | `RES-STAGE-0.3-BOUNDARY-REPAIR-R2` | 本包直接父证据，不覆盖 |
| R3 科学验收（本包） | `RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3` | 当前关闭包，不可覆盖 |

## 6. 验证与测试

- 关闭脚本：`code/scripts/finalize_stage_0_3_scientific_acceptance.py`（fail-closed，任何复核冲突即中止）。
- 全量 pytest 315 passed（含 project docs）；compileall 干净；`validate_project_docs.py --strict-git` 通过；便携证据导出与 `--verify` 通过（提交后复核）。
