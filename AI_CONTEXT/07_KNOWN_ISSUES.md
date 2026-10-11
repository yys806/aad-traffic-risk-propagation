# AAD Known Issues

## 已确认问题

### KI-01 — 阶段 0.2 尚未收口

v2 便携 audit 能证明 NGSIM 生成有效跟驰测量与风险事件，但异常记录、极端值来源、最终分布和适用边界尚未完成。旧 audit 的 `pending_pneuma_and_blind_reaudit` 是迁移前原始字节；当前代码已改为 `active_audit_closure`，需要新 run 才会产生新证据。

Evidence：`evidence/results/RES-STAGE-0.2-NGSIM-V2/audit.json`、`code/src/riskprop/ngsim_risk_calibration.py`、阶段 0.2 执行记录。

### KI-02 — 阶段 0.3 无正式产物

原始 pNEUMA 数据与通用宽表读取函数存在，但没有新职责下的专用统计入口、冻结 config、分布表或 audit。Status：`Not started`。

### KI-03 — packet 级通信证据不可用

当前快照记录官方 Packet 访问返回 HTTP 403；RV_RX 只能支持接收状态连续性，不能估计 packet 级时延、丢包或采用。外部访问状态自该快照后未在本次重构中重新联网核验。

### KI-04 — 阶段 0.5 需要重建

现有结果是职责迁移前的部分真实参考，虽未纳入 pNEUMA TTC，但来源仍指向旧 map-match 产物；SUMO calibration 样本缺失。该结果不能作为最终 coverage Gate。

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
