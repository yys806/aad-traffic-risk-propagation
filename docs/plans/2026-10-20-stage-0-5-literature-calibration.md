# 计划：基于文献证据的微观行为校准与条件交通场景诊断（AAD-0.5-LIT-CAL）

日期：2026-10-20。结果 `RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1`。

## 目标

回答「SUMO–Krauss 复现断面流量却不复现 US-101 拥堵」的错配来自微观跟驰行为、边界供给，还是二者共同作用；并把每个方法都绑定到经原文核验的文献。

## 阶段

| 阶段 | 内容 | 是否需要 SUMO | 产出 |
|---|---|---|---|
| P0 | 项目事实、日期与预算台账核对；文献核验与 Zotero 整理 | 否 | `doc/literature-notes/STAGE_0_5_METHOD_EVIDENCE_MAP.md`、`stage_0_5_method_index.json`、`.ris`、`budget_ledger_audit.json` |
| A1 | 状态识别阈值敏感性（绝对 / Duan `W<0.5` / Saberi `λ<ρ` / FHWA 1/3） | 否 | `jam_definition_rules.csv`、`jam_definition_sensitivity.json` |
| A2 | 逐时间片空间置换零模型（1000 次，种子冻结） | 否 | 同上（`null_*` 字段） |
| B1–B3 | 前车轨迹重放 + Brockfeld / Schrader 指标 + 分层报告 | **是（48 次微型运行）** | `replay_plan.json`、`replay_summary.json` |
| B4 | 预声明解释规则判定 | 否 | `replay_summary.json` |
| C | 条件下游供给 | 门控 | `phase_c_decision.json`（未执行） |

## 预算与停止规则

- B 阶段：2 窗口 × 12 对 × 2 配置 = 48 次独立 SUMO 进程调用（每次 ≤25 s 仿真），运行前写入 `replay_plan.json` 并 SHA 绑定。
- 不继承、不占用 `RES-STAGE-0.5-FINAL-CLOSURE-V1` 的 FR1/FR2 预留重复，也不占用 `RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1` 的 RC1r/RC2r。
- 停止条件：前车跟随偏差 > 0.25 m、SHA 不匹配、插入失败、观测前车缺失；不做 `tau` 搜索、不联合调 `minGap`、不按 P2 选样本。

## 硬边界

- 不修改 Stage 0.2 风险事件定义、身份/时钟/质量语义、分母。
- 不读取第三窗口 `us101__0820_0835` 或 locked holdout。
- 不写 Gate、不创建协议锁、不启动 Stage 1.1 / ABCD。
- 不把工程设定（27.78 m/s）当作实测自由流速度。

## 验证

```
python code/scripts/run_stage_0_5_method_diagnostics.py --phase both
python code/scripts/write_stage_0_5_method_index.py
python -m pytest tests/test_stage_0_5_jam_definition.py tests/test_stage_0_5_leader_replay.py -q
python code/scripts/validate_project_docs.py --strict-git
python code/scripts/export_project_evidence.py --repo-root .
python code/scripts/export_project_evidence.py --repo-root . --verify
```
