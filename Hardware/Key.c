#include "Key.h"

/**
  * @brief  初始化按键 GPIO (内部上拉)
  */
void Key_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
    
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU; /* 输入上拉 */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_12 | GPIO_Pin_13 | GPIO_Pin_14;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);
}

/**
  * @brief  非阻塞式按键扫描 (需在主循环定时调用，建议 10ms-20ms 频次)
  * @retval 返回按下的键值，0为无按键动作
  */
uint8_t Key_Scan_NonBlocking(void)
{
    static uint8_t key_state = 0; /* 状态机：0=等待按下, 1=确认按下并等待松开 */
    uint8_t key_return = KEY_NONE;
    
    /* 组合读取 PB12, PB13, PB14 的电平 */
    uint8_t set_lvl  = GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_12);
    uint8_t up_lvl   = GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_13);
    uint8_t down_lvl = GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_14);

    switch (key_state)
    {
        case 0:
            if (set_lvl == 0 || up_lvl == 0 || down_lvl == 0)
            {
                key_state = 1; /* 检测到低电平，进入确认态 (利用外部定时调用自然消抖) */
            }
            break;
            
        case 1:
            if (set_lvl == 0)       { key_return = KEY_SET; }
            else if (up_lvl == 0)   { key_return = KEY_UP; }
            else if (down_lvl == 0) { key_return = KEY_DOWN; }
            
            if (key_return != KEY_NONE) 
            {
                key_state = 2; /* 识别成功，进入等待松开态 */
            }
            else 
            {
                key_state = 0; /* 属于抖动，复位状态机 */
            }
            break;
            
        case 2:
            if (set_lvl == 1 && up_lvl == 1 && down_lvl == 1)
            {
                key_state = 0; /* 所有按键已松开，完成一次完整击键闭环 */
            }
            break;
    }
    
    return key_return;
}