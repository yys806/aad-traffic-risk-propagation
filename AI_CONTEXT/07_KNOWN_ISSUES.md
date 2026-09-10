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
