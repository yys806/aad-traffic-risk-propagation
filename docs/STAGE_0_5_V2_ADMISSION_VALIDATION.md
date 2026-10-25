# V2准入工程验证记录（2026-10-25）

结果 `RES-STAGE-0.5-V2-ADMISSION-ENGINEERING-V1`；精确命令/环境/测试和审计摘要以便携 `validation_record.json` 为机器依据。软件测试不构成原生执行或隔离验收。

## 安全选择与环境

主工作区没有运行pytest。独立验证克隆位于 `code/tmp/v2_admission_engineering_validate_v1_20261025`，源为5899465纯Git克隆，只叠加明确本轮代码/文档/便携证据，不复制dataset或历史FCD/正式输出。运行前检查 `validate_stage_0_5_research_v2.py` 与测试选择：7个真实SUMO测试按具体node名称排除；无需调用SUMO确认安装。新wrapper仅替换定向列表，不改既有验证器绑定源。禁用自动插件、排除ambient editable项目/插件路径、重定向TMP和MPLCONFIGDIR，检查Python父进程路径/子进程审计。允许的字体等运行时读取不扩展到私人目录。

命令（在独立clone根执行；`--source-workspace`仅供拒绝读取源工作区）：

```powershell
python -B code/scripts/validate_stage_0_5_v2_admission.py --source-workspace D:/shen/TJU/AAD
python -B code/scripts/validate_stage_0_5_v2_admission.py --source-workspace D:/shen/TJU/AAD --full
python -B -m compileall -q code/src code/scripts code/tests
python -B code/scripts/validate_project_docs.py --strict-git
python -B code/scripts/export_project_evidence.py --repo-root . --verify
python -B code/scripts/export_stage_0_5_v2_admission_evidence.py --repo-root . --verify
```

真实symlink创建测试若无权限为明确skip；模拟越界/穿越/白名单拒绝仍运行。未因skip标记原生隔离通过。最终测试数量及阶段记录见机器记录；更新前的105通过与113通过/1跳过仅对应当时工程源码，不能替代最终版。

最终源码：定向 **116 passed / 1 skipped**（17.12 s，exit0）；全量软件 **1083 passed / 15 skipped / 7 deselected**（174.02 s，exit0）。33个新增合成测试函数通过参数化覆盖53个通过案例及1个symlink skip。全量另14个skip为既有本地/可选资源或独立capsule验证条件；2个pandas FutureWarning来自既有测试，未修改科学算法处理它们。两轮最终父进程审计均0拒绝、0 SUMO；全量43个预期软件子进程，定向7个。compileall、strict docs、全便携与新增来源一致性检查均exit0。

审计中的子进程不是全部为0：既有测试包含Git状态/临时Git仓库、Python CLI的help/合成输入、人工生成artifact/contract fixture及资源故障worker。逐项核对其命令和入口，没有SUMO/TraCI启动；两项stage0.1的artifact/contract fixture是软件人工数据入口。Python父审计不自动继承到所有子进程，因此该证据仍不认证原生完整访问隔离。

## 离线命令及失败保留

在主工作区仅执行限定历史离线测量/静态审计，无pytest或SUMO：

```powershell
python -B code/scripts/review_stage_0_5_c6_admission_v1.py measure --repo-root . --allowlist code/outputs/formal/calibration/stage_0_5_v2_admission_engineering_v1/inputs/history_allowlist_v2.json --output code/outputs/formal/calibration/stage_0_5_v2_admission_engineering_v1/measurements_v2
python -B code/scripts/verify_stage_0_5_c6_admission_v1.py --repo-root . --allowlist code/outputs/formal/calibration/stage_0_5_v2_admission_engineering_v1/inputs/history_allowlist_v2.json --measurements code/outputs/formal/calibration/stage_0_5_v2_admission_engineering_v1/measurements_v2 --output code/outputs/formal/calibration/stage_0_5_v2_admission_engineering_v1/independent_verification_v1
```

六项测量与六项独立复核均成功，原科学源码未改。第一次离线prepare因校验器错误拒绝、measurements_v1因既有pyarrow导入权限失败均保留，另建版本完成；初版测量CLI虽返回0，内部六项明确failed，最终脚本已改为任一失败exit1，不能用旧exit0当测量成功。实际执行wrapper源快照留在local输出，最终wrapper增加输出命名空间拒绝与更明确Python打开记录，未重跑已有效测量来凑次数。

## 证据、历史与准入

新增限定导出只增加本结果。全部旧manifest结果对象、DS候选绑定源码/原输入/候选输入和历史预算引用按哈希复核，均保留；不运行主工作区全量历史export以避免重读无关结果源。全部portable一致性校验在无数据clone执行（本地源不存在时按既有验证语义核对便携SHA）；新结果在主工作区额外核对来源hash。

提交后必须再做干净状态strict docs及纯Git克隆定向/编译/便携核验，记录commit及结果。该提交后记录为本地独立文件，避免将自身commit写入其被绑定的提交内容。原生执行、OS级文件访问、动态输入保真、实际干预与车辆插入仍未验证，accepted_for_new_task保持false。
