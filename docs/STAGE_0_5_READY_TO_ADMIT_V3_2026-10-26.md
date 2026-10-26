# Stage 0.5 V3 准入工程与真实阻断

Task `AAD-0.5-READY-TO-ADMIT-V3`。基准本地HEAD、origin/main、GitHub main均为8327068，开始时工作区干净。本轮0 SUMO启动、0真实TraCI连接、0新轨迹；没有查询SUMO可执行文件版本。当前结论为 **BLOCKED_ENGINEERING / OS native isolation unproved**，不能报告READY_FOR_RESEARCHER_APPROVAL。

## A：事实、变化和绑定

初始机器矩阵：`docs/audits/stage_0_5_ready_to_admit_v3/blockers_initial.json`。旧V2提案确有空input_sha256、null worktree_sha256和占位环境；没有绑定当前execution/identity实现。旧measure_completed_capsule把input_fidelity/task_isolation写死false、full_context_events/resource_limits写死true，18单元只看数量/总状态/E/最晚时间。这些是工程缺口，不能用授权false来掩盖。

当前`stage_0_5_execution_v2.py::measure_completed_capsule`调用新增`stage_0_5_acceptance_v3.py::assess_capsule`，八项字段均由具体证据判定。Unknown与Reject分别保存，二者在追加账本中均为false；原生科学等价不由软件检查授予。`stage_0_5_admission_v3.py::technical_preflight`分别报告technical_errors与authorization_pending，真实输入/工具/环境问题与预期的研究者未确认分开。原生构建硬锁仍为True，没有CLI/环境变量解锁入口。

显式入口`run_stage_0_5_admission_v3.py preflight --proposal <精确包路径> --run-id V3_0750_B00_DS38_s20261201`仅做技术检查。execute分支还需精确授权文件，当前构建在读取授权前就拒绝原生执行；原生路径禁止替换measurement/resource callback。没有“把验收换成全真回调”的正式入口。

新包位于`evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/`，有独立版本manifest；**既有evidence/EVIDENCE_MANIFEST.json未修改**。candidate-v1为中间绑定快照，后续源码/验证绑定完善后自动失效，不能批准沿用。最终版本、proposal SHA和验证状态以本任务最终validation_record及final_blockers为准；旧提案、旧候选、旧manifest均保留。新包不登记为新科学轨迹结果。

源码绑定覆盖执行、身份、保真、隔离策略、账本、验收、预检、准备与验证入口，以及实际C6/D1导入闭包（包括riskprop初始化导入的legacy辅助与正式风险配置依赖）。Git基准加实际源码集合SHA表示确切工作树版本，不把8327068描述为未改动的新实现；提交后另保存实际commit与纯Git复核。SUMO/TraCI及schema只做文件哈希与静态版本核对，Python解释器/stdlib/数值包/native库有独立依赖清单，未声称动态运行握手通过。

## B：八项验收如何推导

| 字段 | 实际证据 | 拒绝/Unknown示例 |
|---|---|---|
| input_fidelity | capsule输入字节、精确身份、TripInfo插入几何/速度、逐步五车道回读、匝道完整计划清单 | 输入漂移、错误读回、无插入几何、R判据未确认 |
| initialization_accounting | 从hash链身份日志重新运行IdentityObserver，与封存摘要语义一致，TripInfo身份对照 | API缺失、未核算去向、未知/重复ID、未允许的discard |
| identity_clock | 原生事件/实际出发/延迟、完整0.05s步序列、日志事件数及末时刻 | 摘要篡改、时钟缺口、TripInfo冲突 |
| D1_contract | 当前原生物理C6→measure_state_frame→local_d1_measurement，正合格暴露 | 无可靠前车、零暴露、字段/时钟不合法 |
| all18_common_cells | 逐格时间帧与右端点、≥10状态、正D1；每份绑定参考的18键/elapsed/空间/状态/E | 缺390帧、缺内部帧、缺参考单元、跨块/身份连续性失格 |
| full_context_events | 完整XML、0..419.9全0.1s帧序列；完整上下文事件成员及onset归属 | 不完整XML、封存哈希漂移、缺帧或未知FCD身份 |
| resource_limits | 启动/运行/测量末资源序列、监督覆盖、实际exit code、最后产物字节 | 采样缺失/超间隔、wall/RSS/磁盘/输出超限、进程异常 |
| task_isolation | 绑定的OS运行证据、独立执行器确认、文件/子进程/网络/资源约束证明 | 没有OS证据为Unknown；合成kernel transcript不能冒充原生证书 |

