# P0 Task 1 最终报告

日期：2026-11-01。状态：`Completed with scientific decision blockers`。

## 完成内容

- 核对 AAD 项目状态、Task 17–20 证据边界和 Git 工作区。
- 先审计 Zotero `TJU → AAD`：确认 9 个主题集合及其当前条目结构；未修改 DRIFT、未删除或合并原有条目。
- 复用已有附件并完成 Saberi 2020、Duan 2023、Huang–Du 2022、Sun–Tan 2020、Lyu 2025、Coifman–Li 2024、Ma 2024 的全文阅读记录。
- 对 Schönhof 2006、Wang 2019、Jerath 2024、Peng 2026、Hudgens–Halloran 2008、Aronow–Samii 2017 进行正式来源和最近邻核验；全文不可得或未完成者明确标注。Jerath、Peng、Schönhof、Hudgens、Aronow 与 Wang 冲突图论文的元数据已导入 Zotero AAD；Jerath 与 Aronow 获得 PDF 附件，Wang 冲突图的重复导入记录已标记并保留。
- 建立 P0 治理规范、检索协议、注册表、逐篇记录、最近邻矩阵、创新性分析、NC 风险评估和方向备忘录。

## 对六个最终问题的回答

1. **最有价值的科学问题**：在独立物理传播基准存在时，远端消息是否通过可审计的“送达—验证—采用—动作”链产生可归因的个体和区域风险效应，并且该效应如何受网络干扰约束？
2. **真正可能成立的创新点**：双传播竞争的事件级因果识别、采用与动作中介的可审计闭环、以及干扰感知的区域 estimand。它们都是有条件的 Proposal。
3. **需要放弃或收窄的主张**：信息更快、V2X 改变行为、非局部控制、信息—物理耦合、拥堵网络传播、TTC 风险评价和“作用区域”本身都已有先行工作，不能单独包装为首次创新。
4. **最值得继续的方向**：先做双传播因果链可识别性与证据契约，再决定是否进入新的实验或数据采集。
5. **NC 级不可替代证据**：独立物理 time-indexed witness；消息全生命周期日志；控制器采用和动作中介；干扰下 direct/indirect/total estimand；现实数据或跨场景验证；仿真—现实适用域边界。
6. **下一步 P0 Task 2**：完成“可识别性与证据契约审计”，不启动新的正式 SUMO 或 Stage 1.1。

## 项目状态边界

本任务没有改变：Stage 0.5 `CLOSED_WITH_LIMITATIONS`、Stage 0.6 `PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS`、Protocol Lock `BLOCKED`、Stage I `READY_ENGINEERING_ONLY`、Stage 1.1 `NOT_AUTHORIZED`。没有访问 locked holdout，没有生成 protocol lock，没有改变风险指标或科学 Gate。

## 发现但未处理的问题

- Wang 2024 冲突图论文已有 AAD 条目；本次 DOI 导入意外生成了重复记录 `BYCXQ5A3`。为保护原有条目和附件，已打标签 `P0/DUPLICATE_OF_5LYN24YV`，未合并或删除。后续 Task 可在获得明确处理决定后清理。
- Peng 2026、Schönhof 2006、Hudgens–Halloran 2008 的全文 PDF 在本次合法来源范围内未附加；它们在注册表和 Zotero 中保留正确元数据与阅读状态，不支持超出已读范围的强断言。
- Wang 2019 arXiv 论文的 Zotero identifier lookup 未创建本地记录；其正式 arXiv 来源与部分阅读记录已保留。
