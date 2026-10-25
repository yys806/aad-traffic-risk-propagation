# Stage 0.5 追加式预算与账本契约 V2

Agreed：2026-10-25研究者当前任务明确取消后续研究的三次累计上限，允许预算工程与计划准备，禁止未确认计划启动SUMO。

## 独立任务与历史保护

新任务`AAD-0.5-INTERACTION-RESEARCH-V2`；配置`code/configs/stage_0_5_interaction_research_v2.json`。`maximum_new_trajectory_attempts=null`、`cumulative_wall_s=null`、workers=1。null明确表示无累计上限，不是0或Unknown。旧任务不修改；配置绑定旧预检/执行账本、旧最终计划、旧确认和DS提案SHA。

追加账本`docs/audits/stage_0_5_interaction_research_v2/execution_events.jsonl`，初始仅task_created、实际attempt=0；每个事件带seq、UTC、task_id、run_id、前一事件SHA和本事件SHA。只append/fsync，不重写旧行；独占锁防止并发预约。同一文件已有则拒绝初始化。异常半行/链损坏/配置漂移均fail closed，保留原文件并要求显式恢复，不自动截断；哈希链不是针对恶意重写的签名证明，Git/外部保存的链头仍是重要完整性依据。

## 准入及状态机

实现`code/scripts/stage_0_5_research_ledger.py::ResearchLedger`，只做预算/准入记录，**没有进程启动API**。旧确认入口→旧监督器仍只属于旧任务；不把新schema塞进旧runner，不通过将failed改verified绕过停止。

`initialize`只登记工程任务；`reserve`要求当前task、精确proposal SHA的研究者确认、proposal execution_allowed/researcher_confirmed=true、计划/源码/输入绑定、初始化/测量/输入契约批准、新任务隔离证据、资源快照、研究问题/对照/seed/环境/commit及dirty-worktree哈希、全新产物路径。当前候选这些均未通过，不能预约真实尝试。未来原生工具/执行器还须在实际执行适配器中完整绑定；账本通过不能替代原生隔离或实时资源监督。

`reserved → running → completed → measurement_accepted/rejected`；reserved/running可进入failed/interrupted。completed只表示运行结束，不能自动接受测量。测量接受要求输入、初始化、身份时钟、D1、18单元、上下文事件、资源、隔离检查全部true，并校验产物SHA与单次资源记录。Unknown资源不得冒充0或已通过。

每个reserved都计入一次尝试，后续失败、中断、启动失败仍在。失败/rejected不能重开原ID或改成功；`review_failure`追加研究者明确继续裁决后，下一项才可预约。同配置/seed重复须新ID、replicate_of和repeat_reason，重试也单独计数；不会自动调度或重试。精确提案可含后续新版本、同任务追加运行，累计计数不设上限；仍一次一项、前次需测量接受或明确复核。

每次记录唯一ID、task/plan版本及SHA、proposal SHA、源码/输入哈希、seed、环境、Git/dirty状态、预约/启动/结束UTC、状态、失败原因、资源快照与消耗、产物位置及测量接受状态。原始逐车数据和日志只放独立本机输出根`code/outputs/formal/calibration/stage_0_5_interaction_research_v2/`；便携仅聚合和哈希。

## 单次安全与使用边界

保持wall600s、RSS3GiB、task outputs2GiB、C5GiB/D14GiB、启动内存4GiB、0.5s轮询、workers1。`resource_reason`提供同限额检查；本模块不会监视进程，未来执行器必须定时调用并只终止自有进程树。无累计次数上限不意味着无单次限制、可自动多进程或历史失败已被接受。

当前可用命令（只读）为`python code/scripts/stage_0_5_research_ledger.py --repo-root .`。新科学矩阵仍Proposed，三个执行标志false，无SUMO尝试；实际执行适配器与身份采集、原生输入隔离证明尚未交付，完整批次保持阻断。未来不能将此软件账本测试通过当作仿真实验准入已成立。
