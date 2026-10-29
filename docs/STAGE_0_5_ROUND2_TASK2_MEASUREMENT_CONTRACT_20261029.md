# AAD-S0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029

状态：**Verified offline contract audit; scientific decision pending**。本任务完成离线测量契约审查、候选规则比较、合成边界复现、封存证据复用和 Zotero 查重登记。它没有批准新的科学定义，也没有升级 Stage 0.5 Gate、Stage 0.6、Protocol Lock、Stage I 或第三轮。

## 范围和前置状态

第一轮 Task 1–3 已完成，第一轮科学冻结已获批准；第二轮 Task 1 已完成一次候选运行，固定源区正式 P2=0，Rule A 通过，目标 cohort 有一个事件。`AAD-S0.5-POST-R2-TASK1-20261029` 是本任务的前置离线诊断，结果和历史编号均保留。本任务只读取现有封存 FCD、诊断矩阵、源码和正式配置，并运行 16 个小型内存合成案例；SUMO/TraCI、新轨迹、独立 seed、locked holdout 和参数搜索均为 0。

机器证据包：[RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029](../evidence/results/RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029/)。生成器：[audit_stage_0_5_round2_task2_measurement_contract.py](../code/scripts/audit_stage_0_5_round2_task2_measurement_contract.py)。源码绑定、配置和输入 SHA 在 `source_bindings.json`；包级清单和哈希在 `manifest.json`、`SHA256SUMS`。

## 实际契约审计结果

逐接口矩阵见 `contract_audit_matrix.json`。核心事实如下：

| 维度 | Formal P2 | SUMO native | formal-aligned | D1 | 当前状态 |
|---|---|---|---|---|---|
| TTC | 正净距、正闭合、有限 TTC；`0<TTC<2` | `compute_sumo_measurements` 生成 `ttc_valid` 和状态 | 投影后复用 formal extractor，但不修复矛盾输入 | 额外要求 `measurement_status=valid` 且 TTC>0 | 负 TTC 反例已复现；接口不等价 |
| 阈值/持续/节奏 | 2 s、跨度至少 0.2 s、100 ms、最大间隔 0.11 s | 同一阈值/跨度和 cadence guard | 非 100 ms 明确标为 non-comparable | 100 ms 网格，跨度比较容差为 1e-9 | 工程规则一致；科学等价未批准 |
| 身份 | pair、trajectory、leader trajectory 和时钟连续 | run-scoped `incarnation_id` 与 leader incarnation | incarnation 映射成 trajectory 字段 | run/scenario/vehicle/incarnation 及 leader pair | leader 切换、incarnation 变化均 fail-closed |
| 显式中断 | `identity_break`、`observation_gap` 不得跨接 | `following_link_is_valid` 消费标记 | `build_sumo_formal_source_frame` 将两标记重置为 false | 两端标记必须为 false | 已证实现差异，待研究者裁决 |
| 时钟/帧 | 原始 row/frame 和 absolute clock 可追溯 | observation index、时间和帧增量可审计 | row/frame 是适配器定义的重编号 | 100 ms、frame/global time 增量必须成立 | 持续时间可比，绝对原点语义不同 |
| 车道/路径 | formal P2 不从 lane ID 推断物理路径 | 一般 pair 连续性不要求同 native lane | 投影保留 lane 但不制造连接见证 | 额外要求同 native lane | A/B/C 差异已由合成案例复现 |
| 缺失/Unknown | 无前车、边界、身份不可观测保留 Unknown | no leader=`not_applicable`；身份未解析=`missing` | 保留状态但不能补 NGSIM 来源证据 | `missing`/`not_applicable` 不进入可靠风险 | Unknown 保真，不能解释为安全 |
| P2 与 D1 暴露 | 正式事件资格独立于 D1 分母 | engineering exposure | 事件计数适配器 | 局部 onset attribution + same-lane evaluable links | 三者不可互换 |
| 右删失/重入 | threshold exit、leader switch、continuity break、right censor 分开 | 输出 `exit_reason` | extractor 输出相同词汇 | short/right-censored 候选保留，但不补写全部 exit reason | D1 信息少于 native/formal |

这说明“接口计数一致”不能替代科学等价性。当前源码和合成输入已经证明至少存在 lane、显式 flag 和不一致预测量质量三个契约差异；这不能被用来解释封存源区零事件，因为前置诊断在可靠支持内没有任何 `0<TTC<2` 状态，B00/候选分别只有 30/29 个 `[2,3)` 诊断状态，且没有被 0.2 s 门槛截短的正式风险段。

