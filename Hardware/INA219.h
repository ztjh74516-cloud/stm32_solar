#ifndef __INA219_H
#define __INA219_H

#include "stm32f10x.h"

/* 这里的两个引脚，必须改成你实际插 OLED 的那两个引脚！ */
// 如果你实际插的是 PB6 和 PB7，请改成这样：
#define INA_SCL_PORT  GPIOB
#define INA_SCL_PIN   GPIO_Pin_6    // 改成你真实的 SCL 管脚
#define INA_SDA_PORT  GPIOB
#define INA_SDA_PIN   GPIO_Pin_7    // 改成你真实的 SDA 管脚

void INA219_Init(void);
int16_t INA219_GetShuntRaw(void);
float INA219_GetBusVoltage(void);
float INA219_GetCurrent(void);

#endif
