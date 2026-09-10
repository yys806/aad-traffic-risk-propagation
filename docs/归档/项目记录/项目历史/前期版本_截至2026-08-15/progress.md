# Review Progress

## 2026-08-07 Decisive Nonlocal-Risk Experiment
- User requested strict completion of the decisive experiment.
- Recovered the prior 46-run evidence package and confirmed the unresolved issue is outcome identifiability, not communication implementation.
- Entered design-gated workflow: audit context, compare architectures, obtain design approval, then write spec/plan and execute with TDD.
- No new experiment code or rollout has been started before design approval.
- User approved a dedicated physically disconnected dual-corridor SUMO network; final architecture and frozen decision gates are being presented for approval before implementation.
- Wrote and self-reviewed the approved design spec and the eight-task TDD implementation plan; no placeholders remain.
- Verified the existing linked worktree and branch `experiment/nonlocal-pilot-a`; fresh baseline is 77 passed in 9.39 s.
- Started Task 1 RED tests for topology and trial invariance.
- Task 1 RED failed as expected because `mixlab.decisive_trial` was absent.
- Implemented pure dual-corridor topology/path auditing and the minimal decisive trial coordinator; focused tests are GREEN (6 passed).
- Completed controller integration for source braking, target-leader hazard injection, provenance-gated message delivery, and receiver adoption; focused decisive/risk tests reached 43 passed.
- First real SUMO preflight exposed an unknown `av` vehicle type because the inflow-only type was not registered; fixed the builder to register a zero-count type and reran successfully.
- The original -5.5 m/s2 for 1.0 s target pulse produced no positive TTC burden (minimum TTC about 3.26 s), so it was rejected before formal runs.
- Locked -8.0 m/s2 for 7 steps after 24 calibration runs: 24/24 valid, zero collisions, zero event-invariance failures, mean calibration delta_NL=-0.126852 with bootstrap 95% [-0.129074, -0.124543].
- Wrote the frozen formal configuration and calibration lock (SHA256 D72C3C86C79CBAA3DE9DD2BEDC958906BB00B4F89F7ABB849794E71E8AC6E5CF).
- Started four parallel CPU-only formal cell runners for seeds 2026080701--2026080720; formal results are not interpreted until all 80 runs complete.
- Formal run completed: 80/80 valid runs, zero collisions, all eight support gates passed. `Delta_NL` mean=-0.1312075, paired bootstrap 95% CI [-0.1320726, -0.1303981], sign-permutation p=9.999e-05; 20/20 paired seeds were negative.
- Final full regression: 96 passed and `compileall` passed.
- Independent communication validations completed 36/36 runs: wrong-source, wrong-time, and delivery-only each had zero adoption; medium/severe dose produced 12/2 adopted steps; all validation gates passed.
- Merge-transfer preflight was rerun as a separate four-cell check after two real defects were isolated: Flow merge uses `sims_per_step=5`, which misaligned mechanism steps with state rows, and stale controlled IDs could be selected. The transfer runner now freezes `sims_per_step=1`, filters snapshots against active IDs, and restricts target candidates to the pre-junction `left` edge.
- The corrected merge preflight (`outputs/decisive_merge_preflight_v7`) completed all four cells with the same event and adoption at step 96, no collisions, and pre-adoption target identity. However, all four cells had `I_TTC=0` and minimum TTC 2.92--3.15 s, so `Delta_NL=0`; the pre-registered transfer expansion is stopped rather than interpreted as an external effect.
- A new communication-blind merge calibration tested target braking durations 8, 9, and 10 steps on six `r00/r10` seed pairs. Eight and nine steps produced no positive TTC burden; ten steps produced positive burden in 6/6 seeds per cell, median minimum TTC 1.9404/1.9400 s, zero collisions, invariant events, and identical pre-hazard target trajectories. The lock froze `epsilon_merge=0.0010993341` with SHA-256 `4AE33DF49ECFA0390FBAF251A1D1655EC6A472458543899EBF5AEEA5088807AA`.
- The locked connected-merge formal experiment completed 80/80 CPU runs (20 seeds x 4 cells), with 80 non-empty state/protocol/risk/emission units and zero collisions. Mean `Delta_NL=-0.0069459`, bootstrap 95% CI `[-0.0095418,-0.0042398]`, and sign-permutation `p=0.00049995`, but only 12/20 seeds were negative and only those 12 formed a realized source event and message adoption. The other eight had zero effect because the source failed the three-consecutive-step realized-braking gate. Therefore the preregistered merge-transfer support decision is false despite the negative mean.
- Structured source audit shows six failed seeds selected a stationary `av_5`, one selected a nearly stationary `av_5`, and seed 2026080814 realized only two consecutive braking steps before leaving the source edge. Among the 12 realized/adopted seeds, 12/12 effects were negative; this is mechanism-conditional descriptive evidence, not a replacement primary analysis.
- Full regression after the locked merge workflow is 133 passed; focused merge analysis/calibration tests are 41 passed and `compileall` succeeds.
- The updated weekly document now reports the formal evidence, the corrected merge preflight, and the evidence boundary. The merge transfer is not counted as support for the nonlocal risk effect.


