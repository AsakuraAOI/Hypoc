# 更新日志

## v2.0.0 — 终端渲染 & 暗色主题

### 重大变更

- **真终端渲染**：用 termqt + winpty (ConPTY) 替代 ANSI-to-HTML 伪渲染，txt_compare 的彩色输出在 PTY 中原生显示，完全保留颜色和格式
- **VS Code 风格暗色主题**：全局配色改为暗色系，保留层次感

### 新增

- `RobustTerminalIO`：修复 termqt 未处理 `EOFError` 导致 PTY 关闭时崩溃的问题
- `pyqtSignal` 跨线程通信：修复 `QTimer.singleShot` 在后台线程调用导致 GUI 卡在"运行中"的问题
- Checkdata 自然排序：`3-b10` 不再排在 `3-b2` 前面
- EXE 文件名自动匹配：选择程序后自动选中对应题目

### 重构

- `core/ext_comparison.py`：分离命令构建 (`prepare_*`) 与执行 (`run_*`)，让 GUI 可以拿到命令行再通过 PTY 执行
- `main.py`：删除 `ansi_to_html()`（~120 行）和 `ANSI_COLORS`，终端 widget 在 `_create_terminal()` 中动态创建

### 修复

- 终端背景纯黑：补丁 termqt 两个模块的 `DEFAULT_BG_COLOR`
- `output_start_btn` 重复定义：删除未使用的第一个实例
- 移除冗余描述文案、"测试结果"居中
