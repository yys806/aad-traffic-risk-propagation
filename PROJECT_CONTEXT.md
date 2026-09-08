# AAD - Project Context

> 交接后信息结构更新（2026-09-08）：已建立根 `AGENTS.md` 和 `docs/` 下的项目、研究、实验、结果与架构索引；历史 Pilot 代码/脚本/测试已迁入各自 `legacy/`，根临时工作区和导师批注过程记录已保留式归档。新会话在本文件之后按 `AGENTS.md` 的顺序读取；本次更新未改变下述实验状态、科研 Gate 或精确继续点。  
> 生成时间：2026-09-08 12:46:48 +08:00（Asia/Shanghai）  
> 项目根目录：`D:\shen\TJU\AAD`  
> Git 状态：`main`，HEAD `eb1bb0a62f3c42c36abb867430940953effaaebe`，工作树存在大量已跟踪修改、删除和未跟踪文件  
> 证据范围：截至本交接的对话决策；根目录入口、当前实验推进文档、旧交接、Git 状态与近期历史、`code/` 的配置/入口/核心模块/测试、E00/E15-A/E16-A/E17-A/E01 机器可读审计产物、当前主论文路径。未逐字阅读全部文献、全部大型原始数据、全部历史二进制输出或 `tmp/`。

## 1. 项目概览

AAD 是当前持续推进的交通风险研究项目。DRIFT 是已经完成的上游交通流生成与闭环 rollout 项目，只为 AAD 提供机制和资产参考；本项目不得修改 `D:\shen\TJU\DRIFT`。

论文当前研究问题是：一条来源可追溯、确实被控制器采用的远端风险消息，能否在源扰动的普通物理影响到达目标区域之前，通过改变目标车辆集合的动作，改变目标区域的总体风险。

研究分为两个科学阶段：Stage I 识别并证伪上述信息介导效应；Stage II 仅在 Stage I 获得支持后，研究如何利用该机制降低平均风险与尾部风险，同时约束安全、效率和舒适性代价。当前仍处于正式主效应实验之前的测量与协议锁定阶段。

已确认的非目标：E00 不是科学效应实验；当前不运行 E02，不优化 Stage II 控制器，不把真实数据相关性、历史 Pilot 或 calibration seed 写成“类超距作用成立”。

主要使用者是项目作者及其导师/合作者。当前没有证据表明该仓库是面向公众部署的软件产品。

## 2. 当前快照

| 项目 | 当前状态 | 证据 |
|---|---|---|
| 当前唯一执行任务 | 完成 E15-A pNEUMA 地图匹配/候选前车的人工第一轮审计；先做 v5 页面默认的 48 条平衡试标 | `code/README.md`；`e15a_pneuma_manual_qa_v5/audit.json` |
| 最近完成阶段 | E00 工程与测量基础设施 Gate 已通过；不构成科学结论 | `docs/论文实验推进/阶段0_基础设施与测量/E00/执行记录.md`；E00 report 与双环境比较 |
| 协议锁 | 未生成；`protocol_lock_allowed=false` | `code/outputs/formal/calibration/protocol_lock_readiness_v1.json` |
| E02 | 未启动且当前禁止启动；`e02_allowed=false` | 同上 |
| 分支 / HEAD | `main` / `eb1bb0a62f3c42c36abb867430940953effaaebe` | 2026-09-08 新鲜 Git 查询 |
| 工作树 | 非干净；正式实验实现、测试、文档和输出中有大量未跟踪或未提交内容 | 2026-09-08 `git status --short` |
| 新鲜验证 | 重构后 `python -m pytest tests -q`：`164 passed in 58.20s`；`python -m compileall -q src scripts`：通过；项目文档校验 `PROJECT_DOCS_OK`；v5 标注包 checksum：通过 | 2026-09-08 在 `code/` 运行 |
| 当前阻断 | E15-A 等待人工 Round 1；E16-A 等待官方 Packet 资产访问；E17-A 等待 pNEUMA 人工审计和仿真样本；E01 等待 E15/E17 与容差冻结 | `protocol_lock_readiness_v1.json` |
| 已约定下一步 | 人工完成 v5 的 48 条试标并导出 `pneuma_map_leader_round1_completed.csv`；在此之前不打开密封抽样键，不计算 pNEUMA TTC | `code/README.md`；`pneuma_qa.py` 生成的审计说明与页面逻辑 |

### 与当前继续工作直接相关的未提交文件

