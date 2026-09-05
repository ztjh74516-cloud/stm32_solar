#ifndef __KEY_H
#define __KEY_H

#include "stm32f10x.h"

#define KEY_NONE    0
#define KEY_SET     1
#define KEY_UP      2
#define KEY_DOWN    3

void Key_Init(void);
uint8_t Key_Scan_NonBlocking(void);

#endif