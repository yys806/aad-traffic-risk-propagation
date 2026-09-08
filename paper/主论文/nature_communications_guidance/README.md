# Nature Communications 格式依据

本目录保存 2026-08-12 从 Nature Communications 官方网站下载的格式文件：

- `ncomms-formatting-instructions.pdf`
  - 来源：https://www.nature.com/documents/ncomms-formatting-instructions.pdf
- `ncomms-manuscript-checklist.pdf`
  - 来源：https://www.nature.com/documents/ncomms-manuscript-checklist.pdf

官方投稿页面说明，初投稿不要求专用出版模板；LaTeX 可使用 `article.cls`、`revtex.cls` 或 `amsart.cls` 等标准文档类。因此本项目使用标准 `article.cls`，不使用 Springer `sn-jnl` 冒充 Nature Communications 模板。

当前正文遵循的顺序为：Title、Abstract、Introduction、Results、Discussion、Methods、Data availability、Code availability、References、Acknowledgements、Author contributions、Competing interests、Figure legends、Tables。

关键约束：

- 标题建议不超过 15 个英文单词；最终英文标题另行核对。
- 摘要不含引用，投稿页面当前建议不超过 200 个英文单词；旧格式 PDF 写 150 词，最终以投稿时在线说明为准。
- Introduction 不设子标题，建议少于 1000 词。
- Results 和 Methods 使用不编号的一级小标题，不设二级小标题；小标题建议不超过 60 个字符。
- Discussion 不设子标题。
- 主文 Introduction、Results 和 Discussion 建议不超过 5000 词；Methods 通常少于 3000 词。
- Data availability 必须提供；核心自定义代码适用时单列 Code availability。
- 参考文献采用数字编号，Article 通常不超过 70 条；最终提交 LaTeX 需将参考文献正文嵌入单一 `.tex` 文件。
- 所有 Article 均需 Author contributions 和 Competing interests。

当前 `main.tex` 是中文工作稿，保留 `xeCJK` 和外部 `references.bib` 以便迭代。转英文投稿稿时需要移除中文字体依赖，并将 `.bbl` 内容嵌入 `main.tex`。

## Springer Nature 官方通用 LaTeX 模板

已于 2026-08-13 下载并解压 Springer Nature 官方作者支持页面提供的 2024 年 12 月版通用模板：

- 压缩包：`springer_nature_latex_template_2024.zip`
- 解压目录：`springer_nature_latex_template_2024/sn-article-template/`
- 示例源文件：`springer_nature_latex_template_2024/sn-article-template/sn-article.tex`
- 文档类：`springer_nature_latex_template_2024/sn-article-template/sn-jnl.cls`
- 官方来源：https://www.springernature.com/gp/authors/campaigns/latex-author-support

该模板是 Springer Nature 旗下期刊共用的作者模板，不是 Nature Communications 出版成品的专用双栏模板。示例中的 Nature Portfolio 选项为 `\documentclass[pdflatex,sn-nature]{sn-jnl}`，源文件仍明确使用 `\abstract{...}` 和 `\section{Introduction}`。模板默认用于内容提交；已发表论文中摘要标题、Introduction 标题和双栏版式的显示方式由期刊生产排版决定。

因此，当前中文工作稿继续使用可稳定编译的标准 `article.cls`，并设置为 `10pt,a4paper,twocolumn` 以便内部按 NC 风格进行版面预览。该双栏设置不是 Nature Communications 的官方初投稿强制模板，也不代表最终出版版式；正式英文投稿前仍应根据当时的 Nature Communications 在线说明决定是否恢复单栏或迁移至 `sn-jnl`，期刊专属说明与通用模板冲突时，以期刊专属说明为准。
