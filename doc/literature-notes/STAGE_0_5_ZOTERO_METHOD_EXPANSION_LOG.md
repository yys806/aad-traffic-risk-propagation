# Zotero 整理与核验清单（AAD-0.5-METHOD-EXPANSION）

日期：2026-10-20。唯一文献库：Zotero 集合 `TJU → AAD`（本机 API，用户库 18841865）。

## 1. 本次新增（3 条，全部经 DOI 元数据核验）

| 条目 key | 题名 | 出处 | DOI | 集合 | 标签 |
|---|---|---|---|---|---|
| `4J5V4A3I` | Identifiability of car-following dynamics | Physica D **430**:133090 (2022) | 10.1016/j.physd.2021.133090 | `07_微观跟驰校准与轨迹重放` | `AAD/Stage0.5`、`AAD/Method/identifiability`、`AAD/Role/primary-method` |
| `4ABZDRVU` | Calibration of nonlinear car-following laws for traffic oscillation prediction | TR Part C **69**:1-23 (2016) | 10.1016/j.trc.2016.05.018 | `07_…` | `AAD/Method/oscillation-propagation`、`AAD/Role/contextual` |
| `DIVRKX7J` | A simplified car-following theory: a lower order model | TR Part B **36**(3):195-205 (2002) | 10.1016/S0191-2615(00)00044-8 | `07_…` | `AAD/Method/leader-replay`、`AAD/Role/contextual` |

## 2. 上一任务已入库（13 条，本次核对未重复创建）

`07_微观跟驰校准与轨迹重放`（10 条）：`GMF4LZDC`（Brockfeld 2004）、`GSJPFHJK`（Kesting & Treiber 2008）、`ZJGB2X68`（Punzo et al. 2012）、`I4NU8C5G`（Krauss et al. 1997）、`XHLWGAC3`（Krauß 1998 博士论文）、`B8J8W6P2`（Sharma et al. 2019）、`LIUYDEMK`（Schrader et al. 2024）+ 本次 3 条。
`08_拥堵状态识别与时空传播`（2 条）：`5DE6L9RS`（Duan et al. 2023）、`YA2ACMZV`（Saberi et al. 2020）。
`09_仿真校准规范与验证`（1 条）：`IQR7YZBZ`（FHWA-HOP-18-036）。

## 3. 查重与去重记录（Observation）

- 逐条以 DOI 在本地库检索 `qmode=everything`：本次 3 篇的 DOI 在库中**均不存在**，故为新增。
- 上一任务的 8 篇在创建前同样做过 DOI 预检；本次复核集合内容，**未发现重复条目**，未做合并或删除。
- 未触碰研究者既有条目（如 `9XZTIZ2S` Kolekar 2020）的集合归属。

## 4. 元数据核验

| 项 | 状态 |
|---|---|
| 题名/作者/年份/出处/DOI | 全部经 Crossref DOI 记录核验（2026-10-20） |
| 刊名简称 | **未修改**（沿用 Zotero 已有字段；本次未跑 `standardize_abbrev3.py`，避免以未核验值覆盖） |
| 期刊指标/分区字段 | **未新增**（`easyScholar`/CCF 脚本次任务未执行；按规范不得臆造） |
| 页数/卷期 | 按 Crossref 记录写入 |

## 5. 附件处理（Unresolved，必须如实报告）

- 已下载 4 份**合法开放获取** PDF 到本地 `local_research/litpdf/`（该目录**不提交 Git**，符合"不在仓库中另建论文 PDF 库"的规则）：
  `wang2022_identifiability.pdf`、`brockfeld2004_calibration.pdf`、`schrader2024_sumo_in_the_loop.pdf`、`fhwa2019_tat_vol3.pdf`（HTTP 200，字节数已记录）。
- **上传到 Zotero 附件失败**：本机 API 的 `/items/<key>/file` 返回 `HTTP 400 MD5 hash not provided`，即使同时提供附件条目的 `md5` 字段与请求头 `Content-MD5`（含大写/base64 两种形式）仍失败。判断为本机 Zotero 10.0.6 的本地 API 不支持附件文件上传（与 AGENTS.md 中"导入式附件 + 本地 API 写入"的历史描述不一致）。
- 处理：创建过程中产生的 2 个空附件条目已通过带 `If-Unmodified-Since-Version` 的 DELETE 删除（`AS8QEPJ6`、`6QFNRXZJ`，均返回 204），集合内容已复核为 10/2/1 条论文条目，无悬空附件。
- **待研究者操作**：用 Zotero 客户端（浏览器连接器或 `Retrieve Metadata for PDF`）为以下条目挂原文 PDF；链接已记录：
  - Wang 2022 → https://lab-work.github.io/download/wang2021identifiability.pdf （或 arXiv 2103.08652）
  - Brockfeld 2004 → https://elib.dlr.de/6652/1/TRB2004-001743.pdf
  - Schrader 2024 → https://www.tib-op.org/ojs/index.php/scp/article/download/1127/1245/28090
  - FHWA 2019 → https://ops.fhwa.dot.gov/publications/fhwahop18036/fhwahop18036.pdf
- 双语对照 PDF：**未执行**（PDF2zh 流程需要本地服务；本任务未启动），按 AGENTS.md 该步骤为可选增强。

## 6. 全文获取状态（与 `stage_0_5_method_index.json` 一致）

- **全文已读 8 条**：Duan 2023、Saberi 2020、Brockfeld 2004、Schrader 2024、FHWA 2019、Wang et al. 2022、SUMO 1.26 源码、Kolekar 2020 之外的本项目自研模块（不计入文献）。
  实际为：L1、L2、L3、L4、L5、L6（源码）、L13 = **7 篇文献 + 1 份软件源码**。
- **仅元数据核验 11 条**：Kesting 2008、Punzo 2012、Krauss 1997、Krauß 1998、Sharma 2019、Kolekar 2020、Rhoades 2016、Newell 2002 等——**未据其采用任何公式、指标或阈值**。
- 未获取全文的候选（`Full text unavailable`）：Rhoades et al. 2016（TRC 版付费墙，有开放会议版 10.1016/j.trpro.2015.07.002 但本次未读）、Newell 2002、Kesting & Treiber 2008、Punzo et al. 2012、Krauss et al. 1997、Krauß 1998（DLR 记录已核，正文未读）、Sharma et al. 2019。

## 7. 本次 Zotero 操作是否可复核

每次调用都通过本机 API（`http://127.0.0.1:23119/api/users/18841865`）并使用 `Zotero-API-Key` + `Zotero-Server-ID` 头；新建/删除的 item key 已逐条记录在本文件与 `code/scripts/zotero_add_method_expansion_refs.py`/`zotero_add_stage05_method_refs.py` 中，可按 key 直接复核。
