#ifndef __ALARM_H
#define __ALARM_H

#include "stm32f10x.h"

void Alarm_Init(void);
void Alarm_Set(uint8_t state);
void Alarm_Toggle(void);

#endif