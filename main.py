#!/usr/bin/env python3
"""
Hypoc - 程序测试与验证系统
基于PyQt6的完整版
"""

import sys
import re
from pathlib import Path
from typing import Dict, Any


# PyQt6 imports
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QApplication, QMessageBox, QLabel, QTextEdit, QScrollArea,
    QFileDialog, QPushButton, QSizePolicy, QDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QColor

# termqt — embed real terminal for txt_compare output
from termqt import Terminal
from termqt.terminal_io_windows import TerminalWinptyIO

# Patch termqt's hardcoded Qt.black to match dark theme
import termqt.terminal_buffer as _tb
import termqt.terminal_widget as _tw
_term_bg = QColor("#1E1E1E")
_tb.DEFAULT_BG_COLOR = _term_bg
_tw.DEFAULT_BG_COLOR = _term_bg


class RobustTerminalIO(TerminalWinptyIO):
    """修补 termqt 未处理的 EOFError（PTY 关闭时 read() 抛异常）"""

    def _read_loop(self):
        try:
            while self.running:
                try:
                    buf = self.pty_process.read()
                except EOFError:
                    break
                if not buf:
                    continue
                if isinstance(buf, str):
                    self.stdout_callback(bytes(buf, 'utf-8'))
                else:
                    self.stdout_callback(buf)
        finally:
            self.logger.info("Spawned process has been killed")
            if self.running:
                self.running = False
                self.terminated_callback()


# Import modules
from core.checkdata import build_checkdata_content
from ui.tabs import create_output_check_tab, create_source_check_tab

# Import check modules
sys.path.insert(0, str(Path(__file__).parent))
from Rule.style_checker import check_style
from char.check_gb2312 import is_gb2312
from char.convert_to_gb2312 import convert_file_to_gb2312, detect_encoding


# Theme colors — VS Code-style dark
COLOR_BG_LIGHT = "#1E1E1E"
COLOR_BG_CARD = "#252526"
COLOR_BORDER = "#3E3E3E"
COLOR_TEXT_PRIMARY = "#D4D4D4"
COLOR_TEXT_SECONDARY = "#999999"
COLOR_ACCENT = "#0078D4"
COLOR_SUCCESS = "#4ADE80"
COLOR_ERROR = "#F87171"
COLOR_WARNING = "#FBBF24"


