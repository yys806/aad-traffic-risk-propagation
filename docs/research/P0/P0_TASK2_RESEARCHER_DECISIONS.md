# P0 Task 2：研究者决策清单

本文件只列出 Proposal 和阻塞项，不把任何建议写入 Agreed Decision。

## 1. 需要研究者确认的科学选择

| 编号 | 决策问题 | 当前推荐 Proposal | 未决定时的影响 |
|---|---|---|---|
| D1 | 首要处理是什么 | 道路区段—时间簇随机的 message availability/strategy | 不能冻结 ITT |
| D2 | 目标单位和总体 | 源事件、预先固定 target cohort、固定区域 R 和窗口 W | 区域效应不可定义 |
| D3 | 首要结果 | 已批准风险体系中的固定个体或区域 risk burden | 不能比较不同聚合 |
| D4 | 物理到达定义 | 同源 no-message witness 下预注册状态阈值和持续时间 | Tphys 保持 Unknown |
| D5 | 网络干扰假设 | 默认一般网络 exposure mapping；只有证明隔离才用 partial interference | 不能使用普通 A/B |
| D6 | Adoption 识别 | 只作为随机鼓励/IV 的次级 estimand | adopted/not-adopted 不可解释 |
| D7 | 中介分析 | 首先 ITT；随后 interventional mediation | 自然直接/间接效应不作为默认 |
| D8 | 术语 | 用 information-mediated early risk effect；“类超距”只作为历史项目名称 | 避免把已有信息先到达包装成新现象 |
| D9 | 现实证据路线 | 未来同源消息实验 + 独立物理 witness | 当前四类数据只能做工程/测量准备 |

## 2. 如果核心效应无法识别

可收窄为以下可发表但需要另行评估的方向：

1. 消息生命周期和控制器采用的可审计性/失败边界；
2. BLOS/远端警告的状态依赖响应在交通风险场景的复现；
3. 信息 exposure 与物理 exposure 的测量误差和作用边界；
4. 交通网络干扰下的 design-based estimand 及敏感性分析；
5. SUMO 到现实的证据契约和适用域验证。

这些都是 Proposal，不是替代主线的自动决定。

## 3. 当前明确阻塞

- 无同源随机 message assignment；
- 无逐包 delivery、verification、adoption 和 controller action；
- 无独立 no-message physical witness；
- 无固定区域 cohort/window 的真实风险结果；
- NGSIM/MiTra/SPMD 不能拼成同一事件因果链；
- SUMO fixture 不能替代现实证据；
- Peng 和 Schönhof 的全文已补齐，但它们的先行结果进一步收窄而不是解除上述阻塞。

## 4. 不变的项目边界

本任务不修改 Stage 0.5、Stage 0.6、Protocol Lock、Stage I、Stage 1.1，不修改固定主线规划文件，不调整正式风险指标，不访问 locked holdout，不启动正式 SUMO 或现实数据采集。