## 2026-08-06 Real-risk Communication Experiment
- User authorized complete implementation and execution of the approved Section 3 experiment design.
- Completed repository, worktree, WSL, CPU, memory, Flow, and SUMO environment audit.
- Confirmed the task is CPU-capable; no model retraining or GPU dependency is currently planned.
- Adopted test-first implementation and persistent experiment/configuration/error logging.
- Froze the implementation plan at `docs/superpowers/plans/2026-08-06-real-risk-communication-experiments.md`.
- Added 8 pure mechanism tests. The first run failed as expected because `mixlab.risk_communication` did not exist.
- Implemented the one-event coordinator, realized-braking validation, deterministic risk channel, severity mapping, and transparent action helper; all 8 tests pass in WSL.
- Integrated the coordinator and risk channel into `OursFullController` without changing the ETA pilot or the baseline local controller.
- Added exact message provenance checks, wrong-source/wrong-time placebo modes, delivery-only mediation, impaired communication, leader-aware TTC analysis, paired factorial effects, and empirical physical-arrival auditing.
- Completed 46 CPU rollouts: 2 preflights, 32 main factorial runs, 8 gated-risk runs, and 4 independent validation runs; all completed with zero collisions.
- Main mechanism audit passed: R10 and R11 each produced 8/8 valid realized source events; R11 adopted all 8 and R10 adopted none. Main `Delta_NL` was zero in all four context summaries.
- Gated p60 effect was -0.0004028569 with descriptive 95% interval [-0.0013990223, 0.0005933085]; p80 was zero. No statistically supported safety outcome was claimed.
- Wrong-source, wrong-time, delivery-only, and impaired-channel logs behaved according to the frozen causal switches; topology checks found no direct source-receiver adjacency and no observed R10-vs-R00 receiver divergence within the horizon.
- Corrected two analysis defects with regression tests: exact emission-file selection and the one-step controller/emission time alignment. Recomputed all affected outputs.
- Updated `8.5-8.11推进.md` with actual counts, effects, independent validation results, the uncompleted disconnected-branch experiment, and a current NC No-Go / IEEE-conditional assessment.
- Formal 160-run expansion was deliberately deferred because the predeclared smoke gate failed to produce measurable target risk; the next scientific task is scenario redesign, not more seeds on the same null setup.
- Final verification: 77 focused/regression tests passed, `compileall` passed, both analysis CLIs reported zero errors, all 12 risk configs parsed, 46 summary runs audited with zero collisions, and the updated Section 3.4 table has no malformed rows or replacement characters.


## 2026-07-18 Local Propagation Baseline
- Added `code/src/riskprop/local_propagation_baseline.py` for eligibility, local candidate edges, direct parent selection, chain traversal, run/cell summaries, circular time-shift nulls, and threshold sensitivity.
- Added `code/src/riskprop/local_propagation_visuals.py` with ten figures and a figure catalog.
- Added `code/scripts/build_local_propagation_baseline.py` as the reproducible CPU-only runner.
- Added local baseline tests and visual tests. Focused tests passed before the formal run.
- First full 100-permutation attempt exceeded the command timeout. Profiling showed serial per-run permutations were the bottleneck, so the null model was parallelized while keeping the same permutation count and seed design.
- Formal output was generated at `code/outputs/local_propagation_baseline_20260718`: 2,057 eligible episodes, 2,315 candidate edges, 1,294 direct edges, 763 chains, 214 multi-hop chains, and maximum depth 24.
- The formal CLI was rerun twice with `--permutations 100 --seed 20260718 --workers 8`; the second same-version hash comparison found 21/21 CSV/JSON/PNG files unchanged.
- After visual inspection, the representative-chain figure was simplified to label only selected hops; all ten figures were regenerated and inspected.
- Final verification: `python -m pytest -q` passed with 52 tests in 45.70 s; `python -m compileall -q src scripts` passed; all ten PNGs are readable, larger than 10 KB, at least 900 x 500, and nonblank by pixel variance.
- No GPU was used.

