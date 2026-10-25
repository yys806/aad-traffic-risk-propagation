# V2 工程验证记录

当前任务：AAD-0.5-INTERACTION-RESEARCH-V2，0次新轨迹；不是科学实验验收。

只在无dataset/历史正式输出的独立Git克隆执行软件测试。`code/scripts/validate_stage_0_5_research_v2.py`显式拒绝主工作区，记录Python文件/进程审计，排除7项会生成SUMO轨迹的集成测试。编译及文档/便携检查不能代替原生运行隔离证明。POLICY-A-VALIDATION-SCOPE-01保持Not Accepted。

## 已完成的软件验证

基线7414688的独立Git克隆叠加明确任务文件，不复制dataset/本机正式输出。全量在`code/tmp/interaction_research_v2_validation_20261025`运行，主工作区未运行pytest。

|检查|结果|覆盖边界|
|---|---|---|
|定向软件测试（首个有效版本）|57 passed，11.53s；审计0拒绝/0 SUMO启动|账本、任务白名单、D1、文档；后增3项由最终全量覆盖|
|最终全量软件回归|1030 passed /14 skipped /7 deselected /2 warnings，152.70s，exit0|排除7项SUMO轨迹集成测试，14项缺本机数据skip不计通过|
|最终全量Python审计|0拒绝、0 SUMO启动；父进程43项子进程调用记录|不传播为任意原生子进程全范围审计，不证明原生SUMO隔离|
|compileall|code/src、code/scripts、code/tests通过|仅语法编译|
|历史保护|旧DS提案绑定的22项源码/计划全部匹配，历史预算引用匹配，已有manifest条目未改|旧一次failed_stop保留，新账本实际0次|

最终全量审计SHA256：`9c51257043c23eaa092b2b4c5ff85410fb95454fd77c2ca47490517809b5facb`。原始审计及测试临时材料只保留本机克隆内；便携只导出聚合和哈希。两个warning是既有pandas dtype/downcasting FutureWarning，未修改相关科研源码。

## 预检失败与修正保留

- 首次严格文档检查因新文件尚未暂存及结果索引标题含日期前缀失败，修正标题并完成明确路径暂存后通过；沙箱最初拒绝Git写入，使用用户已授权工程操作的权限执行。
- 初次限定导出拒绝JSONL扩展名，改为便携JSON账本快照；活跃JSONL事件账本仍独立保留，没有修改旧导出器。
- 首次测试入口将Windows NUL设备当成越界，pytest初始化失败；仅修正精确设备识别。
- 一次57项断言通过但隔离审计拒绝外部editable项目元数据及系统临时写入，**不计有效隔离验证**。关闭插件自动加载、过滤sys.path、将临时文件放入克隆后，取得上述有效定向结果。
- 一次1027 passed /14 skipped /7 deselected，但审计224项字体/用户字体缓存访问被拒绝，**不计有效隔离验证**。缓存迁入克隆，仅增加精确运行时字体目录读取后，最终全量1030项通过且无拒绝。

这些拒绝不是获准读取了项目外科研数据；不扩大其效力为OS级零访问证明。早期和最终审计/测试材料保留本机；不把失败覆盖成成功。

## 收口检查

主工作区仅运行V2限定导出/核验和严格文档校验；全量便携证据核验在无数据Git克隆执行，避免无范围回读本机历史源。提交后`--strict-git --require-clean`及新纯Git入口复核另记本机`code/outputs/formal/calibration/stage_0_5_interaction_research_v2/postcommit_verification.json`，不预先用本文件断言未来提交成功。

机器聚合位于`evidence/results/RES-STAGE-0.5-INTERACTION-RESEARCH-V2/validation_record.json`。本轮无SUMO新轨迹，科学计划未确认，POLICY-A-VALIDATION-SCOPE-01仍Not Accepted、Gate不变。
