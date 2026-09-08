# AAD 项目总索引

> 最后核对：2026-09-08  
> 用途：帮助用户和 AI 从问题快速定位到当前证据；精确结论仍须回到原始文件验证。

## 最短阅读路径

1. [项目交接](../PROJECT_CONTEXT.md)：当前工作树、阻断和精确继续点。
2. [研究状态](RESEARCH_STATUS.md)：现在研究什么、确认了什么、正在做什么。
3. [机器登记表](PROJECT_REGISTRY.json)：可自动检查的入口、实验和结果路径。
4. [实验索引](EXPERIMENT_INDEX.md) 与 [结果索引](RESULTS_INDEX.md)：双向追踪实验和证据。
5. [架构说明](ARCHITECTURE.md)：代码、数据、实验、结果和论文如何连接。

## 项目边界

- 当前项目：`D:\shen\TJU\AAD`。
- 上游参考：`D:\shen\TJU\DRIFT`，只读。
- 当前科学问题：远端风险消息在普通物理影响到达目标区域之前，被控制器采用后是否会改变目标车辆集合的动作和目标区域总体风险。
- 当前阶段：正式主效应实验前的测量、现实边界和协议锁定。

## 按问题查找

| 想知道什么 | 首选入口 | 精确核验来源 |
|---|---|---|
| 当前做到哪里 | [RESEARCH_STATUS](RESEARCH_STATUS.md) | `protocol_lock_readiness_v1.json` 与各实验 `audit.json` |
| 当前唯一任务 | [PROJECT_CONTEXT](../PROJECT_CONTEXT.md) 的“精确继续点” | `e15a_pneuma_manual_qa_v5/audit.json` 和人工导出 CSV |
| 核心代码在哪 | [ARCHITECTURE](ARCHITECTURE.md) | `code/src/riskprop/` 与对应测试 |
| 如何运行某项实验 | [EXPERIMENT_INDEX](EXPERIMENT_INDEX.md) | `code/README.md`、`code/scripts/`、冻结配置 |
| 某个数字从哪来 | [RESULTS_INDEX](RESULTS_INDEX.md) | 对应机器产物、manifest、SHA-256 和复算脚本 |
| 某项实验是否做过 | [EXPERIMENT_INDEX](EXPERIMENT_INDEX.md) | `code/outputs/` 与阶段执行记录 |
| 某个结论是否成立 | [RESEARCH_STATUS](RESEARCH_STATUS.md) | 原始结果与 `scientific_claim_eligible` / Gate 字段 |
| 论文写到哪里 | `paper/主论文/main.tex` | 当前编译日志、图表和 Source Data |
| 历史方案为何废弃 | `记录/README.md` 与 `docs/归档/` | 当时的配置、日志、失败记录和交接 |
| 最近信息结构变化 | [CHANGELOG](CHANGELOG.md) | Git diff 与相应验证记录 |

## 工程入口

| 类型 | 位置 | 说明 |
|---|---|---|
| 当前 Python 包 | `code/src/riskprop/` | 当前正式 E00/E01/E15-A/E16-A/E17-A 实现 |
| 历史 Python 包 | `code/src/riskprop/legacy/` | 早期 DRIFT 风险事件、传播和 nonlocal Pilot；只用于追溯/复现 |
| 命令入口 | `code/scripts/` | 当前正式数据准备、实验运行、复算与审计 |
| 历史命令 | `code/scripts/legacy/` | 与历史 Pilot 对应的可复现命令 |
| 测试 | `code/tests/`、`code/tests/legacy/` | 当前与历史测试分层；外部访问和人工标注不由单元测试覆盖 |
| 正式输出 | `code/outputs/formal/` | 机器产物；多数被 Git 忽略，不能依赖远端恢复 |
| 临时输出 | `code/tmp/` | 环境、构建和渲染临时材料；未审计前不批量删除 |
| 实验计划与记录 | `docs/论文实验推进/` | 阶段计划、执行记录、Methods/Results 分工 |
| 论文 | `paper/主论文/` | 当前 `main.tex`、PDF、参考文献和工作稿归档 |
| 文献 | `literature/` | 本地文献库，不进入 GitHub |
| 项目记录 | `记录/` | 周推进、导师批注、交接和历史材料 |

## 代码模块快速定位

| 研究/工程面 | 实现 | 脚本 | 测试 |
|---|---|---|---|
| 正式产物与四格契约 | `formal_artifacts.py`、`formal_design.py`、`formal_runner.py` | E00 相关脚本 | `test_formal_*`、`test_sumo_e00.py` |
| E00 SUMO | `sumo_e00.py`、`upstream_adapter.py` | `run/analyze/compare_e00_*` | `test_sumo_e00.py` |
| E15-A 真实风险测量 | `real_trajectory.py`、`e15a.py` | `run_e15a_ngsim.py` | `test_real_trajectory.py`、`test_e15a.py` |
| pNEUMA 地图与人工 QA | `pneuma_mapmatch.py`、`pneuma_qa.py` | `run_e15a_pneuma_mapmatch.py`、`prepare_pneuma_manual_qa.py` | `test_pneuma_*` |
| E16-A 通信可观测性 | `e16a.py` | `profile/run_e16a_*` | `test_e16a.py` |
| E17-A 现实覆盖 | `e17a.py` | `prepare/run_e17a_*` | `test_e17a.py` |
| E01 预锁验证 | `e01_metrics.py`、`e01_validation.py`、`protocol_lock.py` | `run_e01_prelock_validation.py`、`check_protocol_lock_readiness.py` | `test_e01_*`、`test_protocol_lock.py` |
| 历史风险 Pilot | `legacy/events.py`、`legacy/risk_event_dataset.py`、`legacy/local_propagation_baseline.py` 等 | `scripts/legacy/` | `tests/legacy/` |

## 维护入口

- 协作规则：[AGENTS.md](../AGENTS.md)
- 重构计划：[2026-09-08 重构计划](maintenance/2026-09-08-research-workspace-refactoring-plan.md)
- 自动检查：`cd code; python scripts/validate_project_docs.py`
- 旧导航：[项目导航.md](项目导航.md)，只作兼容和历史追溯。
