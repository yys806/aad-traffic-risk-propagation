# WSL 隔离能力解阻：实际核验及运行时边界

任务仍为 `AAD-0.5-READY-TO-ADMIT-V3`，本次是研究者明确授权的限范围解阻，基准 `00d19793502ccbd7cb9f1c5c508501c79631d3fb`。长期 AGENTS 规则未改。0 SUMO/netconvert 启动、0真实TraCI、0新轨迹；无安装、权限/所有者/ACL/WSL配置变化，无真实数据或旧结果访问。此前自动审批拒绝保留；本次明确授权后的探针获准执行。

## 实际能力与证据

Ubuntu24.04.3，WSL2 Linux6.6.87.2，uid1000；Landlock ABI3，用户systemd255.4，cgroup v2。非特权user/mount/PID/net/IPC命名空间可用。WSL工作目录固定`/home/shen/AAD`；该目录不是Git checkout，未替换为新的工作树。只创建`code/tmp/v3_isolation_20261026_a`至`e`的新临时子目录，未改动已有工作区文件。早期a–d探针和失败原因保留，最终e的原始证据另行导出，不能以wrapper exit0替代逐项核验。

证据：`docs/audits/stage_0_5_wsl_isolation_v1/probe/record.json`、逐组stdout/stderr、`policies_compact.json`、`provenance.json`。compact政策加record中的共同runtime_files_sha256，可重建六份原始canonical政策并核对每份SHA。没有复制轨迹或受限资源。

`stage_0_5_linux_isolation.py`实现无特权隔离broker：独立systemd瞬态服务/cgroup → 新user/mount/PID/net/IPC/UTS命名空间 → 独占限容tmpfs → 精确输入只读挂载 → Landlock读/执行白名单 →清空capabilities/no_new_privs/seccomp →原生子进程。只保留隔离内loopback，禁止AF_UNIX/AF_VSOCK、命名空间逃逸、文件元数据写及未批准exec。broker只在PID1新命名空间内进行子树清理；直接调用child会在任何mount/signal前拒绝。超时/内存失败的合成标记以独占文件封存。

六组真实无害Linux进程探针，14个证据判据全部成立：

| 范围 | 实际结果 |
|---|---|
| 文件 | 允许输入可读/输出可写；输入写EROFS；合成禁区读写EACCES；元数据写EPERM；symlink创建及未批准exec拒绝 |
| 子进程 | 子进程继承读取拒绝；命名空间与父进程全部不同，CapEff=0、NoNewPrivs=1、Seccomp=2 |
| 网络 | 隔离内loopback可通信；宿主loopback哨兵不可达；外部测试地址ENETUNREACH；AF_UNIX/AF_VSOCK为EPERM |
| 资源 | 8任务上限触发EAGAIN和pids.events；64MiB内存探针触发oom_kill；CPU计数记录节流；1MiB逐文件EFBIG/总tmpfs ENOSPC；2s超时终止 |
| 失败保留 | memory_started/timeout_started在终止后封存，非零退出按预期失败记录 |

14项由`stage_0_5_isolation_admission.py::probe_checks`从逐条观测与内核计数重新计算，不能靠all-true摘要获得通过。`capability_report`还核对证据与当前guard源码SHA。依据：[Landlock](https://docs.kernel.org/userspace-api/landlock.html)、[seccomp](https://docs.kernel.org/userspace-api/seccomp_filter.html)、[systemd资源控制](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html)；以本机内核/用户管理器实际行为为准。Landlock ABI3不提供网络规则，本方案网络边界由net namespace与seccomp承担。

## 集成完成范围与真实阻断

技术预检已读取精确Linux能力证据，并独立报告运行时/控制器不兼容。NativeBackend在未来即使解除构建锁，也在Popen前要求控制器确实位于受限Linux命名空间；禁止直接启动裸宿主原生进程。第八项isolation_acceptance已接入能力证据，但缺少对应真实运行的OS receipt时仍Unknown；前七项测量实现保持原逻辑。

**这不是当前Windows SUMO1.26的隔离验收，生产控制器进入Linux capsule的完整执行接线尚未成立。** 已安装Linux SUMO为`1.18.0+dfsg-3build5`，TraCI常量20；当前提案绑定Windows SUMO1.26及其工具。Windows exe不能用Linux namespace/Landlock隔离，也不能把Windows TraCI直接连接到隔离netns。系统Python3.12缺numpy/pandas/pyarrow/psutil/pytest；现有命名Python替代入口未发现。不能静默换1.18、安装依赖、把Windows环境当Linux环境，或先解锁再补证据。

当前最小可行路径是提供/另行明确授权准备与1.26对应的Linux运行时、工具和必要控制器依赖，再将整个控制器与SUMO置于同一已验证Linux capsule，测量可继续使用已有正式接口。现有Windows方案缺已配置隔离执行器；仅Job/进程监督不能证明文件/网络边界，AppContainer权限配置不在本次授权范围。未安装或修改任何系统组件，也没有开展额外环境迁移。

因此保持`BLOCKED_ENGINEERING`，不报告Ready。原生构建硬锁、execution_allowed/researcher_confirmed/protocol_frozen/accepted_for_new_task均不变。历史隔离事故Not Accepted；Gate、δ/h/B、Stage1.1和科研决策不变。DS38/i0007及矩阵仍为既有Proposed/Unknown，不在本次改动范围。

## 新B00精确包及软件验证

新版本`evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v3/`仅重新绑定首个`V3_0750_B00_DS38_s20261201`：沿用candidate-v2的实际B00网络/routes/sumocfg及其SHA、seed20261201、420s、[120,390)，没有重新生成或修改输入。保留原Windows工具/环境绑定，并明确写入Linux运行时不相容和控制器capsule缺失；不把现有1.18作为替代。旧proposal/manifest/账本/C6数据原样保留，旧SHA不迁移授权。精确SHA以新manifest为准；当前不能确认后直接启动。

本次只运行隔离新增/漂移拒绝测试及相关V3/V2/账本回归、编译、严格文档和证据校验；不重跑1130项。旧全量结果只以明确的source unchanged条件复用，不能写成新代码的全量重跑。精确命令/数字/退出码见本次`validation_record.json`；提交后纯Git复核记录在本机忽略目录，避免改动已绑定包。