## 2026-07-18 Quantum Literature Review
- Started a source-verified review separating physical Bell nonlocality, quantum causal models, quantum-like decision models, and traffic relevance.
- The review will treat physical nonlocality as a conceptual boundary unless direct traffic evidence exists; terminology similarity alone is not evidence.
- Checked the local workbook: Song (2022) on quantum decision-making and Asano (2017) are present; foundational Bell/quantum-causal papers and Song (2022) on quantum cognition in autonomous driving are absent.
- Completed the three primary-source search streams and verified the core DOI list.
- Reached the working conclusion that quantum physics does not support a traffic nonlocal mechanism; quantum-like cognition is an optional behavioral model; quantum causal discovery algorithms are inapplicable to classical trajectory inputs.
- Main paper and weekly report remain unchanged pending the user's decision on literature-table additions.

## 2026-07-16 Event Taxonomy And Full Extraction
- Started the CPU-only follow-up after the DRIFT qualification audit.
- Scope fixed to event taxonomy, full extraction, exposure-normalized rates, threshold sensitivity, and review samples; paper text remains unchanged until results stabilize.
- Added red-green tests for non-overlapping braking labels, override-candidate isolation, episode severity, formal file discovery, vehicle-time exposure, sensitivity rates, baseline comparison, and deterministic review sampling.
- Implemented the event taxonomy and the formal dataset extraction script; focused tests pass (22 passed).
- Processed all 270 adopted/formal DRIFT, FS, and PI emission files on CPU.
- Corrected THW validity so it requires a valid leader, positive finite headway, and positive speed; override candidates no longer create combined near-miss labels.
- Added adjacent-frame leader, lane, headway, acceleration, entry/exit, transition, and adjacent-override flags.
- Completed the stratified 60-episode checklist and generated exposure-normalized event rates plus TTC/braking threshold sensitivity tables.
- Final verification: 39 tests passed, source/scripts compiled, and an independent audit reproduced all event/sensitivity aggregates from the per-run tables.

## 2026-07-16 DRIFT Qualification
- Located and inspected the authoritative upstream DRIFT code and final experiment package.
- Read the main benchmark, statistical support, candidate-fit, strict-ablation, selector/feasibility, and OOD tables.
- Confirmed that the existing claim boundary is safety-efficiency-executability trade-off rather than universal metric dominance.
- Identified downstream pilot input anomalies that block risk-propagation use until the emission interface is repaired and verified.
- Started a reproducible DRIFT qualification audit; no GPU is needed for this phase.
- Added tested qualification utilities for formal coverage, mean comparisons, 95% CI comparisons, raw emission auditing, validated event extraction, and extreme-deceleration catalogs.
- Corrected TTC extraction to require a valid leader and added Flow `edge_id:lane_number` adaptation.
- Audited 90 final DRIFT emission files and rebuilt risk events from five final merge-p20 runs.
- Generated `code/outputs/drift_qualification_20260716/DRIFT资格验证报告.md` plus JSON and CSV evidence tables.
- Final verification: 24 tests passed; all source and scripts compiled; the audit reproduced the expected 54/54 coverage and 15 merge-p20 extreme speed-jump records.

## 2026-07-12
- Started a read-only project review.
- Inspected the top-level directory.
- Confirmed that the folder has no Git metadata.
- Read `README.md` and `毕业设计与论文课题固化.md`.
- Extracted the fixed research objective, documented pilot baseline, and stated limitations.
- Inventoried all project files.
- Read `code/README.md` and `docs/可行性验证报告.md`.
- Confirmed the split between implemented CSV analysis and planned DRIFT/Flow counterfactual execution.
- Read package metadata and the main pipeline orchestration.
- Read event extraction, episode coalescing, relation construction, direct-edge selection, role scoring, summary metrics, and intervention screening.
- Read the full test suite and the existing-real-run analysis script.
- Read the experiment roadmap and the real smoke configuration.
- Cross-checked the documented pilot numbers against the actual CSV outputs and inspected event, relation, lane, and intervention-candidate distributions.
- Read the LaTeX paper template and literature module index.
- Ran the full test suite successfully (10 passed).
- Reproduced the real-result episode and graph summary in a temporary directory.
- Verified a clean full LaTeX/BibTeX build in a temporary directory.
- Scanned the project for placeholders, stale paths, counterfactual claims, and unfinished metadata.
- Inspected the synthetic feasibility runner and counted literature/bibliography coverage.
- Completed the repository review and recorded the remaining decisions needed before systematic experiments.

