#include "Telemetry.h"

#include <stdio.h>

static int ToHundredths(float value)
{
    if (value >= 0.0f) {
        return (int)(value * 100.0f + 0.5f);
    }
    return (int)(value * 100.0f - 0.5f);
}

static int ToMilliunits(float value)
{
    if (value >= 0.0f) {
        return (int)(value * 1000.0f + 0.5f);
    }
    return (int)(value * 1000.0f - 0.5f);
}

void Telemetry_Format(char *buffer,
                      float pv_voltage,
                      float pv_current,
                      float output_voltage,
                      float output_current,
                      int16_t shunt_raw,
                      float pv_power,
                      float threshold_voltage,
                      uint8_t relay_status)
{
    int pv_voltage_100 = ToHundredths(pv_voltage);
    int output_voltage_100 = ToHundredths(output_voltage);
    int threshold_voltage_100 = ToHundredths(threshold_voltage);

    sprintf(buffer,
            "V:%d.%02d, I:%d, OUT_V:%d.%02d, OUT_I:%d, SH:%d, P:%d, TH:%d.%02d, RLY:%s\r\n",
            pv_voltage_100 / 100,
            pv_voltage_100 % 100,
            ToMilliunits(pv_current),
            output_voltage_100 / 100,
            output_voltage_100 % 100,
            ToMilliunits(output_current),
            (int)shunt_raw,
            ToMilliunits(pv_power),
            threshold_voltage_100 / 100,
            threshold_voltage_100 % 100,
            relay_status ? "ON" : "OFF");
}
