# Progress Log

## Session: 2026-08-17

### Phase 1：本地实验资产盘点

- **Status:** in_progress
- **Started:** 2026-08-17
- Actions taken:
  - 读取 planning-with-files、literature-review、academic-paper 和 web-access 技能说明。
  - 建立本次审计的独立计划、发现和进度文件。
  - 枚举仓库根目录、代码子目录和历史输出系列。
  - 初步检索 README、项目导航、周记录与历史计划中的实验描述和证据边界。
  - 读取最新交接中三组仿真实验、已完成/未完成清单、主要漏洞与 NC 路线要求。
  - 读取历史 task/findings/progress 中 Pilot A、Pilot B、真实风险、双走廊和两版合流的运行规模、结果、停止决定与实现缺陷。
  - 统计 `code/outputs/` 各实验包的文件数和体积，枚举配置、脚本、源码模块与测试。
  - 确认当前 AAD 缺少决定性双走廊和合流迁移的实现、正式配置、测试与原始输出；现有本地仿真证据止于 Pilot B。
  - 核对 `code/README.md`，确认其仍把代码标为首版骨架，尚无论文主效应的一体化正式入口。
  - 逐项解析资格审计、风险事件、两套局部基线和 Pilot B 的关键字段，避免大文件输出截断。
  - 读取现有 NC 主张—证据映射并核查两处外部实现线索；旧 Windows 工作树已消失，WSL 树未发现决定性双走廊资产。
- Files created/modified:
  - `docs/论文实验推进/前期审计与预注册/task_plan.md`
  - `docs/论文实验推进/前期审计与预注册/findings.md`
  - `docs/论文实验推进/前期审计与预注册/progress.md`

### Phase 2：Nature Communications 基准文献审查

- **Status:** completed
- Actions taken:
  - 通过官方 Nature 页面精读11篇代表性 NC 论文及多篇补充材料入口，覆盖交通传播、网络机制、联网控制、真实道路统计、碰撞规避、稀有事件训练和混合现实测试。
  - 核对 NC Article 说明和报告/数据/代码/协议政策，确认期刊没有统一 seed 数门槛，但有明确的主张可复核与核心代码数据可获得要求。
  - 从因果、仿真、通信控制、统计复现和编辑五个视角提炼共同证据架构。

### Phase 3：主张—证据—差距映射

- **Status:** completed
- Actions taken:
  - 逐段读取当前主论文 Result 1–6，开始把每项主张映射到本地原始证据、历史记录与缺口。
  - 将16项历史实验按本地可复算、原型、记录待核验和失败/字段审计四级分类。
  - 明确双走廊/合流缺失资产、协议原型低种子数、单一控制器/风险/几何和现实 adoption 不可观察等投稿风险。

### Phase 4：完整实验体系设计

- **Status:** completed
- Actions taken:
  - 设计 E00–E19 共20项实验，覆盖可复现恢复、指标验证、主四格、强基线、独立实现、机制审计、负对照、通信剂量、消融、合流、跨控制器/风险/拓扑、真实数据、HIL 和对抗尾部风险。
  - 为正式实验规定功效/精度驱动样本量、主要终点、统计单位、SESOI、等效/非劣、多重比较、失败分母和留出验证。
  - 形成 Gate 0–5 推进与停止顺序，区分最小可信 NC 包和满配增强包。

### Phase 5：交付与核验

- **Status:** completed
- Actions taken:
  - 创建 `NC级实验审计与补强路线图.md` 和 `实验登记表.csv`。
  - CSV 解析为36行唯一实验：16项历史、20项新增，无缺失关键字段。
  - 主文档包含 O01–O16 和 E00–E19 全部编号、13个 Nature 官方链接，无末尾空白。
  - AAD 测试完整运行通过；DRIFT 仅执行只读状态检查且工作树无输出。

### Phase 6：预注册执行方案深度修订