## Venue Research
- Started venue selection research before changing the main paper.
- Verified official scope and author guidance for T-ITS, TR-C, T-IV, AAP, TSE, JITS, ITSC, IV, and TRB.
- Compared venue expectations against the current code, pilot evidence, and planned contribution.
- Reached a provisional recommendation: T-ITS primary, TSE backup, ITSC 2027 conference contingency.
- Located the existing T-ITS `IEEEtran` manuscript at `D:\shen\research\doc\paper\test.tex`.
- Created an independent Chinese T-ITS manuscript package under `paper/tits_cn/`.
- Compiled the manuscript through XeLaTeX/BibTeX/XeLaTeX/XeLaTeX into a five-page PDF.
- Visually inspected all five pages; tables, equations, Chinese text, figures, headers, and references render correctly.
- Re-ran the analysis test suite: 10 tests passed in 2.54 seconds.
- Created `docs/weekly_report_20260712/main.tex` as a standalone A4 weekly report with a front-loaded review of prior work.
- Compiled and visually inspected the six-page weekly report PDF; all text, tables, figures, headers, and page breaks render correctly.
# 2026-07-18 Full Risk Event Visual Package
- Added `code/src/riskprop/risk_event_visuals.py` with 12 reproducible full-dataset figures and a traceable figure catalog.
- Added `code/scripts/render_risk_event_visuals.py` and integrated figure regeneration into `extract_full_risk_events.py`.
- Added `code/tests/test_risk_event_visuals.py`; the initial test failed with the expected missing-module error before implementation.
- Focused visual tests passed: 2 passed.
- Full suite passed: 41 passed in 34.34 s.
- `python -m compileall -q src scripts` passed.
- Re-ran the complete 270-file extraction in 518.8 s. Counts remained 1,609,149 rows, 6,933 events, and 4,131 episodes.
- Verified eight key output hashes were unchanged after rerun.
- Verified 12 catalogued PNG files are readable, at least 900 x 500, larger than 10 KB, and nonblank by pixel variance.
- Visually inspected every figure; corrected title/legend overlap in four multi-panel figures and rerendered them.
- No GPU used.

## 2026-07-21 Project Reappraisal
- **Status:** in_progress
- Loaded the repository's existing review context and confirmed that substantial qualification, event-taxonomy, visualization, and local-baseline work already exists.
- Selected a repository-first, literature-grounded review workflow; explicitly excluded the reproduction workflow because no execution or retraining was requested.
- Started a fresh consistency audit focused on separating current evidence from roadmap claims and developing independent, falsifiable alternatives.
- Inventoried the current repository and identified five literature modules, local full-text extractions, structured digests, recent formal outputs, a current weekly report, and a README updated today.
- Read both current README files and recorded the divergence between the generic pipeline documentation and the newer DRIFT-only local-baseline narrative.
- Began the manuscript consistency audit and flagged unimplemented DRAC, unresolved physical-event duplication, and the difference between a graph residual and a conditioned causal residual.
- Read the event extractor and local-baseline implementation; identified cross-label duplication, overlapping-episode directionality, topology simplifications, heuristic parent selection, and limits of the circular-shift null.
- Quantified those effects directly from both output packages, including duplicate-node coverage, temporally overlapping edges, chain composition, context strata, and multiple-testing sensitivity.
- Recomputed graph summaries under strict temporal succession and overlap-based physical-process collapse; this sharply reduced DRIFT edge and multi-hop counts and changed the statistical interpretation.
- Audited the structured literature metadata and bibliography, then defined five review perspectives to prevent the existing project-oriented digests from anchoring the synthesis.
- Re-read the original Wang risk-graph, Lyu causal-prediction, Runge PCMCI, and Luo cascading-risk papers; corrected the project's earlier interpretation of what each graph or causal claim represents.
- Re-read nonlocal traffic, closed-loop generation, dense safety learning, active-inference behavior, and quantum-game papers; identified information horizon as the testable traffic mechanism behind a stronger alternative framing.
- Compared the written collision-conflict scope with extracted events and found that most hard-braking nodes lack low-TTC/low-THW proximity evidence at onset, especially in the all-method/ring results.
- Read the upstream DRIFT controller and experiment builder. Confirmed that rollout horizon is not sensing horizon and discovered an adopted, hard-coded cross-branch ETA-yield mechanism that should become the primary intervention target and be explicitly logged.
- Completed five-perspective grounded dialogue synthesis and a targeted external gap check; identified two communication-topology/cascading-collision papers as higher-priority additions than generic quantum or graph references.
- Synthesized a mechanism-centered research question, three contribution layers, a minimal paired intervention, alternative routes, and explicit evidence gates.
- Final verification passed: recomputed the DRIFT-only counts and artifact sensitivities, confirmed the cross-branch ETA-yield interface, validated the five-sheet literature workbook, and confirmed no upstream DRIFT worktree changes.
- A final reference-line lookup failed because PowerShell parsed an embedded double-quoted regex as path fragments; logged the error and switched to simpler single-quoted searches.

