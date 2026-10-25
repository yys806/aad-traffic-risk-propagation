# Stage 0.5 interaction diagnostics：执行前阻断报告

> 2026-10-25 最新执行：研究者已确认政策A最终计划并裁决隔离偏差允许有限继续。精确绑定与任务白名单后，ID1在180s因待插入初态的声明出发速度与5m/s供给限速冲突失败；累计1/3，ID2/ID3按停止规则未执行。当前报告见 `docs/STAGE_0_5_INTERACTION_DIAGNOSTICS_POLICY_A_EXECUTION_2026-10-25.md`，证据 `evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/`。隔离Not Accepted保留，Gate不变；以下是历史阻断时点，不代表当前权限或预算。

> 后续授权与当前状态：C6已获批进行离线修复；当前决策材料见 `docs/STAGE_0_5_C6_C7_OFFLINE_DECISION_2026-10-25.md`。C7政策和对应时序未确认，禁止新轨迹。本文件以下保留原草案/阻断时点，不作为当前运行授权。


Task ID: `AAD-0.5-INTERACTION-DIAGNOSTICS-V1`。Status: **Awaiting Researcher Decision**。
这是阶段性工程事实报告，不是 WP2–WP5 完成报告，不登记正式实验结果。

## 授权与执行状态

研究者于2026-10-25授权剩余3次额度重分配、测量整改、有限动态诊断设计。已记录授权和计划草案；机器协议尚未冻结。新轨迹尝试 **0/3**，没有重试或新基线运行。历史账本和产物保留，未访问第三窗口或 locked holdout。

WP3 的连续边接口已接入状态描述及两个历史 runner，50项相关软件测试通过；两份复用基线的 D1 结果与 WP1 独立向量审计一致。WP3全量历史复核和最终验证尚未完成；WP4、WP5未完成。执行 worker 仅为未验收草案，不应直接调用。

## 冲突 C6：空间坐标与物理净间距

- **Documented Intent:** `stage_0_5_state_support.fcd_to_state_frame` 声明净间距为物理前保险杠距离减去前车物理车长，并引用早期 TraCI 验证。P2 使用该净间距和原生速度产生的闭合速度。
- **Actual Implementation:** `stage_0_5_scene_reconstruction.parse_fcd` 将 SUMO 原生 `pos` 按每段比例映射为 `y_m`。跟驰接口用映射后的 `y_m` 差减去未缩放的物理车长。两者不等价：同一原生车道/路段上，差值为 `(scale-1)*(leader_pos-follower_pos)`。原生速度仍未缩放。
- **Evidence:** 两个复用基线的网络比例相同：main_0=1.0849045691、main_1=0.9042898650、main_2=1.0702929866。在预先固定的180/210/300 s、局部纵向范围、同原生车道/路段相邻车辆中，0750共118对，0805共122对；main_1的“适配器间距−原生位置间距”均值分别−2.6287 m、−2.5353 m，最大绝对差分别17.7676 m、10.8478 m。此抽查不涵盖跨路段前车关系，也没有重算假设修复后的P2事件。
- **Affected Files:** `code/src/riskprop/stage_0_5_scene_reconstruction.py`、`code/src/riskprop/stage_0_5_state_support.py`、依赖其测量表的历史/拟议诊断。`stage_0_5_sumo.py`风险核心公式未改。
- **Conflict:** 空间支持映射坐标混入物理净间距，早期不同调用链的TraCI验证不能直接证明当前适配器等价。连续边统计一致只能证明统计实现，不能证明输入量的物理定义一致。
- **Status: Awaiting Researcher Decision**。未修改坐标、净间距或速度算法；未将旧事件数改写为物理修复后的结果。

## 冲突 C7：草案初始化准入失败

- **Documented Intent:** 草案评价窗elapsed `[120,390)`；120 s时局部域不含初态车辆，不声称正式稳态。
- **Actual Implementation:** 0750复用基线在120 s仍有1辆 `i...` 初态车位于主线1–5、`[150,350)`；0805为0辆。ID1在180 s前没有计划中的供给变化，因此不能据草案假定其初始化准入成立。
- **Evidence:** `docs/audits/stage_0_5_interaction_preflight_v1/preflight.json`。该轮核查同时计算了草案窗内P2，所以后续不得默默调整窗口并声称未查看P2。
- **Affected Files:** 任务计划草案、基线有效性、三次运行对照设计。
- **Conflict:** 当前草案自身准入不通过；尚未机器冻结不等于可以基于已见风险结果选择更有利的窗口。
- **Status: Awaiting Researcher Decision**。不换窗、不放宽准入、不消耗额度。

## 已确认的离线统计（Observation）

仅统计历史模拟表、elapsed `[120,390)`、整体`[150,350)`；不是新的物理风险参考或科学验收。

|条件|P2开始归属 N|D1 E (veh-s)|原点分母 (veh-s)|独立审计|
|---|---:|---:|---:|---|
|0750 B_het seed20261201|7|10904.0|11116.5|N/E一致|
|0805 B_het seed20261201|5|11633.0|11836.6|N/E一致|

真实侧既有147/31051.6、216/33091.1完整参考不变；本阶段尚未完成真实侧新诊断窗/offset100的独立复核。

**Interpretation:** 尚不能据此判断供给或交互机制，且没有新运行的结果可解释。
**Hypothesis:** 暂无新增科学主张。下一步优先解决物理测量与空间支持坐标分离及初始化政策，而不是追加参数搜索。

## 待研究者决定的最小后续工作

建议明确批准一个测量修复子阶段：保留映射`y_m`仅用于共同空间支持，另行建立原生物理前车距离接口并验证跨路段/连接段关系；先复用既有FCD离线复核，任何无法观测的关系降级。该方案不改网络、风险阈值、tau或旧结果，不预设其一定可恢复完整D1资格。预计新轨迹预算0；若必须采集原生前车信息，需要另提交三次额度内的重分配方案，不能自动追加。

同时需研究者决定有限动态初始化政策：保留当前窗但明确允许/分层标注残留初态车，或根据与P2隔离的初始化证据重新提出时间支持。两者目前均为 **Proposed**；后者必须披露旧草案窗P2已被查看，不能作为未接触验证。

## 验证与复现

`python code/scripts/audit_stage_0_5_interaction_preflight.py --output <新的独立目录>`，只读两个授权历史基线；已有目录拒绝覆盖。报告含源文件/输入SHA、Git基线与未提交状态、软件版本。几何抽查限制明确记录。无SUMO启动。

相关测试命令：在code目录执行 `python -m pytest tests/test_stage_0_5_d1_measurement.py tests/test_stage_0_5_state_support.py tests/test_stage_0_5_leader_replay.py tests/test_stage_0_5_trajectory_reconstruction.py -q -p no:cacheprovider --basetemp=tmp/interaction_measurement_03`，50 passed。这不是全量最终验收。首次新增测试因合成fixture缺字段失败，修正fixture后通过；历史测试输出未改写。

Gate仍为 `pending_simulation_sample`；`scientific_claim_eligible=false`、`reality_coverage_accepted=false`、`protocol_lock_allowed=false`、`stage_1_1_allowed=false`。R1–R5除明确的任务级有限授权外仍未决。未提交/推送不完整工作；继续决策后须完成全量测试、文档/便携证据验证和纯Git克隆验证。

补充工程检查：新模块compileall、git diff --check、validate_project_docs.py --strict-git和既有便携证据--verify均通过；新结果未登记。全量pytest、纯Git克隆和提交后require-clean尚未执行，不宣称最终验收通过。