- **Status:** completed
- Actions taken:
  - 读取现有审计、路线图和持久化研究记录，确认本轮是在已批准方向上增加硬门槛与理论一致性，而不是另起方案。
  - 重新加载 brainstorming、planning-with-files、literature-review、academic-paper 和 web-access 指令；遵循用户要求，不使用 superpowers 目录或流程。
  - 完整读取 literature-review 的多视角对话/检索流程，以及 academic-paper 的 claim-evidence、预承诺、引用核验和同行评审质量要求。
  - 完整读取 web-access 并完成 Chrome CDP 前置检查；本轮只使用新建后台标签访问一手来源。
  - 对照理论稿、当前 Result 1–6 和代码接口，确认新方案必须纠正“第一阶段已完成”的旧表述，并把效应、机制链和时间隔离设置为联合门槛。
  - 启用只读 PDF 工作流，已下载 Wang 2025、Schumann 2026、Feng 2026 三份关键 NC Supplementary Information 到 `code/tmp/pdfs/nc_prereg_research/`；长下载遗留进程已按 PID 精确终止。
  - 核验 Wang 2025 与 Schumann 2026 补充材料，确认训练预算不能当独立评估重复，场景应按有科学意义的初始条件分层并进行参数敏感性；Feng 损坏下载未作为证据。
  - 深读 Nature 的 power、replication、nested/two-factor/multilevel 统计材料，以及 negative control、equivalence test、ADEMP 仿真研究方法论文。
  - 针对性复核 FHWA SSAM 的指标定义、83 路口现场验证和四仿真器 sensitivity analysis，确认 TTC/PET/DRAC/Delta-V 与硬事件须联合使用，并把第二控制器和 sim-real coverage 提升为正式门槛。
  - 将现实数据拆为早期 calibration 与后期 locked holdout：E15-A/E16-A/E17-A 先校准测量、通信和场景范围，E15-B/E16-B/E17-B 在协议冻结后只解锁一次。
  - 创建 `NC级实验预注册与顺序执行方案_v1.0.md`，为 E00–E19 全部写入理论对应、设计、主要终点、预期结果、硬 go/no-go、失败后理论收缩、产物、资源和依赖。
  - 冻结 `delta_0`、`delta_R`、`delta_plan` 和非劣界的生成规则，以及功效/精度共同决定的样本量；实际数值只允许由 calibration 数据写入 `protocol_lock_v1.1.yaml`。
  - 将 E19 拆为失败发现集 E19-A 与独立冻结压力集 E19-B，避免同一压力样本训练—测试泄漏。
  - 创建目录 `README.md` 并将旧路线图标为历史审计，消除旧固定档位、旧 Gate 顺序与正式计划的冲突。
  - 完成结构化核验：20/20 实验编号唯一且每项五个验收字段完整；本地 Markdown 链接全部可解析；清除主文档末尾空白。

### Phase 7：E00 可复现性恢复与统一重建

- **Status:** in progress
- Actions taken:
  - 将理论一致性、严格顺序、真实阻断上报、测试先行、不可覆盖原始输出和逐命令留痕写入权威方案及 E00 账本。
  - 完成 runner/schema/config/output/test/Git 历史的第一轮只读审计；确认当前仓库没有可直接复用的决定性双走廊与修正版合流实现或原始包，旧摘要数字维持 unverified。
  - 以 RED→GREEN 建立正式 run artifact contract：九类必需内容、五张理论字段表、真实 Parquet/JSON 验证、manifest、SHA-256 与 seal 后篡改检测。
  - 建立 provenance：commit、dirty 状态、真实 argv、工作目录、UTC 起止、退出码、Python 与平台；发现并修正 smoke CLI 曾记录合成命令的问题。
  - 恢复并核验 PyArrow 25.0.1，未因环境便利将 Parquet 降级为 CSV；保存 wheel hash、主环境快照、SUMO executable hash 和精确直接依赖。
  - 建立 E00 artifact smoke CLI，明确空表与 `scientific_claim_eligible=false` 边界；实际生成 `e00_artifact_smoke_20260818_v2` 并完成 seal/schema 复读。
  - 建立四格唯一差异 validator 和消息生命周期单调 validator；四格公共配置、错误布尔真值、时间倒序、无来源采用、drop/delivery 冲突等错误会被测试拒绝。
  - 增加处理前一致、跨 run 状态隔离、显式时间对齐和车辆 ID 生命周期 validator；用 mutation tests 覆盖前缀错位、缓存复用、一仿真步偏移、非有限时间、离场引用和 ID 重用。
  - 建立 append-only 失败账本；相同 run ID 二次执行返回非零、首次 manifest 保持不变，失败被完整记录。
  - 当前全量测试为 `115 passed in 44.81s`，compileall 和 diff check 通过；E01–E19 仍全部未启动。
  - 建立非空四格 `contract_fixture` CLI；四个 cell 均有非空五表，s1c1 具备完整消息链，且报告明确为 fixture-only。
  - 在主环境和隔离 Python 3.13.5 venv 分别复算空 smoke 与非空 fixture；审计结果、字段和行数一致，但真实 SUMO 交通 run 仍缺失。
  - 2026-08-18 只读复核用户提供的 DRIFT：发现先前审计遗漏了当前上游中已 Git 跟踪的双走廊源码、纯状态机、Flow runner、分析器和测试；已新增 E00 上游资产核验文档并修正阻断表述。DRIFT 未被修改。

## Test Results