- `code/src/riskprop/{formal_artifacts,formal_design,formal_runner,sumo_e00}.py`、对应 scripts/tests：E00 正式封存、审计、真实 SUMO 四格和独立复算实现；目前是未跟踪文件，但已有测试及 E00 运行证据。
- `code/src/riskprop/{calibration,e15a,pneuma_mapmatch,pneuma_qa,e16a,e17a,e01_metrics,e01_validation,protocol_lock}.py`、对应 scripts/tests：现实校准、人工 QA、预锁验证与协议锁防护；多数仍是未跟踪文件，不能在整理工作树时误删。
- `code/src/riskprop/real_trajectory.py` 与 `code/tests/test_real_trajectory.py`：已跟踪但未提交，增加 DRAC、测量状态、缺失原因和 NGSIM 字段兼容。
- `code/pyproject.toml`：已跟踪但未提交，增加 `pyarrow>=25.0,<26`。
- `code/README.md`：已跟踪但未提交，记录当前正式入口、v5 标注步骤和证据边界。
- `paper/主论文/main.tex`、`main.pdf`：已跟踪但未提交，包含当前导师反馈后的论文工作稿；本次交接未重新编译。
- `docs/论文实验推进/`、`docs/归档/`、`记录/9.10组会汇报.md`：当前阶段计划、执行记录、归档与汇报材料；部分为未跟踪内容。
- 原根目录 `findings.md`、`progress.md`、`task_plan.md` 已归档到 `记录/项目历史/导师批注修订_2026-08-27_2026-08-29/`；根 `tmp/` 与 `.pytest_cache` 已保留式迁入被 Git 忽略的 `code/tmp/`。迁移前后哈希见 `docs/maintenance/2026-09-08-physical-refactor-manifest.json`。
- `git status` 中还存在大量已跟踪删除，主要对应先前文档归档/目录整理。没有证据表明这些删除应被回滚；接手者不得擅自 reset、checkout 或 clean。

## 3. 架构与组件关系

```text
只读上游 DRIFT ──机制/拓扑参考──┐
真实数据 NGSIM / pNEUMA / SPMD ─┼─> calibration 与测量审计
                                  │       ├─ E15-A 风险测量
AAD 内 SUMO ─> E00 四格运行/五表 ┘       ├─ E16-A 通信可观测性
          └─> 独立只读审计                └─ E17-A 现实覆盖
                                                   │
解析真值与路径测试 ───────────────────────────────> E01
                                                   │
                          全部 Gate 通过 ─> protocol_lock_v1.1
                                                   │
                                      锁定后才允许设计/运行 E02
```

- 仿真运行器负责产生数据，独立分析器只从封存后的表与拓扑重新判断，避免使用 runner 的隐藏内存答案。
- 正式运行以 Parquet/JSON/日志/manifest/SHA-256 作为文件级持久化，不存在已确认的数据库、消息队列或后端服务。
- 现实数据只支持其字段能够直接观察的结论。NGSIM/pNEUMA 用于运动与风险测量；当前 SPMD `RV_RX` 只能支持接收状态连续性，不能推出逐包丢失、时延或控制器采用。

## 4. 仓库地图

```text
D:\shen\TJU\AAD
├─ code/
│  ├─ src/riskprop/       历史风险管线及 E00/E01/E15-A/E16-A/E17-A 正式实现
│  │  └─ legacy/          历史 DRIFT 风险与 nonlocal Pilot 实现
│  ├─ scripts/            当前可复算命令；`legacy/` 保存历史命令
│  ├─ tests/              当前测试；`legacy/` 保存历史测试（合计 164 项通过）
│  ├─ outputs/formal/     正式 Gate、校准与只读审计产物
│  └─ environment/        主环境与干净环境证据
├─ paper/
│  └─ 主论文/             `main.tex`、`main.pdf`、历史版本及 NC 指南
├─ literature/            本地文献库；当前以本地文件为准，不以 Zotero 为主存储
├─ docs/
│  ├─ 论文实验推进/       总计划、阶段 0--6、E00/E01 等执行记录
│  └─ 归档/               真实数据、NC 调研及历史材料归档
├─ 记录/
│  ├─ 交接/               旧交接记录
│  └─ 9.10组会汇报.md     当前 20 个有效工作周的汇报计划
└─ PROJECT_CONTEXT.md     本交接文件
```

开始修改时的入口：

