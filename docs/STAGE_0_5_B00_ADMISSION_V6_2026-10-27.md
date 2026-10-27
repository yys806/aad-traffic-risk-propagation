# AAD-0.5-B00-ADMISSION-V6 — 工程准入与审批边界

日期：2026-10-27（Asia/Shanghai）。任务类型：工程证据整合，非科研执行。

## 结果

candidate-v6 为 **READY_FOR_RESEARCHER_APPROVAL**：technical_errors=[]、ready=true。工程验收证书 Pass，研究者尚未批准精确 proposal。科研三个批准标志与 profile.accepted_for_new_task 均 false，native_launch_locked=true；原 research policy 的 accepted_build=false 保留。此硬锁不构成已经解锁或已经获得执行权限。

本任务没有调用 launch、execute_research、_execute_authorized、netconvert 或真实 TraCI；SUMO 新进程0、真实TraCI连接0、B00新科研轨迹0，无账本预约或状态推进。

## 当前版本与来源

开始时本地 main/HEAD 与实际 git fetch origin main 结果均为 735bab02431f3b4c24466ff12df1d87e8c0cd624，工作区干净；目标candidate-v6不存在。原candidate-v5的proposal SHA=e4b4dcf9e559b56be0ac50c143e3e327c336927f02d9c90c63f5c0463e93442f，技术错误仍为integration_not_accepted，未改写。

独立工具：code/scripts/prepare_stage_0_5_b00_admission_v6.py。它属于另行哈希的工程辅助代码，不加入或改变已有38源科学/生产闭包，也不修改技术预检拒绝逻辑。此前code/tmp的候选组装草稿仅为未使用中间状态，不是正式证书或准入候选。

## 证据复核

逐文件重算任务指定的proposal、false envelope、实际授权envelope、runtime、result、原协调器验收、独立验收、controller/isolation回执哈希。重算prepared-r5、authorized-execution及continuation-r2的SHA256SUMS、manifest与collection全部现存文件，共347个唯一绑定文件。原始失败及其SHA256SUMS保留。不是根据result的SMOKE PASS标签判定。

使用当前stage_0_5_native_capsule_v4.verify_receipt对既有封存archive重建验收，结果与independent_receipt_acceptance.json完全相同，且为原engineering_acceptance.json的完整基础字段子集。独立核对60步/时钟/10→5→10回读、XML输出和哈希、SUMO1.26.0/TraCI22、namespace/security/cgroup、66资源采样及峰值RSS100130816字节和清理记录。全部使用历史文件，没有重新执行SMOKE。

SMOKE和B00的12源映射完全相同，闭包SHA=b1598d279e2665c1c902bae827022440a34f668377fc0544b30fbcf84f8015c2；runtime manifest SHA=3afa1fdb8eac97acf875d1a816eac168bfd39d3318414e316c85b4136d0a4abc。

## B00自身的输入与策略范围

独立重算原B00 input/source/support/measurement-reference/plan/budget/software-validation哈希，并使用现有validate_config、factor_routes与静态audit_bundle检查。真实资格对象仍是原B00候选输入：1150辆、117初始车辆、原DS38政策、seed20261201、420s/0.05s/FCD0.1s、[120,390)与18个参考单元；完整run对象与candidate-v5深度相等。没有把合成SMOKE输入当作科研输入。

B00 research_policy SHA=e7152b8ff703f23ed051ecc0fe9afae7b2b1190221338a79fddd822c08a54bf1。比较runtime依赖闭包、12源只读目录、exact executable allowlist、环境、kernel read scope、32进程上限与隔离守卫。SMOKE/B00有意不同的输入和capsule路径、预算分别使用各自原绑定；B00仍wall600s/RSS3GiB/output2GiB/poll0.5s，无自动重试，worker1。输入、输出路径范围及输出尚不存在均验证。

input_and_test_resource_scope_accepted仅表示原B00输入文件、静态契约、只读策略和现有资源满足工程准入。实际插入、i0007动态情况、DS38科研政策合理性、测量支持、交互相容和科学主效应仍未验证/待研究者决定。历史POLICY-A-VALIDATION-SCOPE-01=Not Accepted不变。

## 实时Linux检查

