# -*- coding: utf-8 -*-
"""
可视曲线页面 - 输入/输出电压、电流、功率多通道实时曲线
根据《太阳能历史数据1.xlsx》实测数据定制坐标系量程:
  - 实测输入电压 V: 0.14V ~ 4.69V (阈值 5.00V) -> 坐标系固定为 0.0 ~ 6.0 V
  - 实测输入电流 I: 0 ~ 948 mA -> 坐标系固定为 0 ~ 1200 mA
  - 实测功率 P: 0 ~ 3610 mW -> 坐标系固定为 0 ~ 4000 mW
坐标轴严格锁定，禁止滚轮与鼠标拖拽缩放，保证波形稳定清晰。
"""

import time
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import pyqtgraph as pg


class DualMetricChart(QFrame):
    """固定坐标系的双通道对比图表 (支持输入线、输出线、阈值线)"""

    def __init__(self, title, y_label, unit,
                 in_name="输入", in_color="#2196F3",
                 out_name="输出", out_color="#4CAF50",
                 has_out=True,
                 y_min=0.0, y_max=6.0,
                 threshold_color="#F44336",
                 has_threshold=False,
                 parent=None):
        super().__init__(parent)
        self.title_text = title
        self.unit = unit
        self.has_out = has_out
        self.has_threshold = has_threshold
        self.max_points = 300

        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(4)

        # ===== 顶部栏：标题 + 实时数值 =====
        top_layout = QHBoxLayout()

        chart_title = QLabel(title)
        chart_title.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
        chart_title.setStyleSheet("color: #333333; border: none;")
        top_layout.addWidget(chart_title)

        top_layout.addStretch()

        # 输入当前值
        self.in_val_label = QLabel(f"{in_name}: -- {unit}")
        self.in_val_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.in_val_label.setStyleSheet(f"color: {in_color}; border: none;")
        top_layout.addWidget(self.in_val_label)

        if has_out:
            top_layout.addSpacing(12)
            self.out_val_label = QLabel(f"{out_name}: -- {unit}")
            self.out_val_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.out_val_label.setStyleSheet(f"color: {out_color}; border: none;")
            top_layout.addWidget(self.out_val_label)

        if has_threshold:
            top_layout.addSpacing(12)
            self.th_val_label = QLabel(f"阈值: -- {unit}")
            self.th_val_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.th_val_label.setStyleSheet(f"color: {threshold_color}; border: none;")
            top_layout.addWidget(self.th_val_label)

        layout.addLayout(top_layout)

        # ===== 图表区域 =====
        pg.setConfigOptions(antialias=True)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setLabel('left', y_label, units=unit, color='#333333')
        self.plot_widget.setLabel('bottom', '时间 (秒)', color='#666666')

        # ★★★ 彻底禁止滚轮与鼠标缩放/拖拽，坐标系尺度固定 ★★★
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.getViewBox().setMenuEnabled(False)

        # 固定设定 Y 轴物理范围
        self.y_min = y_min
        self.y_max = y_max
        self.plot_widget.setYRange(y_min, y_max, padding=0.0)

        # 坐标轴样式配置
        for axis_name in ['left', 'bottom']:
            axis = self.plot_widget.getAxis(axis_name)
            axis.setPen(pg.mkPen(color='#D0D0D0', width=1))
            axis.setTextPen(pg.mkPen(color='#666666'))
            axis.setStyle(tickFont=QFont("Segoe UI", 8))

        # 图例说明 (右上角)
        self.legend = self.plot_widget.addLegend(offset=(-10, 10))
        self.legend.setBrush(pg.mkBrush(255, 255, 255, 200))
        self.legend.setPen(pg.mkPen('#E0E0E0'))

        # 输入曲线
        pen_in = pg.mkPen(color=in_color, width=2.2)
        self.curve_in = self.plot_widget.plot(pen=pen_in, name=in_name)

        # 输出曲线
        if has_out:
            pen_out = pg.mkPen(color=out_color, width=2.0, style=Qt.SolidLine)
            self.curve_out = self.plot_widget.plot(pen=pen_out, name=out_name)
        else:
            self.curve_out = None

        # 阈值线
        if has_threshold:
            threshold_pen = pg.mkPen(color=threshold_color, width=1.8, style=Qt.DashLine)
            self.threshold_line = pg.InfiniteLine(
                pos=5.0, angle=0, pen=threshold_pen,
                label='保护阈值: 5.0V',
                labelOpts={'position': 0.92, 'color': threshold_color, 'fill': '#FFFFFF'}
            )
            self.plot_widget.addItem(self.threshold_line)
        else:
            self.threshold_line = None

        self.plot_widget.setStyleSheet("border: none;")
        layout.addWidget(self.plot_widget)

        # 数据存储
        self.x_data = []
        self.y_in_data = []
        self.y_out_data = []
        self.start_time = time.time()

    def update_values(self, val_in: float, val_out: float = None, threshold: float = None):
        """更新图表数据点"""
        elapsed = time.time() - self.start_time
        self.x_data.append(elapsed)
        self.y_in_data.append(val_in)

        if self.has_out and val_out is not None:
            self.y_out_data.append(val_out)

        # 保持点数在上限以内
        if len(self.x_data) > self.max_points:
            self.x_data = self.x_data[-self.max_points:]
            self.y_in_data = self.y_in_data[-self.max_points:]
            if self.has_out:
                self.y_out_data = self.y_out_data[-self.max_points:]

        # 刷新曲线
        x_arr = np.array(self.x_data)
        self.curve_in.setData(x_arr, np.array(self.y_in_data))

        if self.has_out and self.curve_out is not None and self.y_out_data:
            self.curve_out.setData(x_arr, np.array(self.y_out_data))

        # 阈值线更新
        if self.threshold_line is not None and threshold is not None:
            self.threshold_line.setValue(threshold)
            self.threshold_line.label.setText(f"保护阈值: {threshold:.2f}{self.unit}")
            self.th_val_label.setText(f"阈值: {threshold:.2f} {self.unit}")

        # X 轴时间自动滚动展示 (固定最近 60 秒)
        if elapsed > 60:
            self.plot_widget.setXRange(elapsed - 60, elapsed, padding=0.0)
        else:
            self.plot_widget.setXRange(0, max(elapsed, 10), padding=0.0)

        # 固定 Y 轴范围，防止任何漂移
        self.plot_widget.setYRange(self.y_min, self.y_max, padding=0.0)

        # 更新标签
        self.in_val_label.setText(f"输入: {val_in:.2f} {self.unit}")
        if self.has_out and val_out is not None:
            self.out_val_label.setText(f"输出: {val_out:.2f} {self.unit}")

    def clear_data(self):
        self.x_data = []
        self.y_in_data = []
        self.y_out_data = []
        self.start_time = time.time()
        self.curve_in.setData([], [])
        if self.curve_out:
            self.curve_out.setData([], [])


