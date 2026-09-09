# -*- coding: utf-8 -*-
"""
STM32太阳能发电监控系统 - 串口通信处理模块
文件路径: serial_handler.py

与 STM32F103C8T6 下位机通信:
下位机协议上报格式:
    V:0.16, I:0, SH:-1, P:0, TH:10.00, RLY:ON\r\n
字段含义:
    V   : 输入电压 (V)
    I   : 输入电流 (A)
    SH  : 分流采样值 (shunt_raw)
    P   : 功率 (W)
    TH  : 电压保护阈值 (V)
    RLY : 继电器状态 (ON / OFF)

下位机接收指令格式:
    直接接收浮点数字符串，以 \\r 或 \\n 结尾 (例如 "12.50\\r\\n")，范围 0.0 ~ 25.0V，触发断电保存
"""

import math
import random
import time
from typing import List, Optional, Dict, Any

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import serial
import serial.tools.list_ports


class SerialHandler(QObject):
    """
    串口通信处理类 (SerialHandler)
    """

    # 信号定义
    data_received = pyqtSignal(dict)       # 解析后的结构化数据字典
    raw_data_received = pyqtSignal(str)   # 串口原始接收到的文本行
    raw_data_sent = pyqtSignal(str)       # 向串口发送的原始文本
    connection_changed = pyqtSignal(bool)  # 连接状态变更信号
    error_occurred = pyqtSignal(str)       # 错误发生信号

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        self.serial: Optional[serial.Serial] = None
        self._buffer: str = ""

        # 定时器：读取串口数据 (100ms)
        self._read_timer = QTimer(self)
        self._read_timer.setInterval(50)
        self._read_timer.timeout.connect(self._read_serial_data)

        # 仿真模式
        self.is_simulating: bool = False
        self._sim_timer = QTimer(self)
        self._sim_timer.setInterval(500)
        self._sim_timer.timeout.connect(self._generate_sim_data)

        self._sim_phase: float = math.pi * 0.35
        self._sim_th: float = 10.00

    def get_available_ports(self) -> List[str]:
        """获取所有可用串口"""
        try:
            ports = serial.tools.list_ports.comports()
            port_list = []
            for p in ports:
                port_list.append(p.device)
            return sorted(port_list)
        except Exception as e:
            self.error_occurred.emit(f"扫描串口失败: {str(e)}")
            return []

    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """连接物理串口"""
        if self.is_simulating:
            self.stop_simulation()

        if self.serial is not None and self.serial.is_open:
            self.disconnect()

        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.05,
                write_timeout=1.0
            )
            self._buffer = ""
            self._read_timer.start(50)
            self.connection_changed.emit(True)
            return True

        except serial.SerialException as e:
            self.serial = None
            err_msg = f"无法打开串口 {port}: {str(e)}"
            self.error_occurred.emit(err_msg)
            self.connection_changed.emit(False)
            return False

        except Exception as e:
            self.serial = None
            err_msg = f"串口连接发生未知异常: {str(e)}"
            self.error_occurred.emit(err_msg)
            self.connection_changed.emit(False)
            return False

    def disconnect(self) -> None:
        """断开串口或停止仿真"""
        was_connected = self.is_connected()

        if self._read_timer.isActive():
            self._read_timer.stop()

        if self.serial is not None:
            try:
                if self.serial.is_open:
                    self.serial.close()
            except Exception as e:
                self.error_occurred.emit(f"关闭串口异常: {str(e)}")
            finally:
                self.serial = None

        if self.is_simulating:
            self.stop_simulation()

        self._buffer = ""

        if was_connected:
            self.connection_changed.emit(False)

    def is_connected(self) -> bool:
        is_serial_open = self.serial is not None and self.serial.is_open
        return is_serial_open or self.is_simulating

    def send_command(self, cmd: str) -> bool:
        """
        向串口发送文本指令 (自动追加 \\r\\n)
        """
        clean_cmd = cmd.strip('\r\n')
        full_cmd = clean_cmd + "\r\n"

        if self.is_simulating:
            # 仿真模式下尝试解析阈值更新
            try:
                val = float(clean_cmd)
                if 0.0 <= val <= 25.0:
                    self._sim_th = val
            except ValueError:
                pass
            self.raw_data_sent.emit(clean_cmd)
            return True

        if not (self.serial and self.serial.is_open):
            self.error_occurred.emit("串口未连接，无法发送指令")
            return False

        try:
            payload = full_cmd.encode('utf-8', errors='ignore')
            self.serial.write(payload)
            self.serial.flush()
            self.raw_data_sent.emit(clean_cmd)
            return True
        except serial.SerialTimeoutException:
            self.error_occurred.emit("串口发送超时")
            return False
        except Exception as e:
            self.error_occurred.emit(f"发送指令失败: {str(e)}")
            return False

    def set_threshold(self, threshold: float) -> bool:
        """快捷设置电压保护阈值"""
        cmd_str = f"{threshold:.2f}"
        return self.send_command(cmd_str)

    def _read_serial_data(self) -> None:
        """循环读取串口缓冲"""
        if not (self.serial and self.serial.is_open):
            return

        try:
            waiting = self.serial.in_waiting
            if waiting <= 0:
                return

            raw_bytes = self.serial.read(waiting)
            chunk = raw_bytes.decode('utf-8', errors='ignore')
            self._buffer += chunk

            if len(self._buffer) > 4096 and '\n' not in self._buffer:
                self._buffer = ""
                return

            while '\n' in self._buffer:
                line, self._buffer = self._buffer.split('\n', 1)
                line = line.strip('\r\n ')
                if line:
                    self.raw_data_received.emit(line)
                    self._parse_and_emit(line)

        except serial.SerialException as e:
            self.error_occurred.emit(f"串口通信异常中断: {str(e)}")
            self.disconnect()
        except Exception as e:
            self.error_occurred.emit(f"读取串口数据出错: {str(e)}")

    def _parse_and_emit(self, line: str) -> Optional[Dict[str, Any]]:
        """
        解析数据行: V:0.16, I:0, SH:-1, P:0, TH:10.00, RLY:ON
        """
        parts = [p.strip() for p in line.split(',')]
        kv = {}
        for part in parts:
            if ':' in part:
                k, v = part.split(':', 1)
                kv[k.strip().upper()] = v.strip()

        if kv:
            try:
                voltage = float(kv.get('V', '0'))
                current = float(kv.get('I', '0'))

                # 功率 P
                power_str = kv.get('P', '0')
                power = float(power_str)
                if power == 0 and voltage > 0 and current > 0:
                    power = voltage * current

                # 分流原始值 SH
                shunt = int(float(kv.get('SH', '0')))

                # 阈值 TH
                threshold = float(kv.get('TH', '0'))

                # 继电器状态 RLY
                rly_str = kv.get('RLY', 'OFF').upper()
                relay = 'ON' if 'ON' in rly_str else 'OFF'

                # 输出电压 OUT_V 与 输出电流 OUT_I
                out_voltage = float(kv.get('OUT_V', str(voltage if relay == 'ON' else 0.0)))
                out_current = float(kv.get('OUT_I', str(current if relay == 'ON' else 0.0)))

                data = {
                    'voltage': round(voltage, 2),
                    'current': round(current, 2),
                    'out_voltage': round(out_voltage, 2),
                    'out_current': round(out_current, 2),
                    'power': round(power, 2),
                    'shunt': shunt,
                    'threshold': round(threshold, 2),
                    'relay': relay
                }
                self.data_received.emit(data)
                return data
            except (ValueError, TypeError):
                pass

        # 兼容纯数字逗号分隔
        if len(parts) >= 3:
            try:
                v = float(parts[0])
                c = float(parts[1])
                p = float(parts[2]) if len(parts) > 2 else v * c
                sh = int(float(parts[3])) if len(parts) > 3 else 0
                th = float(parts[4]) if len(parts) > 4 else 10.0
                rly = parts[5] if len(parts) > 5 else ('ON' if v > th else 'OFF')

                data = {
                    'voltage': round(v, 2),
                    'current': round(c, 2),
                    'power': round(p, 2),
                    'shunt': sh,
                    'threshold': round(th, 2),
                    'relay': rly
                }
                self.data_received.emit(data)
                return data
            except ValueError:
                pass

        return None

    # =========================================================================
    # 模拟模式 (与硬件功能完全匹配)
    # =========================================================================

    def start_simulation(self, interval_ms: int = 500) -> None:
        if self.serial is not None and self.serial.is_open:
            self.disconnect()

        self.is_simulating = True
        self._sim_timer.start(interval_ms)
        self.connection_changed.emit(True)
        self._generate_sim_data()

    def stop_simulation(self) -> None:
        if not self.is_simulating:
            return

        self.is_simulating = False
        self._sim_timer.stop()
        self.connection_changed.emit(False)

    def _generate_sim_data(self) -> None:
        if not self.is_simulating:
            return

        self._sim_phase = (self._sim_phase + 0.04) % (2 * math.pi)
        raw_sun = math.sin(self._sim_phase)

        if raw_sun > 0:
            sun_intensity = raw_sun ** 1.1
            noise = random.uniform(-0.02, 0.02)
            eff = max(0.0, min(1.0, sun_intensity + noise))

            voltage = max(0.1, 15.0 * eff + random.uniform(-0.1, 0.1))
            current = max(0.0, 3.5 * eff + random.uniform(-0.03, 0.03))
            power = voltage * current
            shunt = int(current * 1000 + random.randint(-5, 5))
        else:
            voltage = max(0.05, random.uniform(0.1, 0.25))
            current = 0.0
            power = 0.0
            shunt = random.randint(-3, 0)

        relay = 'ON' if voltage > self._sim_th else 'OFF'

        sim_line = f"V:{voltage:.2f}, I:{current:.2f}, SH:{shunt}, P:{power:.2f}, TH:{self._sim_th:.2f}, RLY:{relay}"
        self.raw_data_received.emit(sim_line)

        data = {
            'voltage': round(voltage, 2),
            'current': round(current, 2),
            'power': round(power, 2),
            'shunt': shunt,
            'threshold': round(self._sim_th, 2),
            'relay': relay
        }
        self.data_received.emit(data)

    def close(self) -> None:
        self.disconnect()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
