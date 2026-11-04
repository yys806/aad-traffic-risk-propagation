# P5 Task1 设计审计便携证据

Task ID：AAD-P5-TASK1-20261104。日期：2026-11-04。

基线 Git commit：3682de08c411e941dd4340474ae7c7702b3fd2e1；开始工作区 clean。最终任务提交由 Git 历史定位（提交主题 docs(p5): audit causal identification design）；不在提交内容内写入无法自引用的最终 SHA。实际提交和远端同步见任务最终回复及 git log。

## 1. 交付与清单

- [核心设计](../../../docs/research/P5/P5_TASK1_CAUSAL_IDENTIFICATION_DESIGN.md)、[决策登记](../../../docs/research/P5/P5_TASK1_RESEARCHER_DECISION_REGISTER.md)、[最终报告](../../../docs/research/P5/P5_TASK1_FINAL_REPORT.md)。
- source_manifest.json：36 个必要来源的基线 Git blob 与读取时工作区 SHA256。Context 随本任务增加日期导航，来源审计仍绑定基线，不反写历史。
- protected_files.json：601 个既有受保护文件的起始 native 与 Git blob SHA256；覆盖 AGENTS、Formal/P3/P4/P7、正式配置、定义及历史证据。
- method_sources.json：已有 Zotero 历史索引与 6 组定向原始来源的实际访问/阅读范围、失败和版本；不含论文 PDF、原始网页、附件或密钥。
- check_identification_math.py / identification_math_results.json：11 项标准库 Fraction 识别恒等式、非识别反例及界的独立复算；不导入生产代码，不抽随机数。
- environment.json：解释器、平台、基线和执行边界。
- validation.json：影响范围、实际文档/证据检查与限制。
- verify_p5_evidence.py / SHA256SUMS：自包含数学与交付物哈希检查；完整仓库下另验保护字节、来源、定义数量及既有 registry/Gate。

## 2. 数学检查的含义

全部例子为 DETERMINISTIC_IDENTIFICATION_CHECK_ONLY / SYNTHETIC_VALIDATION_ONLY，不是交通实验、参数校准、功效计算或独立样本。

1. p=1/4、τQ=−1/5、τ非Q=1/10、τS0=1/20 给 τS1=1/40、τSC=−1/40，显示 τQ 不能代替交互。数字仅是代数反例。
2. 两个潜在世界的全部可观测四格边际及有源 Q 分布相同，全体交互都为 0；但 Q(1)=1 principal-stratum 交互分别为 −1/2、+1/2。随机化不识别潜在资格耦合。
3. 有界结果的潜在子总体均值界、两臂 ITT 界和四格交互界，以 Fraction 与独立端点枚举复核；识别界不是置信区间。

## 3. 复核方式

完整当前工作区：

~~~powershell
python evidence/research/P5_TASK1_20261104/check_identification_math.py
python evidence/research/P5_TASK1_20261104/verify_p5_evidence.py --repo-root . --view both
~~~

另一平台/检出换行不同的完整 Git 仓库，可用 --view git 检查原 Git blob；该视图不伪装成 native 起始字节检查。软件不会为通过核验改写历史换行。

只带 docs/research/P5 与本证据目录的最小 Git 归档，须按原 Git blob 字节导出。当前环境 core.autocrlf=true 会影响默认 archive，因此导出命令使用单次参数 git -c core.autocrlf=false archive（不改持久 Git 配置或历史 .gitattributes）。在归档根目录运行：

~~~powershell
python evidence/research/P5_TASK1_20261104/verify_p5_evidence.py --repo-root . --package-only
~~~

package-only 仅核验便携交付哈希与数学例子，不能核验不存在的源文件/历史 Git 对象。SHA256SUMS 绑定原始字节；完整检出时如工作区换行变化，允许验证精确的已提交 blob，不采用模糊换行归一化。方法网站的 retrieval SHA 仅标识当时下载版本，未来网站内容变化不应重写本次审计。

## 4. 边界与失败记录

本任务只写文档、设计审计证据和项目导航；没有运行 SUMO/TraCI/Pilot/V、使用 seed、读取 holdout、采集数据、修改生产代码/参数/schema/定义/Overleaf。没有因果效果估计。

本机 Zotero AAD 只读 API 请求失败，未核验 live 库数量；出版社方法页遇阻，改用作者 arXiv；NBER 扫描稿未获得可检索正文，IV 条件用作者书相关页核对，不称精读原论文。过程中的一次输出编码错误发生在 metadata 已保存后；另一次工具输入语法错误未执行命令，随后修正。

首次最小 Git archive 核验失败：默认 core.autocrlf=true 将13个已绑定LF文件导出为CRLF。workspace与index原字节相同，失败在archive视图；未修改旧文件或永久配置。改用上述单次参数后重新核验，原失败归档保留在忽略的 code/outputs/audits/p5_task1_20261104/portable_preview_01。失败原因及最终结果登记于 validation.json，不伪装为首次全绿。以上均不是交通运行/实验失败，也未产生科研样本。

P4 的 172 测试和 15 数学检查为引用的历史事实，本任务不重跑。新增数学反例只验证推导，不证明假设成立。Formal A/独立 Qualified 仍为 0；真实完整区域 Y、F0、因果机制和总体时间优先性仍 Unknown/Blocked。新设计均 Proposal/Awaiting，待研究者审阅后决定；本任务到此停止。
