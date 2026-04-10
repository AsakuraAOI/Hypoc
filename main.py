#!/usr/bin/env python3
"""
Hypoc - 程序测试与验证系统
基于PyQt6的完整版
"""

import sys
from pathlib import Path

# PyQt6 imports
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QApplication, QMessageBox, QLabel, QTextEdit, QScrollArea,
    QFileDialog, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

# Import modules
from core.comparison import run_preset_comparison, run_custom_comparison
from core.checkdata import parse_checkdata, build_checkdata_content
from ui.cards import GlassCard, ResultCard
from ui.tabs import create_output_check_tab, create_source_check_tab

# Import check modules
sys.path.insert(0, str(Path(__file__).parent))
from Rule.style_checker import check_style
from char.check_gb2312 import is_gb2312
from char.convert_to_gb2312 import convert_file_to_gb2312, detect_encoding


# Theme colors - Light theme (like Lite)
COLOR_BG_LIGHT = "#F5F5F5"
COLOR_BG_CARD = "#FFFFFF"
COLOR_BORDER = "#E0E0E0"
COLOR_TEXT_PRIMARY = "#1A1A1A"
COLOR_TEXT_SECONDARY = "#666666"
COLOR_ACCENT = "#2563EB"
COLOR_SUCCESS = "#22C55E"
COLOR_ERROR = "#EF4444"
COLOR_WARNING = "#F59E0B"


class HypocWindow(QMainWindow):
    """Hypoc 主窗口"""
    def __init__(self):
        super().__init__()
        self.file_paths = {}  # 存储各种文件路径
        self.checkdata_content = ""  # checkdata文件内容
        self.setup_window()
        self.setup_ui()

    def setup_window(self):
        self.setWindowTitle("Hypoc")
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
        title.setStyleSheet("color: #1A1A1A; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)

        hint = QLabel("水平有限，仅供参考")
        hint.setStyleSheet("color: #999999; font-size: 11px;")
        header_layout.addWidget(hint)

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
                background: #FFFFFF;
                color: #666666;
                padding: 12px 32px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin-right: 8px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #2563EB;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background: #F5F5F5;
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

            # Update label
            if file_type == "preset_exe":
                self.preset_exe_label.setText(Path(path).name)
            elif file_type == "custom_demo":
                self.custom_demo_label.setText(Path(path).name)
            elif file_type == "custom_user":
                self.custom_user_label.setText(Path(path).name)

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

    def run_preset_test(self):
        """运行预设模式测试"""
        exe_path = self.file_paths.get("preset_exe")
        if not exe_path:
            self.output_status.setText("请先选择程序文件")
            self.output_status.setStyleSheet(f"color: {COLOR_ERROR};")
            return

        problem = self.preset_problem_combo.currentText()

        # 预设模式使用程序提供的checkdata，无需用户选择

        self.output_status.setText("运行中...")
        self.output_status.setStyleSheet("color: #2563EB;")
        self.output_start_btn.setEnabled(False)

        # 清除之前的结果
        while self.output_results_container.count():
            child = self.output_results_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        try:
            results = run_preset_comparison(exe_path, problem)

            passed = sum(1 for r in results if r.status == "PASS")
            failed = len(results) - passed

            # 显示摘要
            summary = QLabel(f"完成: {passed}/{len(results)} 通过" + (" ✓" if failed == 0 else " ✗"))
            summary.setStyleSheet(f"color: {'#22C55E' if failed == 0 else '#EF4444'}; font-size: 14px; font-weight: bold;")
            self.output_results_container.addWidget(summary)

            # 显示结果卡片
            for result in results:
                card = ResultCard(result)
                self.output_results_container.addWidget(card)

            self.output_status.setText(f"完成: {passed}/{len(results)} 通过, {failed} 失败")
            self.output_status.setStyleSheet(f"color: {'#22C55E' if failed == 0 else '#EF4444'};")

        except Exception as e:
            self.output_status.setText(f"错误: {str(e)}")
            self.output_status.setStyleSheet(f"color: {COLOR_ERROR};")
        finally:
            self.output_start_btn.setEnabled(True)

    def run_custom_test(self):
        """运行自定义模式测试"""
        demo_path = self.file_paths.get("custom_demo")
        user_path = self.file_paths.get("custom_user")

        if not demo_path:
            QMessageBox.warning(self, "警告", "请先选择 Demo 程序")
            return

        if not user_path:
            QMessageBox.warning(self, "警告", "请先选择用户程序")
            return

        # 获取checkdata
        checkdata_content = ""
        if self.checkdata_tabs.currentIndex() == 0:  # 文件模式
            if not self.checkdata_content:
                QMessageBox.warning(self, "警告", "请先选择 Checkdata 文件")
                return
            checkdata_content = self.checkdata_content
        else:  # 在线构造模式
            checkdata_content = self.get_online_checkdata()
            if not checkdata_content.strip():
                QMessageBox.warning(self, "警告", "请添加至少一个检查点")
                return

        self.output_status.setText("运行中...")
        self.output_status.setStyleSheet("color: #2563EB;")
        self.output_start_btn.setEnabled(False)

        # 清除之前的结果
        while self.output_results_container.count():
            child = self.output_results_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        try:
            results = run_custom_comparison(demo_path, user_path, checkdata_content)

            passed = sum(1 for r in results if r.status == "PASS")
            failed = len(results) - passed

            # 显示摘要
            summary = QLabel(f"完成: {passed}/{len(results)} 通过" + (" ✓" if failed == 0 else " ✗"))
            summary.setStyleSheet(f"color: {'#22C55E' if failed == 0 else '#EF4444'}; font-size: 14px; font-weight: bold;")
            self.output_results_container.addWidget(summary)

            # 显示结果卡片
            for result in results:
                card = ResultCard(result)
                self.output_results_container.addWidget(card)

            self.output_status.setText(f"完成: {passed}/{len(results)} 通过, {failed} 失败")
            self.output_status.setStyleSheet(f"color: {'#22C55E' if failed == 0 else '#EF4444'};")

        except Exception as e:
            error_label = QLabel(f"错误: {str(e)}")
            error_label.setStyleSheet(f"color: {COLOR_ERROR};")
            self.output_results_container.addWidget(error_label)
            self.output_status.setText(f"错误: {str(e)}")
            self.output_status.setStyleSheet(f"color: {COLOR_ERROR};")
        finally:
            self.output_start_btn.setEnabled(True)


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
            color: #666666;
            font-size: 12px;
            font-weight: bold;
            min-width: 30px;
        """)

        self.input_val = QTextEdit()
        self.input_val.setPlaceholderText("输入内容...")
        self.input_val.setMinimumHeight(150)
        self.input_val.setMaximumHeight(250)
        self.input_val.setStyleSheet("""
            border: 1px solid #E0E0E0;
            border-radius: 6px;
            padding: 4px;
            background: white;
            color: #1A1A1A;
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