class CurvesTab(QWidget):
    """可视曲线页面 - 严格根据实测数据量程对齐"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 14)
        main_layout.setSpacing(10)

        # ===== 顶部标题栏 =====
        top_layout = QHBoxLayout()

        title = QLabel("输入与输出特性曲线")
        title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        title.setStyleSheet("color: #1E2530;")
        top_layout.addWidget(title)

        top_layout.addSpacing(16)

        desc = QLabel("坐标系已按实测值锁定: 电压 [0~6V] · 电流 [0~1200mA] · 功率 [0~4000mW] (禁止滚轮缩放)")
        desc.setFont(QFont("Microsoft YaHei UI", 9))
        desc.setStyleSheet("color: #5E6977;")
        top_layout.addWidget(desc)

        top_layout.addStretch()

        main_layout.addLayout(top_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #E5E7EB; max-height: 1px;")
        main_layout.addWidget(line)

        # ===== 三个图表垂直排列 =====
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;
                height: 6px;
            }
        """)
        splitter.setHandleWidth(6)

        # 1. 电压曲线 (输入 vs 输出 vs 阈值)
        self.voltage_chart = DualMetricChart(
            title="电压特性对比 (V)",
            y_label="电压",
            unit="V",
            in_name="输入电压 (PV)",
            in_color="#4A6FA5",       # 莫兰迪蓝
            out_name="输出电压 (OUT)",
            out_color="#548C72",      # 莫兰迪绿
            has_out=True,
            y_min=0.0,
            y_max=6.0,
            threshold_color="#BA5B55", # 砖红阈值虚线
            has_threshold=True
        )
        splitter.addWidget(self.voltage_chart)

        # 2. 电流曲线 (输入 vs 输出)
        self.current_chart = DualMetricChart(
            title="电流特性对比 (mA)",
            y_label="电流",
            unit="mA",
            in_name="输入电流 (I)",
            in_color="#5C8D89",       # 莫兰迪青绿
            out_name="输出电流 (OUT_I)",
            out_color="#C48A54",      # 莫兰迪暖赭
            has_out=True,
            y_min=0.0,
            y_max=1200.0,
            has_threshold=False
        )
        splitter.addWidget(self.current_chart)

        # 3. 功率曲线
        self.power_chart = DualMetricChart(
            title="实时输出功率 (mW)",
            y_label="功率",
            unit="mW",
            in_name="发电功率 (P)",
            in_color="#A67C52",       # 哑光茶金
            has_out=False,
            y_min=0.0,
            y_max=4000.0,
            has_threshold=False
        )
        splitter.addWidget(self.power_chart)

        # 等分三栏高度
        splitter.setSizes([1, 1, 1])
        main_layout.addWidget(splitter)

    def update_data(self, data: dict):
        """更新所有图表数据"""
        # 电压数据 (V)
        v_in = float(data.get('voltage', 0.0))
        v_out = float(data.get('out_voltage', v_in if data.get('relay') == 'ON' else 0.0))
        th = float(data.get('threshold', 5.0))
        self.voltage_chart.update_values(v_in, v_out, th)

        # 电流数据 (mA)
        c_in = float(data.get('current', 0.0))
        c_out = float(data.get('out_current', c_in if data.get('relay') == 'ON' else 0.0))
        self.current_chart.update_values(c_in, c_out)

        # 功率数据 (mW)
        p = float(data.get('power', 0.0))
        self.power_chart.update_values(p)
        # 辅助更新功率卡片上的瓦数换算
        w_val = p / 1000.0
        self.power_chart.in_val_label.setText(f"功率: {p:.0f} mW ({w_val:.2f} W)")
