#include "stm32f10x.h"
#include "Delay.h"
#include "OLED.h"
#include "INA219.h"  
#include "PV_Monitor.h"
#include "Key.h"
#include "Alarm.h"
#include "Serial.h"
#include <stdio.h> 
#include <stdlib.h> 

volatile uint32_t sys_tick = 0;

void System_Timer_Init(void) {
    TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;
    NVIC_InitTypeDef NVIC_InitStructure;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM4, ENABLE);
    TIM_TimeBaseStructure.TIM_Period = 1000 - 1;
    TIM_TimeBaseStructure.TIM_Prescaler = 72 - 1;
    TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(TIM4, &TIM_TimeBaseStructure);
    TIM_ITConfig(TIM4, TIM_IT_Update, ENABLE);

    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
    NVIC_InitStructure.NVIC_IRQChannel = TIM4_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);
    TIM_Cmd(TIM4, ENABLE);
}

void TIM4_IRQHandler(void) {
    if (TIM_GetITStatus(TIM4, TIM_IT_Update) != RESET) {
        sys_tick++;
        TIM_ClearITPendingBit(TIM4, TIM_IT_Update);
    }
}

void Relay_Init(void) {
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    GPIO_InitTypeDef GPIO_InitStructure;
    /* 低电平触发模块需要释放状态由模块自身上拉到5V，使用开漏输出 */
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_1; // 依然使用 PA1
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    /* 初始化先释放继电器，避免上电瞬间低电平误吸合 */
    GPIO_SetBits(GPIOA, GPIO_Pin_1);
}

void Relay_Set(uint8_t state) {
    /* 当前继电器模块为低电平触发：低电平吸合，高电平释放 */
    if (state) GPIO_ResetBits(GPIOA, GPIO_Pin_1);
    else GPIO_SetBits(GPIOA, GPIO_Pin_1); 
}

/* 浮点数拆分打印宏 */
#define FLOAT_I(val)  ((int)(val))
#define FLOAT_F(val)  ((int)(((val) - (int)(val)) * 100))

