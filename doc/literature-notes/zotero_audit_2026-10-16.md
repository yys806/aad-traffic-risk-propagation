# Zotero AAD 文献库审计（2026-10-16）

> 审计接口：Zotero 7 本机 HTTP API（`http://localhost:23119`，只读 GET；未使用、也未改动任何 Zotero 数据库文件）。
> 审计范围：`TJU → AAD` 集合（集合 key `TGJP2TIA`）及全部子集合；生成时间 2026-10-16T08:26:47Z。
> 本文件为轻量审计摘要；条目以 Zotero item key 追踪，可复核、可撤销。不导出 PDF、批注或私人笔记。

## 1. 实际结构与数量

| 集合 | key | 条目数 |
|---|---|---|
| TJU → AAD（根，直接条目） | TGJP2TIA | 0（无未分类） |
| 01_风险事件与安全指标 | NXNARCWW | 6 |
| 02_混合自动驾驶传播与控制 | P4SI7DRD | 11 |
| 03_闭环仿真与场景测试 | 9CM9ATK9 | 7 |
| 04_人类行为交互与轨迹预测 | 8PR6RF36 | 3 |
| 05_非局部风险与因果验证 | WCC9X92Q | 23 |
| NC_统一汇总 | ARY6BQCW | 6 |

- 唯一文献条目：**56**（全部为期刊论文 journalArticle；每条恰属一个子集合）。
- AAD 根集合无未分类条目；无条目同时挂多个子集合。
- 核心元数据完整度：56/56 条均具备 DOI、正式题名、第一作者、年份、期刊名，且均有 ≥1 个 PDF 附件（本机存储核对依赖历史 md5 校验记录）。
- 标签：全部 56 条含 `AAD` 与 `imported:2026-10-16`；6 条含 `NC`。

## 2. 发现的问题

1. **`05_非局部风险与因果验证` 过载且主题混杂**（23 条 = 全库 41%）：混装三类内容——非局部交通流模型（8）、量子非定域/量子决策/量子因果理论参照（13，即“类超距”理论来源）、因果发现方法（Runge 2019）与 1 条车队级联风险测量（Luo 2026，主题上更接近 01）。
2. **`NC_统一汇总` 是期刊维度集合，与主题维度不一致**：仅含 6 条 NC 论文且都未挂主题子集合；而库内另有 5 条 Nature Communications 论文只挂在主题集合。期刊维度造成组织标准不统一（旧本地目录曾要求 NC 论文双挂，Zotero 现状未双挂）。
3. **跨项目重复条目（真实重复，非多集合挂载）**：7 篇论文在 AAD 与 DRIFT 集合中各存在一个独立 Zotero 条目（相同 DOI、不同 item key），见 §4。
4. **04 子集合偏薄**（3 条），与文献实际分布一致，暂不需处理。
5. **CCF/影响因子**：核心元数据完整；项目 xlsx 总表记录有各刊影响因子及检索来源（检索日期 2026-07-16），未在本次审计中重新联网核验，当前值一律视为 `Unverified`（2026-10-16），刷新流程见 README。

## 3. 推荐分类体系（需研究者批准后执行）

原则：保留 01–04；把 05 拆为“非局部交通流模型”与“类超距与因果理论”；退役期刊维度的 `NC_统一汇总`（保留 `NC` 标签追踪期刊来源）。调整后仍为 6 个主题子集合，一层结构，不新增层级。

| 新集合 | 内容 | 调整后条目数 |
|---|---|---|
| 01_风险事件与安全指标 | 不变 + Luo 2026 车队级联风险测量 | 7 |
| 02_混合自动驾驶传播与控制 | 不变 | 11 |
| 03_闭环仿真与场景测试 | 不变 | 7 |
| 04_人类行为交互与轨迹预测 | 不变 + Kolekar 2020 | 4 |
| 05_非局部交通流模型 | 原位更名：非局部/前瞻交通流、激波、网络交通流 | 11 |
| 06_类超距与因果理论 | 新建：量子非定域、量子决策、量子因果、因果发现、网络失效传播理论 | 16 |

### 逐条调整对照表（item key 可追踪、可撤销）

