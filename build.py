#!/usr/bin/env python3
"""
Nuitka 构建脚本 - 将 Hypoc 打包为独立 exe
"""

import subprocess
import sys
import os
from pathlib import Path

def build():
    project_dir = Path(__file__).parent
    main_py = project_dir / "main.py"
    icon_path = project_dir / "favicon.ico"

    if not main_py.exists():
        print(f"错误: {main_py} 不存在")
        return

    # Nuitka 命令参数
    # 使用 standalone 模式（非 onefile），data 目录会直接放在 exe 同级目录
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        f"--output-dir=dist",
        f"--windows-icon-from-ico={icon_path}" if icon_path.exists() else "",
        "--windows-console-mode=disable",
        "--enable-plugin=pyqt6",
        "--remove-output",
        "--follow-imports",
        f"--include-data-dir=./data=data",
        str(main_py),
    ]

    # 过滤空字符串
    cmd = [c for c in cmd if c]

    print("开始打包 (standalone 模式)...")
    print(" ".join(cmd))
    print()

    result = subprocess.run(cmd, cwd=str(project_dir))
    if result.returncode == 0:
        print("\n打包完成!")
        print("输出目录: dist/main.dist/")
        print("运行方式: dist/main.dist/main.exe")
        print("注意: data 目录已复制到 dist/main.dist/data")
        print()
        print("【首次使用前需配置外部工具】")
        print("  启动后点击「配置工具」按钮，分别指定：")
        print("  - get_input_data.exe")
        print("  - txt_compare.exe")
    else:
        print(f"\n打包失败: {result.returncode}")

if __name__ == "__main__":
    build()
