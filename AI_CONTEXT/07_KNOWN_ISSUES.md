# AAD Known Issues

## 已确认问题

### KI-01 — 阶段 0.2 尚未收口

v2 便携 audit 能证明 NGSIM 生成有效跟驰测量与风险事件，但异常记录、极端值来源、最终分布和适用边界尚未完成。旧 audit 的 `pending_pneuma_and_blind_reaudit` 是迁移前原始字节；当前代码已改为 `active_audit_closure`，需要新 run 才会产生新证据。

Evidence：`evidence/results/RES-STAGE-0.2-NGSIM-V2/audit.json`、`code/src/riskprop/ngsim_risk_calibration.py`、阶段 0.2 执行记录。

### KI-02 — 阶段 0.3 正式产物已生成，科学参数未冻结

**已解决（2026-10-16）**：研究者经任务 AAD-0.3.3 批准适用范围、连续性参数（0<Δt≤0.043 s）、极端观测处理、描述阈值与 Gate=pass，阶段 0.3 已关闭（`RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3`）。遗留但归属清晰：独立物理真实性永久 `Unverified`；车型→SUMO vType 映射、时间权重抽样与覆盖阈值属 Stage 0.5 独立待决。

### KI-03 — packet 级通信证据不可用

官方 Packet 下载端点历史 403；2026-10-16（AAD-0.4.1，日期勘误 2026-10-17）重验为 302→官方文件 API；同日（AAD-0.4.2）Range/ZIP64 在新 blob 重验可用并获取 `RSE_BSM`（`RES-STAGE-0.4-RSE-BSM-V1`）。2026-10-17（AAD-0.4.3）官方文档裁定：RxDevice≡车辆设备 ID、Gentime=生成时间（µs，1609.2）；**车辆侧接收时间在 SPMD 全家族不存在→V2V 端到端时延不可算**（结构性缺失，非下载可解）；RSE_BSM 无绝对时间与信道条件，配对 Ambiguous；其采样设计（≤2 记录方/发送方 ID、双记录对全含 10106）Unverified——接收率统计前必须查明；行为统计按 holdout 规则暂缓（4 候选隔离方案待研究者）。Gentime↔UTC 35 s 官方文档冲突待经验校准；跨设备时钟同步为残余时延类主张（仅生成→RSE 捕获）的共同未验证前置。Packet 尚未下载（Gate `pending_official_packet_access` 不变）。

### KI-04 — 阶段 0.5 需要重建

现有结果是职责迁移前的部分真实参考，虽未纳入 pNEUMA TTC，但来源仍指向旧 map-match 产物；SUMO calibration 样本缺失。该结果不能作为最终 coverage Gate。pNEUMA 侧参考接口已由 Stage 0.3 r2 包提供并携带逐状态质量字段（write_real_reference_package 读取并 fail-closed 使用）；按状态抽样是否保持时间加权权重属 Stage 0.5 设计决定，未冻结。

### KI-05 — readiness 是迁移前快照

`RES-PROTOCOL-READINESS-V1` 保留旧实验键和旧 blocker，只能证明当时未就绪。阶段 0 前置项与科学容差完成后，必须用当前 `stage_X_Y` 入口重新生成；当前不允许协议锁或阶段 1.1。

### KI-06 — 当前没有训练模型

仓库没有可核验的训练循环、loss、optimizer、checkpoint 或阶段 1.1 模型。任何对“当前模型结构/训练参数”的进一步描述均为 `Unverified`，直到研究者确认设计并实现。

## 当前冲突状态

2026-09-10 发现的 pNEUMA 职责冲突已由研究者批准退役决定解决。当前没有尚待研究者决定的已知重大科研冲突。

## 冲突记录模板

未来出现重大冲突时必须逐项填写：

- `Documented Intent`
- `Actual Implementation`
- `Evidence`
- `Affected Files`
- `Conflict`
- `Status: Awaiting Researcher Decision`

## 2026-10-10 KI-01 工程问题收尾

任务 1.4 解释 936 个合并编号异常，修复过度分段及不确定记录误入可靠事件的路径。基线包：`evidence/results/RES-STAGE-0.2-TASK-1.4/`。官方两个来源时段与物理身份未证明，但字段连续性和单帧唯一匹配可独立核验，不再作为工程验收硬阻断。科学异常/极端值审计、最终事件规则与阈值仍未冻结。历史任务 1.3 连续性筛选描述已由任务 1.4 报告更正，历史文件不改写。

## 2026-10-10 KI-01 工程状态更新

跨时钟前车匹配潜在缺口已修复并通过构造测试和全量回归；真实数据无跨时钟匹配。任务 1 工程项建议关闭，官方来源时段/物理身份与科学事件口径仍为 Unverified/待后续审计。


## 2026-10-11 决策归档后仍待处理

正式提取器默认最小跨度仍为 0.1 s，而研究者已批准 P2=0.2 s；指数 rho、固定车辆/窗口、区域贡献上下界和 DID 区间实现尚缺。NGSIM 100 ms 与 SUMO 200 ms 采样语义不可直接等价。

## 2026-10-11 Formal measurement implementation status

P2 formal event extraction and rho/bounded contribution primitives are implemented in an isolated versioned module and independently revalidated to 4,545 reliable events. Historical 0.1 s extractor and linear TTC exposure remain unchanged. Target region, target cohort qualification, evaluation window, message de-duplication, and formal quality gate are still Decision Required/Unresolved; fixed-window burden has not been claimed as completed without those inputs. GitHub automatic project-integrity workflow is disabled; local validation remains required.

## 2026-10-11 一致性修复状态

正式接口的三个确定性问题已修复并回归验证。历史 0.1 s 提取器、旧线性指标和既有产物不变。目标区域/窗口等科学参数仍未决。


## 2026-10-12 Stage 0.2 综合收口（当前状态）

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。

### 论文版本冲突 — Awaiting Researcher Decision

Documented Intent：06_DECISIONS指数rho/固定分母/车辆等权。Actual Implementation：formal v2符合批准设计，旧main.tex:378-405仍为线性/观测分母/求和。Evidence：最新版20261010 PDF与最终包paper_version_conflict.md。Affected Files：paper/主论文/main.tex、paper/历史记录/20261010_YYS.pdf、06_DECISIONS。Conflict：论文版本与当前设计未同步。Status: Awaiting Researcher Decision；研究者指定正式版本，不修改论文、不替换批准算法。
