# DRIFT 资格验证计划

## 决定性类超距风险实验重构（2026-08-07）

### 目标
在不依赖事后挑选指标的前提下，构造同时具备“目标区真实风险、信息先于物理作用、来源可追溯、反事实可配对”的决定性实验，并完成预检、正式统计和证伪审计。

### 阶段
- [complete] 审计现有路网、触发器、风险窗口和上轮零效应原因
- [complete] 比较候选实验架构并取得用户对决定性设计的确认
- [complete] 写入设计规格与逐步实现计划
- [complete] 以TDD实现目标风险触发、物理隔离拓扑和冻结判据
- [complete] 完成CPU预检并冻结事件率、效应窗、阈值和样本量
- [complete] 运行正式配对实验、安慰剂、通信剂量和独立通信核验
- [complete] 生成结构化统计结果并回填推进文档
- [complete] 完成首轮受控合流迁移并按预注册门槛判为不支持，不将负均值解释为迁移成功
- [complete] 事前冻结源车物理资格、补充锁和全新种子，完成修正后的20种子×4单元正式迁移实验
- [complete] 正式效应、机制、协议和物理实现14项门槛全部通过，并回填周推进文档

### 硬性门槛
- 设计批准前不修改实验代码或启动正式仿真。
- 主结局、观察窗、排除规则和停止规则在预检后一次冻结，正式结果不得反向调参。
- 目标风险必须在无消息反事实中真实存在；通信动作必须先于任何可观测物理到达。
- 至少10个有效配对种子；若效应区间不排除预设等效区间，结论必须判为不支持。
- 当前阶段优先CPU；只有引入并训练新模型时才申请GPU。

### 执行证据
- 规格：`docs/superpowers/specs/2026-08-07-decisive-nonlocal-risk-design.md`
- 计划：`docs/superpowers/plans/2026-08-07-decisive-nonlocal-risk-experiment.md`
- 隔离工作树：`C:/Users/Lenovo/.config/superpowers/worktrees/code/nonlocal-pilot-a`，分支`experiment/nonlocal-pilot-a`
- 实施前基线：77 passed（2026-08-07，9.39 s）
- Task 1 RED：`tests/test_decisive_dual_corridor.py`在收集阶段按预期失败，根因为`ModuleNotFoundError: mixlab.decisive_trial`；证明新trial接口尚未存在。
- 实现后聚焦回归测试为83 passed，`compileall`通过；受控合流扩展后的全量回归为133 passed；双走廊正式实验完成80/80次、独立通信核验36/36次、合流正式实验80/80次。
- 双走廊正式分析支持门槛全部通过：配对种子数、等效区间、方向一致性、无碰撞、事件不变性、采用前目标一致性、控制单元零采用和拓扑零路径。
- 合流校准按8/9/10步盲序贯执行，10步首个通过并冻结；正式合流均值`Delta_NL=-0.0069459`、95% CI `[-0.0095418,-0.0042398]`，但仅12/20个种子有效采用且方向为负，未达到16/20和逐种子采用门槛，结论为不支持迁移。
- 修正实验未删除旧种子，而是用6个独立种子事前冻结最低速度2.7 m/s与剩余距离不少于`0.8v`的源资格；6/6形成真实制动，补充锁哈希为`7E4DC444DA9C44C69D6D997D6491F778FDC62801004B12C84ACB6BA2D1E92E32`。
- 全新正式种子2026081101—2026081120完成80/80次运行，0碰撞；`Delta_NL=-0.0102834`，95% CI `[-0.0119463,-0.0082990]`，符号置换`p=9.999e-5`，18/20为负、2/20为0。
- 14项冻结判据全部通过：样本量、实质阈值、方向数、无碰撞、事件不变、采用前一致、控制格零采用、逐种子采用、采用先于分化、协议锁、源资格、r10/r11源事件实现及父/补充锁匹配。