| item key | 年份 | 第一作者 | 题名（截断） | 原集合 | 建议新集合 |
|---|---|---|---|---|---|
| C5CMBLYV | 2026 | Luo | Enhancing vehicle platoon safety assessment: A novel casca… | 05_非局部风险与因果验证 | 01_风险事件与安全指标 |
| 9XZTIZ2S | 2020 | Kolekar | Human-like driving behaviour emerges from a risk-based dri… | NC_统一汇总 | 04_人类行为交互与轨迹预测 |
| ACHCD2XZ | 2024 | Chiarello | A non-local traffic flow model for 1-to-1 junctions with b… | 05_非局部风险与因果验证 | 05_非局部交通流模型 |
| 2ST8W9E7 | 2024 | Coclite | A nonlocal lagrangian traffic flow model and the zero-filt… | 05_非局部风险与因果验证 | 05_非局部交通流模型 |
| 2T5ZPT7R | 2026 | Colombo | Coexisting automated and human-driven vehicles: Well-posed… | 05_非局部风险与因果验证 | 05_非局部交通流模型 |
| VSH9Q4PG | 2022 | Friedrich | Network models for nonlocal traffic flow | 05_非局部风险与因果验证 | 05_非局部交通流模型 |
| ZTEPXKBA | 2022 | Huang | Stability of a nonlocal traffic flow model for connected v… | 05_非局部风险与因果验证 | 05_非局部交通流模型 |
| DFAFL48E | 2026 | Hui | An anisotropic traffic flow model with look-ahead effect f… | 05_非局部风险与因果验证 | 05_非局部交通流模型 |
| VIPIJ222 | 2020 | Sun | On a class of new nonlocal traffic flow models with look-a… | 05_非局部风险与因果验证 | 05_非局部交通流模型 |
| Q65YUJ89 | 2026 | Zhang | Physics-informed graph modeling for traffic shockwave anal… | 05_非局部风险与因果验证 | 05_非局部交通流模型 |
| 5DE6L9RS | 2023 | Duan | Spatiotemporal dynamics of traffic bottlenecks yields an e… | NC_统一汇总 | 05_非局部交通流模型 |
| ANN7E2VL | 2021 | Hamedmoghadam | Percolation of heterogeneous flows uncovers the bottleneck… | NC_统一汇总 | 05_非局部交通流模型 |
| YA2ACMZV | 2020 | Saberi | A simple contagion process describes spreading of traffic … | NC_统一汇总 | 05_非局部交通流模型 |
| 8TGYGMNC | 2017 | Allen | Quantum common causes and quantum causal models | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| L6DLWJRL | 2017 | Asano | A quantum-like model of selection behavior | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| M2S823IP | 1964 | Bell | On the einstein podolsky rosen paradox | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| U9X6T495 | 2014 | Brunner | Bell nonlocality | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| XLY3WEK4 | 2006 | Busemeyer | Quantum dynamics of human decision-making | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| 6K5N6XDR | 2016 | Costa | Quantum causal modelling | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| QL5UQZWU | 2018 | Giarmatzi | A quantum causal discovery algorithm | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| HK4HMBLF | 2015 | Hensen | Loophole-free bell inequality violation using electron spi… | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| 5I4RXXWY | 2013 | Leifer | Towards a formulation of quantum theory as a causally neut… | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| WFHAM457 | 2009 | Pothos | A quantum probability explanation for violations of ‘ratio… | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| 6PUKMHEZ | 2014 | Wang | Context effects produced by question orders reveal quantum… | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| CFAYC4B7 | 2022 | Song | Quantum decision making in automatic driving | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| MV5WEAF6 | 2022 | Song | Research on quantum cognition in autonomous driving | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| N47NR5PG | 2019 | Runge | Detecting and quantifying causal associations in large non… | 05_非局部风险与因果验证 | 06_类超距与因果理论 |
| R52FEKEP | 2021 | Kaiser | Network isolators inhibit failure spreading in complex net… | NC_统一汇总 | 06_类超距与因果理论 |
| BHJHC96X | 2022 | Bao | Impact of basic network motifs on the collective response … | NC_统一汇总 | 06_类超距与因果理论 |

执行方式建议：在 Zotero 中新建 `06_类超距与因果理论`、将 `05_非局部风险与因果验证` 更名为 `05_非局部交通流模型`，按上表移动条目（Zotero 内移动不改变 item key，可随时撤销），完成后删除空的 `NC_统一汇总` 集合。

## 4. 跨项目重复条目（AAD ↔ DRIFT，建议合并，需研究者批准）

| DOI | AAD 条目 | DRIFT 条目 | 题名（截断） |
|---|---|---|---|
| 10.1016/j.trc.2024.104702 | TLXAH3L6 | LQKJGSG4 | Modelling two-dimensional driving behaviours at unsignalis… |
| 10.1109/tits.2024.3431591 | TWCEFISL | 4LZKVS8H | Modeling and robust H ∞ control synthesis of the CAV-HDV h… |
| 10.1109/tits.2024.3384050 | JAEYQ62C | RIC9TNXW | Enhancing safety in mixed traffic: Learning-based modeling… |
| 10.1109/tits.2025.3553697 | J24MWAMC | ZHHNSMRB | Interaction-aware and driving style-aware trajectory predi… |
| 10.1109/tits.2025.3592741 | 7NL3NJ6F | YISH2BAF | TrafficMCTS: A closed-loop traffic flow generation framewo… |
| 10.1109/tiv.2024.3414828 | G4RN4E2L | 5WPWLHBB | An efficient high-risk lane-changing scenario edge cases g… |
| 10.1109/tro.2024.3443504 | HQUD47EN | 3BLAL5X2 | Hybrid system stability analysis of multilane mixed-autono… |

处理建议：对每对条目在 Zotero 中合并（保留元数据较全者，附件合并，双方标签 `AAD`/`DRIFT` 保留或改为多集合挂载）。合并不可由只读接口完成，且涉及附件与笔记归属，须研究者批准后执行。AAD 集合内部无重复条目。

## 5. 元数据与质量状态

- 核心元数据（DOI/题名/作者/年份/期刊）：56/56 完整，未发现明显错误；本次未做修改。
- PDF 附件：56/56 至少 1 个；退役迁移时已做 md5 全量核对（见 README）。
- 影响因子/CCF：以 xlsx 总表为历史来源（检索 2026-07-16）；当前值未重新核验，全部标记 `Unverified`；更新归 Zotero 条目维护流程，不写入本文件冒充最新数据。
- 题名待核对项：1 条含非 ASCII 期刊名（Zeitschrift für angewandte Mathematik und Physik）为正常 Unicode，无需修改。

## 6. 本次已实际执行的修改

**无。** 本机 Zotero 接口仅支持只读读取，且分类调整属于需研究者批准的范围。本审计只读取元数据与结构，未修改任何条目、集合、附件、批注或笔记。

