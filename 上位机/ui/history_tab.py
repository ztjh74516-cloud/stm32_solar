# -*- coding: utf-8 -*-
"""
历史数据页面 - 以表格形式展示所有采集到的数据记录
"""

import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QHeaderView,
    QFrame, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class HistoryTab(QWidget):
    """历史数据页面"""

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 16, 24, 24)
        main_layout.setSpacing(16)

        # ===== 顶部标题栏 =====
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        title = QLabel("历史数据记录")
        title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        title.setStyleSheet("color: #1E2530;")
        top_bar.addWidget(title)

        top_bar.addStretch()

        # 数据条数显示
        self.count_label = QLabel("共 0 条记录")
        self.count_label.setFont(QFont("Microsoft YaHei UI", 10))
        self.count_label.setStyleSheet("color: #5E6977; margin-right: 10px;")
        top_bar.addWidget(self.count_label)

        # 刷新按钮 (低饱和度中性灰白)
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFont(QFont("Microsoft YaHei UI", 9))
        refresh_btn.setMinimumHeight(32)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #1E2530;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 4px 14px;
            }
            QPushButton:hover { background-color: #F3F4F6; }
        """)
        refresh_btn.clicked.connect(self.refresh_table)
        top_bar.addWidget(refresh_btn)

        # 清空按钮 (低饱和度砖红)
        clear_btn = QPushButton("清空数据")
        clear_btn.setFont(QFont("Microsoft YaHei UI", 9))
        clear_btn.setMinimumHeight(32)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #BA5B55;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 14px;
            }
            QPushButton:hover { background-color: #9E4843; }
        """)
        clear_btn.clicked.connect(self._on_clear)
        top_bar.addWidget(clear_btn)

        # 导出按钮 (低饱和度莫兰迪绿)
        export_btn = QPushButton("导出Excel")
        export_btn.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        export_btn.setMinimumHeight(32)
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #548C72;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 14px;
            }
            QPushButton:hover { background-color: #426E59; }
        """)
        export_btn.clicked.connect(self._on_export)
        top_bar.addWidget(export_btn)

        main_layout.addLayout(top_bar)

        # ===== 分隔线 =====
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #E0E0E0; max-height: 1px;")
        main_layout.addWidget(line)

        # ===== 数据表格 =====
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "时间", "输入电压 (V)", "输入电流 (A)",
            "输出功率 (W)", "分流采样 (SH)", "保护阈值 (V)", "继电器状态"
        ])

        # 表格样式
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.SolidLine)

        # 设置表头
        header = self.table.horizontalHeader()
        header.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 7):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #F0F0F0;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #F0F0F0;
            }
            QTableWidget::item:alternate {
                background-color: #FAFAFA;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #333333;
            }
            QHeaderView::section {
                background-color: #F8F9FA;
                color: #333333;
                padding: 10px 12px;
                border: none;
                border-bottom: 2px solid #2196F3;
                font-weight: bold;
            }
        """)

        main_layout.addWidget(self.table)

    def refresh_table(self):
        """刷新表格数据"""
        records = self.data_manager.get_all_records()
        self.table.setRowCount(0)

        for record in reversed(records):
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 时间
            time_item = QTableWidgetItem(
                record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            )
            time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, time_item)

            # 电压
            v_item = QTableWidgetItem(f"{record.get('voltage', 0.0):.2f}")
            v_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, v_item)

            # 电流
            c_item = QTableWidgetItem(f"{record.get('current', 0.0):.3f}")
            c_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, c_item)

            # 功率
            p_item = QTableWidgetItem(f"{record.get('power', 0.0):.2f}")
            p_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, p_item)

            # 分流采样 SH
            sh_item = QTableWidgetItem(str(record.get('shunt', 0)))
            sh_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, sh_item)

            # 阈值 TH
            th_item = QTableWidgetItem(f"{record.get('threshold', 0.0):.2f}")
            th_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, th_item)

            # 继电器状态 RLY
            rly_str = str(record.get('relay', 'OFF'))
            rly_item = QTableWidgetItem(rly_str)
            rly_item.setTextAlignment(Qt.AlignCenter)
            if rly_str == 'ON':
                rly_item.setForeground(QColor("#4CAF50"))
            else:
                rly_item.setForeground(QColor("#F44336"))
            self.table.setItem(row, 6, rly_item)

        self.count_label.setText(f"共 {len(records)} 条记录")

    def _on_clear(self):
        """清空所有数据"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有历史数据吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.data_manager.clear_records()
            self.refresh_table()
            QMessageBox.information(self, "完成", "历史数据已全部清空。")

    def _on_export(self):
        """导出数据到Excel"""
        if self.data_manager.get_record_count() == 0:
            QMessageBox.warning(self, "提示", "暂无数据可导出。")
            return

        export_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
        parent = self.parent()
        while parent:
            if hasattr(parent, 'settings_tab'):
                export_dir = parent.settings_tab.get_export_dir()
                break
            parent = parent.parent()

        default_name = f"太阳能历史数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        default_filepath = os.path.join(export_dir, default_name)

        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出数据", default_filepath,
            "Excel 文件 (*.xlsx)"
        )
        if filepath:
            try:
                export_count = self.data_manager.get_record_count()
                self.data_manager.export_to_excel(filepath, count=export_count)
                QMessageBox.information(self, "导出成功",
                                        f"已导出全部 {export_count} 条数据到:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败: {str(e)}")
