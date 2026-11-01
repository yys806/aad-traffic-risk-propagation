# AAD P1 双传播因果 DAG

日期：2026-11-01
状态：**P1_PROPOSED_DAG**。DAG 描述识别结构，不批准具体随机化、平台或中介估计方案。

## 1. 时间分层

以事件 \(e\) 和时间步 \(t\) 展开反馈。图中的 \(H_e\) 是处理前背景，\(Z_e\) 是随机化/策略分配，消息、采用、命令、动作和物理状态均在分配之后按时间发生。任何反馈都写成 \(X_t\to X_{t+1}\)，不在同一时间层画环。

## 2. DAG 源码

下面的 Mermaid 源码可直接渲染。节点名称中的 t、t+1 是时间层标签；同一物理实体在后续时间层是新节点。

    flowchart LR
      H[处理前背景 H_e<br/>初始交通状态、车辆特征、道路拓扑<br/>控制器配置、通信条件、网络干扰]
      S[Source Event S_e]
      Z[Treatment Assignment Z_e<br/>source × communication strategy]
      A[Message Strategy A_e]
      H --> S
      H --> Z
      H --> A
      S --> Z
      Z --> A

      subgraph INFO[信息传播链 at t]
        Gt[Message Generation G_j,t]
        Xt[Transmission X_j,t]
        Dt[Delivery D_j,t]
        Vt[Verification V_j,t]
        ADt[Controller Adoption AD_ij,t]
        CDt[Controller Decision D_ij,t]
        CCt[Control Command Ucmd_i,t]
        AUt[Actual Vehicle Action U_i,t]
        Gt --> Xt --> Dt --> Vt --> ADt --> CDt --> CCt --> AUt
      end

      subgraph PHYS[物理传播链 at t]
        X0t[Initial Physical State X_t]
        GPt[Physical Interaction Network G_P,t]
        PIt[Vehicle Interaction PI_t]
        PPt[Physical Propagation PP_t]
        PAt[Physical Arrival T_P]
        XTt[Target Region State X_T,t]
        Rt[Regional Risk R_T,t]
        X0t --> GPt --> PIt --> PPt --> PAt --> XTt --> Rt
      end

      subgraph MEAS[测量与时间]
        GIt[Information Network G_I,t]
        Y[Fixed Region Outcome Y_T]
        TR[Risk-effect onset T_R]
        W[Clock / identity / measurement quality W_t]
      end

      H --> X0t
      H --> GPt
      H --> GIt
      H --> W
      S --> Gt
      S --> PIt
      A --> Gt
      GIt --> Xt
      H --> ADt
      X0t --> CDt
      PIt --> CDt
      ADt --> CDt
      CDt --> CCt
      CCt --> AUt
      PIt --> PPt
      AUt --> XTt
      PPt --> Dt
      PPt --> GIt
      PPt --> XTt
      Rt --> Y
      XTt --> Y
      W --> Dt
      W --> Vt
      W --> AUt
      W --> Y
      Rt --> TR
      PAt --> TR

      AUt --> Xt1[State X_t+1]
      PPt --> Xt1
      Xt1 --> GPt1[Physical Network G_P,t+1]
      Xt1 --> GIt1[Information Network G_I,t+1]
      Xt1 --> PIt1[Vehicle Interaction PI_t+1]
      GIt1 --> Dt1[Delivery D_j,t+1]
      PIt1 --> PPt1[Physical Propagation PP_t+1]

## 3. 节点语义

| 节点 | 类型 | 说明 |
|---|---|---|
| \(H_e\) | 处理前背景/混杂 | 初始交通状态、车辆与道路特征、控制器配置、通信条件、网络干扰；可同时影响分配、链路和结果 |
| \(S_e\) | 源事件 | 源风险事件或受控扰动资格；正式资格由 P2 决定，当前不冻结 |
| \(Z_e,A_e\) | 处理/策略 | 随机化或外生分配及其 message strategy；分配单位可以是事件、session、簇或整网，待 P5 决定 |
| \(G,X,D,V\) | 处理后机制 | 生成、传输、送达和验证；每个阶段可失败、重复或删失 |
| \(AD,CD,CC,AU\) | 处理后机制 | 采用、控制器决策、命令和实际动作；采用和动作不是同一变量 |
| \(G_P,G_I\) | 动态网络 | 分别表示物理交互和信息可达；共享节点不意味着共享边 |
| \(PI,PP,PA\) | 物理基准 | 物理交互、状态传播和独立物理到达；\(PA\) 需要路径和时钟 witness |
| \(X_T,R,Y_T\) | 结果 | 目标区域状态、Formal rho/P2 风险过程和固定区域结果 |
| \(W_t\) | 测量/质量 | 时钟桥接、身份连续性、遮挡、观测质量和缺失机制；可影响所有观测节点 |
| \(T_R\) | 时间结果 | 风险因果效应 onset，不等于首次观察下降 |

