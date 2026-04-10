#!/usr/bin/env python3
"""
UI组件模块 - 基础组件
"""

from PyQt6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit

# Theme colors - Clean light theme (like Lite)
COLOR_BG_LIGHT = "#F5F5F5"
COLOR_BG_CARD = "#FFFFFF"
COLOR_BORDER = "#E0E0E0"
COLOR_TEXT_PRIMARY = "#1A1A1A"
COLOR_TEXT_SECONDARY = "#666666"
COLOR_ACCENT = "#2563EB"
COLOR_ACCENT_HOVER = "#1D4ED8"
COLOR_SUCCESS = "#22C55E"
COLOR_ERROR = "#EF4444"
COLOR_WARNING = "#F59E0B"
COLOR_CRITICAL = "#DC2626"


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
        card_bg = "#E8F5E9" if is_pass else "#FFEBEE"
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
        case_label.setStyleSheet("color: #1A1A1A; font-size: 14px; font-weight: 600;")

        header_layout.addWidget(status_label)
        header_layout.addWidget(case_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Input
        input_label = QLabel(f"输入: {self.result.input_val}")
        input_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(input_label)

        # Output section
        output_frame = QFrame()
        output_frame.setStyleSheet(f"""
            background-color: #FAFAFA;
            border-radius: 6px;
            padding: 8px;
        """)
        output_layout = QVBoxLayout(output_frame)
        output_layout.setSpacing(4)

        # Expected
        exp_label = QLabel("期望:")
        exp_label.setStyleSheet("color: #666666; font-size: 11px;")
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
        actual_label.setStyleSheet("color: #666666; font-size: 11px;")
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
                background-color: #FFF8E1;
                border-radius: 6px;
                padding: 6px;
            """)
            layout.addWidget(diff_label)
