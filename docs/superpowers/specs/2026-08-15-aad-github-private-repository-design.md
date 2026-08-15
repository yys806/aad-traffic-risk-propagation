# AAD GitHub Private Repository Design

## 目标

为 `D:\shen\TJU\AAD` 建立一个由 Codex 统一维护的 Git 仓库，并创建对应的 GitHub Private 远程仓库 `aad-traffic-risk-propagation`。仓库同时承担代码版本管理和未发表论文、项目文档的异地备份。

## 仓库边界

### 纳入版本控制

- `code/` 中的源代码、测试、配置、示例、运行说明和必要的开发文档；
- `paper/` 中的论文源文件、参考文献、论文说明、已确认的 PDF 和历史稿备份；
- `docs/` 中的项目导航、交接、研究记录、设计规格和实施计划；
- 根目录 `README.md`、`新对话完整交接_2026-08-15.md`、课题说明和项目级维护文档；
- 根目录和代码目录中用于复现环境的依赖声明，例如 `pyproject.toml`。

### 明确排除

- `literature/` 中的本地论文 PDF、抽取文本、下载记录和文献工作簿；这些文件继续只保存在本地；
- `code/outputs/`、原始轨迹、实验日志、生成图片和大批量 JSON/CSV/JSONL 结果；
- `tmp/`、`.pytest_cache/`、`__pycache__/`、`.pyc`、LaTeX 构建中间文件和临时渲染目录；
- 本地环境、凭据、令牌、机器绝对路径配置和任何 `.env` 文件；
- Windows/WSL 私有工作树、外部目录和 `D:\shen\TJU\DRIFT` 的任何内容。

排除规则只影响 Git 跟踪，不删除本地文件。论文、文档和源代码的本地原件保持原位。

## 远程与分支

- GitHub 仓库：`aad-traffic-risk-propagation`；
- 可见性：Private；
- 默认分支：`main`；
- 首次远程创建后立即推送经过检查的初始提交；
- 后续由 Codex 负责提交前检查、提交说明、推送和状态报告，不自动推送未经用户要求的改动。

## 初始提交策略

1. 为 AAD 根目录初始化 Git，不初始化或修改 DRIFT。
2. 扩充根 `.gitignore`，先用 `git status --short --ignored` 检查候选文件。
3. 用 `git check-ignore` 和文件大小审计确认排除项生效。
4. 只暂存批准范围内的代码、论文、文档和配置；不使用 `git add .` 盲目纳入全部文件。
5. 运行 AAD 主测试和 SPMD 测试，确认初始提交不改变运行状态。
6. 创建本地初始提交，检查提交清单和敏感路径，再通过 GitHub 登录态创建 Private 远程并推送 `main`。
7. 推送后核对远程 URL、默认分支、提交 ID 和工作区状态。

## 日常管理规则

- 每次修改前先检查 `git status` 和当前分支；
- 代码行为变化先测试再提交；文档整理也必须检查是否误纳入论文 PDF、文献和输出；
- 提交按单一目的组织，消息说明真实变更，不重写历史；
- 不把 GitHub 当作原始数据或文献版权归档系统；需要备份大文件时另行设计存储方案；
- DRIFT 始终是只读上游参考，不添加为 submodule，不从 AAD 仓库提交其文件。

## 验收标准

- 本地 AAD 根目录成为 Git 工作树，默认分支为 `main`；
- 初始提交只包含批准范围内的文件；`literature/`、`code/outputs/`、原始数据、缓存和临时材料均未进入提交；
- `paper/`、`docs/`、代码和测试在提交后仍可读取；
- AAD 主测试和 SPMD 测试通过；
- GitHub Private 仓库已创建并包含同一个初始 `main` 提交；
- DRIFT 的 HEAD、工作区状态和文件内容不发生变化。

