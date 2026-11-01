# P0 Task 1 文献检索协议

日期：2026-11-01。状态：`Verified`（检索记录已固化；后续 Task 可追加新批次）。

## 范围

AAD 的问题被拆成十个检索方向：交通流/冲击波与瓶颈传播；交通风险传播与安全代理指标；非局部交通流与控制；V2V/V2X 信息传播；BLOS/远端警告；信息流—交通流耦合；网络干扰与因果推断；控制器采用与消息信任；代理指标有效性；仿真—现实验证。

## 检索式与来源

| 批次 | 主要检索式 | 来源 | 用途 |
|---|---|---|---|
| A | `traffic flow propagation`, `traffic shockwave`, `bottleneck propagation`, `traffic network cascade` | Zotero、Nature、Crossref、出版社 | 物理传播基准 |
| B | `traffic risk propagation`, `conflict propagation`, `spatiotemporal risk`, `surrogate safety measures` | Zotero、TRC、A&A&P、AMAR | 风险定义与测量 |
| C | `nonlocal traffic flow`, `look-ahead control`, `connected vehicle zone of influence` | Zotero、SIAM、PLOS、TRID | 非局部控制和作用边界 |
| D | `V2V information propagation`, `information flow propagation wave`, `vehicular information diffusion` | arXiv、IEEE/Elsevier、作者页面 | 信息链传播 |
| E | `beyond-line-of-sight warning`, `remote hazard awareness`, `V2X warning causal effect` | ScienceDirect、A&A&P、TRF | 控制器/驾驶员采用与动作 |
| F | `coupled vehicle and information flows`, `dual-layer propagation network` | Physica A、IEEE/Elsevier | 信息—物理耦合最近邻 |
| G | `causal inference network interference`, `spillover`, `exposure mapping`, `partial interference` | JASA、Annals、JMLR、PMC | 因果识别与干扰 |
| H–J | `controller adoption`, `message trust`, `TTC validation`, `simulation calibration`, `trajectory validation` | Zotero、FHWA、TRC、SUMO proceedings | 机制闭环与适用域 |

外部检索核验的代表性正式来源包括：Schönhof 等（Physica A, DOI `10.1016/j.physa.2006.01.057`）、Wang 等（arXiv `1901.11133`）、Jerath 等（PLOS ONE, DOI `10.1371/journal.pone.0301188`）、Peng 等（A&A&P, DOI `10.1016/j.aap.2026.108642`）、Hudgens & Halloran（JASA, DOI `10.1198/016214508000000292`）和 Aronow & Samii（Annals of Applied Statistics, DOI `10.1214/16-AOAS1005`）。其中 Jerath、Peng、Schönhof、Hudgens、Aronow 和 Wang 冲突图论文的正式元数据已通过 Zotero 本机 DOI 导入；Aronow 与 Jerath 获得了 Zotero PDF 附件。Wang 冲突图论文已有 AAD 条目，导入时产生的重复记录已打上 `P0/DUPLICATE_OF_5LYN24YV`，未合并或删除。

## 筛选和饱和

先审计现有 Zotero，再按最近邻、引用网络和 2024–2026 更新进行补检。停止条件不是文献数量，而是十个方向均已有至少一条可核验主线，新增检索只返回已知方法、重复条目或主题偏离。P0 Task 1 的注册表保留 16 篇代表性候选；未纳入的发现保留在 Zotero 搜索历史或后续 Task。

## 事实边界

出版社摘要和检索摘要用于发现与元数据核验，不能替代全文证据。Zotero 本地附件可读性与本文阅读状态分开记录。对全文不可得的论文，记录 DOI、合法来源和未核验内容，不用其支持强创新结论。
