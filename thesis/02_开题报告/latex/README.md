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
| `main.tex` | `fontset=arphic`（文鼎 AR PL UMing + FandolHei，TeX Live 自带） | **Overleaf 上改稿 + 预览**。本地也能编。 |
| `main-windows.tex` | `fontset=windows`（宋体/黑体） | **定稿交学校的 PDF**，在本地编。Overleaf 上没有宋体/黑体，会编译失败，别选它。 |

为什么不用大家都熟的 fandol：fandol 只覆盖 GB2312，「珅」这类 GBK 字缺字形，姓名会显示方框。
arphic 覆盖 GBK，「珅」正常显示（实测远端 PDF 里 `禹尧珅` 三个字齐全）。
代价是明体字形与宋体略有差异 —— 只影响预览，不影响定稿。

两版实测差：x 坐标完全一致，y 方向整体差约 1.8 pt（字体度量不同），在允许范围内。

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
