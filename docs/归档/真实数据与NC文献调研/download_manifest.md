# 2026-08-12 下载与来源清单

状态说明：`完整`表示文件已经写入本地并通过格式或压缩包目录检查；`说明已取得`表示已取得官方元数据/手册，但原始大包尚未完整下载；`待申请`表示官方要求人工申请，未绕过访问控制。

## 数据集

| 数据集 | 本地状态 | 已取得内容 | 官方规模/访问条件 | 当前用途边界 |
|---|---|---|---|---|
| NGSIM | 完整 | US-101、I-80、Lankershim、Peachtree 四个轨迹与配套 ZIP，四份元数据 PDF，算法与报告 ZIP，5 行 API 样本 | 四个场景包合计 1,004,994,059 B；USDOT 公共下载 | 可做 TTC、物理传播和跨道路场景验证；无消息发送、接收或采用字段 |
| SPMD | 关键接收表已取得 | USDOT 两份手册、数据页 JSON、ZIP64 目录、`RV_RX` 接收表及 4 个摘要/索引 ZIP | 完整 `SPMD.zip` 为 117,346,016,961 B；已用 Range 请求选择性下载关键成员 | `RV_RX` 可支持接收可达性和远车状态流；逐消息时延/丢包仍需 `Packet` 与发送侧表；无采用字段 |
| pNEUMA | 最小轨迹样本已取得 | Zenodo 元数据 JSON、README、数据集说明论文，以及 `20181101_d1_0800_0830.csv` | 完整包 15,759,302,461 B，MD5 `4e842b2200bea2f80d41c6b785a9de25`；通过远程 ZIP 目录选择性下载最小轨迹成员 | 样本含 785 条车辆轨迹、1,239,475 个 0.04 s 状态点，可开始轨迹读取与 TTC 可行性检查；无通信生命周期 |
| INTERACTION | 待申请 | 官方格式/访问说明已核验，数据集论文 PDF 已下载 | 官方要求填写申请表并使用高校/单位邮箱，审核后发送下载链接；非商业研究使用且禁止再分发 | 获批后用于合流、换道、环岛及交叉口轨迹验证；无通信生命周期 |

说明：pNEUMA 官方页面目前存在许可表述不一致。Zenodo 记录为 CC BY 4.0，EPFL 专题页和下载页页脚写 CC BY-NC 4.0，下载页 FAQ 又写 CC BY 4.0。在作者或数据托管方澄清前，按更严格的 CC BY-NC 4.0 管理。

## 已完成文件校验

| 相对路径 | 字节数 | SHA-256 |
|---|---:|---|
| `dataset/NGSIM/US-101-LosAngeles-CA.zip` | 327638049 | `830442BB08F1F7A20A686B5879B4B82BFB7C47E526D48908DB666FCCC7E811DC` |
| `dataset/NGSIM/I-80-Emeryville-CA.zip` | 441781993 | `B274BB96F20C971E37651E73CA0F86677FDA8009E22885E71322716ECA84FF73` |
| `dataset/NGSIM/Lankershim-Boulevard-LosAngeles-CA.zip` | 184896776 | `757C693BA72B7C8BA7561EE1B5107DFA7119CC4862584A4F033AA445246C56C1` |
| `dataset/NGSIM/Peachtree-Street-Atlanta-GA.zip` | 50677241 | `91B9B1D4ED1D261E8C525DF536ADC466B6844FF49DC6FB08B815C735FE072A2F` |
| `dataset/NGSIM/Algorithms_and_Reports.zip` | 10117981 | `8127783A28B9E4E6D719F3C3FE57E63D07D199455AF572BE9287458FCF6CC396` |
| `dataset/SPMD/Safety_Pilot_Model_Deployment_Sample_Data_Handbook.docx` | 1319936 | `EBA0D61811FC41CF4C8707A21248A88C6BA7B9B675D69DFA1F47972021E4D359` |
| `dataset/SPMD/Safety_Pilot_Model_Deployment_Sample_Metadata_Documentation.docx` | 125863 | `5B1A497FFD9EBB057BB7EF55AE076EB0E5CDFE0BB7846AC44B9259B954263A16` |
| `dataset/SPMD/selected/RV_RX.csv.zip` | 783804721 | `9E5E7A3842B15ADC08366D1AFE098224C912D3C593A70D4BB4071088749AB56E` |
| `dataset/SPMD/selected/BsmP1Summary.csv.zip` | 13177267 | `79F56E13C99EEC1EE35B9FD825A99B164CADF2467BB4264104250DB085968F7D` |
| `dataset/SPMD/selected/DataWsuSummary.csv.zip` | 357100 | `B9D0CBA46578388D00D67B97720ACE054976C7846A84372859262BB25A1DA06C` |
| `dataset/SPMD/selected/PCAPFile.csv.zip` | 654994 | `1CD5958983E019EB02A5D2727F8C812F2E8CF333C5F909B504317EE2C11BE459` |
| `dataset/SPMD/selected/TripFact.csv.zip` | 840157 | `CA269CAFFBEEE303E9EB0AA85C2FD110A17ED9DDAB8F403AA823D7917865B59F` |
| `dataset_papers/INTERACTION_Dataset_2019_arXiv_1910.03088.pdf` | 4587328 | `4CE27487274AF592174D01C1A7CE94B8D81D38CA64E02ACC685C2A70AB003A81` |
| `dataset_papers/pNEUMA_large_scale_field_experiment_2020.pdf` | 23397909 | `28C8571542EC123B907D4812E7706705B1FA01A2A36F317B13B8B78BBB66B617` |
| `dataset/pNEUMA/20181101_d1_0800_0830.csv` | 73509485 | `F9CDE0A3CA5010E2217EA4CBC0BDF26ED87BE1EC0D8C2BE5E2CB93AAC82BA28C` |

四个 NGSIM 场景包和 `Algorithms_and_Reports.zip` 均已用 `tar -tf` 成功读取目录；两篇数据集论文均已用 `pypdf` 完整解析。NGSIM 四份元数据 PDF 和 7 篇 NC PDF 也均已通过 `pypdf` 解析。

## NC 原文

7 篇候选原文均位于 `nc_papers/`，对应文本位于 `nc_text/`。候选 DOI 和核心/参照分组分别见 `nc_candidate_dois.txt` 与 `nc_candidate_matrix.md`。所有 PDF 均来自开放获取渠道，下载时禁用了 Sci-Hub 回退。

## 尚未完成的下载

- SPMD 主包：已验证支持 Range 请求并读取全部 46 个成员目录，避免盲目下载 117 GB。`RV_RX` 和 4 个小型配套表已完成；逐消息识别还需要约 15.33 GB 的 `Packet` 和约 55.72 GB 的 `BsmP1`，是否继续下载应由识别收益与本周时间成本共同决定。
- pNEUMA 主包：已读取远程 ZIP64 目录（222 个成员）并选择性下载最小真实轨迹 `20181101_d1_0800_0830.csv`。完整包仍受服务器限速，不作为本轮完成目标；测速片段已隔离在 `_incomplete_downloads/`，不得当作数据使用。
- INTERACTION 原始数据：必须由课题组成员用正式邮箱提交官方申请。未获下载链接前无法合法取得原始包。

## 下载脚本

`download_datasets.ps1` 使用临时扩展名、精确字节数检查和完成后原子改名，避免半包被误识别为正式数据。该脚本适合 USDOT 中小型附件；pNEUMA 和 SPMD 大包还需要可靠的分块/断点下载器和稳定网络。
