# Stage 0.5 V2 准入工程闭环（2026-10-25）

任务 `AAD-0.5-INTERACTION-RESEARCH-V2`；结果 `RES-STAGE-0.5-V2-ADMISSION-ENGINEERING-V1`。基准本地 HEAD、origin/main 与远端 main 均核对为 `5899465f7c934c7544f04ef2ba290147e4999deb`，开始时 main 干净。本轮新 SUMO 启动 **0**、新轨迹 **0**；没有调用版本命令、空网络探针或真实执行适配器。

## 当前结论及边界

**Verified 工程事实**：逐车身份契约/状态机、初始化静态保真检查器、精确历史允许清单、六份历史 C6 重测及独立复核、硬锁执行适配器、路径/进程策略及合成测试已实现。旧核心测量、旧执行链、既有精确提案、旧账本和失败产物未修改。证据入口为 `evidence/results/RES-STAGE-0.5-V2-ADMISSION-ENGINEERING-V1/`；完整离线表只保存在 `code/outputs/formal/calibration/stage_0_5_v2_admission_engineering_v1/`。

**Unknown / Not Accepted**：真实原生进程的文件访问隔离、实际插入速度/时间、全部车辆生命周期核算、干预实际施加、18 个共同单元和新批次测量验收。软件守卫与合成测试不能证明这些性质。`POLICY-A-VALIDATION-SCOPE-01` 仍 Not Accepted，`accepted_for_new_task=false`。

**Proposed**：四条件矩阵、初始化范围、seed 队列、重复策略和科学判读约定仍待研究者决定。`execution_allowed/researcher_confirmed/protocol_frozen=false`；δ/h/B 未填值，Gate、pending_simulation_sample、科学结论资格、真实覆盖接受状态、Stage 1.1 不变，WP2–WP5 未整体完成。无限累计预算已 Agreed；V2 真实账本仍 0 次，旧 1/3 失败历史保留。合成账本的通过状态仅存在无数据测试临时目录。

## A：真实身份数据流及新契约

旧调用链为 `run_stage_0_5_policy_a_confirmed.py` → `supervise_stage_0_5_diagnostic.py` → `interaction_diagnostic_worker.py::execute`。worker 使用已连接 TraCI，每步 0.05 s，FCD 0.1 s；读 `getDepartedIDList/getArrivedIDList/getPendingVehicles/vehicle.getIDList` 后主要保留长度及累计计数、时钟和 main_2 限速，未保留逐车事件集合。数量守恒不能证明身份守恒，旧历史不能据此补建逐车插入/丢弃记录。

`stage_0_5_scene_reconstruction.py::parse_fcd` 读取已写出的 FCD 时间/ID/车道/原生位置；`prepare_stage_0_5_depart_speed_candidate.py::observe_initial` 流式计算首末 FCD 观测。两者均没有原生插入事件。首次 FCD 是 100 ms 采样代理；不存在 FCD 记录不能推出 pending、discard、零速或仍在网。旧日志只有 1 辆 discarded 的总数，身份仍 Unknown。i0007 的警告不能自动等同于该丢弃身份。

`stage_0_5_state_support.py::fcd_to_state_frame` 在同一原生 lane/edge 内按原生位置寻找可观测前车，物理净间距不用映射 y；连接段与车道边界不可观测关系标 missing。`measure_state_frame` 调用当前物理测量；`stage_0_5_d1_measurement.py::local_d1_measurement` 要求同 follower/leader incarnation、可靠关系、两端质量、原生 lane 连续、相邻 0.1 s 及区域/窗口资格；完整上下文 P2 按 onset 归属，保留未确认右删失。缺身份、缺可靠前车、缺连续边会减少有效 D1，不能补零风险。上述源码均未修改。