## 4. 处理前与处理后变量

**处理前**：\(H_e\)、\(X_0\)、车辆特征、道路拓扑、计划的控制器配置、通信覆盖/容量、预定的 source stratum，以及在随机化前确定的目标 cohort/region/window 候选。它们可以用于分层、精度和设计权重，但不能用处理后值替代。

**处理变量**：\(S_e\)、\(C_e\) 或更一般的 \(Z_e,A_e\)。四格设计要求只在 source-present 与 communication-enabled 两个科学因素上改变；具体配置仍需研究者确认。

**处理后机制变量**：\(G,X,D,V,AD,CD,CC,AU,PI,PP,PA\) 以及消息延迟、采用状态和安全覆盖。将这些变量条件化会改变目标总体，不能自动得到自然中介效应。

**结果变量**：固定 \(Y_{\mathcal T}\)、风险曲线 \(R_{\mathcal T}(t)\)、动作时间 \(T_U\)、风险效应时间 \(T_R\) 和独立物理到达 \(T_P\)。

## 5. 主要因果路径和竞争路径

### 5.1 目标信息介导路径

    Z/A → Generation → Transmission → Delivery → Verification
       → Adoption → Controller Decision → Command → Actual Action
       → Vehicle Interaction / Target State → Regional Risk

该路径只表示机制假设；每个箭头都需要对应日志或状态测量。

### 5.2 普通物理路径

    Source Event → Physical Interaction → Physical Propagation
       → Physical Arrival → Target Region State → Regional Risk

路径资格不能以时间先后、同车有序轨迹或目标端第一次速度变化单独证明。

### 5.3 关键竞争路径

- \(H_e\to D/AD/AU/Y\)：背景交通、车辆能力、通信条件和控制器配置同时影响链路和结果，需在分配或设计阶段处理。
- \(H_e\to S\to Y\)：源事件强度/资格可能与结果相关；源事件定义和分层必须在处理前或独立来源中固定。
- \(S\to PP\to PA\to Y\)：普通物理传播可以在没有消息时改变风险，不能把消息组的物理状态当作反事实。
- \(AU\to GI\to D\)：动作改变可能改变通信可达和后续消息，故时间展开的网络干扰不能被当作静态协变量。
- Network Interference：其他车辆的分配、采用和动作通过 \(G_P/G_I\) 影响目标结果；车辆级 SUTVA 默认不成立。

## 6. 干扰与潜在结果

在存在网络干扰时，目标车辆 \(i\) 的结果写成 \(Y_i(\mathbf A_e)\)，事件/区域结果写成 \(Y_e(\mathbf A_e)\)，其中 \(\mathbf A_e\) 是整场处理分配。只有在明确 partial-interference 域、exposure mapping 和正支持时，才可将其压缩为 \(Y_i(a_i,g_i)\) 或 cluster policy outcome。未知域外影响时，普通个体 A/B 差异没有清楚的因果含义。

建议同时保存：

1. 自身处理 \(a_i\)；
2. 物理 exposure（邻车动作、路径连接）；
3. 信息 exposure（可达、实际送达、消息版本）；
4. 整网/簇的 assignment vector；
5. 域外泄漏和安全覆盖标记。

## 7. 识别限制

1. 随机化 \(Z\) 可以识别相应 assignment-level ITT，但不把 post-treatment adoption/action 变成已识别的中介效应。
2. 只观察 message-delivered 或 adopted 子集会发生选择；需要鼓励随机化、IV、principal stratification 或其他明确条件才能讨论 complier/mediation 对象。
3. 独立测量 witness 解决测量独立性的一部分，不等于 no-message 反事实；未采用车辆也不等于 \(Y(0)\)。
4. 两臂 source-present 设计不识别 \(S\times C\) 四格交互，除非额外假设 source-absent 下 communication effect 为零等。
5. \(T_R<T_P\) 需要风险效应 onset 与物理到达均有可辩护的区间；时间排序本身不是因果证明。
6. 反馈由时间层展开后仍可能有未观测混杂；必须把身份、时钟、缺失和安全中止保留在审计记录中。

## 8. 与工程接口的关系

现有 formal_design.py 强制四格配置和生成—发送—送达—验证—采用的时间顺序；stage_i_mechanism.py 对联合时间轴在物理到达缺失时返回 Unknown；protocol_lock.py 仍要求所有 Gate 和冻结字段齐全才能锁定。本 DAG 仅规定理论关系，不改变这些函数或准入状态。