## 2026-07-25 非局部问题文献调研
- **Status:** complete

## 2026-08-02 显式通信与主论文同步推进
- **Status:** in_progress
- 用户授权按既定计划持续推进，补满 `7.29-8.4推进.md`，并直接修改 `paper/主论文` 下的 TeX 文件。
- 已恢复旧计划、发现和进度记录；确认 Pilot A 已完成，但其证据层级仍是理想 ETA 机制冒烟基线。
- 已锁定真实性规则：没有可复现实验或已核验来源的内容不得写成事实性结论。
- 已盘点周报、代码输出和主论文：周报只有标题；主论文是局部基线旧稿，参考文献存在缺失元数据记录。
- 已选用现有 IEEEtran 主论文包继续修订，不新建重复论文工程。
- 已完整读取 2026-07-29 交接文件和 Pilot A 汇总，确认上游仓库、隔离 worktree、WSL 运行副本及不得整包覆盖的版本边界。
- 已按 worktree 规范确认 `experiment/nonlocal-pilot-a` 是独立 linked worktree，且保留上周 3 个修改文件、1 个新增模块和测试目录。
- 已读取 Pilot A helper、12 项测试和上游 diff，确认显式通信需要新增网络通道状态机，而不是改名现有 ETA 日志。
- Windows `compileall` 通过；专用 pytest 因缺少 `flow` 在收集阶段退出，已转向既有 WSL 运行环境验证。
- 第一次 WSL pytest 因测试路径不存在而未运行任何测试；已记录错误，下一步先枚举真实目录，不重复该命令。
- 第二次 WSL pytest 使用挂载测试路径，但因缺少额外 Flow 源码路径在收集阶段退出；`compileall` 对 worktree 源码仍成功。
- 恢复 `/home/shen/shen/paper_repos/flow` 后，worktree 基线为 12 passed（9.03 s）；可以开始 TDD 实现显式通信。
- Task 1 完成：确定性 ETA 消息通道经历 RED（8 failed、12 passed）和 GREEN（20 passed），参数验证与全局 RNG 隔离均有测试。
- Task 2 完成：控制器通信接入经历 RED（5 failed、19 passed）和 GREEN（24 passed）；禁止 oracle 回退、延迟 payload、缓存过期和完整日志均有测试。
- Task 3 完成：多 seed、profile/condition token、通信参数校验与四份配置已实现；33 tests passed，配置审计为 4×8=32 次运行。
- 已开始 Task 4，核对真实 emission schema 和 Pilot A 汇总代码；确认需要从 headway/relative speed 重建目标区 TTC。
- 已复用现有 leader-aware TTC 定义并发现单独 left 主线区在 Pilot A smoke 中无 TTC<2 s，正在据真实 edge 分布收敛目标区。
- Task 4 核心模块完成：5 tests passed；目标区改为下游合流冲突区，CLI 待真实 Pilot B 输出后完成。
- Task 5 已完成 WSL prepatch 备份和哈希核验；确认需对旧版 runner 做最小 stress-profile/多-seed 移植。
- WSL 最小补丁通过 33 项真实代码测试；四条件 p60 preflight 全部成功，oracle 与 comm-ideal 指标一致，受损通信出现可识别偏离。
- preflight 独立审计通过：0 errors、字段完整、oracle/comm-ideal emission 逐值相同；获准进入完整 32-run smoke。
- 恢复并核对既有非局部交通、通信拓扑、级联风险、时序因果与 DRIFT 跨支路 ETA 机制结论。
- 通过 OpenAlex、arXiv、Semantic Scholar 与出版社/IEEE 原始页面补查近三年文献；记录检索空缺，不把低精度搜索结果当成证据。
- 已在后台打开 IEEE 文献 10499221；页面加载完成并确认题名，待提取其原始摘要和图定义后关闭。
- 核对 IEEE 原始全文后确认其 dynamic conflict graph 是车辆组协同排序/轨迹规划图，不是风险传播图。
- 核对网络干扰、反事实安全干预与交通—通信耦合原始摘要，形成暴露映射、三图分离、三层定义和 E0–E4 证据门槛。
- 已关闭本轮及上轮调研创建的三个后台浏览器标签页；未修改代码或论文。

