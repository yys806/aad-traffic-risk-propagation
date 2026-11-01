# AAD P1 双传播因果 DAG

日期：2026-11-01
状态：**P1_TASK2_REFINED_DAG**。DAG 描述识别结构；研究者已确认 SUMO 优先、单跳通信和自动控制器，具体随机化/阈值/中介参数仍未冻结。

## 1. 时间分层

以事件 \(e\) 和时间步 \(t\) 展开反馈。图中的 \(H_e\) 是处理前背景，\(Z_S\) 和 \(Z_C\) 是随机化/场景分配，\(S^*\) 和 \(C^*\) 是实际源事件与实际策略执行状态，消息、采用、命令、动作和物理状态均在分配之后按时间发生。任何反馈都写成 \(X^*_t\to X^*_{t+1}\)，不在同一时间层画环。

## 2. DAG 源码

下面的 Mermaid 源码可直接渲染。带星号的节点是真实过程，带波浪号的节点是观测/派生记录；节点名称中的 t、t+1 是时间层标签。

    flowchart LR
      H[处理前背景 H_e<br/>初始交通状态、车辆特征、道路拓扑<br/>控制器配置、通信条件、网络干扰]
      ZS[Source assignment Z_S]
      SS[Actual source state S*<br/>Formal P2 or B mechanism]
      ZC[Communication assignment Z_C]
      MS[Message Strategy policy]
      CS[Actual strategy execution C*<br/>single-hop direct]
      ZA[Optional adoption encouragement Z_A]

      H --> ZS
      H --> ZC
      H --> ZA
      H --> SS
      ZS --> SS
      H --> CS
      ZC --> MS
      MS --> CS

      subgraph INFO[真实信息传播链 at t]
        Gs[Generation G*]
        Ts[Transmission T*]
        Ds[Delivery D*]
        Vs[Verification V*]
        As[Controller Adoption A*]
        Decs[Controller Decision D*]
        Ucs[Control Command Ucmd*]
        Us[Actual Action U*]
        Gs --> Ts --> Ds --> Vs --> As --> Decs --> Ucs --> Us
      end

      subgraph PHYS[真实物理传播链 at t]
        Xs[Physical State X*_t]
        GPs[Physical Network G*_P,t]
        PIs[Vehicle Interaction PI*_t]
        PPs[Physical Propagation PP*_t]
        PAs[Physical Arrival T_P]
        XTs[Target State X*_T,t]
        Rs[Regional Risk R*_T,t]
        Xs --> GPs --> PIs --> PPs --> PAs --> XTs --> Rs
      end

      subgraph OBS[观测与时间过程]
        GI[Information Network G*_I,t]
        XO[Observer record X~_t]
        DO[Message/log record D~]
        AO[Controller log A~]
        UO[Action record U~]
        RO[Risk record R~_T,t]
        PO[Physical arrival record T~_P]
        TR[Population risk-effect onset T^hat_R]
        Q[Clock / identity / measurement quality Q_t]
      end

      H --> Xs
      H --> GPs
      H --> GI
      H --> Q
      SS --> Gs
      SS --> PIs
      CS --> Gs
      GI --> Ts
      ZA --> As
      Xs --> Decs
      PIs --> Decs
      PIs --> PPs
      Us --> XTs
      PPs --> Ds
      PPs --> GI
      PPs --> XTs
      Rs --> XO
      Rs --> RO
      Ds --> DO
      As --> AO
      Us --> UO
      PAs --> PO
      Q --> XO
      Q --> DO
      Q --> AO
      Q --> UO
      Q --> RO
      Q --> PO
      RO --> TR

      Us --> Xs1[Physical State X*_{t+1}]
      PPs --> Xs1
      Xs1 --> GPs1[Physical Network G*_{P,t+1}]
      Xs1 --> GI1[Information Network G*_{I,t+1}]
      Xs1 --> PIs1[Vehicle Interaction PI*_{t+1}]
      GI1 --> Ds1[Delivery D*_{t+1}]
      PIs1 --> PPs1[Physical Propagation PP*_{t+1}]

## 3. 节点语义

| 节点 | 类型 | 说明 |
|---|---|---|
| \(H_e\) | 处理前背景/混杂 | 初始交通状态、车辆与道路特征、控制器配置、通信条件、网络干扰；可同时影响分配、链路和结果 |
| \(Z_S,Z_C,Z_A\) | 分配变量 | 源事件场景/实验分配、通信策略分配和可选 Adoption encouragement；不等于实际状态 |
| Message Strategy | 策略变量 | 由 \(Z_C\) 指定的单跳消息政策；实际是否执行由 \(C^*\) 表示 |
| \(S^*,C^*\) | 实际处理状态 | 实际 Formal P2/B 源事件和实际单跳策略执行；可能因资格、链路或安全覆盖失败 |
| \(G^*,T^*,D^*,V^*\) | 真实信息过程 | 生成、发送、送达和验证；每个阶段可失败、重复、过期或删失 |
| \(A^*,D^*,U^{cmd,*},U^*\) | 真实机制 | Adoption、Controller Decision、Command 和 Actual Action；采用和动作不是同一变量 |
| \(G_P^*,G_I^*\) | 真实动态网络 | 分别表示物理交互和信息可达；共享节点不意味着共享边 |
| \(PI^*,PP^*,T_P\) | 真实物理过程 | 物理交互、状态传播和独立物理到达；\(T_P\) 需要路径和时钟 witness |
| \(X^*_T,R^*_T,Y^*\) | 真实结果 | 目标区域状态、Formal rho/P2 风险过程和固定区域结果 |
| \(\widetilde X,\widetilde D,\widetilde A,\widetilde U,\widetilde R,\widetilde T_P\) | 观测/派生记录 | Observer、消息/控制器日志、轨迹和风险计算；受误差、身份、时钟和缺失影响 |
| \(Q_t\) | 测量质量 | 时钟桥接、身份连续性、遮挡、观测质量和缺失机制；不直接改变真实过程 |
| \(\widehat T_R\) | 总体时间结果 | 从区域风险组间曲线派生的总体 onset，不等于首次观察下降 |

