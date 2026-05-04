#!/usr/bin/env python3
"""
UI组件模块 - 基础组件
"""

from PyQt6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit

# Theme colors — VS Code-style dark
COLOR_BG_LIGHT = "#1E1E1E"
COLOR_BG_CARD = "#252526"
COLOR_BORDER = "#3E3E3E"
COLOR_TEXT_PRIMARY = "#D4D4D4"
COLOR_TEXT_SECONDARY = "#999999"
COLOR_ACCENT = "#0078D4"
COLOR_ACCENT_HOVER = "#1A8CDC"
COLOR_SUCCESS = "#4ADE80"
COLOR_ERROR = "#F87171"
COLOR_WARNING = "#FBBF24"
COLOR_CRITICAL = "#EF4444"


class GlassCard(QFrame):
    """卡片组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setStyleSheet(f"""
            QFrame#GlassCard {{
                background-color: {COLOR_BG_CARD};
                border: none;
                border-radius: 12px;
            }}
        """)


class ResultCard(QFrame):
    """测试结果卡片"""
    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.result = result
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("ResultCard")
        is_pass = self.result.status == "PASS"
        card_bg = "#1A3A2A" if is_pass else "#3A1A1A"
        border_color = COLOR_SUCCESS if is_pass else COLOR_ERROR

        self.setStyleSheet(f"""
            QFrame#ResultCard {{
                background-color: {card_bg};
                border: none;
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header row
        header_layout = QHBoxLayout()
        status_label = QLabel("✓ PASS" if is_pass else "✗ FAIL")
        status_label.setStyleSheet(f"color: {border_color}; font-size: 14px; font-weight: bold;")

        case_label = QLabel(f"#{self.result.case_id}")
        case_label.setStyleSheet("color: #D4D4D4; font-size: 14px; font-weight: 600;")

        header_layout.addWidget(status_label)
        header_layout.addWidget(case_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Input
        input_label = QLabel("输入:")
        input_label.setStyleSheet("color: #999999; font-size: 11px;")
        layout.addWidget(input_label)

        input_text = QTextEdit(self.result.input_val)
        input_text.setStyleSheet(f"""
            background-color: #2D2D2D;
            border: none;
            border-radius: 6px;
            color: {COLOR_TEXT_PRIMARY};
            font-size: 12px;
            padding: 4px;
        """)
        input_text.setReadOnly(True)
        input_text.setMaximumHeight(60)
        layout.addWidget(input_text)

        # Output section
        output_frame = QFrame()
        output_frame.setStyleSheet(f"""
            background-color: #2D2D2D;
            border-radius: 6px;
            padding: 8px;
        """)
        output_layout = QVBoxLayout(output_frame)
        output_layout.setSpacing(4)

        # Expected
        exp_label = QLabel("期望:")
        exp_label.setStyleSheet("color: #999999; font-size: 11px;")
        output_layout.addWidget(exp_label)

        exp_text = QTextEdit(self.result.expected_text)
        exp_text.setStyleSheet(f"""
            background-color: transparent;
            border: none;
            color: {COLOR_SUCCESS};
            font-size: 12px;
        """)
        exp_text.setReadOnly(True)
        exp_text.setMaximumHeight(60)
        output_layout.addWidget(exp_text)

        # Actual
        actual_label = QLabel("实际:")
        actual_label.setStyleSheet("color: #999999; font-size: 11px;")
        output_layout.addWidget(actual_label)

        actual_text = QTextEdit(self.result.actual_text)
        actual_text_color = COLOR_SUCCESS if is_pass else COLOR_ERROR
        actual_text.setStyleSheet(f"""
            background-color: transparent;
            border: none;
            color: {actual_text_color};
            font-size: 12px;
        """)
        actual_text.setReadOnly(True)
        actual_text.setMaximumHeight(60)
        output_layout.addWidget(actual_text)

        layout.addWidget(output_frame)

        # HEX diff info
        if self.result.diff_info:
            diff = self.result.diff_info
            diff_label = QLabel(
                f"差异: 第{diff['char_pos']}个字符开始不同\n"
                f"期望: {diff.get('expected_char', '')}\n"
                f"实际: {diff.get('actual_char', '')}"
            )
            diff_label.setStyleSheet(f"""
                color: {COLOR_WARNING};
                font-size: 11px;
                background-color: #3A2E00;
                border-radius: 6px;
                padding: 6px;
            """)
            layout.addWidget(diff_label)

        # HEX section
        hex_frame = QFrame()
        hex_frame.setStyleSheet("""
            background-color: #333333;
            border-radius: 6px;
            padding: 8px;
        """)
        hex_layout = QVBoxLayout(hex_frame)
        hex_layout.setSpacing(4)

        hex_title = QLabel("HEX:")
        hex_title.setStyleSheet("color: #999999; font-size: 11px; font-weight: bold;")
        hex_layout.addWidget(hex_title)

        # Expected HEX
        exp_hex_label = QLabel("期望:")
        exp_hex_label.setStyleSheet("color: #999999; font-size: 10px;")
        hex_layout.addWidget(exp_hex_label)

        exp_hex_text = QTextEdit(self.result.expected_hex)
        exp_hex_text.setStyleSheet(f"""
            background-color: transparent;
            border: none;
            color: {COLOR_SUCCESS};
            font-size: 10px;
            font-family: monospace;
        """)
        exp_hex_text.setReadOnly(True)
        exp_hex_text.setMaximumHeight(40)
        hex_layout.addWidget(exp_hex_text)

        # Actual HEX
        actual_hex_label = QLabel("实际:")
        actual_hex_label.setStyleSheet("color: #999999; font-size: 10px;")
        hex_layout.addWidget(actual_hex_label)

        actual_hex_text = QTextEdit(self.result.actual_hex)
        actual_hex_text_color = COLOR_SUCCESS if is_pass else COLOR_ERROR
        actual_hex_text.setStyleSheet(f"""
            background-color: transparent;
            border: none;
            color: {actual_hex_text_color};
            font-size: 10px;
            font-family: monospace;
        """)
        actual_hex_text.setReadOnly(True)
        actual_hex_text.setMaximumHeight(40)
        hex_layout.addWidget(actual_hex_text)

        layout.addWidget(hex_frame)
