# 第三方软件声明

本仓库包含以下并非项目作者原创的组件：

- `Library/`：STM32F10x Standard Peripheral Library（文件头标注为 STMicroelectronics，V3.5.0）。
- `Start/stm32f10x.h`、`Start/system_stm32f10x.*` 与相关设备文件：STMicroelectronics 的 STM32F10x CMSIS/设备支持文件。
- `Start/core_cm3.*`：ARM CMSIS Cortex-M3 组件。

本仓库根目录的 [MIT License](LICENSE) 仅授予项目原创代码的许可；它不修改或取代上述第三方组件自身的版权声明、许可或使用条件。再发布本仓库时，请保留第三方文件头部的版权与声明，并核对适用于所使用版本的软件包许可。

官方参考：

- [STMicroelectronics：STM32 Standard Peripheral Libraries 文档](https://www.st.com/en/embedded-software/stm32-standard-peripheral-libraries/documentation.html)
- [STMicroelectronics：STM32F10x Standard Peripheral Library（STSW-STM32054）](https://www.st.com/en/embedded-software/stsw-stm32054.html)
