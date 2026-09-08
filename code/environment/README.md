# E00 环境证据

本目录保存正式实验环境的可核查记录。它不把当前机器状态误称为“完全锁定环境”。

- `e00-primary-environment.json`：E00 主环境的机器可读快照，包含解释器、直接依赖、SUMO 可执行文件和 SHA-256。
- `requirements-e00-primary.txt`：当前已验证的 Python 直接依赖精确版本，供第二干净环境复算时使用。
- `e00-clean-py313-lock.txt` 与 `e00-clean-py313.json`：实际建立并使用的隔离 venv 及其 wheels/hash。

边界：当前主环境是既有 Miniconda 环境，`pyarrow` 位于用户级 site-packages，因此只算 primary-environment evidence。已建立 `include-system-site-packages=false` 的 Python 3.13.5 venv，并用本地 hash 已校验 wheels 离线安装 pandas/PyArrow 及其依赖；双环境 artifact smoke 的字段、行数、manifest schema 和“不可用于科学主张”分类一致。由于 smoke 表为空、正式交通 runner 尚未重建，G00-15 只完成 artifact layer，不能判整个 E00 通过。

PyArrow 安装证据：

- 文件：`pyarrow-25.0.1-cp313-cp313-win_amd64.whl`
- 来源：PyPI 官方发布页
- SHA-256：`31e49a7888fcdf3a835da33ae777f6bb9a866334e5a789282fc26dcf426f7f15`
- 安装命令：`python -m pip install --user --no-index <已校验 wheel 路径>`

不得用 CSV 代替计划规定的 Parquet；依赖安装失败时应停止并上报。

双环境比较报告：`docs/论文实验推进/阶段0_基础设施与测量/E00/双环境artifact smoke复算报告.json`。
