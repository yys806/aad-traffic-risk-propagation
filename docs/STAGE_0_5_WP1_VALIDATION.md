# Issue #1 工作包1验证记录

基线 `c94e6cccb89349845b8ad905b7f65376a3c2f9c4`，远端main与本地一致、初始工作区干净。完整Issue及评论已读（评论0条）。本任务只做证据审计与既有输出离线复算，科研边界见 [专项报告](STAGE_0_5_WP1_EVIDENCE_AUDIT.md)。

## 离线核验

`python code/scripts/audit_stage_0_5_work_package_1.py --output docs/audits/stage_0_5_wp1_v1`：`WP1_AUDIT_OK real=2 simulation=74 inputs=104`。逐输入SHA记录于provenance，并在计算结束再次核对未变。两真实来源SHA与正式收口provenance一致；独立复现147/31051.6、216/33091.1及全源543/732事件、111425.9/133505.6s暴露；44历史局部事件N和74点E一致。

初次复算因历史grid缺显式leader_incarnation_id停止，无输出目录生成。随后显式标记30份grid为仅观测前车ID资格，重新完成，不伪造缺失字段。第一轮合成边界测试6 passed/1临时目录setup error；建立独立临时父目录后7 passed/1 FutureWarning（pandas object fillna未来行为，测试覆盖该分支）。独立测试临时内容保留于ignored `code/tmp/`。

## 验证资源约束

根工作区仅运行文档和本任务合成测试。全量pytest收集和可运行范围在**不含dataset/历史outputs的纯Git克隆**执行。以下7项会启动SUMO生成新轨迹，且第一项包含四格协议，按本Issue禁止新轨迹/ABCD边界明确deselect；未修改测试、未伪装成通过：

```text
tests/test_stage_0_1_sumo.py::test_real_sumo_stage_0_1_seals_nonempty_four_cell_package_and_read_only_audit
tests/test_stage_0_5_sumo.py::test_sumo_baseline_engineering_run_is_sealed_and_contract_complete
tests/test_stage_0_5_sumo.py::test_sumo_probe_fixture_confirms_a_p2_event_in_both_adapters
tests/test_stage_0_5_sumo.py::test_sumo_run_is_reproducible_for_the_same_seed_and_config
tests/test_stage_0_5_sumo.py::test_sumo_internal_and_recorded_steps_are_separately_configurable
tests/test_stage_0_5_sumo.py::test_sumo_warmup_window_is_respected_and_unbuilt_scenarios_are_refused
tests/test_stage_0_5_sumo.py::test_sumo_smoke_runs_never_change_the_stage_gate
```

全量验证命令是 `python -m pytest -q -rs -p no:cacheprovider --basetemp=tmp/wp1_full_01` 加上述7个精确 `--deselect=`。其余数据依赖项由原skip条件如实跳过；skip/deselect均不是科学验收通过。

## 执行结果

环境：Windows原生Python3.13.5（D:/miniconda/python.exe），pandas2.2.3、numpy2.3.2、PyArrow25.0.1、pytest8.4.1。沙箱不能导入既有用户级PyArrow，经权限流程使用现有依赖执行；没有安装或修改环境。

| 检查 | 实际结果 |
|---|---|
| 根 `validate_project_docs.py --strict-git` | PROJECT_DOCS_OK |
| 根 `export_project_evidence.py --repo-root . --verify` | PORTABLE_EVIDENCE_OK；既有登记结果audit/config/manifest/provenance/SHA均未变，未重导出 |
| 新审计 `--verify` | WP1_CHECKSUM_OK，根absent_local_inputs=0 |
| 根定向文档+审计边界测试 | 20 passed，1 warning，5.83s |
| 纯Git克隆+精确任务文件全量可授权回归 | 958 passed、14 skipped、7 deselected、2 warnings，131.26s |
| 旧判定对账 | grid30+structural4+timing20，共54个已存primary与C5执行重算一致 |
| Markdown链接/表格 | 全部改动Markdown的96个相对链接存在，表格列数一致；早期三份新文档检查17个链接亦通过 |
| `git diff --cached --check` | 通过 |

14个skip中13个因纯克隆缺本地原始/密封输入，1个为既有专用-S胶囊bootstrap测试；不能算科学通过。2个warning分别为既有final_closure测试给int列写1.5，以及本次合成缺前车案例的pandas fillna未来行为；当前断言均通过，没有改生产科研逻辑。

第一次纯克隆审计verify发现原工作区部分.py为LF、部分为CRLF，默认checkout转换导致source SHA不同；这是已定位的字节复现问题。新增 `.gitattributes` 仅对绑定SHA的具体源码规定各自原有换行，对新聚合审计文件禁用文本转换；核心源码内容未改。修正后复核对应入口与编译，最终真正由Git检出的SHA还在提交后独立克隆确认。失败记录保留，不把首轮verify写成通过。

修正后的提交前隔离检出：`PROJECT_DOCS_OK`、`PORTABLE_EVIDENCE_OK`、`WP1_CHECKSUM_OK absent_local_inputs=76`，compileall通过；76个本地输入（2真实+74模拟）在纯克隆不存在，校验只验证可携带产物和源码/摘要，绝不称为重新复算成功。独立核对9个生产源码当前Git blob与HEAD相同。代码/配置/正式决定/旧evidence/AGENTS无暂存变更，21个改动文件均属本Issue。

提交后最终SHA的 `--strict-git --require-clean`、纯Git克隆文档/证据/本次审计/编译及定向测试的实际结果由最终交付报告给出；这里区分提交前验证和提交后证据，不预先声称完成。