- 当前人工标注：先读 `code/README.md`、v5 `审计说明.md` 和 `audit.json`，再打开 v5 `review_map.html`。
- E00：读阶段 0 的 E00 `执行记录.md`、`sumo_e00.py`、`test_sumo_e00.py` 与当前 report。
- E15-A：读 `e15a.py`、`pneuma_mapmatch.py`、`pneuma_qa.py` 及对应测试。
- E16-A/E17-A/E01：分别读同名模块、脚本、测试及机器可读 `audit.json`。
- 论文：先读 `paper/主论文/main.tex` 和 `记录/导师批注_2026-08-27/`；Methods 与 Results 的职责不可混写。

未逐项检查：`literature/` 的每篇 PDF、归档中的所有历史文本、所有大型原始 CSV/ZIP、历史 Pilot 全量输出、`tmp/` 内容和二进制 PDF 的页面视觉质量。

## 5. 技术与环境

- 语言/运行时：Python；2026-09-08 当前解释器为 Python 3.13.5。
- 交通仿真：Eclipse SUMO 1.26.0；E00 使用 AAD 内直接 SUMO/TraCI adapter。
- Python 依赖约束：pandas ≥2.0、PyArrow ≥25,<26、Matplotlib ≥3.8、NetworkX ≥3.2；开发测试 pytest ≥8。来源：`code/pyproject.toml`。
- 包布局：`src` layout；正确测试工作目录是 `D:\shen\TJU\AAD\code`。从仓库根直接运行 pytest 曾因找不到 `riskprop` 失败。
- 文件格式：Parquet、JSON、JSONL、CSV、HTML、Markdown、LaTeX/PDF；正式包使用 manifest 与 SHA-256 封存。
- 论文工具：当前主稿使用 XeLaTeX。旧记录支持曾成功编译，但本次交接未做新鲜论文编译或版面检查。
- 数据库、ORM、队列、缓存服务、容器、CI/CD、云部署：当前检查范围内没有确认实现；浏览器 `localStorage` 仅用于人工标注页面的临时进度。
- 环境变量：本交接未发现当前步骤必须设置的项目密钥类环境变量，也未记录任何环境变量值。

## 6. 功能模块

### 历史 Pilot 风险管线

- 职责：从 DRIFT/Flow emission 提取风险事件、构造局部传播关系、时间置换和早期候选分析。
- 文件：`code/src/riskprop/legacy/`、`code/scripts/legacy/`、`code/tests/legacy/` 与历史 outputs。
- 状态：**Verified（历史能力）**；不能作为当前正式四格主效应证据。
- 限制：旧阈值、旧路径和旧摘要可能已过时；历史结果不覆盖当前冻结协议。

### 正式产物与审计契约

- 职责：五表 schema、provenance、manifest、checksum、失败账本、四格唯一差异、处理前一致、协议时序、运行隔离、时钟和车辆生命周期审计。
- 文件：`formal_artifacts.py`、`formal_design.py`、`formal_runner.py` 及对应测试。
- 状态：**Verified**；2026-09-08 全量测试包含这些行为并通过。
- 限制：代码当前多数未被 Git 跟踪/提交，整理工作树时必须保留。

### E00 真实 SUMO 四格

- 职责：在物理断开的双走廊中运行 `s0c0/s0c1/s1c0/s1c1`，生成非空五表和独立路径审计。
- 文件：`sumo_e00.py`、`run_e00_sumo.py`、`analyze_e00_sumo.py`、`compare_e00_sumo_runs.py`、`test_sumo_e00.py`。
- 状态：**Completed and Verified（仅工程 Gate）**。
- 证据：主环境真实包、clean venv 包、结构比较 `structural_match=true`；四格、处理前、消息生命周期、运行隔离、时钟、车辆生命周期与断开路径审计通过。
- 限制：全部输出 `scientific_claim_eligible=false`；风险行为是 E00 验证状态，不能写入 Results 证明效应。

### E15-A 真实风险测量

- 职责：标准化 NGSIM、计算 TTC/DRAC、合并事件；对 pNEUMA 做地图匹配、候选前车推断与人工审计。
- 文件：`real_trajectory.py`、`e15a.py`、`pneuma_mapmatch.py`、`pneuma_qa.py` 及对应 scripts/tests。
- 状态：**Active**。
- 当前证据：NGSIM v2 已形成四个完整输入时间窗的状态包；pNEUMA v2 地图匹配包已形成；v5 人工 QA 包有 300 条样本、四层各 75 条、默认试标 48 条。
- 限制：`leader_relations_validated=false`、`ttc_generated=false`、Gate `pending_human_round1`。当前不能把 pNEUMA 候选前车当真值，也不能计算 pNEUMA TTC。