## 合成边界案例

输入逐行在 `synthetic_case_inputs.json`，逐接口输出在 `synthetic_case_results.json`。每个案例记录事件成员、onset/confirmation/end、leader 和 incarnation、lane/edge、flags、`measurement_status`、TTC、暴露链接、incomplete 候选和拒绝/Unknown 原因；不只比较事件总数。

| 案例 | SUMO native | formal-aligned | D1 | A/B/C 影响 |
|---|---:|---:|---:|---|
| 正常连续跟驰 | 1 个事件，0.0–0.4 s，right-censored | 1 个同成员事件 | 1 个 onset，0.4 s 暴露 | A=B=C，事件成员一致 |
| native lane ID 变化、无连接见证 | 1 个事件，跨 lane | 1 个跨 lane 事件 | 只保留同 lane 的 0.0–0.2 s，后段为短/边界候选 | A/B 暴露 0.3 s；C 暴露 0.4 s、跨 lane 事件成员不同 |
| 有真实道路连接见证的边界 | 1 个跨 edge 事件 | 1 个跨 edge 事件 | same-lane D1 只保留边界前段 | A 截断；B/C 接受连续 pair；B 依赖显式连接见证 |
| 真实换道、无物理路径资格 | native/formal 仍可形成 pair 事件 | 1 个 pair 事件 | D1 切断 lane 边界 | C 保留一般 pair；A/B 将物理路径资格与 P2 分开/拒绝 |
| leader 切换 | 不跨接 | 不跨接 | 不跨接 | 事件数为 0，原因是 leader identity boundary |
| incarnation 变化 | 不跨接 | 不跨接 | 不跨接 | 事件数为 0，保留生命周期边界 |
| `identity_break` / `observation_gap` | 不跨接 | formal-aligned 映射后标记丢失，可继续 | 不跨接 | 直接证明显式 flag 保真差异 |
| 缺帧、非正 TTC、阈值边界 | 缺帧切段；负 TTC 输入可被 native risk mask 接受 | 负 TTC 被 `non-risk event member` 拒绝 | 负 TTC 不成事件；恰好 2 s 不成事件 | 质量和边界行为不可强行统一 |
| 恰好/不足 0.2 s | 恰好成立、不足不成立 | 同一跨度门槛 | 同一跨度门槛并保留 incomplete | 0.2 s 是首末跨度，不是成员数×0.1 的替代 |
| 风险退出后重入、窗口边界、无前车 | 退出与重入分段；无前车为 not applicable | 同一 formal 词汇 | onset attribution 和 right-censored/short 候选分开 | 事件资格和 D1 暴露需分开报告 |

其中“有真实道路连接见证”的 `B` 只表示合成输入中显式提供了 `road_connection_witness=true`；它没有证明任何真实封存 lane transition 具有该物理见证。`C` 的 pair P2 与物理路径资格分层记录，不能把 lane change 自动解释为风险成因。

## A/B/C 候选规则

三者均为待裁决候选：

- **A**：严格要求同一 `native_lane_id`，作为保守的路径代理。
- **B**：同 lane 或有真实道路连接见证，并且 follower/leader/clock 连续；未见证的边界保留 Unknown。
- **C**：以车辆对和时间连续性判断一般 P2，另列 lane change 和物理路径资格。

本包没有把任何候选写入正式生产规则。当前合成证据支持：A 最保守但可能切断真实连接；B 需要可核验的连接见证，避免把任意 lane ID 变化当成连续路径；C 适合把“一般 pair 风险”与“物理路径资格”分层，但它会扩大一般 P2 的候选集合。最终选择、估计对象和是否修改实现由研究者裁决。

## 封存轨迹复用和影响边界

`sealed_trace_reuse.json` 索引了上一份离线诊断的 `diagnostic.json`、边界矩阵、等价性矩阵、反例、源区 segment 表和 54 格诊断表。复用事实为：B00/候选源观察 86234/91058，D1 暴露 8457.4/8900.0 veh-s，可靠支持中的 formal risk states 均为 0，`[2,3)` 状态为 30/29，SUMO/TraCI/新轨迹/holdout 均为 0。本任务没有重复 610k 级轨迹诊断。

