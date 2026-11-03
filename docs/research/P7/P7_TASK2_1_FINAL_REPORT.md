# P7 Task2.1 — v2 单次 SUMO 复验与工程验收收口

Task ID：AAD-P7-TASK2.1-20261103；2026-11-03。

**ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS**。下述真实运行与离线证据检查支持本确定性合成场景的工程验收，不证明科研假设。

## 1. 目标与边界

完成唯一一次Enabled v2/v1.1真实SUMO复验，复用既有No Message/Disabled，不增加种子、参数搜索或第二次仿真。消息→策略→命令→实际动作链可追溯；不是Adoption因果识别、Formal P2资格或区域风险效应证明。

## 2. v1历史失败

Task2 Enabled v1在2.80 s异常制动9.00 m/s²（wished4.50），原摘要误报PASS，派生验收BLOCKED_ABNORMAL_BRAKING。原源码、配置、轨迹、日志、Task2报告和便携包保持原字节；本次结果只形成后续版本化接受记录，不把旧失败改成通过。

## 3. v2策略和工程修正

message_driven_longitudinal_controller.py与v2配置从任务开始至运行未修改：目标参考=max(desired,current_speed−1.0×0.1)，并保留原速度上限。LOW/MEDIUM/HIGH映射0.9/0.7/0.5、headway1.0不变。该式约束参考值，不硬约束实际加速度，不是Safety Layer。参数仍ENGINEERING_CANDIDATE_NOT_FORMAL。配置source中的NOT_EXECUTED是创建时说明，运行事实以本报告/provenance为准，不改已运行配置字节。

本次只补充独立run_id、显式端口单次启动、逐步碰撞/teleport/emergency stopping诊断、双日志warning检查及1e−9 m/s²浮点容差。固定port使SUMO1.26.0 TraCI.start在连接失败时退出外层进程启动循环；允许同一进程socket连接重试，不允许再起进程。启动前独占写入launch_consumed.json，无论成功失败额度均消耗。历史调用者可省略run_id；旧Stage执行路径不改。

## 4. 前置检查与影响判断

开始HEAD=2a6c388ff69e61840fc32ed5d058b343b3fd1519，main，已有76个Task2暂存文件，保存其hash与task_start_sources。改动涉及P7执行管理、身份、诊断和离线验收脚本，不改变策略、消息gate、P3 schema、P4测量或Formal算法。定向测试覆盖运行守卫和原接口；不运行全仓pytest/compileall。

v2与三份v1 config仅版本/source/新增reference_deceleration不同，交通、seed、步长、初始化和风险映射相同。逐一复核两基准各351份snapshot均messages=[]，以v2重新调用纯策略仍NATIVE_FOLLOWING/无目标参考，因此直接复用。SUMO二进制和全部TraCI binding hash与Task2相同。Windows/Python及numpy/pandas版本见provenance；启动前磁盘约202.29 GB可用，工程输出预计50 MB。

## 5. 唯一运行

run_id=p7-task2.1-enabled-v2-20261103；assignment=AAD-P7-TASK2.1-ENABLED-V2-20261103；来源=researcher-authorized-single-revalidation-AAD-P7-TASK2.1-20261103。Mode=ENABLED且整run固定。SUMO1.26.0、seed20261103、dt0.1 s；合成HIGH消息生成2.0 s，有效[2.0,8.0)。新增SUMO启动1次，No Message/Disabled重跑0，其他新SUMO=0。

完整命令/时戳：[启动调用](../../../evidence/research/P7_TASK2_1_20261103/one_launch_invocation.json)、[额度回执](../../../evidence/research/P7_TASK2_1_20261103/launch_consumed.json)。原始目录：code/outputs/engineering/p7_task2_20261103_v2_revalidation/enabled_v2。returncode=0、status=PASS，目标step3进入、step354退出。

## 6. 异常制动和交通安全

