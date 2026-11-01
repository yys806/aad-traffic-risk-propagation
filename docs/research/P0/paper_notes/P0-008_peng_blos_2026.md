# Peng et al. (2026) — The state-dependent causal effect of a V2X-based beyond-line-of-sight warning system on young driver response

- **完整题名**：The state-dependent causal effect of a V2X-based beyond-line-of-sight warning system on young driver response: a causal machine learning approach
- **作者 / 发表**：Zishan Peng, Bo Yu, Shan Bao, Wenjie Lu, Yuren Chen, Junhua Wang; 2026; Accident Analysis & Prevention 235:108642
- **DOI / 正式链接**：10.1016/j.aap.2026.108642; https://doi.org/10.1016/j.aap.2026.108642
- **Zotero**：Item HP4DIXED；Publisher PDF P9WNTXKL
- **PDF 来源与 SHA256**：研究者提供的 D:\下载\1-s2.0-S0001457526002514-main.pdf；87F71B3A89E5F9260031C19A61A90F52892A22ACA73B15148DA2CEBA67942FD4
- **阅读状态**：**FULL_TEXT_READ**（16 页正文逐页核读；随机化、变量定义、DML/CausalForestDML、稳健性、结果、讨论和局限均已记录）

## 研究问题和实验

论文研究 V2X-based beyond-line-of-sight warning 对年轻驾驶者响应的平均和状态依赖因果效应。实验为 SCANeR Studio 高保真驾驶模拟器，连续记录车辆运动和驾驶输入，采样频率 100 Hz。

- 40 名持证驾驶者（20 男、20 女），年龄 19–27 岁，均值 22.08；每人完成六个试次，原始 240 条，1 条日志失败后分析 239 条有效试次（第 4 页）。
- 采用 2 × 3 被试内设计：警告/无警告 × 三种 BLOS 场景；六个试次顺序在参与者之间 counterbalanced。
- 三类场景为：被前车遮挡的静态道路施工障碍、四车队中被中间车辆遮挡的紧急制动、交叉口盲区行人。高速场景警告距离 250 m，低速行人场景触发距离 20 m（第 3–4 页）。
- 警告由双声、中文语音和文字提示组成；警告在脚本中预配置，不模拟真实通信丢包、感知不确定性或传感器检测延迟（第 3–4 页）。
- 处理 T 是试次级随机分配的 BLOS warning；作者用同一参与者的无警告试次构造潜在结果对照。

## 结果变量

- 反应模式：R 为超过刹车/转向阈值的明确躲避动作；SSD 为警告前已持续低速；NR 为没有响应且人工复核为碰撞或显著偏离。239 条中 R=206、SSD=11、NR=22（第 6 页）。
- 反应时间 RT：首次显著刹车或转向时间减去警告触发时间；无警告组用同一空间位置的虚拟触发时间。RT 分析只包括可识别躲避反应的试次，因此是 response-conditioned，而非全体试次无条件反应时间（第 5–6 页）。
- ORS：将 RT timeliness score 和六项动作稳定性描述量（最大减速度、平均纵向 jerk、最大横向加速度、平均横向 jerk、最大转向速度、峰值合加速度）组合。PCA 前两主成分约解释 85% 方差；ORS 为 0–100 分，R 取 0.5 RTscore + 0.5 Evqual，SSD 只取 Evqual，NR 取 0（第 6–7 页）。

## 因果识别和估计

作者将 warning presence 作为 T，结果 Y 为 RT 或 ORS；DAG 中协变量包括静态驾驶者特征、警告前瞬时车辆控制状态和场景/试次顺序。随机化保证试次处理独立于潜在反应；positivity 来自每种驾驶者—场景组合均有警告和无警告。作者承认被试内重复暴露有 carryover，因此把 trial order、previous warning 和 cumulative warning exposure 纳入协变量，但这是假定这些变量足以吸收主要学习/适应过程，不能等同于无干扰证明（第 8–10 页）。

- DML 用 gradient boosting outcome model 和 regularized logistic treatment model，五折 cross-fitting；ATE 通过 residual-on-residual 回归估计。
- 置信区间使用按参与者聚类的 2,000 次 bootstrap。
- CausalForestDML 估计 CATE，SHAP 和 surrogate decision tree 解释状态依赖；R-learner 作为模型稳健性比较。
- 稳健性包括 1,000 次 placebo treatment permutation、随机 80% 子样本、dummy outcome、去除 sequential exposure 协变量和 R-learner 比较。

## 定量结果

- ORS ATE = **+6.73 points**，95% CI [1.36, 11.99]（第 10、14 页）。
- response-conditioned RT ATE = **−2.28 s**，95% CI [−3.17, −1.14]（第 10、14 页）。
- 去除 sequential exposure 协变量后，ORS=7.29、RT=−2.36；80% 子样本 ORS=7.02、RT=−2.26；dummy outcome ORS=−0.03、RT=0.01（第 11 页）。
- ORS CATE 范围约 0.88–9.44，中心约 +6.34；RT CATE 中心约 −2.17 s。SHAP 排名显示 steering reversal rate、mean jerk、maximum steering angle 等瞬时状态高于静态特征（第 11–13 页）。
- 高 steering reversal subgroup：ORS +11.12，95% CI [3.744, 15.772]；RT −2.11 s，95% CI [−3.288, −0.928]。低 mean jerk subgroup：ORS +12.81，95% CI [7.969, 19.329]；RT −4.62 s，95% CI [−6.257, −2.855]（第 14 页）。

## 作者真正证明了什么

- **Fact**：在该随机化被试内驾驶模拟器和预配置 BLOS 事件中，警告对年轻驾驶者 ORS 和可识别反应试次的 RT 有正向/提前响应的因果效应；效应具有瞬时车辆控制状态异质性。
- **Fact**：作者的处理是 warning presence，而不是实际通信 delivery、verification 或 controller adoption。
- **Inference**：远端警告改变驾驶响应已经有直接因果证据；AAD 不能把“警告改变动作”作为首次创新。
- **未证明**：真实道路中的消息送达/验证/采用链，独立物理传播基准，其他车辆的 spillover，区域风险或事故概率的因果变化。

## 局限性和 AAD 威胁

实验是高保真模拟器而非现实道路，参与者全为年轻驾驶者；脚本预配置警告，不含通信失败和感知不确定性；被试内重复试次仍可能有学习和 carryover；RT 只对可识别反应试次定义；ORS 是复合代理，不等同于事故概率；数据按申请提供。该论文直接封堵“BLOS warning causes action change”这一宽泛主张，AAD 只能把创新收窄到双传播时序、消息生命周期可审计性、干扰下区域效应和独立物理反事实。
