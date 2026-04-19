#!/usr/bin/env python3
"""
UI组件模块 - Tab页面创建
"""

from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QScrollArea, QFileDialog, QMessageBox,
    QFrame, QTabWidget, QSizePolicy, QSpinBox, QCheckBox,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPalette

from .cards import GlassCard, ResultCard

# Problem list - 支持的预设题目
PROBLEMS = [
    "3-b5", "3-b7", "3-b8", "3-b9", "3-b10", "3-b12-1", "3-b13-1", "3-b13-2",
    "4-b1", "4-b2", "4-b3", "4-b5", "4-b6", "4-b7", "4-b8", "4-b9",
    "4-b10", "4-b11", "4-b12", "4-b13", "4-b14",
    "5-b8", "5-b9", "5-b10", "5-b15", "5-b16", "5-b17", "5-b18",
    "6-b1", "6-b2", "6-b3",
]

# Theme colors - Clean light theme
COLOR_TEXT_PRIMARY = "#1A1A1A"
COLOR_TEXT_SECONDARY = "#666666"
COLOR_ACCENT = "#2563EB"
COLOR_ACCENT_HOVER = "#1D4ED8"
COLOR_SUCCESS = "#22C55E"
COLOR_ERROR = "#EF4444"
COLOR_WARNING = "#F59E0B"
COLOR_CRITICAL = "#DC2626"
COLOR_BG_CARD = "#FFFFFF"
COLOR_BORDER = "#E0E0E0"


