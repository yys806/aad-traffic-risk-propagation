# AAD 项目交接

> 状态快照日期：2026-10-12（**历史交接信息**，部分阶段描述已过时）。当前阶段、Gate 与下一步以 `AI_CONTEXT/00_PROJECT_STATE.md` 和 `docs/RESEARCH_STATUS.md` 为准；本文件只保留稳定边界和当时的精确继续点，实时文件状态仍需用 Git 和机器产物核验。

## 1. 项目目标

验证来源可追溯且被控制器采用的远端风险消息，能否在普通物理影响到达目标区域前改变车辆动作与区域总体风险。

## 2. 当前阶段（2026-10-12 快照，历史）

当前位于阶段 0。主任务是阶段 0.2 NGSIM风险审计，阶段 0.3 pNEUMA城市运动学分布同步整理；阶段 1.1未启动。

本段为 2026-10-12 快照时点的事实；其后进展（阶段 0.3 已关闭、阶段 0.5 现被交互相容层阻断）不在此追写，请读 `AI_CONTEXT/00_PROJECT_STATE.md`。

## 3. 当前事实

阶段 0.1工程链已验证；Stage 0.2 已在研究者批准的有限范围内 `Completed / Closed`（四源 NGSIM、100 ms、P2=4,545）；Stage 0.3 pNEUMA 描述性统计、质量审计与 Stage 0.5 参考接口已完成并通过独立复算，为 Gate Pass Candidate，科学验收与未冻结参数待研究者。SPMD RV_RX只支持接收状态连续性；其他科学参数未冻结。

## 4. 当前未知

NGSIM独立物理真实性与质量验收标准尚未完成/批准；100/200ms不等价。pNEUMA运动学分布、packet级通信、仿真—现实覆盖、科学容差、样本量和核心效应均未完成或未确认。

## 5. 当前 Gate

阶段 0.2 已在有限范围内通过；阶段 0.3 为 Gate Pass Candidate 待研究者审核；阶段 0.5和0.6未闭合；阶段 0.4受外部 Packet访问限制，可按有限证据边界冻结。协议锁未通过。

## 6. 已确认研究分工

NGSIM负责前车关系、跟驰风险指标和风险事件；研究者已于 2026-09-10 批准 pNEUMA 前车推断与人工复核退役，pNEUMA只负责速度、纵向加速度与车型分布；SPMD负责通信可观测边界。

## 7. 数据位置

原始数据统一位于根目录 `dataset/`，包含 NGSIM、pNEUMA和SPMD。该目录本机保留且不进入 Git。

## 7.1 论文与研究材料位置（2026-10-23 更新）

- 当前最新版论文只在 **Overleaf**，仓库不保留活动 `.tex` 论文源；根目录 `paper/`（`paper/主论文/main.tex`）已于 2026-10-23 退役，不得恢复本地论文编辑流程，未登记真实链接前不写 Overleaf URL。
- 历史论文 PDF、图稿、组会 PPT 与辅助笔记位于本机 `D:\shen\OB\科研\TJU\AAD`：`AAD\`（00–05 辅助笔记）、`历史Paper\paper\`（历史 PDF）、`历史Paper\figure\`（图稿/PPT）、`组会PPT\`、`组会笔记\`。这些材料仅提供历史与辅助上下文，不进入 Git，也不得当作最新版正文或当前状态。
- 当前实现、实验结果与阶段状态仍以本 GitHub 仓库为准；OB 笔记不能覆盖仓库当前状态。导航入口：`docs/PAPER_AND_MATERIAL_SOURCES.md`。

## 8. 当前代码

正式实现位于 `code/src/riskprop/`，入口位于 `code/scripts/`，测试位于 `code/tests/`。新代码使用 `stage_X_Y`或任务语义命名。

## 9. 历史代码与证据

旧实现位于各 `legacy/`；旧编号文档位于 `docs/归档/旧实验编号材料/`；旧输出和证据位于 `code/outputs/history/`、`evidence/history/`。不得默认接回当前路径。

## 10. 证据规则

索引只负责导航。结论应回到 audit、冻结配置、manifest、provenance、SHA256SUMS、原始表和代码交叉核验。

## 11. 科研停止规则

Gate未通过时，不签协议锁、不看 locked holdout、不降低阈值、不挑种子、不运行阶段 1.1，也不把工程或校准结果写成主效应。

## 12. 当前结果边界

现有结果全部不可支持“类超距效应已经存在”。消息交付、采用、动作变化和风险变化必须分别记录与验证。

## 13. 精确继续点

1. 研究者审阅 Stage 0.3 Gate Pass Candidate 包（`code/outputs/formal/calibration/stage_0_3_pneuma_kinematics_20261012_r1/`），裁决连续性容差、描述性阈值、车型映射、适用范围与科学 Gate。
2. 按新分工重建阶段 0.5真实参考并生成 SUMO校准样本。
3. 重算阶段 0.6 readiness；所有 Gate通过后再签协议锁。

## 14. 维护入口

AI 快速恢复入口见 `AI_CONTEXT/00_PROJECT_STATE.md`；计划与执行记录见 `docs/论文实验推进/`；机器状态见 `docs/PROJECT_REGISTRY.json`；阶段、结果、历史分别见 `docs/STAGE_INDEX.md`、`docs/RESULTS_INDEX.md`、`docs/HISTORY_INDEX.md`；论文与材料位置见 `docs/PAPER_AND_MATERIAL_SOURCES.md`。

## 15. 完成定义

文档与注册表同步、真实路径存在、证据可校验、测试覆盖实际入口、失败与不确定记录保留，才可声明相应工程任务完成；科研 Gate仍需独立判定。
