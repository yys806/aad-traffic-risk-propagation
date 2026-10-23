# 论文与研究材料位置（AAD）

> 核对日期：2026-10-23。本文件只登记**文件来源与导航**，不改变任何科研结论、Gate、实验结果或论文内容。

## 1. 事实源分工

| 对象 | 唯一事实源 | 说明 |
|---|---|---|
| 当前最新版论文正文 | **Overleaf** | 正文、公式、符号、章节结构与正式表述以 Overleaf 当前版本为准；本仓库不保存活动 `.tex` 论文源。未登记真实项目链接前不写 URL。 |
| 当前实现与项目状态 | **GitHub 仓库 `D:\shen\TJU\AAD`** | 代码、配置、实验产物、audit/manifest/provenance/SHA256SUMS、正式决策与阶段 Gate 以仓库真实文件为准。 |
| 历史论文 PDF、图稿、组会 PPT、辅助笔记 | 本机 `D:\shen\OB\科研\TJU\AAD` | 仅供历史追溯与辅助上下文，不是当前正文，也不是当前状态。 |

事实优先级不变：当前源码/config/experiment 与机器产物 > `AI_CONTEXT/` > 普通项目文档 > 历史聊天或历史推断。OB 笔记不能覆盖仓库当前状态。

## 2. OB 专用目录（已授权核查范围，2026-10-23 核验结构如下）

| 目录 | 内容 |
|---|---|
| `D:\shen\OB\科研\TJU\AAD\AAD\` | `00计划与进度.md`、`01课题研究问题与总体链路.md`、`02文献与创新定位.md`、`03核心概念与方法框架.md`、`04数据集与仿真平台.md`、`05核心实验部分.md` |
| `D:\shen\OB\科研\TJU\AAD\历史Paper\paper\` | 历史论文 PDF（含导师批注版本） |
| `D:\shen\OB\科研\TJU\AAD\历史Paper\figure\` | 历史图稿、图片与 `*_FIG.pptx`；`old\` 为旧版图 |
| `D:\shen\OB\科研\TJU\AAD\组会PPT\` | 组会汇报 PPT 与 `模板.pptx` |
| `D:\shen\OB\科研\TJU\AAD\组会笔记\` | 组会记录与论文批注 |

授权仅限该目录，不扩展到 OB 其他任何路径。不得修改、移动、删除这些材料，也不得把其内容批量复制进仓库。

## 3. 已退役的本地路径

- 根目录 `paper/`（`paper/主论文/main.tex` 等本地 `.tex` 编辑流）于 **2026-10-23 退役**，当前仓库根目录没有活动 `paper/` 论文源。
- 历史报告、`docs/归档/`、旧 manifest 与 `code/outputs/local_checks/` 等位置中的 `paper/...` 路径属**历史证据或历史克隆**，不得当作当前论文源，也不在本轮清理。

## 4. 当前状态入口

科研状态、Gate 与下一步以 `AI_CONTEXT/00_PROJECT_STATE.md`、`docs/RESEARCH_STATUS.md`、`docs/PROJECT_REGISTRY.json`、`docs/STAGE_INDEX.md` 和 `evidence/` 为准。