新 `stage_0_5_identity_observation.py::IdentityObserver/collect_snapshot` 独立于科学算法；契约、API 来源、状态转换及限制见 `docs/STAGE_0_5_V2_IDENTITY_CONTRACT.md` 与便携 `identity_contract.json`。安装 API 文件以 AST 与 SHA 核对，二进制仅哈希读取；与旧绑定一致。1.26.0 来自旧失败 FCD 头，当前运行握手 Unknown，不伪称本轮原生验证。

## B：静态初始化复核

`stage_0_5_input_fidelity.py::inventory/config_references/audit_bundle/compare_initial_policy` 针对实际 vType/route/vehicle 结构检查身份唯一、顺序、所有属性及子元素、初态/非初态、route/type/depart/lane/position/speed、网络连接与权限、配置相对引用和 exact hash。XML DTD/entity、额外文件引用及越界路径拒绝；候选的允许变化必须与原始数值 10→max 的精确目标集合一致，且核对除允许字节替换外完全一致。不会写输入 XML。

| 输入 | 总车辆 | 初态 | 初态 main_2 | 数值10 | main_2 数值速度>5的潜在冲突 |
|---|---:|---:|---:|---:|---:|
| ID1 0750 原输入 |1150|117|38|38|38|
| ID2 0805 原输入 |1031|131|52|44|52|
| ID3 0750 原输入 |1150|117|38|38|38（假设施加该脉冲；ID3实际无此脉冲）|

两份 DS10MAX-V1 候选均只改 38 辆初态；其余 79 辆、1033 辆非初态及网络/config 原字节不变。候选将可静态识别的 main_2 数值>5字段冲突降为 0，**不等于安全插入验证通过**。0805 main_2 的另外 8 辆为 7.71–9.92 m/s；44 辆方案不能覆盖全部潜在冲突。

i0007_i0007 原速度15.23，起始 main_1_5 静态限速27.78，距边终点约0.13 m，下游 main_2 为10；静态起始限速检查通过与前方慢车警告可以同时成立。警告沿用旧原生日志事实，本轮无新动态解决证据。所有输入 SHA 见 `provenance.json/static_input_sha256`，候选差异见 `initialization_audit.json`；逐车明细仅本地。

| 待决选项 | 范围/预期作用 | 混杂及剩余问题 | 所需证据/执行资格 |
|---|---|---|---|
| 0750 DS38，0805暂停 |只处理明确数值10群；与现候选一致 |max可能改变38辆插入速度、时序、在场与排队；i0007保留 |同政策无干预配对基线、逐车原生记录；目前无执行资格 |
| 按受扰动起始edge，各窗口独立 |0750为38，0805为52；覆盖该edge现有数值>5冲突 |0805需独立新政策/输入，仍不处理上游速度/前车安全 |研究者定义允许字段及范围、静态重审、新精确绑定；未准备/无资格 |
| 更广初始化重建 |范围由研究者定义，可能涉及全部初态 |改变更多相对位置/速度/插入队列，因果归因更难；无证据支持直接117全max |先明确研究问题与重建约束，再独立对照；未准备/无资格 |

静态“潜在冲突”只说明若这些车辆仍未插入且限速变5则存在数值不相容，不声称它们到180 s均pending。三种范围均不由本轮工程工作批准。

## C：最小历史允许清单与离线重测

没有扫描轨迹库。`review_stage_0_5_c6_admission_v1.py::prepare/validate_allowlist/measure` 从既有正式摘要追踪两窗口、seed20261201：B_het 四车道结构实验各一份，边界时序 U/E 各两窗口，共 **6** 份需重测 FCD。每份只允许 fcd/routes/network/config/旧 measured_state 五种角色，路径、字节、SHA、原结果ID、研究问题、两个评价窗口均在 `history_allowlist.json`。仅接受前两个校准窗口和固定目录模板；第三窗口/其他路径拒绝。既有两份 B_het/vlim10 当前 C6 基线经派生文件哈希核对直接复用，未重开 FCD。历史文件在本轮首次捕获之前的完整性仍 Unknown，不能倒推“从未变过”。

