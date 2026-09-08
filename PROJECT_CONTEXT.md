# AAD 项目交接与继续工作上下文

> 更新日期：2026-09-08（Asia/Shanghai）
> 用途：新任务的第一入口。瞬时 Git 状态必须实时查询；科研状态以注册表、便携证据和原始产物共同核验。

## 1. 项目身份与边界

- 当前项目根目录：`D:\shen\TJU\AAD`。
- 研究主题：车联网远端风险信息被控制器采用后，能否在普通物理影响到达前改变目标车辆集合动作与目标区域总体风险。
- 上游 `D:\shen\TJU\DRIFT` 只读，不向其写入。
- 根目录业务层为 `code/`、`paper/`、`literature/`、`docs/`、`记录/`、`evidence/`；根部只保留治理和入口文件。
- 本次收口只整理知识、证据和维护机制，没有改变研究问题、算法、损失、指标、实验变量或 Gate。

## 2. 人与 AI 的职责

- 研究者决定科学问题、变量含义、实验设计、容差、Gate、人工标签和结论表达。
- AI 执行检索、代码、测试、证据导出、索引维护与独立质疑；发现缺口时应明确报告，不能暗改科学设计。
- 已确认范围内持续执行，不重复询问同一权限；若缺失信息会改变科学结果，则停止并请研究者决定。
- 当前 E15-A 人工盲审必须由研究者完成，AI 不得根据算法输出代标或“修正”标签。

## 3. 证据层级

从高到低、从当前到历史依次为：

1. 当前机器可读 Gate、audit、冻结配置、manifest、provenance 和 SHA256SUMS。
2. Git 内 `evidence/` 的精确小型快照及其证据清单。
3. 当前正式源代码、测试与实验执行记录。
4. 论文中的方法/结果文字。
5. 旧交接、历史 Pilot、legacy 代码和归档记录。

命令退出成功不等于科学 Gate 通过。索引用于定位，结论必须回到原始证据；本机大产物缺失也不能被解释成实验没有发生。

## 4. 当前研究状态

- 所处阶段：Stage I 主效应实验之前的测量、现实边界和协议锁定。
- 已验证：E00 工程链；E01 解析/路径真值；NGSIM 风险参考；pNEUMA QA 包结构；SPMD RV_RX 的观测边界；部分现实参考。
- 尚未验证：pNEUMA leader/TTC 人工有效性、packet 级通信、完整 sim-real 覆盖、科学容差与样本量、Stage I 主效应。
- 所有现有结果均为 `scientific_claim_eligible=false`。
- 当前机器判定：`protocol_lock_allowed=false`、`e02_allowed=false`。

## 5. 当前唯一任务

由研究者打开本机 `code/outputs/formal/calibration/e15a_pneuma_manual_qa_v5/review_map.html`，只完成页面默认的 48 条平衡 pilot，并导出 `pneuma_map_leader_round1_completed.csv`。

在 CSV 交给 AI 前：不猜测浏览器 localStorage 的完成度，不打开密封抽样键，不生成 pNEUMA TTC，不宣称 E15-A 通过。导出后，AI 只读统计，保留真实错误和 `uncertain`，再把 Gate 证据交给研究者决策。

## 6. 实验与结果总览

| 实验 | 当前状态 | 结果 ID | 科学边界 |
|---|---|---|---|
| E00 | 工程验证通过 | RES-E00-PRIMARY-V3、RES-E00-ENV-COMPARE-V3 | 物理路径未接通 |
| E15-A | 等待人工 Round 1 | NGSIM、mapmatch、QA 三项结果 | leader/TTC 未通过 |
| E16-A | 等待官方 Packet | RES-E16A-OBS-V3 | 仅接收状态连续性 |
| E17-A | 部分现实参考 | RES-E17A-REAL-REF-V1 | 缺 pNEUMA TTC 与仿真样本 |
| E01 | 技术验证通过、科学冻结未完 | PRELOCK、READINESS | 容差未冻结 |
| E02 | 已约定但阻断 | 无 | 未实现、未运行 |

完整字段、正反向链接和核心数值见 `docs/PROJECT_REGISTRY.json`、`EXPERIMENT_INDEX.md`、`RESULTS_INDEX.md`。

## 7. 核心方法与数据流

数据先经过适配和风险测量。E15-A 校准 leader/TTC，E16-A 界定通信观测，E17-A 建立现实覆盖，E01 验证数学和离散实现。只有这些 Gate 与科学容差齐全，才生成不可覆盖的协议锁，再允许设计和运行 E02。

E00 是工程底座：四格只改变源事件 `s` 与通道 `c`，五表分别记录 state、emission、protocol、action、risk。消息生成、发送、交付、校验、采用、动作分化和风险变化必须分开。通俗解释和公式见 `docs/METHOD_AND_ALGORITHM_GUIDE.md`。

## 8. 目录与持久化

- `code/src/riskprop/`：当前正式实现；`legacy/`：历史实现。
- `code/scripts/`：当前命令；`code/tests/`：自动测试；其各自 `legacy/` 只作历史追溯。
- `code/outputs/`：本机完整实验产物和大表，默认不进 Git。
- `evidence/`：从已登记本地产物导出的精确小型证据快照，进入 Git；不含大表、原始 CSV、HTML、图片、日志或密封抽样键。
- `paper/主论文/main.tex`：论文正文唯一源；`docs/论文实验推进/`：阶段计划与执行记录。
- `记录/`、`docs/归档/`：历史决策和原始版本，不覆盖当前事实源。
- 当前没有数据库或服务端持久化；GitHub 只保证已跟踪内容可恢复。