测量复用`stage_0_5_scene_reconstruction.parse_fcd`、`stage_0_5_state_support.fcd_to_state_frame/measure_state_frame`与当前D1；这些核心科学源码未改。映射坐标仅作区域归属，原生位置用于物理gap；连接段/边界不可观测仍missing。完整上下文提取事件后按onset归属，TTC<2、跨度≥0.2s、100ms相邻边/身份资格不变。逐格[low,high]右端点在XML中可观测并由原D1相邻边契约计算E；空格/空帧不强行补车。状态支持不是分布匹配或科学通过。

`verdicts`保存具体条件、原因和证据；不是仅返回八个布尔值。通过场景使用明确的synthetic replay且调用真实验收与C6/D1，未传all-true measurement callback。原有回调式小型账本单测保留其局部用途，不能替代新端到端验收证据。

## C：身份、插入与干预

新配置明确TripInfo输出与write-unfinished/write-undeparted；`IdentityObserver.observe_tripinfo`交叉核对出发时间/延迟、插入速度/车道/位置、到达与未完成。getSpeed/getLanePosition为完成步后的单独观测，不能代替精确插入值；FCD首末仍100ms代理。无TripInfo不推出丢弃，负depart保留未出发语义，pending必须来自身份快照。遥移API非初始缺失仍使完整性false。

