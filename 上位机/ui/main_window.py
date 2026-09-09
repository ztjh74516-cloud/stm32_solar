# -*- coding: utf-8 -*-
"""
主窗口 - 整合四个一级选项卡及串口通信/数据流控制 (纯文本无表情符，低饱和度色系)
"""

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar, QLabel, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont

from ui.dashboard_tab import DashboardTab
from ui.history_tab import HistoryTab
from ui.settings_tab import SettingsTab
from ui.curves_tab import CurvesTab


class MainWindow(QMainWindow):
    """太阳能发电系统上位机主窗口"""

    def __init__(self, serial_handler, data_manager, parent=None):
        super().__init__(parent)
        self.serial_handler = serial_handler
        self.data_manager = data_manager

        self.setWindowTitle("STM32 太阳能发电监控系统")
        self.setMinimumSize(1100, 750)
        self.resize(1280, 840)

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # 顶部标题栏 (纯文本)
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        app_title = QLabel("STM32 太阳能发电监控系统")
        app_title.setFont(QFont("Microsoft YaHei UI", 13, QFont.Bold))
        app_title.setStyleSheet("color: #1E2530; border: none;")
        header_layout.addWidget(app_title)

        header_layout.addStretch()

        self.time_label = QLabel("")
        self.time_label.setFont(QFont("Segoe UI", 10))
        self.time_label.setStyleSheet("color: #5E6977; border: none;")
        header_layout.addWidget(self.time_label)

        central_layout.addWidget(header)

        # 选项卡区域 (纯文本)
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Microsoft YaHei UI", 11))
        self.tab_widget.setDocumentMode(True)

        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #F7F8FA;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #FFFFFF;
                color: #5E6977;
                border: none;
                border-bottom: 2px solid transparent;
                padding: 10px 24px;
                margin-right: 2px;
                font-size: 13px;
                font-weight: 500;
                min-width: 90px;
            }
            QTabBar::tab:selected {
                color: #4A6FA5;
                border-bottom: 2px solid #4A6FA5;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                color: #1E2530;
                background-color: #F1F3F5;
            }
        """)

        # 四个一级选项卡 (纯文本无 Emoji)
        self.dashboard_tab = DashboardTab(self.data_manager, self.serial_handler)
        self.history_tab = HistoryTab(self.data_manager)
        self.settings_tab = SettingsTab(self.serial_handler)
        self.curves_tab = CurvesTab()

        self.tab_widget.addTab(self.dashboard_tab, "仪表盘")
        self.tab_widget.addTab(self.history_tab, "历史数据")
        self.tab_widget.addTab(self.settings_tab, "设置")
        self.tab_widget.addTab(self.curves_tab, "可视曲线")

        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        central_layout.addWidget(self.tab_widget)
        self.setCentralWidget(central_widget)

        # 状态栏 (纯文本)
        self.statusBar().setFont(QFont("Microsoft YaHei UI", 9))
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #FFFFFF;
                border-top: 1px solid #E5E7EB;
                color: #5E6977;
                padding: 4px 14px;
            }
        """)
        self.statusBar().showMessage("就绪 | 请选择串口点击连接或启动模拟模式")

        # 时间定时器
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)
        self._update_time()

        self.setStyleSheet("QMainWindow { background-color: #FFFFFF; }")

    def _connect_signals(self):
        """连接所有业务信号"""
        # 串口数据
        self.serial_handler.data_received.connect(self._on_data_received)
        self.serial_handler.raw_data_received.connect(self._on_raw_data_received)
        self.serial_handler.raw_data_sent.connect(self._on_raw_data_sent)
        self.serial_handler.connection_changed.connect(self._on_connection_changed)
        self.serial_handler.error_occurred.connect(self._on_error)

        # 仪表盘控制
        self.dashboard_tab.command_send_requested.connect(self.serial_handler.send_command)
        self.dashboard_tab.connect_requested.connect(self._on_connect_requested)
        self.dashboard_tab.disconnect_requested.connect(self._on_disconnect_requested)
        self.dashboard_tab.simulation_requested.connect(self._on_simulation_requested)

        # 设置页面控制
        self.settings_tab.connect_requested.connect(self._on_connect_requested)
        self.settings_tab.disconnect_requested.connect(self._on_disconnect_requested)
        self.settings_tab.simulation_requested.connect(self._on_simulation_requested)

    @pyqtSlot(dict)
    def _on_data_received(self, data: dict):
        if not self.dashboard_tab.is_monitoring:
            return

        self.data_manager.add_record(data)
        self.dashboard_tab.update_data(data)
        self.curves_tab.update_data(data)

        count = self.data_manager.get_record_count()
        self.statusBar().showMessage(
            f"监视中 | 已记录 {count} 条 | "
            f"输入电压: {data.get('voltage', 0):.2f}V  "
            f"输入电流: {data.get('current', 0):.0f}mA  "
            f"输出功率: {data.get('power', 0):.0f}mW  "
            f"保护阈值: {data.get('threshold', 0):.2f}V  "
            f"继电器: {data.get('relay', 'OFF')}"
        )

    @pyqtSlot(str)
    def _on_raw_data_received(self, line: str):
        self.dashboard_tab.append_terminal_line(line, is_send=False)

    @pyqtSlot(str)
    def _on_raw_data_sent(self, line: str):
        self.dashboard_tab.append_terminal_line(line, is_send=True)

    @pyqtSlot(bool)
    def _on_connection_changed(self, connected: bool):
        self.dashboard_tab.update_connection_status(connected)
        self.settings_tab.update_connection_status(connected)
        if connected:
            self.statusBar().showMessage("串口已连接 | 正在接收数据...")
        else:
            self.statusBar().showMessage("串口已断开 | 请选择串口连接")

    @pyqtSlot(str)
    def _on_error(self, error_msg: str):
        QMessageBox.warning(self, "通信提示", error_msg)
        self.statusBar().showMessage(f"提示: {error_msg}")

    @pyqtSlot(str, int)
    def _on_connect_requested(self, port: str, baudrate: int):
        success = self.serial_handler.connect(port, baudrate)
        if success:
            self.statusBar().showMessage(f"已成功连接到 {port} (波特率: {baudrate})")
            # 同步更新两边界面的串口与波特率显示
            self.dashboard_tab.port_combo.setCurrentText(port)
            self.dashboard_tab.baud_combo.setCurrentText(str(baudrate))
            self.settings_tab.port_combo.setCurrentText(port)
            self.settings_tab.baud_combo.setCurrentText(str(baudrate))
        else:
            QMessageBox.warning(
                self, "连接失败",
                f"无法连接到 {port}。\n\n"
                "常见原因:\n"
                "1. 该串口已被 VSCode 或其他串口工具占用，请先断开其他软件连接。\n"
                "2. CH340 驱动未就绪或 USB 数据线松动。"
            )

    @pyqtSlot()
    def _on_disconnect_requested(self):
        self.serial_handler.disconnect()

    @pyqtSlot(bool)
    def _on_simulation_requested(self, start: bool):
        # 同步更新两个界面的模拟按钮状态
        self.dashboard_tab.sim_btn.blockSignals(True)
        self.dashboard_tab.sim_btn.setChecked(start)
        self.dashboard_tab.sim_btn.setText("停止模拟" if start else "模拟")
        self.dashboard_tab.sim_btn.blockSignals(False)

        self.settings_tab.sim_btn.blockSignals(True)
        self.settings_tab.sim_btn.setChecked(start)
        self.settings_tab.sim_btn.setText("停止模拟" if start else "模拟模式")
        self.settings_tab.sim_btn.blockSignals(False)

        if start:
            self.serial_handler.start_simulation()
            self.statusBar().showMessage("模拟模式运行中...")
            self.dashboard_tab.update_connection_status(True)
        else:
            self.serial_handler.stop_simulation()
            self.statusBar().showMessage("模拟模式已停止")
            self.dashboard_tab.update_connection_status(False)

    def _on_tab_changed(self, index):
        if index == 0:
            self.dashboard_tab.refresh_ports()
        elif index == 1:
            self.history_tab.refresh_table()
        elif index == 2:
            self.settings_tab._refresh_ports()

    def _update_time(self):
        from datetime import datetime
        now = datetime.now()
        self.time_label.setText(now.strftime("%Y-%m-%d %H:%M:%S"))

    def closeEvent(self, event):
        self.serial_handler.disconnect()
        self.serial_handler.stop_simulation()
        event.accept()