使用原有 `parse_fcd → fcd_to_state_frame → measure_state_frame → local_d1_measurement`，未写近似替代。主对照保留各历史预设 `[300,420)`；同时独立列出已提出的 `[120,390)`，不是事后选优，二者不可混读。下表 E 为有效D1 veh·s，率为事件/有效车辆小时；“旧表D1”是给旧测量表套当前D1，不代表旧物理值已修复。

| 原条件（seed均20261201） | 已发布旧N | 旧表D1 N/E | 当前C6 N/E | 当前率 |
|---|---:|---:|---:|---:|
| 0750 四车道 |33|33 / 6401.5|14 / 5882.8|8.56735|
| 0805 四车道 |32|32 / 5969.5|10 / 5433.6|6.62544|
| 0750 U |1|1 / 5618.1|0 / 5071.2|0（有效暴露内）|
| 0750 E |2|2 / 5446.4|0 / 4903.0|0（有效暴露内）|
| 0805 U |1|1 / 5649.7|0 / 5109.4|0（有效暴露内）|
| 0805 E |2|2 / 4859.9|0 / 4353.7|0（有效暴露内）|

复用基线在 `[120,390)` 分别 N/E=0/9754.8、0/10456.7。不得将不同窗口数值当seed重复。六份当前结果均标 `rechecked_current_interface_changed`；旧发布率的点暴露分母也与D1不同，两种变化分开记录。缺失/不可观测计数、删失、事件成员与边界变化在 `C6_comparison.json`；完整上下文事件成员集合与窗口onset N不同，不能把集合大小当局部事件数。

`verify_stage_0_5_c6_admission_v1.py` 对新保存表做独立原生前车几何、标量事件成员及相邻D1边核对，六份均通过，没有再次解析FCD。完整新表与新事件JSON独立版本保存，旧表/旧manifest不改。完整独立报告哈希及实际执行wrapper快照在本地，便携摘要绑定核心及最终工程源。

**Observation**：当前支持下结构实验仍有14/10事件，四个时序样本有效暴露内0；缺失支持同时存在。**Interpretation的限度**：C6同时改变前车几何及可评价支持，无法单靠N下降区分数值纠错与失去可观测性，更不能宣称风险消失、旧实验整体无效或某机制不存在。**待验证假设**：恢复真实到达是否在实际入口被排队抹平、同初始化四臂是否出现额外交互，历史单seed不足以识别。402次旧运行没有重跑，其全部P2未获追认。

离线失败也保留：首次prepare误把XML output分组当文件引用，拒绝后修正校验器；`inputs/history_allowlist.json` 保留，成功版本为 `_v2`。`measurements_v1` 六项因受限环境不可导入既有pyarrow失败，未产生有效测量；获准使用既有依赖后成功结果另存 `measurements_v2`。没有安装依赖、自动覆盖重试或新轨迹；这些离线尝试不写入仿真账本。

## D：锁定的执行与监督接口

新增 `stage_0_5_execution_v2.py`，不改既有账本模块：

1. `ExecutionAdapter.preflight` 对精确提案、单次授权、三布尔标志、初始化/测量/保真确认、隔离接受、预算、源码/计划/输入/工具/环境哈希、config seed/时长及输出作用域检查。缺失/Unknown/错误类型拒绝，写独立拒绝报告；拒绝不预约attempt。
2. `NATIVE_LAUNCH_LOCKED=True` 是代码构建锁，无CLI/环境覆盖；adapter与`NativeBackend.start`双重拒绝。当前完整候选也不能到子进程创建。
3. `ReplayBackend` 仅合成数据、无process factory；必须明确synthetic fixture，才能测试预约→运行→完成→测量验收或失败/中断。真实V2配置仍false。
4. 已验证输入字节快照复制到独占新capsule，避免校验后再读取不同版本。单worker、唯一ID、hash链/fsync账本、失败复核、禁止自动重试沿用 `ResearchLedger`。每次输出限额为该capsule，非无限研究任务历史总和。
5. `ResourceSupervisor/ResourceWatchdog/native_resource_probe` 接口覆盖wall/RSS/磁盘/可用内存/单次输出字节和本任务持有的进程树；PID出生时间核对，停止不杀其他任务。合成异常和watchdog已测；原生监控完整性仍Unknown。
6. 未来NativeBackend含精确命令、显式环境、连接版本握手、每步身份采集、每步限速施加和getter回读、日志/FCD及核心测量调用。**此分支未启动、未原生验证，不能只改标志就使用**。`measure_completed_capsule` 对未证明input_fidelity/task_isolation保守返回false，需要未来独立准入合同。实际插入速度没有原生输出时仍Unknown；匝道到达必须用逐车实际时序另外验收。