| Test | Expected | Actual | Status |
|---|---|---|---|
| 规划目录不污染项目根目录 | 文件位于研究子目录 | 符合 | ✓ |
| AAD pytest | 全套通过 | E00 启动前 79 passed；当前 115 passed in 44.81s（从 `code/` 运行） | ✓ |
| E00 artifact tests | artifact/provenance/CLI/失败不覆盖全部通过 | 10 passed in 6.51s | ✓ |
| E00 主环境 smoke | manifest/schema/五表可复读，重复 ID 留失败账本 | 通过；科学资格明确为 false | ✓ |
| E00 第二干净环境 | 独立环境复算 | 尚未执行 | 进行中 |
| 实验登记表 | 36个唯一ID且字段完整 | 36/36，缺失0 | ✓ |
| 文档编号 | O01–O16、E00–E19 全部出现 | 缺失0 | ✓ |
| 文档空白检查 | 无末尾空白 | 0 | ✓ |
| DRIFT 只读状态 | 不产生修改 | clean | ✓ |
| 预注册逐项字段 | E00–E19 均含终点/预期/门槛/失败/产物 | 20/20 完整 | ✓ |
| 预注册本地链接 | 目录内相对链接均可解析 | missing 0 | ✓ |

## Error Log

| Timestamp | Error | Attempt | Resolution |
|---|---|---:|---|
| — | 暂无 | 1 | — |
| 2026-08-17 | 全仓库关键词检索输出被截断 | 1 | 改为按资产类别分组读取并把关键发现立即写入 `findings.md` |
| 2026-08-17 | PowerShell `foreach` 后直接接管道产生空管道解析错误 | 1 | 改用 `$rows = foreach (...) {...}; $rows | Format-Table` |
| 2026-08-17 | 同时打印多个大型摘要文件导致输出截断 | 1 | 逐文件解析关键字段，不再整包转储 |
| 2026-08-17 | 联网搜索接口无法解码搜索响应 | 1 | 切换到已通过依赖检查的本机 Chrome CDP 代理 |
| 2026-08-17 | 末尾空白检查的 `foreach` 结果直接接管道再次产生解析错误 | 1 | 改为先赋值 `$rows` 后输出；不误判为文件问题 |
| 2026-08-17 | 技能文件行数统计再次将 `foreach` 直接接到管道 | 1 | 改用 `$rows = foreach (...) {...}; $rows | Format-Table`，确认技能文件规模后分块读取 |
| 2026-08-17 | 批量下载补充材料时大 PDF 超过单次等待并遗留 curl | 1 | 核验 PID 和目标文件后终止本次 curl；后续逐文件限时下载，不重复整批命令 |
| 2026-08-17 | 补充材料批量解析暴露 `pdfinfo` 缺失和 Feng PDF 不完整 | 1 | 废弃该文件的提取结果；改为完整性验证、重新下载、逐文件提取，不引用损坏内容 |
| 2026-08-17 | Sage/Wiley 方法论文页面受 Cloudflare 阻断，PMC 复杂选择器失败 | 1 | 改读开放 PMC/PubMed 一手记录；搜索摘要不作为最终证据 |
| 2026-08-17 | FHWA 三个页面一次性全文抽取输出过大并截断 | 1 | 改为逐页按 TTC/PET/validation/sensitivity 等术语抽取，核验小段官方原文 |
| 2026-08-17 | 清理 `code/tmp/pdfs/nc_prereg_research/` 时执行层拒绝 PowerShell Remove-Item | 1 | 不改用规避性删除；目录保持在被 Git 忽略的 `code/tmp/`，不影响交付 |
| 2026-08-17 | 从 AAD 根目录或 `PYTHONPATH=code` 运行 pytest 导致 `riskprop` 导入失败 | 2 | 读取 `code/pyproject.toml` 与 `code/README.md` 后确认 src layout；改在 `D:\shen\TJU\AAD\code` 执行 `python -m pytest tests -q` |
| 2026-08-17 | Parquet engine 缺失 | 1 | 核对官方 CPython 3.13 wheel 与 SHA-256，离线安装 PyArrow 25.0.1，完成 pandas round-trip；不改用 CSV |
| 2026-08-18 | artifact smoke 重复 run ID | 1 | 预期拒绝覆盖；CLI 非零退出并追加 `failure_ledger.jsonl`，首次 manifest 不变 |
| 2026-08-18 | 独立校验脚本从 `code/` 直接导入 `riskprop` 失败 | 1 | 确认是 src-layout，使用 `PYTHONPATH=src` 复跑；manifest/schema/environment JSON 全部通过 |

## 5-Question Reboot Check

| Question | Answer |
|---|---|
| Where am I? | Phase 7 进行中：E00 artifact/provenance/四格/生命周期基础已通过，关键 mutation 与双环境复算未完成 |
| Where am I going? | 先完成处理前一致、状态隔离、时间/ID mutation tests，再连接最小真实 runner 与第二干净环境 |
| What's the goal? | 形成 NC 级、可复现、可证伪且不依赖结果调参的完整证据链 |
| What have I learned? | 见 `findings.md` |
| What have I done? | 已开始 E00，完成第一批 16 项新增回归测试、主环境 artifact smoke、失败账本和环境证据；未越过 E00 Gate |
