# AAD-S0.5-POST-R2-TASK9：独立物理参考与固定前车配对准备

日期：2026-10-31。任务状态：`COMPLETED_WITH_BLOCKERS`。

本任务沿两条已授权工作流推进：恢复 Task7 官方询问状态并尝试核查可用邮件通道；复查 Task8 固定前车方向、封存 B00/Round2 输入和历史 324 次重放，并把本次 minGap-only 配对契约落到可验证的工程代码。Stage 0.5 仍 `blocked`，`scientific_equivalence=false`，Stage 0.6、Protocol Lock、Stage I 和 Round3 均未启动。

## 1. 影响范围与停止边界

修改范围是 Task9 独立配对契约、证据准备脚本、定向测试、报告与事实索引。没有修改 Formal P2、D1、事件窗口、数据分割、模型数学逻辑或生产实验配置；没有读取 holdout、第三窗口或私人研究笔记，没有下载视频，没有启动 SUMO/TraCI，也没有重跑历史 324 次实验。

本轮把“历史配置可复用”与“真实物理输入已合格”分开处理。代码只允许验证静态配置、共同前车输入、匹配初始状态和运动学积分残差；缺少合格物理片段时不会构造或运行合成正式样本。

## 2. 工作流 A：官方沟通与独立物理参考

原询问未改写，继续使用 Task7.2 证据包中的 `provider_inquiry_draft.md`，原始 SHA256 为 `212d3f2299138061d6ee5a60dfb0be0fab8f95d8403197e3b620ab5359c981ee`，收件地址仍为 `data.itsjpo@dot.gov`。询问六项保持不变：四个 raw AVI 的适用许可、科研/论文/衍生图片与结果发布权限、最小子集和校验信息、实际采集时间与时区、PTS/time base/FPS 及 Frame_ID/Global_Time 对应、相机同步偏移/漂移和 Local_Y 空间对应。

本轮没有形成实际发送。Windows Edge 窗口无法被 Computer Use 安全层可靠解析当前 URL，因此没有进入邮件界面；随后尝试应用内 Gmail 入口被安全审查拒绝，原因是 Google Accounts 认证来源未被特定授权且没有绑定已确认的账户。两个动作都没有输入收件人、正文或附件，没有实际收件人、发件身份、发送时间、Message-ID 或发送回执。该状态记录为 `NOT_SENT_BLOCKED`，原始未发送 EML 和 Task7 dispatch 记录保留不变。

因此许可、资源使用条件、视频 PTS/实际起止时间、Frame_ID 对应、相机同步和有效源车道覆盖仍为 `Unknown/Blocked`。四个 raw AVI 仍只完成目录级元数据核验：压缩成员合计 1,248,582,779 bytes，解压大小合计 1,248,560,044 bytes；没有载荷下载、CRC32 载荷核验、ffprobe、时间映射或人工视频审查。独立物理参考状态仍为 `BLOCKED_NO_VERIFIED_INDEPENDENT_PHYSICAL_REFERENCE`，抽样对象为 0。

## 3. 工作流 B：固定前车配对工程准备

### 3.1 封存输入复查

直接读取封存的 B00 A03 与 Round2 candidate-v1 路线/网络/仿真配置，确认：

- 两组路线 XML 的差异恰为五个异质 passenger vType 的 `minGap=2.5` 到 `1.0`；
- 五档 tau 保持 `0.7389146576529666`、`1.093342856277335`、`1.3877275660721775`、`1.8288599276236361`、`2.5614676647488244`；
- `network.net.xml` 与 `run.sumocfg` 字节一致；
- 历史响应包为 324 行、20 s、三个 seed `20261101/20261102/20261103`。

历史 324 次数据仍只作为工程和随机波动参考，不是当前异质 B00 的 Task9 结果，也不转移为物理参考或当前统计功效证据。

### 3.2 本次冻结的条件配对契约

