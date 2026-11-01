# Aronow & Samii (2017) — Estimating average causal effects under general interference

- **完整题名**：Estimating average causal effects under general interference, with application to a social network experiment
- **作者 / 发表**：Peter M. Aronow, Cyrus Samii; 2017; The Annals of Applied Statistics 11(4):1912–1947
- **DOI / 正式链接**：10.1214/16-AOAS1005; https://doi.org/10.1214/16-AOAS1005
- **开放 PDF**：Zotero 附件 LPLMUALR；Project Euclid 正式全文
- **Zotero**：Item T6SFNY5I；PDF LPLMUALR
- **阅读状态**：**FULL_TEXT_READ**（全文逐节核读，含 exposure mapping、估计量、方差和应用限制）

## 研究问题和框架

论文把干扰问题拆成三部分：已知的 treatment assignment design、从全体 assignment 到单位 exposure 的 exposure mapping，以及研究者真正要估计的 estimand。潜在结果对映射后的暴露状态而不是整个处理向量建模。

## 估计方法和假设

- 在已知随机化设计和映射下，使用 Horvitz–Thompson / inverse-probability weighting 估计平均暴露状态效应；也讨论 Hájek/协变量调整改进。
- 需要每个单位目标暴露状态的正概率（positivity），并知道或可计算其 exposure probability。
- 在局部依赖条件下给出保守方差估计和渐近正态结果；网络结构越密、暴露映射越不稳定，方差和可解释性越差。
- 暴露映射可以是任意预先定义的函数，但它不是由回归自动识别出来的。错误映射会改变 estimand，而不是只增大标准误。

## 应用和局限

社会网络实验说明 assignment→exposure→outcome 的设计式估计可以处理一般干扰；但方法本身不提供交通物理邻域、消息距离、时间窗口或多跳扩散的定义。交通网络还存在动态节点、车辆进出、物理相互作用和消息转发反馈，需要时间展开映射。

## AAD 关系

该文是 AAD Message Exposure 与 Physical Interaction Exposure 双暴露设计的直接方法基础。AAD 不能声称创造了新的一般干扰估计理论；可主张的增量只能是把交通机制、可审计消息生命周期和物理到达时间纳入可测量的 exposure mapping，并用真实/受控随机化检验。
