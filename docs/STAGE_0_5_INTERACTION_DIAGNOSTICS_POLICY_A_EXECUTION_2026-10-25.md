# 政策 A：首次尝试失败与停止报告

Task ID：`AAD-0.5-INTERACTION-DIAGNOSTICS-V1`；Result ID：`RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1`。

**Status: Stopped / Evidence Insufficient。新轨迹 1/3，失败 1 次；ID2、ID3 未执行，剩余 2 次未动用。WP2 的任务级计划获批并绑定，WP3 的有限测量整改有离线证据，WP4 设计已确认；WP5 未完成三次对照，WP2–WP5 不标为整体完成。**

## 研究者决定与精确绑定

2026-10-25 研究者批准政策 A 最终科学设计及三次职责，允许完成任务级隔离整改后逐次启动；每次结束先核验再继续。执行沿用 elapsed `[120,390)`、供给 `[180,240)`、offset100 两块、seed20261201、420s，未改变网络、行为、阈值或科学 Gate。

批准原文计划保持字节不变，即使其历史正文仍写 Proposed：`docs/plans/2026-10-25-stage-0-5-interaction-diagnostics-policy-a-final.md`，SHA256 `ba79b36733fcb93b37898250c5c12dbe074efa36af8798ac0cc3644a7bbd39a7`。机器提案 `review_ready_plan.json` SHA256 `0f0d84aec6881c957d10331a96dfd22c809980e53f8726af72599a27d2219f97` 同样保留为历史快照。新的 `execution_freeze.json` 记录研究者对该确切设计的确认与附加工程入口哈希；不是 Protocol Lock。

研究者裁决保留 `POLICY-A-VALIDATION-SCOPE-01`，任务级数据隔离 **Not Accepted**；998 passed 主工作区回归无隔离验证效力。没有完整运行时访问追踪，不能证明全范围零访问。目前材料未指出第三窗口或 locked holdout 被访问；意外访问临时产物不作为科学证据。该偏差不自动取消有限诊断资格，不再扩展历史数据审计或重跑全量回归。

## 启动前与工程边界

只读哈希核验覆盖批准源码、最终计划、准备文件、两份获准参考/基线输入、SUMO 二进制与 TraCI 文件；均匹配提案基准。新隔离代码仅有当前冻结值，没有历史未变基准；历史意外访问的文件完整性与全范围访问集合仍 Unknown。

新增入口仅允许精确输入文件、Python 运行库、任务输出和注册的一次 Python/SUMO 子进程；写入局限于任务目录，拒绝额外进程和 shell。子进程使用 `-I -S`，禁用未绑定历史字节码，SUMO 的 XML 输入/输出引用经静态检查。它是可执行的 Python 白名单及固定原生输入约束，**不是 OS 沙箱或原生完整文件追踪**。两次运行库根目录枚举被拒绝，父监督器无拒绝项；不据此将任务级隔离改为 Accepted。

导入预检不生成轨迹；首次工具包父目录枚举被拒绝，修正仅目录枚举许可后通过。两次受限测试环境临时目录错误、既有 pyarrow 不可见及首次启动命令读取 UTF-8 确认文件失败均保留为工程预检失败；UTF-8 错误发生在预算登记和任何子进程启动之前。随后完成明确编码修正并重新绑定工程哈希，才登记唯一轨迹尝试。无已登记尝试重试。

启动前 C/D 空闲 116616015872 / 241465208832 B，可用内存 12589006848 B。监督器 wall/RSS/磁盘/输出限额均保留，未清理资料。

## Observation

`ID1_SUPPLY_0750` 在启动前登记 attempt1；唯一 SUMO 进程非零退出。wall 14.3401s，进程树峰值 RSS 70836224 B。原始 FCD、summary、getter、配置和完整失败日志保存在独立本机目录，历史结果未覆盖。

SUMO 在 t=0 报 `i0007_i0007` 因前方慢车无法按声明速度出发；末条 summary 记录 discarded=1。t=180 限速切为5后，报告 `i0063_i0063` 对 main_2 的声明出发速度过高，并退出；TraCI 报 Connection closed。FCD 最后179.9s，summary 最后179.95s；getter最后180.0s：running149、inserted496、arrived347、pending63，下游五车道限速均5m/s，逐行车辆守恒成立。没有完成60s供给脉冲和恢复阶段；不能声称条件输入按计划完整实现。

初始化、逐阶段/逐块状态、净间距、closing、TTC、完整上下文事件成员和 D1 部分暴露见便携 `failure_review.json`、`common_support_18_cells.csv` 及本机 `partial_measured_state.parquet`。未观测后续单元显式缺失，不补零，不把部分暴露当270s完整支持。新运行初始化独立测量，不套用旧基线的1辆/106条结论。

新运行在120s局部初态1辆、全网在场初态2辆；局部最后130.5s、窗内106条/10.6veh-s。117辆声明初态中有9辆截至失败未在FCD出现，不能把它们全部认定为pending；具体pending身份未采集。报错的 `i0063_i0063` 声明 depart=0、departSpeed=10、route=from_main_2_through，失败前从未出现于FCD。

部分上下文P2=0、D1 E=1933.0veh-s，仅是已有轨迹的局部统计，完整270s风险率为不可评价。4个单元有完整半开状态点与正的部分D1暴露，其中仅前2个单元具有完整右端点D1支持：`[150,180)`块缺少180.0s状态，不能与基线完整边暴露等同。扰动前状态均速11.4711m/s、离散3.3620m/s、密度37.1917veh/km/lane，与基线相同；D1 E比基线1936.6少3.6veh-s，来自缺失末端边，不能解释为行为差异。其余14个状态单元未观测，不解释为零事件。第一版离线审计将半开状态完整与D1边完整混用，已保留并由v2明确更正。

失败触发已冻结的输入可施加性与共同支持停止规则，也使必要对照无法完成，因此不启动 ID2/ID3，不换窗、seed、出发速度、阈值或供给时间，不自动使用剩余预算。

## Interpretation / Hypothesis

**Interpretation（工程范围）**：此配置在脉冲开始时无法完成声明的边界输入，现有证据不足以比较供给机制或匝道机制对平均状态、相对运动及风险的影响。不能从未完成运行推断“机制无效”或“零风险”。已完整观测的扰动前阶段仅作预声明阶段的描述性对照。

**Hypothesis（待研究者决定）**：局部已退出的初态车辆并不保证所有待插入初态已消失；固定数值出发速度可能与动态供给限速冲突。下一步最小有效工作是先明确待插入初态与动态限速的相容政策，再决定是否修改输入编码或初始化方案。选择会影响条件输入与可比性，需重新提交具体方案及剩余额度说明；本轮未实施任何替代方案或新实验。

## 验证与边界

沿用已保留的无数据 Git 克隆全量回归987 passed /14 skipped /7 deselected，仅证明其软件覆盖范围，不是本次实际环境的隔离证明。新增工程使用定向非轨迹测试、compileall、严格文档检查、便携证据及纯 Git 入口复核；精确最终记录见 `validation_record.json`。

Gate 仍为 `pending_simulation_sample`；`scientific_claim_eligible=false`、`reality_coverage_accepted=false`、`protocol_lock_allowed=false`、`stage_1_1_allowed=false`。δ/h/B 未获批准，WP1 正式冻结候选仍 Proposed / Awaiting Researcher Decision。本报告完成失败归档和停止交接，未宣称三次诊断完成。