本任务批准的三 seed 采用既有预声明集合：每个合格物理片段执行 6 次（A/B 两臂各三个 seed），总量为 `6N`。A 为原始异质 B00 `minGap=2.5 m`，B 为相同异质 B00 且仅 `minGap=1.0 m`。五档 tau 必须保留，不替换为 homogeneous tau=1.0。

两臂必须读取同一外部前车位置/速度序列和同一物理时间锚；后车初始速度、前车初始速度和实际物理净间距匹配。匹配目标是物理 net gap，不是各臂 `minGap` 调整后的模型内部间距。若输入或初始状态不匹配，样本失败；不得平移时间、按结果删除、替换 seed 或以 arm-specific settling 修复。

代码 `riskprop.stage_0_5_fixed_leader_pair` 新增了以下 fail-closed 检查：

1. 静态 XML 只允许五个 `minGap` 差异并校验异质 tau；
2. 共同前车时间、位置和速度必须逐样本相同；
3. 两臂初始 follower speed 与物理 net gap 必须相同；
4. 计算 `C_initial`、`C_f`、`C_l`、`C`、`C_gap` 和残差 `R`，并核验积分代数闭合；
5. 在共同前车和匹配初始速度条件下检查 `ΔC_initial=0`、`ΔC_l=0` 以及 `ΔC=ΔC_f`。

该模块不选择事件、不生成物理片段、不改变正式 P2/D1 定义，也不执行 SUMO。正式指标仍分别报告 physical net gap、follower/leader speed、closing speed、TTC、运动学分解、响应时序、Formal P2 和适用时的 D1 局部暴露；不合并为综合得分。

### 3.3 当前执行状态

静态配置、公平性契约和定向测试均通过。由于 A 工作流没有取得许可、PTS/Global_Time 映射和有效源车道覆盖，合格物理片段数 `N` 仍为 `Unknown`，本轮正式固定前车运行数为 0，配对观察为 0，B 状态为 `Blocked by physical input`。这不是用任意合成片段替代真实输入，也不是对 SUMO 动态响应的科学结论。

## 4. 结果边界

**Observation：** 静态 B00/Round2 配置只有五个 `minGap` 差异；历史 324 次重放包含三个预声明 seed；Task9 配对契约已可在运行前检查共同 leader 输入、初始状态和积分残差。

**Interpretation：** 若以后取得合格物理片段，配对差异可识别给定前车输入和初始状态下的条件响应；关系 `ΔC=ΔC_f` 是该条件下的可核验运动学判别式。

**Hypothesis：** 本轮没有新数据支持或削弱真实交通与 SUMO 微观交互差异的机制假设；minGap 条件响应仍无法区分。

## 5. 证据与复现

机器证据：`evidence/results/RES-STAGE-0.5-POST-R2-TASK9-FIXED-LEADER-PREP-20261031/`。

- `arm_config_audit.json`：封存输入差异和 tau 核验；
- `historical_seed_audit.json`：324 行、20 s、三个 seed 的历史审计；
- `task9_protocol.json`：本次批准的两臂、seed、指标和停止规则；
- `provider_dispatch_status.json`：未发送状态、阻断证据和原稿绑定；
- `source_bindings.json`：源码、配置和历史包 SHA256。

新增代码：`code/src/riskprop/stage_0_5_fixed_leader_pair.py`、`code/scripts/audit_stage_0_5_task9_fixed_leader.py`、`code/tests/test_stage_0_5_fixed_leader_pair.py`。

## 6. 最终状态

- A 独立物理参考：**未取得**；官方沟通实际发送仍阻断，许可/时间/空间条件未闭合，视频与人工审查未启动。
- B 有效配对观察：**未取得**；工程准备和契约验证完成，正式执行 `Blocked by physical input`。
- 支持/削弱/无法区分：本轮无新的机制主效应；仅确认了未来配对实验的输入公平性和运动学核验边界。
- 下一阶段资格：不足以通过 Stage 0.5，不启动 Round3、Stage 0.6、Protocol Lock 或 Stage I。