## 2026-08-02 Pilot B final correction and manuscript update
- Added regression coverage for penetration parsing with stress-profile suffixes and channel reset between Flow runs.
- Isolated invalid runs, reran only affected cells, copied all raw/corrected outputs into the downstream project, and regenerated a 32-cell valid summary.
- Filled the weekly progression document and updated `paper/主论文/main.tex` plus verified communication bibliography entries.
- XeLaTeX/BibTeX/XeLaTeX/XeLaTeX completed successfully and produced a 10-page PDF.

## 2026-07-26 周推进文档完善
- **Status:** complete
- 已向用户解释：远端机制是跨越普通逐车/逐区物理链的显式信息或控制通道；机制启停点应改称激活/退出条件；开关实验只屏蔽指定远端输入或控制边，不关闭整个控制器。
- 检查了现有周推进文档，确认 1.2 将拓扑边界、机制边界和等距切分并列，存在区域定义随实验机制变化的问题。
- 决定采用稳定的两层划分：名义固定长度作为基础，拓扑变化作为强制边界；机制状态仅作属性，不参与切区。
- Chrome 与 Edge 的 CDP 远程调试均未开启，新的网页检索暂不可用；继续使用项目已保存的一手 PDF 和 2026-07-25 已核对的出版社/IEEE 记录，不将未核实检索结果写入文档。
- 已更新 `7.21-7.28推进.md`：重构区域边界算法与跨支路距离定义，补齐 10 篇核心文献对比、本项目目标、5 条拟创新点及 3 项本周小实验。
- 完成结构化验收：15 项检查全部通过；10 条 DOI 文献行、26 个成对展示公式标记、299 行 UTF-8 文本、0 个表格列错误、0 个乱码字符，第一部分无具体 merge 坐标。
- 按用户反馈将周记录从论文式表述压缩为个人汇报提纲：299 行/约 20 KB 缩减为 155 行/约 7 KB；文献表保留 8 篇核心对照，区域公式、跨支路距离、因果效应和 20 次 pilot 设计仍保留。复核结果为 0 个缺失要点、0 个表格列错误、0 个乱码字符。

