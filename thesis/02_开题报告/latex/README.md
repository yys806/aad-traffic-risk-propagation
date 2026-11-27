# 开题报告 · LaTeX 工程（AAD 毕设）

课题：**面向未来混合自动驾驶环境的风险传播机理研究**（取自 2027 届任务书定稿）
学生：禹尧珅 2352396 ｜ 学院：电子与信息工程学院 ｜ 专业：人工智能 ｜ 指导教师：李王明卉

## 这份工程是什么

把学校 2027 届官方 Word 模板（`2毕业设计(论文)开题报告.doc`）**逐项量测后**在 LaTeX 里重建，
不是「看起来像」，而是按官方 PDF 的坐标对齐。对齐结果见下表（全部单位 pt，A4 595.32×842.04）：

| 项 | 官方 Word | 本模板 | 差 |
|---|---|---|---|
| 校名图顶 / 高 | 127.6 / 49.2 | 127.6 / 47.9 | 0 |
| 大标题 y（36pt 黑体） | 196.0 | 195.6 | 0.4 |
| 课题名称标签 y | 336.4 | 336.4 | 0 |
| 信息表五条底线 y | 353.0 / 395.8 / 438.8 / 481.6 / 524.6 | 353.5 / 396.4 / 439.2 / 482.1 / 524.9 | ≤0.5 |
| 标签列 x / 值列 x | 116.3 / 204.2 | 116.9 / 204.5 | ≤0.6 |
| 「学号」标签 x | 291.6 | 291.0 | 0.6 |
| 底部年月日底线 y | 708.9 | 708.9 | 0 |
| 正文一级标题 y / 字号 | 73.5 / 14pt 黑体 | 73.5 / 14pt | 0 |
| 说明性小字 | 9pt 宋体、缩进 0.635cm | 同 | — |

## 两个主文件（别搞混）

| 文件 | 字体集 | 用在哪 |
|---|---|---|
| `main.tex` | `fontset=noto`（Noto Serif/Sans CJK） | **Overleaf 上改稿 + 预览**。Overleaf 预装，加载快。 |
| `main-windows.tex` | `fontset=windows`（宋体/黑体） | **定稿交学校的 PDF**，在本地编。Overleaf 上没有宋体/黑体，会编译失败，别选它。 |

字体集的三个坑，都实测踩过：

- **fandol**（模板自带默认）只覆盖 GB2312，「珅」缺字形，姓名显示方框。
- **arphic**（文鼎 AR PL UMing）字形齐全，但字体文件大，Overleaf 上加载极慢，
  连续三次编译超时（日志停在加载字体那行）。已弃用。
- **noto** 是 Overleaf（Ubuntu）预装的，覆盖完整、加载快，远端实测 122.5 KB / 5 页一次编译通过，
  `禹尧珅` 三个字齐全、无缺字符。

代价是字形与宋体略有差异 —— 只影响预览，不影响定稿。

## 本地编译

```
cd D:/shen/TJU/AAD/thesis/02_开题报告/latex
latexmk -xelatex main-windows.tex     # 定稿 PDF
latexmk -xelatex main.tex             # 与 Overleaf 一致的预览版
```

## 目录

```
main.tex / main-windows.tex   两个主文件
chapters/metadata.tex         封面信息（学院/专业/姓名/学号/题名/导师）——改这里
chapters/proposal_body.tex    正文四节（一、课题背景 二、方案介绍 三、参考文献 四、审核意见）
style/tongjithesis.cls        文档类（封面几何、标题、审核框、信息表都在这里）
style/font/tongji-cjk-font-*.def  各字体集定义
figures/tongji.pdf            封面校名图
```

## 正文结构（学校 2027 届新版，四节固定）

- 一、毕业设计（论文）课题背景 → 1．选题背景与研究意义 ／ 2．国内外研究现状（文献综述）
- 二、毕业设计（论文）方案介绍 → 1．主要研究内容 ／ 2．研究方案 ／ 3．工作进度安排
- 三、毕业设计（论文）主要参考文献（GB/T 7714-2025 著录）
- 四、审核意见（导师、专业负责人填，学生**不写**）

## 学校原件在哪

`D:/shen/TJU/AAD/thesis/00_学校原件/`（8 份官方 Word + 教务处通知原文），**只读**，
要用就复制出去改，不要动原件。

## 在 Overleaf 上改稿（工作流）

Overleaf 项目「AAD-开题报告」，项目 ID `6b084c4b691e5b6f950a9514`。
主文件是 `main.tex`（arphic 字体），编译器已设为 **XeLaTeX**（项目默认的 pdfLaTeX 排不了中文）。

两条铁律：

1. **`latexmkrc` 不能改名成 `.latexmkrc`**。Overleaf 不读隐藏配置，改名后立刻报
   `File 'tongjithesis.cls' not found`——因为 cls 在 `style/` 子目录，
   XeLaTeX 默认不去子目录找，必须靠 `ensure_path('TEXINPUTS','./style//')` 追加路径。
   追加要用 `ensure_path`，不能写 `$ENV{TEXINPUTS}=...`，那会把 TeX 自己的搜索路径覆盖掉。
2. **定稿别在 Overleaf 上出**。Overleaf 没有宋体/黑体，字体集只能用替代品。
   定稿回本地跑 `latexmk -xelatex main-windows.tex`。

本地与 Overleaf 同步用 olcli：
`node D:/hermes/node/node_modules/@aloth/olcli/dist/cli.js push <本地目录> --project 6b084c4b691e5b6f950a9514 --all`

## 改哪个文件

- 改学院/专业/姓名/学号/题名/导师 → `chapters/metadata.tex`
- 改正文内容 → `chapters/proposal_body.tex`
- 改版式（间距、字号、表格） → `style/tongjithesis.cls`