### E16-A 通信可观测性

- 职责：界定现实 SPMD 字段可支持的发送/接收证据边界。
- 文件：`e16a.py`、`profile_e16a_rv_rx.py`、`run_e16a_observability.py` 及测试。
- 状态：**Active / blocked by external access**。
- 当前证据：calibration `RV_RX` 有 17,481,111 行、7,601 个 device-trip；当前边界为 `receive_state_continuity_only`。
- 限制：官方 Packet 资产在当前环境返回 HTTP 403；尚未评估 Packet schema，未估计时延或丢包，未推断 adoption。

### E17-A 仿真现实覆盖

- 职责：构建现实参考分布并检查后续仿真是否只覆盖“容易成功”的交通状态。
- 文件：`e17a.py`、`prepare_e17a_real_reference.py`、`run_e17a_coverage.py` 及测试。
- 状态：**Active**。
- 当前证据：现实参考包含 25,000 条运动学样本、20,000 条跟驰样本和 4,758 条风险事件记录；pNEUMA TTC 被明确排除。
- 限制：Gate `pending_pneuma_manual_and_simulation_sample`；当前没有 sim-real Gate 通过证据。

### E01 预锁测量验证

- 职责：用解析真值验证 TTC/DRAC/PET/碰撞、物理路径三分类和时间步收敛；为后续冻结容差与样本量提供前置依据。
- 文件：`e01_metrics.py`、`e01_validation.py`、`run_e01_prelock_validation.py`、`protocol_lock.py` 及测试。
- 状态：**Active**。
- 当前证据：解析指标真值与路径真值通过；0.1/0.05/0.02/0.01 s 的方向一致，0.05 与 0.02 s 的当前差值约 0.00298695。
- 限制：尚未冻结 `delta_eq`、`delta_R`、动作/状态容差和 E02 样本量；Gate 为 `pending_e15_e17_and_frozen_tolerances`。

### 论文与研究记录

- 职责：维护 NC 导向的论文工作稿、导师批注、阶段计划、实验记录与组会材料。
- 文件：`paper/主论文/main.tex`、`docs/论文实验推进/`、`记录/`。
- 状态：**Active**。
- 限制：主稿是可交导师审阅的理论/方法工作稿，不是已有完整科学证据的最终投稿稿；实验数字只能在相应 Gate 通过并复算后写入 Results。

## 7. 核心逻辑与数据流

1. E00 先证明运行、封存和独立复算链可靠。其四格中，`s` 表示源事件是否存在，`c` 表示指定消息通道是否开放；只有这两个科学处理字段可变化。
2. 正式五表按同一 SUMO 时钟记录 state、emission、protocol、action 和 risk。消息“生成、发送、交付、校验、采用”是不同状态，交付不能替代采用。
3. 双走廊路径由封存后的拓扑与状态独立复算。E00 当前结论为物理拓扑断开、`reachable=false`；这只验证路径分析器和场景契约。
4. E15-A 用真实轨迹校验风险“尺子”。NGSIM 有报告前车；pNEUMA 没有可靠前车字段，必须先地图匹配、候选前车推断和人工核验，不能用欧氏最近车辆直接替代。
5. 人工 QA 页把标签暂存于浏览器本地。导出 CSV 前，这些标签不是项目文件，Codex 无法仅凭仓库判断已经标了多少条。
6. E16-A 只按真实字段界定通信可观测性；当前 `RV_RX` 的一行不是一条可核验消息，观测断点也不是丢包。
7. E17-A 先建立 real-real 自然差异基准，再检查 sim-real 覆盖。当前仅有现实参考包，仿真覆盖 Gate 未完成。
8. E01 解析真值通过后仍不能自动冻结阈值。只有 E15-A、E17-A 和容差/实际意义门槛齐全，才能生成并校验 `protocol_lock_v1.1.yaml`。
9. 协议锁之前，E02 必须停止；不得通过降低门槛、改指标、挑种子或查看 locked holdout 来制造正向效应。

## 8. 数据结构与持久化

### E00 五张正式表

- `state.parquet`：运行/场景/cell/seed、SUMO 时间、车辆、道路车道、位置、速度、加速度、前车、净间距、相对速度。
- `emission.parquet`：用于独立复核运动学和派生量的逐步车辆记录。
- `protocol.parquet`：消息 ID、源事件/源车/目标车、生成至采用各时刻、校验布尔量、拒绝原因、载荷与消息种类。
- `action.parquet`：目标车控制命令、实际加速度、安全介入、动作是否分化及配对参考 cell。
- `risk.parquet`：目标车、窗口、指标和值、物理到达边界、归因与纳入状态。