## 9. 外部依赖与访问边界

- SUMO/TraCI/netconvert：E00 仿真依赖。
- NGSIM、pNEUMA、SPMD：本地现实数据；原始文件不进入仓库，身份由 manifest/SHA-256 记录。
- SPMD 官方 Packet：现有证据记录访问返回 HTTP 403；这只表示外部访问阻断，不表示 schema 不合格。
- INTERACTION：旧记录为尚未获批，本次未重新核验，不是当前唯一任务。
- 没有已确认的部署、对外 API、身份认证或数据库目标；`review_map.html` 是本地静态人工审核页。

## 10. 构建与验证命令

在项目根目录运行：

```powershell
python code/scripts/validate_project_docs.py --strict-git
python code/scripts/export_project_evidence.py --repo-root . --verify
Set-Location code
python -m pytest tests -q
python -m compileall -q src scripts
```

提交后再运行 `python code/scripts/validate_project_docs.py --strict-git --require-clean`。CI 会在纯 Git checkout 中执行知识系统、证据和测试验证。真实 SUMO 与大数据实验不因整理无理由重跑；已有 run ID 不可覆盖。

## 11. 已冻结的决策与停止规则

- AAD 是当前项目，DRIFT 只读。
- 研究对象是目标区域总体风险，不是单车风险。
- Stage I 使用完整四格 intention-to-run 分母，不能按处理后的 adoption 或动作分化筛样本。
- 缺失不补零；不可观测不推断；失败、空效应和 uncertain 保留。
- E00 是工程 Gate，不能写成科学主效应。
- E15-A/E16-A/E17-A/E01 与协议锁通过前，E02 停止。
- Methods 写定义、设计和统计；Results 只写实际观察。
- 不通过换指标、挑种子、看 locked holdout 或降低容差制造正向效应。

## 12. 已完成、未完成与阻断

已完成：正式代码与历史代码分层；历史资料保留式归档；机器注册表 v2；实验/结果/历史双向索引；Git 内便携证据层；学习路径与方法指南；严格校验器及测试；CI 防漂移入口。

科研未完成：人工 QA、packet 数据访问、sim-real 覆盖、科学容差与样本量冻结、协议锁、E02 及后续论文科学结果。

阻断分三类：人工输入阻断 E15-A；外部访问阻断 E16-A；上游依赖和科学冻结阻断 E17-A/E01/协议锁/E02。项目工程收口不能把这些科研阻断伪装为已解决。

## 13. 精确继续点

1. 新接手者先运行实时 Git 状态与严格项目校验。
2. 读取 `evidence/results/RES-E15A-PNEUMA-QA-V5/审计说明.md` 和本机 v5 `audit.json`。
3. 研究者完成 48 条平衡 pilot 并导出 CSV；若浏览器已有未导出进度，先保留。
4. AI 对 CSV 做只读统计、校验 blind ID 和完成度，不改人工标签。
5. 研究者根据预先约定 Gate 决定继续完整 Round 1/2 还是保留失败并停止。

若用户尚未提供 CSV，下一任务不得跳到 pNEUMA TTC、协议锁或 E02。

## 14. 入口索引

| 需求 | 首选文件 |
|---|---|
| 快速恢复项目 | `docs/LEARNING_PATH.md` |
| 当前科研状态 | `docs/RESEARCH_STATUS.md` |
| 机器事实与正反向链接 | `docs/PROJECT_REGISTRY.json` |
| 实验/结果/历史 | `docs/EXPERIMENT_INDEX.md`、`RESULTS_INDEX.md`、`HISTORY_INDEX.md` |
| 方法与公式 | `docs/METHOD_AND_ALGORITHM_GUIDE.md` |
| 代码和证据架构 | `docs/ARCHITECTURE.md` |
| Git 内证据 | `evidence/README.md`、`EVIDENCE_MANIFEST.json` |
| AI 工作约束 | `AGENTS.md` |
| 论文阶段记录 | `docs/论文实验推进/README.md` |
| 变更与归档清单 | `docs/CHANGELOG.md`、`docs/maintenance/` |

## 15. 未知、冲突与实时检查

- 浏览器 localStorage 中 v5 人工标注完成度未知；导出前仓库无法判断。
- 未来 CSV 的实际保存位置未知，需用户导出后提供。
- 官方 Packet 和 INTERACTION 后续访问状态未知；不得沿用旧状态作永久事实。
- 论文 PDF 是否与当前 `main.tex` 完全同步，本次工程收口未重新编译/逐页审阅。
- 旧文档中若仍出现 v3/50 条 pilot、历史 Pilot 主效应或“正式 runner 尚未建立”等表述，以 v5 audit、当前正式代码、机器 Gate 和更新日期更晚的执行记录为准。
- Git HEAD、工作树和远端同步是瞬时状态，不写死在交接中。接手时使用 `git rev-parse HEAD`、`git status --short`、`git status --branch --short` 实时取得。