### 本轮错误记录
| 错误 | 次数 | 处理 |
|---|---:|---|
| WSL heredoc中的Python路径引号被外层shell剥离 | 1 | 不重试该写法，改用WSL UNC直接读取Flow源码。 |
| 假定通用`AccelEnv`位于不存在的`envs/loop/accel.py` | 1 | 先枚举真实文件，确认路径为`flow/envs/ring/accel.py`。 |
| WSL `grep`因参数转义异常扫描到项目根目录并超时 | 1 | 终止该方式，使用带`-LiteralPath`的UNC文件读取。 |
| 直接调用`python`时WSL仅提供`python3`且无pytest | 2 | 枚举到项目虚拟环境`/home/shen/shen/mixed_autonomy_lab/.venv/bin/python`后，用该解释器完成83项测试和编译检查。 |
| 首次合流迁移预检未形成有效源—目标事件并超时 | 2 | 进一步对齐机制日志与state后推翻“流入车辆未受控”的初判，定位为仿真子步错位与失效ID残留；废弃旧输出。 |
| 合流迁移复用merge配置的`sims_per_step=5`，机制步与state行号错位 | 1 | 将迁移runner冻结为`sims_per_step=1`，重新运行并通过目标观察窗审计。 |
| 四个merge进程并行运行时SUMO/写出卡住，state文件保持0字节 | 1 | 终止本次并行预检，改用单进程串行运行；不使用v4输出。 |
| 外层PowerShell展开WSL循环变量`$cell`，导致三个单元参数缺失 | 1 | 改为固定cell命令分别运行，三次运行均成功。 |
| 外层PowerShell展开WSL验证命令中的`$PY`，使Python文件被bash误执行 | 1 | 不再传递该变量，改用虚拟环境解释器绝对路径重跑。 |
| WSL smoke命令再次使用`$PY/$OUT`并被外层PowerShell展开 | 1 | 改用四条完全展开的解释器和输出路径命令，正式脚本内部变量不经PowerShell拼接。 |
| WSL兼容性复核的嵌套`python -c`引号被Bash截断 | 1 | 拆为独立分析命令和PowerShell JSON读取，不再嵌套多层引号。 |
| PowerShell首次把4个summary JSON数组当作4个对象，误报4行和4次碰撞 | 1 | 逐文件展开数组后重算为80行、0碰撞；错误计数未写入正式分析。 |
| 合流分析器首次在cell目录查找summary，但runner实际写在输出根目录 | 1 | 按真实目录结构改为`cell_dir.parent`读取并重新分析。 |

## 真实风险通信与类超距核验实验（2026-08-06）

### 目标
在现有显式 ETA 通信基线上实现真实源风险消息，完成源风险×指定通道的配对实验，并用独立核验实验逐项检验第二部分的拓扑、时间、来源和反事实判据。

### 阶段
- [complete] 审计上游工作树、WSL运行副本、依赖和既有通信接口
- [complete] 编写实现计划并冻结源事件、消息、控制、指标和运行矩阵
- [complete] 以TDD实现风险事件注入、风险消息与透明控制采用
- [complete] 以TDD实现四组实验、机制日志、来源安慰剂和独立核验条件
- [complete] 完成CPU smoke并审计32个配对单元
- [complete] 完成8次风险门控配对和4次独立通信核验
- [deferred] 正式扩展到160次运行：smoke未产生可测目标风险，先重构场景再扩种
- [complete] 将真实结果、失败项和证据边界写入推进文档

### 完成门槛
- 所有新增行为均有先失败后通过的自动化测试。
- 主实验四组只切换源事件和指定消息，不关闭原控制器或局部感知。
- 日志可连接源事件、消息生成/交付/采用、动作和目标风险。
- 主效应、安慰剂、时间顺序和物理路径核验均有结构化输出。
- 未通过的定义条件明确报告，不以相关性替代因果结论。

### 资源边界
- 使用WSL中的Flow/SUMO与CPU并行运行；不重新训练DRIFT。
- 只有出现必须训练的新模型时才申请GPU，本计划不包含该步骤。