每个 E00 cell 另有 `config_frozen.json`、`provenance.json`、`audit.json`、`run.log`、`topology.json`、`clock.parquet`、`vehicle_lifecycle.parquet`、`manifest.json` 和 `SHA256SUMS`。失败追加到 `failure_ledger.jsonl`，已有 run ID 不可覆盖。

### 校准与人工标签

- calibration 输入用文件清单、来源、分割、SHA-256 和数据边界封存；locked holdout 不能用于调规则。
- v5 人工标注输入为 `map_leader_review_round1.csv`，密封层信息位于 `sealed_sampling_key.csv`。
- 页面导出目标文件名为 `pneuma_map_leader_round1_completed.csv`，字段为：`blind_id`、`reviewed_road_match`、`reviewed_travel_direction`、`reviewed_leader_match`、`reviewer_uncertain`、`reviewer_notes`。
- 当前 v5 目录中尚未观察到上述 completed CSV；页面中的未导出进度属于浏览器本地状态，状态未知。

### 数据库与远端持久化

当前未发现数据库或服务端持久化。GitHub 远端 `origin/main` 与当前 HEAD 一致，但工作树的新实现和产物尚未提交，因此不能把远端仓库视为当前状态的完整备份。

## 9. API 与外部集成

- DRIFT：本地只读上游；AAD 复用其机制概念和映射，不写入其仓库。
- SUMO/TraCI/netconvert：E00 的本地仿真与网络生成依赖。
- NGSIM、pNEUMA、SPMD：本地现实数据资产。SPMD Packet 官方下载在当前环境返回 HTTP 403。
- INTERACTION：旧记录显示尚未获批，不是当前 Gate 的必需通过项；本次未重新核验访问状态。
- 对外 HTTP API、Web 后端、身份认证和部署接口：当前未记录。`review_map.html` 是本地静态人工审核页。

## 10. 构建、运行、测试与部署

| 用途 | 命令 | 证据/结果 | 备注 |
|---|---|---|---|
| 全量测试 | `cd D:\shen\TJU\AAD\code; python -m pytest tests -q` | 2026-09-08 重构后：`164 passed in 58.20s` | 新鲜验证；不包含人工标签正确性、外部 Packet 下载或论文排版 |
| Python 编译检查 | `cd ...\code; python -m compileall -q src scripts` | 2026-09-08：退出码 0 | 新鲜验证 |
| 差异格式检查 | `git diff --check` | 2026-09-08：退出码 0；仅有 LF→CRLF 警告 | 不等于代码已提交或工作树干净 |
| v5 checksum | 比较 v5 `SHA256SUMS` 与目录内六个封存文件的当前 SHA-256 | 2026-09-08：`V5_CHECKSUMS_OK` | 第一次从 `code/` 错写成 `code\code\...` 而未找到路径；修正相对路径后通过 |
| E00 真实运行 | `python scripts\run_e00_sumo.py --output-root outputs\formal\E00 --run-id <唯一ID> --seed <冻结seed> --repo-root ..` | 历史记录：主环境与 clean venv v3 成功 | 不应无理由重跑已有 ID；E00 已通过 |
| E00 独立分析 | `python scripts\analyze_e00_sumo.py <E00包目录>` | 当前主环境包内已有 `independent_analysis.json` | 只读复算 |
| 当前人工 QA | 打开 `code\outputs\formal\calibration\e15a_pneuma_manual_qa_v5\review_map.html` | 页面与 checksum 已验证；人工完成度未知 | 默认只显示 48 条试标；完成后导出 CSV |
| 协议准入检查 | `python scripts\check_protocol_lock_readiness.py --help` 后按已记录参数运行 | 当前已有 readiness：不允许锁定/E02 | 不能绕过 Gate 直接写锁 |
| 论文构建 | XeLaTeX 编译 `paper/主论文/main.tex` | 历史记录曾通过；本次未运行 | 交接中不修改/重建论文产物 |
| 部署 | 当前未记录 | 未验证 | 研究代码仓库，无确认部署目标 |

## 11. 决策与约束