全部354个simulationStep保存原生collision/teleport/emergency getter结果。最大实际减速度0.9999999999999964 m/s²，未超过native_decel4.5；仅允许1e−9浮点误差。异常减速度样本0、emergency braking warning0、emergency stopping0、碰撞0、teleport0。双日志hash与实际轨迹检查见[anomaly_checks.json](../../../evidence/research/P7_TASK2_1_20261103/anomaly_checks.json)。这些检查独立于摘要PASS和API成功。

## 7. 消息消费和Adoption

合成Payload SHA256=35c8d92b45637c2ba3c682da5b02f4df0d24347f1c2edecc9b68985d1a120acd，与Disabled/v1相同。Source/Message/Send/Delivery各1，Validation/Input/Consumption各334；52条POLICY_INPUT_INCLUDED均使用Agreed v1，关联具体decision及input snapshot hash。2.0 s收到消息不等于可用；目标进入适用edge后2.8 s开始实际纳入。不根据动作反推Adoption。

## 8. 命令、实际执行与原生跟驰

351决策，39个真实setMaxSpeed命令（含1恢复），326执行readback，352 Action Observation（351在场+1退出）。所有命令ACK、getter等于参考值，command/decision/执行/动作显式关联通过。无setSpeed/setAcceleration或轨迹写回。原生Krauss/speedMode31保留，285个前车约束下低于单车上限样本；actual speed与getSpeedWithoutTraCI最大差0。实际位置/v/a/road/lane/leader/gap逐步读回；前车不在场用合法None，不补零。

## 9. 实际动作变化

两基准均有351个共同在场时刻；网络/route XML语义、初始化、原生参数、seed/步长一致。消息前及2.8 s第一次命令当步的实际轨迹一致，首个速度和加速度差异均在2.9 s post-step出现。

| 对比量 | Enabled v2 vs No Message（vs Disabled相同） |
|---|---:|
| 最大速度绝对差 | 2.649473720 m/s |
| 最大加速度绝对差 | 2.719870887 m/s² |
| 速度不同样本 | 325；2.9–35.3 s |
| 加速度不同样本 | 312；2.9–34.0 s |
| 速度首末跨度/样本支持时长 | 32.4 s / 32.5 s |
| 加速度首末跨度/样本支持时长 | 31.1 s / 31.2 s |

使用全部共同观测时刻，数值误差比较1e−9；时长分别为首末采样差及样本数×dt，不插值、不冻结正式动作窗口/阈值。状态ACTION_RESPONSE_OBSERVED_ENGINEERING_ONLY，只是本场景描述比较，不是Adoption-induced Action Effect。完整结果见[comparison.json](../../../evidence/research/P7_TASK2_1_20261103/comparison.json)。

## 10. 过期与恢复

8.0 s验证EXPIRED，消息不再进入策略输入，产生RESTORE_NATIVE_MAX_SPEED=20 m/s，API返回getter一致，8.1 s起实际readback上限为20。8.0 s及之后采用回执0、274次策略输入为空。

恢复原生控制不等于瞬间回到另一条轨迹：过期后共同样本最大速度差2.443522282 m/s，末在场样本35.3 s残余差0.002836795 m/s。这是实际交通状态差异，不是继续采用过期消息的证据。

## 11. P3/P4及Unknown

完整图VALID_WITH_UNKNOWNS。Message→Consumption→Decision→Command→Execution及Action引用、run/incarnation/phase、Payload/snapshot hash和外部原始字节检查通过。Source1、Message1、Send1、Delivery1、Validation334、Controller1、Input334、Consumption334、Decision351、Command39、Execution326、Action352、Risk1。Safety0是D6决定，不伪造producer。

具体Unknown类型和数量见[validation.json](../../../evidence/research/P7_TASK2_1_20261103/validation.json)的unknown_issue_counts，完整图/audit可复核。来源资格Unknown；风险只引用现有per-state TTC/quality adapter，不重算Formal rho/P2。正式Region/Cohort/Window未冻结，risk effect Unknown。14类按适用性处理，缺独立Safety不是程序漏记。

