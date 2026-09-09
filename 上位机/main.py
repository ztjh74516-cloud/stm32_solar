# -*- coding: utf-8 -*-
"""
STM32 太阳能发电监控系统 - 上位机程序入口
极简工业设计，低饱和度色系，纯文本界面
"""

import sys
import os

# 确保当前目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QLinearGradient
from PyQt5.QtCore import Qt, QTimer

from serial_handler import SerialHandler
from data_manager import DataManager
from styles import get_main_stylesheet
from ui.main_window import MainWindow


def create_splash_pixmap():
    """创建极简低饱和度启动画面"""
    pixmap = QPixmap(460, 240)
    pixmap.fill(QColor("#FFFFFF"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # 顶部细横线
    gradient = QLinearGradient(0, 0, 460, 0)
    gradient.setColorAt(0, QColor("#4A6FA5"))
    gradient.setColorAt(1, QColor("#5C8D89"))
    painter.setBrush(gradient)
    painter.setPen(Qt.NoPen)
    painter.drawRect(0, 0, 460, 4)

    # 边框
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QColor("#E5E7EB"))
    painter.drawRect(0, 0, 459, 239)

    # 标题 (纯文本)
    painter.setPen(QColor("#1E2530"))
    painter.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
    painter.drawText(pixmap.rect().adjusted(0, 50, 0, 0),
                     Qt.AlignHCenter, "STM32 太阳能发电监控系统")

    # 副标题
    painter.setPen(QColor("#5E6977"))
    painter.setFont(QFont("Microsoft YaHei UI", 10))
    painter.drawText(pixmap.rect().adjusted(0, 100, 0, 0),
                     Qt.AlignHCenter, "STM32F103C8T6 硬件监控与控制工作台")

    # 加载提示
    painter.setPen(QColor("#4A6FA5"))
    painter.setFont(QFont("Microsoft YaHei UI", 9))
    painter.drawText(pixmap.rect().adjusted(0, 160, 0, 0),
                     Qt.AlignHCenter, "系统初始化中...")

    # 版本
    painter.setPen(QColor("#9CA3AF"))
    painter.setFont(QFont("Segoe UI", 9))
    painter.drawText(pixmap.rect().adjusted(0, 0, -16, -12),
                     Qt.AlignRight | Qt.AlignBottom, "v1.1.0")

    painter.end()
    return pixmap


def main():
    """程序主入口"""
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 10))

    # 应用低饱和度全局样式表
    app.setStyleSheet(get_main_stylesheet())

    splash_pixmap = create_splash_pixmap()
    splash = QSplashScreen(splash_pixmap)
    splash.show()
    app.processEvents()

    serial_handler = SerialHandler()
    data_manager = DataManager()
    window = MainWindow(serial_handler, data_manager)

    # 注册退出清理钩子：确保无论点击右上角叉号、快捷键退出或程序意外终止，串口都能 100% 释放
    import atexit
    atexit.register(serial_handler.disconnect)
    app.aboutToQuit.connect(serial_handler.disconnect)

    def show_main():
        splash.close()
        window.show()

    QTimer.singleShot(800, show_main)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