| 决策或约束 | 状态 | 已记录理由 | 来源 |
|---|---|---|---|
| AAD 是当前项目；DRIFT 只读，不修改 | Agreed | DRIFT 是已完成的上游交通流项目，只作参考 | 用户反复纠正；根 README；E00 记录 |
| 科学对象是目标区域总体风险，而非单个目标车风险 | Agreed | 与导师对研究对象的理解一致 | 当前论文对话与主稿 |
| E00 只验证工程链，不写成科学结果 | Agreed | 防止把基础设施成功冒充效应成立 | E00 计划、report、执行记录 |
| E15-A→E16-A→E17-A→E01/协议锁后才进入 E02 | Agreed | 先验证尺子、现实边界、仿真覆盖与预冻结规则 | 已确认执行计划；`code/README.md` |
| 缺失字段不补零，不可观测结论不推断 | Agreed | 避免把缺失误当无效应或无消息 | 论文/实验原则及实现测试 |
| Methods 写定义、模型、设计和统计；Results 写实际观察 | Agreed | 防止前后混写和事后修改方法 | `docs/论文实验推进/README.md` |
| 论文符号先定义后使用；标签上标、索引下标；同体系尽量使用常用英文字母 | Agreed | 导师明确反馈符号体系需统一 | 导师批注对话与主稿修改记录 |
| 解释和证明要易懂、最小必要、不得发散 | Agreed | 用户指出 AI 表达容易复杂晦涩 | 推进管理规则 |
| 本地文献为主要存储，不依赖 Zotero | Agreed | 防止文献丢失并便于项目内管理 | 用户明确决定；`literature/` |
| 每次实验保留失败、空效应、原始产物和 checksum，不因结果调规则 | Agreed | 保持可证伪性与可复算性 | 实验计划与执行记录 |
| 组会计划共 20 个有效工作周 | Agreed as planning record | 阶段 0 两周、阶段 4/5 各四周，其余最多三周 | `记录/9.10组会汇报.md` |
| 根目录只保留 `code/paper/literature/docs/记录` 五个业务文件夹以及必要的根入口文件 | Agreed and satisfied for known root clutter | 用户要求目录整洁且需保留稳定入口 | 2026-09-08 迁移 manifest 与当前根目录 |

## 12. 开发状态

### 已完成且已验证

- E00 真实 SUMO 四格最小包、五表封存、独立分析、mutation tests、失败账本和第二干净环境结构复算已通过。
- E00 四格处理前一致、状态隔离、消息生命周期、统一时钟、车辆生命周期和断开拓扑路径结论均有机器可读证据。
- E01 的解析 TTC/DRAC/PET/碰撞真值与物理路径真值 fixture 当前通过。
- 2026-09-08 受控迁移后，当前工作树代码全量 pytest 通过164项，Python 编译与项目文档校验通过。
- v5 人工 QA 包已生成且当前 checksum 与封存清单一致。

### 正在进行

- E15-A pNEUMA 人工第一轮地图/方向/候选前车审计；当前应先做 48 条平衡试标。
- E15-A NGSIM 风险测量、E16-A 现实通信边界、E17-A 现实参考和 E01 预锁验证已有实现/产物，但各自完整 Gate 未通过。
- 主论文和组会汇报材料持续更新；本次未复核 PDF 视觉版面。
- 大量当前实现和实验文档尚未被 Git 跟踪或提交。

### 已同意但尚未完成

- 人工 QA：试标通过后完成总计 300 条 Round 1；按原计划间隔至少 7 天进行打乱后的 Round 2；无法判断保留 `uncertain`。
- pNEUMA 审计通过后才允许生成 TTC；不通过则不得降低门槛冒充双来源验证。
- E16-A 只有在官方 Packet 可访问且字段 Gate 通过后才考虑 BsmP1 与 Tx/Rx 配对。
- 生成仿真校准样本并完成 E17-A sim-real 覆盖 Gate。
- 冻结 E01 的风险指标、时间步、`delta_eq`、`delta_R`、动作/状态容差、calibration seeds 与 E02 样本量。
- 全部必需 Gate 通过后生成不可覆盖的 `protocol_lock_v1.1.yaml`；之后另行设计 E02。
- 实验产生证据后再补论文相应 Results；Stage II、Discussion 和全文结论不能提前写成已验证结果。

### 已讨论或提议

- NC 是当前冲刺标准，但最终投稿期刊尚未被不可逆锁定；若一般性和现实边界不足，旧交接讨论过收缩到 IEEE Transactions 的可能性。
- 后续跨控制器、跨风险类型、信息图、通信受损、合流与尾部风险实验已在阶段计划中排列，但不属于当前执行面。

