#!/usr/bin/env bash
set -euo pipefail

echo "本脚本展示在 Windows 环境中使用 pyinstaller 打包的命令示例。"
echo "在 Windows 上运行："
echo "  python -m pip install -r requirements.txt"
echo "  pyinstaller --clean --onefile --windowed fitness_toolbox.spec"

echo "构建产物位于 dist/FitnessToolbox.exe" 
