# C6/C7离线阶段验证记录

本阶段完成的是授权测量修复与离线决策材料；C7政策与三次运行草案待研究者确认，WP2–WP5整体未完成。新轨迹预算0、实际0。

## 已执行

|检查|结果及覆盖范围|
|---|---|
|物理坐标/跟驰/D1/场景相关测试|40 passed；新增D1原生车道中断测试后的定向检查20 passed|
|两份旧FCD离线重测|新目录保存完整修复状态、逐状态TTC和事件成员对照；历史10份输入SHA不变|
|独立验证器|通过原生物理净间距、完整事件成员和原始产物SHA核验|
|运行源码绑定|provenance的5份源码SHA与运行后文件一致；记录基线SHA及未提交状态，不把单独Git SHA冒充完整复现版本|
|初始化身份|0750/0805的i前缀车辆分别117/131辆，routes中全部depart=0，其他车辆没有depart=0；C7函数不读取风险字段|
|纯Git克隆+精确任务文件全量可授权回归|978 passed、14 skipped、7 deselected、2 warnings；139.24s|
|文档严格检查|PROJECT_DOCS_OK；初次检查发现索引反向登记/未暂存问题，修正登记并暂存后通过|
|便携证据校验|PORTABLE_EVIDENCE_OK，新增包SHA与本机聚合来源一致|
|compileall / diff check|code/src、code/scripts、code/tests通过；无空白错误|
|边界保护|注册表current/Gate与基线一致；AGENTS与formal_risk_measurement.py未改|

纯Git克隆路径为 `code/tmp/c6_c7_git_validation`，来自main，覆盖精确任务文件；没有复制dataset或历史outputs。全量命令：在该克隆code目录运行 `python -m pytest -q -rs -p no:cacheprovider --basetemp=tmp/c6_full_01`，附加 `docs/STAGE_0_5_WP1_VALIDATION.md` 列出的七个精确 `--deselect=`。七项均会生成SUMO轨迹，其中含四格运行，因此按本轮零轨迹边界不执行；不算通过。14项按原测试条件缺本地数据/胶囊条件跳过，没有读取验证资源。两条warning来自既有pandas dtype兼容性测试，未修改历史测试来消除警告。

## 证据复核命令

- `python code/scripts/review_stage_0_5_c6_c7_offline.py --output <新目录>`
- `python code/scripts/verify_stage_0_5_c6_c7_offline.py --root <该目录> --report <新报告路径>`
- `python code/scripts/export_project_evidence.py --repo-root . --verify`
- `python code/scripts/validate_project_docs.py --strict-git`

前两项需要本机两份授权FCD，纯Git不能重放，不能用便携SHA校验冒充原始数据复算。新结果`raw_artifact_SHA256SUMS.txt`绑定本机产物；便携`SHA256SUMS`绑定包内文件。

提交后需再执行 `validate_project_docs.py --strict-git --require-clean`，并对该提交建立无数据纯Git克隆，核验入口、便携SHA、文档测试和源码SHA。提交后结果在最终执行汇报中给出；不预写为通过。
