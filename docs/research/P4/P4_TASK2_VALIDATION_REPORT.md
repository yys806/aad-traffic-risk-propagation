# P4 Task2离线验证报告

状态IMPLEMENTATION_COMPLETE_WITH_LIMITATIONS；2026-11-04。验证影响：新增P4适配层及工程契约，未改Formal/P3核心；使用88项P4测试+84项直接相关历史回归及独立数学复算。不执行全仓pytest/compileall，不启动SUMO。

## 1. 最终结果

最终一轮172 passed，0 failed，0 errors，0 skipped。新test_p4_measurement.py为88；原六文件84（Formal7、prelock8、P7 saved evidence7、P3 controller50、P7 revalidation7、StageI5）。实际命令、JUnit/log hash、环境和逐文件数量见[tests.json](../../../evidence/research/P4_TASK2_20261104/tests.json)。进程audit hook阻断任何子进程创建，最终blocked_attempts为空，new_SUMO_processes=0。

覆盖：相同/变化Δv/Δa、角色换ID、无映射/错scope/重复、钟/共同时间、缺帧、lane/leader、incarnation/退出/末端、可靠性；名单重复/缺/额外/同N错人/处理后/无来源/规则；TTC NaN/Inf/非正、native none与unobserved区别、独立空间质量、整车/首尾/中间缺失、显式连续性；固定N/同窗域/上下界、hash/FK/来源字节、多对多native与实际P7链。

## 2. 首次失败如实保留

p4_tests_01：79 passed /1 failed，P3 source_event_id在context，新增索引错误地仅从data取；修正索引所有权。p4_tests_02：79 passed /1 failed，测试fixture从可空command.source_event_id取事件，实际消费receipt有源事件；改为沿显式decision→receipt取得，未放宽事件校验。完整初始日志/JUnit在code/outputs/audits/p4_task2_20261104/，其hash写入便携tests.json。

中间acceptance_01为164通过（80新+84旧）。补充8项QC/字节/错误scope边界后，acceptance_02为172通过（17.22s）；保留source_derivation_version元数据后，最终acceptance_03仍172通过（17.16s）。不把多轮测试数量相加宣称独立样本，不将失败隐藏为首次通过。开发早期传输语法错误未执行命令/实验；无新增交通运行。

## 3. 独立数学复算

全部样例SYNTHETIC_VALIDATION_ONLY：L=3s，3成员；仅软件时域，不是科研窗口/采样参数。用既有τ与TTC=τln2、τln4生成rho=.5/.25，原Formal公式不变。

|成员|真实观测支持|J下界|J上界|均值下界|均值上界|
|---|---|---|---|---|---|
|m1|0,1,2,3连续、rho=.5|3/2|3/2|1/2|1/2|
|m2|0,1,3，仅0→1连续、rho=.25|1/4|9/4|1/12|3/4|
|m3|全缺失|0|3|0|1|

Y下界=(1/2+1/12+0)/3=7/36；Y上界=(1/2+3/4+1)/3=3/4。完整点案例三车全窗rho=.5/.25/.5，Y=5/12。完整资格声明不成立案例输出UNKNOWN_SCOPE和null Y；同N=3但错误member被EXTRA_OR_WRONG_MEMBER拒绝。

verify_p4_mathematical_examples.py使用标准库Fraction手算，不导入riskprop、不调用被测函数；15项断言通过。样例输入/输出、source bytes和math结果均在便携包，可独立运行复算。

## 4. 数据及保护检查

无新SUMO、seed、Pilot、V、holdout读取；现有P7只验证实际证据，未伪造完整名单。原Formal/config/P3/历史证据/Task1交付受554文件字节保护；四个定义文件append-only prefix检查、v0.4/27项数量保持。实际保护统计、source hashes、文档strict-git、exporter、Git索引字节检查见证据；失败则不提交。

封包第一轮发现4处既有CRLF/LF视图差异，未改写历史代码/config；source_manifest分别绑定工作区和Git blob SHA，并独立验证两种字节视图。工作区554保护文件与四定义原前缀均保持；Git前缀按基线原blob另验。首次封包未生成完整SHA清单即停止，错误日志留档；不作为测试或交通实验失败。

旧Task1 source_manifest绑定的是本任务前字节。四份定义授权追加后，用基线58c7e68861b283d7f31e7bafb860cea03dc2e76d复核旧快照；不重写旧manifest使其伪装成当前树绑定。

## 5. 未覆盖与限制

未验证真实完整区域Y、正式几何/窗、科学动作onset、现实风险可观测性；没有P5/P6因果/功效估计。来源哈希不自动证明名单语义完整；非零钟误差时不作精确配对；无leader整段可能保守Unknown。v1只处理契约合格输入，不自动从任意数据集推断身份/区域/完整总体。通过离线测试不等于科学假设成立。