语义依据：[SUMO TripInfo](https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html)、[输出选项](https://sumo.dlr.de/docs/sumo.html)、[车辆值接口](https://sumo.dlr.de/docs/TraCI/Vehicle_Value_Retrieval.html)；安装的1.26.0相关TraCI与TripInfo schema另按文件SHA绑定，未调用SUMO查询版本。

NativeBackend每内部步先核对原生时钟，记录目标与五车道逐条set/get及失败；180和240边界采用[180,240)。失败/最后控制记录单独封存。原生Error日志早停，只当错误证据，不据此制造discard身份。资源PID出生时间与启动元数据用锁同步；只停止自身进程，进程树OS硬约束仍待隔离环境证明。

四个0750候选均有具体network/routes/sumocfg及SHA。B00/S10共用相同声明初态与原匝道时序；R01/SR11按既有每60s块20–25s、0.05s取整规则，除非初态entering的depart与必要排序外不改属性。配对校验逐身份/车型/route/块归属/数量，不用文件存在代替保真。90%仍为候选诊断；R臂不因“已进入者100%命中”而获资格，完整计划数、进入数、未进入ID、实际时间、延迟和删失都保留。

只读复核既有DS38基线及原ID1 routes：117初态恰38个数值10→max，79辆及1033非初态原样。已命名的worker_console.log SHA `2eaf711e946b275deb93cfba10660475ada7223f936ba2596f562b9b5ad4d258`明确写i0007在0s不能按给定速度出发，但没有身份级discard记录。汇总discarded=1不能补成i0007已丢弃。本轮不读历史FCD、不重测C6。i0007仍15.23，本候选若再报错会早停，且不能复用为合格B00。0805暂停，未生成其新输入。

## D：原生隔离的真实阻断

证据为`environment_probe.json`：Windows命令入口未发现WindowsSandbox/docker/podman/bwrap；WSL已安装Ubuntu但Stopped。尝试只做工具定位/用户命名空间能力探针的请求，在创建进程前被自动审批拒绝，理由为AGENTS.md WSL启停限制。没有WSL启动，没有绕道访问WSL共享目录，没有安装组件、修改ACL或系统策略。

这些事实只证明当前任务**没有可验收的OS执行隔离证据**，不证明Windows/WSL理论上不支持隔离。Python路径守卫、无数据Git克隆、假内核transcript都不替代OS证书。没有获准的运行环境/独立原生约束探针，不能接受新任务隔离，也不能生成解锁构建。历史POLICY-A-VALIDATION-SCOPE-01仍Not Accepted，无需也不能追认。

独立V3预算/账本只创建task_created，真实attempts0，无累计cap；旧V2/三次账本未动。每次预约必须有精确提案SHA与运行ID的人工授权、输入/源码/环境/资源/隔离校验；失败保留并需显式继续裁决，不自动重试。

## E：验证和交付边界

最终源码定向：163 passed、1 skipped，180.90s，exit0；全量软件：1130 passed、15 skipped、7项原生测试排除、2个既有pandas FutureWarning，320.00s，exit0。25项源码与独立无数据克隆逐字节相同；两轮父进程审计均0拒绝、0 SUMO。编译、strict-git文档、既有便携证据校验exit0。15个skip为13项缺少本地密封/原始资源、1项专用-S引导验证、1项Windows symlink权限不足；不计为通过。两次会话丢失而无完成审计的运行目录保留，未计作通过。精确命令、退出码、审计SHA、源码新旧SHA、跳过身份与原因见`docs/audits/stage_0_5_ready_to_admit_v3/validation_record.json`。

最终候选为`evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v2/`，proposal SHA256 `978fe0222a3fc00bb7a92b8c9065a204df0233449c6f778070628876864f6edc`，首个Proposed ID `V3_0750_B00_DS38_s20261201`。生成时完整技术预检只剩`OS_native_isolation_not_accepted`与`native_build_remains_locked_pending_OS_acceptance_and_review`；授权待定项另列。当前SHA可用于审阅内容，不能用于直接执行。candidate-v1仍保留且已因源码漂移失效，不可迁移批准。最终阻断矩阵见`docs/audits/stage_0_5_ready_to_admit_v3/final_blockers.json`；提交后实际commit、纯Git复核及push另记录于本机忽略目录，避免修改已绑定证据形成自引用。

软件验证只在独立无数据克隆执行，真实SUMO七项固定排除，禁用自动插件并审计Python父进程；原生访问隔离仍Unknown。首轮149通过/4失败/1跳过保留：摘要比较把JSON数值0/0.0误当不同，以及三个测试误限定了已正确拒绝漂移的异常类型。修正后真实验收定向157通过/1跳过；最后的额外哈希/完整上下文回归与最终全量/编译/strict docs/包校验数字见本任务validation_record。

最终包完整校验在已绑定的Python环境通过，portable-only校验也通过。一次受限工具会话完整校验因用户级pyarrow不可见而exit1；同一解释器在已批准主机环境的sys.path包含该用户site，模块位置与提案一致，完整哈希复核exit0。失败未计为通过，没有安装依赖或改变封存包；环境差异记录为`docs/audits/stage_0_5_ready_to_admit_v3/package_verification_environment.json`。受限会话不能被当作相同运行环境。

原生隔离验证：未完成，blocked。真实科学实验：未执行。软件验收通过不能写成Stage0.5通过、真实覆盖接受、WP2–WP5整体完成或Stage1.1准入；δ/h/B不变。旧manifest保持原字节，新证据使用独立manifest并单独验证。

## F：最小决策包

1. **环境授权**：推荐仅授权启动已安装Ubuntu做非SUMO隔离能力核验；备选保持当前环境并由研究者提供已经配置的Windows隔离执行器。后果：当前仍是硬工程阻断；无论选择哪种，都必须取得实际证据并重绑后续精确提案，不能批准当前包后直接运行。
2. **首个初始化候选**：推荐0750 DS38 B00先作初始化/支持诊断，严格早停；备选先另版处理i0007/更广初始化。后果：前者可能因已知错误早停且不具备矩阵基线资格；后者会改变初始化，必须四臂一致重绑，不自动扩到117辆。
3. **首批范围**：推荐只确认B00具体运行ID，全部八项验收满足才复用；备选先确认同seed四臂设计但逐次单独授权。后续R臂完整脉冲判据另待确认，首个B00不需要冻结它；不把seed队列或δ/h/B塞进本次必要决定。

精确首个计划见`docs/plans/2026-10-26-stage-0-5-ready-to-admit-v3.md`，最新候选提案SHA/实际首个ID见独立包manifest。它是可审查的完整内容绑定候选，**当前不可执行、不可报告Ready**。最终授权入口仍在任何子进程创建前拒绝未确认/漂移/隔离不足/资源不足的运行。