## 4. 处理前与处理后变量

**处理前**：\(H_e\)、\(X_0^*\)、车辆特征、道路拓扑、计划的控制器配置、通信覆盖/容量、预定的 source stratum，以及在随机化前确定的目标 cohort/region/window 候选。它们可以用于分层、精度和设计权重，但不能用处理后值替代。

**处理变量**：\(Z_S\)、\(Z_C\) 和可选的 \(Z_A\)。四格设计要求只在 source-present 与 communication-enabled 两个分配因素上改变；\(S^*\) 和 \(C^*\) 是处理后实际状态。

**处理后机制变量**：\(S^*,C^*,G^*,T^*,D^*,V^*,A^*,D^*,U^{cmd,*},U^*,PI^*,PP^*,T_P\) 以及消息延迟、采用状态和安全覆盖。将这些变量条件化会改变目标总体，不能自动得到自然中介效应。

**结果变量**：固定 \(Y^*_{\mathcal T}\) 及其观测 \(\widetilde Y_{\mathcal T}\)、风险曲线 \(R^*_{\mathcal T}(t)\)、动作时间 \(T_U\)、总体风险 onset \(\widehat T_R\) 和物理到达 \(T_P\) 及 \(\widetilde T_P\)。

## 5. 主要因果路径和竞争路径

### 5.1 目标信息介导路径

    Z_C → C* → Generation → Transmission → Delivery → Verification
       → Adoption → Controller Decision → Command → Actual Action
       → Vehicle Interaction / Target State → Regional Risk

该路径只表示机制假设；每个箭头都需要对应日志或状态测量。

### 5.2 普通物理路径

    Z_S → S* → Physical Interaction → Physical Propagation
       → Physical Arrival → Target Region State → Regional Risk

路径资格不能以时间先后、同车有序轨迹或目标端第一次速度变化单独证明。

### 5.3 关键竞争路径

- \(H_e\to Z_S/Z_C/S^*/C^*/Y^*\)：背景交通、车辆能力、通信条件和控制器配置可能同时影响分配、实际状态和结果，需在分配或设计阶段处理。
- \(Z_S\to S^*\to Y^*\)：场景分配不保证实际 Formal P2 资格；自然事件或资格失败不能被当成已实现的源处理。
- \(S^*\to PP^*\to T_P\to Y^*\)：普通物理传播可以在没有消息时改变风险，不能把消息组的物理状态当作反事实。
- \(U^*_t\to X^*_{t+1}\to G_P^*(t+1),G_I^*(t+1)\)：动作改变影响下一时间步的物理和信息网络；不能把反馈压缩成同一时间层的协变量。
- \(X^*,D^*,A^*,U^*,R^*\to \widetilde X,\widetilde D,\widetilde A,\widetilde U,\widetilde R\)：观测过程记录真实过程，不反向成为真实状态的原因。
- Network Interference：其他车辆的分配、采用和动作通过 \(G_P/G_I\) 影响目标结果；车辆级 SUTVA 默认不成立。

## 6. 干扰与潜在结果

在存在网络干扰时，目标车辆 \(i\) 的结果写成 \(Y_i^*(\mathbf Z_e)\)，事件/区域结果写成 \(Y_e^*(\mathbf Z_e)\)，其中 \(\mathbf Z_e=(Z_{S,e},Z_{C,e},Z_{A,e},\ldots)\) 是整场分配向量。只有在明确干扰域、exposure mapping 和正支持时，才可将其压缩为 \(Y_i(z_i,g_i)\) 或 cluster policy outcome。未知域外影响时，普通个体 A/B 差异没有清楚的因果含义。

建议同时保存：

1. 自身分配 \(z_i\)；
2. 物理 exposure（邻车动作、路径连接）；
3. 信息 exposure（可达、实际送达、消息版本）；
4. 整网/簇的 assignment vector；
5. 域外泄漏和安全覆盖标记。

## 7. 识别限制

1. 随机化 \(Z_S/Z_C\) 可以识别相应 assignment-level ITT，但不把 \(S^*/C^*\) 或 post-treatment adoption/action 变成已识别的中介效应。
2. 只观察 message-delivered 或 adopted 子集会发生选择；需要鼓励随机化、IV、principal stratification 或其他明确条件才能讨论 complier/mediation 对象。
3. SUMO Observer 的只读性只支持模型内观测独立；现实独立 witness 还需要时空标定、身份和缺失证据，不等于 no-message 反事实。
4. 两臂 source-present 设计不识别 \(S\times C\) 四格交互，除非额外假设 source-absent 下 communication effect 为零等。
5. \(T_R<T_P\) 需要风险效应 onset 与物理到达均有可辩护的区间；时间排序本身不是因果证明。
6. 反馈由时间层展开后仍可能有未观测混杂；必须把身份、时钟、缺失和安全中止保留在审计记录中。

## 8. 与工程接口的关系

现有 formal_design.py 强制四格配置和生成—发送—送达—验证—采用的时间顺序，但当前字段主要校验配置与生命周期，不是完整的 \(Z\)/actual/observation 生产契约；stage_i_mechanism.py 对联合时间轴在物理到达缺失时返回 Unknown；protocol_lock.py 仍要求所有 Gate 和冻结字段齐全才能锁定。本 DAG 仅规定理论关系，不改变这些函数或准入状态。
