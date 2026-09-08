# AAD 项目总索引

> 核对日期：2026-09-08。索引用于检索，机器登记和原始证据用于定论。

## 最短阅读路径

1. [PROJECT_CONTEXT](../PROJECT_CONTEXT.md)：边界、Gate 和唯一继续点。
2. [LEARNING_PATH](LEARNING_PATH.md)：从零恢复项目理解。
3. [RESEARCH_STATUS](RESEARCH_STATUS.md)：当前已知、未知和阻断。
4. [PROJECT_REGISTRY](PROJECT_REGISTRY.json)：可自动校验的实验—结果—历史登记。
5. [METHOD_AND_ALGORITHM_GUIDE](METHOD_AND_ALGORITHM_GUIDE.md)：直觉、公式、实现和实验影响。

## 按问题查找

| 想知道什么 | 首选入口 | 精确核验 |
|---|---|---|
| 当前做到哪里 | `RESEARCH_STATUS.md` | readiness 与各结果 audit |
| 下一步做什么 | `PROJECT_CONTEXT.md` 第 13 节 | E15-A QA v5 audit 与人工导出 CSV |
| 项目为何这样设计 | `METHOD_AND_ALGORITHM_GUIDE.md` | 论文 Methods、冻结协议、测试 |
| 某实验如何运行 | `EXPERIMENT_INDEX.md` | 注册表的入口/配置/测试字段 |
| 某数字从哪里来 | `RESULTS_INDEX.md` | `evidence/` 或本机完整产物 |
| 历史方案为何不用 | `HISTORY_INDEX.md` | legacy README、归档清单和旧记录 |
| 代码与数据如何连接 | `ARCHITECTURE.md` | 当前源码、manifest 和测试 |
| 论文写到哪里 | `paper/主论文/main.tex` | 编译日志、图表和 Source Data |
| 最近改变了什么 | `CHANGELOG.md` | Git diff 与 maintenance manifest |

## 工程入口

| 类型 | 位置 | 说明 |
|---|---|---|
| 正式实现 | `code/src/riskprop/` | E00/E01/E15-A/E16-A/E17-A 与项目校验 |
| 正式命令 | `code/scripts/` | 数据准备、运行、复算、Gate、证据导出 |
| 自动测试 | `code/tests/` | 当前契约；人工标签和外部访问不由单元测试替代 |
| 历史实现 | 三个 `legacy/` | 可追溯，不属于当前科学路径 |
| 本机完整输出 | `code/outputs/formal/` | 大表、日志和完整实验包，默认 Git 忽略 |
| 临时材料 | `code/tmp/` | 构建、环境和渲染缓存，不作证据入口 |
| Git 便携证据 | `evidence/` | audit/config/manifest/provenance/checksum 小型快照 |
| 阶段计划与记录 | `docs/论文实验推进/` | 预注册、Methods/Results 分工、执行记录 |
| 论文 | `paper/主论文/` | `main.tex` 是正文源 |
| 文献 | `literature/` | 本地文献库 |
| 过程和历史 | `记录/`、`docs/归档/` | 不覆盖当前机器事实 |

## 当前代码快速定位

| 研究/工程面 | 实现 | 脚本 | 测试 |
|---|---|---|---|
| 正式产物与四格契约 | `formal_artifacts.py`、`formal_design.py`、`formal_runner.py` | E00 脚本 | `test_formal_artifacts.py`、`test_formal_design.py` |
| E00 SUMO | `sumo_e00.py`、`upstream_adapter.py` | `run/analyze/compare_e00_*` | `test_sumo_e00.py`、`test_upstream_adapter.py` |
| E15-A | `real_trajectory.py`、`e15a.py` | `run_e15a_ngsim.py` | `test_real_trajectory.py` |
| pNEUMA | `pneuma_mapmatch.py`、`pneuma_qa.py` | mapmatch 与 QA 准备脚本 | `test_pneuma_mapmatch.py`、`test_pneuma_qa.py` |
| E16-A | `e16a.py` | `profile/run_e16a_*` | `test_formal_design.py` 覆盖正式契约 |
| E17-A | `e17a.py` | `prepare/run_e17a_*` | `test_formal_design.py` 覆盖正式契约 |
| E01 与协议锁 | `e01_metrics.py`、`e01_validation.py`、`protocol_lock.py` | 预锁验证/readiness | `test_protocol_lock.py`、`test_formal_design.py` |
| 知识与证据系统 | `project_docs.py` | 验证器、证据导出器 | `test_project_docs.py` |

## 维护入口

- AI 规则：根 `AGENTS.md`。
- 证据政策：`evidence/README.md`。
- 当前收口计划：`maintenance/2026-09-08-long-term-collaboration-closure-plan.md`。
- 历史迁移与归档证明：`maintenance/` 下三个 manifest。
- 自动验证：`python code/scripts/validate_project_docs.py --strict-git`。
- CI：`.github/workflows/project-integrity.yml`。
- 旧 `docs/项目导航.md` 只作兼容和历史追溯。