### 已知问题与限制

- pNEUMA 没有原生可靠 lane/leader 字段；当前候选关系未经人工验证。
- SPMD `RV_RX` 不能提供发送机会分母、逐包丢失或 controller adoption；Packet 官方资产当前不可访问。
- E17-A 尚未有仿真现实覆盖通过结果。
- E01 尚不能证明 0.05 s 差异已落入冻结零效应容差，因为该容差仍为空。
- 所有 calibration/E00/E01 预锁产物均标为 `scientific_claim_eligible=false`。
- 工作树非常脏且包含大规模重组；误用 `git clean`、`reset --hard` 或 checkout 会丢失当前实现和用户文件。
- 当前 Git 远端不包含大部分最新工作，不能依赖 GitHub 恢复全部状态。

### 阻断

- **人工输入阻断 E15-A：** 必须由用户进行真实标注，AI 不应代替人工判定这些盲样本。
- **外部访问阻断 E16-A 完整消息级分析：** 当前环境访问官方 Packet 返回 HTTP 403。该阻断不允许被解释为 Packet schema 不合格。
- **依赖阻断协议锁/E02：** E15-A、E17-A 和 E01 容差冻结未完成，因此协议锁与 E02 均被机器规则拒绝。

## 13. 精确继续点

### 当前目标

不是继续写论文结果，也不是运行 E02，而是完成 `e15a_pneuma_manual_qa_v5` 的第一轮人工审计入口。

### 最后已完成动作

- v5 QA 包已经生成：300 条盲样本，四个层各 75 条；页面默认勾选“只看平衡试标批次”，共 48 条。
- 2026-09-08 验证 v5 六个封存文件 checksum 全部匹配。
- 2026-09-08 受控迁移后全量测试 `164 passed`，`compileall` 与 `PROJECT_DOCS_OK` 通过。
- 仓库中尚未发现导出的 `pneuma_map_leader_round1_completed.csv`。

### 下一步唯一动作

1. 确保打开的是：`code/outputs/formal/calibration/e15a_pneuma_manual_qa_v5/review_map.html`。旧 v1--v4 都不是当前入口；此前对话环境曾显示 v3 页面，若该标签页仍在，应关闭或忽略并重新打开 v5。
2. 只标页面默认显示的 48 条平衡试标：分别判断道路匹配、行驶方向、候选前车是否正确；证据不足就选 `uncertain`，没有候选前车对象时前车项按页面规则标为不适用。
3. 完成后点击“导出标签 CSV”，保留 `pneuma_map_leader_round1_completed.csv`，再把文件交给 Codex 做只读统计与 Gate 判断。
4. Round 1 完成前不要打开 `sealed_sampling_key.csv`，以免看到抽样层破坏盲审。

### 必须保留的验收边界

- 当前只要求先完成 48 条试标，不把这 48 条当成 300 条完整 Round 1。
- 人工结果不理想时保留真实标签和 `uncertain`，不能让 AI 根据算法结果替人“修正”标签。
- 没有 pNEUMA 人工 Gate 通过前，不生成 pNEUMA TTC，不宣布 E15-A 通过。
- readiness 文件仍为 `protocol_lock_allowed=false`、`e02_allowed=false`；任何继续任务都必须尊重这一停止规则。

### 接手者需要向用户确认的信息

- 浏览器 `localStorage` 中是否已经保存了部分 v5 标注，仓库无法判断；不要覆盖用户尚未导出的进度。
- 用户导出的 CSV 实际保存路径需要在导出后确认。未得到文件前，不猜测完成度或标注结论。

## 14. 文件与文档索引

