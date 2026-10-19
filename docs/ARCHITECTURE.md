# AAD 架构

```text
dataset/
  NGSIM ──> 阶段 0.2 跟驰风险测量 ─┐
  pNEUMA ─> 阶段 0.3 城市运动学 ───┼─> 阶段 0.5 仿真—现实覆盖
  SPMD ───> 阶段 0.4 通信边界 ─────┘
                                      ↓
                         阶段 0.6 数值验证与协议锁
                                      ↓
                         阶段 1.1 核心效应确认
```

阶段 0.1提供四格运行和五表证据链。五表分别记录车辆状态、源事件、消息生命周期、控制动作和风险。阶段 0.2—0.6只负责测量、校准与准入，不产生核心效应结论。

正式代码、入口和测试分别位于 `code/src/riskprop/`、`code/scripts/`、`code/tests/`；本机完整输出位于 `code/outputs/`；小型便携证据位于 `evidence/`。

2026-10-18：独立stage_0_5_calibration_gaps.py只连接两个SHA/角色受控原始校准成员与封存状态，输出车型/时钟/局部归一化/统一分层摘要；独立订阅式工程基准消费小型摘要，不调用正式校准/Gate evaluator，旧Stage0.2/0.3/0.4及P2语义不变。


## 2026-10-19 B1.2 分层准入与机制再验证

B1.2独立观测/执行层stage_0_5_b12_{observation,network,runtime,worker}.py：内部步全边分层数值、身份守恒与局部穿越分账、显式junction路径与分车道队列。主矩阵由observability_integration_audit准入，首个fixture终速不一致使准入false；未执行的主入口不代表动态验证完成。