def create_output_check_tab(window) -> QWidget:
    """创建输出检查Tab（预设+自定义子模式）"""
    tab = QWidget()
    layout = QHBoxLayout(tab)
    layout.setSpacing(16)

    # 左侧面板
    left_panel = QWidget()
    left_layout = QVBoxLayout(left_panel)
    left_layout.setSpacing(12)

    # 输出检查说明
    output_desc = QLabel(
        "使用 get_input_data + txt_compare 外部工具链进行比对，复现真实测试环境。"
    )
    output_desc.setWordWrap(True)
    output_desc.setStyleSheet("color: #666666; font-size: 11px; background: #F0F7FF; "
                                "border-radius: 6px; padding: 8px;")
    left_layout.addWidget(output_desc)

    # 比对参数区域（置于开始测试按钮下方）
    tc_group = QGroupBox("比对参数（txt_compare）")
    tc_group.setStyleSheet("""
        QGroupBox {
            font-size: 12px;
            font-weight: bold;
            color: #666666;
            border: 1px solid #E0E0E0;
            border-radius: 6px;
            margin-top: 4px;
            padding-top: 8px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
        }
    """)
    tc_grid = QGridLayout(tc_group)
    tc_grid.setSpacing(8)

    # --trim
    trim_label = QLabel("--trim")
    trim_label.setStyleSheet("color: #666666; font-size: 11px;")
    window.tc_trim_combo = QComboBox()
    window.tc_trim_combo.addItems(["none", "left", "right", "all"])
    window.tc_trim_combo.setCurrentText("none")
    window.tc_trim_combo.setStyleSheet("""
        QComboBox {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            padding: 4px 8px;
            color: #1A1A1A;
            font-size: 11px;
        }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            color: #1A1A1A;
            font-size: 11px;
        }
    """)
    tc_grid.addWidget(trim_label, 0, 0)
    tc_grid.addWidget(window.tc_trim_combo, 0, 1)

    # --lineskip
    lineskip_label = QLabel("--lineskip")
    lineskip_label.setStyleSheet("color: #666666; font-size: 11px;")
    window.tc_lineskip_spin = QSpinBox()
    window.tc_lineskip_spin.setRange(0, 100)
    window.tc_lineskip_spin.setValue(0)
    window.tc_lineskip_spin.setStyleSheet("""
        QSpinBox {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            padding: 4px 8px;
            color: #1A1A1A;
            font-size: 11px;
        }
    """)
    tc_grid.addWidget(lineskip_label, 0, 2)
    tc_grid.addWidget(window.tc_lineskip_spin, 0, 3)

    # --lineoffset
    lineoffset_label = QLabel("--lineoffset")
    lineoffset_label.setStyleSheet("color: #666666; font-size: 11px;")
    window.tc_lineoffset_spin = QSpinBox()
    window.tc_lineoffset_spin.setRange(-100, 100)
    window.tc_lineoffset_spin.setValue(0)
    window.tc_lineoffset_spin.setStyleSheet("""
        QSpinBox {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            padding: 4px 8px;
            color: #1A1A1A;
            font-size: 11px;
        }
    """)
    tc_grid.addWidget(lineoffset_label, 1, 0)
    tc_grid.addWidget(window.tc_lineoffset_spin, 1, 1)

    # --ignore_blank
    window.tc_ignore_blank_cb = QCheckBox("--ignore_blank")
    window.tc_ignore_blank_cb.setStyleSheet("""
        QCheckBox {
            color: #666666;
            font-size: 11px;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            border-radius: 3px;
            border: 1px solid #CCCCCC;
            background: white;
        }
        QCheckBox::indicator:checked {
            background: #2563EB;
            border: 1px solid #2563EB;
        }
    """)
    tc_grid.addWidget(window.tc_ignore_blank_cb, 1, 2, 1, 2)

    # --ignore_linefeed
    window.tc_ignore_linefeed_cb = QCheckBox("--ignore_linefeed")
    window.tc_ignore_linefeed_cb.setStyleSheet("""
        QCheckBox {
            color: #666666;
            font-size: 11px;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            border-radius: 3px;
            border: 1px solid #CCCCCC;
            background: white;
        }
        QCheckBox::indicator:checked {
            background: #2563EB;
            border: 1px solid #2563EB;
        }
    """)
    tc_grid.addWidget(window.tc_ignore_linefeed_cb, 2, 0, 1, 2)

    # --max_diff
    max_diff_label = QLabel("--max_diff")
    max_diff_label.setStyleSheet("color: #666666; font-size: 11px;")
    window.tc_max_diff_spin = QSpinBox()
    window.tc_max_diff_spin.setRange(0, 100)
    window.tc_max_diff_spin.setValue(0)
    window.tc_max_diff_spin.setStyleSheet("""
        QSpinBox {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            padding: 4px 8px;
            color: #1A1A1A;
            font-size: 11px;
        }
    """)
    tc_grid.addWidget(max_diff_label, 2, 2)
    tc_grid.addWidget(window.tc_max_diff_spin, 2, 3)

    # --max_line
    max_line_label = QLabel("--max_line")
    max_line_label.setStyleSheet("color: #666666; font-size: 11px;")
    window.tc_max_line_spin = QSpinBox()
    window.tc_max_line_spin.setRange(0, 10000)
    window.tc_max_line_spin.setValue(0)
    window.tc_max_line_spin.setStyleSheet("""
        QSpinBox {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            padding: 4px 8px;
            color: #1A1A1A;
            font-size: 11px;
        }
    """)
    tc_grid.addWidget(max_line_label, 3, 0)
    tc_grid.addWidget(window.tc_max_line_spin, 3, 1)

    # 开始测试按钮
    window.output_start_btn = QPushButton("开始测试")
    window.output_start_btn.setStyleSheet("""
        QPushButton {
            background-color: #2563EB;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #1D4ED8; }
    """)
    window.output_start_btn.clicked.connect(window.run_output_test)
    # 预设/自定义 子Tab
    window.output_sub_tabs = QTabWidget()
    window.output_sub_tabs.setStyleSheet("""
        QTabWidget::pane {
            border: none;
            background: transparent;
        }
        QTabBar::tab {
            background: #FFFFFF;
            color: #666666;
            padding: 8px 20px;
            border: 1px solid #E0E0E0;
            border-radius: 6px;
            margin-right: 6px;
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

    # ==================== 预设子Tab ====================
    preset_widget = QWidget()
    preset_layout = QVBoxLayout(preset_widget)
    preset_layout.setSpacing(10)

    # EXE选择
    exe_layout = QVBoxLayout()
    exe_label = QLabel("程序文件")
    exe_label.setStyleSheet("color: #666666; font-size: 12px;")
    exe_layout.addWidget(exe_label)

    exe_btn_layout = QHBoxLayout()
    window.preset_exe_btn = QPushButton("选择EXE")
    window.preset_exe_btn.setStyleSheet("""
        QPushButton {
            background-color: #2563EB;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
        }
        QPushButton:hover { background-color: #1D4ED8; }
    """)
    window.preset_exe_btn.clicked.connect(lambda: window.select_file("preset_exe", "exe"))
    window.preset_exe_label = QLabel("未选择")
    window.preset_exe_label.setStyleSheet("color: #666666; font-size: 12px;")
    exe_btn_layout.addWidget(window.preset_exe_btn)
    exe_btn_layout.addWidget(window.preset_exe_label)
    exe_btn_layout.addStretch()
    exe_layout.addLayout(exe_btn_layout)
    preset_layout.addLayout(exe_layout)

    # 问题选择
    problem_layout = QVBoxLayout()
    problem_label = QLabel("问题")
    problem_label.setStyleSheet("color: #666666; font-size: 12px;")
    problem_layout.addWidget(problem_label)

    window.preset_problem_combo = QComboBox()
    window.preset_problem_combo.addItems(PROBLEMS)
    window.preset_problem_combo.setStyleSheet("""
        QComboBox {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 6px;
            padding: 10px;
            color: #1A1A1A;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            color: #1A1A1A;
        }
    """)
    problem_layout.addWidget(window.preset_problem_combo)
    preset_layout.addLayout(problem_layout)

    preset_layout.addStretch()

    window.output_sub_tabs.addTab(preset_widget, "预设")

    # ==================== 自定义子Tab ====================
    custom_widget = QWidget()
    custom_layout = QVBoxLayout(custom_widget)
    custom_layout.setSpacing(10)

    # Demo EXE
    demo_layout = QVBoxLayout()
    demo_label = QLabel("Demo程序")
    demo_label.setStyleSheet("color: #666666; font-size: 12px;")
    demo_layout.addWidget(demo_label)

    demo_btn_layout = QHBoxLayout()
    window.custom_demo_btn = QPushButton("选择Demo")
    window.custom_demo_btn.setStyleSheet("""
        QPushButton {
            background-color: #2563EB;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
        }
        QPushButton:hover { background-color: #1D4ED8; }
    """)
    window.custom_demo_btn.clicked.connect(lambda: window.select_file("custom_demo", "exe"))
    window.custom_demo_label = QLabel("未选择")
    window.custom_demo_label.setStyleSheet("color: #666666; font-size: 12px;")
    demo_btn_layout.addWidget(window.custom_demo_btn)
    demo_btn_layout.addWidget(window.custom_demo_label)
    demo_btn_layout.addStretch()
    demo_layout.addLayout(demo_btn_layout)
    custom_layout.addLayout(demo_layout)

    # User EXE
    user_layout = QVBoxLayout()
    user_label = QLabel("用户程序")
    user_label.setStyleSheet("color: #666666; font-size: 12px;")
    user_layout.addWidget(user_label)

    user_btn_layout = QHBoxLayout()
    window.custom_user_btn = QPushButton("选择用户EXE")
    window.custom_user_btn.setStyleSheet("""
        QPushButton {
            background-color: #2563EB;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
        }
        QPushButton:hover { background-color: #1D4ED8; }
    """)
    window.custom_user_btn.clicked.connect(lambda: window.select_file("custom_user", "exe"))
    window.custom_user_label = QLabel("未选择")
    window.custom_user_label.setStyleSheet("color: #666666; font-size: 12px;")
    user_btn_layout.addWidget(window.custom_user_btn)
    user_btn_layout.addWidget(window.custom_user_label)
    user_btn_layout.addStretch()
    user_layout.addLayout(user_btn_layout)
    custom_layout.addLayout(user_layout)

    # 测试数据标题
    checkdata_title = QLabel("测试数据")
    checkdata_title.setStyleSheet("color: #1A1A1A; font-size: 14px; font-weight: bold;")
    custom_layout.addWidget(checkdata_title)

    # 预设 / 文件上传 / 在线构造 切换
    window.checkdata_tabs = QTabWidget()
    window.checkdata_tabs.setStyleSheet("""
        QTabWidget::pane {
            border: none;
            background: transparent;
        }
        QTabBar::tab {
            background: #FFFFFF;
            color: #666666;
            padding: 6px 16px;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            margin-right: 4px;
        }
        QTabBar::tab:selected {
            background: #2563EB;
            color: white;
        }
    """)

    # 预设模式：从 data/checkdata 选题目
    preset_cd_widget = QWidget()
    preset_cd_layout = QVBoxLayout(preset_cd_widget)
    preset_cd_layout.setSpacing(8)

    window.checkdata_preset_combo = QComboBox()
    window.checkdata_preset_combo.setStyleSheet("""
        QComboBox {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 6px;
            padding: 10px;
            color: #1A1A1A;
        }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            color: #1A1A1A;
        }
    """)
    preset_cd_layout.addWidget(window.checkdata_preset_combo)
    preset_cd_layout.addStretch()
    window.checkdata_tabs.addTab(preset_cd_widget, "预设")

    # 文件模式
    file_widget = QWidget()
    file_layout = QVBoxLayout(file_widget)
    file_layout.setSpacing(8)

    window.checkdata_file_btn = QPushButton("选择Checkdata文件")
    window.checkdata_file_btn.setStyleSheet("""
        QPushButton {
            background-color: #2563EB;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
        }
        QPushButton:hover { background-color: #1D4ED8; }
    """)
    window.checkdata_file_btn.clicked.connect(window.select_checkdata_file)
    file_layout.addWidget(window.checkdata_file_btn)

    window.checkdata_file_label = QLabel("未选择")
    window.checkdata_file_label.setStyleSheet("color: #666666; font-size: 12px;")
    file_layout.addWidget(window.checkdata_file_label)

    window.checkdata_tabs.addTab(file_widget, "文件")

    # 在线构造模式
    online_widget = QWidget()
    online_layout = QVBoxLayout(online_widget)
    online_layout.setSpacing(8)

    # 添加按钮在滚动区域上方
    window.add_checkpoint_btn = QPushButton("+ 添加检查点")
    window.add_checkpoint_btn.setStyleSheet("""
        QPushButton {
            background-color: #2563EB;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px;
        }
        QPushButton:hover { background-color: #1D4ED8; }
    """)
    window.add_checkpoint_btn.clicked.connect(window.add_checkpoint)
    online_layout.addWidget(window.add_checkpoint_btn)

    # 检查点滚动区域
    window.checkpoint_scroll = QScrollArea()
    window.checkpoint_scroll.setWidgetResizable(True)
    window.checkpoint_scroll.setMinimumHeight(300)
    window.checkpoint_scroll.setStyleSheet("""
        QScrollArea {
            border: 1px solid #E0E0E0;
            border-radius: 6px;
            background: white;
        }
        QScrollBar:vertical {
            background: #F5F5F5;
            width: 6px;
            border-radius: 3px;
        }
        QScrollBar::handle {
            background: #CCCCCC;
            border-radius: 3px;
        }
    """)
    window.checkpoint_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    window.checkpoint_entries = []
    window.checkpoint_container = QVBoxLayout()
    window.checkpoint_container.setSpacing(6)
    window.checkpoint_container.setContentsMargins(0, 0, 0, 0)
    window.checkpoint_container.addStretch(1)

    checkpoint_widget = QWidget()
    checkpoint_widget.setLayout(window.checkpoint_container)
    window.checkpoint_scroll.setWidget(checkpoint_widget)

    online_layout.addWidget(window.checkpoint_scroll)

    window.checkdata_tabs.addTab(online_widget, "在线构造")

    custom_layout.addWidget(window.checkdata_tabs)

    custom_layout.addStretch()

    window.output_sub_tabs.addTab(custom_widget, "自定义")

    left_layout.addWidget(window.output_sub_tabs)

    # 开始测试按钮
    window.output_start_btn = QPushButton("开始测试")
    window.output_start_btn.setStyleSheet("""
        QPushButton {
            background-color: #2563EB;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #1D4ED8; }
    """)
    window.output_start_btn.clicked.connect(window.run_output_test)
    left_layout.addWidget(window.output_start_btn)

    # 配置工具按钮
    window.configure_tools_btn = QPushButton("配置工具")
    window.configure_tools_btn.setStyleSheet("""
        QPushButton {
            background-color: transparent;
            color: #666666;
            border: 1px solid #E0E0E0;
            border-radius: 8px;
            padding: 8px;
            font-size: 12px;
        }
        QPushButton:hover { background-color: #F5F5F5; color: #1A1A1A; }
    """)
    window.configure_tools_btn.clicked.connect(window.open_tools_config)
    left_layout.addWidget(window.configure_tools_btn)

    # 比对参数（置于问题选择下方）
    left_layout.addWidget(tc_group)

    # 状态
    window.output_status = QLabel("")
    window.output_status.setStyleSheet("color: #666666; font-size: 12px;")
    left_layout.addWidget(window.output_status)

    layout.addWidget(left_panel, 1)

    # 右侧：结果展示
    results_card = GlassCard()
    results_layout = QVBoxLayout(results_card)

    results_title = QLabel("测试结果")
    results_title.setStyleSheet("color: #1A1A1A; font-size: 16px; font-weight: bold;")
    results_layout.addWidget(results_title)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("""
        QScrollArea {
            border: none;
            background: transparent;
        }
        QScrollBar:vertical {
            background: #F5F5F5;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle {
            background: #CCCCCC;
            border-radius: 4px;
        }
    """)

    window.output_results_container = QVBoxLayout()
    window.output_results_container.setSpacing(8)

    results_widget = QWidget()
    results_widget.setLayout(window.output_results_container)
    scroll.setWidget(results_widget)

    results_layout.addWidget(scroll)

    layout.addWidget(results_card, 2)

    return tab


def create_source_check_tab(window) -> QWidget:
    """创建源码检查Tab（格式检查+字符集检查）"""
    tab = QWidget()
    layout = QHBoxLayout(tab)
    layout.setSpacing(16)

    # 左侧：源码上传
    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setSpacing(12)

    left_title = QLabel("源码检查")
    left_title.setStyleSheet("color: #1A1A1A; font-size: 14px; font-weight: bold;")
    left_layout.addWidget(left_title)

    # 源码上传
    source_layout = QVBoxLayout()
    source_btn_layout = QHBoxLayout()
    window.source_btn = QPushButton("选择源码文件")
    window.source_btn.setStyleSheet("""
        QPushButton {
            background-color: #2563EB;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
        }
        QPushButton:hover { background-color: #1D4ED8; }
    """)
    window.source_btn.clicked.connect(window.select_source_file)
    window.source_label = QLabel("未选择")
    window.source_label.setStyleSheet("color: #666666; font-size: 12px;")
    source_btn_layout.addWidget(window.source_btn)
    source_btn_layout.addWidget(window.source_label)
    source_btn_layout.addStretch()
    source_layout.addLayout(source_btn_layout)
    left_layout.addLayout(source_layout)

    left_layout.addStretch()

    layout.addWidget(left_widget, 1)

    # 右侧：检查结果
    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setSpacing(12)

    right_title = QLabel("检查结果")
    right_title.setStyleSheet("color: #1A1A1A; font-size: 14px; font-weight: bold;")
    right_layout.addWidget(right_title)

    # 格式检查
    style_layout = QVBoxLayout()
    style_layout.setSpacing(8)

    style_title = QLabel("格式检查")
    style_title.setStyleSheet("color: #1A1A1A; font-size: 13px; font-weight: 600;")
    style_layout.addWidget(style_title)

    window.style_status = QLabel("未检查")
    window.style_status.setStyleSheet("color: #666666; font-size: 12px;")
    style_layout.addWidget(window.style_status)

    window.style_result = QTextEdit()
    window.style_result.setReadOnly(True)
    window.style_result.setStyleSheet("""
        background-color: #FAFAFA;
        border: none;
        border-radius: 6px;
        padding: 8px;
        color: #1A1A1A;
        font-size: 12px;
    """)
    style_layout.addWidget(window.style_result)

    right_layout.addLayout(style_layout)

    # 字符集检查
    encoding_layout = QVBoxLayout()
    encoding_layout.setSpacing(8)

    encoding_title = QLabel("字符集检查")
    encoding_title.setStyleSheet("color: #1A1A1A; font-size: 13px; font-weight: 600;")
    encoding_layout.addWidget(encoding_title)

    window.encoding_status = QLabel("未检查")
    window.encoding_status.setStyleSheet("color: #666666; font-size: 12px;")
    encoding_layout.addWidget(window.encoding_status)

    window.encoding_convert_btn = QPushButton("转换为 GB2312")
    window.encoding_convert_btn.setStyleSheet("""
        QPushButton {
            background-color: #2563EB;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
        }
        QPushButton:hover { background-color: #1D4ED8; }
    """)
    window.encoding_convert_btn.clicked.connect(window.convert_to_gb2312)
    window.encoding_convert_btn.hide()
    encoding_layout.addWidget(window.encoding_convert_btn)

    window.encoding_result = QTextEdit()
    window.encoding_result.setReadOnly(True)
    window.encoding_result.setStyleSheet("""
        background-color: #FAFAFA;
        border: none;
        border-radius: 6px;
        padding: 8px;
        color: #1A1A1A;
        font-size: 12px;
    """)
    encoding_layout.addWidget(window.encoding_result)

    right_layout.addLayout(encoding_layout)

    layout.addWidget(right_widget, 2)

    return tab
