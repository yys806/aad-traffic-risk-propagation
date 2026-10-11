# AAD AI Context Changelog

这里只记录影响结构、实现、实验流程或 AI_CONTEXT 的重要变化；细节以 Git diff 和原始实验记录为准。

## 2026-09-10 — 重要变化

- 建立九文件 `AI_CONTEXT/`，作为 ChatGPT 从 GitHub 快速恢复项目状态的入口。
- 重写长期 `AGENTS.md`，固化 Research Engineer 角色、科研决策边界、冲突停止规则、Context Consistency Check、验证与自动 commit/push 规则。
- 当前代码、入口、测试、索引和证据目录统一为阶段化命名；旧编号材料保留在 archive/history。
- 研究者明确批准 pNEUMA 前车推断与人工复核退役，当前只保留城市运动学校准职责。
- 项目文档校验器开始检查 AI_CONTEXT 文件集合、必需主题和严格 Git 跟踪状态。

## 2026-10-10 任务 1.4

依据真实全量字段证据修复 Lankershim 时钟/帧序列身份口径；记录级冲突传播到诊断段，事件同时检查前后车和完整观测。保留原始候选及拒绝原因；全量重跑与 US-101 回归、便携证据和报告同步。任务 1 建议工程验收，科研规则未冻结。

## 2026-10-10 任务 1.5

前车匹配显式隔离诊断时钟和 Frame_ID；显式时钟缺失或与 `Global_Time - 100*Frame_ID` 冲突时标记不可观测/冲突，不猜测匹配；完全没有诊断字段的历史调用保留兼容路径。新增独立匹配审计，r4 全量回归与 US-101/Lankershim 核心测量和事件数无变化。

## 2026-10-10 任务 2

新增 NGSIM 任务 2 描述性审计入口，复用任务 1.5 state 和事件实现，输出质量状态、有限值分布、极端记录、连续性摘要和 TTC×持续时间敏感性网格；不冻结科学规则或 Stage 0.2 Gate。

## 2026-10-10 任务 2.1

新增固定种子极端/阈值/普通案例复核入口；447 个案例完成独立前车匹配和 TTC/DRAC 重算，生成局部 follower/leader Parquet 和案例图册。自动分类仅作诊断标签，人工物理真实性仍待研究者复核。

- 2026-10-11：任务 2.2.1 连续风险最终修复；统一前向边界语义和完整风险掩码段统计，固定 447 案例与 48 案例包生成 r9 产物。

- 2026-10-11：任务 2.3 生成全量质量、S0/S1/S2 稳健性、暴露候选和科学决策矩阵；正式事件规则差异待研究者裁决。

- 2026-10-11：任务 2.4 完成正式事件提取逐事件等价性验证、S1 真实质量条件重跑、S2 极端观测压力测试和严格连续暴露候选分母；5,381 正式事件与独立结果完全对应，科学规则保持未冻结。

- 2026-10-11：任务 2.5 完成文献证据、6×4 阈值/持续时间联合分析、事件确认时刻、非插值采样敏感性和 24 个真实案例定向复核材料；所有规则保留为 Proposal，未冻结科学参数。


- 2026-10-11：任务 2.5.1 完成 P1/P2/P3 成员级事件对应、24 案例新图册、实际观测确认时刻、rejected 联接修复、极端压力诊断和公平采样状态；P1/P2/P3 仍为 Proposal。


- 2026-10-11：任务 2.5.2 完成中心事件/附近事件区分、P2-only/P3-only/确认时刻差异案例和新图册；P2 未获得唯一科学优先证据。


- 2026-10-11：归档研究者确认的 Stage 0.2 风险事件、连续风险聚合、tau 校准和限定验收设计；新增 tau/P2 独立核定产物，明确实现冲突和未决参数。


- 2026-10-11：完成 rho 时间尺度合理性诊断；报告 tau/2、tau、2tau、TTC 分箱风险贡献和极端压力，不修改 tau 或正式 pipeline。

## 2026-10-11 Formal risk measurement

Added isolated formal measurement interface/config, P2 event revalidation, contribution/status fixture audit, temporal semantics audit, and four unit tests. No production default or historical artifact was overwritten. Automatic GitHub project-integrity workflow was archived and disabled in commit 4deb43d.