本轮接口建设不修改供给/匝道幅度、评价窗口或矩阵。未来精确提案还须绑定这些新增源及全部动态参数；旧批准不能迁移。新adapter的原生路径仍须单独工程审查、独立隔离证据与研究者授权，不能绕过构建锁。

## E：隔离守卫与未证明事项

`stage_0_5_isolation_v2.py::Scope` 将read bindings、独占输出和进程命令分离：拒绝非允许读写、`..`、symlink/junction逃逸、密封目录、输入漂移、既有输出覆盖、shell与未列命令；所有新输出用exclusive create。`offline_audit` 限定六文件组/新输出及明确Python运行时，拒绝任何子进程，记录Python打开路径和拒绝。

定向合成测试包含身份/时钟异常、FCD缺失、重复/未知ID、右删失、XML修改越界、引用穿越、hash/env/source漂移、journal损坏、资源失败、输出过量、白名单与不重复账本、失败后需复核、旧manifest保留。真实symlink需要OS权限；不可创建时明确skip，另有可重复的flag模拟越界测试，不伪称真实symlink已验证。

局限：Python audit不能覆盖所有native/pyarrow内部文件访问，不是OS sandbox；路径check与open仍不能证明对恶意并发替换的原子防御；本轮未观测原生进程/插件/驱动/工具所有访问，不能认证零验证资源访问。离线读取旧audit的`reads=[]`指未使用read_bound快照接口，不是零实际读取；新记录区分Python opened paths与bound snapshots。禁止以软件测试零拒绝替代原生准入证据。历史隔离事件不被“修复通过”覆盖。

## F：验证与证据

完整命令、测试数、退出码、实际环境、跳过/排除及hash见 `docs/STAGE_0_5_V2_ADMISSION_VALIDATION.md` 与 `validation_record.json`。测试仅在独立无真实数据Git克隆进行；不是主工作区全量测试。现有验证器源码先审查：明确排除7个原生SUMO集成测试，禁用自动插件、过滤ambient路径、临时目录重定向，Python审计拒绝源工作区数据和仿真进程；其native不继承性质仍不作证明。

本轮使用追加导出器 `export_stage_0_5_v2_admission_evidence.py`，只添加本结果，最终核对全部旧manifest结果对象及旧绑定源码/输入/账本未变。旧exporter保持原字节。portable不复制原始FCD、逐车大表、密封键、HTML或日志。

## 后续研究者决策与新的判别信息

需要确认：初始化三选项及窗口适用范围；同政策无干预/仅供给/仅匝道/联合矩阵及精确脉冲；seed/重复规则、科学判读阈值；独立原生隔离准入及可接受证据。δ/h/B与Gate不在本轮授权内。

在这些决定前可继续静态/合成修复，但不能启动。经将来单独授权后，首先要获得同政策基线与逐车原生生命周期/实际施加证据，才能区分初始化变化和供给/匝道因素；四臂因子差异才可能识别额外交互。当前六份重测只解决历史数值测量可复用性，既没有新同政策基线，也没有回答实际插入冲突。下一项有效实验须填这些缺口，而非重新把跟驰/限速/缩道/时序当作从未测试过的发现。
