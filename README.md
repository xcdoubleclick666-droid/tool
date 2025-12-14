# FitnessToolbox 打包说明

目标：在 Windows 上生成独立的 `FitnessToolbox.exe` 可执行文件。

依赖
- Python 3.10/3.11
- 在 `requirements.txt` 中列出的依赖（主要是 `PySide6` 和 `pyinstaller`）

本地（Windows）构建步骤

1. 在 Windows 上安装 Python & Git，克隆仓库：

```bash
git clone <repo> .
python -m pip install --upgrade pip
pip install -r requirements.txt
pyinstaller --clean --onefile --windowed fitness_toolbox.spec
```

2. 构建产物位于 `dist/FitnessToolbox.exe`。

通过 GitHub Actions 构建（推荐）

我已添加 [.github/workflows/build-windows.yml](.github/workflows/build-windows.yml)，可在仓库的 Actions 页面手动触发 `Build Windows EXE` 工作流；成功后会生成并上传 `FitnessToolbox.exe` 工件供下载。

在 macOS 上直接构建 .exe

直接在 macOS 上运行 PyInstaller 通常会生成 macOS 可执行程序，而不是 Windows `.exe`。要在 macOS 构建 Windows `.exe`，需在 Windows 环境或使用专门的交叉构建容器/虚拟机（如使用 Windows CI runner 或 Wine/docker 镜像）中运行 PyInstaller。

提示
- 如果你希望我在 CI（GitHub Actions）上帮你触发一次构建，我可以创建一个临时 commit/PR 或引导你如何手动触发。 
- 如果你想我在本机尝试构建（注意：在 macOS 上无法生成真正的 .exe），请确认。
# FitnessToolbox (Qt6 示例)

这是一个基于 Qt6 的最小示例，用于在 macOS + VSCode 环境下启动多选项卡的健身设备工具。

主要文件:
- `qt_main.py` — Qt6 GUI 示例，包含“跑步机”选项卡与计算逻辑。
- `main.py` — 仓库中原有的 Tkinter 示例（保留）。
- `requirements.txt` — 运行示例所需依赖。

快速开始（推荐使用虚拟环境）:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 qt_main.py
```

说明:
- 跑步机选项卡允许填写参数：电机功率、转速、带轮、滚筒直径、跑带时速等。
- 当且仅当有且只有一项留空时，点击“计算”按钮会尝试根据其它值计算该项。

如果需要，我可以把计算逻辑扩展成更完整的工程文件、加入保存/导入配置、或者把界面风格化。
