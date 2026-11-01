# Hudgens & Halloran (2008) — Toward causal inference with interference

- **完整题名**：Toward causal inference with interference
- **作者 / 发表**：Michael G. Hudgens, M. Elizabeth Halloran; 2008; Journal of the American Statistical Association 103(482):832–842
- **DOI / 正式链接**：10.1198/016214508000000292; https://doi.org/10.1198/016214508000000292
- **开放全文**：PMC2600548; https://pmc.ncbi.nlm.nih.gov/articles/PMC2600548/
- **Zotero**：Item H8GFNS8U；无 PDF 附件
- **阅读状态**：**FULL_TEXT_READ**（PMC HTML 全文逐节核读；没有把 Zotero 附件缺失误记为未读）

## 研究问题和潜在结果

论文研究一个单位的结果依赖同组其他单位处理时，如何定义和估计因果效应。潜在结果写成整个组内处理向量的函数，而不是只写本单位处理。核心是部分干扰假设：不同组之间没有干扰，但组内可以干扰。

## 处理设计和 estimands

- 先在组层随机分配疫苗覆盖策略，再在组内进行个体随机化的两阶段设计。
- 定义 direct effect（个体自身处理变化、同组其他处理固定）、indirect effect（其他个体处理变化、本个体处理固定）、total effect（两者共同变化）和 overall effect。
- 估计量在给定随机化设计下无偏；在更强的分层干扰假设下推导方差。作者明确说明方差假设可能不成立，需按实际干扰结构选取其他策略。
- 识别依赖设计已知、潜在结果和组划分合理、处理概率正且没有跨组干扰。文章不是交通消息机制的模型。

## 作者真正证明了什么

- **Fact**：在两阶段随机化和部分干扰结构下，直接、间接、总效应可以被定义并用设计式估计。
- **Inference**：交通区域效应必须先定义网络簇/暴露结构；普通独立单位 A/B 不是自动有效。
- **未证明**：道路网络天然满足部分干扰，或车辆消息/物理邻域能够被固定划分。

## AAD 关系

这篇论文提供 AAD 区域效应的因果设计基础，而不是 AAD 的创新本身。AAD 需要证明消息和物理交互的 exposure mapping 可观测、时间内稳定且不跨簇泄漏；若通信和跟驰跨越簇边界，则应改用一般网络干扰或政策效应。
