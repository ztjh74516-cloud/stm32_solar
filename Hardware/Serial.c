#include "Serial.h"

char Serial_RxPacket[16]; // 用于存放接收到的字符串 (如 "1.1")
uint8_t Serial_RxFlag = 0; // 接收完成标志位
static uint8_t Serial_RxIndex = 0; // 缓冲区索引

void Serial_Init(void)
{
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    
    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_9;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    
    USART_InitTypeDef USART_InitStructure;
    USART_InitStructure.USART_BaudRate = 115200;
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    USART_InitStructure.USART_Mode = USART_Mode_Tx | USART_Mode_Rx;
    USART_InitStructure.USART_Parity = USART_Parity_No;
    USART_InitStructure.USART_StopBits = USART_StopBits_1;
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;
    USART_Init(USART1, &USART_InitStructure);
    
    /* 开启 RXNE (接收寄存器非空) 中断 */
    USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
    
    /* 配置 NVIC 中断优先级 */
    NVIC_InitTypeDef NVIC_InitStructure;
    NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);
    
    USART_Cmd(USART1, ENABLE);
}

/* 发送函数 */
void Serial_SendString(char *str)
{
    uint16_t timeout; 
    while (*str != '\0')
    {
        USART_SendData(USART1, (uint8_t)*str);
        timeout = 0;
        while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET)
        {
            timeout++;
            if (timeout > 60000) break; 
        }
        str++;
    }
}

/* 清除接收标志位，准备接收下一包数据 */
void Serial_ClearRxFlag(void)
{
    Serial_RxFlag = 0;
    Serial_RxIndex = 0;
}

/* USART1 底层中断服务函数 */
void USART1_IRQHandler(void)
{
    if (USART_GetITStatus(USART1, USART_IT_RXNE) != RESET)
    {
        char rx_data = USART_ReceiveData(USART1);
        
        /* 如果收到回车或换行符，说明电脑发完了一条完整的指令 */
        if (rx_data == '\r' || rx_data == '\n') 
        {
            if (Serial_RxIndex > 0) {
                Serial_RxPacket[Serial_RxIndex] = '\0'; // 封死字符串结尾
                Serial_RxFlag = 1; // 通知主循环收到数据
            }
        }
        else 
        {
            /* 如果还在发送过程中，就把字符存进数组 */
            if (Serial_RxFlag == 0 && Serial_RxIndex < 15) {
                Serial_RxPacket[Serial_RxIndex++] = rx_data;
            }
        }
        USART_ClearITPendingBit(USART1, USART_IT_RXNE);
    }
}