### 错误记录
| 错误 | 次数 | 处理 |
|---|---:|---|
| WSL `grep -E` 正则中的竖线被外层 PowerShell 拆成命令 | 1 | 改用 `\\wsl.localhost\Ubuntu` UNC 路径和本地 `rg`，不重复跨两层 shell 的复杂正则。 |
| PowerShell 语句级 `foreach` 直接接管道导致空管道语法错误 | 2 | 再次出现于 checkpoint 探查；已固定使用 `$rows = foreach (...) {...}; $rows | Format-Table` 模式，后续不再直接接管道。 |
| 并行接口审计中一个独立 `rg` 无匹配返回 1，使组合调用整体提前退出 | 1 | 按规则视为“未找到”，拆分调用并显式把退出码 1 归一化为正常结果。 |
| 按命名规律猜测了不存在的 Pilot B 配置文件名 | 1 | 先枚举 `configs/nonlocal_pilot_b_*.json`，再读取实际存在的修正配置。 |
| WSL 冷启动探测在 10 s 和 20 s 两次超时 | 2 | 改用 120 s 的一次性冷启动检查；环境随后在 8 s 内恢复，确认虚拟环境可用。 |
| 批量生成四个 JSON 时首个公共字段残留了补丁标记 `+` | 1 | JSON 解析准确定位到该字符；用最小补丁删除四个文件中的残留标记并重新验证。 |
| `apply_patch` 修复事件首步标志时上下文与真实文件不完全匹配 | 1 | 重新读取目标片段，按真实内容提交最小补丁；未改用跨 shell 写入。 |
| 分析器按字典序选取 emission，混入其他渗透率/需求文件 | 1 | 先写失败回归测试，再按渗透率、需求和 run index 精确匹配；重算全部主实验和门控结果。 |
| 控制器 step 直接乘 0.2，使结果窗比 emission 锚点晚 0.2 s | 1 | 由两组真实位置记录确认 `time=(step-1)×0.2`，增加回归测试并重算结果。 |
| 两个独立验证首次使用工作树内不存在的 `.venv/bin/python` | 1 | 枚举并确认正式解释器为 `/home/shen/shen/mixed_autonomy_lab/.venv/bin/python` 后重跑成功。 |
| 最终测试命令漏写路径中的一层 `/shen` | 1 | 读取准确错误后改用已确认绝对路径，随后测试通过。 |
| 汇总 analysis JSON 时再次把语句级 `foreach` 直接接管道 | 1 | 按既定规则先赋给 `$rows` 再格式化，后续命令成功。 |
| 跨 shell 的 Python heredoc 引号被 PowerShell 改写，导致一次性读取脚本失败 | 1 | 改用 PowerShell 原生 JSON 读取或固定脚本文件，不再把复杂 heredoc 嵌在 PowerShell 字符串中。 |
| 首次把 gate 输出根目录写成不存在的路径 | 1 | 先枚举实际输出目录，再对 `nonlocal_risk_gate_validation_20260806` 运行分析。 |
| 文档表格审计把不同列数的历史表格与本次三列表格混查，且一次在非 Git 目录执行 diff | 1 | 将检查范围限定为第3.4节，并在实验 worktree 根目录重跑；结果通过。 |

## 量子相关文献调研（2026-07-18）
- [in_progress] 核对现有量子/非局域文献记录并建立检索边界
- [pending] 调研 Bell 非局域性、无信号约束与实验验证
- [pending] 调研量子因果模型与因果发现方法
- [pending] 调研量子概率、量子认知及风险决策应用
- [pending] 判断与交通非局部假设的可迁移部分和不可使用部分
- [pending] 核实 DOI、发表信息和本地文献缺口，形成调研结论

## 目标
在风险传播与因果分析前，判断 DRIFT 是否具备足够的闭环性能、数据真实性和风险事件有效性。结论必须区分“模型表现”“导出接口质量”和“风险研究可用性”。