因此可以报告“当前可评价支持内未观察到源区正式风险命中”和“接口契约存在已复现差异”，不能报告“整个源区物理上没有风险”、不能把 lane/flag/负 TTC 反例说成当前零事件的已证原因，也不能把 D1 暴露率写成正式科学发生率。

## 文献查重、获取与 Zotero

Zotero 本地健康检查通过（10.0.6）。清单文献按 DOI/正式题名检查全库和 AAD 相关主题集合；Sharma et al. 2019 复用已有 item key `B8J8W6P2`，没有创建重复条目。其余 8 篇已按用途登记：SSAM/冲突指标进入 `01_风险事件与安全指标`（`NXNARCWW`），Hale 进入 `07_微观跟驰校准与轨迹重放`（`PWZDPXEE`）。登记结果和 item key 在 `literature_dedup_acquisition.json` 和 `zotero_registration_result.json`。

| 文献 | Zotero item key | 处理 |
|---|---|---|
| Pu & Joshi, 2008, FHWA-HRT-08-050 | `SLTMG63B` | 元数据登记；官方页面核验；PDF 未获取 |
| Gettman et al., 2008, FHWA-HRT-08-051 | `9LCCTDGZ` | 元数据登记；FHWA PDF 页面核验；PDF 未获取 |
| Gettman & Head, 2003, FHWA-RD-03-050 | `4H9FNF5K` | 元数据登记；FHWA 页面核验；PDF 未获取 |
| Arun et al., 2021, DOI 10.1016/j.amar.2021.100185 | `XVNDBFHV` | DOI/正式题名和作者核验；指标待 easyScholar；全文附件未获取 |
| Lu et al., 2021, DOI 10.1016/j.aap.2021.106403 | `Q9NQASFD` | DOI/作者/期刊核验；合法开放来源已登记；附件未获取 |
| Hu et al., 2022, DOI 10.1093/tse/tdac017 | `3EGJM6N6` | DOI/作者/期刊核验；CityU Scholars 合法全文来源已登记；附件未获取 |
| Tang et al., 2026, DOI 10.1371/journal.pone.0344623 | `VBRW3ZMR` | DOI/作者/期刊核验；PLOS/PMC 来源已登记；附件未获取 |
| Hale et al., 2021, FHWA-HRT-21-071 / DOI 10.21949/1521658 | `MIYY2V2Q` | 报告元数据和官方 PDF 核验；附件未获取 |

本机 PowerShell/Python 外联 socket 被策略阻断，因此没有把未取得的 PDF 伪写成附件，也没有向仓库写入论文 PDF。报告中列出官方/出版商/合法开放来源 URL；指标未能从 easyScholar 核验的条目明确标为待核验，不编造数值。

## 验证、未决事项和 Gate

`validation_record.json`：16 个案例、A/B/C 三组规则输出齐全；负 TTC 拒绝路径、lane 规则差异、连接边界见证均可复现；新 SUMO/TraCI、新轨迹、holdout 和全文附件均为 0。本任务从 `code` 目录执行的完整回归为 **1416 passed、35 failed、4 skipped**；失败清单在 `full_pytest_failure_inventory.json`，逐项 traceback 均指向缺少 `pyarrow/fastparquet` 的 Parquet 依赖。相关测量测试为 62 passed、2 个同类依赖失败，项目文档测试 13 passed，隔离缓存 `compileall` 通过。父诊断已有的 1415 passed、28 个缺少 Parquet engine 的失败、4 skipped 和 7 个原生测试排除继续保留，未被本任务重写为通过。

需要研究者裁决的事项：

1. 一般 formal P2 是否采用 A、B 或 C 的估计对象；B 的“真实道路连接及连续跟驰见证”需要什么可接受证据。
2. formal-aligned 适配器是否必须保真 `identity_break`/`observation_gap`，以及如何处理 simulator 与 NGSIM 的原始时钟/row 语义。
3. D1 的 same-native-lane 暴露是否继续作为局部诊断分母，还是与一般 pair P2 分层报告；在裁决前不改生产实现。
4. 8 篇新增文献的期刊指标和合法全文附件是否由研究者在 Zotero 桌面端完成补全。

Stage 0.5 Gate 仍 `blocked`；Stage 0.6、Protocol Lock、Stage I 和第三轮均保持原状态。科学等价性仍未通过。