## 2026-07-26 非局部 Pilot A
- **Status:** in_progress
- 用户已授权持续执行到实验结束；范围锁定为区域尺度分析、ETA 日志/开关、固定种子配对和 p60/p80 共 4 次冒烟仿真。
- 已恢复项目计划、研究发现和进度记录；确认上游 Git 仓库位于干净 `main`，下游目录不是 Git 仓库。
- 已开始按 writing-plans、using-git-worktrees、executing-plans、TDD 和 verification-before-completion 流程执行。
- 已在 `C:/Users/Lenovo/.config/superpowers/worktrees/code/nonlocal-pilot-a` 建立 `experiment/nonlocal-pilot-a` 隔离 worktree；未改动上游 `main`。
- 基线验证：下游 `python -m pytest -q` 为 52 passed（40.98 s）；上游仓库没有 pytest 测试（exit 5），但 `python -m compileall -q mixlab scripts` 通过。
- WSL 运行环境已确认：`/home/shen/shen/mixed_autonomy_lab/.venv` 存在，系统 Python 3.12.3，SUMO 1.18.0 位于 `/usr/bin/sumo`。
- 区域尺度正式脚本已运行：纳入 p60/p80 的 46 条合格 episode；25/50/75 m 分别得到 39/21/18 个暴露区域和 5/4/4 个风险区域，输出位于 `code/outputs/nonlocal_pilot_a_20260726/region_scale`。
- Windows 隔离 worktree 新增 12 项 ETA/日志/seed 测试并全部通过；compileall 与 `git diff --check` 通过。
- 同步前哈希审计发现 WSL 正式运行代码不是 Windows `main` 的逐文件副本；已停止整文件同步，转为对 WSL 当前版本做备份后的最小补丁移植。
- WSL 当前版本已备份到 `backups/nonlocal_pilot_a_20260726_prepatch`，随后仅移植 ETA 模式、日志、控制器参数覆盖和 seed 接口；针对 WSL 实际代码的 12 项测试与 compileall 通过。
- 2 步真实预检通过；随后 p60/p80 × on/shadow-off 共 4 次、每次 120 步的仿真全部正常退出，配置 seed 均为 20260726，实际 SUMO seed 均为 13269。
- 配对汇总通过：p60/p80 on 实际应用 651/749 次；shadow-off 候选触发 629/625 次但应用 0 次；首次应用 9.6 s、首次轨迹分化 9.8 s，处理前车辆键和值完全一致。
- 原始仿真、机制日志、运行日志和配置已复制到 `code/outputs/nonlocal_pilot_a_20260726/simulation`；汇总位于 `pilot_summary`。
- 最终验证：下游 62 tests passed、compileall 通过；WSL 实际运行代码 12 tests passed、compileall 通过；区域与汇总共 16 个文件重复生成后 SHA256 全部不变。
- 独立输出审计通过：4 个 emission、4 个字段完整的机制日志、2 个配对检查、3 个区域尺度、0 个 runner errors；WSL 预补丁备份的 3 个 SHA256 全部校验为 OK。
- **Status:** complete
# 2026-08-03 第二部分文献详述与 Zotero 入库

- 读取并审计 `7.29-8.4推进.md` 第二部分，确认共 7 篇核心文献。
- 以原文、作者版、正式摘要和本地全文为证据，逐篇补写“解决的问题、使用的方法、结果与结论、对本课题的启发”，第二部分扩展为 6630 个字符。
- 修正 Hasan 论文与本课题实现的边界：消息全生命周期和ETA过期禁用属于本课题延伸，不是该文原方法。
- Zotero 查重后新增 Hasan 2023、Razzaghpour 2023、Wang 2025 三条题录；原有 Wang 2024、Liu 等、Huang/Du、Hui/Zhang 四条不重复创建。
- 7个论文条目均进入 `风险图传播/04 非最近邻信息、通信与控制` 并添加 `7.29-8.4新增文献` 标签；相关交叉集合保留。
- 父条目附件路径核验未通过，7篇均标入 `98 待补PDF`。5个由文件接口误建的独立 `document` 已移入 Zotero 回收站；本地合法PDF仍保留。
- 文档验证：7个论文小节均各有4个证据块，旧过度表述为0，UTF-8替换字符为0。
- Zotero验证：7个父条目均为 `journalArticle`，DOI、作者、期刊、年份、标签和集合已逐项读取；5个误建条目均显示可恢复的 `In Trash`。

# 2026-08-03 第5—7篇论文详细解释

- **Status:** in_progress
- 已确认三篇准确题录及周报中的现有证据边界。
- 已加载 planning-with-files、literature-review 与 web-access 规范，建立统一解释框架和四个审视视角。
## 2026-08-03：第5—7篇论文详细解释

- 已核对推进文档中的第5—7篇题名、DOI、arXiv记录和本地全文位置。
- 已完成第一轮原文级事实核验：研究问题、主要模型、核心结论和与本课题的边界。
- 下一步：从本地全文提取关键定义、方程、定理假设和数值实验设置，形成可直接用于汇报的详细中文解释。
- 已提取第5篇条件高斯/条件AVaR与图拓扑实验、第6篇稳定性定理与五组数值实验、第7篇非局部ARZ及混合交通扩展的关键段落。
- 已核验第7篇稳定条件、环路/离散参数、前视距离与渗透率对比的精确设置；已核验第5篇二阶随机延迟车辆模型与通信图假设。
- 已核对可公开引用的三篇主来源；第6篇 HTML 全文可直接逐条支持模型假设与稳定性结论，第5/7篇细节由本地全文与公开 arXiv 记录交叉核验。
- 已完成三篇的解释素材闭环，能够区分：定理证明、数值案例、作者结论与针对本课题的推论；准备输出最终中文讲解。

