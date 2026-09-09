# -*- coding: utf-8 -*-
"""
设置页面 - 接口配置与导出条数管理 (纯文本无表情符，低饱和度色系)
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QSlider,
    QGroupBox, QFrame, QMessageBox, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class SettingsTab(QWidget):
    """设置页面"""

    connect_requested = pyqtSignal(str, int)
    disconnect_requested = pyqtSignal()
    simulation_requested = pyqtSignal(bool)

    def __init__(self, serial_handler, parent=None):
        super().__init__(parent)
        self.serial_handler = serial_handler
        self.export_count = 100
        self.export_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 16, 24, 24)
        main_layout.setSpacing(20)

        # 顶部标题 (纯文本)
        title = QLabel("系统设置")
        title.setFont(QFont("Microsoft YaHei UI", 15, QFont.Bold))
        title.setStyleSheet("color: #1E2530;")
        main_layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #E5E7EB; max-height: 1px;")
        main_layout.addWidget(line)

        # 接口设置分组框
        serial_group = QGroupBox("接口设置")
        serial_group.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
        serial_group.setStyleSheet("""
            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 20px;
                color: #1E2530;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 6px;
                color: #1E2530;
            }
        """)
        serial_layout = QGridLayout(serial_group)
        serial_layout.setContentsMargins(20, 20, 20, 20)
        serial_layout.setHorizontalSpacing(16)
        serial_layout.setVerticalSpacing(14)

        # 串口号选择
        port_label = QLabel("串口号:")
        port_label.setFont(QFont("Microsoft YaHei UI", 10))
        port_label.setStyleSheet("color: #5E6977;")
        serial_layout.addWidget(port_label, 0, 0)

        self.port_combo = QComboBox()
        self.port_combo.setMinimumHeight(34)
        self.port_combo.setMinimumWidth(200)
        self.port_combo.setFont(QFont("Segoe UI", 10))
        self.port_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 4px 10px;
                background-color: #FFFFFF;
                color: #1E2530;
            }
            QComboBox:focus { border-color: #4A6FA5; }
        """)
        serial_layout.addWidget(self.port_combo, 0, 1)

        # 刷新串口按钮
        refresh_port_btn = QPushButton("刷新")
        refresh_port_btn.setFont(QFont("Microsoft YaHei UI", 9))
        refresh_port_btn.setMinimumHeight(34)
        refresh_port_btn.setCursor(Qt.PointingHandCursor)
        refresh_port_btn.setStyleSheet("""
            QPushButton {
                background-color: #F9FAFB;
                color: #5E6977;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 4px 14px;
            }
            QPushButton:hover { background-color: #F3F4F6; color: #1E2530; }
        """)
        refresh_port_btn.clicked.connect(self._refresh_ports)
        serial_layout.addWidget(refresh_port_btn, 0, 2)

        # 波特率选择
        baud_label = QLabel("波特率:")
        baud_label.setFont(QFont("Microsoft YaHei UI", 10))
        baud_label.setStyleSheet("color: #5E6977;")
        serial_layout.addWidget(baud_label, 1, 0)

        self.baud_combo = QComboBox()
        self.baud_combo.setMinimumHeight(34)
        self.baud_combo.setMinimumWidth(200)
        self.baud_combo.setFont(QFont("Segoe UI", 10))
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("115200")
        self.baud_combo.setStyleSheet(self.port_combo.styleSheet())
        serial_layout.addWidget(self.baud_combo, 1, 1)

        # 操作按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.connect_btn = QPushButton("连接")
        self.connect_btn.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
        self.connect_btn.setMinimumHeight(36)
        self.connect_btn.setMinimumWidth(100)
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A6FA5;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 18px;
            }
            QPushButton:hover { background-color: #3A5A88; }
            QPushButton:disabled { background-color: #E5E7EB; color: #9CA3AF; }
        """)
        self.connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("断开")
        self.disconnect_btn.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
        self.disconnect_btn.setMinimumHeight(36)
        self.disconnect_btn.setMinimumWidth(100)
        self.disconnect_btn.setCursor(Qt.PointingHandCursor)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #BA5B55;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 18px;
            }
            QPushButton:hover { background-color: #9E4843; }
            QPushButton:disabled { background-color: #E5E7EB; color: #9CA3AF; }
        """)
        self.disconnect_btn.clicked.connect(self._on_disconnect)
        btn_layout.addWidget(self.disconnect_btn)

        self.sim_btn = QPushButton("模拟模式")
        self.sim_btn.setFont(QFont("Microsoft YaHei UI", 10))
        self.sim_btn.setMinimumHeight(36)
        self.sim_btn.setMinimumWidth(100)
        self.sim_btn.setCursor(Qt.PointingHandCursor)
        self.sim_btn.setCheckable(True)
        self.sim_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #A57140;
                border: 1px solid #ECC8A4;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover { background-color: #FDF5ED; }
            QPushButton:checked { background-color: #C48A54; color: #FFFFFF; border: none; }
        """)
        self.sim_btn.clicked.connect(self._on_simulation_toggle)
        btn_layout.addWidget(self.sim_btn)

        btn_layout.addStretch()
        serial_layout.addLayout(btn_layout, 2, 0, 1, 3)

        self.connection_status = QLabel("状态: 未连接")
        self.connection_status.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
        self.connection_status.setStyleSheet("color: #BA5B55;")
        serial_layout.addWidget(self.connection_status, 3, 0, 1, 3)

        main_layout.addWidget(serial_group)

        # 数据导出设置
        export_group = QGroupBox("数据导出设置")
        export_group.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
        export_group.setStyleSheet(serial_group.styleSheet())
        export_layout = QGridLayout(export_group)
        export_layout.setContentsMargins(20, 20, 20, 20)
        export_layout.setHorizontalSpacing(16)
        export_layout.setVerticalSpacing(14)

        # 1. 导出保存位置
        dir_label = QLabel("导出保存位置:")
        dir_label.setFont(QFont("Microsoft YaHei UI", 10))
        dir_label.setStyleSheet("color: #5E6977;")
        export_layout.addWidget(dir_label, 0, 0)

        dir_h_layout = QHBoxLayout()
        dir_h_layout.setSpacing(8)

        self.export_dir_edit = QLineEdit(self.export_dir)
        self.export_dir_edit.setMinimumHeight(34)
        self.export_dir_edit.setFont(QFont("Segoe UI", 9))
        self.export_dir_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #FFFFFF;
                color: #1E2530;
            }
            QLineEdit:focus { border-color: #4A6FA5; }
        """)
        dir_h_layout.addWidget(self.export_dir_edit, 1)

        browse_dir_btn = QPushButton("选择位置")
        browse_dir_btn.setFont(QFont("Microsoft YaHei UI", 9))
        browse_dir_btn.setMinimumHeight(34)
        browse_dir_btn.setCursor(Qt.PointingHandCursor)
        browse_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A6FA5;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 14px;
            }
            QPushButton:hover { background-color: #3A5A88; }
        """)
        browse_dir_btn.clicked.connect(self._on_browse_dir)
        dir_h_layout.addWidget(browse_dir_btn)

        open_dir_btn = QPushButton("打开文件夹")
        open_dir_btn.setFont(QFont("Microsoft YaHei UI", 9))
        open_dir_btn.setMinimumHeight(34)
        open_dir_btn.setCursor(Qt.PointingHandCursor)
        open_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #F9FAFB;
                color: #5E6977;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover { background-color: #F3F4F6; color: #1E2530; }
        """)
        open_dir_btn.clicked.connect(self._on_open_dir)
        dir_h_layout.addWidget(open_dir_btn)

        export_layout.addLayout(dir_h_layout, 0, 1, 1, 2)

        # 2. 导出条数
        count_label = QLabel("单次导出条数:")
        count_label.setFont(QFont("Microsoft YaHei UI", 10))
        count_label.setStyleSheet("color: #5E6977;")
        export_layout.addWidget(count_label, 1, 0)

        self.export_slider = QSlider(Qt.Horizontal)
        self.export_slider.setMinimum(10)
        self.export_slider.setMaximum(500)
        self.export_slider.setValue(100)
        self.export_slider.setTickPosition(QSlider.TicksBelow)
        self.export_slider.setTickInterval(50)
        self.export_slider.setMinimumWidth(300)
        self.export_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background-color: #E5E7EB;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background-color: #4A6FA5;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #FFFFFF;
                border: 2px solid #4A6FA5;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        self.export_slider.valueChanged.connect(self._on_slider_changed)
        export_layout.addWidget(self.export_slider, 1, 1)

        self.export_spinbox = QSpinBox()
        self.export_spinbox.setMinimum(10)
        self.export_spinbox.setMaximum(500)
        self.export_spinbox.setValue(100)
        self.export_spinbox.setSuffix(" 条")
        self.export_spinbox.setMinimumHeight(34)
        self.export_spinbox.setMinimumWidth(90)
        self.export_spinbox.setFont(QFont("Segoe UI", 10))
        self.export_spinbox.setStyleSheet("""
            QSpinBox {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #FFFFFF;
                color: #1E2530;
            }
        """)
        self.export_spinbox.valueChanged.connect(self._on_spinbox_changed)
        export_layout.addWidget(self.export_spinbox, 1, 2)

        # 3. 说明
        hint_label = QLabel("说明: 范围 10 ~ 500 条，一键导出时默认保存至上述设定位置")
        hint_label.setFont(QFont("Microsoft YaHei UI", 9))
        hint_label.setStyleSheet("color: #8C96A4;")
        export_layout.addWidget(hint_label, 2, 0, 1, 3)

        main_layout.addWidget(export_group)
        main_layout.addStretch()

        self._refresh_ports()

    def _refresh_ports(self):
        self.port_combo.clear()
        ports = self.serial_handler.get_available_ports()
        if ports:
            self.port_combo.addItems(ports)
        else:
            self.port_combo.addItem("无可用串口")

    def _on_connect(self):
        port = self.port_combo.currentText()
        if port == "无可用串口":
            QMessageBox.warning(self, "提示", "未检测到可用串口，请检查设备连接。")
            return
        baudrate = int(self.baud_combo.currentText())
        self.connect_requested.emit(port, baudrate)

    def _on_disconnect(self):
        self.disconnect_requested.emit()

    def _on_simulation_toggle(self, checked):
        self.simulation_requested.emit(checked)
        if checked:
            self.sim_btn.setText("停止模拟")
        else:
            self.sim_btn.setText("模拟模式")

    def _on_slider_changed(self, value):
        self.export_spinbox.blockSignals(True)
        self.export_spinbox.setValue(value)
        self.export_spinbox.blockSignals(False)
        self.export_count = value

    def _on_spinbox_changed(self, value):
        self.export_slider.blockSignals(True)
        self.export_slider.setValue(value)
        self.export_slider.blockSignals(False)
        self.export_count = value

    def _on_browse_dir(self):
        """选择导出保存目录"""
        current = self.get_export_dir()
        selected = QFileDialog.getExistingDirectory(self, "选择Excel导出保存目录", current)
        if selected:
            self.export_dir = selected
            self.export_dir_edit.setText(selected)

    def _on_open_dir(self):
        """打开当前设定的导出目录"""
        current = self.get_export_dir()
        if os.path.exists(current):
            try:
                os.startfile(current)
            except Exception as e:
                QMessageBox.warning(self, "提示", f"打开目录失败: {str(e)}")
        else:
            QMessageBox.warning(self, "提示", f"指定的目录不存在:\n{current}")

    def get_export_dir(self) -> str:
        """获取当前配置的导出目录"""
        text = self.export_dir_edit.text().strip()
        if text and os.path.exists(text):
            return text
        return self.export_dir

    def get_export_count(self):
        return self.export_count

    def update_connection_status(self, connected: bool):
        if connected:
            self.connection_status.setText("状态: 已连接")
            self.connection_status.setStyleSheet("color: #548C72; font-weight: bold;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
        else:
            self.connection_status.setText("状态: 未连接")
            self.connection_status.setStyleSheet("color: #BA5B55; font-weight: bold;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