## 阶段
- [complete] 核对上游正式实验包、指标定义和覆盖范围
- [complete] 为正式结果与本地 pilot 编写可复跑审计测试
- [complete] 实现资格验证脚本并生成结构化结果
- [complete] 解释优势、弱项、异常项和通过门槛
- [complete] 运行测试与审计，形成中文验证报告
- [complete] 将结论同步到本项目研究记录
- [complete] 重构事件分类：制动事件单标签化并单列 SUMO 安全速度覆盖候选
- [complete] 增加车辆时间归一化统计、阈值敏感性和人工复核样本
- [complete] 重提取全部 DRIFT 最终数据并核对输出
- [complete] 视可用性提取 FS、PI、IDM、Flow-AIL 和 Flow-RL 对照数据
- [complete] 运行全套测试、编译检查和结果一致性复核

## 通过门槛
- 正式结果覆盖 ring、figure8、merge，多渗透率和多次运行。
- DRIFT 至少在候选拟合、闭环效率或安全尾部中表现出稳定增益，不要求每项第一。
- 风险传播输入必须保留有效的 leader、lane、位置、速度、加速度和时间字段。
- 无前车车辆不得产生有限 TTC；异常加速度和长时间低 TTC 必须可解释或被剔除。
- 风险事件必须能回到原始轨迹或仿真画面核查。

## 资源边界
- 读取现有结果、运行统计审计和小规模 Flow/SUMO 检查使用 CPU。
- 只有重新训练 Module A/B/C、Flow-AIL 或 Flow-RL 时才需要 GPU。
- 当前阶段不重新训练模型。

## 错误记录
| 错误 | 次数 | 处理 |
|---|---:|---|
| 当前风险传播目录不是 Git 仓库 | 1 | 只记录文件级变更和验证命令，不执行提交。 |
| 审计脚本直接运行时找不到 `riskprop` | 1 | 增加命令行启动测试，并沿用现有脚本的 `src` 路径初始化方式。 |
| PowerShell 展开 WSL 命令中的 `$()`，导致 Bash 命令被错误解析 | 1 | 改用 UNC 路径直接读取 WSL 文件，不再跨两层 shell 拼接命令。 |
| `python -c` 中 UNC 字符串被 PowerShell 改写 | 1 | 对一次性只读检查改用管道输入 Python 标准输入。 |
| PowerShell `foreach` 输出后直接接管道触发空管道语法错误 | 1 | 将循环结果先赋给变量，再单独格式化；其余并行读取未执行，重新拆分。 |
| 假定正式 emission 文件名含 `run0`，目标文件不存在 | 1 | 不再猜文件名，先枚举正式目录并从实际首个文件读取表头。 |
| PowerShell 管道向 Python 传递中文报告路径时文件名变成问号 | 1 | 一致性审计改用输出目录中的 `*.md` 枚举，不在跨进程脚本中硬编码中文文件名。 |
| 最终行号检索中的双引号正则被 PowerShell 拆成路径参数 | 1 | 改为单引号正则并拆分查询；不重复原命令。 |
| PowerShell 5 `ConvertFrom-Json` 将 OpenAlex 倒排索引中的大小写键视为重复键 | 1 | 保留 `curl` 获取方式，改用 Node 的标准 JSON 解析器从标准输入读取，不重复使用 PowerShell JSON 解析。 |
| IEEE 新建后台页后的首个复杂 `/eval` 返回 `Uncaught` | 1 | 保留 target，先用 `/info` 与最小表达式确认加载状态，再逐步提取 DOM；不重复原复杂表达式。 |
| IEEE 页面 `meta[name=description]` 选择器表达式返回 `Uncaught` | 1 | 正文 `innerText` 已完整包含原始摘要与定义，不再依赖 meta 提取。 |
| Semantic Scholar 精确题名查询返回 0 条，随后接口触发 429 | 1 | 不重试该接口；改用 Crossref 精确题名接口和期刊原始页面核对。 |
| ScienceDirect 两篇 AAP 原始页经 Jina 访问触发机器人验证/返回脚本噪声 | 1 | 不重复静态入口；改用 PubMed E-utilities 获取出版社提交的题录与摘要。 |
# Full Risk Event Visual Package (2026-07-18)
- [complete] Lock the visual package contract and write failing tests
- [complete] Implement full-dataset summary and sensitivity figures
- [complete] Add representative adjacent-frame event figures
- [complete] Add a reproducible renderer and extraction integration
- [complete] Run full tests, compilation, rendering, and pixel-level review
# Local Propagation Baseline (2026-07-18)
- [complete] Define eligibility, local relations, and failing tests
- [complete] Implement one-hop edges and multi-hop traversal
- [complete] Add permutation null and threshold sensitivity
- [complete] Generate ten baseline figures and representative chains
- [complete] Run the formal dataset and verify graph/data invariants

