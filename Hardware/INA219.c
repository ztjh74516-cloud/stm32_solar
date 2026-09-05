#include "INA219.h"

#define INA219_ADDRESS  0x80  // I2C 物理地址 (0x40 左移 1 位)

/* 极简软件延时，防止和系统的 Delay 冲突 */
static void INA_Delay(void) {
    uint8_t i = 20;
    while(i--);
}

/* 软件 I2C 引脚控制宏 */
#define SCL_H()  GPIO_SetBits(INA_SCL_PORT, INA_SCL_PIN)
#define SCL_L()  GPIO_ResetBits(INA_SCL_PORT, INA_SCL_PIN)
#define SDA_H()  GPIO_SetBits(INA_SDA_PORT, INA_SDA_PIN)
#define SDA_L()  GPIO_ResetBits(INA_SDA_PORT, INA_SDA_PIN)
#define SDA_R()  GPIO_ReadInputDataBit(INA_SDA_PORT, INA_SDA_PIN)

static void I2C_Start(void) {
    SDA_H(); SCL_H(); INA_Delay();
    SDA_L(); INA_Delay(); SCL_L(); INA_Delay();
}

static void I2C_Stop(void) {
    SDA_L(); SCL_H(); INA_Delay();
    SDA_H(); INA_Delay();
}

static void I2C_SendByte(uint8_t byte) {
    uint8_t i;
    for (i = 0; i < 8; i++) {
        if (byte & 0x80) SDA_H();
        else SDA_L();
        byte <<= 1;
        SCL_H(); INA_Delay();
        SCL_L(); INA_Delay();
    }
    SDA_H(); SCL_H(); INA_Delay(); SCL_L(); INA_Delay(); // 忽略 ACK
}

static uint16_t I2C_ReadWord(uint8_t reg) {
    uint16_t data = 0;
    uint8_t i;
    
    /* 写寄存器地址 */
    I2C_Start();
    I2C_SendByte(INA219_ADDRESS);
    I2C_SendByte(reg);
    
    /* 读 16 位数据 */
    I2C_Start();
    I2C_SendByte(INA219_ADDRESS | 0x01); // 读方向
    
    SDA_H(); // 释放 SDA 准备读取
    for (i = 0; i < 16; i++) {
        SCL_H(); INA_Delay();
        data <<= 1;
        if (SDA_R()) data |= 0x01;
        SCL_L(); INA_Delay();
        
        if (i == 7) { // 发送 ACK (读完高8位)
            SDA_L(); SCL_H(); INA_Delay(); SCL_L(); INA_Delay(); SDA_H();
        }
    }
    /* 发送 NACK (读完低8位) */
    SDA_H(); SCL_H(); INA_Delay(); SCL_L(); INA_Delay();
    I2C_Stop();
    
    return data;
}

void INA219_Init(void) {
    GPIO_InitTypeDef GPIO_InitStructure;
    if (INA_SCL_PORT == GPIOA || INA_SDA_PORT == GPIOA) RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    if (INA_SCL_PORT == GPIOB || INA_SDA_PORT == GPIOB) RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
    if (INA_SCL_PORT == GPIOC || INA_SDA_PORT == GPIOC) RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
    
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD; // I2C 必须使用开漏输出
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    
    GPIO_InitStructure.GPIO_Pin = INA_SCL_PIN;
    GPIO_Init(INA_SCL_PORT, &GPIO_InitStructure);
    
    GPIO_InitStructure.GPIO_Pin = INA_SDA_PIN;
    GPIO_Init(INA_SDA_PORT, &GPIO_InitStructure);
    
    SCL_H(); SDA_H();
}

/* 读取真实的母线电压 (光伏板输入电压) */
float INA219_GetBusVoltage(void) {
    uint16_t reg_data = I2C_ReadWord(0x02); // 寄存器 0x02 存电压
    reg_data >>= 3;                         // INA219 规定需要右移 3 位
    return (float)reg_data * 0.004f;        // 每一位代表 4mV
}

/* 读取原始分流电压寄存器，单位为 10uV/bit，保留符号用于排查方向问题 */
int16_t INA219_GetShuntRaw(void) {
    return (int16_t)I2C_ReadWord(0x01);
}

/* 读取真实的回路电流 (安培) */
float INA219_GetCurrent(void) {
    int16_t shunt_reg = INA219_GetShuntRaw(); // 寄存器 0x01 存分流电压
    /* INA219 自带的采样电阻是 R100(0.1欧)。根据欧姆定律直接换算成安培 */
    return ((float)shunt_reg * 0.00001f) / 0.1f; 
}
