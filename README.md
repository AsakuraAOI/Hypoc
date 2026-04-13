# Hypoc - 程序测试与验证系统

基于程序测试与验证工具，支持输出比对（外部工具链）、源码格式检查和字符集检测。

## 功能特性

### 输出检查
使用 `get_input_data` + `txt_compare` 外部工具链进行比对，复现真实测试环境。

- **预设模式**：从 `data/checkdata/` 自动加载题目测试数据，期望输出从内置 JSON 还原
- **自定义模式**：上传 Demo 程序和用户程序进行对比
  - **预设来源**：从 `data/checkdata/` 选择题目
  - **文件上传**：上传自定义 checkdata 文件
  - **在线构造**：手动添加测试用例

> **首次使用**：点击「配置工具」按钮，指定 `get_input_data.exe` 和 `txt_compare.exe` 的路径。路径自动保存至 `config.json`，无需重复配置。

### 源码检查
- **格式检查**：基于规则检查 C/C++ 代码风格（缩进、大括号、配对、switch/case、do-while 等）
- **字符集检查**：检测 GB2312 编码，非 GB2312 时支持一键转换

### 支持的预设题目
3-b5, 3-b7, 3-b8, 3-b9, 3-b10, 3-b12-1, 3-b13-1, 3-b13-2,
4-b1, 4-b2, 4-b3, 4-b5, 4-b6, 4-b7, 4-b8, 4-b9, 4-b10, 4-b11, 4-b12, 4-b13, 4-b14,
5-b8, 5-b9, 5-b10, 5-b15, 5-b16, 5-b17, 5-b18,
6-b1, 6-b2, 6-b3

## 运行

```bash
python main.py
```

## 打包

```bash
python build.py
```

打包后位于 `dist/main.dist/main.exe`，`data/` 目录已包含。外部工具路径需在运行后通过 UI 配置。

## 项目结构

```
Hypoc/
├── main.py              # 主程序入口 + 窗口类
├── build.py             # Nuitka 打包脚本
├── core/
│   ├── comparison.py    # 预设模式比对（get_base_dir 等工具路径）
│   ├── checkdata.py     # checkdata 格式解析与构建
│   └── ext_comparison.py # 外部工具比对逻辑
├── ui/
│   ├── tabs.py          # Tab 页面构建
│   └── cards.py         # 结果卡片组件
├── Rule/
│   └── style_checker.py # C++ 代码风格检查
├── char/
│   ├── check_gb2312.py      # GB2312 编码检测
│   └── convert_to_gb2312.py # GB2312 编码转换
└── data/
    ├── checkdata/        # 预设题目测试数据
    └── demoraw/          # 预设题目期望输出
```

## 依赖

- Python 3.8+
- PyQt6 >= 6.4.0
- Nuitka >= 2.0（仅打包用）
