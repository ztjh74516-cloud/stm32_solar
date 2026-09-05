# 基于 STM32 的太阳能发电监测与保护系统

这是一个基于 STM32F103C8 的太阳能/外部直流电源监测项目。固件采集输入电压与电流，计算功率，在 OLED 上显示状态，并依据可配置的电压阈值控制继电器和声光报警。

## 功能

- 通过 PA0 ADC 采集光伏输入电压；程序中的分压换算倍率为 5。
- 通过 INA219 读取分流电压并计算电流与功率。
- OLED 实时显示输入电压、电流、阈值、继电器状态和系统状态。
- PB12、PB13、PB14 按键用于进入阈值设置、增大和减小阈值。
- 阈值保存至备份寄存器，断电后可恢复。
- USART1 以 115200 bps 输出监测数据，也可接收 0–25 V 的阈值设置值。
- 输入电压超过阈值时断开继电器并触发蜂鸣器与指示灯报警。

## 开发环境

- MCU：STM32F103C8（Cortex-M3）
- IDE：Keil MDK（工程文件：`Project.uvprojx`）
- Keil Device Family Pack：`Keil.STM32F1xx_DFP.2.2.0`
- 也提供 EIDE 项目配置：`.eide/eide.yml`

## 构建与烧录

1. 在 Keil MDK 中打开 `Project.uvprojx`。
2. 安装或选择 `Keil.STM32F1xx_DFP` 设备包，并确认目标设备为 `STM32F103C8`。
3. 编译 Target 1；生成的 `.hex`、`.axf` 等产物会被 Git 忽略。
4. 使用 ST-Link、J-Link 或与你的调试器匹配的下载配置烧录程序。

详细引脚定义、模块连接和电平注意事项见 [硬件连接说明](docs/硬件连接说明.md)。

## 目录结构

- `User/`：程序入口与中断配置
- `Hardware/`：OLED、INA219、按键、报警、串口与电压监测驱动
- `System/`：系统通用功能
- `Library/`：STM32 标准外设库
- `Start/`：启动文件与 CMSIS 相关文件

## 许可证

本项目的原创代码采用 [MIT License](LICENSE)。`Library/` 与 `Start/` 中包含的 STMicroelectronics 标准外设库和 ARM CMSIS 文件不因本许可证而被重新授权；其版权与使用条件见 [第三方软件声明](THIRD_PARTY_NOTICES.md) 及各文件头部。
