# AAD-S0.5-POST-R2-TASK10：Round2 最终综合科研诊断

日期：2026-10-31。基线：`69be65d398f998d4203c6837c4fe79deeb9a4d26`。任务状态：`COMPLETED_WITH_BLOCKERS`。

本任务只做离线证据复用、事件/对照质量审计、物理交互路径审计和 Task9 准入判断。没有重新提取 Formal P2，没有启动 SUMO/TraCI，没有读取第三窗口或 locked holdout，没有下载视频或发送新的数据申请。Formal P2、D1 和 B 的定义保持不变。

## A. Research observations

### 1. 轨迹质量与风险事件稳健性

复用 Task6 已保存的两个 NGSIM source 上下文表，在一秒事件锚点上比较 Formal P2 事件与已有非风险对照：

- 0750–0805：事件 167、对照 165；0805–0820：事件 159、对照 149。Formal P2 计数未重新计算、未删改。
- 两个窗口的 leader onset matching 均为全数可用；事件和对照均没有观察到 backwards trajectory。
- 事件/对照的 gap residual 和 position–speed residual 中位数总体接近。0750 事件 gap residual 中位数为 0.079 m、对照为 0.075 m；position–speed residual 中位数为 0.047 m、对照为 0.043 m。0805 对应值分别为 0.056/0.058 m 和 0.029/0.024 m。
- 0750 事件 acceleration residual 的中位数为 0.070 m/s²、对照为 0.053 m/s²；95 分位为 0.975/0.253 m/s²。0805 的中位数为 0.030/0.035 m/s²，95 分位为 0.279/0.186 m/s²。该差异是描述性质量信号，不能单独判定事件为测量异常。
- 事件的 onset gap/closing 与对照明显不同，这是风险状态本身的样本差异，不能把它当作质量偏差。
- Jerk 和 spectral analysis 没有重新实现：加速度及其滤波噪声尚未形成独立验证链，Task10 不为了形式完整引入新的信号处理管线。

结论：当前轨迹足以支持受限的内部一致性和微观交互描述，但不足以提供独立物理真实性证明。事件没有因为质量审计被重新筛选或删除。

### 2. PreciseNGSIM 辅助交叉验证

Task7.1 已有的两个 PreciseNGSIM 文件检查被重新用于事件级准入判断。结构、字段和范围资料可读，但完整事件级对应关系不能可靠建立：

- 既有检查只建立了结构/范围和前 500 行来源比较，并非全量事件 identity crosswalk；
- `Vehicle_ID`、`Frame_ID`、`Global_Time` 等字段继承原始 NGSIM，不能作为独立身份或时间真值；
- 两个窗口的 `Local_Y`、`v_Vel`、`v_Acc` 在已有字段比较中均存在差异；
- 每个窗口保留一个末行语义异常/诊断标记，且时间支持较短。

因此 PreciseNGSIM 事件级 crosswalk 状态为 `BLOCKED_EVENT_LEVEL_CROSSWALK`，没有重新计算辅助 P2、TTC、gap 或 closing speed，也没有改变正式 167/159。

### 3. 真实交通物理交互路径

在两个 canonical NGSIM 窗口中，以已有 Formal P2 source/target 事件锚点寻找同一车辆的 source→target 有序候选：

- 0750–0805 有 16 个同车有序候选；0805–0820 有 24 个，共 40 个；窗口之间没有合并身份。
- 40/40 具有可追溯车辆身份、时间化 lane/road 记录、连续 canonical 轨迹、连续 leader/follower 观测和 source 先于 target 的时间顺序。
- 40/40 的 `physical_connection_basis` 为 `Unknown`：当前 `road_id=US-101` 和 lane/time 记录不能独立证明从 source 到 target 的物理连接依据，也不能替代已批准的 B 类真实路径见证。
- 因此合格 B witness：0；`Unknown`：40；`FAIL`：0。

这些候选是同车运动和事件先后关系的描述性证据，不是已验证的物理传播链，也不构成 source risk 导致 target risk 的因果证据。

## B. Method reuse

直接复用：

- Task4/5 的正式事件、onset attribution、窗口独立性和数据完整性；
- Task6 的 identity-context 生成、gap/position–speed/acceleration residual、leader/lane transition 和事件/对照匹配；
- Task8 的五秒运动学分解、固定 onset leader、`C_initial/C_f/C_l/C/C_gap/R` 和 SUMO Krauss 源码边界；
- Task9 的 B00/Round2 arm audit、共同 leader/初始状态契约和三 seed 状态；
- Punzo 风格的 internal/platoon consistency 方法边界，以及 Task7.1 已有 Zhang/STDE/PreciseNGSIM 检查结果。

本次真正新增：

1. Task6 事件/对照质量字段的窗口级和指标级比较；
2. PreciseNGSIM 是否具备事件级辅助比较条件的准入判断；
3. canonical trajectory 上 source→target 同车候选的 B 五项逐项审计；
4. Task9 最终准入和 Round2 综合决策。

机器证据：`evidence/results/RES-STAGE-0.5-POST-R2-TASK10-FINAL-DIAGNOSTIC/`。

## C. Limitations

- 内部轨迹一致性不等于独立物理真实性；无视频、独立标定或车辆几何链。
- PreciseNGSIM 不能提供可靠事件级独立 crosswalk。
- 40 个 source→target 候选缺少 B 所需的独立 physical connection basis。
- Task9 没有合格物理片段，不能执行固定前车正式实验。
- 网络扰动供给、纵向响应、换道/多车交互、测量误差和人群构成差异仍无法唯一分离。

## D. Scientific interpretation

**Observation：** Task6/Task8 的真实—SUMO 微观交互差异仍在已有测量边界内可复用；风险事件与对照的部分加速度残差尾部存在描述性差异；真实窗口内存在 40 个同车 source→target 有序候选。

**Interpretation：** 这些结果支持继续把真实事件用于受限机制诊断，但不能把当前轨迹包装成独立物理真值，也不能把同车时序关系包装成已验证物理传播。

**Hypothesis：** 网络扰动供给不足、车辆纵向条件响应差异、换道/多车交互和测量质量仍是竞争性解释；Task10 没有唯一选择其中之一。

## E. Final decision

- 真实风险事件的测量稳健性：**部分足够**。内部一致性和事件/对照比较可支持描述性研究；独立物理真实性仍 Unknown。
- 合格 B 类物理路径：**0 条**。40 条同车有序候选均因 physical connection basis Unknown 不能通过。
- Task9 执行条件：**不具备**。Task9 工程接口充分，但合格物理输入为 0，固定前车正式运行保持 `Blocked by physical input`。
- Stage 0.5：**继续 blocked**；scientific equivalence 继续 `false`。
- 距离下一阶段缺少：独立物理参考及许可/时间/空间闭合、可验证的 B 类物理连接依据，以及合格的固定前车物理片段。当前不需要追加参数搜索或新仿真矩阵。

最终分类为 **Case B：部分证据成立，但物理路径和固定前车输入仍不足**。Round2 到此收口，不自动创建 Task10.1/Task10.2/Task10.3，不启动 Round3、Stage 0.6、Protocol Lock 或 Stage I。
