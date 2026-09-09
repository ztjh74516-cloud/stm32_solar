# -*- coding: utf-8 -*-
"""
仪表盘页面 - 极简纯文本设计，低饱和度高级工业配色
功能:
  - 顶部串口控制栏: 串口/波特率、连接/断开/模拟模式、开始监视/暂停监视、导出Excel
  - 核心数据看板 (输入输出电压、电流、功率、保护阈值、分流采样、继电器状态)
  - 底部串口通信终端 (实时查看收发数据、快捷发送修改电压阈值)
"""

import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QFileDialog, QMessageBox,
    QTextEdit, QLineEdit, QDoubleSpinBox, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QTextCursor


class DataCard(QFrame):
    """极简纯文本数据卡片"""

    def __init__(self, title, unit, accent_color="#4A6FA5", parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.unit = unit
        self.setMinimumHeight(105)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        # 标题栏 (纯文本，无表情符)
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Microsoft YaHei UI", 9))
        self.title_label.setStyleSheet("color: #5E6977; border: none; background: transparent;")
        layout.addWidget(self.title_label)

        # 核心数值
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont("Segoe UI", 21, QFont.Bold))
        layout.addWidget(self.value_label)

        # 物理单位/说明
        self.unit_label = QLabel(unit)
        self.unit_label.setFont(QFont("Microsoft YaHei UI", 8))
        self.unit_label.setStyleSheet("color: #8C96A4; border: none; background: transparent;")
        layout.addWidget(self.unit_label)

        self.set_accent_color(accent_color)

    def set_accent_color(self, accent_color: str):
        self.accent_color = accent_color
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                border-top: 3px solid {accent_color};
            }}
        """)
        self.value_label.setStyleSheet(f"color: {accent_color}; border: none; background: transparent; font-weight: bold;")

    def set_value(self, value):
        if isinstance(value, float):
            self.value_label.setText(f"{value:.2f}")
        else:
            self.value_label.setText(str(value))

    def set_unit(self, unit: str):
        self.unit = unit
        self.unit_label.setText(unit)


class DashboardTab(QWidget):
    """仪表盘主页面"""

    command_send_requested = pyqtSignal(str)
    connect_requested = pyqtSignal(str, int)
    disconnect_requested = pyqtSignal()
    simulation_requested = pyqtSignal(bool)
    monitoring_changed = pyqtSignal(bool)

    def __init__(self, data_manager, serial_handler=None, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.serial_handler = serial_handler
        self.is_monitoring = True

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 14)
        main_layout.setSpacing(10)

        # ===== 顶部快捷操作栏 =====
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        title = QLabel("实时运行监控")
        title.setFont(QFont("Microsoft YaHei UI", 13, QFont.Bold))
        title.setStyleSheet("color: #1E2530;")
        top_bar.addWidget(title)

        top_bar.addSpacing(8)

        # 串口号选择
        self.port_combo = QComboBox()
        self.port_combo.setFixedHeight(30)
        self.port_combo.setMinimumWidth(85)
        self.port_combo.setFont(QFont("Segoe UI", 9))
        self.port_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 2px 6px;
                background-color: #FFFFFF;
                color: #1E2530;
            }
        """)
        top_bar.addWidget(self.port_combo)

        # 波特率选择
        self.baud_combo = QComboBox()
        self.baud_combo.setFixedHeight(30)
        self.baud_combo.setMinimumWidth(85)
        self.baud_combo.setFont(QFont("Segoe UI", 9))
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("115200")
        self.baud_combo.setStyleSheet(self.port_combo.styleSheet())
        top_bar.addWidget(self.baud_combo)

        # 连接按钮 (低饱和度蓝)
        self.connect_btn = QPushButton("连接")
        self.connect_btn.setFixedHeight(30)
        self.connect_btn.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A6FA5;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover { background-color: #3A5A88; }
            QPushButton:disabled { background-color: #E5E7EB; color: #9CA3AF; }
        """)
        self.connect_btn.clicked.connect(self._on_connect)
        top_bar.addWidget(self.connect_btn)

        # 断开按钮 (低饱和度灰红)
        self.disconnect_btn = QPushButton("断开")
        self.disconnect_btn.setFixedHeight(30)
        self.disconnect_btn.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        self.disconnect_btn.setCursor(Qt.PointingHandCursor)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #BA5B55;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover { background-color: #9E4843; }
            QPushButton:disabled { background-color: #E5E7EB; color: #9CA3AF; }
        """)
        self.disconnect_btn.clicked.connect(self._on_disconnect)
        top_bar.addWidget(self.disconnect_btn)

        # 模拟模式按钮 (低饱和度暖茶色)
        self.sim_btn = QPushButton("模拟")
        self.sim_btn.setFixedHeight(30)
        self.sim_btn.setFont(QFont("Microsoft YaHei UI", 9))
        self.sim_btn.setCursor(Qt.PointingHandCursor)
        self.sim_btn.setCheckable(True)
        self.sim_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #A57140;
                border: 1px solid #ECC8A4;
                border-radius: 4px;
                padding: 4px 10px;
            }
            QPushButton:hover { background-color: #FDF5ED; }
            QPushButton:checked { background-color: #C48A54; color: #FFFFFF; border: none; }
        """)
        self.sim_btn.clicked.connect(self._on_simulation_toggle)
        top_bar.addWidget(self.sim_btn)

        # 垂直分隔线
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setStyleSheet("color: #E5E7EB; max-width: 1px;")
        top_bar.addWidget(sep1)

        # 开始/暂停监视按钮 (仅四个汉字: "暂停监视" 或 "开始监视")
        self.monitor_btn = QPushButton("暂停监视")
        self.monitor_btn.setFixedHeight(30)
        self.monitor_btn.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        self.monitor_btn.setCursor(Qt.PointingHandCursor)
        self.monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #EDF5F1;
                color: #426E59;
                border: 1px solid #B8D5C6;
                border-radius: 4px;
                padding: 4px 14px;
            }
            QPushButton:hover { background-color: #DCEDE4; }
        """)
        self.monitor_btn.clicked.connect(self._toggle_monitoring)
        top_bar.addWidget(self.monitor_btn)

        top_bar.addStretch()

        # 连接状态文字指示
        self.status_indicator = QLabel("未连接")
        self.status_indicator.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        self.status_indicator.setStyleSheet("color: #BA5B55; margin-right: 6px;")
        top_bar.addWidget(self.status_indicator)

        # 导出Excel按钮 (低饱和度莫兰迪绿)
        self.export_btn = QPushButton("导出Excel")
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.setFixedHeight(30)
        self.export_btn.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setStyleSheet("""
            QPushButton#exportBtn {
                background-color: #548C72;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 14px;
            }
            QPushButton#exportBtn:hover { background-color: #426E59; }
        """)
        self.export_btn.clicked.connect(self._on_export)
        top_bar.addWidget(self.export_btn)

        main_layout.addLayout(top_bar)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #E5E7EB; max-height: 1px;")
        main_layout.addWidget(line)

        # ===== 核心数据卡片 (低饱和度色系，一行4个) =====
        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(10)
        cards_layout.setVerticalSpacing(8)

        # 第一行: 输入电压、电流、功率、累计电量
        self.card_voltage = DataCard("输入电压 (V)", "伏特", "#4A6FA5")
        self.card_current = DataCard("输入电流 (I)", "毫安", "#5C8D89")
        self.card_power = DataCard("输出功率 (P)", "毫瓦", "#C48A54")
        self.card_energy = DataCard("累计电量 (E)", "毫瓦时 (mWh)", "#2A8C82")

        # 第二行: 阈值、采样、继电器、预留占位卡片
        self.card_threshold = DataCard("保护阈值 (TH)", "伏特", "#7A6F8D")
        self.card_shunt = DataCard("分流采样 (SH)", "计数值", "#64748B")

        # 继电器状态卡片 (统一使用 DataCard，确保边框与卡片样式一致)
        self.relay_card = DataCard("继电器状态 (RLY)", "过压保护动作开关", "#BA5B55")
        self.relay_card.set_value("OFF")
        self.relay_status_label = self.relay_card.value_label
        self.relay_sub_label = self.relay_card.unit_label

        # 预留占位卡片 (第二行第4个，统一使用 DataCard，确保边框一致)
        self.card_placeholder = DataCard("系统扩展通道", "预留扩展通道", "#9CA3AF")
        self.card_placeholder.set_value("待添加")
        self.card_placeholder.value_label.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold))
        self.ph_value_label = self.card_placeholder.value_label
        self.ph_sub_label = self.card_placeholder.unit_label

        # 栅格布局 (2行4列)
        cards_layout.addWidget(self.card_voltage, 0, 0)
        cards_layout.addWidget(self.card_current, 0, 1)
        cards_layout.addWidget(self.card_power, 0, 2)
        cards_layout.addWidget(self.card_energy, 0, 3)

        cards_layout.addWidget(self.card_threshold, 1, 0)
        cards_layout.addWidget(self.card_shunt, 1, 1)
        cards_layout.addWidget(self.relay_card, 1, 2)
        cards_layout.addWidget(self.card_placeholder, 1, 3)

        cards_layout.setColumnStretch(0, 1)
        cards_layout.setColumnStretch(1, 1)
        cards_layout.setColumnStretch(2, 1)
        cards_layout.setColumnStretch(3, 1)

        main_layout.addLayout(cards_layout)

        # ===== 底部通信终端 (极简纯文本) =====
        terminal_group = QFrame()
        terminal_group.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
            }
        """)
        terminal_layout = QVBoxLayout(terminal_group)
        terminal_layout.setContentsMargins(12, 8, 12, 10)
        terminal_layout.setSpacing(6)

        # 终端顶部控制栏
        term_header = QHBoxLayout()
        term_title = QLabel("串口通信终端")
        term_title.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
        term_title.setStyleSheet("color: #1E2530; border: none;")
        term_header.addWidget(term_title)

        term_header.addSpacing(12)

        self.chk_autoscroll = QCheckBox("自动滚屏")
        self.chk_autoscroll.setChecked(True)
        self.chk_autoscroll.setFont(QFont("Microsoft YaHei UI", 9))
        self.chk_autoscroll.setStyleSheet("color: #5E6977; border: none;")
        term_header.addWidget(self.chk_autoscroll)

        self.chk_timestamp = QCheckBox("时间戳")
        self.chk_timestamp.setChecked(True)
        self.chk_timestamp.setFont(QFont("Microsoft YaHei UI", 9))
        self.chk_timestamp.setStyleSheet("color: #5E6977; border: none;")
        term_header.addWidget(self.chk_timestamp)

        term_header.addStretch()

        clear_btn = QPushButton("清空输出")
        clear_btn.setFont(QFont("Microsoft YaHei UI", 9))
        clear_btn.setFixedHeight(24)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #F9FAFB;
                color: #5E6977;
                border: 1px solid #E5E7EB;
                border-radius: 3px;
                padding: 2px 8px;
            }
            QPushButton:hover { background-color: #F3F4F6; }
        """)
        clear_btn.clicked.connect(self._clear_terminal)
        term_header.addWidget(clear_btn)

        terminal_layout.addLayout(term_header)

        # 终端控制台 (柔和深炭色，等宽字符)
        self.terminal_text = QTextEdit()
        self.terminal_text.setReadOnly(True)
        self.terminal_text.setMinimumHeight(120)
        self.terminal_text.setFont(QFont("Consolas", 10))
        self.terminal_text.setStyleSheet("""
            QTextEdit {
                background-color: #21262D;
                color: #C9D1D9;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 6px;
                line-height: 1.4;
            }
        """)
        terminal_layout.addWidget(self.terminal_text)

        # 发送栏
        send_bar = QHBoxLayout()
        send_bar.setSpacing(8)

        th_label = QLabel("修改电压阈值:")
        th_label.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        th_label.setStyleSheet("color: #1E2530; border: none;")
        send_bar.addWidget(th_label)

        self.th_spinbox = QDoubleSpinBox()
        self.th_spinbox.setMinimum(0.0)
        self.th_spinbox.setMaximum(25.0)
        self.th_spinbox.setValue(5.0)
        self.th_spinbox.setSingleStep(0.1)
        self.th_spinbox.setDecimals(2)
        self.th_spinbox.setSuffix(" V")
        self.th_spinbox.setMinimumWidth(85)
        self.th_spinbox.setFixedHeight(28)
        self.th_spinbox.setFont(QFont("Segoe UI", 9))
        self.th_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #D1D5DB;
                border-radius: 3px;
                padding: 2px 4px;
                background-color: #FFFFFF;
            }
        """)
        send_bar.addWidget(self.th_spinbox)

        set_th_btn = QPushButton("发送阈值")
        set_th_btn.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        set_th_btn.setFixedHeight(28)
        set_th_btn.setCursor(Qt.PointingHandCursor)
        set_th_btn.setStyleSheet("""
            QPushButton {
                background-color: #7A6F8D;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                padding: 3px 10px;
            }
            QPushButton:hover { background-color: #685E78; }
        """)
        set_th_btn.clicked.connect(self._on_send_threshold)
        send_bar.addWidget(set_th_btn)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet("color: #E5E7EB; max-width: 1px;")
        send_bar.addWidget(sep2)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("输入指令/数值回车发送 (例如 5.00)")
        self.cmd_input.setFont(QFont("Segoe UI", 9))
        self.cmd_input.setFixedHeight(28)
        self.cmd_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 3px;
                padding: 3px 6px;
                background-color: #FFFFFF;
            }
            QLineEdit:focus { border-color: #4A6FA5; }
        """)
        self.cmd_input.returnPressed.connect(self._on_send_command)
        send_bar.addWidget(self.cmd_input, 1)

        send_btn = QPushButton("发送")
        send_btn.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        send_btn.setFixedHeight(28)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A6FA5;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                padding: 3px 14px;
            }
            QPushButton:hover { background-color: #3A5A88; }
        """)
        send_btn.clicked.connect(self._on_send_command)
        send_bar.addWidget(send_btn)

        terminal_layout.addLayout(send_bar)
        main_layout.addWidget(terminal_group)

        # 初始化刷新串口列表
        self.refresh_ports()

    # ===== 交互逻辑 =====

    def refresh_ports(self):
        self.port_combo.clear()
        if self.serial_handler:
            ports = self.serial_handler.get_available_ports()
            if ports:
                self.port_combo.addItems(ports)
                return
        self.port_combo.addItem("无可用串口")

    def _on_connect(self):
        port = self.port_combo.currentText()
        if port == "无可用串口":
            QMessageBox.warning(self, "提示", "未检测到可用串口，请检查设备连接。")
            return
        baud = int(self.baud_combo.currentText())
        self.connect_requested.emit(port, baud)

    def _on_disconnect(self):
        self.disconnect_requested.emit()

    def _on_simulation_toggle(self, checked):
        self.simulation_requested.emit(checked)
        if checked:
            self.sim_btn.setText("停止模拟")
        else:
            self.sim_btn.setText("模拟")

    def _toggle_monitoring(self):
        """只展示四字按钮: '暂停监视' 或 '开始监视'"""
        self.is_monitoring = not self.is_monitoring
        self.monitoring_changed.emit(self.is_monitoring)

        if self.is_monitoring:
            self.monitor_btn.setText("暂停监视")
            self.monitor_btn.setStyleSheet("""
                QPushButton {
                    background-color: #EDF5F1;
                    color: #426E59;
                    border: 1px solid #B8D5C6;
                    border-radius: 4px;
                    padding: 4px 14px;
                }
                QPushButton:hover { background-color: #DCEDE4; }
            """)
        else:
            self.monitor_btn.setText("开始监视")
            self.monitor_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FDF5ED;
                    color: #A57140;
                    border: 1px solid #ECC8A4;
                    border-radius: 4px;
                    padding: 4px 14px;
                }
                QPushButton:hover { background-color: #F8E7D5; }
            """)

    def update_data(self, data: dict):
        if not self.is_monitoring:
            return

        if 'voltage' in data:
            self.card_voltage.set_value(data['voltage'])

        if 'current' in data:
            self.card_current.set_value(data['current'])

        if 'power' in data:
            self.card_power.set_value(data['power'])

        # 累计发电量更新
        mwh = None
        if 'energy_mwh' in data:
            mwh = float(data['energy_mwh'])
        elif self.data_manager and hasattr(self.data_manager, 'get_total_energy_mwh'):
            mwh = self.data_manager.get_total_energy_mwh()

        if mwh is not None:
            if mwh < 1000.0:
                self.card_energy.set_value(f"{mwh:.2f}")
                self.card_energy.set_unit("毫瓦时 (mWh)")
            else:
                self.card_energy.set_value(f"{mwh / 1000.0:.3f}")
                self.card_energy.set_unit("瓦时 (Wh)")

        if 'threshold' in data:
            self.card_threshold.set_value(data['threshold'])

        if 'shunt' in data:
            self.card_shunt.set_value(data['shunt'])

        if 'relay' in data:
            rly = str(data['relay']).upper()
            self.relay_card.set_value(rly)
            if rly == 'ON':
                self.relay_card.set_accent_color("#548C72")
            else:
                self.relay_card.set_accent_color("#BA5B55")

    def append_terminal_line(self, line: str, is_send: bool = False):
        if not self.is_monitoring and not is_send:
            return

        now_str = ""
        if self.chk_timestamp.isChecked():
            now_str = f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "

        if is_send:
            formatted = f'<span style="color: #7EA1C4;">{now_str}发送: {line}</span>'
        else:
            formatted = f'<span style="color: #6E7681;">{now_str}</span><span style="color: #C9D1D9;">{line}</span>'

        self.terminal_text.append(formatted)

        if self.chk_autoscroll.isChecked():
            self.terminal_text.moveCursor(QTextCursor.End)

    def _clear_terminal(self):
        self.terminal_text.clear()

    def _on_send_threshold(self):
        val = self.th_spinbox.value()
        self.command_send_requested.emit(f"{val:.2f}")

    def _on_send_command(self):
        text = self.cmd_input.text().strip()
        if text:
            self.command_send_requested.emit(text)
            self.cmd_input.clear()

    def update_connection_status(self, connected: bool):
        if connected:
            self.status_indicator.setText("已连接")
            self.status_indicator.setStyleSheet("color: #548C72; font-weight: bold; margin-right: 6px;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
        else:
            self.status_indicator.setText("未连接")
            self.status_indicator.setStyleSheet("color: #BA5B55; font-weight: bold; margin-right: 6px;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)

    def _on_export(self):
        if self.data_manager.get_record_count() == 0:
            QMessageBox.warning(self, "提示", "暂无数据可导出。")
            return

        export_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
        export_count = 100
        parent = self.parent()
        while parent:
            if hasattr(parent, 'settings_tab'):
                export_count = parent.settings_tab.get_export_count()
                export_dir = parent.settings_tab.get_export_dir()
                break
            parent = parent.parent()

        default_name = f"太阳能数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        default_filepath = os.path.join(export_dir, default_name)

        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出数据", default_filepath,
            "Excel 文件 (*.xlsx)"
        )
        if filepath:
            try:
                self.data_manager.export_to_excel(filepath, count=export_count)
                QMessageBox.information(self, "导出成功", f"数据已导出到:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败: {str(e)}")