## Local Baseline Error Log
- Formal 100-permutation run exceeded the 600 s command limit on the first attempt. No completed output was claimed; profile the null and sensitivity stages before changing the algorithm.
- Windows `ProcessPoolExecutor` failed when tested from `python -` because worker processes cannot import the `<stdin>` main module. The formal CLI has a normal `if __name__ == "__main__"` entry point and was verified instead.
- A manual verification script first assumed edge tables used `source_file`; actual local-baseline tables use `run_id`. The check was corrected to the exported schema.
- A manual verification check incorrectly treated adjacent override context as an exclusion. The actual rule excludes `safe_speed_override_candidate` events and boundary rows, while adjacent-override context remains a reporting stratum.
- Direct stdin visual regeneration initially missed `PYTHONPATH=src` and then used the wrong `sensitivity` table key. The verification script was corrected before figures were regenerated.

# Project Reappraisal And Literature Synthesis (2026-07-21)
- [complete] Re-read current README files, repository structure, recent outputs, and manuscript claims
- [complete] Audit the local literature corpus and map papers to actual project assumptions
- [complete] Trace the implemented event, graph, null-model, and intervention boundaries in code
- [complete] Supplement only the literature gaps needed to challenge or extend the current framing
- [complete] Synthesize verified facts, unresolved risks, and independent research directions
- [complete] Verify citations and internal consistency, then deliver a detailed Chinese assessment

## Reappraisal Questions
- What is the project actually able to claim today, as distinct from its intended final contribution?
- Which assumptions are measurement choices, which are causal assumptions, and which are simulator artifacts?
- Does a propagation graph add scientific information beyond event clustering and local interaction graphs?
- What falsifiable intervention result would turn the work from descriptive analysis into a causal contribution?
- Which alternative framing gives the strongest paper if the nonlocal hypothesis fails?

# 非局部问题文献调研与定义收敛（2026-07-25）
- [complete] 恢复既有项目审计、非局部文献和上游跨支路 ETA 机制结论
- [complete] 补查近三年非局部/前视信息、通信拓扑、风险级联和闭环因果干预文献
- [complete] 比较文献定义的可迁移性、不可用边界和竞争解释
- [complete] 形成项目的操作性定义、识别条件、反证标准与第一部分汇报结构
- [complete] 核验 DOI、年份和一手来源，向用户提交仅限第一部分的结论

## 当前边界
- 主定义候选为“显式信息或控制通道介导的非最近邻因果作用”，不采用固定米数或无通道的物理超距定义。
- 统计时序方法只负责候选发现；因果命名必须经过通道开关/限幅/延迟等配对闭环干预。
- 当前只研究第一部分，不修改代码、论文、创新点或实验实现。

# 周推进文档完善（2026-07-26）
- [complete] 解释远端机制、机制激活/退出条件与候选机制开关
- [complete] 基于本地一手文献重构可执行、与机制无关的区域定义
- [complete] 完成核心文献对比表、本项目目标与创新点凝练
- [complete] 设计区域尺度、局部范围和远端机制开关的小实验
- [complete] 更新 `7.21-7.28推进.md` 并检查公式、表格与表述边界