UNKNOWN_SOURCE_QUALIFICATION=1对应合成源；UNKNOWN_SAFETY=326对应D6不设置独立安全生产者，原生约束另有实际检查。MISSING_STATE_READBACK=1与UNKNOWN_EXECUTION=1均指同一35.4 s/step354的VEHICLE_EXITED记录：退出事实和readbacks/354.json存在，运动量按契约为null，不虚构退出后的v/a。全部351份在场状态完整；这些不是未解释的结构错误。未修改P3通用Unknown语义。

## 12. 测试和验证记录

首次108 passed/42 setup errors，全部为系统pytest临时目录权限，包含未被Windows路径式deselect正确排除的7项；42项未进入测试体，没有启动SUMO。原XML/log保留。一次有限环境修正：独立basetemp、名称式排除7项、离线subprocess启动守卫。最终143 passed/7 deselected/0 failed/0 errors（17.57 s），覆盖v2配置/单调/下降约束/gate/过期/命令与执行/P3/P4及显式端口单次启动。7项不计通过，没有为测试追加仿真。

完整P3图、外部字节、351点实际轨迹比较和便携验证由只读finalize_p7_task2_1.py/verify_evidence.py执行。文档strict、evidence exporter/verify、定向语法和Git字节检查见project_checks.json及本机封口后日志；不运行全仓测试。

## 13. 失败、限制与保存

v1异常、原误报PASS、首次测试权限错误与修正记录保留。参数未因复验通过升级为正式参数。console保留SUMO_HOME未正确配置导致关闭XML schema validation的环境warning；SUMO实际读取网络/route并完成运行，网络语义独立核验，无emergency warning。本任务不为消除环境warning追加运行或修改环境。

完整原始输出/轨迹/CSV/log在本机独立目录。便携包保存完整P3 sidecar/audit、全部39条命令原始字节、选定Payload/snapshot/readback样本、源码/版本/环境/hash和摘要，不复制大型原始表或日志。Task2历史verifier的current-source绑定指向当时字节，后续代码演化应使用本次保留的task_start_sources复核，不把源码演化解释为历史证据被覆盖。

Git字节复核确认既有formal_risk_measurement.py的工作区运行字节与Git blob存在CRLF/LF差异；该源码和其既有属性均未修改。新source_manifest显式分别记录运行字节与Git字节SHA，保存运行原字节；验证器只在两个SHA均已登记且规范化CRLF/LF后完全相等时接受该已知视图差异，不放宽其他内容或hash检查，不扩展为历史换行清理。

## 14. 最终工程状态和Git

当前P7/Task2工程接受状态由本次更新为ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS；Task2 v1原运行/报告/证据仍是历史失败状态。Task2和Task2.1作为一个逻辑完整交付提交并推送origin/main，核对HEAD。具体执行结果和SHA以实际Git及最终回复为准，报告不内嵌自身提交SHA。

## 15. 科研状态与后续

仅合成工程消息、进程内单跳，不代表真实无线链路；参数工程候选，不证明正式消息资格、Adoption因果效应或区域风险效应。Formal A=0、独立Qualified=0、F0/总体TR–TP Unknown；统一定义v0.4/27项、四格/P1 ITT、Formal算法/config、科研Gate/Protocol Lock不变；Stage1.1 NOT_AUTHORIZED。无Pilot、Independent V、holdout或论文修改。

P7基础工程接口收口，不围绕同一异常无限追加前置实验。下一研究重点为P5资格总体、稳定assignment、完整ITT与采用—动作—风险识别，结合P4/P6及必要P8，须研究者独立决策和授权；本任务不启动后续。Context Consistency Check同步00–08及机器/人类索引，定义目录只链接不修改。