class ToolsConfigDialog(QDialog):
    """配置 get_input_data.exe 和 txt_compare.exe 路径"""

    def __init__(self, parent, gid_path="", tc_path=""):
        super().__init__(parent)
        self.setWindowTitle("配置外部工具")
        self.setMinimumWidth(520)
        self.setStyleSheet("background: #2D2D2D;")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        hint = QLabel("请指定以下两个工具的路径（首次使用需配置，之后自动记住）：")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #D4D4D4; font-size: 12px;")
        layout.addWidget(hint)

        btn_style = """
            QPushButton {
                background-color: #0078D4; color: white;
                border: none; border-radius: 6px; padding: 6px 14px;
            }
            QPushButton:hover { background-color: #1A8CDC; }
        """
        edit_style = """
            QLineEdit {
                background: #3C3C3C; border: 1px solid #3E3E3E;
                border-radius: 6px; padding: 6px; color: #D4D4D4; font-size: 12px;
            }
        """

        # get_input_data
        gid_label = QLabel("get_input_data.exe")
        gid_label.setStyleSheet("color: #D4D4D4; font-size: 12px; font-weight: bold;")
        layout.addWidget(gid_label)
        gid_row = QHBoxLayout()
        self.gid_edit = QLineEdit(gid_path)
        self.gid_edit.setPlaceholderText("未配置")
        self.gid_edit.setStyleSheet(edit_style)
        gid_browse = QPushButton("浏览")
        gid_browse.setStyleSheet(btn_style)
        gid_browse.clicked.connect(lambda: self._browse(self.gid_edit))
        gid_row.addWidget(self.gid_edit, 1)
        gid_row.addWidget(gid_browse)
        layout.addLayout(gid_row)

        # txt_compare
        tc_label = QLabel("txt_compare.exe")
        tc_label.setStyleSheet("color: #D4D4D4; font-size: 12px; font-weight: bold;")
        layout.addWidget(tc_label)
        tc_row = QHBoxLayout()
        self.tc_edit = QLineEdit(tc_path)
        self.tc_edit.setPlaceholderText("未配置")
        self.tc_edit.setStyleSheet(edit_style)
        tc_browse = QPushButton("浏览")
        tc_browse.setStyleSheet(btn_style)
        tc_browse.clicked.connect(lambda: self._browse(self.tc_edit))
        tc_row.addWidget(self.tc_edit, 1)
        tc_row.addWidget(tc_browse)
        layout.addLayout(tc_row)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(btn_style)
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #999;
                border: 1px solid #3E3E3E; border-radius: 6px; padding: 6px 14px;
            }
            QPushButton:hover { background-color: #3C3C3C; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def _browse(self, edit: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(self, "选择", "", "Executable (*.exe)")
        if path:
            edit.setText(path)

    def get_paths(self):
        return self.gid_edit.text().strip(), self.tc_edit.text().strip()


class TestWorker(QThread):
    """在后台线程准备比对数据（生成 temp 文件），避免阻塞 UI"""
    ready = pyqtSignal(str, object)   # (command_string, cleanup_fn)
    failed = pyqtSignal(str)          # 错误信息

    def __init__(self, prepare_fn):
        super().__init__()
        self._prepare_fn = prepare_fn

    def run(self):
        try:
            cmd, cleanup = self._prepare_fn()
            self.ready.emit(cmd, cleanup)
        except Exception as e:
            self.failed.emit(str(e))


class HypocWindow(QMainWindow):
    """Hypoc 主窗口"""

    # 跨线程信号：终端 IO 完成后在 UI 线程处理
    _term_done = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.file_paths = {}
        self.checkdata_content = ""
        self._terminal = None
        self._terminal_io = None
        self._term_done.connect(self._on_terminal_complete)
        self.setup_window()
        self.setup_ui()
        self.populate_preset_checkdata()

    def setup_window(self):
        self.setWindowTitle("Hypoc")

        # 动态设置窗口大小，根据屏幕可用区域调整
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            # 窗口占屏幕的85%，最大不超过屏幕尺寸，最小保证可读性
            win_width = min(int(screen_geo.width() * 0.85), 1400)
            win_height = min(int(screen_geo.height() * 0.85), 900)
            # 小屏幕笔记本上保证最小可用尺寸
            win_width = max(win_width, 800)
            win_height = max(win_height, 600)
            self.resize(win_width, win_height)
            # 窗口居中
            self.move(
                screen_geo.left() + (screen_geo.width() - win_width) // 2,
                screen_geo.top() + (screen_geo.height() - win_height) // 2
            )
        else:
            self.setMinimumSize(1000, 700)

        # Remove default window border
        self.setStyleSheet("QMainWindow { border: none; }")

        # Load icon
        icon_path = Path(__file__).parent / "favicon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def setup_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 16)

        title = QLabel("Hypoc")
        title.setStyleSheet("color: #D4D4D4; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)

        hint = QLabel("程序测试与验证系统")
        hint.setStyleSheet("color: #999999; font-size: 11px;")
        header_layout.addWidget(hint)

        disclaimer = QLabel("水平有限，仅供参考")
        disclaimer.setStyleSheet("color: #555555; font-size: 10px;")
        header_layout.addWidget(disclaimer)

        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # 主Tab widget - 输出检查 和 源码检查
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #2D2D2D;
                color: #999999;
                padding: 12px 32px;
                border: 1px solid #3E3E3E;
                border-radius: 8px;
                margin-right: 8px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #0078D4;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background: #3C3C3C;
            }
        """)
        main_layout.addWidget(self.tab_widget)

        # 创建Tab页面
        output_check_tab = create_output_check_tab(self)
        self.tab_widget.addTab(output_check_tab, "输出检查")

        source_check_tab = create_source_check_tab(self)
        self.tab_widget.addTab(source_check_tab, "源码检查")

    # ==========================================================================
    # File Selection Methods
    # ==========================================================================

    def select_file(self, file_type: str, file_ext: str):
        """选择文件"""
        filters = {
            "exe": "Executable Files (*.exe)",
            "cpp": "C++ Files (*.cpp *.cc *.cxx *.c)",
            "txt": "Text Files (*.txt)"
        }

        path, _ = QFileDialog.getOpenFileName(
            self, f"选择 {file_type}", "", filters.get(file_ext, "*.*")
        )

        if path:
            self.file_paths[file_type] = path
            name = Path(path).stem

            # Update label
            if file_type == "preset_exe":
                self.preset_exe_label.setText(Path(path).name)
                self._auto_select_problem(name, self.preset_problem_combo)
            elif file_type == "custom_demo":
                self.custom_demo_label.setText(Path(path).name)
            elif file_type == "custom_user":
                self.custom_user_label.setText(Path(path).name)
                self._auto_select_problem(name, self.checkdata_preset_combo)

    def select_checkdata_file(self):
        """选择checkdata文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择Checkdata文件", "", "Text Files (*.txt)"
        )
        if path:
            self.file_paths["checkdata"] = path
            self.checkdata_file_label.setText(Path(path).name)
            with open(path, 'r', encoding='utf-8') as f:
                self.checkdata_content = f.read()

    def _natural_key(self, s):
        """自然排序键：将字符串中的数字段转为整数，实现 3-b5 < 3-b10"""
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

    def _auto_select_problem(self, exe_name, combo):
        """根据 EXE 文件名自动匹配下拉框中的题目，匹配不到则保留当前选择"""
        m = re.search(r'(\d+-b\d+(?:-\d+)?)', exe_name)
        if not m:
            return
        pid = m.group(1)
        idx = combo.findText(pid)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def populate_preset_checkdata(self):
        """用 data/checkdata/ 里的文件填充预设 checkdata 下拉框"""
        from core.comparison import CHECKDATA_DIR
        self.checkdata_preset_combo.clear()
        if CHECKDATA_DIR.exists():
            names = sorted(
                (p.stem for p in CHECKDATA_DIR.glob("*.txt")),
                key=self._natural_key
            )
            self.checkdata_preset_combo.addItems(names)

    def select_source_file(self):
        """选择源码文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择源码文件", "", "C++ Files (*.cpp *.cc *.cxx *.c)"
        )
        if path:
            self.file_paths["source"] = path
            self.source_label.setText(Path(path).name)
            self.check_source_file(path)

    # ==========================================================================
    # Checkpoint Methods (Online Construction)
    # ==========================================================================

    def add_checkpoint(self):
        """添加检查点"""
        entry = CheckpointEntry(len(self.checkpoint_entries))
        entry.delete_btn.clicked.connect(lambda: self.remove_checkpoint(entry))
        self.checkpoint_entries.append(entry)
        self.checkpoint_container.addWidget(entry)

    def remove_checkpoint(self, entry):
        """删除检查点"""
        self.checkpoint_entries.remove(entry)
        self.checkpoint_container.removeWidget(entry)
        entry.deleteLater()
        # Renumber
        for i, e in enumerate(self.checkpoint_entries):
            e.index = i

    def get_online_checkdata(self) -> str:
        """获取在线构造的checkdata内容"""
        entries = []
        for i, entry in enumerate(self.checkpoint_entries):
            input_val = entry.input_val.toPlainText().strip()
            if input_val:
                # 自动生成 case_id: 01, 02, 03...
                case_id = f"{i + 1:02d}"
                entries.append((case_id, input_val))
        return build_checkdata_content(entries)

    # ==========================================================================
    # Source Check Methods
    # ==========================================================================

    def check_source_file(self, path: str):
        """检查源码文件"""
        try:
            # 读取文件
            with open(path, 'rb') as f:
                raw_data = f.read()

            # 格式检查
            encoding = detect_encoding(raw_data)
            source_code = raw_data.decode(encoding, errors='replace')
            errors = check_style(source_code)

            if not errors:
                self.style_status.setText("✓ 通过 - 无格式问题")
                self.style_status.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px;")
                self.style_result.setText("")
            else:
                self.style_status.setText(f"✗ 发现 {len(errors)} 个问题")
                self.style_status.setStyleSheet(f"color: {COLOR_ERROR}; font-size: 12px;")
                text = ""
                for err in errors:
                    severity_icon = "🔴" if err.severity == "critical" else "⚠️"
                    text += f"{severity_icon} Line {err.line}: [{err.severity}] {err.message}\n"
                    text += f"   代码: {err.code} | 列: {err.column}\n\n"
                self.style_result.setText(text)

            # 字符集检查
            is_gb = is_gb2312(raw_data)

            if is_gb:
                self.encoding_status.setText(f"✓ 通过 - GB2312 编码")
                self.encoding_status.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px;")
                self.encoding_result.setText(f"检测到编码: {encoding}")
                self.encoding_convert_btn.hide()
            else:
                self.encoding_status.setText(f"⚠ 非 GB2312 编码 (当前: {encoding})")
                self.encoding_status.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 12px;")
                self.encoding_result.setText(
                    f"当前编码: {encoding}\n"
                    "提示: 部分编译器仅支持 GB2312 编码"
                )
                self.encoding_convert_btn.show()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"检查文件时出错: {str(e)}")

    def convert_to_gb2312(self):
        """转换源码为GB2312"""
        path = self.file_paths.get("source")
        if not path:
            return

        try:
            if convert_file_to_gb2312(path):
                QMessageBox.information(self, "成功", "文件已成功转换为 GB2312 编码")
                # 重新检查
                self.check_source_file(path)
            else:
                QMessageBox.warning(self, "失败", "转换失败，请检查文件内容")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"转换时出错: {str(e)}")

    # ==========================================================================
    # Output Test Methods
    # ==========================================================================

    def run_output_test(self):
        """运行输出测试"""
        sub_tab_index = self.output_sub_tabs.currentIndex()

        if sub_tab_index == 0:  # 预设模式
            self.run_preset_test()
        else:  # 自定义模式
            self.run_custom_test()

    def open_tools_config(self):
        """打开工具配置对话框"""
        from core.ext_comparison import locate_tools, save_tools_config
        from core.comparison import get_base_dir
        base_dir = str(get_base_dir())

        # 读取已有路径（如果有）
        gid_cur, tc_cur = "", ""
        try:
            gid_cur, tc_cur = locate_tools(base_dir)
        except FileNotFoundError:
            pass

        dlg = ToolsConfigDialog(self, gid_cur, tc_cur)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            gid, tc = dlg.get_paths()
            if not gid or not tc:
                QMessageBox.warning(self, "警告", "两个路径都必须填写")
                return
            from pathlib import Path
            if not Path(gid).exists():
                QMessageBox.warning(self, "警告", f"文件不存在:\n{gid}")
                return
            if not Path(tc).exists():
                QMessageBox.warning(self, "警告", f"文件不存在:\n{tc}")
                return
            save_tools_config(base_dir, gid, tc)
            QMessageBox.information(self, "已保存", "工具路径已保存，可以开始测试了。")

    def _get_tc_params(self) -> Dict[str, Any]:
        """收集用户选择的 txt_compare 参数"""
        return {
            "trim": self.tc_trim_combo.currentText(),
            "lineskip": self.tc_lineskip_spin.value(),
            "lineoffset": self.tc_lineoffset_spin.value(),
            "ignore_blank": self.tc_ignore_blank_cb.isChecked(),
            "ignore_linefeed": self.tc_ignore_linefeed_cb.isChecked(),
            "max_diff": self.tc_max_diff_spin.value(),
            "max_line": self.tc_max_line_spin.value(),
        }

    def _get_tools(self):
        """获取工具路径，找不到时弹出配置对话框。返回 (gid, tc) 或 None（用户取消）"""
        from core.ext_comparison import locate_tools, save_tools_config
        from core.comparison import get_base_dir
        base_dir = str(get_base_dir())

        try:
            return locate_tools(base_dir)
        except FileNotFoundError:
            pass

        # 自动弹出配置对话框
        QMessageBox.information(
            self, "需要配置工具",
            "首次使用需要指定 get_input_data.exe 和 txt_compare.exe 的路径。\n"
            "路径配置后会自动记住，下次无需重新配置。"
        )
        dlg = ToolsConfigDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        gid, tc = dlg.get_paths()
        from pathlib import Path
        if not gid or not tc or not Path(gid).exists() or not Path(tc).exists():
            QMessageBox.warning(self, "配置无效", "路径无效，请重新配置")
            return None
        save_tools_config(base_dir, gid, tc)
        return gid, tc

    # ==========================================================================
    # 测试结果共享处理（termqt 终端）
    # ==========================================================================

    def _clear_terminal(self):
        """移除旧终端 widget，终止旧 IO"""
        if hasattr(self, '_terminal_io') and self._terminal_io:
            try:
                self._terminal_io.terminate()
            except Exception:
                pass
            self._terminal_io = None

        if hasattr(self, '_terminal') and self._terminal:
            try:
                self.terminal_layout.removeWidget(self._terminal)
                self._terminal.deleteLater()
            except Exception:
                pass
            self._terminal = None

    def _create_terminal(self, cmd, cleanup_fn):
        """创建 termqt Terminal widget 并执行 txt_compare"""
        self._clear_terminal()

        cw = self.terminal_container.width()
        ch = self.terminal_container.height()
        if cw < 100:
            cw, ch = 800, 500

        terminal = Terminal(cw, ch, padding=6, font_size=11)
        terminal.set_bg(QColor("#1E1E1E"))
        terminal.set_fg(QColor("#D4D4D4"))
        self.terminal_layout.addWidget(terminal)
        terminal.show()

        io = RobustTerminalIO(
            cols=terminal.row_len,
            rows=terminal.col_len,
            cmd=cmd
        )
        io.stdout_callback = terminal.stdout
        io.terminated_callback = lambda: self._term_done.emit(cleanup_fn)

        self._terminal = terminal
        self._terminal_io = io

        io.spawn()

    def _on_terminal_complete(self, cleanup_fn):
        """txt_compare 运行完毕，清理临时文件"""
        try:
            if cleanup_fn:
                cleanup_fn()
        except Exception:
            pass
        self.output_status.setText("完成")
        self.output_status.setStyleSheet(f"color: {COLOR_SUCCESS};")
        self.output_start_btn.setEnabled(True)

    def _start_test(self, prepare_fn):
        """启动后台准备线程，prepare_fn 返回 (cmd_string, cleanup_fn)"""
        self.output_status.setText("准备中...")
        self.output_status.setStyleSheet("color: #0078D4;")
        self.output_start_btn.setEnabled(False)

        self._clear_terminal()

        self._worker = TestWorker(prepare_fn)
        self._worker.ready.connect(self._on_test_ready)
        self._worker.failed.connect(self._on_test_failed)
        self._worker.start()

    def _on_test_ready(self, cmd, cleanup_fn):
        """数据准备好，创建终端执行 txt_compare"""
        self.output_status.setText("运行中...")
        self._create_terminal(cmd, cleanup_fn)

    def _on_test_failed(self, msg):
        self.output_status.setText(f"错误: {msg}")
        self.output_status.setStyleSheet(f"color: {COLOR_ERROR};")
        self.output_start_btn.setEnabled(True)

    # ==========================================================================
    # Output Test Methods
    # ==========================================================================

    def run_preset_test(self):
        """运行预设模式测试（get_input_data + txt_compare）"""
        import json, tempfile, os
        from core.ext_comparison import prepare_preset_comparison, parse_data_file
        from core.comparison import get_base_dir, CHECKDATA_DIR, DEMORAW_DIR

        exe_path = self.file_paths.get("preset_exe")
        if not exe_path:
            self.output_status.setText("请先选择程序文件")
            self.output_status.setStyleSheet(f"color: {COLOR_ERROR};")
            return

        problem = self.preset_problem_combo.currentText()

        demo_json = DEMORAW_DIR / f"{problem}-demo_output.json"
        if not demo_json.exists():
            self.output_status.setText(f"未找到期望输出文件: {demo_json.name}")
            self.output_status.setStyleSheet(f"color: {COLOR_ERROR};")
            return

        with open(demo_json, "r", encoding="utf-8") as f:
            demo_data = json.load(f)
        expected_hex_map = {
            tc["case_id"]: tc.get("output_hex", "")
            for tc in demo_data.get("test_cases", [])
        }

        checkdata_file = CHECKDATA_DIR / f"{problem}.txt"
        if not checkdata_file.exists():
            entries = [(tc["case_id"], tc.get("input_text", ""))
                       for tc in demo_data.get("test_cases", [])]
            content = build_checkdata_content(entries)
            fd, checkdata_path = tempfile.mkstemp(suffix=".txt")
            os.close(fd)
            with open(checkdata_path, "w", encoding="utf-8") as f:
                f.write(content)
            cleanup_checkdata = lambda: os.path.exists(checkdata_path) and os.unlink(checkdata_path)
        else:
            checkdata_path = str(checkdata_file)
            cleanup_checkdata = None

        tools = self._get_tools()
        if tools is None:
            if cleanup_checkdata:
                cleanup_checkdata()
            return
        gid_exe, tc_exe = tools

        case_ids = parse_data_file(checkdata_path)
        tc_params = self._get_tc_params()

        def prepare():
            cmd, cleanup_tmp = prepare_preset_comparison(
                data_file=checkdata_path,
                case_ids=case_ids,
                user_exe=exe_path,
                gid_exe=gid_exe,
                tc_exe=tc_exe,
                expected_hex_map=expected_hex_map,
                tc_params=tc_params,
            )
            def cleanup_all():
                cleanup_tmp()
                if cleanup_checkdata:
                    cleanup_checkdata()
            return cmd, cleanup_all

        self._start_test(prepare)

    def run_custom_test(self):
        """运行自定义模式测试（get_input_data + txt_compare）"""
        import tempfile, os
        from core.ext_comparison import prepare_custom_comparison, parse_data_file
        from core.comparison import CHECKDATA_DIR

        demo_path = self.file_paths.get("custom_demo")
        user_path = self.file_paths.get("custom_user")

        if not demo_path:
            QMessageBox.warning(self, "警告", "请先选择 Demo 程序")
            return
        if not user_path:
            QMessageBox.warning(self, "警告", "请先选择用户程序")
            return

        tab_idx = self.checkdata_tabs.currentIndex()
        cleanup_checkdata = None

        if tab_idx == 0:  # 预设
            name = self.checkdata_preset_combo.currentText()
            if not name:
                QMessageBox.warning(self, "警告", "预设 Checkdata 列表为空")
                return
            checkdata_path = str(CHECKDATA_DIR / f"{name}.txt")
        elif tab_idx == 1:  # 文件
            checkdata_path = self.file_paths.get("checkdata")
            if not checkdata_path:
                QMessageBox.warning(self, "警告", "请先选择 Checkdata 文件")
                return
        else:  # 在线构造
            content = self.get_online_checkdata()
            if not content.strip():
                QMessageBox.warning(self, "警告", "请添加至少一个检查点")
                return
            fd, checkdata_path = tempfile.mkstemp(suffix=".txt")
            os.close(fd)
            with open(checkdata_path, "w", encoding="utf-8") as f:
                f.write(content)
            cleanup_checkdata = lambda: os.path.exists(checkdata_path) and os.unlink(checkdata_path)

        tools = self._get_tools()
        if tools is None:
            if cleanup_checkdata:
                cleanup_checkdata()
            return
        gid_exe, tc_exe = tools

        case_ids = parse_data_file(checkdata_path)
        if not case_ids:
            self.output_status.setText("Checkdata 文件中没有找到测试用例")
            self.output_status.setStyleSheet(f"color: {COLOR_ERROR};")
            if cleanup_checkdata:
                cleanup_checkdata()
            return

        tc_params = self._get_tc_params()

        def prepare():
            cmd, cleanup_tmp = prepare_custom_comparison(
                data_file=checkdata_path,
                case_ids=case_ids,
                user_exe=user_path,
                gid_exe=gid_exe,
                tc_exe=tc_exe,
                demo_exe=demo_path,
                tc_params=tc_params,
            )
            def cleanup_all():
                cleanup_tmp()
                if cleanup_checkdata:
                    cleanup_checkdata()
            return cmd, cleanup_all

        self._start_test(prepare)


class CheckpointEntry(QWidget):
    """单个检查点输入组件"""
    def __init__(self, index: int):
        super().__init__()
        self.index = index
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # 自动生成的 case_id（只读显示）
        case_id_label = QLabel(f"#{self.index + 1:02d}")
        case_id_label.setStyleSheet("""
            color: #999999;
            font-size: 12px;
            font-weight: bold;
            min-width: 30px;
        """)

        self.input_val = QTextEdit()
        self.input_val.setPlaceholderText("输入内容...")
        self.input_val.setMinimumHeight(150)
        self.input_val.setMaximumHeight(250)
        self.input_val.setStyleSheet("""
            border: 1px solid #3E3E3E;
            border-radius: 6px;
            padding: 4px;
            background: #2D2D2D;
            color: #D4D4D4;
        """)

        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #DC2626; }
        """)

        layout.addWidget(case_id_label)
        layout.addWidget(self.input_val, 1)
        layout.addWidget(self.delete_btn)


# =============================================================================
# Main Entry
# =============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = HypocWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