## 本轮写作边界
- 区域采用“固定长度为基础、拓扑点强制切分”，机制激活状态不用于切区。
- 文献已有方法、本文拟采用定义、当前代码已实现内容必须分开表述。
- 本周只定义可复现的小实验，不把尚未完成的 DRAC、远端日志和反事实结果写成既有成果。

# 非局部 Pilot A 执行（2026-07-26）
- [complete] 建立实验设计、执行计划和隔离工作区，验证基线与固定种子接口
- [complete] 实现拓扑区域划分，完成 25/50/75 m 尺度分析
- [complete] 实现跨支路 ETA 机制 on/shadow-off、完整机制日志和配对随机种子
- [complete] 在 WSL 中运行 p60/p80 各 on/off、同一 seed 的 4 次冒烟仿真
- [complete] 汇总区域稳定性、机制触发、开关有效性、配对一致性和安全/效率指标
- [complete] 完成全量测试、输出审计和实验边界说明

## Pilot A 验收条件
- 旧正式输出不被覆盖，新结果只写入 `code/outputs/nonlocal_pilot_a_20260726` 和独立上游输出目录。
- on/off 使用相同初始随机种子；首次机制实际生效前，车辆集合与轨迹保持一致。
- on 组至少出现一次 `applied=true`；off 组允许 `would_trigger=true`，但 `applied` 必须始终为 false。
- 机制日志包含 run token、ego/remote 车辆、两车 ETA、ETA gap、候选触发、实际应用和最终动作。
- 25/50/75 m 区域结果可复现；同时报告风险区域数、排序相关性、事件归属一致性和局部距离分位数。
- 4 次仿真仅作为机制冒烟验证，不声称统计显著的因果效应。

## Pilot A 错误记录
| 错误 | 次数 | 处理 |
|---|---:|---|
| 并行环境探查脚本中一个子命令以非零状态退出，导致组合调用只返回首段输出 | 1 | 拆分调用，分别读取计划文件、Git 状态和 session catchup；三项均已成功获取。 |
| `wsl bash -lc` 经 PowerShell/WSL 参数转义后把含空格和括号的 PATH 拆入命令，环境探查失败 | 1 | 不重复内联复杂命令；改为用 `apply_patch` 创建临时只读探查脚本，再由 WSL 执行脚本文件。 |
| 同时通过 UNC 枚举 WSL emission 并读取下游 CSV，10 s 内未完成 | 1 | 不重复并行 UNC 枚举；下游本地文件单独读取，WSL 文件改由已验证的脚本入口枚举。 |
| WSL 正式运行副本的 3 个目标文件与 Windows Git `main` 哈希不一致 | 1 | 已用 `git diff --no-index` 确认不是换行问题；WSL 是生成正式数据时的较早控制器版本。禁止整文件覆盖，改为先备份，再把已测试的最小开关/日志/seed 补丁逐段移植到 WSL 当前版本。 |
| WSL 收尾审计再次使用双引号内联 Bash，PowerShell 展开 `$root/$backup`，且系统没有 `diffstat` | 1 | 不重复内联命令；改用 `apply_patch` 创建固定路径审计脚本，以 `diff --brief`、`wc` 和备份哈希校验替代 `diffstat`。 |

# 显式通信与主论文同步推进（2026-08-02）
- [complete] 恢复周报、代码、实验输出和主论文的当前状态
- [complete] 审计 Pilot A 可复用接口与显式通信缺口
- [pending] 实现消息生成、传输、接收、缓存、采用和控制作用日志
- [pending] 建立源区扰动 × 通信通道的配对因果实验
- [pending] 运行无通信、理想 ETA、显式通信和受损通信对照
- [pending] 核验通信拓扑、时延、丢包和交通安全相关文献
- [pending] 逐节补齐 `7.29-8.4推进.md`
- [pending] 同步修改 `paper/主论文` 下的 TeX 与参考文献
- [pending] 编译、测试并审计文档、实验和引用一致性

