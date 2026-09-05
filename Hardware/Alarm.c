#include "Alarm.h"

void Alarm_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
    
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10 | GPIO_Pin_11;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);
    
    /* 初始化默认不报警 */
    Alarm_Set(0);
}

void Alarm_Set(uint8_t state)
{
    if (state) {
        /* 触发报警：蜂鸣器给低电平(响)，LED给高电平(亮) */
        GPIO_ResetBits(GPIOB, GPIO_Pin_10); 
        GPIO_SetBits(GPIOB, GPIO_Pin_11);   
    } else {
        /* 解除报警：蜂鸣器给高电平(静音)，LED给低电平(灭) */
        GPIO_SetBits(GPIOB, GPIO_Pin_10);   
        GPIO_ResetBits(GPIOB, GPIO_Pin_11); 
    }
}

void Alarm_Toggle(void)
{
    /* 读取 LED 当前状态并反转，完美带动蜂鸣器同频动作 */
    uint8_t current_state = GPIO_ReadOutputDataBit(GPIOB, GPIO_Pin_11);
    Alarm_Set(!current_state);
}