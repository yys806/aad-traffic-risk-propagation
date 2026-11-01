# P0 Task 2：双传播动态因果模型

状态：**Proposal**。这是可审计的研究模型，不是已验证的科学机制。

## 1. 时间展开结构

AAD 不能用一个静态串联图表示整个过程。对离散时间 t = 0, 1, …, K，定义：

- E：源风险事件及其质量；
- L0：事件前车辆和交通基线；
- A：消息策略分配/可用性；
- Gt：消息生成；
- St：发送；
- Dt：送达；
- Vt：验证；
- Mt：控制器采用；
- Ut：控制器命令或驾驶动作；
- YUt：观察到的车辆动作；
- Spt：车辆运动、跟驰和交通状态；
- Pt：物理暴露及其邻域；
- Tphys：预先定义的物理状态到达；
- Yit：个体风险；
- Yrt：固定区域和窗口内的区域风险；
- Qt：身份、时钟、空间映射和测量质量。

时间顺序为：

E → A → G0 → S0 → D0 → V0 → M0 → U0/YU0 → Sp1 → P1 → {G1, S1, D1, …} → Yi/Yr

物理链并行展开：

E → L0 → source motion → leader/follower interaction → Spt → Tphys → target response

动作在 t 改变 Spt+1，Spt+1 又改变下一时刻的通信邻居、物理邻域、风险和消息转发，因此使用时间索引而不是把反馈画回静态 DAG。

## 2. 结构方程草图

- Spt+1 = f_phys(Spt, L0, YUt, E, Ht, εphys,t)
- Gt = f_gen(E, Spt, A, policy_version, εgen,t)
- Dt = f_del(St, communication_state_t, distance_t, density_t, εdel,t)
- Vt = f_ver(Dt, source_valid_t, freshness_t, content_t, εver,t)
- Mt = f_adopt(Vt, driver/controller_state_t, risk_state_t, εadopt,t)
- YUt = f_action(Ut, Spt, human/controller_state_t, εaction,t)
- Yit = f_risk(YUt, Spt, measurement_rule, εrisk,t)
- Yrt = aggregate(Yit, C_t, R, W, missing_policy)

这些方程是结构化 Proposal。只有在同源数据中记录各节点、时钟和质量状态后，才能检验其中的边。

## 3. 动态 DAG 的必要边

1. L0 同时影响 A 的可用性、通信成功、采用倾向、动作和风险。
2. E 同时影响消息生成、源车物理动作和下游物理传播。
3. A 影响 G、S、D、V、M、U；不能把 D 或 M 当作随机处理。
4. Spt 影响通信距离、物理交互、未来消息和风险。
5. 邻车处理 A−i、消息暴露 Xmsg 和物理暴露 Xphys 影响目标车动作与风险。
6. YUt 影响后续 Spt+1，因此可能产生跨车辆 spillover。
7. Q 影响哪些节点被观察到；Q 既可能与交通状态相关，也可能与处理路径相关。按 Q 筛选完整案例可能产生选择偏差。
8. 未观测的驾驶状态、控制器内部置信度、道路几何和通信拥塞是潜在共同原因，不能由 DAG 画出就假设已控制。

## 4. DAG 文本表示

    E ───────► Gt ─► St ─► Dt ─► Vt ─► Mt ─► Ut/YUt ─► Spt+1 ─► Yi/Yr
    │          │                         │       │          │
    │          │                         │       └──────────┘
    │          │                         └────► future message exposure
    │          └────────────────────────────────────────────► physical source motion
    │
    └────────────────────────────► Spt physical disturbance ─► Tphys ─► target response

    L0 ─► A ─► Gt
    L0 ─► communication state ─► Dt
    L0 ─► driver/controller state ─► Mt ─► YUt
    L0 ─► Spt, Yi
    A−i ─► Xmsg ─► Mt/YUt/Yi/Yr
    Spt ─► Xphys ─► YUt/Yi/Yr
    Q ─► observed(D,V,M,YU,Tphys,Yi,Yr)

该文本是时间展开的逻辑图；真正绘图时应为每个 t 复制节点并只连接 t 到 t+1，避免把反馈错误地表示为有环静态 DAG。

## 5. 变量字典摘要

| 变量 | 数学定义 | 物理含义 | 时间戳 | 因果角色 | 当前数据 |
|---|---|---|---|---|---|
| Source event | E=(event_id,tE,xE,type,qE) | 源风险事件 | 事件时钟 | 源 | 部分可派生 |
| Initial state | L0=(v,a,gap,leader,type,road) | 事件前状态 | 基线窗口 | 混杂/基线 | MiTra/NGSIM 部分 |
| Assignment | Ai∈{0,1} 或策略 | 是否可用消息 | 分配时钟 | 处理 | 不存在 |
| Delivery | Di=(message_id,tD) | 接收端确实收到 | 接收时钟 | 中介 | 不可观测 |
| Verification | Vi=(tV,valid) | 来源/时效/内容通过验证 | 控制器时钟 | 中介 | 不可观测 |
| Adoption | Mi=(tM,status) | 控制器采用 | 控制器时钟 | 中介 | 不可观测 |
| Action | YUi(t) | 实际速度/加速度/间距变化 | 轨迹时钟 | 中介/结果前 | 可部分派生 |
| Physical state | Spt | 交通扰动和交互 | 轨迹/仿真时钟 | 中介 | 可部分观察 |
| Physical arrival | Tphys | 预定义状态到达目标 | 统一时钟 | 时间结果 | 无独立 witness |
| Individual risk | Yi | 已批准代理指标 | 轨迹时钟 | 结果 | 可部分派生 |
| Regional risk | Yr | 固定区域 cohort 聚合 | 区域窗口 | 结果 | 未识别 |
| Observation quality | Q | 是否可观测、有效、同步 | 记录时钟 | 测量/选择 | 各源不同 |

## 6. Fact、Inference、Hypothesis、Proposal

- **Fact**：既有文献已经分别研究了信息波、非局部控制、物理拥堵传播和 BLOS 动作响应；项目现有数据没有完整双链。
- **Inference**：两条传播链的竞争只能在同源事件、相同 cohort、统一时钟和 no-message 基准下比较。
- **Hypothesis**：在某些交通状态下，消息介导动作可能先于物理状态到达而改变个体风险；方向和单调性尚未知道。
- **Proposal**：以消息策略 ITT 和区域 policy effect 为最小 estimand，把采用和中介作为次级机制分析。

## 7. 与 Task1 最近邻的边界

Schönhof 已覆盖信息与车辆运动耦合概念；Wang 已覆盖队列—LWR 信息波；Jerath 已覆盖联网车辆的作用边界；Peng 已覆盖随机化 BLOS 警告对驾驶响应的因果异质性；Hudgens–Halloran 和 Aronow–Samii 已提供干扰下 estimand 与 exposure mapping。AAD 若继续，只能主张在交通风险场景把这些已知链条统一成可审计、可反事实替换的动态证据契约。