## 本轮证据边界
- 不把上周单种子 ETA 冒烟结果写成通信因果效应。
- 不虚构尚未运行的实验结果、统计显著性或文献结论。
- “类超距”仅指显式通信或控制通道介导的非最近邻作用，不指无通道瞬时物理超距。
- 论文结论必须能回指代码、日志、结构化结果或已核验的一手文献。

## Pilot B completion audit (2026-08-02)
- [complete] Implement and test the explicit ETA message lifecycle and controller integration.
- [complete] Run and audit 32 valid paired cells after excluding and correcting two discovered state/configuration bugs.
- [complete] Generate target-zone risk, communication, paired-effect, and factorial-effect tables.
- [complete] Fill every section of `7.29-8.4推进.md` with evidence-bounded content.
- [complete] Update and compile the main TeX manuscript with communication methods and preliminary Pilot B results.

## 本轮错误记录
| 错误 | 次数 | 处理 |
|---|---:|---|
| Windows worktree 收集 `test_nonlocal_pilot.py` 时缺少 `flow` | 1 | `compileall` 已通过；不在 Windows 盲装依赖，改到上周已验证的 WSL Flow 环境运行同一基线。 |
| WSL 简写路径下直接运行 `tests/test_nonlocal_pilot.py` 找不到文件 | 1 | 命令返回 no tests ran；先枚举实际目录层级，再使用真实测试路径，不重复原命令。 |
| WSL `.venv` 挂载运行 worktree 测试仍找不到 `flow` | 1 | 说明正式启动还依赖外部 Flow 源码路径；从既有脚本和环境变量恢复真实 `PYTHONPATH`，不安装新包。 |
| PowerShell 内联 WSL 环境探查引号未闭合 | 1 | Bash 报 `unexpected EOF while looking for matching '"'`；改用 `apply_patch` 创建固定只读脚本，由 WSL 执行文件。 |

# 第二部分文献详述与 Zotero 入库（2026-08-03）
- [complete] 核对第二部分 7 篇论文的题录、原文来源、现有本地附件和 Zotero 重复项
- [complete] 逐篇提取“问题—方法—结果/结论—对本课题启发”的一手证据
- [complete] 将 7 篇论文录入 Zotero 对应集合并核验 DOI、作者、年份和附件状态
- [complete] 扩写 `7.29-8.4推进.md` 第二部分，纠正超出原文的表述
- [complete] 复核文档、Zotero 条目和本地证据的一致性

## 本轮证据边界
- 论文原结果与“对本课题启发”分栏表述，后者明确标为本课题推论。
- 不以摘要或二手网页替代可获得的论文全文；暂时无法获得全文时明确标注证据层级。
- Zotero 入库前先查重，不重复创建同 DOI 条目。

## 本轮错误记录
| 错误 | 次数 | 处理 |
|---|---:|---|
| Zotero 集合接口返回 `WinError 10061` | 1 | 已确认连接器能读取个人库但 Zotero 桌面端未运行；定位真实程序路径后启动桌面端，再重试集合读取。 |
| 探查 Zotero 进程时 `Get-Process` 无匹配导致组合命令退出码 1 | 1 | 按“未找到结果”处理，不误判为权限故障；已由候选路径检查确认安装位置。 |
| 公开 PDF 批量获取部分失败：IEEE 直链 HTTP 418、Wang 2024 无 OA 命中 | 1 | 保留准确的题录/待补 PDF 状态；改用作者机构库与 arXiv 获取 Hasan、Liu 等合法版本，不伪造附件完成状态。 |
| 两个公开 PDF 的组合下载超过 120 秒 | 1 | 检查落盘文件后确认 Hasan 完整、Razzaghpour 未落盘；不重复原调用，Hasan 继续入库，Razzaghpour 保留题录。 |
| `pdfinfo` 命令不可用 | 1 | 不安装或猜测依赖；改用 arXiv HTML 和现有全文抽取文本核验 Liu 等论文。 |
| Zotero `add_from_file` 将 5 个 PDF 建成独立 `document`，未关联父论文 | 1 | 通过父条目附件路径和返回键元数据识别真实状态；5个误建条目已移入回收站，7个正确论文条目统一保留在 `98 待补PDF`，本地全文未删除。 |
| Windows Computer Use 无法绑定 Zotero 窗口，错误中的旧/新 owner ID 完全相同 | 3 | 按恢复规则停止 UI 自动化，不使用陈旧坐标；改由 Zotero 连接器完成可审计的题录、集合、标签与回收站操作。 |
| Zotero 语义索引更新缺少 `zotero-mcp-server[semantic]` 依赖 | 1 | 不擅自安装新依赖；普通题录检索与集合核验不受影响，语义索引本轮未更新。 |