## 2026-08-08 修正后的合流决定性实验

- 用户授权继续执行修正后的决定性实验。
- 已确认仍在隔离工作树 `experiment/nonlocal-pilot-a`，没有遗留的Flow/SUMO实验进程；此前未提交依赖改动保持不动。
- 已复核旧正式实验的失败结构：12个有效源事件全部为负效应，8个无效源事件全部为零效应。
- 已定位代码根因：源车候选仅按源边位置排序，缺少触发前的最低速度和剩余路段资格检查。
- 当前阶段只推导并冻结物理资格条件，尚未启动任何新正式效应实验。
- 已冻结补充预注册：最低速度2.7 m/s；剩余距离不少于触发速度乘0.8 s；两条源边长度均为100 m。
- 新资格种子为2026081191—2026081196，smoke种子为2026081182，正式种子为2026081101—2026081120；项目检索未发现这些种子被使用。
- 设计与实施计划已分别提交为 `94cdd72` 和 `8863b2c`。
- 实施前全量基线为133 passed（21.27 s）；WSL同时打印localhost/NAT环境警告，但测试退出码为0且无失败。
- Task 1 RED已确认：资格公式与选择测试在收集阶段因缺少 `source_minimum_speed` 按预期失败；这证明新测试覆盖的是尚未实现的行为。
- Task 1 GREEN：新增触发前最低速度、保守剩余距离和等待逻辑；旧版无资格映射的选择行为保持不变。决定性/风险聚焦测试48 passed（6.06 s），提交 `c066d47`。
- Task 2 RED按预期因缺少version-2协议常量失败；首次GREEN回归暴露 `get_position` 补丁命中相似函数，已按堆栈定位并用两项原始失败测试验证修复。
- Task 2最终聚焦回归75 passed（8.61 s）；version-1的20配对正式输出重新分析后协议锁审计仍为true、均值保持-0.0069458928，提交 `9f9a455`。
- Task 3 RED按预期因资格分析模块不存在而失败；GREEN后新增仅审计源资格/真实制动的六种子分析器、单一r10串行运行器和SHA-256补充锁。
- 资格分析测试10 passed（5.63 s），`compileall`通过；分析输出不包含TTC负担或通信效应，提交 `58e6493`。
- 六种子源资格仿真串行完成（约260.9 s）：6/6完整，6/6源事件满足资格，6/6至少5步连续真实制动，0碰撞；补充锁哈希为 `7E4DC444DA9C44C69D6D997D6491F778FDC62801004B12C84ACB6BA2D1E92E32`。
- 四格smoke种子2026081182完成：事件不变性、采用前目标一致性、r11采用、控制格零采用、采用早于分化、r11源事件形成和零碰撞均通过；单次效应仅作协议检查，不进入正式统计。
- 补充锁正式分析器经历缺模块RED后完成；45项聚焦测试和158项全量测试通过，`compileall`与Bash语法通过，提交 `8f9ca67`。
- 修正后的正式合流实验以串行CPU完成80/80个单元；四格各20个固定新种子，协议、state、机制、emission和summary产物均完整，0碰撞且无运行异常。
- 正式分析按冻结计划只执行一次：`Delta_NL=-0.0102834018`，bootstrap 95% CI `[-0.0119462976,-0.0082990135]`，符号置换`p=9.9990001e-5`，18/20个配对为负。
- 14项资格、机制、时序、协议和统计判据全部通过，正式判定`supports_qualified_merge_transfer=true`；保留`supports_dual_corridor_claim=false`以明确本实验不提供物理断开拓扑证据。
- 已将首轮失败、事前修正、正式结果和证据边界写回`8.5-8.11推进.md`；NC路线的剩余关键缺口更新为严格理论定义、真实数据校准和外部验证。
- 用户确认将真实数据/外部验证移到下一周；本周先完成理论整理。
- 已形成《类超距作用理论整理_2026-08-08.md》冻结稿：定义交通状态、物理交互图、信息交互图、潜在结果与`Delta_NL`；区分机制支持、物理断开强证据和合流场景迁移证据；列出必要条件、证伪条件及与非局部交通流/V2X/网络干扰/量子超距的边界。