## 当前进度：骨架已搭好，正文未填

`chapters/proposal_body.tex` 现在是**框架**，不是成稿：

- 四节结构与两级标题完全照官方模板；
- 每个小节下用灰色 `【待写】` 标出「这一段要写什么」，共 27 处；
- 技术路线图用 `\tjformfigslot` 留了图位框；
- 参考文献只留位置，没有编造条目。

清理命令（成稿前必须跑，两条都应为 0）：

```
grep -c 'tjformslot\|tjformfigslot' chapters/proposal_body.tex
grep -c 'tjformnote' chapters/proposal_body.tex
```

## cls 里新增的三个排版件

| 命令 | 干什么 | 依据 |
|---|---|---|
| `tjformbody` 环境 | 正文段落：宋体小四、首行缩进 2 字符、段前后各 0.5 行 | 官方说明文字；段前后 0.5 行按 18pt 基线折算为 9pt，属推算值（官方 .doc 无正文段落可实测） |
| `tjformslot{…}` | 灰色【待写】占位标记，成稿删 | 仅搭骨架用 |
| `tjformref{…}` / `tjformrefs` 环境 | 参考文献悬挂缩进 0.74 cm | 模板原文规定 |

## 字体核对：与官方 Word 逐 span 一致（2026-11-27 实测）

判据不是肉眼看，是把官方 PDF 与我方 PDF 里每个文字 span 的 `字体名 + 字号` 抓出来做**集合比对**。

| | 官方 Word 导出 PDF | 定稿 PDF（main-windows.tex） |
|---|---|---|
| 字体族 | SimHei / SimSun / TimesNewRomanPSMT / TimesNewRomanPS-BoldMT | **完全相同，一个不多一个不少** |

逐项对应关系（官方 .doc 用 Word COM 逐字符读 `Font.Name / NameAscii / NameFarEast` 得到）：

| 部位 | 中文 | 英文与数字 | 字号 |
|---|---|---|---|
| 封面大标题「毕业设计(论文)开题报告」 | 黑体 | 括号「(」「)」**是宋体**（三者 NameAscii 全为宋体，不是 Times） | 36 pt |
| 封面信息表标签与值 | 宋体 | Times New Roman | 14 pt |
| 一级标题（一、二、三、四） | 黑体 | Times New Roman | 14 pt |
| 二级标题（1．2．3．） | 黑体 | Times New Roman | 12 pt |
| 正文 | 宋体 | Times New Roman | 12 pt |
| 说明小字 | 宋体 | Times New Roman | 9 pt |
| 参考文献说明 | **宋体伪粗**（不是黑体） | Times New Roman **Bold** | 12 pt |

### 两个必须知道的坑

1. **`times=true` 必须开**。模板默认走 `newtx`，英文与数字用 TeX Gyre Termes —— 与 Times 度量兼容但**不是同一个字体**，字体名一比就露。
   本机 `main-windows.tex` 已加该选项；开它之后字体度量变化会把封面整体顶偏 2–3 pt，
   故 `ctitlegap` 24.1→22.3、`cbodygap` 93.6→98.0 已同步重校（大标题、首行标签均精确回到官方坐标）。
2. **标题括号与参考文献说明不能用默认设置**。xeCJK 默认把 ASCII 括号码归西文字体，直接用 `(` 会变成 Times；
   模板又把宋体的 BoldFont 设成 SimHei，`\bfseries` 会让「宋体粗」变成黑体。两处都已在 cls 里单独处理。

## 编译速度（2026-11-27 实测，解决“卡住编不出来”）

| 场景 | 耗时 |
|---|---|
| Overleaf 冷编译（改一个字触发重编） | **9.7 / 10.1 / 10.5 / 10.6 秒**（四次） |
| 本机 clean + 全量编译 | 约 40 秒 |

快的两个前提，别动：

- `latexmkrc` 里 `$max_repeat = 2`、`$bibtex_use = 0`、`$biber = ''`。这份文档没有目录、交叉引用和 .bib，
  两轮就稳定；默认设置会反复重跑到「日志不再变」，在 Overleaf 上白白多等几十秒甚至被判超时。
- 字体集用 **noto**，不要用 arphic。arphic（文鼎 AR PL UMing）字形齐全但字体文件大，
  Overleaf 上连续三次编译超时，日志就停在加载该字体那行。

## 定稿工作流（重要）

Overleaf 上编出来的是 **Noto 字体**，与宋体黑体不同形。所以：

1. 在 Overleaf 上改内容（快、随时能看）；
2. 拉回本地：`olcli pull 6b084c4b691e5b6f950a9514 <目录>`；
3. 本机编 `main-windows.tex` 出定稿 PDF；
4. **交学校的必须是第 3 步这份**。

在线版与定稿版的实测差：x 坐标基本一致，y 方向整体差 1–2 pt（字体度量不同）。

### 排查陷阱：首行缩进「测出来只有 18pt」是假象

骨架里 `\tjformslot` 的文字都以「【待写】」开头，量 PDF 会看到首行 x0 = 107.95（左界 89.9 + **18.05**），
像是缩进只做了 1.5 字符。**这不是 bug**：`\parindent` 确实是 2em = 24.09pt（编译期 `\typeout` 已证），
是 xeCJK 的**行首标点挤压**把全角「【」向左挪了约 6pt。

验证方法：写一段以普通汉字开头的 `tjformbody`，量得 x0 = 113.86 = 89.86 + 24.0，正好 2 字符。
正式正文不会以「【」开头，所以不受影响。**以后再看到 18pt 别去改 `\parindent`。**
