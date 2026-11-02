# Hall — 宏观交通测量补充说明

Fred L. Hall. Traffic Stream Characteristics. *Traffic Flow Theory*, Chapter2，FHWA官方文件：https://www.fhwa.dot.gov/publications/research/operations/tft/chap2.pdf 。下载38页；SHA256 f448a402f846768bbdae8f673120fae782fed98f257ce30bec1bc6c0fb2584a6。Zotero26RQQ7EE。出版年份本轮未验证，不猜1997/2001。状态PARTIAL_READ：引言及§2.1–2.2测量定义；后半基本图模型综述未精读。Edie1963原文未取得，不能宣称其原文已读。

研究问题：交通量的定义与测量支持如何影响速度、密度和流量解释。点流量是指定时间内过点车辆数/时间；密度要求空间支持。§2.2.2比较point/time mean、全区瞬时空间车辆均速，以及时空矩形中总行程/总驻留时间，明确部分穿越车辆的贡献不能任意删除。点样本速度调和均值在速度随位置变化时不自动等同给定区段行程速度。§2.2.3提醒不同空间/时间支持下机械套q=ku可导致误导。

AAD推荐：采用明确同域的Edie型q_A=Σd_i/|A|、k_A=Σt_i/|A|、u_A=Σd_i/Σt_i（Proposal），轨迹裁切保留入口/出口部分，lane与单位显式。q=ku在这一共同构造下是代数关系，不能把任意其他观测的q/k/u混乘。k=0时u未定义；缺轨迹不补零。完整瞬时空间普查均速可另作snapshot macro量，不能称任何算术均值都无意义。

本章是测量理论解释，不含AAD阈值、物理到达真值或随机no-message实证。不将章节背景当作现实AAD有效性验证；技术章无期刊指标，未做机器双语译文。定义细则见DEF-PHY-009，微宏层关系见DEF-PHY-010。
