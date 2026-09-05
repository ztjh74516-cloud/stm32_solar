#ifndef __PV_MONITOR_H
#define __PV_MONITOR_H

#include "stm32f10x.h"

#define ADC_RESOLUTION        4096.0f
#define STM32_VDD_REF         3.3f
#define VOLTAGE_SENSOR_RATIO  5.0f

void PV_ADC_Init(void);
float PV_Get_Real_Voltage(void);

#endif