# 开题报告 · LaTeX 工程（AAD 毕设）

课题：**面向未来混合自动驾驶环境的风险传播机理研究**
学生：禹尧珅 2352396 ｜ 学院：电子与信息工程学院 ｜ 专业：人工智能 ｜ 指导教师：李王明卉

## 怎么编（唯一的操作方法）

**就编 `main.tex` 这一个文件，用 XeLaTeX。**

- 编辑器（TeXstudio / VS Code / TeXworks 等）：打开 `main.tex`，编译器选 **XeLaTeX**，直接点编译即可。
- 命令行：`latexmk -xelatex main.tex`，或 `xelatex main.tex` 连跑三遍。

不需要配任何搜索路径、不需要改环境变量——`main.tex` 开头那段 `\input@path` 已经把 `style/` 和 `style/font/` 告诉了 TeX。

## 目录（2026-11-27 清理后只剩这些）

```
main.tex                     唯一源文件：封面信息 + 正文，全在这里
main.pdf                     编译产物（最近一次）
latexmkrc                    编译配置（XeLaTeX、不碰 bibtex）
README.md                    本文件
figures/tongji.pdf           封面校名图（文档类引用，别删）
style/tongjithesis.cls       文档类：封面几何、标题、审核框、信息表
style/tongjithesis.cfg       文档类配置
style/tongji-circled.def     带圈数字（二级标题用）
style/font/tongji-cjk-font-*.def   各字体集定义（现在只用 windows 那个）
```

中间文件（`.aux .log .xdv .fls .synctex.gz` 等）已经清空，编一次会自动生成一套，可以随时删。

## 改哪里

- 封面信息（学院/专业/姓名/学号/题名/导师）→ `main.tex` 上部 `\school` `\major` `\student` 那一段
- 正文内容 → `main.tex` 里 `\MakeDocument` 之后
- 版式（间距、字号、表格、审核框）→ `style/tongjithesis.cls`

## 当前进度：骨架，正文未填

`main.tex` 是**框架**不是成稿：

- 四节结构与两级标题完全照官方 2027 届模板；
- **25 处 `【待写】`**（`\tjformslot`）标出每段该写什么；另有 **1 个图位**（技术路线图，还没画）；
- 参考文献只留位置，没有编造条目。

成稿前必查（两条都应为 0）：

```
grep -n 'tjformslot\|tjformfigslot' main.tex
grep -n 'tjformnote' main.tex
```

⚠️ 上面两条 grep 会把文件开头注释里的同名字符串也算进去，实际数比显示值多 2，属正常。

🔴 **防泄露（导师 2026-11 微信要求）**：正文不得写 AAD 论文未公开的核心创新点——消息可达性判据的具体定义、H1–H4 因果识别框架、十四类消息生命周期分类、区域风险聚合的具体公式、现有量化结论。只写研究问题、技术路线、公开指标。

## 与官方 Word 的一致性（2026-11-27 实测）

判据是把官方 Word 导出的 PDF 与我方 PDF 里每个文字 span 的「字体名 + 字号」抓出来做集合比对，不靠肉眼。

| 项 | 官方 Word | 本工程 |
|---|---|---|
| 字体族 | SimHei / SimSun / TimesNewRomanPSMT / TimesNewRomanPS-BoldMT | **完全一致，一个不多一个不少** |
| 大标题 y（36pt 黑体） | 196.0 | 196.0 |
| 课题名称 y / x | 336.4 / 116.3 | 336.4 / 116.9 |
| 底部年月日底线 y | 708.9 | 708.9 |
| 标签到下划线间距 | 16.6 | 16.4 |
| 信息表行间距 | 42.8–43.0 | 42.8 / 42.8 / 42.9 |
| 页边距 | 左右 89.9、版心宽 415.6 | 同 |
| 首行缩进 | 2 字符 | 24pt（= 2 × 12pt） |
| 说明小字 | 9pt、缩进 0.635cm | 同 |

用空标题实测的结果；填上真实 21 字题名后题名折两行、信息表整体下移一行，属内容长度而非版式误差。

## 五个坑（都实测踩过，别再踩）

1. **`main.tex` 开头的 `\input@path` 不能删**。删了 TeX 找不到 `style/tongjithesis.cls`，报 `File 'tongjithesis.cls' not found`。
2. **`times=true` 必须开**。不开会回退到 TeX Gyre Termes，看着像 Times 但**不是同一个字体**，字体名一比就露。
   开它之后字体度量会变，`ctitlegap` 22.3 / `cbodygap` 98.0 是按开它之后重校过的，别照旧值调。
3. **封面大标题的括号是宋体，不是 Times**。官方 `.doc` 逐字符读过，`(` `)` 的 NameAscii 也是宋体；xeCJK 默认把 ASCII 括号码归西文字体，cls 里已用字符类声明单独处理。
4. **参考文献那段灰字是 12pt 宋体伪粗，不是 9pt 黑体**。模板把宋体 BoldFont 设成了 SimHei，直接 `\bfseries` 会变成黑体，cls 里用 AutoFakeBold 单独做，命令是 `\tjformrefnote`。
5. **`latexmkrc` 里不要限制编译轮数**。从零开始编需要三轮才稳定，限死两轮会报 `xelatex needed too many passes`（当初为 Overleaf 超时限制过，Overleaf 已不用了）。

### 排查陷阱：首行缩进「测出来只有 18pt」是假象

占位符都以「【待写】」开头，量 PDF 会看到首行 x0 = 107.95（左界 89.9 + **18.05**），像只缩进 1.5 字符。
**不是 bug**：`\parindent` 确实是 2em = 24.09pt（编译期 `\typeout` 证过），是 xeCJK 的**行首标点挤压**把全角「【」左移了约 6pt。
用普通汉字开头的段落实测 x0 = 113.86 = 89.86 + 24.0，正好 2 字符。**以后再看到 18pt 别去改 `\parindent`。**

## 交付

编译出的 PDF 复制到 `../交付/` 下。学校 1 系统的上传框接受 **doc / docx / pdf 任一**、单文件 ≤10MB；
导师意见与签名由系统在审核通过后自动带出，学生不填第四节。