| 文件 | 用途 | 接手时何时阅读 | 证据状态 |
|---|---|---|---|
| `PROJECT_CONTEXT.md` | 当前交接总入口 | 新对话第一份 | Current |
| `README.md` | 项目边界与旧入口 | 了解历史；其中 2026-08-15 内容可能落后于本交接 | Partly stale |
| `记录/交接/新对话完整交接_2026-08-15.md` | 旧迁移、论文、真实数据与证据边界 | 追溯历史，不覆盖当前机器产物 | Historical |
| `code/README.md` | 当前正式命令、v5 标注入口和边界 | 执行任何代码前 | Current active |
| `docs/论文实验推进/README.md` | 阶段结构和 Methods/Results 分工 | 解释全局顺序时 | Current plan |
| `记录/9.10组会汇报.md` | 20 周组会计划与阶段安排 | 汇报或排期时 | Agreed plan, not completion evidence |
| `docs/论文实验推进/阶段0_基础设施与测量/E00/执行记录.md` | E00 从失败到 Gate 通过的完整记录 | 判断 E00 是否需重跑时 | Verified record |
| `code/outputs/formal/E00/e00_real_sumo_20260907_primary_v3/e00_report.json` | E00 主环境机器可读总结 | 核对四格/时钟/路径时 | Verified artifact |
| `code/outputs/formal/E00/e00_real_sumo_environment_comparison_20260907_v3.json` | 主/clean 环境结构比较 | 核对 E00 可复算性时 | Verified artifact |
| `code/outputs/formal/calibration/e15a_pneuma_manual_qa_v5/audit.json` | 当前人工 QA 规模和 Gate | 开始标注前 | Verified package metadata |
| `code/outputs/formal/calibration/e15a_pneuma_manual_qa_v5/审计说明.md` | 人工标签含义与盲审规则 | 开始标注前 | Current instructions |
| `code/outputs/formal/calibration/e15a_pneuma_manual_qa_v5/review_map.html` | 当前人工标注界面 | 立即下一步 | Active human task |
| `code/outputs/formal/calibration/protocol_lock_readiness_v1.json` | 协议锁/E02 准入状态 | 每次准备跨阶段前 | Current machine gate |
| `code/outputs/formal/calibration/e01_prelock_validation_v2/audit.json` | E01 解析真值与时间步状态 | 冻结容差前 | Partial verified |
| `code/outputs/formal/calibration/e16a_observability_v3/audit.json` | SPMD 现实通信边界 | 讨论 Packet/丢包/采用时 | Current boundary |
| `code/outputs/formal/calibration/e17a_real_reference_v1/audit.json` | 现实参考样本及待完成 Gate | 开始 sim-real 覆盖时 | Partial verified |
| `paper/主论文/main.tex` | 当前论文唯一正文源 | 证据 Gate 后补写相应部分 | Active manuscript |
| `paper/主论文/nature_communications_guidance/README.md` | NC 格式与本地指南入口 | 格式检查时 | Reference |

## 15. 未知、冲突与检查边界

### 未知或需要后续确认

- v5 页面在浏览器中已经完成多少条：未知。标签在导出前只存在本地浏览器存储。
- `pneuma_map_leader_round1_completed.csv` 的未来下载路径：需要用户导出后确认。
- 官方 SPMD Packet 何时能够访问：未知；当前只确认本环境 HTTP 403。
- INTERACTION 申请是否已有新进展：本次未核验。
- 当前主论文 PDF 是否与 `main.tex` 完全同步且版面无误：本次未重新编译/渲染。
- 已知根目录散落工作文件已完成保留式归档；既存的大量已跟踪删除仍属于此前目录重组，来源未逐项确认，不能擅自回滚或清理。

### 明确冲突或版本替代

- 旧交接和旧 README 曾把 DRIFT 轨迹分析或历史双走廊摘要描述为当前主要证据；现在的正式证据层级以 AAD 内 E00、calibration、E01 机器可读产物和当前代码为先。历史 Pilot 只作历史参考。
- E00 `code/environment/README.md` 末段仍保留“正式交通 runner 尚未重建、不能判 E00 通过”的旧 artifact-smoke 表述；同文件前文及 2026-09-07 E00 执行记录和真实 v3 产物已经证明后续真实 runner 与双环境比较完成。此旧句已被后续日期和机器产物替代，本次未修改原文件。
- 先前页面/对话曾使用 v3 或 50 条试标说明；当前代码 README、v5 audit 和页面实现固定为 v5、48 条（每层 12 条）。继续时采用 v5/48。
- 组会文档给出阶段时间表，但时间到期不等于 Gate 自动通过；机器 Gate 和原始证据优先。

### 本次检查限制

- 未打开或逐页审阅全部 PDF、图片和 `review_map.html` 的每个样本；只核对页面代码、包元数据和 checksum。
- 未读取完整大型 NGSIM/pNEUMA/SPMD 原始文件，只使用已经封存的审计摘要和当前实现/测试证据。
- 未重新运行真实 SUMO E00，因为已有不可覆盖的主/clean 成功包且当前任务是交接，不是复现实验；只运行了全量自动测试。
- 未访问网络、未下载 Packet、未修改 DRIFT、未生成协议锁、未运行 E02。
- 本次仅新增本交接文档；没有修改代码、论文、计划或已有实验产物。