先对原B00 proposal执行既有Linux driver preflight，后对新proposal精确字节执行同一preflight，再调用未修改的technical_preflight_v4(inspect_runtime=True)。检查8031运行时文件、实际输入和策略，资源满足C>=5GiB/D>=14GiB/memory>=4GiB以及WSL和archive输出预算+1GiB余量。

实时读取Ubuntu24.04.3、kernel6.6.87.2-microsoft-standard-WSL2并与原绑定比较；Landlock ABI3、seccomp actions、cgroupv2 cpu/memory/pids、systemd user manager实际查询均通过。当前只读接口检查和历史六模式强制隔离回执分开，不把历史探针冒充本轮新探针。没有安装依赖、修改安全配置或清理数据。WSL stderr的localhost代理提示保留原字节，不影响exit0和技术校验。

静态technical_preflight_v4(inspect_runtime=False)按原实现保留唯一live_Linux_runtime_and_resource_check_required，不伪称静态阶段已检查实时环境。完整实时预检才是ready=true。authorization_pending保留10个精确人工授权及科研政策确认项，不将其作为工程错误或自动清空。

## 新包与哈希

- proposal：evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/proposal.json
  SHA-256：b43e2d3af03dd53dd23bee3abd027725f298f58c97a2ae73d868ca9168a229b3
- manifest：evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/manifest.json
  SHA-256：afddd83c77e1f7b9eaf64c3b5059f9d29f740b9bf003ed36d22325c93eee4978
- 工程证书：evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/integration_acceptance.json
  SHA-256：342ed54cccedcaf0d477ec72b70b98e956140179961dec2d59904d4648a71528
- 最终完整预检：evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/technical_preflight.json
- 结构化深度差异：evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/scientific_diff.json
- 工程审计：docs/audits/stage_0_5_ready_to_admit_v3/candidate-v6/

manifest覆盖全部其它正式候选文件；manifest自身SHA由外部审计清单绑定，避免自引用。证书不包含candidate-v6 proposal自身最终SHA。所有新证书仓库路径为拒绝绝对路径、穿越和符号链接的安全相对路径。proposal必须包含的原Linux环境绝对路径保留，唯一新proposal位置通过/mnt/d指向同一正式文件，未覆盖r5的research_proposal.json。

## 验证与提交

新增工具初次定向测试34 passed/1 skipped（Windows无symlink权限的正向创建测试；拒绝路径测试实际通过），exit0。最终新增工具定向34 passed/1 skipped；V4及隔离相关定向288 passed/1 skipped；全量1331 passed/16 skipped/7原生测试排除；文档单测13 passed。以上命令及compileall、strict-git文档、候选验证、export、export --verify全部exit0，实际命令和stdout/stderr哈希见本审计validation_record.json。完整软件测试在无dataset/无科研输出的独立Git检出中执行，明确排除7项原生测试，skip不计pass。

提交前的源码字节校验与最终提交后全新纯Git校验分别登记；本报告不把预提交测试充作提交后结果。最终commit/push及提交后独立校验结果由外部postcommit审计/最终回复记录，避免自引用提交SHA。

补充原路线字节对照再次确认仅原numeric10的38辆改为max，其他79辆初态/1033非初态及i0007原属性完全不变，candidate-v5自身manifest也逐文件核验；见supplemental_DS38_static_verification.json。正式schema报告列出仅新增两个工程证书链接字段、未删除字段，run和全部科研映射深度相等。

16项skip明细已单独复核：13项需要封存本地数据/CSV/PDF，2项Windows符号链接权限不可用，1项bootstrap由专用-S capsule检查覆盖；均未计为pass，明细见validation/skip_reasons.json。原生7项被固定排除，未启动。

通用exporter已知未包含三个既有扩展的总目录条目；按要求实际运行export并保存其生成版和原目录哈希，仅恢复该命令自身改动的总目录字节，以保留历史扩展。随后export --verify通过；本任务没有修改任何历史结果，通用exporter缺口未在本任务扩大修复。

## Context Consistency Check

已更新00当前状态、05工程验证记录、07待解决事项、08变更记录和正式registry/research status/index。01研究背景、02架构、03数据流、04模块图、06科研决策没有变化，无需机械修改。科研Gate、δ/h/B、Stage1.1、初始化定义、测量契约、输入保真定义和所有历史记录保持原字节或原语义。最终交付只表示工程准备好交给研究者审批。