int main(void) {
    float pv_v = 0.0f;  // 光伏输入电压
    float pv_c = 0.0f;  // 光伏输入电流 
    float pv_p = 0.0f;  // 【新增】光伏输入功率
    float out_v = 0.0f; // 继电器输出电压
    float out_c = 0.0f; // 继电器输出电流
    float th_v = 1.00f; // 电压保护阈值
    uint8_t relay_status = 0; 
    
    uint32_t t_adc = 0, t_key = 0, t_oled = 0, t_alarm = 0, t_serial = 0;
    uint8_t ui_state = 0; 
    char buf[32];
    int16_t shunt_raw = 0;

    /* 系统大动脉初始化 */
    OLED_Init();
    INA219_Init();  
    PV_ADC_Init();
    Key_Init();
    Alarm_Init();
    Serial_Init(); 
    Relay_Init(); 
    System_Timer_Init(); 

    /* 【新增】BKP 备份寄存器初始化 */
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_PWR | RCC_APB1Periph_BKP, ENABLE);
    PWR_BackupAccessCmd(ENABLE);
    uint16_t saved_th = BKP_ReadBackupRegister(BKP_DR1);
    if (saved_th == 0 || saved_th == 0xFFFF) {
        th_v = 1.00f; // 首次上电无记忆，使用默认值
    } else {
        th_v = saved_th / 100.0f; // 恢复之前的记忆阈值
    }

    OLED_Clear();
    
    while (1) {
        /* 【任务 1】：按键扫描 */
        if (sys_tick - t_key >= 15) {
            uint8_t key = Key_Scan_NonBlocking();
            if (key == KEY_SET) {
                ui_state = (ui_state == 0) ? 1 : 0; 
            }
            else if (key == KEY_UP && ui_state == 1) { 
                th_v += 0.1f; 
                if(th_v > 25.0f) th_v = 25.0f; 
                BKP_WriteBackupRegister(BKP_DR1, (uint16_t)(th_v * 100)); // 【新增】断电保存
            }
            else if (key == KEY_DOWN && ui_state == 1) { 
                th_v -= 0.1f; 
                if(th_v < 0.0f) th_v = 0.0f; 
                BKP_WriteBackupRegister(BKP_DR1, (uint16_t)(th_v * 100)); // 【新增】断电保存
            }
            t_key = sys_tick;
        }
        
        /* 【任务 1.5】：串口指令接收 */
        if (Serial_RxFlag == 1) {
            float new_th = atof(Serial_RxPacket);
            if (new_th >= 0.0f && new_th <= 25.0f) {
                th_v = new_th; 
                BKP_WriteBackupRegister(BKP_DR1, (uint16_t)(th_v * 100)); // 【新增】串口修改也触发断电保存
            }
            Serial_ClearRxFlag();
        }

        /* 【任务 2】：I2C 传感器高精度读取 (100ms) */
        if (sys_tick - t_adc >= 100) {
            /* 光伏/外部电源电压由继电器前端的 PA0 分压模块测量，
             * 避免继电器断开后 INA219 VIN- 悬空产生假电压。 */
            pv_v = PV_Get_Real_Voltage();
            shunt_raw = INA219_GetShuntRaw();
            pv_c = ((float)shunt_raw * 0.00001f) / 0.1f;
            if (pv_c < 0) pv_c = 0; 
            pv_p = pv_v * pv_c; // 【新增】计算实时功率
            t_adc = sys_tick;
        }

        /* 【任务 3】：保护中枢与物理闭环 (200ms) */
        if (sys_tick - t_alarm >= 200) {
            if (pv_v > th_v) {
                Alarm_Toggle();
                relay_status = 0;
                Relay_Set(relay_status);
                out_v = 0.00f; 
                out_c = 0.00f; 
            } else {
                Alarm_Set(0); 
                relay_status = 1;
                Relay_Set(relay_status);
                out_v = pv_v; 
                out_c = pv_c; 
            }
            t_alarm = sys_tick;
        }

        /* 【任务 4】：工业风 OLED 全新排版 (150ms) */
        if (sys_tick - t_oled >= 150) {
            /* 第一行：将电流单位改为 mA，数值乘以 1000 直接显示整数 */
            sprintf(buf, "PV :%2d.%02dV %4dmA", FLOAT_I(pv_v), FLOAT_F(pv_v), (int)(pv_c * 1000));
            OLED_ShowString(1, 1, buf);
            
            if (ui_state == 1) sprintf(buf, "Set:%2d.%02dV <   ", FLOAT_I(th_v), FLOAT_F(th_v));
            else               sprintf(buf, "Set:%2d.%02dV     ", FLOAT_I(th_v), FLOAT_F(th_v));
            OLED_ShowString(2, 1, buf);

            sprintf(buf, "Out:%2d.%02dV [%s]", FLOAT_I(out_v), FLOAT_F(out_v), relay_status ? "ON " : "OFF");
            OLED_ShowString(3, 1, buf);

            if (relay_status == 1) OLED_ShowString(4, 1, "STA: SYSTEM NORM");
            else                   OLED_ShowString(4, 1, "STA: OVER-VOLT! ");

            t_oled = sys_tick;
        }

        /* 【任务 5】：更新串口协议 (500ms) */
        if (sys_tick - t_serial >= 500) {
            char tx_buf[80];
            /* 将电流(I)和功率(P)放大 1000 倍，以 mA 和 mW 的整数形式输出 */
            sprintf(tx_buf, "V:%d.%02d, I:%d, SH:%d, P:%d, TH:%d.%02d, RLY:%s\r\n", 
                    FLOAT_I(pv_v), FLOAT_F(pv_v), 
                    (int)(pv_c * 1000), 
                    (int)shunt_raw,
                    (int)(pv_p * 1000), 
                    FLOAT_I(th_v), FLOAT_F(th_v), 
                    relay_status ? "ON" : "OFF");
            Serial_SendString(tx_buf);
            t_serial = sys_tick;
        }
    }
}