# 第5—7篇论文详细解释（2026-08-03）

- [complete] 核对三篇题录、本地全文与一手公开来源
- [complete] 从风险理论、非局部PDE和混合交通三个视角提取问题、方法、结果与边界
- [complete] 按与第四篇相同的详细标准解释第5篇
- [complete] 按与第四篇相同的详细标准解释第6篇
- [complete] 按与第四篇相同的详细标准解释第7篇
- [complete] 综合比较三篇与类超距作用、显式通信实验的关系并核验引用

## 本轮专家视角

- 随机网络与风险控制：关注条件碰撞风险、AVaR、拓扑与时延下界。
- 非局部守恒律与PDE：关注积分核、作用范围、稳定性证明与常数核反例。
- 混合交通流建模：关注ARZ多类别模型、前视距离、CAV渗透率与空间分布。
- 因果与实验审稿：区分理论机制、数值仿真和本课题可识别的跨支路因果效应。

## 本轮证据规则

- 每篇优先使用正式论文、作者版或出版社原始页面；摘要层证据不扩写成全文结论。
- 定量结果必须能在原文中定位；无法定位时明确说明证据缺口。
- 论文结论与“对本课题启发”分开，后者作为项目推论而非作者原结论。

# 修正源事件资格后的合流决定性实验（2026-08-08）

- [complete] 从既有20种子正式日志推导源事件资格门槛，禁止按效应结果选择阈值
- [complete] 冻结补充预注册、全新校准种子和全新正式种子
- [complete] 按TDD实现资格筛选、协议锁定和源事件审计
- [complete] 完成独立烟雾校验并锁定配置
- [in_progress] 执行全新正式四格实验并按预注册门槛判定
- [pending] 更新推进文档、发现记录和完整验证证据

## 本轮硬性边界

- 已使用过的2026080801—2026080820只用于诊断失败机制，不进入新一轮效应统计。
- 资格条件只能依赖触发前可观测状态和道路几何，不能依赖消息是否生成、后续TTC或效应方向。
- 新正式结果开始前冻结配置、种子、主要结局和全部支持门槛；正式运行期间不查看中间效应。

## 本轮错误记录

| 错误 | 次数 | 处理 |
|---|---:|---|
| 将WSL UNC网络文件全量读取和20份机制JSONL解析放入同一并行命令，20秒后超时（exit 124） | 1 | 不重复联合命令；拆为网络关键行检索和已有结构化分析字段读取，并提高单项超时上限。 |
| `rg` 搜索机制JSON时引号被错误解析，导致目录反斜杠进入正则并报 `unrecognized escape sequence` | 1 | 不重复该正则；网络文件继续用简单 `rg`，机制日志改用 PowerShell `Select-String -SimpleMatch`。 |
| `get_position` 补丁命中相似的真实风险快照函数，导致决定性快照变量未赋值且旧风险快照测试退化（2 failed） | 1 | 用堆栈和局部diff确认根因；删除误插入行并在 `_collect_decisive_snapshot` 精确赋值，原两项测试及75项聚焦回归随后通过。 |
