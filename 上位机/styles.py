# -*- coding: utf-8 -*-
"""
styles.py - STM32太阳能发电监控系统 全局样式表与色彩定义模块

设计理念:
1. 极简现代工业设计 (Dieter Rams / Nord / Morandi 色系)
2. 低饱和度高级调色，避免高刺眼荧光色
3. 纯文本无 Emoji 干扰，信息层级清晰、呼吸感充足
"""

# ==============================================================================
# 低饱和度高级色系调色板 (Low-Saturation Palette Constants)
# ==============================================================================
PRIMARY = '#4A6FA5'         # 莫兰迪沉稳蓝 (主色调，稳健专业)
PRIMARY_DARK = '#3A5A88'    # 主色深
PRIMARY_LIGHT = '#E8EEF5'   # 极淡蓝灰背景
PRIMARY_BORDER = '#C3D2E2'

SECONDARY = '#5C8D89'       # 灰调青竹绿 (辅助色)
SECONDARY_DARK = '#48726E'

SUCCESS = '#548C72'         # 莫兰迪鼠尾草绿 (用于导出、已连接、开启状态)
SUCCESS_DARK = '#426E59'
SUCCESS_LIGHT = '#EDF5F1'
SUCCESS_BORDER = '#B8D5C6'

WARNING = '#C48A54'         # 哑光暖赭/陶土色 (用于功率、待定状态)
WARNING_DARK = '#A57140'
WARNING_LIGHT = '#FDF5ED'
WARNING_BORDER = '#ECC8A4'

DANGER = '#BA5B55'          # 莫兰迪砖红/柔和灰红 (用于断开、超限、报警)
DANGER_DARK = '#9E4843'
DANGER_LIGHT = '#FAEEEE'
DANGER_BORDER = '#E8B6B3'

# 中性背景与边框
BG_WHITE = '#FFFFFF'        # 纯白
BG_PAGE = '#F7F8FA'         # 极浅冷灰底色
BG_CARD = '#FFFFFF'         # 卡片背景
BG_HOVER = '#F1F3F5'        # 悬停灰
BORDER = '#E2E5E9'          # 边框主色
BORDER_LIGHT = '#ECEFF2'    # 弱化分割线

# 文字排版色阶
TEXT_PRIMARY = '#1E2530'    # 主标题/数值: 极深石墨炭黑
TEXT_SECONDARY = '#5E6977'  # 副标题/标签: 中性灰
TEXT_MUTED = '#8C96A4'      # 辅助说明/单位: 浅灰
TEXT_DISABLED = '#BAC1CA'   # 禁用文本


def get_main_stylesheet() -> str:
    """获取全局低饱和度 QSS 样式表"""
    return f"""
    * {{
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
        font-size: 13px;
        color: {TEXT_PRIMARY};
    }}

    QMainWindow, QDialog {{
        background-color: {BG_WHITE};
    }}

    /* 选项卡容器 */
    QTabWidget::pane {{
        border: none;
        background-color: {BG_PAGE};
    }}

    QTabWidget::tab-bar {{
        alignment: left;
    }}

    QTabBar::tab {{
        background-color: {BG_WHITE};
        color: {TEXT_SECONDARY};
        border: none;
        border-bottom: 2px solid transparent;
        padding: 10px 24px;
        margin-right: 4px;
        font-size: 13px;
        font-weight: 500;
        min-width: 90px;
    }}

    QTabBar::tab:selected {{
        color: {PRIMARY};
        border-bottom: 2px solid {PRIMARY};
        font-weight: bold;
    }}

    QTabBar::tab:hover:!selected {{
        color: {TEXT_PRIMARY};
        background-color: {BG_HOVER};
    }}

    /* 按钮通用 */
    QPushButton {{
        background-color: {BG_WHITE};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 5px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: {BG_HOVER};
        border-color: {PRIMARY};
        color: {PRIMARY};
    }}

    QPushButton:pressed {{
        background-color: {PRIMARY_LIGHT};
    }}

    QPushButton:disabled {{
        background-color: {BG_PAGE};
        border-color: {BORDER_LIGHT};
        color: {TEXT_DISABLED};
    }}

    /* 表格 */
    QTableWidget {{
        background-color: {BG_WHITE};
        border: 1px solid {BORDER};
        border-radius: 6px;
        gridline-color: {BORDER_LIGHT};
        font-size: 12px;
    }}

    QTableWidget::item {{
        padding: 6px 10px;
        border-bottom: 1px solid {BORDER_LIGHT};
    }}

    QTableWidget::item:alternate {{
        background-color: #FAFBFC;
    }}

    QTableWidget::item:selected {{
        background-color: {PRIMARY_LIGHT};
        color: {TEXT_PRIMARY};
    }}

    QHeaderView::section {{
        background-color: {BG_PAGE};
        color: {TEXT_SECONDARY};
        padding: 8px 10px;
        border: none;
        border-bottom: 1px solid {BORDER};
        font-weight: bold;
        font-size: 12px;
    }}

    /* 分组框 */
    QGroupBox {{
        background-color: {BG_WHITE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 14px;
        padding-top: 16px;
        font-weight: bold;
        color: {TEXT_PRIMARY};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 14px;
        padding: 0 6px;
        color: {TEXT_PRIMARY};
    }}

    /* 输入框与下拉框 */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 4px 8px;
        background-color: {BG_WHITE};
        color: {TEXT_PRIMARY};
        selection-background-color: {PRIMARY};
    }}

    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {PRIMARY};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    /* 滑块 */
    QSlider::groove:horizontal {{
        border: none;
        height: 4px;
        background-color: {BORDER};
        border-radius: 2px;
    }}

    QSlider::sub-page:horizontal {{
        background-color: {PRIMARY};
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        background-color: {BG_WHITE};
        border: 2px solid {PRIMARY};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}

    QSlider::handle:horizontal:hover {{
        background-color: {PRIMARY_LIGHT};
    }}

    /* 状态栏 */
    QStatusBar {{
        background-color: {BG_WHITE};
        border-top: 1px solid {BORDER};
        color: {TEXT_MUTED};
        padding: 4px 14px;
    }}
    """
