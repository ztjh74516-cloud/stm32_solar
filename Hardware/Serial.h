#ifndef __SERIAL_H
#define __SERIAL_H

#include "stm32f10x.h"

/* 暴露出接收缓冲区和标志位，供 main 函数使用 */
extern char Serial_RxPacket[];
extern uint8_t Serial_RxFlag;

void Serial_Init(void);
void Serial_SendString(char *str);
void Serial_ClearRxFlag(void);

#endif