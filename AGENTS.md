# AAD 长期 AI 协作规则

本文件适用于整个 `D:\shen\TJU\AAD`。目标是 Human-driven、AI-accelerated：研究方向和最终判断由研究者掌握，AI 负责高质量执行、独立质疑、验证和知识维护。

## 1. 每次进入项目的阅读顺序

1. `PROJECT_CONTEXT.md`：稳定边界、当前 Gate 与精确继续点。
2. `docs/PROJECT_REGISTRY.json`：机器可读实验、结果、历史和路径登记。
3. `docs/RESEARCH_STATUS.md`：研究问题、已知、未知与阻断。
4. `docs/PROJECT_INDEX.md`：按问题定位代码、证据和历史。
5. `git status --branch --short`：实时仓库状态。
6. 需要定论时回到 audit、冻结配置、manifest、provenance、checksum、原始表和代码。

索引用于导航，原始证据用于验证。发生冲突先报告，不静默挑选更方便的版本。

## 2. 人与 AI 的职责

研究者负责研究问题、核心思想、算法原理、模型结构、loss、变量、假设、技术路线、实验目的、科学 Gate、人工标签和最终结论。

AI 负责代码、测试、调试、已授权实验执行、自动化、数据处理、结果整理、可视化、审查、检索、通俗解释和有证据的备选方案。AI 应主动检查前提、反例、混杂、实现一致性和证据强度，但未经确认不得改变上述科学设计。

已明确授权的范围持续执行，不重复询问同一权限。只有缺失信息会实质改变结果、操作超出范围或涉及未授权高风险动作时才停下确认。

## 3. 证据与状态词

优先级：当前机器 Gate/原始产物 → Git 内精确证据快照 → 当前代码与测试 → 明确研究者决策 → 当前文档 → 历史记录。

- `Verified`：当前实现或结果有直接、可核验的证据。
- `Active`：已经开始，但完整 Gate 尚未通过。
- `Agreed`：研究者同意的未来工作或约束。
- `Proposed`：候选思路，尚未同意或验证。
- `Historical`：只用于追溯。
- `Unknown`：证据缺失、冲突或尚未核验。

代码存在不等于实验完成；测试通过不等于科学结论成立；消息交付不等于采用；采用不等于动作变化；动作变化不等于区域风险变化。

## 4. 科研保护与停止规则

- AAD 是当前项目；`D:\shen\TJU\DRIFT` 只读。
- 跨阶段前必须读取 `RES-PROTOCOL-READINESS-V1` 或本机 readiness 原件。
- Gate 未通过时，不生成协议锁、不运行后续正式实验、不看 locked holdout、不降低阈值、不挑种子、不把 calibration/E00 写成科学主效应。
- 缺失不补零；不可观测不推断；失败、空效应、旧结果、配置、日志和 `uncertain` 均保留。
- pNEUMA 人工标签由研究者完成；AI 只做界面/格式校验和只读统计。
- 不执行会丢失项目资料的 `git clean`、`git reset --hard`、批量 checkout、递归删除或覆盖；确需清理时先精确解析目标并采用可恢复方式。

## 5. 当前与历史代码

- 当前实现、脚本和测试分别位于 `code/src/riskprop/`、`code/scripts/`、`code/tests/`。
- 历史实现统一位于三个 `legacy/` 子目录，不得默认接回正式路径。
- 当前本机完整输出位于 `code/outputs/`；临时材料位于 `code/tmp/`。
- Git 内便携证据位于 `evidence/`，只保存已登记的小型审计快照；不得包含原始大表、HTML、图片、日志或密封抽样键。
- 历史归档的替代理由和证据边界见 `docs/HISTORY_INDEX.md`。

## 6. 解释规范

复杂内容按“解决什么问题 → 直觉 → 为什么需要 → 具体怎么做 → 数学表示 → 代码实现 → 实验影响”组织。公式解释变量、单位、每一项、设计理由和变化后果。避免只说“提升鲁棒性/泛化能力”，必须说明对象、机制、指标和验证方式。

## 7. 信息结构维护义务

| 变化 | 必须检查或更新 |
|---|---|
| 新增/完成实验 | 注册表、实验索引、研究状态、阶段执行记录 |
| 新结果、失败或结果失效 | 注册表、结果索引、研究状态、便携证据、CHANGELOG |
| 模块、入口、路径变化 | 项目索引、架构、注册表、测试 |
| 方案转为历史 | 历史索引、注册表、归档说明；保留原证据 |
| 科研结论或证据等级变化 | 研究状态、结果索引、论文相应位置 |
| 协作规则变化 | AGENTS、PROJECT_CONTEXT、CHANGELOG |
| 后续接手状态变化 | PROJECT_CONTEXT 的当前任务、阻断和继续点 |

旧实验记录采用追加或归档方式保留，不反向改写成当前观点。机器事实源和人类索引必须在同一提交中同步。

## 8. 便携证据更新

当登记结果的 audit/config/manifest/provenance/SHA256SUMS 变化时，在根目录运行：

```powershell
python code/scripts/export_project_evidence.py --repo-root .
python code/scripts/export_project_evidence.py --repo-root . --verify
```

导出是精确复制并记录大小和 SHA-256，不改原始产物。新结果必须先加入导出脚本和 `PROJECT_REGISTRY.json`，再更新结果索引。密封抽样键永不导出。

## 9. 完成前验证

信息结构变化至少运行：

```powershell
python code/scripts/validate_project_docs.py --strict-git
python code/scripts/export_project_evidence.py --repo-root . --verify
Set-Location code
python -m pytest tests/test_project_docs.py -q
```

代码变化还要运行覆盖实际路径的测试，并在最终收口时运行全量 `pytest` 和 `compileall`。论文变化必须编译、渲染并检查。提交后使用 `--strict-git --require-clean`，再从纯 Git 克隆验证一次。命令成功只证明其覆盖范围，不自动证明科研 Gate。
