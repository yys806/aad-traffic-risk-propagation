# AAD 交通风险研究项目

本仓库研究车联网远端风险信息被控制器采用后，能否在普通物理影响到达目标区域以前改变目标车辆集合动作与目标区域总体风险。

当前仍处于 Stage I 主效应实验之前的测量、现实边界和协议锁定阶段。已有 E00/E15-A/E16-A/E17-A/E01 工程或校准证据，但所有现有结果均为 `scientific_claim_eligible=false`；`protocol_lock_allowed=false`、`e02_allowed=false`。当前唯一前进任务是由研究者完成 pNEUMA v5 的 48 条人工 Round 1 pilot。

## 第一次进入

1. [项目交接](PROJECT_CONTEXT.md)：当前 Gate、边界和精确继续点。
2. [协作规则](AGENTS.md)：人和 AI 的职责、停止规则、维护义务。
3. [重新上手路径](docs/LEARNING_PATH.md)：从研究问题到代码、实验和结果。
4. [项目总索引](docs/PROJECT_INDEX.md)：按问题查找。
5. [机器注册表](docs/PROJECT_REGISTRY.json)：实验—结果—历史的结构化事实源。

## 研究与证据入口

- 当前科研状态：[RESEARCH_STATUS](docs/RESEARCH_STATUS.md)
- 通俗方法与公式：[METHOD_AND_ALGORITHM_GUIDE](docs/METHOD_AND_ALGORITHM_GUIDE.md)
- 架构和证据流：[ARCHITECTURE](docs/ARCHITECTURE.md)
- 实验、结果、历史：[EXPERIMENT_INDEX](docs/EXPERIMENT_INDEX.md)、[RESULTS_INDEX](docs/RESULTS_INDEX.md)、[HISTORY_INDEX](docs/HISTORY_INDEX.md)
- Git 内便携证据：[evidence/README](evidence/README.md)
- 论文实验推进：[docs/论文实验推进/README](docs/论文实验推进/README.md)
- 当前代码：[code/README](code/README.md)

## 目录

| 目录 | 职责 |
|---|---|
| `code/` | 当前实现、脚本、测试、本机完整输出和临时材料 |
| `paper/` | 主论文及论文工作资料 |
| `literature/` | 本地文献资产，不进入远端仓库 |
| `docs/` | 当前索引、研究推进、架构、维护清单和归档 |
| `记录/` | 过程记录、导师批注、交接和历史材料 |
| `evidence/` | Git 可携带的小型审计快照及哈希清单 |

上游 `D:\shen\TJU\DRIFT` 只读。历史 DRIFT 风险事件和传播 Pilot 已移入三个 `legacy/` 子目录并由历史索引说明，不能覆盖当前正式路径。

## 快速验证

```powershell
python code/scripts/validate_project_docs.py --strict-git
python code/scripts/export_project_evidence.py --repo-root . --verify
Set-Location code
python -m pytest tests -q
python -m compileall -q src scripts
```

旧版根 README 的 2026-08-15 快照保留在 Git 历史与 2026-09-08 归档清单中；当前状态不再从旧快照读取。
